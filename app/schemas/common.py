from typing import Generic, TypeVar

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

