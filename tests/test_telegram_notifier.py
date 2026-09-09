import httpx
import respx

from src.database.models import JobRecord
from src.telegram.notifier import format_job_message, send_daily_jobs, send_telegram_message


def make_job_record(title="Graduate QA Engineer", company="Acme Ltd"):
    return JobRecord(
        external_id="1",
        title=title,
        company=company,
        location="London",
        salary="£25,000",
        url="https://example.com/1",
        source="adzuna",
        date_found="2026-09-09",
        dedup_hash="fakehash1",
    )


def test_format_job_message_includes_key_fields():
    jobs = [make_job_record()]
    message = format_job_message(jobs)

    assert "Graduate QA Engineer" in message
    assert "Acme Ltd" in message
    assert "London" in message
    assert "https://example.com/1" in message


@respx.mock
def test_send_telegram_message_returns_true_on_success():
    respx.post("https://api.telegram.org/bottest_token/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    result = send_telegram_message("test_token", "12345", "hello")
    assert result is True


@respx.mock
def test_send_telegram_message_returns_false_on_failure():
    respx.post("https://api.telegram.org/bottest_token/sendMessage").mock(
        return_value=httpx.Response(400, json={"ok": False, "description": "bad request"})
    )

    result = send_telegram_message("test_token", "12345", "hello")
    assert result is False


@respx.mock
def test_send_daily_jobs_handles_empty_list():
    respx.post("https://api.telegram.org/bottest_token/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    result = send_daily_jobs("test_token", "12345", [])
    assert result is True
