---
title: Smart Ticket Classifier
sdk: docker
app_port: 7860
pinned: false
---

# Smart Ticket Classifier

Smart Ticket Classifier is a FastAPI backend that receives technical support tickets, classifies them, suggests priority and probable root cause, and records an audit trail for the decision.

## What is it?

It is an API-first ticket triage service for support, service desk, and automation operations scenarios.

The API can:

- classify a support ticket from `title`, `description`, `requester`, and optional `source_system`
- return category, priority, probable root cause, suggested queue, confidence, and justification
- record audit information for each classification
- return example tickets for demos
- expose basic metrics and health endpoints

The classifier uses deterministic rules by default. An optional LLM fallback can be used when configured, but the service can run without an OpenAI API key.

## Why was it built?

Support tickets often arrive with incomplete descriptions, inconsistent classification, and subjective priority decisions. A structured first-pass triage can make the next support step clearer without hiding how the decision was made.

This project was built to demonstrate a practical AI-adjacent backend: deterministic rules first, optional LLM fallback, explicit decision traces, persistence, auditability, API validation, tests, Docker support, and a deployable container setup.

## How does it work?

A client sends a ticket payload to `/classify`.

The classification service validates the input, applies local rules, optionally attempts LLM classification when configured, persists the ticket and audit data in SQLite, and returns a structured response.

The response includes:

- `ticket_id`
- `category`
- `priority`
- `probable_root_cause`
- `suggested_queue`
- `confidence_score`
- `summary_justification`
- `decision_source`
- `decision_trace`
- `audit_trail`

### Main technologies

- Python 3.12
- FastAPI
- Pydantic
- Pydantic Settings
- SQLAlchemy
- SQLite
- Pytest
- Docker
- Optional OpenAI-compatible LLM fallback

### API endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Basic service information |
| `GET` | `/status` | Service status and version |
| `GET` | `/health` | Health check |
| `GET` | `/examples` | Return sample tickets |
| `GET` | `/metrics` | Return classification metrics |
| `POST` | `/classify` | Classify a ticket |
| `GET` | `/audit/{ticket_id}` | Return audit data for one ticket |
| `GET` | `/docs` | Swagger API documentation |

### Example usage

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Certificate generation error",
    "description": "The student completed the course, but the certificate was not issued in the portal after 48 hours.",
    "requester": "academic_support",
    "source_system": "student_portal"
  }'
```

Example response shape:

```json
{
  "data": {
    "ticket_id": "ticket-id",
    "category": "incident",
    "priority": "alta",
    "probable_root_cause": "Falha operacional ou indisponibilidade do servico.",
    "suggested_queue": "noc-aplicacoes",
    "confidence_score": 0.82,
    "summary_justification": "Incident category suggested by matched keywords.",
    "decision_source": "rules",
    "decision_trace": [
      "rule: matched error-related keywords"
    ],
    "audit_trail": []
  }
}
```

If the Hugging Face Space is running, the public demo is available at:

- Space: `https://huggingface.co/spaces/jvitbrandao/smart-ticket-classifier`
- API: `https://jvitbrandao-smart-ticket-classifier.hf.space`
- Swagger: `https://jvitbrandao-smart-ticket-classifier.hf.space/docs`

### Project structure

```text
app/
  main.py                 FastAPI application factory
  api/routes/             HTTP endpoints
  core/                   Configuration, database, errors, logging, middleware
  domain/                 Rules, enums, and domain models
  infra/repositories/     SQLite repositories
  prompts/                LLM prompt template
  schemas/                Pydantic request and response schemas
  services/               Classification, audit, metrics, and LLM fallback logic
data/
docs/
scripts/
tests/
Dockerfile
docker-compose.yml
pyproject.toml
requirements.txt
```

## How do I run it?

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:

- API: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

### Run with Docker

```bash
docker build -t smart-ticket-classifier .
docker run -p 8000:7860 smart-ticket-classifier
```

With Docker Compose:

```bash
docker compose up --build
```

### Optional LLM configuration

The service runs with deterministic rules when no LLM key is configured. To enable the optional LLM fallback, create a `.env` file from `.env.example`, set `LLM_ENABLED=true`, and configure `LLM_API_KEY` or `OPENAI_API_KEY` before starting the app.

### Tests and validation

```bash
python -m pytest -v
```

Additional project evaluation script:

```bash
python scripts/evaluate_classifier.py
```
