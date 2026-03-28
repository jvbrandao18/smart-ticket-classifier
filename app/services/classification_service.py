from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from time import perf_counter
from typing import Any, Literal

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppException
from app.domain.rules import RuleEngine, RuleEvaluation
from app.infra.repositories.audit_repository import AuditRepository
from app.infra.repositories.ticket_repository import TicketRepository
from app.schemas.audit import AuditTrailItem
from app.schemas.ticket import ClassificationResponse, TicketDecision, TicketProcessingMetadata, TicketRequest
from app.services.llm_classifier import LLMClassifier, LLMExecutionResult


@dataclass(frozen=True)
class ConsolidationResult:
    decision: TicketDecision
    decision_source: Literal["rules", "llm"]


class ClassificationService:
    def __init__(
        self,
        *,
        settings: Settings,
        llm_classifier: LLMClassifier,
        ticket_repository: TicketRepository,
        audit_repository: AuditRepository,
    ) -> None:
        self.settings = settings
        self.rule_engine = RuleEngine()
        self.llm_classifier = llm_classifier
        self.ticket_repository = ticket_repository
        self.audit_repository = audit_repository
        self.logger = logging.getLogger(__name__)

    async def classify_ticket(
        self,
        *,
        payload: TicketRequest,
        correlation_id: str,
        session: Session,
    ) -> ClassificationResponse:
        started_at = perf_counter()
        audit_trail: list[AuditTrailItem] = [
            self._audit_item(
                event="input_validated",
                details={
                    "requester": payload.requester,
                    "source_system": payload.source_system,
                },
            )
        ]

        rule_evaluation = self.rule_engine.evaluate(
            title=payload.title,
            description=payload.description,
            confidence_threshold=self.settings.rule_confidence_threshold,
        )
        audit_trail.append(
            self._audit_item(
                event="rule_evaluation_completed",
                details={
                    "category": rule_evaluation.category.value,
                    "priority": rule_evaluation.priority.value,
                    "matched_keywords": list(rule_evaluation.matched_keywords),
                    "confidence_score": rule_evaluation.confidence_score,
                    "llm_required": rule_evaluation.llm_required,
                },
            )
        )
        self.logger.info(
            "Rule evaluation completed.",
            extra={
                "event": "rule_evaluation_completed",
                "correlation_id": correlation_id,
            },
        )

        llm_result: LLMExecutionResult | None = None
        if rule_evaluation.llm_required:
            llm_result = await self.llm_classifier.classify_ticket(
                payload=payload,
                correlation_id=correlation_id,
            )
            audit_trail.append(
                self._audit_item(
                    event="llm_evaluation_completed" if llm_result.suggestion else "llm_evaluation_skipped",
                    details={
                        "enabled": self.settings.llm_enabled,
                        "attempts": llm_result.attempts,
                        "latency_ms": llm_result.latency_ms,
                        "received_suggestion": llm_result.suggestion is not None,
                        "fallback_reason": llm_result.fallback_reason,
                    },
                )
            )
        else:
            audit_trail.append(
                self._audit_item(
                    event="llm_not_required",
                    details={"confidence_score": rule_evaluation.confidence_score},
                )
            )

        consolidation = self._consolidate(rule_evaluation=rule_evaluation, llm_result=llm_result)
        decision_trace = self._build_decision_trace(
            rule_evaluation=rule_evaluation,
            llm_result=llm_result,
            consolidation=consolidation,
        )
        processing_time_ms = max(1, int((perf_counter() - started_at) * 1000))
        processing_metadata = TicketProcessingMetadata(
            decision_source=consolidation.decision_source,
            llm_attempted=bool(llm_result and llm_result.attempts > 0),
            llm_used=consolidation.decision_source == "llm",
            llm_attempt_count=llm_result.attempts if llm_result else 0,
            llm_latency_ms=llm_result.latency_ms if llm_result else 0,
            processing_time_ms=processing_time_ms,
            decision_trace=decision_trace,
        )
        audit_trail.append(
            self._audit_item(
                event="final_classification_consolidated",
                details={
                    "category": consolidation.decision.category.value,
                    "priority": consolidation.decision.priority.value,
                    "confidence_score": consolidation.decision.confidence_score,
                    "decision_source": consolidation.decision_source,
                    "decision_trace": decision_trace,
                },
            )
        )

        try:
            ticket = self.ticket_repository.create(
                session,
                payload=payload,
                decision=consolidation.decision,
                metadata=processing_metadata,
                correlation_id=correlation_id,
            )
            audit_trail.append(
                self._audit_item(
                    event="ticket_persisted",
                    details={
                        "ticket_id": ticket.id,
                        "processing_time_ms": processing_time_ms,
                    },
                )
            )
            self.audit_repository.create_many(
                session,
                ticket_id=ticket.id,
                correlation_id=correlation_id,
                audit_trail=audit_trail,
            )
            session.commit()
        except SQLAlchemyError as exc:
            session.rollback()
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="PERSISTENCE_ERROR",
                message="Failed to persist ticket classification.",
            ) from exc

        self.logger.info(
            "Ticket classified and persisted.",
            extra={
                "event": "ticket_classified",
                "correlation_id": correlation_id,
                "ticket_id": ticket.id,
            },
        )
        return ClassificationResponse(
            ticket_id=ticket.id,
            category=consolidation.decision.category,
            priority=consolidation.decision.priority,
            probable_root_cause=consolidation.decision.probable_root_cause,
            suggested_queue=consolidation.decision.suggested_queue,
            confidence_score=consolidation.decision.confidence_score,
            summary_justification=consolidation.decision.summary_justification,
            decision_source=consolidation.decision_source,
            decision_trace=decision_trace,
            audit_trail=audit_trail,
        )

    def _consolidate(
        self,
        *,
        rule_evaluation: RuleEvaluation,
        llm_result: LLMExecutionResult | None,
    ) -> ConsolidationResult:
        if llm_result and llm_result.suggestion and llm_result.suggestion.confidence_score >= rule_evaluation.confidence_score:
            return ConsolidationResult(
                decision=TicketDecision(
                    category=llm_result.suggestion.category,
                    priority=llm_result.suggestion.priority,
                    probable_root_cause=llm_result.suggestion.probable_root_cause,
                    suggested_queue=llm_result.suggestion.suggested_queue,
                    confidence_score=llm_result.suggestion.confidence_score,
                    summary_justification=llm_result.suggestion.summary_justification,
                ),
                decision_source="llm",
            )

        return ConsolidationResult(
            decision=TicketDecision(
                category=rule_evaluation.category,
                priority=rule_evaluation.priority,
                probable_root_cause=rule_evaluation.probable_root_cause,
                suggested_queue=rule_evaluation.suggested_queue,
                confidence_score=rule_evaluation.confidence_score,
                summary_justification=rule_evaluation.summary_justification,
            ),
            decision_source="rules",
        )

    def _build_decision_trace(
        self,
        *,
        rule_evaluation: RuleEvaluation,
        llm_result: LLMExecutionResult | None,
        consolidation: ConsolidationResult,
    ) -> list[str]:
        trace: list[str] = []
        if rule_evaluation.matched_keywords:
            joined_keywords = ", ".join(rule_evaluation.matched_keywords)
            trace.append(
                f"rule: palavras '{joined_keywords}' -> categoria {rule_evaluation.category.value}"
            )
        else:
            trace.append(
                "rule: nenhuma palavra-chave forte encontrada -> classificacao provisoria solicitacao"
            )

        trace.append(
            f"rule: prioridade {rule_evaluation.priority.value} com confidence_score {rule_evaluation.confidence_score:.2f}"
        )

        if llm_result is None:
            trace.append(
                f"llm: nao acionado porque confidence_score das regras ficou em {rule_evaluation.confidence_score:.2f}"
            )
        elif llm_result.suggestion is None:
            trace.append(
                f"llm: fallback total para regras por {llm_result.fallback_reason or 'falha_desconhecida'}"
            )
        elif consolidation.decision_source == "llm":
            trace.append(
                f"llm: reforcou a decisao final para {llm_result.suggestion.category.value} com prioridade {llm_result.suggestion.priority.value}"
            )
        else:
            trace.append(
                "llm: resposta valida recebida, mas as regras permaneceram por maior ou igual confianca"
            )

        trace.append(
            f"final: decisao {consolidation.decision_source} com confidence_score {consolidation.decision.confidence_score:.2f}"
        )
        return trace

    def _audit_item(self, *, event: str, details: dict[str, Any]) -> AuditTrailItem:
        return AuditTrailItem(
            event=event,
            timestamp=datetime.now(timezone.utc),
            details=details,
        )
