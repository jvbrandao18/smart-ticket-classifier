from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.domain.enums import Category, Priority
from app.infra.repositories.audit_repository import AuditRepository
from app.infra.repositories.ticket_repository import TicketRepository
from app.schemas.audit import AuditTrailItem, TicketAuditResponse


class AuditService:
    def __init__(
        self,
        *,
        ticket_repository: TicketRepository,
        audit_repository: AuditRepository,
    ) -> None:
        self.ticket_repository = ticket_repository
        self.audit_repository = audit_repository

    def get_ticket_audit(self, *, session: Session, ticket_id: str) -> TicketAuditResponse:
        ticket = self.ticket_repository.get_by_id(session, ticket_id)
        if ticket is None:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="TICKET_NOT_FOUND",
                message="Ticket not found for the provided id.",
                details={"ticket_id": ticket_id},
            )

        logs = self.audit_repository.get_by_ticket_id(session, ticket_id)
        audit_trail = [
            AuditTrailItem(
                event=log.event,
                timestamp=log.created_at,
                details=log.details or {},
            )
            for log in logs
        ]
        return TicketAuditResponse(
            ticket_id=ticket.id,
            correlation_id=ticket.correlation_id,
            category=Category(ticket.category),
            priority=Priority(ticket.priority),
            created_at=ticket.created_at,
            audit_trail=audit_trail,
        )
