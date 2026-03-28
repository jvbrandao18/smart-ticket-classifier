from app.domain.enums import Category, Priority
from app.domain.rules import RuleEngine


def test_priority_conflict_prefers_critical_over_default_priority() -> None:
    evaluation = RuleEngine().evaluate(
        title="Login critico",
        description="Sistema parado para todos os usuarios, sem acesso ao portal e com senha rejeitada.",
        confidence_threshold=0.72,
    )

    assert evaluation.category == Category.ACESSO
    assert evaluation.priority == Priority.CRITICA


def test_priority_conflict_prefers_high_over_low_terms() -> None:
    evaluation = RuleEngine().evaluate(
        title="Solicitacao de melhoria com erro de timeout",
        description="O time abriu uma solicitacao, mas hoje existe erro de timeout no processo principal.",
        confidence_threshold=0.72,
    )

    assert evaluation.category == Category.INCIDENTE
    assert evaluation.priority == Priority.ALTA
