import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.domain.enums import Category, Priority
from app.schemas.ticket import LLMClassificationSuggestion, TicketRequest
from app.services.llm_classifier import LLMClassifier, LLMExecutionResult


@pytest.mark.anyio
async def test_llm_classifier_retries_after_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    classifier = LLMClassifier(
        settings=Settings(
            environment="test",
            llm_enabled=True,
            llm_api_key="secret",
            llm_max_retries=2,
        )
    )
    responses = [
        {"choices": [{"message": {"content": "not-json"}}]},
        {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "category": "dados",
                                "priority": "media",
                                "probable_root_cause": "Inconsistencia de dados entre as fontes.",
                                "suggested_queue": "analytics-ops",
                                "confidence_score": 0.91,
                                "summary_justification": "O contexto aponta para falha de dados consolidada.",
                            }
                        )
                    }
                }
            ]
        },
    ]

    async def fake_send_completion_request(prompt: str) -> dict[str, object]:
        return responses.pop(0)

    monkeypatch.setattr(classifier, "_send_completion_request", fake_send_completion_request)

    result = await classifier.classify_ticket(
        payload=TicketRequest(
            title="Dashboard inconsistente",
            description="Os dados nao batem com o ERP desde ontem.",
            requester="analytics",
        ),
        correlation_id="corr-llm-001",
    )

    assert result.suggestion is not None
    assert result.attempts == 2
    assert result.fallback_reason is None
    assert result.suggestion.category == Category.DADOS


@pytest.mark.anyio
async def test_llm_classifier_falls_back_after_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    classifier = LLMClassifier(
        settings=Settings(
            environment="test",
            llm_enabled=True,
            llm_api_key="secret",
            llm_max_retries=1,
        )
    )

    async def fake_send_completion_request(prompt: str) -> dict[str, object]:
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(classifier, "_send_completion_request", fake_send_completion_request)

    result = await classifier.classify_ticket(
        payload=TicketRequest(
            title="Solicitacao ambigua",
            description="Preciso de ajuda para entender um comportamento estranho no sistema.",
            requester="ops",
        ),
        correlation_id="corr-llm-002",
    )

    assert result.suggestion is None
    assert result.attempts == 2
    assert result.fallback_reason == "llm_timeout"


def test_classify_uses_llm_when_rules_have_low_confidence(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_classify_ticket(*, payload: TicketRequest, correlation_id: str) -> LLMExecutionResult:
        return LLMExecutionResult(
            suggestion=LLMClassificationSuggestion(
                category=Category.DADOS,
                priority=Priority.MEDIA,
                probable_root_cause="Indicadores apontam para inconsistencias na camada analitica.",
                suggested_queue="analytics-ops",
                confidence_score=0.93,
                summary_justification="O contexto ambigio foi resolvido para dados pelo modelo.",
            ),
            attempts=1,
            latency_ms=18,
            fallback_reason=None,
        )

    monkeypatch.setattr(
        client.app.state.classification_service.llm_classifier,
        "classify_ticket",
        fake_classify_ticket,
    )

    response = client.post(
        "/classify",
        json={
            "title": "Contexto ambiguo no sistema",
            "description": "Os usuarios relatam um comportamento estranho sem erro claro e sem palavra-chave forte.",
            "requester": "time.ops",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["decision_source"] == "llm"
    assert payload["category"] == "dados"
    assert any(step.startswith("llm: reforcou") for step in payload["decision_trace"])

    metrics_response = client.get("/metrics")
    metrics_payload = metrics_response.json()["data"]
    assert metrics_payload["llm_fallback_count"] == 1
    assert metrics_payload["llm_fallback_rate_percent"] == 100.0
    assert metrics_payload["llm_attempt_rate_percent"] == 100.0


def test_classify_falls_back_to_rules_when_llm_returns_none(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_classify_ticket(*, payload: TicketRequest, correlation_id: str) -> LLMExecutionResult:
        return LLMExecutionResult(
            suggestion=None,
            attempts=2,
            latency_ms=40,
            fallback_reason="invalid_llm_payload",
        )

    monkeypatch.setattr(
        client.app.state.classification_service.llm_classifier,
        "classify_ticket",
        fake_classify_ticket,
    )

    response = client.post(
        "/classify",
        json={
            "title": "Ajuste solicitado sem detalhes claros",
            "description": "Preciso de apoio para revisar um comportamento que nao ficou claro para o usuario.",
            "requester": "time.ops",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["decision_source"] == "rules"
    assert payload["category"] == "solicitacao"
    assert any("fallback total para regras" in step for step in payload["decision_trace"])

    metrics_response = client.get("/metrics")
    metrics_payload = metrics_response.json()["data"]
    assert metrics_payload["llm_fallback_count"] == 0
    assert metrics_payload["llm_attempt_rate_percent"] == 100.0
