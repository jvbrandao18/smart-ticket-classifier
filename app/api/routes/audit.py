from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.audit import TicketAuditResponse
from app.schemas.common import ResponseEnvelope, success_envelope
from app.services.audit_service import AuditService


router = APIRouter()


def get_audit_service(request: Request) -> AuditService:
    return request.app.state.audit_service


@router.get("/audit/{ticket_id}", response_model=ResponseEnvelope[TicketAuditResponse])
async def get_audit(
    ticket_id: str,
    request: Request,
    service: AuditService = Depends(get_audit_service),
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    result = service.get_ticket_audit(session=session, ticket_id=ticket_id)
    return success_envelope(request.state.correlation_id, result)
