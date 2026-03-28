from fastapi.testclient import TestClient


def test_classify_rejects_missing_description(client: TestClient) -> None:
    response = client.post(
        "/classify",
        json={
            "title": "Titulo valido",
            "requester": "time.ops",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_classify_rejects_too_short_title(client: TestClient) -> None:
    response = client.post(
        "/classify",
        json={
            "title": "oi",
            "description": "Descricao suficientemente longa para o teste de validacao.",
            "requester": "time.ops",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "VALIDATION_ERROR"
