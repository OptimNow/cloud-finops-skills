"""Tests for ``get_live_figures``, the server's one outbound tool.

Every test replaces ``live_figures._fetch`` with a fake that serves the saved
copies under ``tests/fixtures/live_figures/`` (see the README there for the
date they were fetched), so the suite never touches the network.
"""

from __future__ import annotations

import inspect
import json
import urllib.error
from pathlib import Path

import pytest

from cloud_finops_mcp import live_figures, server

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "live_figures"
SLUGS = ["savings-plans-vs-reserved-instances", "arm-against-x86", "batch-api-economics"]


class FakeFetch:
    """Records each URL requested and answers from a ``{url: response}`` map.

    A response is ``(status, body)``, or an exception instance to raise.
    Unmapped URLs answer 404, which is what OptimToken does for an unknown slug.
    """

    def __init__(self, responses: dict[str, object] | None = None) -> None:
        self.calls: list[str] = []
        self.responses: dict[str, object] = {
            live_figures.FIGURES_URL.format(slug=slug): (
                200,
                (FIXTURES / f"{slug}.json").read_bytes(),
            )
            for slug in SLUGS
        }
        self.responses[live_figures.LLMS_TXT_URL] = (200, (FIXTURES / "llms.txt").read_bytes())
        self.responses.update(responses or {})

    def __call__(self, url: str) -> tuple[int, bytes]:
        self.calls.append(url)
        response = self.responses.get(url, (404, b""))
        if isinstance(response, BaseException):
            raise response
        return response  # type: ignore[return-value]


@pytest.fixture(autouse=True)
def _clean_cache():
    live_figures.reset_cache()
    yield
    live_figures.reset_cache()


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeFetch:
    fetch = FakeFetch()
    monkeypatch.setattr(live_figures, "_fetch", fetch)
    return fetch


def _url(slug: str) -> str:
    return live_figures.FIGURES_URL.format(slug=slug)


@pytest.mark.parametrize("slug", SLUGS)
def test_hit_returns_the_document_untouched(fake: FakeFetch, slug: str) -> None:
    result = live_figures.get_live_figures(slug)
    saved = json.loads((FIXTURES / f"{slug}.json").read_text(encoding="utf-8"))
    assert result["document"] == saved, "the figures must be passed through, not recomputed"
    assert result["source"] == "live"
    assert "cache_age_seconds" not in result
    assert result["fetched_at"].endswith("Z")
    assert saved["snapshotDate"] in result["note"]
    assert fake.calls == [_url(slug)]


def test_figures_are_not_rounded(fake: FakeFetch) -> None:
    doc = live_figures.get_live_figures("savings-plans-vs-reserved-instances")["document"]
    aws = doc["figures"]["clouds"]["AWS"]
    assert aws["flexibilityPremium"]["oneYear"]["median"] == 0.0941
    assert aws["instruments"]["savingsPlan1yr"]["median"] == 0.2743


