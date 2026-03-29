# Smart Ticket Classifier

> Projeto de portfólio focado em triagem inteligente de tickets para operações de suporte, service desk e automação corporativa.

API de triagem inteligente para chamados técnicos, projetada para classificar tickets, sugerir causa raiz, priorizar atendimento e registrar auditoria técnica.

## Objetivo

Reduzir triagem manual em operações de suporte e service desk, combinando:

- regras determinísticas
- fallback opcional com LLM
- explainability
- persistência de resultados
- avaliação offline

## Problema que resolve

Times de suporte recebem chamados com:

- descrição incompleta
- classificação inconsistente
- baixa padronização
- priorização subjetiva

Este projeto transforma texto livre em uma saída estruturada e auditável para acelerar atendimento e melhorar qualidade operacional.

## O que a API retorna

Para cada ticket, a API pode retornar:

- **categoria**
- **prioridade**
- **causa raiz provável**
- **justificativa da classificação**
- **score/confiança**
- **trilha de auditoria**
- **decision trace**

## Exemplo de entrada

```json
{
  "title": "Erro ao gerar certificado",
  "description": "Aluno concluiu o curso, mas o certificado nao foi emitido no portal apos 48 horas.",
  "requester": "suporte.academico",
  "source_system": "portal-do-aluno"
}
```

## Exemplo de saída

```json
{
  "category": "incidente",
  "priority": "alta",
  "probable_root_cause": "Falha operacional ou indisponibilidade do servico.",
  "confidence_score": 0.82,
  "summary_justification": "Categoria incidente sugerida pelas palavras-chave: erro.",
  "decision_trace": [
    "rule: palavras 'erro' -> categoria incidente",
    "rule: prioridade alta com confidence_score 0.82"
  ],
  "audit_trail": [
    {
      "event": "input_validated"
    }
  ]
}
```

---

## Arquitetura

```text
Cliente / Frontend / Postman
            |
            v
         FastAPI
            |
   +--------+--------+
   |        |        |
   v        v        v
 Rules   Classifier  Audit
 Engine  / LLM       Logger
   |        |          |
   +--------+-----+----+
                  v
               SQLite
```

## Stack utilizada

- **Python 3.12**
- **FastAPI**
- **Pydantic**
- **SQLite**
- **SQLAlchemy**
- **Pytest**
- **Docker**
- **Hugging Face Spaces (deploy)**
- **LLM fallback opcional**

## Principais capacidades

- classificação automática de chamados
- priorização por impacto e urgência
- sugestão de causa raiz
- explicabilidade da decisão
- persistência para histórico e análise
- endpoint de healthcheck
- endpoint de exemplos para demo
- testes automatizados
- deploy containerizado

## Casos de uso reais

Este projeto é aderente a cenários como:

- service desk corporativo
- sustentação de automações
- triagem de incidentes operacionais
- backlog técnico
- automação de atendimento interno
- operações com alto volume de chamados

## Diferenciais técnicos

### 1) Regras + IA

Evita depender 100% de LLM. Mantém previsibilidade e custo controlado.

### 2) Auditabilidade

Cada classificação pode ser rastreada, revisada e explicada.

### 3) Estrutura pronta para operação

Projeto organizado para API real, testes, avaliação, auditoria e deploy.

### 4) Expansível

Pode evoluir para:

- integração com Jira / ServiceNow / Zendesk
- classificação multi-rótulo
- RAG com base de incidentes
- recomendação automática de resolução
- dashboard operacional

---

## Como executar localmente

### 1. Clonar o projeto

```bash
git clone https://github.com/jvbrandao18/smart-ticket-classifier.git
cd smart-ticket-classifier
```

### 2. Criar ambiente virtual

```bash
python -m venv .venv
```

### 3. Ativar ambiente

**Windows**

```bash
.venv\Scripts\activate
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

### 4. Instalar dependências

```bash
pip install -e .[dev]
```

### 5. Rodar a API

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Acesse:

- API: `http://127.0.0.1:8000`
- Docs Swagger: `http://127.0.0.1:8000/docs`

---

## Rodando com Docker

```bash
docker build -t smart-ticket-classifier .
docker run -p 8000:7860 smart-ticket-classifier
```

---

## Testes

```bash
python -m pytest -v
```

## Estrutura do projeto

```text
smart-ticket-classifier/
├── app/
│   ├── api/
│   ├── core/
│   ├── domain/
│   ├── infra/
│   ├── prompts/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
├── data/
├── docs/
├── scripts/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Próximos passos

Roadmap sugerido:

- [ ] autenticação por API key
- [ ] endpoint batch para múltiplos tickets
- [ ] dashboard com métricas de classificação
- [ ] integração com fila/mensageria
- [ ] feedback loop para reclassificação
- [ ] benchmark entre regras e LLM

## Deploy

Demo pública:

[Hugging Face Space](https://huggingface.co/spaces/jvitbrandao/smart-ticket-classifier)

## Valor de negócio

Este projeto demonstra capacidade prática em:

- engenharia de software aplicada a IA
- automação corporativa
- design de APIs
- classificação de texto
- explainable AI
- arquitetura pronta para operação

## Autor

**João Vitor**
Analista de TI | Python | Automação | IA aplicada a operações

GitHub: `https://github.com/jvbrandao18`
