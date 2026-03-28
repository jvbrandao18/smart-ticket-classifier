from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import AuditLog
from app.schemas.audit import AuditTrailItem


class AuditRepository:
    def create_many(
        self,
        session: Session,
        *,
        ticket_id: str,
        correlation_id: str,
        audit_trail: list[AuditTrailItem],
    ) -> list[AuditLog]:
        logs = [
            AuditLog(
                ticket_id=ticket_id,
                event=item.event,
                details=item.details,
                step_order=index,
                correlation_id=correlation_id,
                created_at=item.timestamp,
            )
            for index, item in enumerate(audit_trail, start=1)
        ]
        session.add_all(logs)
        session.flush()
        return logs

    def get_by_ticket_id(self, session: Session, ticket_id: str) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.ticket_id == ticket_id)
            .order_by(AuditLog.step_order.asc(), AuditLog.created_at.asc())
        )
        return list(session.scalars(statement).all())

    def count_all(self, session: Session) -> int:
        statement = select(func.count(AuditLog.id))
        return int(session.scalar(statement) or 0)
