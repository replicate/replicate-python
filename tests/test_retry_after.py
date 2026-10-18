from datetime import datetime, timezone

import httpx
import pytest

from replicate import client as client_module
from replicate.client import RetryTransport


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None) -> datetime:
        return datetime(2026, 10, 18, 12, 0, 0, tzinfo=timezone.utc).astimezone(tz)


CASES = [
    ("Sun, 18 Oct 2026 12:00:30 GMT", 30),
    ("Sunday, 18-Oct-26 12:00:30 GMT", 30),
    ("Sun Oct 18 12:00:30 2026", 30),
    ("Sun, 18 Oct 2026 12:01:30 GMT", 60),
    ("2026-10-18T12:00:30+00:00", 30),
    ("Sun, 18 Oct 2026 11:59:30 GMT", 0.1),
    ("invalid", 0.1),
    ("", 0.1),
    ("0", 0),
    ("3", 3),
    ("120", 120),
]


@pytest.mark.parametrize("header,expected", CASES)
@pytest.mark.parametrize("status", [429, 503])
def test_retry_after_sync(monkeypatch, header, expected, status):
    monkeypatch.setattr(client_module, "datetime", FixedDateTime)
    sleeps = []
    monkeypatch.setattr(client_module.time, "sleep", sleeps.append)
    responses = [
        httpx.Response(status, headers={"Retry-After": header}),
        httpx.Response(200, json={"ok": True}),
    ]
    attempts = []

    def respond(request):
        attempts.append(request)
        return responses[len(attempts) - 1]

    with httpx.Client(
        transport=RetryTransport(
            httpx.MockTransport(respond), max_attempts=2, jitter_ratio=0
        )
    ) as client:
        response = client.get("https://example.test/predictions")

    assert response.json() == {"ok": True}
    assert sleeps == [expected]
    assert len(attempts) == 2
    assert responses[0].is_closed


@pytest.mark.parametrize("header,expected", CASES)
@pytest.mark.parametrize("status", [429, 503])
async def test_retry_after_async(monkeypatch, header, expected, status):
    monkeypatch.setattr(client_module, "datetime", FixedDateTime)
    sleeps = []

    async def sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(client_module.asyncio, "sleep", sleep)
    responses = [
        httpx.Response(status, headers={"Retry-After": header}),
        httpx.Response(200, json={"ok": True}),
    ]
    attempts = []

    def respond(request):
        attempts.append(request)
        return responses[len(attempts) - 1]

    async with httpx.AsyncClient(
        transport=RetryTransport(
            httpx.MockTransport(respond), max_attempts=2, jitter_ratio=0
        )
    ) as client:
        response = await client.get("https://example.test/predictions")

    assert response.json() == {"ok": True}
    assert sleeps == [expected]
    assert len(attempts) == 2
    assert responses[0].is_closed
