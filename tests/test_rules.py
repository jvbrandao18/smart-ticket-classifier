from app.domain.enums import Category, Priority
from app.domain.rules import RuleEngine


def test_rule_engine_matches_access_keywords() -> None:
    evaluation = RuleEngine().evaluate(
        title="Reset de senha sem acesso",
        description="Usuario sem acesso por permissao incorreta no portal.",
        confidence_threshold=0.72,
    )

    assert evaluation.category == Category.ACESSO
    assert evaluation.priority == Priority.MEDIA
    assert {"senha", "acesso", "permissao"} <= set(evaluation.matched_keywords)
    assert evaluation.llm_required is False


def test_rule_engine_normalizes_accents_for_automation_terms() -> None:
    evaluation = RuleEngine().evaluate(
        title="Robô de automação nao executou",
        description="O robô do financeiro nao processou o job agendado nesta madrugada.",
        confidence_threshold=0.72,
    )

    assert evaluation.category == Category.AUTOMACAO
    assert evaluation.suggested_queue == "squad-automacoes"
    assert "robo" in evaluation.matched_keywords
