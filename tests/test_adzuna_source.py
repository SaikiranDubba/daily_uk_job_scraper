import httpx
import respx

from src.scraper.adzuna_source import ADZUNA_BASE_URL, fetch_adzuna_jobs

FAKE_ADZUNA_RESPONSE = {
    "results": [
        {
            "id": "123456",
            "title": "Graduate QA Automation Engineer",
            "company": {"display_name": "Example Ltd"},
            "location": {"display_name": "Manchester, UK"},
            "salary_min": 26000,
            "salary_max": 30000,
            "description": "Java, Selenium, SQL required...",
            "redirect_url": "https://example.com/jobs/123456",
            "created": "2026-09-01T10:00:00Z",
        }
    ]
}


@respx.mock
def test_fetch_adzuna_jobs_parses_results_correctly():
    respx.get(ADZUNA_BASE_URL).mock(
        return_value=httpx.Response(200, json=FAKE_ADZUNA_RESPONSE)
    )

    jobs = fetch_adzuna_jobs(
        app_id="fake_id",
        app_key="fake_key",
        keywords="graduate qa engineer",
    )

    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Graduate QA Automation Engineer"
    assert job.company == "Example Ltd"
    assert job.location == "Manchester, UK"
    assert job.salary == "£26,000 - £30,000"
    assert job.source == "adzuna"
    assert job.external_id == "123456"


@respx.mock
def test_fetch_adzuna_jobs_handles_empty_results():
    respx.get(ADZUNA_BASE_URL).mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    jobs = fetch_adzuna_jobs(app_id="fake_id", app_key="fake_key", keywords="nonsense role")

    assert jobs == []
