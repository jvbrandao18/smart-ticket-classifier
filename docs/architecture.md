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
4. O LLM passa por validação estrita de schema, retry controlado e fallback para regras em caso de erro.
5. O `ClassificationService` consolida a decisão final e monta o `decision_trace`.
6. O ticket é persistido na tabela `tickets`.
7. A trilha de auditoria é persistida na tabela `audit_logs`.
8. A API retorna um envelope JSON padronizado com os dados da decisão.

## Explainability

Cada resposta de classificação inclui `decision_trace`, uma trilha textual resumida da decisão final. Isso complementa a auditoria técnica persistida e facilita demonstrações de portfólio, debugging e revisão humana.

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
- tempo de processamento
- uso e latência do fallback por LLM
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

## Métricas

O endpoint `/metrics` consolida:

- volume total de tickets
- volume total de auditoria
- distribuição por categoria e prioridade
- média de `confidence_score`
- latência média de processamento
- taxa de tentativa de LLM
- taxa efetiva de fallback por LLM

## Decisões importantes

- SQLite foi escolhido pela simplicidade operacional do bootstrap.
- SQLAlchemy 2.x fornece tipagem forte para os modelos.
- O LLM é opcional e desligado por padrão para manter o projeto executável sem dependências externas.
- Regras + LLM reduzem custo, preservam previsibilidade e melhoram cobertura em casos ambíguos.
- O score de confiança desta V1 é heurístico e explicitamente documentado.

## Limitações

- Não há migrations nesta versão.
- Não há autenticação/autorização.
- O dataset de exemplo é sintético.
- As métricas não estão no formato Prometheus.
