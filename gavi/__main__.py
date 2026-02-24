"""Entry point: python -m gavi"""

import sys
import asyncio
import time
import logging

from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from . import config
from . import bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("gavi")


def main():
    if not config.BOT_TOKEN:
        logger.error("CREW_BOT_TOKEN nao definido.")
        sys.exit(1)

    # Limpa webhook anterior
    async def cleanup():
        b = Bot(token=config.BOT_TOKEN)
        async with b:
            await b.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deletado.")

    asyncio.run(cleanup())
    time.sleep(5)

    app = Application.builder().token(config.BOT_TOKEN).build()

    # Comandos basicos
    app.add_handler(CommandHandler("start", bot.cmd_start))
    app.add_handler(CommandHandler("ideia", bot.cmd_ideia))
    app.add_handler(CommandHandler("tarefa", bot.cmd_tarefa))
    app.add_handler(CommandHandler("urgente", bot.cmd_urgente))
    app.add_handler(CommandHandler("ref", bot.cmd_ref))

    # Pilares
    app.add_handler(CommandHandler("gosto", bot.cmd_gosto))
    app.add_handler(CommandHandler("pensar", bot.cmd_pensar))
    app.add_handler(CommandHandler("fonte", bot.cmd_fonte))
    app.add_handler(CommandHandler("corpo", bot.cmd_corpo))

    # CREW
    app.add_handler(CommandHandler("desafio", bot.cmd_desafio))
    app.add_handler(CommandHandler("segunda", bot.cmd_segunda))
    app.add_handler(CommandHandler("review", bot.cmd_review))
    app.add_handler(CommandHandler("agente", bot.cmd_agente))
    app.add_handler(CommandHandler("status", bot.cmd_status))
    app.add_handler(CommandHandler("ajuda", bot.cmd_ajuda))

    # Handlers para conteudo livre
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, bot.handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))

    logger.info("Gavi v3.0 iniciado — Segundo Cerebro")
    logger.info(f"  Notion Inbox: {'OK' if config.NOTION_INBOX_ID else 'N/A'}")
    logger.info(f"  Notion Gosto: {'OK' if config.NOTION_GOSTO_ID else 'N/A'}")
    logger.info(f"  Notion Pensamento: {'OK' if config.NOTION_PENSAMENTO_ID else 'N/A'}")
    logger.info(f"  Notion Fontes: {'OK' if config.NOTION_FONTES_ID else 'N/A'}")
    logger.info(f"  Groq Whisper: {'OK' if config.GROQ_API_KEY else 'N/A'}")

    app.run_polling(drop_pending_updates=True, poll_interval=2.0, timeout=10)


# CLI para envio programatico
async def _send(chat_id, text):
    b = Bot(token=config.BOT_TOKEN)
    async with b:
        await b.send_message(chat_id=int(chat_id), text=text, parse_mode="Markdown")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        chat_id = sys.argv[2] if len(sys.argv) > 2 else str(config.MARCUS_CHAT_ID)

        if action == "send-msg":
            msg = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "Teste Gavi"
            asyncio.run(_send(chat_id, msg))
        else:
            print(f"Acao desconhecida: {action}")
            print("Uso: python -m gavi send-msg CHAT_ID texto")
    else:
        main()
