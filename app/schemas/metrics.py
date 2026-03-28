from pydantic import BaseModel


class MetricsSnapshot(BaseModel):
    total_tickets: int = 0
    total_audit_logs: int = 0

