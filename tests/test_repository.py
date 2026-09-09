import pytest

from src.database.models import Base, get_session
from src.database.repository import compute_dedup_hash, save_new_jobs
from src.scraper.models import RawJob
from sqlalchemy import create_engine


@pytest.fixture
def session():
    """A fresh in-memory SQLite database for each test - no files touched."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    s = get_session(engine)
    yield s
    s.close()


def make_job(title="Graduate QA Engineer", company="Acme Ltd", url="https://example.com/1"):
    return RawJob(
        external_id="1",
        title=title,
        company=company,
        location="London",
        salary="£25,000",
        description="desc",
        url=url,
        source="adzuna",
    )


def test_dedup_hash_is_deterministic():
    job = make_job()
    assert compute_dedup_hash(job) == compute_dedup_hash(job)


def test_dedup_hash_differs_for_different_jobs():
    job_a = make_job(title="Graduate QA Engineer")
    job_b = make_job(title="Graduate Software Engineer")
    assert compute_dedup_hash(job_a) != compute_dedup_hash(job_b)


def test_save_new_jobs_inserts_first_time(session):
    jobs = [make_job()]
    inserted = save_new_jobs(session, jobs)
    assert len(inserted) == 1


def test_save_new_jobs_skips_duplicates_on_second_call(session):
    """This is THE key behaviour: running the pipeline twice should not
    re-insert or re-report the same job - this is what stops you getting
    the same Telegram notification every single day."""
    jobs = [make_job()]

    first_run = save_new_jobs(session, jobs)
    second_run = save_new_jobs(session, jobs)  # identical jobs, run again

    assert len(first_run) == 1
    assert len(second_run) == 0  # nothing new the second time


def test_save_new_jobs_distinguishes_different_jobs(session):
    jobs = [
        make_job(title="Graduate QA Engineer", url="https://example.com/1"),
        make_job(title="Graduate Software Engineer", url="https://example.com/2"),
    ]
    inserted = save_new_jobs(session, jobs)
    assert len(inserted) == 2
