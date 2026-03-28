from dataclasses import dataclass
import json
import logging
import re
from time import perf_counter
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import BASE_DIR, Settings
from app.schemas.ticket import LLMClassificationSuggestion, TicketRequest


@dataclass(frozen=True)
class LLMExecutionResult:
    suggestion: LLMClassificationSuggestion | None
    attempts: int
    latency_ms: int
    fallback_reason: str | None


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
    ) -> LLMExecutionResult:
        if not self.settings.llm_enabled:
            return LLMExecutionResult(
                suggestion=None,
                attempts=0,
                latency_ms=0,
                fallback_reason="llm_disabled",
            )
        if not self.settings.llm_api_key:
            return LLMExecutionResult(
                suggestion=None,
                attempts=0,
                latency_ms=0,
                fallback_reason="llm_api_key_missing",
            )

        prompt = self._build_prompt(payload)
        last_failure_reason = "llm_unknown_error"
        started_at = perf_counter()
        max_attempts = max(1, self.settings.llm_max_retries + 1)

        for attempt in range(1, max_attempts + 1):
            try:
                response_payload = await self._send_completion_request(prompt)
                content = self._extract_content(response_payload)
                suggestion = self._parse_response(content)
                return LLMExecutionResult(
                    suggestion=suggestion,
                    attempts=attempt,
                    latency_ms=self._elapsed_ms(started_at),
                    fallback_reason=None,
                )
            except httpx.TimeoutException:
                last_failure_reason = "llm_timeout"
                self.logger.warning(
                    "LLM request timed out.",
                    extra={
                        "event": "llm_timeout",
                        "correlation_id": correlation_id,
                    },
                )
            except httpx.HTTPError:
                last_failure_reason = "llm_http_error"
                self.logger.warning(
                    "LLM request returned an HTTP error.",
                    extra={
                        "event": "llm_http_error",
                        "correlation_id": correlation_id,
                    },
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError):
                last_failure_reason = "invalid_llm_payload"
                self.logger.warning(
                    "LLM response could not be validated.",
                    extra={
                        "event": "invalid_llm_payload",
                        "correlation_id": correlation_id,
                    },
                )

        return LLMExecutionResult(
            suggestion=None,
            attempts=max_attempts,
            latency_ms=self._elapsed_ms(started_at),
            fallback_reason=last_failure_reason,
        )

    def _build_prompt(self, payload: TicketRequest) -> str:
        return (
            f"Title: {payload.title}\n"
            f"Description: {payload.description}\n"
            f"Requester: {payload.requester}\n"
            f"Source System: {payload.source_system or 'n/a'}\n"
        )

    async def _send_completion_request(self, prompt: str) -> dict[str, Any]:
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
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {self.settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            response.raise_for_status()
            return response.json()

    def _extract_content(self, response_payload: dict[str, Any]) -> str:
        return str(response_payload["choices"][0]["message"]["content"])

    def _parse_response(self, content: str) -> LLMClassificationSuggestion:
        parsed = json.loads(self._extract_json(content))
        return LLMClassificationSuggestion.model_validate(parsed)

    def _extract_json(self, content: str) -> str:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in response.")
        return match.group(0)

    def _elapsed_ms(self, started_at: float) -> int:
        return max(1, int((perf_counter() - started_at) * 1000))
