from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domain.enums import Category, Priority


class AuditTrailItem(BaseModel):
    event: str
    timestamp: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class TicketAuditResponse(BaseModel):
    ticket_id: str
    correlation_id: str
    category: Category
    priority: Priority
    decision_source: Literal["rules", "llm"]
    decision_trace: list[str] = Field(default_factory=list)
    created_at: datetime
    audit_trail: list[AuditTrailItem] = Field(default_factory=list)
