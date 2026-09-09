"""
Repository layer: turns RawJob objects into database rows, handling
deduplication so a job we've already seen never gets stored (or shown) twice.
"""

import hashlib
from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import JobRecord
from src.scraper.models import RawJob


def compute_dedup_hash(job: RawJob) -> str:
    """
    A job is considered "the same" if title + company + url match exactly.
    This catches the common case of the same listing appearing under
    multiple search terms in one run, or across daily runs.

    (It will NOT catch the same job cross-posted to Adzuna AND Reed with a
    different URL - that's a fuzzy-matching problem for a later phase.)
    """
    raw = f"{job.title.strip().lower()}|{(job.company or '').strip().lower()}|{job.url.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def save_new_jobs(session: Session, jobs: list[RawJob]) -> list[JobRecord]:
    """
    Insert jobs that haven't been seen before. Jobs that already exist
    (same dedup_hash) are silently skipped - this is what makes daily
    re-runs only surface genuinely NEW jobs.

    Returns the list of JobRecord rows that were newly inserted this call.
    """
    newly_inserted: list[JobRecord] = []
    today = date.today().isoformat()

    for job in jobs:
        dedup_hash = compute_dedup_hash(job)

        # Skip if we already have this exact job - cheap existence check
        # before attempting an insert.
        exists = session.query(JobRecord).filter_by(dedup_hash=dedup_hash).first()
        if exists:
            continue

        record = JobRecord(
            external_id=job.external_id,
            title=job.title,
            company=job.company,
            location=job.location,
            salary=job.salary,
            description=job.description,
            url=job.url,
            source=job.source,
            date_posted=job.date_posted,
            date_found=today,
            dedup_hash=dedup_hash,
        )
        session.add(record)
        try:
            session.commit()
            newly_inserted.append(record)
        except IntegrityError:
            # Race-condition safety net: two jobs in this same batch hashed
            # identically (shouldn't happen given the query above, but the
            # unique constraint is the real guarantee, not the query).
            session.rollback()

    return newly_inserted


def get_unnotified_jobs(session: Session, limit: int = 10) -> list[JobRecord]:
    """
    Jobs that exist in the DB but haven't been sent to Telegram yet.
    This is what makes the daily message only ever contain NEW jobs -
    once a job is marked notified, it will never be sent again even if
    it keeps showing up in future search results.
    """
    return (
        session.query(JobRecord)
        .filter(JobRecord.notified_at.is_(None))
        .order_by(JobRecord.date_found.desc())
        .limit(limit)
        .all()
    )


def mark_as_notified(session: Session, jobs: list[JobRecord]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for job in jobs:
        job.notified_at = now
    session.commit()
