[![CI](https://github.com/jvbrandao18/smart-ticket-classifier/actions/workflows/ci.yml/badge.svg)](https://github.com/jvbrandao18/smart-ticket-classifier/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Tests](https://img.shields.io/badge/tests-19%20passing-brightgreen)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/jvbrandao18/smart-ticket-classifier)

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

## Endpoints

- `GET /health`
- `POST /classify`
- `GET /audit/{id}`
- `GET /metrics`
- `GET /examples`

## Demo rápida

### Caso 1: acesso

Input:

```json
{
  "title": "Usuario sem acesso apos reset de senha",
  "description": "O usuario segue sem acesso ao portal e recebe erro de permissao ao autenticar.",
  "requester": "time.suporte",
  "source_system": "portal-interno"
}
```

Output resumido:

```json
{
  "category": "acesso",
  "priority": "alta",
  "suggested_queue": "service-desk-acessos",
  "decision_source": "rules"
}
```

### Caso 2: integracao

Input:

```json
{
  "title": "Integracao CRM x ERP nao sincroniza",
  "description": "A integracao via API nao envia pedidos desde ontem a noite.",
  "requester": "operacoes",
  "source_system": "crm"
}
```

Output resumido:

```json
{
  "category": "integracao",
  "priority": "alta",
  "suggested_queue": "squad-integracoes",
  "decision_source": "rules"
}
```

### Caso 3: automacao

Input:

```json
{
  "title": "Robo de faturamento nao processou",
  "description": "A automacao do faturamento nao executou o job agendado durante a madrugada.",
  "requester": "backoffice",
  "source_system": "orquestrador"
}
```

Output resumido:

```json
{
  "category": "automacao",
  "priority": "media",
  "suggested_queue": "squad-automacoes",
  "decision_source": "rules"
}
```

### Caso 4: fallback controlado

Input:

```json
{
  "title": "Solicitacao de novo perfil",
  "description": "Time de compras precisa de um novo perfil de consulta para homologacao.",
  "requester": "compras",
  "source_system": "iam"
}
```

Output resumido:

```json
{
  "category": "solicitacao",
  "priority": "baixa",
  "decision_source": "rules",
  "decision_trace": [
    "rule: nenhuma palavra-chave forte encontrada -> classificacao provisoria solicitacao",
    "llm: fallback total para regras por llm_disabled"
  ]
}
```

### Caso 5: conflito de prioridade

Input:

```json
{
  "title": "Login critico",
  "description": "Sistema parado para todos os usuarios, sem acesso ao portal e com senha rejeitada.",
  "requester": "time.ops"
}
```

Output resumido:

```json
{
  "category": "acesso",
  "priority": "critica",
  "decision_source": "rules"
}
```

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

## Métricas

`GET /metrics` expõe:

- total de tickets
- total de eventos de auditoria
- média de `confidence_score`
- latência média de processamento
- taxa de fallback via LLM
- taxa de tentativa de uso de LLM
- distribuição por categoria
- distribuição por prioridade

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

## Deploy

O repositório está preparado para deploy com Docker no Render via [render.yaml](render.yaml). O botão no topo do README cria o serviço a partir do GitHub com:

- health check em `/health`
- uso de `PORT` dinâmico
- disco persistente para o SQLite
- configuração mínima de ambiente

Observação: eu preparei a infraestrutura de deploy, mas o URL público final depende da criação do serviço na sua conta Render.

## Execução com Docker

```bash
cp .env.example .env
docker compose up --build
```

## Hardening do LLM

- validação estrita do schema via Pydantic
- extra keys proibidas
- retry controlado
- fallback total para regras em caso de timeout, erro HTTP ou payload inválido

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

## Próximos passos

- criar um deploy público real a partir do `render.yaml`
- ligar o fluxo a um provedor LLM real
- adicionar benchmark supervisionado com mais classes e mais ruído
- publicar dashboard de métricas
- adicionar autenticação e rate limiting
