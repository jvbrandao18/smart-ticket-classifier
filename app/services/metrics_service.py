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
        return MetricsSnapshot(
            total_tickets=self.ticket_repository.count_all(session),
            total_audit_logs=self.audit_repository.count_all(session),
            average_confidence_score=self.ticket_repository.average_confidence(session),
            tickets_by_category=self.ticket_repository.count_by_category(session),
            tickets_by_priority=self.ticket_repository.count_by_priority(session),
        )
