from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    database_path = tmp_path / "test_smart_ticket_classifier.db"
    return Settings(
        app_name="smart-ticket-classifier-test",
        environment="test",
        database_url=f"sqlite:///{database_path.as_posix()}",
        llm_enabled=False,
        rule_confidence_threshold=0.72,
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    app = create_app(test_settings)
    with TestClient(app) as test_client:
        yield test_client
