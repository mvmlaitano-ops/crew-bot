"""Handlers do Telegram para o Gavi."""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from . import notion
from .crew.agents import AGENTES, DESAFIOS
from .capture.text import classify_tipo, classify_pilar, has_url, extract_urls
from .capture.text import classify_gosto_reacao, classify_pensamento_tipo
from .capture.voice import transcribe_telegram_voice
from .capture.links import extract_article, make_preview

logger = logging.getLogger(__name__)

TIPO_EMOJI = {
    "Ideia": "💡", "Tarefa": "📋", "Urgente": "🔥",
    "Pergunta": "❓", "Referencia": "📎",
}

# Reacoes validas para /gosto
REACOES_VALIDAS = {"bonito", "irritante", "genuino", "tendencia", "surpreendente"}


# ─── Comandos basicos ────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *Gavi Online.*\n\n"
        "Sou seu segundo cerebro. Tudo que voce mandar aqui eu capturo, classifico e guardo.\n\n"
        "*Captura rapida:*\n"
        "Texto livre → salvo no Inbox\n"
        "Audio → transcrito e salvo\n"
        "Link → artigo extraido e salvo\n\n"
        "*Pilares:*\n"
        "/gosto [reacao] [texto] — registro estetico\n"
        "/pensar [reflexao] — journal\n"
        "/fonte [url] [comentario] — referencia curada\n\n"
        "*CREW:*\n"
        "/ideia · /tarefa · /urgente · /ref\n"
        "/agente [nome] [msg] · /desafio\n"
        "/status · /ajuda",
        parse_mode="Markdown"
    )


async def cmd_ideia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Manda a ideia depois do /ideia")
        return
    saved = notion.add_to_inbox(text, "Ideia")
    await update.message.reply_text(
        f"{'💡' if saved else '📝'} Ideia registrada.\n_{text[:100]}_",
        parse_mode="Markdown"
    )


async def cmd_tarefa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Manda a tarefa depois do /tarefa")
        return
    saved = notion.add_to_inbox(text, "Tarefa")
    await update.message.reply_text(
        f"{'📋' if saved else '📝'} Tarefa registrada.\n_{text[:100]}_",
        parse_mode="Markdown"
    )


async def cmd_urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("O que e urgente?")
        return
    saved = notion.add_to_inbox(text, "Urgente")
    await update.message.reply_text(
        f"{'🔥' if saved else '📝'} URGENTE registrado.\n_{text[:100]}_",
        parse_mode="Markdown"
    )


async def cmd_ref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Manda o link depois do /ref")
        return
    # Tenta extrair artigo se tem URL
    urls = extract_urls(text)
    if urls:
        _save_fonte_from_url(urls[0], text)
        await update.message.reply_text(f"📎 Referencia salva e processando...\n_{text[:100]}_", parse_mode="Markdown")
    else:
        saved = notion.add_to_inbox(text, "Referencia")
        await update.message.reply_text(f"📎 Referencia salva.\n_{text[:100]}_", parse_mode="Markdown")


# ─── Comandos dos 3 pilares ─────────────────────────────────────────

