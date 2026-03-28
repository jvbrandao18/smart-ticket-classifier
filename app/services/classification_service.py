from datetime import datetime, timezone
import logging
from typing import Any

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppException
from app.domain.rules import RuleEngine, RuleEvaluation
from app.infra.repositories.audit_repository import AuditRepository
from app.infra.repositories.ticket_repository import TicketRepository
from app.schemas.audit import AuditTrailItem
from app.schemas.ticket import ClassificationResponse, LLMClassificationSuggestion, TicketDecision, TicketRequest
from app.services.llm_classifier import LLMClassifier


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

        llm_suggestion: LLMClassificationSuggestion | None = None
        if rule_evaluation.llm_required:
            llm_suggestion = await self.llm_classifier.classify_ticket(
                payload=payload,
                correlation_id=correlation_id,
            )
            audit_trail.append(
                self._audit_item(
                    event="llm_evaluation_completed" if llm_suggestion else "llm_evaluation_skipped",
                    details={
                        "enabled": self.settings.llm_enabled,
                        "received_suggestion": llm_suggestion is not None,
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

        decision = self._consolidate(rule_evaluation=rule_evaluation, llm_suggestion=llm_suggestion)
        audit_trail.append(
            self._audit_item(
                event="final_classification_consolidated",
                details={
                    "category": decision.category.value,
                    "priority": decision.priority.value,
                    "confidence_score": decision.confidence_score,
                },
            )
        )

        try:
            ticket = self.ticket_repository.create(
                session,
                payload=payload,
                decision=decision,
                correlation_id=correlation_id,
            )
            audit_trail.append(
                self._audit_item(
                    event="ticket_persisted",
                    details={"ticket_id": ticket.id},
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
            category=decision.category,
            priority=decision.priority,
            probable_root_cause=decision.probable_root_cause,
            suggested_queue=decision.suggested_queue,
            confidence_score=decision.confidence_score,
            summary_justification=decision.summary_justification,
            audit_trail=audit_trail,
        )

    def _consolidate(
        self,
        *,
        rule_evaluation: RuleEvaluation,
        llm_suggestion: LLMClassificationSuggestion | None,
    ) -> TicketDecision:
        if llm_suggestion and llm_suggestion.confidence_score >= rule_evaluation.confidence_score:
            return TicketDecision(
                category=llm_suggestion.category,
                priority=llm_suggestion.priority,
                probable_root_cause=llm_suggestion.probable_root_cause,
                suggested_queue=llm_suggestion.suggested_queue,
                confidence_score=llm_suggestion.confidence_score,
                summary_justification=llm_suggestion.summary_justification,
            )

        return TicketDecision(
            category=rule_evaluation.category,
            priority=rule_evaluation.priority,
            probable_root_cause=rule_evaluation.probable_root_cause,
            suggested_queue=rule_evaluation.suggested_queue,
            confidence_score=rule_evaluation.confidence_score,
            summary_justification=rule_evaluation.summary_justification,
        )

    def _audit_item(self, *, event: str, details: dict[str, Any]) -> AuditTrailItem:
        return AuditTrailItem(
            event=event,
            timestamp=datetime.now(timezone.utc),
            details=details,
        )
