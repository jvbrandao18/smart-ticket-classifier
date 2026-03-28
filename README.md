# smart-ticket-classifier

API em FastAPI para triagem inteligente de chamados técnicos. O projeto combina regras determinísticas por palavras-chave com fallback opcional via LLM, persistência em SQLite, trilha de auditoria e explainability em `decision_trace`.

## Stack

- Python 3.12
- FastAPI
- Pydantic
- SQLite
- SQLAlchemy
- pytest
- Docker

## Problema resolvido

Times de suporte normalmente recebem tickets com texto curto, ambíguo e inconsistente. O objetivo aqui é acelerar a triagem inicial e devolver uma classificação padronizada com:

- categoria
- prioridade
- causa raiz provável
- fila sugerida
- confidence score
- justificativa resumida
- trilha de auditoria
- decision trace explicável

## Fluxo

```text
Request -> Pydantic validation -> RuleEngine -> optional LLM fallback -> consolidation
        -> persistence (tickets + audit_logs) -> standardized JSON response
```

## Por que regras + LLM

- Regras são rápidas, baratas, previsíveis e ótimas para sinais claros como `senha`, `timeout` ou `integracao`.
- LLM entra apenas quando a confiança das regras é baixa ou o texto é ambíguo.
- Esse desenho reduz custo e mantém o comportamento auditável sem abrir mão de cobertura em cenários mais nebulosos.

## Confidence score

O `confidence_score` desta V1 é heurístico. Ele sobe com o número de palavras-chave relevantes encontradas e cai quando há competição entre categorias ou sinais fracos. Isso está explícito no código e é uma decisão consciente para manter o projeto simples, testável e barato.

## Explainability mode

Toda classificação retorna `decision_trace`, por exemplo:

```json
[
  "rule: palavras 'senha, acesso, permissao' -> categoria acesso",
  "rule: prioridade alta com confidence_score 0.89",
  "llm: nao acionado porque confidence_score das regras ficou em 0.89",
  "final: decisao rules com confidence_score 0.89"
]
```

## Endpoints

- `GET /health`
- `POST /classify`
- `GET /audit/{id}`
- `GET /metrics`

## Métricas expostas

`GET /metrics` retorna:

- total de tickets
- total de eventos de auditoria
- média de `confidence_score`
- latência média de processamento
- taxa de fallback via LLM
- taxa de tentativa de uso de LLM
- distribuição por categoria
- distribuição por prioridade

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

4. Suba a API.

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Rode os testes.

```bash
python -m pytest
```

## Execução com Docker

```bash
cp .env.example .env
docker compose up --build
```

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
    "decision_source": "rules",
    "decision_trace": [
      "rule: palavras 'acesso, senha, permissao' -> categoria acesso",
      "llm: nao acionado porque confidence_score das regras ficou em 0.89"
    ],
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

## Hardening do LLM

- validação estrita do schema via Pydantic
- extra keys proibidas
- retry controlado
- fallback total para regras em caso de timeout, erro HTTP ou payload inválido

## Qualidade

- 18 testes automatizados cobrindo API, edge cases, prioridade conflitante, input inválido e fallback do LLM
- respostas JSON padronizadas
- logs estruturados com `correlation_id`
- auditoria persistida em `audit_logs`

## Python 3.12

O projeto permanece alinhado ao requisito de Python 3.12. Além do `Dockerfile`, o repositório inclui workflow de CI para validar a suíte em Python 3.12 no GitHub Actions.

## Trade-offs

- SQLite simplifica a operação, mas não é o banco ideal para cargas concorrentes maiores.
- O score de confiança é heurístico, não probabilístico calibrado.
- Não há camada de migração de banco nesta V1.
- O LLM é opcional e desligado por padrão para manter a execução local simples.

## Limitações

- Sem versionamento formal de prompts.
- Sem benchmark de qualidade por dataset rotulado.
- Sem autenticação/autorização nos endpoints.
- Métricas ainda são aplicacionais, não Prometheus nativo.

## Próximos passos

- adicionar migrations com Alembic
- criar benchmark supervisionado por categoria
- publicar dashboard de métricas
- adicionar autenticação e rate limiting
- integrar provider LLM real com observabilidade dedicada
