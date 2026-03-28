# smart-ticket-classifier

API em FastAPI para classificar chamados técnicos com regras determinísticas, complemento opcional por LLM, persistência em SQLite e trilha de auditoria por ticket.

## Stack

- Python 3.12
- FastAPI
- Pydantic
- SQLite
- SQLAlchemy
- pytest
- Docker

## Estrutura

```text
app/
  api/routes/
  core/
  domain/
  infra/repositories/
  prompts/
  schemas/
  services/
tests/
docs/
data/
```

## Como executar localmente

1. Crie um ambiente virtual com Python 3.12.
2. Instale as dependências:

```bash
pip install -e .[dev]
```

3. Crie o arquivo de ambiente:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

4. Suba a API:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Rode os testes:

```bash
python -m pytest
```

## Como executar com Docker

```bash
cp .env.example .env
docker compose up --build
```

## Endpoints

- `GET /health`
- `POST /classify`
- `GET /audit/{id}`
- `GET /metrics`

## Exemplo de payload

```json
{
  "title": "Usuario sem acesso apos reset de senha",
  "description": "O usuario segue sem acesso ao portal e recebe erro de permissao ao autenticar.",
  "requester": "time.suporte",
  "source_system": "portal-interno"
}
```

## Exemplo de resposta

```json
{
  "status": "success",
  "correlation_id": "corr-123",
  "data": {
    "ticket_id": "uuid",
    "category": "acesso",
    "priority": "alta",
    "probable_root_cause": "Credencial expirada ou permissao inconsistente.",
    "suggested_queue": "service-desk-acessos",
    "confidence_score": 0.89,
    "summary_justification": "Categoria acesso sugerida pelas palavras-chave: acesso, senha, permissao.",
    "audit_trail": [
      {
        "event": "input_validated",
        "timestamp": "2026-03-28T00:00:00Z",
        "details": {}
      }
    ]
  }
}
```

## Regras de classificação

- `acesso`, `senha`, `permissao` direcionam para `acesso`
- `indisponivel`, `timeout`, `erro`, `falha` direcionam para `incidente`
- `integracao` direciona para `integracao`
- `dashboard`, `dados` direcionam para `dados`
- `robo`, `automacao` direcionam para `automacao`
- ausência de sinais fortes cai em `solicitacao`

Quando a confiança das regras fica abaixo do limiar configurado, a aplicação tenta complementar a classificação com um LLM compatível com API estilo OpenAI. Se o LLM estiver desabilitado, a resposta segue somente com o resultado determinístico e a auditoria registra essa decisão.

## Variáveis principais

- `DATABASE_URL`: URL SQLite da aplicação
- `RULE_CONFIDENCE_THRESHOLD`: limiar para acionar complemento por LLM
- `LLM_ENABLED`: habilita ou desabilita chamada externa
- `LLM_API_KEY`: chave do provedor LLM
- `LLM_BASE_URL`: endpoint base compatível com `/chat/completions`
- `LLM_MODEL`: modelo a ser utilizado

## Observações

- O banco SQLite é criado automaticamente em `data/`
- O endpoint `/metrics` consolida tickets e logs de auditoria
- O endpoint `/audit/{id}` retorna a trilha persistida do ticket
- Logs são emitidos em formato estruturado JSON
