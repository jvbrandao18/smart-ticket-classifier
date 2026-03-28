from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.common import ResponseEnvelope, success_envelope
from app.schemas.metrics import MetricsSnapshot
from app.services.metrics_service import MetricsService


router = APIRouter()


def get_metrics_service(request: Request) -> MetricsService:
    return request.app.state.metrics_service


@router.get("/metrics", response_model=ResponseEnvelope[MetricsSnapshot])
async def get_metrics(
    request: Request,
    service: MetricsService = Depends(get_metrics_service),
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    result = service.get_snapshot(session=session)
    return success_envelope(request.state.correlation_id, result)
