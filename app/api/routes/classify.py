from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.common import ResponseEnvelope, success_envelope
from app.schemas.ticket import ClassificationResponse, TicketRequest
from app.services.classification_service import ClassificationService


router = APIRouter()


def get_classification_service(request: Request) -> ClassificationService:
    return request.app.state.classification_service


@router.post("/classify", response_model=ResponseEnvelope[ClassificationResponse])
async def classify_ticket(
    payload: TicketRequest,
    request: Request,
    service: ClassificationService = Depends(get_classification_service),
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    result = await service.classify_ticket(
        payload=payload,
        correlation_id=request.state.correlation_id,
        session=session,
    )
    return success_envelope(request.state.correlation_id, result)
