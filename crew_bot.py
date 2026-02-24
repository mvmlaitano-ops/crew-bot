#!/usr/bin/env python3
"""
CREW Bot — Telegram + Notion Integration (Gaví System)
Bot que conecta Marcus ao CREW via Telegram, salvando mensagens no Notion
para que o Claude processe e tome decisões.
"""

import os
import sys
import json
import asyncio
import time
import logging
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Config
BOT_TOKEN = os.environ.get("CREW_BOT_TOKEN", "")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_INBOX_ID = os.environ.get("NOTION_INBOX_ID", "")
MARCUS_CHAT_ID = 1006281052

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Notion Helper
def notion_add_message(message_text, msg_type="Ideia", agente=None):
    if not NOTION_TOKEN or not NOTION_INBOX_ID:
        logger.warning("Notion nao configurado.")
        return False
    url = "https://api.notion.com/v1/pages"
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
    properties = {
        "Mensagem": {"title": [{"text": {"content": message_text[:2000]}}]},
        "Tipo": {"select": {"name": msg_type}},
        "Status": {"select": {"name": "Novo"}},
        "Data": {"date": {"start": datetime.now(timezone.utc).isoformat()}}
    }
    if agente:
        properties["Agente"] = {"select": {"name": agente}}
    payload = json.dumps({"parent": {"database_id": NOTION_INBOX_ID}, "properties": properties}).encode("utf-8")
    try:
        req = Request(url, data=payload, headers=headers, method="POST")
        with urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                logger.info(f"Mensagem salva no Notion: {message_text[:50]}...")
                return True
    except Exception as e:
        logger.error(f"Erro ao salvar no Notion: {e}")
    return False

# Agentes
AGENTES = {
    "sonda": ("🔬", "SONDA", "Pesquisador"),
    "leme": ("🧭", "LEME", "Estrategista"),
    "tinta": ("✒️", "TINTA", "Redator"),
    "forma": ("🎨", "FORMA", "Designer"),
    "pulso": ("⚡", "PULSO", "Produtor"),
    "lupa": ("🔍", "LUPA", "Critico"),
}

DESAFIOS = {
    "sonda": "O Dado Invisivel",
    "leme": "6 Palavras",
    "tinta": "A Primeira Frase",
    "forma": "Marca em 60 Minutos",
    "pulso": "Conteudo Relampago",
    "lupa": "Destrua Isso",
}

# Comandos
async def cmd_start(update, context):
    await update.message.reply_text("⚡ *CREW Online.*\n\nTudo que voce mandar aqui vai pro Notion. Claude processa e agentes executam.\n\n/ideia — registra ideia\n/tarefa — registra tarefa\n/urgente — marca urgente\n/ref — salva referencia\n/agente [nome] [msg] — fala com agente\n/desafio — desafios da semana\n/status — status do sistema\n/ajuda — todos os comandos", parse_mode="Markdown")

async def cmd_ideia(update, context):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Manda a ideia depois do /ideia")
        return
    saved = notion_add_message(text, "Ideia")
    emoji = "✅" if saved else "📝"
    await update.message.reply_text(f"{emoji} Ideia registrada.\n_{text[:100]}_", parse_mode="Markdown")

async def cmd_tarefa(update, context):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Manda a tarefa depois do /tarefa")
        return
    saved = notion_add_message(text, "Tarefa")
    emoji = "✅" if saved else "📝"
    await update.message.reply_text(f"{emoji} Tarefa registrada.\n_{text[:100]}_", parse_mode="Markdown")

async def cmd_urgente(update, context):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("O que e urgente? Manda depois do /urgente")
        return
    saved = notion_add_message(text, "Urgente")
    emoji = "🔥" if saved else "📝"
    await update.message.reply_text(f"{emoji} URGENTE registrado.\n_{text[:100]}_", parse_mode="Markdown")

async def cmd_ref(update, context):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Manda o link depois do /ref")
        return
    saved = notion_add_message(text, "Referencia")
    emoji = "📎" if saved else "📝"
    await update.message.reply_text(f"{emoji} Referencia salva.\n_{text[:100]}_", parse_mode="Markdown")

async def cmd_desafio(update, context):
    linhas = ["🎯 *Desafios da Semana:*\n"]
    for key, (emoji, nome, _) in AGENTES.items():
        desafio = DESAFIOS.get(key, "—")
        linhas.append(f"{emoji} *{nome}*: {desafio}")
    await update.message.reply_text("\n".join(linhas), parse_mode="Markdown")

async def cmd_segunda(update, context):
    await update.message.reply_text("📅 *Planning Semanal — CREW*\n\nSEG → Desafio + Planning\nTER → SONDA pesquisa + LEME estrategia\nQUA → TINTA escreve + FORMA cria\nQUI → PULSO produz + publica\nSEX → LUPA review + showcase\nSAB → PULSO newsletter\nDOM → Descanso", parse_mode="Markdown")

async def cmd_review(update, context):
    await update.message.reply_text("📊 *Review Semanal*\n\nClaude analisa o progresso na proxima sessao.", parse_mode="Markdown")

