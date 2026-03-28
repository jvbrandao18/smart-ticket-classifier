from pydantic import BaseModel, ConfigDict, Field


class TicketRequest(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=4000)
    requester: str = Field(min_length=2, max_length=120)
    source_system: str | None = Field(default=None, max_length=80)

    model_config = ConfigDict(str_strip_whitespace=True)

