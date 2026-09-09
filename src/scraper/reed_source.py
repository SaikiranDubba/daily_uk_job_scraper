"""
Reed.co.uk job source.

Calls Reed's official public Jobseeker API directly - no scraping involved.
Docs: https://www.reed.co.uk/developers/jobseeker

Auth: Reed uses HTTP Basic Auth where your API key is the username and the
password is left blank. You need a free key from reed.co.uk/developers.
"""

import httpx

from src.scraper.models import RawJob

REED_BASE_URL = "https://www.reed.co.uk/api/1.0/search"


def fetch_reed_jobs(
    api_key: str,
    keywords: str,
    location: str = "UK",
    results_to_take: int = 20,
) -> list[RawJob]:
    """
    Fetch UK jobs from Reed matching `keywords`.

    Raises httpx.HTTPStatusError if the API call fails (bad key, rate limit, etc.)
    """
    params = {
        "keywords": keywords,
        "locationName": location,
        "resultsToTake": results_to_take,
    }

    response = httpx.get(
        REED_BASE_URL,
        params=params,
        auth=(api_key, ""),  # Reed uses HTTP Basic Auth: key as username, blank password
        timeout=15.0,
    )
    response.raise_for_status()
    data = response.json()

    jobs: list[RawJob] = []
    for item in data.get("results", []):
        jobs.append(
            RawJob(
                external_id=str(item.get("jobId")),
                title=(item.get("jobTitle") or "").strip(),
                company=item.get("employerName"),
                location=item.get("locationName"),
                salary=_format_salary(item),
                description=item.get("jobDescription"),
                url=item.get("jobUrl", ""),
                source="reed",
                date_posted=item.get("date"),
            )
        )
    return jobs


def _format_salary(item: dict) -> str | None:
    lo = item.get("minimumSalary")
    hi = item.get("maximumSalary")
    currency = item.get("currency") or "GBP"
    symbol = "£" if currency == "GBP" else currency + " "
    if lo and hi:
        return f"{symbol}{lo:,.0f} - {symbol}{hi:,.0f}"
    if lo:
        return f"{symbol}{lo:,.0f}+"
    return None
