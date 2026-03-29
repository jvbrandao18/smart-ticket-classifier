---
title: Smart Ticket Classifier
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

[![CI](https://github.com/jvbrandao18/smart-ticket-classifier/actions/workflows/ci.yml/badge.svg)](https://github.com/jvbrandao18/smart-ticket-classifier/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Tests](https://img.shields.io/badge/tests-19%20passing-brightgreen)

# smart-ticket-classifier

API em FastAPI para triagem inteligente de chamados técnicos. O projeto combina regras determinísticas com fallback opcional via LLM, persistência em SQLite, auditoria, explainability e avaliação offline sobre dataset rotulado.

## O que a API retorna

- categoria
- prioridade
- causa raiz provável
- fila sugerida
- confidence score
- justificativa resumida
- trilha de auditoria
- decision trace explicável

## Stack

- Python 3.12
- FastAPI
- Pydantic
- SQLite
- SQLAlchemy
- pytest
- Docker

## Endpoints

- `GET /health`
- `POST /classify`
- `GET /audit/{id}`
- `GET /metrics`
- `GET /examples`
- `GET /docs`

## Fluxo

```text
Request -> validation -> RuleEngine -> optional LLM fallback -> consolidation
        -> persistence (tickets + audit_logs) -> standardized JSON response
```

## Por que regras + LLM

- Regras são rápidas, baratas e auditáveis para sinais claros como `senha`, `timeout` e `integracao`.
- LLM só entra quando a confiança cai ou o texto fica ambíguo.
- Isso reduz custo e mantém previsibilidade sem abrir mão de cobertura em casos difíceis.

## Confidence score

O `confidence_score` desta V1 é heurístico. Ele sobe com o número de palavras-chave relevantes encontradas e cai quando há competição entre categorias ou sinais fracos. Não é uma probabilidade calibrada; é uma métrica operacional para triagem inicial.

## Explainability mode

Toda classificação retorna `decision_trace`, por exemplo:

```json
[
  "rule: palavras 'acesso, senha, permissao' -> categoria acesso",
  "rule: prioridade alta com confidence_score 0.89",
  "llm: nao acionado porque confidence_score das regras ficou em 0.89",
  "final: decisao rules com confidence_score 0.89"
]
```

## Avaliação offline

O repositório inclui [scripts/evaluate_classifier.py](scripts/evaluate_classifier.py), que roda o classificador contra o dataset rotulado em [data/sample_tickets.json](data/sample_tickets.json).

```bash
python scripts/evaluate_classifier.py --output docs/evaluation_report.json
```

Baseline atual com a configuração padrão do projeto:

- total de exemplos: `30`
- accuracy de categoria: `0.8333`
- accuracy de prioridade: `0.8667`
- taxa de fallback via LLM: `0.0`
- confidence score médio: `0.749`

O relatório completo da última execução está em [docs/evaluation_report.json](docs/evaluation_report.json).

## Execução local

1. Crie um ambiente virtual com Python 3.12.
2. Instale as dependências.

```bash
pip install -e .[dev]
```

3. Crie o arquivo `.env`.

```bash
cp .env.example .env
```

No PowerShell:

```powershell
Copy-Item .env.example .env
```

4. Suba a API localmente.

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Rode os testes.

```bash
python -m pytest
```

## Execução com Docker local

```bash
cp .env.example .env
docker compose up --build
```

A API continua acessível localmente em `http://localhost:8000`.

## Deploy no Hugging Face Spaces

Este repositório está pronto para Space do tipo Docker.

### Como criar o Space

1. Crie um novo Space no Hugging Face.
2. Escolha o tipo `Docker`.
3. Faça push deste repositório para o Space.
4. Aguarde o build do `Dockerfile`.

### Variáveis e secrets

Configure nas Settings do Space, sem commitá-las:

- `LLM_ENABLED`
- `LLM_API_KEY` ou `OPENAI_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `RULE_CONFIDENCE_THRESHOLD`

Se nenhuma chave de API existir, a aplicação continua subindo normalmente e opera em modo determinístico com fallback explícito.

### Endpoints para validar após o deploy

- `/health`
- `/docs`
- `/examples`
- `/metrics`

### Observação sobre SQLite

No Hugging Face Spaces Docker, o banco SQLite roda em armazenamento efêmero de demo. Após rebuild ou restart, os dados podem ser perdidos. Isso é aceitável para portfólio e demonstração pública, mas não é persistência forte de produção.

## Docker e runtime do Space

- a aplicação escuta em `0.0.0.0`
- a porta padrão do container é `7860`
- o `Dockerfile` usa fallback explícito para `PORT=7860`
- o banco no container usa `DATABASE_URL` em `/tmp` por padrão

## Variáveis principais

- `PORT`
- `DATABASE_URL`
- `RULE_CONFIDENCE_THRESHOLD`
- `LLM_ENABLED`
- `LLM_API_KEY`
- `OPENAI_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_RETRIES`

## Qualidade

- 19 testes automatizados cobrindo API, edge cases, prioridade conflitante, input inválido, `/examples` e fallback do LLM
- CI em Python 3.12 via GitHub Actions
- auditoria persistida em `audit_logs`
- logs estruturados com `correlation_id`

## Trade-offs

- SQLite simplifica a operação, mas não é o banco ideal para alta concorrência.
- O score de confiança é heurístico, não probabilístico calibrado.
- O LLM é opcional e desligado por padrão para manter execução local simples.
- As métricas atuais são aplicacionais, não Prometheus nativo.

## Limitações

- Sem autenticação/autorização nos endpoints.
- Sem migrations formais de banco.
- Dataset sintético, apesar de mais realista.
- Sem observabilidade externa de produção.

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
data/
docs/
scripts/
tests/
.github/workflows/
```
