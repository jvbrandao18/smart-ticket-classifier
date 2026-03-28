from dataclasses import dataclass
import unicodedata

from app.domain.enums import Category, Priority


@dataclass(frozen=True)
class KeywordRule:
    category: Category
    keywords: tuple[str, ...]
    probable_root_cause: str
    suggested_queue: str
    default_priority: Priority


@dataclass(frozen=True)
class RuleEvaluation:
    category: Category
    priority: Priority
    probable_root_cause: str
    suggested_queue: str
    confidence_score: float
    summary_justification: str
    matched_keywords: tuple[str, ...]
    llm_required: bool


PRIORITY_RANK: dict[Priority, int] = {
    Priority.BAIXA: 1,
    Priority.MEDIA: 2,
    Priority.ALTA: 3,
    Priority.CRITICA: 4,
}


KEYWORD_RULES: tuple[KeywordRule, ...] = (
    KeywordRule(
        category=Category.ACESSO,
        keywords=("acesso", "senha", "permissao", "login"),
        probable_root_cause="Credencial expirada ou permissao inconsistente.",
        suggested_queue="service-desk-acessos",
        default_priority=Priority.MEDIA,
    ),
    KeywordRule(
        category=Category.INCIDENTE,
        keywords=("indisponivel", "timeout", "erro", "falha"),
        probable_root_cause="Falha operacional ou indisponibilidade do servico.",
        suggested_queue="noc-aplicacoes",
        default_priority=Priority.ALTA,
    ),
    KeywordRule(
        category=Category.INTEGRACAO,
        keywords=("integracao", "api", "webhook", "sincronizacao"),
        probable_root_cause="Quebra na comunicacao entre sistemas integrados.",
        suggested_queue="squad-integracoes",
        default_priority=Priority.ALTA,
    ),
    KeywordRule(
        category=Category.DADOS,
        keywords=("dashboard", "dados", "relatorio", "base"),
        probable_root_cause="Inconsistencia, atraso ou ausencia de dados.",
        suggested_queue="analytics-ops",
        default_priority=Priority.MEDIA,
    ),
    KeywordRule(
        category=Category.AUTOMACAO,
        keywords=("robo", "automacao", "bot", "job"),
        probable_root_cause="Falha em rotina automatizada ou job agendado.",
        suggested_queue="squad-automacoes",
        default_priority=Priority.MEDIA,
    ),
)


CRITICAL_TERMS = ("critico", "urgente", "parado", "fora do ar", "todos os usuarios")
HIGH_TERMS = ("indisponivel", "timeout", "falha", "erro")
LOW_TERMS = ("solicitacao", "ajuste", "melhoria", "duvida")


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    stripped = "".join(character for character in normalized if not unicodedata.combining(character))
    return stripped.lower()


class RuleEngine:
    def evaluate(self, *, title: str, description: str, confidence_threshold: float) -> RuleEvaluation:
        combined_text = normalize_text(f"{title} {description}")
        ranked_matches = self._rank_matches(combined_text)
        if ranked_matches:
            selected_rule, matched_keywords = ranked_matches[0]
            confidence_score = self._calculate_confidence(matched_keywords, len(ranked_matches))
            priority = self._detect_priority(combined_text, selected_rule.default_priority)
            justification = self._build_justification(selected_rule.category, matched_keywords)
            return RuleEvaluation(
                category=selected_rule.category,
                priority=priority,
                probable_root_cause=selected_rule.probable_root_cause,
                suggested_queue=selected_rule.suggested_queue,
                confidence_score=confidence_score,
                summary_justification=justification,
                matched_keywords=matched_keywords,
                llm_required=confidence_score < confidence_threshold,
            )

        return RuleEvaluation(
            category=Category.SOLICITACAO,
            priority=self._detect_priority(combined_text, Priority.BAIXA),
            probable_root_cause="Solicitacao generica sem indicios fortes de incidente.",
            suggested_queue="service-desk-geral",
            confidence_score=0.42,
            summary_justification="Nenhuma palavra-chave forte foi encontrada nas regras deterministicas.",
            matched_keywords=tuple(),
            llm_required=True,
        )

    def _rank_matches(self, text: str) -> list[tuple[KeywordRule, tuple[str, ...]]]:
        matches: list[tuple[KeywordRule, tuple[str, ...]]] = []
        for rule in KEYWORD_RULES:
            matched_keywords = tuple(keyword for keyword in rule.keywords if keyword in text)
            if matched_keywords:
                matches.append((rule, matched_keywords))

        matches.sort(
            key=lambda item: (
                len(item[1]),
                PRIORITY_RANK[item[0].default_priority],
            ),
            reverse=True,
        )
        return matches

    def _calculate_confidence(
        self,
        matched_keywords: tuple[str, ...],
        total_matches: int,
    ) -> float:
        confidence = 0.58 + (len(matched_keywords) * 0.12)
        if total_matches > 1:
            confidence -= 0.05
        return max(0.35, min(confidence, 0.96))

    def _detect_priority(self, text: str, default_priority: Priority) -> Priority:
        if any(term in text for term in CRITICAL_TERMS):
            return Priority.CRITICA
        if any(term in text for term in HIGH_TERMS):
            return max_priority(default_priority, Priority.ALTA)
        if any(term in text for term in LOW_TERMS):
            return max_priority(default_priority, Priority.BAIXA)
        return default_priority

    def _build_justification(
        self,
        category: Category,
        matched_keywords: tuple[str, ...],
    ) -> str:
        keywords = ", ".join(matched_keywords)
        return f"Categoria {category.value} sugerida pelas palavras-chave: {keywords}."


def max_priority(left: Priority, right: Priority) -> Priority:
    if PRIORITY_RANK[left] >= PRIORITY_RANK[right]:
        return left
    return right