def test_second_call_within_ttl_is_cached(
    fake: FakeFetch, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = [1_000_000.0]
    monkeypatch.setattr(live_figures, "_now", lambda: clock[0])
    first = live_figures.get_live_figures("arm-against-x86")
    clock[0] += 120
    second = live_figures.get_live_figures("arm-against-x86")

    assert second["source"] == "cached"
    assert second["cache_age_seconds"] == 120
    assert second["fetched_at"] == first["fetched_at"]
    assert second["document"] == first["document"]
    assert fake.calls == [_url("arm-against-x86")], "the cached call must not refetch"


def test_cache_expires_after_the_ttl(fake: FakeFetch, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [1_000_000.0]
    monkeypatch.setattr(live_figures, "_now", lambda: clock[0])
    live_figures.get_live_figures("arm-against-x86")
    clock[0] += live_figures.CACHE_TTL_SECONDS
    again = live_figures.get_live_figures("arm-against-x86")
    assert again["source"] == "live"
    assert fake.calls == [_url("arm-against-x86")] * 2


def test_404_lists_the_available_guides(fake: FakeFetch) -> None:
    result = live_figures.get_live_figures("savings-plan-vs-reserved-instance")
    assert "error" in result
    assert result["available_guides"] == [
        {"slug": "arm-against-x86", "title": "ARM against x86: what Graviton, Ampere and Axion save"},
        {"slug": "batch-api-economics", "title": "Batch API economics: when the -50% applies"},
        {
            "slug": "savings-plans-vs-reserved-instances",
            "title": "Savings plans against reserved instances: what the flexibility costs",
        },
    ], "only the guides with a 'Figures as JSON' line are listed"
    assert result["suggestions"][0] == "savings-plans-vs-reserved-instances"


def test_guide_list_is_cached_too(fake: FakeFetch) -> None:
    live_figures.get_live_figures("nope-one")
    live_figures.get_live_figures("nope-two")
    assert fake.calls.count(live_figures.LLMS_TXT_URL) == 1


def test_404_with_unreadable_guide_list_still_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch = FakeFetch({live_figures.LLMS_TXT_URL: TimeoutError("timed out")})
    monkeypatch.setattr(live_figures, "_fetch", fetch)
    result = live_figures.get_live_figures("no-such-guide")
    assert result["available_guides"] == []
    assert result["suggestions"] == []
    assert result["fallback"] == live_figures.FALLBACK


@pytest.mark.parametrize(
    "response",
    [
        TimeoutError("timed out"),
        urllib.error.URLError("Name or service not known"),
        OSError("network unreachable"),
        (500, b"Internal Server Error"),
        (200, b"<!doctype html><html></html>"),
        (200, b"\xff\xfe not utf-8"),
        (200, json.dumps({"guide": "arm-against-x86", "title": "no figures"}).encode()),
        (200, json.dumps(["not", "an", "object"]).encode()),
        (200, b"{" + b" " * live_figures.MAX_BODY_BYTES + b"}"),
    ],
    ids=["timeout", "dns-failure", "oserror", "http-500", "html", "bad-utf8",
         "no-figures", "json-list", "over-cap"],
)
def test_failures_return_the_error_shape(
    monkeypatch: pytest.MonkeyPatch, response: object
) -> None:
    fetch = FakeFetch({_url("arm-against-x86"): response})
    monkeypatch.setattr(live_figures, "_fetch", fetch)
    result = live_figures.get_live_figures("arm-against-x86")
    assert set(result) == {"error", "fallback"}
    assert result["fallback"] == live_figures.FALLBACK


def test_a_failure_is_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch = FakeFetch({_url("arm-against-x86"): (503, b"")})
    monkeypatch.setattr(live_figures, "_fetch", fetch)
    assert "error" in live_figures.get_live_figures("arm-against-x86")
    fetch.responses[_url("arm-against-x86")] = (200, (FIXTURES / "arm-against-x86.json").read_bytes())
    assert live_figures.get_live_figures("arm-against-x86")["source"] == "live"


@pytest.mark.parametrize(
    "slug",
    ["", "Savings-Plans", "../etc/passwd", "a/b", "a b", "x" * 81, "slug?x=1", "é", None, 42],
)
def test_invalid_slug_makes_no_request(fake: FakeFetch, slug: object) -> None:
    result = live_figures.get_live_figures(slug)  # type: ignore[arg-type]
    assert set(result) == {"error", "fallback"}
    assert fake.calls == []


def test_request_carries_the_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real _fetch, with the opener swapped: one GET, our User-Agent, a timeout."""
    seen = {}

    class Response:
        status = 200

        def read(self, n: int) -> bytes:
            seen["read_cap"] = n
            return b"{}"

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class Opener:
        def open(self, request, timeout):
            seen["url"] = request.full_url
            seen["ua"] = request.get_header("User-agent")
            seen["timeout"] = timeout
            return Response()

    monkeypatch.setattr(live_figures, "_opener", Opener())
    assert live_figures._fetch(_url("arm-against-x86")) == (200, b"{}")
    assert seen["url"] == "https://optimtoken.optimnow.io/guides/arm-against-x86/figures.json"
    assert seen["ua"].startswith("cloud-finops-mcp/")
    assert "github.com/OptimNow/cloud-finops-skills" in seen["ua"]
    assert seen["timeout"] == 5
    assert seen["read_cap"] == live_figures.MAX_BODY_BYTES + 1


def test_redirect_off_host_is_refused() -> None:
    handler = live_figures._SameHostRedirect()
    assert handler.redirect_request(None, None, 302, "Found", {}, "https://example.com/x") is None


async def test_server_tool_runs_off_the_event_loop(fake: FakeFetch) -> None:
    """Through the registered MCP tool: async wrapper, same result as the function.

    The fetch blocks for up to five seconds; a sync tool would run on the event
    loop and stall every other request on the hosted server.
    """
    assert inspect.iscoroutinefunction(server.get_live_figures)
    result = await server.get_live_figures("batch-api-economics")
    assert result["document"]["guide"] == "batch-api-economics"
    assert result["source"] == "live"
