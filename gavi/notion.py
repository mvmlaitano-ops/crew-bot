"""Cliente Notion API para o Gavi."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from . import config

logger = logging.getLogger(__name__)

NOTION_API = "https://api.notion.com/v1"


def _headers():
    return {
        "Authorization": f"Bearer {config.NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": config.NOTION_VERSION,
    }


def _post(endpoint: str, payload: dict) -> dict | None:
    """POST generico para Notion API. Retorna response body ou None."""
    url = f"{NOTION_API}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    try:
        req = Request(url, data=data, headers=_headers(), method="POST")
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            result = json.loads(body)
            logger.info(f"Notion {endpoint}: {resp.status}")
            return result
    except Exception as e:
        error_msg = str(e)
        # Extrair body do erro HTTP pra diagnostico
        if hasattr(e, 'read'):
            try:
                error_body = e.read().decode()
                error_msg = f"{e} | body: {error_body[:300]}"
            except Exception:
                pass
        if hasattr(e, 'code'):
            if e.code == 401:
                logger.error(f"Notion 401 UNAUTHORIZED — Token invalido ou expirado! Token prefix: {config.NOTION_TOKEN[:12]}...")
            elif e.code == 404:
                logger.error(f"Notion 404 — Database nao encontrado ou integracao sem acesso. DB ID no payload: {json.dumps(payload.get('parent', {}))}")
            elif e.code == 400:
                logger.error(f"Notion 400 — Payload invalido: {error_msg}")
            else:
                logger.error(f"Notion {endpoint} HTTP {e.code}: {error_msg}")
        else:
            logger.error(f"Notion {endpoint} erro: {error_msg}")
        return None


def check_connection() -> bool:
    """Testa se o token Notion esta valido. Chamado no startup."""
    if not config.NOTION_TOKEN:
        logger.warning("NOTION_TOKEN nao definido.")
        return False

    try:
        from urllib.request import Request, urlopen
        req = Request(f"{NOTION_API}/users/me", headers=_headers())
        with urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            bot_name = body.get("name", "?")
            logger.info(f"Notion conectado! Bot: {bot_name}")
            return True
    except Exception as e:
        code = getattr(e, 'code', '?')
        logger.error(f"Notion token INVALIDO (HTTP {code}). Regenere em notion.so/profile/integrations")
        return False


def add_to_inbox(text: str, msg_type: str = "Ideia", agente: str = None) -> bool:
    """Salva mensagem no Inbox (database Ideias)."""
    if not config.NOTION_TOKEN or not config.NOTION_INBOX_ID:
        logger.warning("Notion nao configurado.")
        return False

    properties = {
        "Mensagem": {"title": [{"text": {"content": text[:2000]}}]},
        "Tipo": {"select": {"name": msg_type}},
        "Status": {"select": {"name": "Novo"}},
        "Data": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
    }
    if agente:
        properties["Agente"] = {"select": {"name": agente}}

    result = _post("pages", {"parent": {"database_id": config.NOTION_INBOX_ID}, "properties": properties})
    if result and result.get("id"):
        logger.info(f"Inbox: {text[:50]}...")
        return True
    return False


def add_to_gosto(entrada: str, reacao: str, categoria: str = None,
                 fonte_url: str = None, comentario: str = None) -> bool:
    """Salva entrada no database Gosto."""
    if not config.NOTION_GOSTO_ID:
        logger.warning("NOTION_GOSTO_ID nao configurado. Salvando no Inbox.")
        return add_to_inbox(f"[GOSTO/{reacao}] {entrada}", "Ideia")

    properties = {
        "Entrada": {"title": [{"text": {"content": entrada[:2000]}}]},
        "Reacao": {"select": {"name": reacao}},
        "Data": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
    }
    if categoria:
        properties["Categoria"] = {"select": {"name": categoria}}
    if fonte_url:
        properties["Fonte"] = {"url": fonte_url}
    if comentario:
        properties["Comentario"] = {"rich_text": [{"text": {"content": comentario[:2000]}}]}

    result = _post("pages", {"parent": {"database_id": config.NOTION_GOSTO_ID}, "properties": properties})
    return bool(result and result.get("id"))


def add_to_pensamento(entrada: str, tipo: str = "Observacao", tags: list[str] = None) -> bool:
    """Salva entrada no database Pensamento."""
    if not config.NOTION_PENSAMENTO_ID:
        logger.warning("NOTION_PENSAMENTO_ID nao configurado. Salvando no Inbox.")
        return add_to_inbox(f"[PENSAMENTO/{tipo}] {entrada}", "Ideia")

    properties = {
        "Entrada": {"title": [{"text": {"content": entrada[:2000]}}]},
        "Tipo": {"select": {"name": tipo}},
        "Data": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
    }
    if tags:
        properties["Tags"] = {"multi_select": [{"name": t} for t in tags[:5]]}

    result = _post("pages", {"parent": {"database_id": config.NOTION_PENSAMENTO_ID}, "properties": properties})
    return bool(result and result.get("id"))


def add_to_fontes(titulo: str, url: str = None, resumo: str = None,
                  tipo: str = "Artigo", tags: list[str] = None,
                  relevancia: str = "Util") -> bool:
    """Salva entrada no database Fontes."""
    if not config.NOTION_FONTES_ID:
        logger.warning("NOTION_FONTES_ID nao configurado. Salvando no Inbox.")
        return add_to_inbox(f"[FONTE] {titulo} {url or ''}", "Referencia")

    properties = {
        "Titulo": {"title": [{"text": {"content": titulo[:2000]}}]},
        "Tipo": {"select": {"name": tipo}},
        "Relevancia": {"select": {"name": relevancia}},
        "Data": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
    }
    if url:
        properties["Fonte"] = {"url": url}
    if resumo:
        properties["Resumo"] = {"rich_text": [{"text": {"content": resumo[:2000]}}]}
    if tags:
        properties["Tags"] = {"multi_select": [{"name": t} for t in tags[:5]]}

    result = _post("pages", {"parent": {"database_id": config.NOTION_FONTES_ID}, "properties": properties})
    return bool(result and result.get("id"))
