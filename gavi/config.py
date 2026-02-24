"""Configuracao central do Gavi."""

import os

# Telegram
BOT_TOKEN = os.environ.get("CREW_BOT_TOKEN", "")
MARCUS_CHAT_ID = 1006281052

# Notion
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_VERSION = "2022-06-28"

# Notion Database IDs
NOTION_INBOX_ID = os.environ.get("NOTION_INBOX_ID", "")
NOTION_GOSTO_ID = os.environ.get("NOTION_GOSTO_ID", "")
NOTION_PENSAMENTO_ID = os.environ.get("NOTION_PENSAMENTO_ID", "")
NOTION_FONTES_ID = os.environ.get("NOTION_FONTES_ID", "")

# Groq (Whisper transcription - free tier)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
