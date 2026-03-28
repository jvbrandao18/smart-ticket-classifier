from datetime import datetime
from typing import Any

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
    created_at: datetime
    audit_trail: list[AuditTrailItem] = Field(default_factory=list)
