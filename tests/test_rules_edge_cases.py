from app.domain.enums import Category, Priority
from app.domain.rules import RuleEngine


def test_rule_engine_falls_back_to_solicitacao_without_keywords() -> None:
    evaluation = RuleEngine().evaluate(
        title="Ajuste cadastral",
        description="Solicitacao de melhoria para revisao de cadastro e processo interno.",
        confidence_threshold=0.72,
    )

    assert evaluation.category == Category.SOLICITACAO
    assert evaluation.priority == Priority.BAIXA
    assert evaluation.llm_required is True


def test_rule_engine_prefers_integration_when_multiple_keywords_match() -> None:
    evaluation = RuleEngine().evaluate(
        title="Timeout na integracao da API",
        description="A integracao via API apresenta timeout intermitente desde a madrugada.",
        confidence_threshold=0.72,
    )

    assert evaluation.category == Category.INTEGRACAO
    assert evaluation.priority == Priority.ALTA
    assert {"integracao", "api"} <= set(evaluation.matched_keywords)


def test_rule_engine_detects_critical_priority_terms() -> None:
    evaluation = RuleEngine().evaluate(
        title="Acesso critico ao portal",
        description="Todos os usuarios estao parados e sem acesso apos a troca de senha.",
        confidence_threshold=0.72,
    )

    assert evaluation.category == Category.ACESSO
    assert evaluation.priority == Priority.CRITICA


def test_rule_engine_requests_llm_when_categories_compete() -> None:
    evaluation = RuleEngine().evaluate(
        title="Erro no dashboard e na integracao",
        description="O dashboard mostra erro depois da integracao via API falhar na sincronizacao.",
        confidence_threshold=0.9,
    )

    assert evaluation.category == Category.INTEGRACAO
    assert evaluation.llm_required is True
    assert evaluation.confidence_score < 0.9
