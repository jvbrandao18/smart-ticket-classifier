from pydantic import BaseModel


class AuditTrailItem(BaseModel):
    event: str
    details: dict[str, object]

