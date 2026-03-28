from pydantic import BaseModel, Field


class MetricsSnapshot(BaseModel):
    total_tickets: int = 0
    total_audit_logs: int = 0
    average_confidence_score: float = 0.0
    average_processing_time_ms: float = 0.0
    llm_fallback_count: int = 0
    llm_fallback_rate_percent: float = 0.0
    llm_attempt_rate_percent: float = 0.0
    tickets_by_category: dict[str, int] = Field(default_factory=dict)
    tickets_by_priority: dict[str, int] = Field(default_factory=dict)
