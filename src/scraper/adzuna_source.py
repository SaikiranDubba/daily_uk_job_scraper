"""
Adzuna job source.

Calls Adzuna's official public Jobs API directly - no scraping involved.
Docs: https://developer.adzuna.com/overview

You need a free app_id + app_key from https://developer.adzuna.com
"""

import httpx

from src.scraper.models import RawJob

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/gb/search/1"


def fetch_adzuna_jobs(
    app_id: str,
    app_key: str,
    keywords: str,
    location: str = "UK",
    results_per_page: int = 20,
) -> list[RawJob]:
    """
    Fetch UK jobs from Adzuna matching `keywords`.

    Raises httpx.HTTPStatusError if the API call fails (bad key, rate limit, etc.)
    so the caller can decide how to handle it - we don't swallow errors silently here.
    """
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": keywords,
        "where": location,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }

    response = httpx.get(ADZUNA_BASE_URL, params=params, timeout=15.0)
    response.raise_for_status()
    data = response.json()

    jobs: list[RawJob] = []
    for item in data.get("results", []):
        jobs.append(
            RawJob(
                external_id=str(item.get("id")),
                title=item.get("title", "").strip(),
                company=(item.get("company") or {}).get("display_name"),
                location=(item.get("location") or {}).get("display_name"),
                salary=_format_salary(item),
                description=item.get("description"),
                url=item.get("redirect_url", ""),
                source="adzuna",
                date_posted=item.get("created"),
            )
        )
    return jobs


def _format_salary(item: dict) -> str | None:
    lo = item.get("salary_min")
    hi = item.get("salary_max")
    if lo and hi:
        return f"£{lo:,.0f} - £{hi:,.0f}"
    if lo:
        return f"£{lo:,.0f}+"
    return None