async def cmd_gosto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/gosto [reacao] [comentario] — ex: /gosto bonito tipografia incrivel"""
    if not context.args:
        await update.message.reply_text(
            "🎨 *Como usar /gosto:*\n\n"
            "/gosto bonito [comentario]\n"
            "/gosto irritante [comentario]\n"
            "/gosto genuino [comentario]\n"
            "/gosto tendencia [comentario]\n"
            "/gosto surpreendente [comentario]\n\n"
            "Pode mandar com link tambem.",
            parse_mode="Markdown"
        )
        return

    reacao_raw = context.args[0].lower()
    comentario = " ".join(context.args[1:]) if len(context.args) > 1 else ""

    if reacao_raw not in REACOES_VALIDAS:
        # Trata tudo como comentario, detecta reacao automaticamente
        full_text = " ".join(context.args)
        reacao = classify_gosto_reacao(full_text)
        comentario = full_text
    else:
        reacao = reacao_raw.capitalize()

    if not comentario:
        await update.message.reply_text("Precisa de um comentario sobre o que voce viu.")
        return

    urls = extract_urls(comentario)
    fonte_url = urls[0] if urls else None

    saved = notion.add_to_gosto(comentario, reacao, fonte_url=fonte_url)
    await update.message.reply_text(
        f"🎨 Gosto registrado: *{reacao}*\n_{comentario[:100]}_",
        parse_mode="Markdown"
    )


async def cmd_pensar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pensar [reflexao] — salva no journal de pensamento."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "💭 *Como usar /pensar:*\n\n"
            "/pensar [sua reflexao]\n\n"
            "Tipos detectados automaticamente:\n"
            "• Filosofia — posicoes que voce defende\n"
            "• Provocacao — perguntas que incomodam\n"
            "• Observacao — algo que voce notou\n"
            "• Conexao — fios entre assuntos diferentes",
            parse_mode="Markdown"
        )
        return

    tipo = classify_pensamento_tipo(text)
    saved = notion.add_to_pensamento(text, tipo)
    await update.message.reply_text(
        f"💭 Pensamento registrado: *{tipo}*\n_{text[:100]}_",
        parse_mode="Markdown"
    )


async def cmd_fonte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/fonte [url] [comentario] — salva e extrai referencia."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "📚 *Como usar /fonte:*\n\n"
            "/fonte [url] [comentario opcional]\n\n"
            "O Gavi extrai titulo e resumo automaticamente.",
            parse_mode="Markdown"
        )
        return

    urls = extract_urls(text)
    if urls:
        url = urls[0]
        comentario = text.replace(url, "").strip()
        result = _save_fonte_from_url(url, comentario)
        if result:
            await update.message.reply_text(
                f"📚 Fonte salva: *{result}*\n_{comentario[:80] or 'Extraindo conteudo...'}_",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"📚 Fonte salva (sem extracao).\n_{text[:100]}_", parse_mode="Markdown")
    else:
        saved = notion.add_to_fontes(text)
        await update.message.reply_text(f"📚 Fonte salva.\n_{text[:100]}_", parse_mode="Markdown")


async def cmd_corpo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/corpo [registro] — placeholder pro pilar Corpo."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("🏋️ Manda o registro depois do /corpo\nEx: /corpo treinei pesado hoje")
        return
    saved = notion.add_to_inbox(f"[CORPO] {text}", "Ideia")
    await update.message.reply_text(
        f"🏋️ Registro corporal salvo no Inbox.\n_{text[:100]}_",
        parse_mode="Markdown"
    )


# ─── Comandos CREW ──────────────────────────────────────────────────

async def cmd_desafio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    linhas = ["🎯 *Desafios da Semana:*\n"]
    for key, (emoji, nome, _) in AGENTES.items():
        desafio = DESAFIOS.get(key, "—")
        linhas.append(f"{emoji} *{nome}*: {desafio}")
    await update.message.reply_text("\n".join(linhas), parse_mode="Markdown")


async def cmd_segunda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 *Planning Semanal — CREW*\n\n"
        "SEG → Desafio + Planning\n"
        "TER → SONDA pesquisa + LEME estrategia\n"
        "QUA → TINTA escreve + FORMA cria\n"
        "QUI → PULSO produz + publica\n"
        "SEX → LUPA review + showcase\n"
        "SAB → PULSO newsletter\n"
        "DOM → Descanso",
        parse_mode="Markdown"
    )


async def cmd_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 *Review Semanal*\nClaude analisa o progresso na proxima sessao Cowork.",
        parse_mode="Markdown"
    )


async def cmd_agente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        linhas = ["🤖 *Agentes CREW:*\n"]
        for key, (emoji, nome, desc) in AGENTES.items():
            linhas.append(f"{emoji} *{nome}* — {desc}")
        linhas.append("\nUse: /agente sonda [mensagem]")
        await update.message.reply_text("\n".join(linhas), parse_mode="Markdown")
        return

    agente_key = context.args[0].lower()
    if agente_key not in AGENTES:
        await update.message.reply_text(f"Agente '{agente_key}' nao existe.")
        return

    emoji, nome, desc = AGENTES[agente_key]
    msg = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    if msg:
        saved = notion.add_to_inbox(f"[{nome}] {msg}", "Tarefa", nome)
        await update.message.reply_text(
            f"{'✅' if saved else '📝'} Mensagem para *{nome}* registrada.\n_{msg[:100]}_",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"{emoji} *{nome}* — {desc}\n\nMande: /agente {agente_key} [sua mensagem]",
            parse_mode="Markdown"
        )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from . import config as cfg
    notion_ok = bool(cfg.NOTION_TOKEN and cfg.NOTION_INBOX_ID)
    gosto_ok = bool(cfg.NOTION_GOSTO_ID)
    pensamento_ok = bool(cfg.NOTION_PENSAMENTO_ID)
    fontes_ok = bool(cfg.NOTION_FONTES_ID)
    groq_ok = bool(cfg.GROQ_API_KEY)

    await update.message.reply_text(
        "📡 *Status Gavi*\n\n"
        f"Bot Telegram: 🟢 Online\n"
        f"Notion Inbox: {'🟢' if notion_ok else '🔴'}\n"
        f"Notion Gosto: {'🟢' if gosto_ok else '⚪'}\n"
        f"Notion Pensamento: {'🟢' if pensamento_ok else '⚪'}\n"
        f"Notion Fontes: {'🟢' if fontes_ok else '⚪'}\n"
        f"Groq Whisper: {'🟢' if groq_ok else '⚪'}\n"
        f"Claude Cowork: ⏸️ Aguardando sessao",
        parse_mode="Markdown"
    )


async def cmd_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Comandos Gavi:*\n\n"
        "*Captura:*\n"
        "Texto livre → auto-classifica e salva\n"
        "Audio → transcreve e salva\n"
        "/ideia · /tarefa · /urgente · /ref\n\n"
        "*Pilares:*\n"
        "/gosto [reacao] [texto]\n"
        "/pensar [reflexao]\n"
        "/fonte [url] [comentario]\n"
        "/corpo [registro]\n\n"
        "*CREW:*\n"
        "/agente [nome] [msg]\n"
        "/desafio · /segunda · /review\n"
        "/status",
        parse_mode="Markdown"
    )


# ─── Handler mensagens livres ────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Texto livre → classifica e salva no Notion."""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    tipo = classify_tipo(text)
    pilar = classify_pilar(text)

    # Se tem URL, tenta extrair e salvar como fonte
    urls = extract_urls(text)
    if urls and pilar == "Fontes":
        title = _save_fonte_from_url(urls[0], text.replace(urls[0], "").strip())
        if title:
            await update.message.reply_text(
                f"📚 Fonte capturada: *{title}*",
                parse_mode="Markdown"
            )
            return

    # Salva no pilar detectado ou no inbox
    if pilar == "Gosto":
        reacao = classify_gosto_reacao(text)
        saved = notion.add_to_gosto(text, reacao)
        await update.message.reply_text(f"🎨 Gosto capturado: *{reacao}*\n_{text[:80]}_", parse_mode="Markdown")
    elif pilar == "Pensamento":
        ptipo = classify_pensamento_tipo(text)
        saved = notion.add_to_pensamento(text, ptipo)
        await update.message.reply_text(f"💭 Pensamento capturado: *{ptipo}*\n_{text[:80]}_", parse_mode="Markdown")
    else:
        saved = notion.add_to_inbox(text, tipo)
        emoji = TIPO_EMOJI.get(tipo, "📝")
        status = "registrada no Notion" if saved else "recebido (Notion offline)"
        await update.message.reply_text(f"{emoji} *{tipo}* {status}.", parse_mode="Markdown")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Audio → transcreve via Groq Whisper → classifica e salva."""
    if not update.message or not update.message.voice:
        return

    voice = update.message.voice
    duration = voice.duration or 0

    await update.message.reply_text("🎙️ Transcrevendo...")

    text = await transcribe_telegram_voice(context.bot, voice.file_id)
    if not text:
        await update.message.reply_text("❌ Nao consegui transcrever. Tenta de novo?")
        return

    # Salva no inbox com marcacao de que veio de audio
    tipo = classify_tipo(text)
    saved = notion.add_to_inbox(f"[🎙️ {duration}s] {text}", tipo)

    preview = text[:150] + "..." if len(text) > 150 else text
    emoji = TIPO_EMOJI.get(tipo, "📝")
    await update.message.reply_text(
        f"🎙️ Transcrito e salvo como *{tipo}*:\n\n_{preview}_",
        parse_mode="Markdown"
    )


# ─── Helpers ─────────────────────────────────────────────────────────

def _save_fonte_from_url(url: str, comentario: str = "") -> str | None:
    """Extrai artigo da URL e salva no database Fontes. Retorna titulo ou None."""
    article = extract_article(url)
    if article:
        titulo = article["title"]
        resumo = make_preview(article)
        notion.add_to_fontes(titulo, url=url, resumo=resumo or comentario)
        return titulo
    else:
        # Fallback: salva so a URL
        notion.add_to_fontes(comentario or url, url=url)
        return None
