from fastapi import APIRouter, Request

from app.schemas.common import HealthStatus, ResponseEnvelope, success_envelope


router = APIRouter()


@router.get("/health", response_model=ResponseEnvelope[HealthStatus])
async def healthcheck(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    data = HealthStatus(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    return success_envelope(request.state.correlation_id, data)
