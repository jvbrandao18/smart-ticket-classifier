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


class LLMClassificationSuggestion(TicketDecision):
    pass


class ClassificationResponse(TicketDecision):
    ticket_id: str | None = None
    audit_trail: list[AuditTrailItem] = Field(default_factory=list)
