"""
Sends the daily job shortlist to Telegram.

Setup (one-time, do this yourself in the Telegram app):
1. Message @BotFather -> /newbot -> follow prompts -> copy the bot token.
2. Message your new bot anything at all (so it has a chat with you).
3. Visit https://api.telegram.org/bot<TOKEN>/getUpdates in a browser and
   read the chat id out of the JSON response ("chat": {"id": ...}).
Put both values in your .env as TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
"""

import logging

import httpx

from src.database.models import JobRecord

logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4096  # Telegram hard limit on a single message


def format_job_message(jobs: list[JobRecord], header: str = "🚀 DAILY UK GRADUATE JOB MATCHES") -> str:
    lines = [f"*{header}*\n"]
    for i, job in enumerate(jobs, start=1):
        lines.append(
            f"{i}. *{job.title}*\n"
            f"Company: {job.company or 'Not specified'}\n"
            f"Location: {job.location or 'Not specified'}\n"
            f"Salary: {job.salary or 'Not specified'}\n"
            f"Source: {job.source}\n"
            f"Apply: {job.url}\n"
        )
    return "\n".join(lines)


def _chunk_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    """Split a long message into Telegram-safe chunks, breaking on job
    boundaries (blank lines) rather than mid-sentence where possible."""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        if len(current) + len(block) + 2 > limit:
            chunks.append(current.strip())
            current = ""
        current += block + "\n\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    """
    Sends one Telegram message. Returns True on success, False on failure -
    a Telegram failure must never crash the whole daily pipeline (Excel
    export etc. should still complete), so we swallow errors here and just
    log + report success/failure to the caller.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        response = httpx.post(url, json=payload, timeout=15.0)
        response.raise_for_status()
        return True
    except httpx.HTTPError as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_daily_jobs(bot_token: str, chat_id: str, jobs: list[JobRecord]) -> bool:
    """Formats and sends the day's new jobs, splitting into multiple
    messages if the list is long enough to exceed Telegram's limit."""
    if not jobs:
        return send_telegram_message(
            bot_token, chat_id, "🚀 *DAILY UK GRADUATE JOB MATCHES*\n\nNo new jobs found today."
        )

    full_text = format_job_message(jobs)
    chunks = _chunk_message(full_text)

    all_sent = True
    for chunk in chunks:
        sent = send_telegram_message(bot_token, chat_id, chunk)
        all_sent = all_sent and sent
    return all_sent
