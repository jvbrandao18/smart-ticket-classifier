from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import Ticket
from app.schemas.ticket import TicketDecision, TicketRequest


class TicketRepository:
    def create(
        self,
        session: Session,
        *,
        payload: TicketRequest,
        decision: TicketDecision,
        correlation_id: str,
    ) -> Ticket:
        ticket = Ticket(
            title=payload.title,
            description=payload.description,
            requester=payload.requester,
            source_system=payload.source_system,
            category=decision.category.value,
            priority=decision.priority.value,
            probable_root_cause=decision.probable_root_cause,
            suggested_queue=decision.suggested_queue,
            confidence_score=decision.confidence_score,
            summary_justification=decision.summary_justification,
            correlation_id=correlation_id,
        )
        session.add(ticket)
        session.flush()
        return ticket

    def get_by_id(self, session: Session, ticket_id: str) -> Ticket | None:
        statement = select(Ticket).where(Ticket.id == ticket_id)
        return session.scalar(statement)

    def count_all(self, session: Session) -> int:
        statement = select(func.count(Ticket.id))
        return int(session.scalar(statement) or 0)

    def average_confidence(self, session: Session) -> float:
        statement = select(func.avg(Ticket.confidence_score))
        value = session.scalar(statement)
        return round(float(value or 0.0), 4)

    def count_by_category(self, session: Session) -> dict[str, int]:
        statement = select(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category)
        rows = session.execute(statement).all()
        return {category: int(total) for category, total in rows}

    def count_by_priority(self, session: Session) -> dict[str, int]:
        statement = select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
        rows = session.execute(statement).all()
        return {priority: int(total) for priority, total in rows}
