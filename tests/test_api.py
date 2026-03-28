from fastapi.testclient import TestClient


def test_health_returns_application_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["environment"] == "test"
    assert "correlation_id" in payload


def test_classify_persists_ticket_and_exposes_audit_and_metrics(client: TestClient) -> None:
    response = client.post(
        "/classify",
        headers={"X-Correlation-ID": "corr-test-001"},
        json={
            "title": "Usuario sem acesso apos reset de senha",
            "description": "O usuario segue sem acesso ao portal e recebe erro de permissao ao autenticar.",
            "requester": "time.suporte",
            "source_system": "portal-interno",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    ticket_id = data["ticket_id"]

    assert payload["correlation_id"] == "corr-test-001"
    assert data["category"] == "acesso"
    assert data["priority"] == "alta"
    assert data["suggested_queue"] == "service-desk-acessos"
    assert data["confidence_score"] >= 0.7
    assert any(item["event"] == "ticket_persisted" for item in data["audit_trail"])

    audit_response = client.get(f"/audit/{ticket_id}")

    assert audit_response.status_code == 200
    audit_payload = audit_response.json()["data"]
    assert audit_payload["ticket_id"] == ticket_id
    assert audit_payload["category"] == "acesso"
    assert len(audit_payload["audit_trail"]) >= 4

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    metrics_payload = metrics_response.json()["data"]
    assert metrics_payload["total_tickets"] == 1
    assert metrics_payload["total_audit_logs"] >= 4
    assert metrics_payload["tickets_by_category"]["acesso"] == 1
