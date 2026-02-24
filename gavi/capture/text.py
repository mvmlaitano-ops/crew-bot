"""Classificacao de texto por regras heuristicas."""
from __future__ import annotations

import re

# Palavras-chave por pilar
_GOSTO_WORDS = [
    "bonito", "feio", "lindo", "horroroso", "irritante", "estetica", "estética",
    "design", "visual", "tipografia", "fonte", "paleta", "layout", "marca",
    "elegante", "generico", "genérico", "preguicoso", "preguiçoso", "surpreendente",
    "genuino", "genuíno", "tendencia", "tendência", "identidade visual",
]
_PENSAMENTO_WORDS = [
    "pensei", "acho que", "filosofia", "conexao", "conexão", "percebi",
    "reflexao", "reflexão", "posicao", "posição", "provocacao", "provocação",
    "observei", "notei", "defendo que", "acredito que", "minha tese",
]
_URGENTE_WORDS = ["urgente", "agora", "rapido", "rápido", "asap", "preciso agora", "já"]
_TAREFA_WORDS = ["fazer", "criar", "publicar", "entregar", "produzir", "escrever", "preparar"]
_PERGUNTA_STARTERS = ["como", "por que", "por quê", "quando", "onde", "qual", "quem", "o que"]

_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")


def has_url(text: str) -> bool:
    return bool(_URL_PATTERN.search(text))


def extract_urls(text: str) -> list[str]:
    return _URL_PATTERN.findall(text)


def classify_pilar(text: str) -> str | None:
    """Detecta pilar: Gosto, Pensamento, Fontes, ou None (fica no Inbox)."""
    lower = text.lower()
    if any(w in lower for w in _GOSTO_WORDS):
        return "Gosto"
    if any(w in lower for w in _PENSAMENTO_WORDS):
        return "Pensamento"
    if has_url(text):
        return "Fontes"
    return None


def classify_tipo(text: str) -> str:
    """Classifica tipo: Urgente, Referencia, Pergunta, Tarefa, ou Ideia."""
    lower = text.lower()
    if any(w in lower for w in _URGENTE_WORDS):
        return "Urgente"
    if has_url(text):
        return "Referencia"
    if text.strip().endswith("?") or any(lower.startswith(w) for w in _PERGUNTA_STARTERS):
        return "Pergunta"
    if any(w in lower for w in _TAREFA_WORDS):
        return "Tarefa"
    return "Ideia"


def classify_gosto_reacao(text: str) -> str:
    """Tenta detectar reacao estetica no texto."""
    lower = text.lower()
    if any(w in lower for w in ["bonito", "lindo", "elegante", "belo"]):
        return "Bonito"
    if any(w in lower for w in ["irritante", "feio", "horroroso", "preguicoso", "preguiçoso", "generico", "genérico"]):
        return "Irritante"
    if any(w in lower for w in ["genuino", "genuíno", "real", "verdade", "autêntico", "autentico"]):
        return "Genuino"
    if any(w in lower for w in ["tendencia", "tendência", "moda", "hype", "todo mundo"]):
        return "Tendencia"
    if any(w in lower for w in ["surpreendente", "inesperado", "pegou de guarda", "nao esperava", "não esperava"]):
        return "Surpreendente"
    return "Bonito"  # default


def classify_pensamento_tipo(text: str) -> str:
    """Tenta detectar tipo de pensamento."""
    lower = text.lower()
    if any(w in lower for w in ["defendo", "acredito", "posicao", "posição", "filosofia", "principio", "princípio"]):
        return "Filosofia"
    if any(w in lower for w in ["por que", "por quê", "incomoda", "provocacao", "provocação", "?"]):
        return "Provocacao"
    if any(w in lower for w in ["conexao", "conexão", "relacao", "relação", "fio", "cruza", "parece com"]):
        return "Conexao"
    return "Observacao"
