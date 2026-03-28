from sqlalchemy.orm import Session

from app.infra.repositories.audit_repository import AuditRepository
from app.infra.repositories.ticket_repository import TicketRepository
from app.schemas.metrics import MetricsSnapshot


class MetricsService:
    def __init__(
        self,
        *,
        ticket_repository: TicketRepository,
        audit_repository: AuditRepository,
    ) -> None:
        self.ticket_repository = ticket_repository
        self.audit_repository = audit_repository

    def get_snapshot(self, *, session: Session) -> MetricsSnapshot:
        total_tickets = self.ticket_repository.count_all(session)
        llm_fallback_count = self.ticket_repository.count_llm_used(session)
        llm_attempt_count = self.ticket_repository.count_llm_attempted(session)
        return MetricsSnapshot(
            total_tickets=total_tickets,
            total_audit_logs=self.audit_repository.count_all(session),
            average_confidence_score=self.ticket_repository.average_confidence(session),
            average_processing_time_ms=self.ticket_repository.average_processing_time(session),
            llm_fallback_count=llm_fallback_count,
            llm_fallback_rate_percent=self._rate(llm_fallback_count, total_tickets),
            llm_attempt_rate_percent=self._rate(llm_attempt_count, total_tickets),
            tickets_by_category=self.ticket_repository.count_by_category(session),
            tickets_by_priority=self.ticket_repository.count_by_priority(session),
        )

    def _rate(self, numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)
