"""
Database models for the job pipeline.

SQLite is the source of truth; Excel (later phase) is generated FROM this,
not the other way round.
"""
import os
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class JobRecord(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)
    date_posted = Column(String, nullable=True)
    date_found = Column(String, nullable=False)

    # sha256(title + company + url), enforced unique at insert time in the
    # repository layer (see repository.py) - this is how we avoid ever
    # showing the same job twice, even across different search terms/runs.
    dedup_hash = Column(String, unique=True, nullable=False)

    notified_at = Column(String, nullable=True)  # set once sent via Telegram (later phase)
    application_status = Column(String, default="Not Applied")


def get_engine(db_path: str = "data/jobs.db"):
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")


def init_db(db_path: str = "data/jobs.db"):
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