async def cmd_agente(update, context):
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
        saved = notion_add_message(f"[{nome}] {msg}", "Tarefa", nome)
        emoji2 = "✅" if saved else "📝"
        await update.message.reply_text(f"{emoji2} Mensagem para *{nome}* registrada.\n_{msg[:100]}_", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"{emoji} *{nome}* — {desc}\n\nMande: /agente {agente_key} [sua mensagem]", parse_mode="Markdown")

async def cmd_status(update, context):
    notion_status = "🟢 Conectado" if (NOTION_TOKEN and NOTION_INBOX_ID) else "🔴 Nao configurado"
    await update.message.reply_text(f"📡 *Status CREW*\n\nBot Telegram: 🟢 Online\nNotion Inbox: {notion_status}\nClaude Cowork: ⏸️ Aguardando sessao", parse_mode="Markdown")

async def cmd_ajuda(update, context):
    await update.message.reply_text("📖 *Comandos CREW:*\n\nQualquer mensagem → salva como ideia\n/ideia [texto]\n/tarefa [texto]\n/urgente [texto]\n/ref [link]\n/agente [nome] [msg]\n/desafio\n/segunda\n/review\n/status", parse_mode="Markdown")

# Handler mensagens livres
async def handle_message(update, context):
    if not update.message or not update.message.text:
        return
    text = update.message.text
    if any(w in text.lower() for w in ["urgente", "agora", "rapido", "asap"]):
        msg_type = "Urgente"
    elif any(w in text.lower() for w in ["http", "www", ".com", "link"]):
        msg_type = "Referencia"
    elif text.endswith("?"):
        msg_type = "Pergunta"
    else:
        msg_type = "Ideia"
    saved = notion_add_message(text, msg_type)
    tipos = {"Ideia": "💡", "Tarefa": "📋", "Urgente": "🔥", "Pergunta": "❓", "Referencia": "📎"}
    emoji = tipos.get(msg_type, "📝")
    if saved:
        await update.message.reply_text(f"{emoji} *{msg_type}* registrada no Notion.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"{emoji} Recebido. (Notion offline)", parse_mode="Markdown")

# Envio programatico
async def enviar_desafio_semanal(chat_id):
    bot = Bot(token=BOT_TOKEN)
    linhas = ["🎯 *Desafios da Semana:*\n"]
    for key, (emoji, nome, _) in AGENTES.items():
        desafio = DESAFIOS.get(key, "—")
        linhas.append(f"{emoji} *{nome}*: {desafio}")
    async with bot:
        await bot.send_message(chat_id=int(chat_id), text="\n".join(linhas), parse_mode="Markdown")

async def enviar_planning(chat_id):
    bot = Bot(token=BOT_TOKEN)
    async with bot:
        await bot.send_message(chat_id=int(chat_id), text="📅 *Bom dia, Marcus.* Semana nova na CREW. Manda /segunda.", parse_mode="Markdown")

async def enviar_review(chat_id):
    bot = Bot(token=BOT_TOKEN)
    async with bot:
        await bot.send_message(chat_id=int(chat_id), text="📊 *Review time.* Manda /review.", parse_mode="Markdown")

async def enviar_mensagem(chat_id, texto):
    bot = Bot(token=BOT_TOKEN)
    async with bot:
        await bot.send_message(chat_id=int(chat_id), text=texto, parse_mode="Markdown")

# Main
def main():
    async def cleanup_and_start():
        bot = Bot(token=BOT_TOKEN)
        async with bot:
            await bot.delete_webhook(drop_pending_updates=True)
            print("Webhook deletado, aguardando 30s...")
    asyncio.run(cleanup_and_start())
    time.sleep(30)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ideia", cmd_ideia))
    app.add_handler(CommandHandler("tarefa", cmd_tarefa))
    app.add_handler(CommandHandler("urgente", cmd_urgente))
    app.add_handler(CommandHandler("ref", cmd_ref))
    app.add_handler(CommandHandler("desafio", cmd_desafio))
    app.add_handler(CommandHandler("segunda", cmd_segunda))
    app.add_handler(CommandHandler("review", cmd_review))
    app.add_handler(CommandHandler("agente", cmd_agente))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("ajuda", cmd_ajuda))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("CREW Bot v2.0 iniciado — Gavi System")
    print(f"Notion: {'Conectado' if NOTION_TOKEN else 'Nao configurado'}")
    app.run_polling(drop_pending_updates=True, poll_interval=2.0, timeout=10)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        chat_id = sys.argv[2] if len(sys.argv) > 2 else str(MARCUS_CHAT_ID)
        if action == "send-desafio":
            asyncio.run(enviar_desafio_semanal(chat_id))
        elif action == "send-planning":
            asyncio.run(enviar_planning(chat_id))
        elif action == "send-review":
            asyncio.run(enviar_review(chat_id))
        elif action == "send-msg":
            msg = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "Teste CREW"
            asyncio.run(enviar_mensagem(chat_id, msg))
    else:
        main()