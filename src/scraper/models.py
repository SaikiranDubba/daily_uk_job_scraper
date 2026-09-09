"""
Shared data model for a job listing, regardless of which source it came from.

Every source adapter (Adzuna, Reed, etc.) must return a list of RawJob objects
so the rest of the pipeline never needs to know which API a job came from.
"""

from pydantic import BaseModel


class RawJob(BaseModel):
    external_id: str          # the source's own ID for this job (used later for dedup)
    title: str
    company: str | None = None
    location: str | None = None
    salary: str | None = None
    description: str | None = None
    url: str
    source: str                # e.g. "adzuna", "reed"
    date_posted: str | None = None
