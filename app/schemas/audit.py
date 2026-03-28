from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditTrailItem(BaseModel):
    event: str
    timestamp: datetime
    details: dict[str, Any] = Field(default_factory=dict)
