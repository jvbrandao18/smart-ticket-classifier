import json
from functools import lru_cache

from fastapi import APIRouter, Query, Request

from app.core.config import BASE_DIR
from app.schemas.common import ResponseEnvelope, success_envelope
from app.schemas.examples import ExampleTicket, ExamplesResponse


router = APIRouter()


@lru_cache
def load_examples() -> list[ExampleTicket]:
    payload = json.loads((BASE_DIR / "data" / "sample_tickets.json").read_text(encoding="utf-8"))
    return [ExampleTicket.model_validate(item) for item in payload]


@router.get("/examples", response_model=ResponseEnvelope[ExamplesResponse])
async def get_examples(
    request: Request,
    limit: int = Query(default=5, ge=1, le=10),
) -> dict[str, object]:
    examples = load_examples()
    data = ExamplesResponse(
        total_available=len(examples),
        returned_count=min(limit, len(examples)),
        examples=examples[:limit],
    )
    return success_envelope(request.state.correlation_id, data)
