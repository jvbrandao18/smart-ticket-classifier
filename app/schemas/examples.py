from pydantic import BaseModel, Field

from app.domain.enums import Category, Priority


class ExampleTicket(BaseModel):
    title: str
    description: str
    requester: str
    source_system: str | None = None
    expected_category: Category
    expected_priority: Priority


class ExamplesResponse(BaseModel):
    total_available: int = 0
    returned_count: int = 0
    examples: list[ExampleTicket] = Field(default_factory=list)
