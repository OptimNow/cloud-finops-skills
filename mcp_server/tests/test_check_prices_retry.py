"""scripts/check-prices.py retries a throttled price list instead of failing the run.

The weekly price check went red on its first run in GitHub Actions (11 November
2026) with no drift: one Azure Retail Prices request out of 47 was answered 429 and
the script did not try again. These tests load the script by path, since it is not
part of the package, and replace the network with a scripted ``requests`` module.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
import types
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check-prices.py"

pytestmark = pytest.mark.skipif(
    not SCRIPT.is_file(), reason="repository scripts are not part of this checkout"
)


class FakeHTTPError(Exception):
    pass


class FakeResponse:
    def __init__(self, status_code: int, headers: dict | None = None) -> None:
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise FakeHTTPError(f"{self.status_code} error")


@pytest.fixture()
def prices(monkeypatch):
    """The script as a module, a scripted ``requests``, and the pauses it asked for."""
    spec = importlib.util.spec_from_file_location("check_prices_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "check_prices_under_test", module)
    spec.loader.exec_module(module)

    fake = types.ModuleType("requests")
    fake.ConnectionError = type("ConnectionError", (Exception,), {})
    fake.Timeout = type("Timeout", (Exception,), {})
    fake.answers = []
    fake.calls = 0

    def get(url, params=None, headers=None, timeout=None):
        fake.calls += 1
        answer = fake.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    fake.get = get
    monkeypatch.setitem(sys.modules, "requests", fake)
    module.RETRY.update(retries=0, waited=0.0)
    pauses: list[float] = []
    return module, fake, pauses


def test_a_429_is_retried_with_the_pause_the_server_asks(prices) -> None:
    module, fake, pauses = prices
    fake.answers = [FakeResponse(429, {"Retry-After": "3"}), FakeResponse(200)]
    response = module.http_get("https://example.test/prices", sleep=pauses.append)
    assert response.status_code == 200
    assert fake.calls == 2
    assert pauses == [3]
    assert module.RETRY == {"retries": 1, "waited": 3}


def test_without_retry_after_the_schedule_applies(prices) -> None:
    module, fake, pauses = prices
    fake.answers = [FakeResponse(503), FakeResponse(502), FakeResponse(200)]
    assert module.http_get("https://example.test/prices", sleep=pauses.append).status_code == 200
    assert pauses == [2, 5]


def test_a_throttle_that_persists_still_fails(prices) -> None:
    module, fake, pauses = prices
    fake.answers = [FakeResponse(429) for _ in range(5)]
    with pytest.raises(FakeHTTPError):
        module.http_get("https://example.test/prices", sleep=pauses.append)
    assert fake.calls == 5
    assert pauses == list(module.HTTP_RETRY_PAUSES)


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_an_error_of_the_query_itself_is_not_retried(prices, status) -> None:
    module, fake, pauses = prices
    fake.answers = [FakeResponse(status), FakeResponse(200)]
    with pytest.raises(FakeHTTPError):
        module.http_get("https://example.test/prices", sleep=pauses.append)
    assert fake.calls == 1
    assert pauses == []


def test_a_dropped_connection_is_retried(prices) -> None:
    module, fake, pauses = prices
    fake.answers = [fake.ConnectionError("reset"), fake.Timeout("slow"), FakeResponse(200)]
    assert module.http_get("https://example.test/prices", sleep=pauses.append).status_code == 200
    assert pauses == [2, 5]


def test_a_connection_that_stays_down_raises(prices) -> None:
    module, fake, pauses = prices
    fake.answers = [fake.ConnectionError("down") for _ in range(5)]
    with pytest.raises(fake.ConnectionError):
        module.http_get("https://example.test/prices", sleep=pauses.append)
    assert fake.calls == 5


def test_a_long_retry_after_is_capped(prices) -> None:
    module, fake, pauses = prices
    fake.answers = [FakeResponse(429, {"Retry-After": "3600"}), FakeResponse(200)]
    module.http_get("https://example.test/prices", sleep=pauses.append)
    assert pauses == [module.HTTP_RETRY_AFTER_CAP]


def test_the_run_stops_retrying_once_its_budget_is_spent(prices) -> None:
    module, fake, pauses = prices
    module.RETRY["waited"] = float(module.HTTP_RETRY_BUDGET)
    fake.answers = [FakeResponse(429), FakeResponse(200)]
    with pytest.raises(FakeHTTPError):
        module.http_get("https://example.test/prices", sleep=pauses.append)
    assert fake.calls == 1
    assert pauses == []


def test_retry_after_reads_seconds_and_http_dates(prices) -> None:
    module, _fake, _pauses = prices
    now = dt.datetime(2026, 11, 11, 9, 30, 0, tzinfo=dt.timezone.utc)
    assert module.retry_after_seconds("7") == 7
    assert module.retry_after_seconds(" 0.5 ") == 0.5
    assert module.retry_after_seconds("Wed, 11 Nov 2026 09:30:10 GMT", now) == 10
    assert module.retry_after_seconds("Wed, 11 Nov 2026 09:29:00 GMT", now) == 0
    assert module.retry_after_seconds("soon") is None
    assert module.retry_after_seconds(None) is None
    assert module.retry_after_seconds("") is None
