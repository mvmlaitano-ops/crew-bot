"""Extracao de conteudo de URLs via trafilatura."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def extract_article(url: str) -> dict | None:
    """Extrai titulo e conteudo principal de uma URL.

    Returns:
        dict com keys: title, text, author (ou None se falhou)
    """
    try:
        from trafilatura import fetch_url, extract, bare_extraction

        downloaded = fetch_url(url)
        if not downloaded:
            logger.warning(f"Nao conseguiu baixar: {url}")
            return None

        result = bare_extraction(downloaded, url=url, include_links=False)
        if not result:
            logger.warning(f"Nao conseguiu extrair: {url}")
            return None

        return {
            "title": result.get("title", "").strip() or url,
            "text": (result.get("text", "") or "")[:3000],
            "author": result.get("author", ""),
        }

    except ImportError:
        logger.warning("trafilatura nao instalado. Extração desativada.")
        return None
    except Exception as e:
        logger.error(f"Erro ao extrair {url}: {e}")
        return None


def make_preview(article: dict, max_len: int = 200) -> str:
    """Gera preview curto do artigo."""
    text = article.get("text", "")
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "..."
    return text
