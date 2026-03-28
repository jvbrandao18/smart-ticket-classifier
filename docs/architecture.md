# Arquitetura

## Visão geral

O `smart-ticket-classifier` segue uma separação simples por camadas para manter o código legível, tipado e fácil de evoluir:

- `app/api/routes`: expõe os endpoints HTTP
- `app/core`: configuração, erros, middleware e bootstrap do banco
- `app/domain`: enums, modelos SQLAlchemy e regras determinísticas
- `app/infra/repositories`: acesso ao banco
- `app/prompts`: prompt base para o classificador LLM
- `app/schemas`: contratos Pydantic de entrada e saída
- `app/services`: orquestração do fluxo de negócio

## Fluxo do POST /classify

1. O request é validado via Pydantic e recebe um `correlation_id`.
2. O `RuleEngine` aplica classificação por palavras-chave.
3. Se a confiança ficar abaixo do limiar configurado, o `LLMClassifier` é consultado de forma opcional.
4. O `ClassificationService` consolida a decisão final.
5. O ticket é persistido na tabela `tickets`.
6. A trilha de auditoria é persistida na tabela `audit_logs`.
7. A API retorna um envelope JSON padronizado com os dados da decisão.

## Persistência

### Tabela `tickets`

Armazena:

- dados originais do chamado
- categoria final
- prioridade final
- causa raiz provável
- fila sugerida
- score de confiança
- justificativa resumida
- `correlation_id`
- timestamp de criação

### Tabela `audit_logs`

Armazena:

- ticket relacionado
- evento executado
- detalhes estruturados em JSON
- ordem do passo
- `correlation_id`
- timestamp

## Decisões importantes

- SQLite foi escolhido pela simplicidade operacional do bootstrap.
- SQLAlchemy 2.x fornece tipagem forte para os modelos.
- O LLM é opcional e desligado por padrão para manter o projeto executável sem dependências externas.
- O envelope padrão de resposta facilita consumo, tracing e tratamento de erro.
