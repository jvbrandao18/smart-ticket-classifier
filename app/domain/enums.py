from enum import StrEnum


class Category(StrEnum):
    INCIDENTE = "incidente"
    SOLICITACAO = "solicitacao"
    ACESSO = "acesso"
    INTEGRACAO = "integracao"
    DADOS = "dados"
    AUTOMACAO = "automacao"


class Priority(StrEnum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

