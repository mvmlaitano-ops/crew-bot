"""Transcricao de audio via Groq Whisper (free tier)."""

import io
import json
import logging
import tempfile
from urllib.request import Request, urlopen

from .. import config

logger = logging.getLogger(__name__)

GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


async def transcribe_telegram_voice(bot, file_id: str) -> str | None:
    """Baixa audio do Telegram e transcreve via Groq Whisper.

    Args:
        bot: instancia do telegram.Bot
        file_id: file_id do voice message no Telegram

    Returns:
        Texto transcrito ou None se falhou.
    """
    if not config.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY nao configurado. Transcricao desativada.")
        return None

    try:
        # Baixar arquivo do Telegram
        tg_file = await bot.get_file(file_id)
        audio_bytes = await tg_file.download_as_bytearray()
        logger.info(f"Audio baixado: {len(audio_bytes)} bytes")

        # Enviar para Groq Whisper (multipart/form-data)
        text = _send_to_groq(bytes(audio_bytes), "audio.ogg")
        if text:
            logger.info(f"Transcricao: {text[:80]}...")
        return text

    except Exception as e:
        logger.error(f"Erro na transcricao: {e}")
        return None


def _send_to_groq(audio_data: bytes, filename: str) -> str | None:
    """Envia audio para Groq Whisper API via multipart/form-data."""
    boundary = "----GaviBoundary"

    # Montar multipart body
    body = io.BytesIO()

    # Campo: model
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="model"\r\n\r\n')
    body.write(b"whisper-large-v3\r\n")

    # Campo: language
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="language"\r\n\r\n')
    body.write(b"pt\r\n")

    # Campo: file
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.write(b"Content-Type: audio/ogg\r\n\r\n")
    body.write(audio_data)
    body.write(b"\r\n")

    # Fim
    body.write(f"--{boundary}--\r\n".encode())
    body_bytes = body.getvalue()

    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    try:
        req = Request(GROQ_TRANSCRIPTION_URL, data=body_bytes, headers=headers, method="POST")
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result.get("text", "").strip() or None
    except Exception as e:
        logger.error(f"Groq Whisper erro: {e}")
        return None
