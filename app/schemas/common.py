from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


class ResponseEnvelope(BaseModel, Generic[DataT]):
    status: str = "success"
    correlation_id: str
    data: DataT


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    status: str = "error"
    correlation_id: str
    error: ErrorDetail


class HealthStatus(BaseModel):
    app_name: str
    version: str
    environment: str
    status: str = "ok"


def success_envelope(correlation_id: str, data: BaseModel | dict[str, Any]) -> dict[str, Any]:
    payload = data.model_dump(mode="json") if isinstance(data, BaseModel) else data
    return {
        "status": "success",
        "correlation_id": correlation_id,
        "data": payload,
    }
