import httpx
import respx

from src.scraper.reed_source import REED_BASE_URL, fetch_reed_jobs

FAKE_REED_RESPONSE = {
    "results": [
        {
            "jobId": 987654,
            "jobTitle": "Graduate Test Automation Engineer",
            "employerName": "Example Recruitment Ltd",
            "locationName": "Leeds",
            "minimumSalary": 25000,
            "maximumSalary": 28000,
            "currency": "GBP",
            "jobDescription": "Selenium, Java, SQL desired...",
            "jobUrl": "https://www.reed.co.uk/jobs/987654",
            "date": "09/09/2026",
        }
    ]
}


@respx.mock
def test_fetch_reed_jobs_parses_results_correctly():
    respx.get(REED_BASE_URL).mock(return_value=httpx.Response(200, json=FAKE_REED_RESPONSE))

    jobs = fetch_reed_jobs(api_key="fake_key", keywords="test automation")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Graduate Test Automation Engineer"
    assert job.company == "Example Recruitment Ltd"
    assert job.location == "Leeds"
    assert job.salary == "£25,000 - £28,000"
    assert job.source == "reed"
    assert job.external_id == "987654"


@respx.mock
def test_fetch_reed_jobs_handles_empty_results():
    respx.get(REED_BASE_URL).mock(return_value=httpx.Response(200, json={"results": []}))

    jobs = fetch_reed_jobs(api_key="fake_key", keywords="nonsense role")

    assert jobs == []
