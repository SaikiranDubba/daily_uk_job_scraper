"""
The actual daily pipeline: fetch jobs from Adzuna + Reed, store new ones in
SQLite (deduplicated), then send today's not-yet-notified jobs to Telegram.

Run manually:
    python main.py

Run automatically every day via GitHub Actions - see
.github/workflows/daily-job-run.yml
"""

import logging
import os

from dotenv import load_dotenv

from src.database.models import get_session, init_db
from src.database.repository import get_unnotified_jobs, mark_as_notified, save_new_jobs
from src.scraper.adzuna_source import fetch_adzuna_jobs
from src.scraper.reed_source import fetch_reed_jobs
from src.telegram.notifier import send_daily_jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/app.log")],
)
logger = logging.getLogger(__name__)

load_dotenv()

ADZUNA_APP_ID = os.environ["ADZUNA_APP_ID"]
ADZUNA_APP_KEY = os.environ["ADZUNA_APP_KEY"]
REED_API_KEY = os.environ["REED_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SEARCH_TERMS = [
    "graduate software engineer",
    "graduate developer",
    "qa engineer",
    "test automation",
    "software tester",
    "graduate scheme technology",
]

# How many of today's new jobs to actually push to Telegram, so a huge
# search day doesn't flood you with 40 messages.
MAX_JOBS_PER_TELEGRAM_MESSAGE = 10


def fetch_all_sources() -> list:
    all_jobs = []
    for term in SEARCH_TERMS:
        try:
            adzuna_jobs = fetch_adzuna_jobs(ADZUNA_APP_ID, ADZUNA_APP_KEY, keywords=term)
            all_jobs.extend(adzuna_jobs)
        except Exception as e:
            logger.error(f"Adzuna fetch failed for '{term}': {e}")

        try:
            reed_jobs = fetch_reed_jobs(REED_API_KEY, keywords=term)
            all_jobs.extend(reed_jobs)
        except Exception as e:
            logger.error(f"Reed fetch failed for '{term}': {e}")

    return all_jobs


def main() -> None:
    logger.info("Starting daily job pipeline run")

    engine = init_db("data/jobs.db")
    session = get_session(engine)

    raw_jobs = fetch_all_sources()
    logger.info(f"Fetched {len(raw_jobs)} total raw results across all sources/terms")

    new_jobs = save_new_jobs(session, raw_jobs)
    logger.info(f"{len(new_jobs)} of those were genuinely new and saved to the database")

    to_notify = get_unnotified_jobs(session, limit=MAX_JOBS_PER_TELEGRAM_MESSAGE)
    logger.info(f"Sending {len(to_notify)} jobs to Telegram")

    sent_ok = send_daily_jobs(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, to_notify)
    if sent_ok:
        mark_as_notified(session, to_notify)
        logger.info("Telegram send succeeded, jobs marked as notified")
    else:
        logger.warning("Telegram send failed - jobs left un-notified, will retry next run")

    session.close()
    logger.info("Pipeline run complete")


if __name__ == "__main__":
    main()
