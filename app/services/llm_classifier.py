import json
import logging
import re

import httpx

from app.core.config import BASE_DIR, Settings
from app.schemas.ticket import LLMClassificationSuggestion, TicketRequest


class LLMClassifier:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.prompt_path = BASE_DIR / "app" / "prompts" / "classification_prompt.txt"

    async def classify_ticket(
        self,
        *,
        payload: TicketRequest,
        correlation_id: str,
    ) -> LLMClassificationSuggestion | None:
        if not self.settings.llm_enabled or not self.settings.llm_api_key:
            return None

        prompt = self._build_prompt(payload)
        endpoint = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"
        request_body = {
            "model": self.settings.llm_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self.prompt_path.read_text(encoding="utf-8")},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {self.settings.llm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_body,
                )
                response.raise_for_status()
        except httpx.HTTPError:
            self.logger.exception(
                "LLM classification request failed.",
                extra={
                    "event": "llm_request_failed",
                    "correlation_id": correlation_id,
                },
            )
            return None

        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_response(content)

    def _build_prompt(self, payload: TicketRequest) -> str:
        return (
            f"Title: {payload.title}\n"
            f"Description: {payload.description}\n"
            f"Requester: {payload.requester}\n"
            f"Source System: {payload.source_system or 'n/a'}\n"
        )

    def _parse_response(self, content: str) -> LLMClassificationSuggestion | None:
        try:
            parsed = json.loads(self._extract_json(content))
            return LLMClassificationSuggestion.model_validate(parsed)
        except (KeyError, ValueError, json.JSONDecodeError):
            self.logger.exception("Invalid LLM classification payload received.")
            return None

    def _extract_json(self, content: str) -> str:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in response.")
        return match.group(0)
