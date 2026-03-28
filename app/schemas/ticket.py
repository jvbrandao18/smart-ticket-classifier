from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import Category, Priority
from app.schemas.audit import AuditTrailItem


class TicketRequest(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=4000)
    requester: str = Field(min_length=2, max_length=120)
    source_system: str | None = Field(default=None, max_length=80)

    model_config = ConfigDict(str_strip_whitespace=True)


class TicketDecision(BaseModel):
    category: Category
    priority: Priority
    probable_root_cause: str = Field(min_length=10, max_length=240)
    suggested_queue: str = Field(min_length=3, max_length=120)
    confidence_score: float = Field(ge=0.0, le=1.0)
    summary_justification: str = Field(min_length=10, max_length=280)

    model_config = ConfigDict(extra="forbid")


class LLMClassificationSuggestion(TicketDecision):
    pass


class TicketProcessingMetadata(BaseModel):
    decision_source: Literal["rules", "llm"]
    llm_attempted: bool = False
    llm_used: bool = False
    llm_attempt_count: int = Field(default=0, ge=0)
    llm_latency_ms: int = Field(default=0, ge=0)
    processing_time_ms: int = Field(default=0, ge=0)
    decision_trace: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ClassificationResponse(TicketDecision):
    ticket_id: str
    decision_source: Literal["rules", "llm"]
    decision_trace: list[str] = Field(default_factory=list)
    audit_trail: list[AuditTrailItem] = Field(default_factory=list)
