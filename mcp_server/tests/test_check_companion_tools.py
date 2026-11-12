"""scripts/check-companion-tools.py reads INSTALLATION.md and the live servers the same way.

INSTALLATION.md lists the tools of two MCP servers that live in other repositories.
On 12 November 2026 it listed five pricing tools while the server served eight, and
nothing had failed. The script compares the page with each server's ``tools/list``;
these tests hold its parsing, its comparison and its exit codes without the network.
They load the script by path, since it is not part of the package, and read the two
recorded answers in ``scripts/fixtures/companion-tools/`` (trimmed to names, input
property names and required lists).
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-companion-tools.py"
FIXTURES = REPO_ROOT / "scripts" / "fixtures" / "companion-tools"

pytestmark = pytest.mark.skipif(
    not SCRIPT.is_file(), reason="repository scripts are not part of this checkout"
)

# The two sections as they stood on 12 November 2026, cut to what the script reads.
# A copy on purpose: the tests must not move when the page is edited.
PAGE = """\
# Installation

### Companion connector: OptimNow AI Pricing Hub (optional)

- Claude Code: `claude mcp add --transport http ai-pricing-hub <url>`.

**Eight tools (all read-only), as of server 0.11.0 on 12 November 2026.** The rest.

- `compare-llm-models(provider?, category?, openness?, capability?, maxInputPrice?, maxOutputPrice?, minElo?, useCasePreset?, volumePreset?, sortBy?, limit?)` - a ranked table
- `recommend-llm-model(useCasePreset, maxMonthlyBudget?, minElo?, requiredCapability?, openness?, volumePreset?)` - a top 3
- `compare-models-side-by-side(models, volumePreset?)` - named models
- `estimate-llm-cost(modelName?, useCasePreset?, monthlyVolume?, customInputTokens?, customOutputTokens?, cacheHitRate?, batchEligible?)` - a cost
- `compare-model-hosts(models, useCasePreset?, volumePreset?)` - hosts
- `track-llm-price-changes(models?, direction?, provider?, includeFlagged?, limit?, useCasePreset?, volumePreset?)` - moves
- `compare-compute-pricing(region?, provider?, category?, processor?, useCase?, minVCPUs?, maxVCPUs?, minMemory?, maxMemory?, sortBy?, limit?)` - instances
- `estimate-self-hosting-breakeven(model, instanceType?, provider?, region?, hourlyRate?, instanceCount?, outputTokensPerSecond?, monthlyOperationsCost?, useCasePreset?, monthlyVolume?, customInputTokens?, customOutputTokens?, cacheHitRate?, batchEligible?)` - a break-even

| `provenance.tier` | not a tool |

---

### Companion connector: AI ROI Calculator (optional)

**Four tools (all read-only, no credentials):**

- `calculate-roi-v4` - full ROI
- `lookup-model-price` - prices for a model
- `load-preset` - defaults
- `sensitivity-analysis` - impact ranking

## API integration

- `not-a-companion-tool` - a bullet under another heading
"""


@pytest.fixture()
def check(monkeypatch):
    """The script as a module, with its pauses removed."""
    spec = importlib.util.spec_from_file_location("check_companion_tools_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "check_companion_tools_under_test", module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.time, "sleep", lambda seconds: None)
    return module


def _server(check, key):
    return next(s for s in check.SERVERS if s.key == key)


def _recorded(check, key):
    """The recorded server as the script would have read it."""
    doc = json.loads((FIXTURES / f"{key}-tools-list.json").read_text(encoding="utf-8"))
    tools = []
    for raw in doc["response"]["result"]["tools"]:
        schema = raw["inputSchema"]
        required = set(schema.get("required", []))
        tools.append(
            check.LiveTool(
                name=raw["name"],
                parameters={p: p not in required for p in schema["properties"]},
            )
        )
    return check.LiveServer(name=doc["server"]["name"], version=doc["server"]["version"], tools=tools)


# ------------------------------------------------------------------------- the page


def test_the_pricing_section_gives_tools_parameters_and_optional_marks(check):
    section = check.parse_section(PAGE, _server(check, "pricing"))
    assert [t.name for t in section.tools][:2] == ["compare-llm-models", "recommend-llm-model"]
    assert len(section.tools) == 8
    assert section.stated_count == 8
    assert section.as_of_version == "0.11.0"
    recommend = section.tools[1].parameters
    assert recommend["useCasePreset"] is False  # required: no question mark
    assert recommend["volumePreset"] is True
    assert check.page_problems(section) == []


def test_the_roi_section_gives_names_only_and_stops_at_the_next_heading(check):
    section = check.parse_section(PAGE, _server(check, "roi"))
    assert [t.name for t in section.tools] == [
        "calculate-roi-v4",
        "lookup-model-price",
        "load-preset",
        "sensitivity-analysis",
    ]
    assert all(not t.parameters for t in section.tools)
    assert section.stated_count == 4
    assert section.as_of_version is None


def test_a_bullet_that_is_not_a_tool_is_left_out(check):
    names = [t.name for t in check.parse_section(PAGE, _server(check, "pricing")).tools]
    assert "claude" not in names
    assert all("provenance" not in name for name in names)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda p: p.replace("Companion connector: AI ROI Calculator", "ROI connector"), "no heading"),
        (lambda p: p.replace("- `calculate-roi-v4` - ", "- calculate-roi-v4: ")
         .replace("- `lookup-model-price` - ", "- lookup-model-price: ")
         .replace("- `load-preset` - ", "- load-preset: ")
         .replace("- `sensitivity-analysis` - ", "- sensitivity-analysis: "), "lists no tool"),
        (lambda p: p.replace("- `load-preset` - defaults", "- `load-preset` - defaults\n- `load-preset` - again"), "listed twice"),
        (lambda p: p.replace("**Four tools", "**Several tools"), "not a count"),
    ],
)
def test_a_page_the_script_cannot_read_is_an_error_not_an_empty_list(check, change, message):
    with pytest.raises(check.PageError, match=message):
        check.parse_section(change(PAGE), _server(check, "roi"))


def test_a_parameter_that_is_not_a_name_is_an_error(check):
    page = PAGE.replace("(models, volumePreset?)", "(models, volume preset?)")
    with pytest.raises(check.PageError, match="not a parameter name"):
        check.parse_section(page, _server(check, "pricing"))


def test_a_count_that_does_not_match_the_bullets_is_reported(check):
    page = PAGE.replace("- `load-preset` - defaults\n", "")
    problems = check.page_problems(check.parse_section(page, _server(check, "roi")))
    assert problems == ["the page says 4 tools and lists 3"]


# -------------------------------------------------------------------- the comparison


@pytest.mark.parametrize("key", ["pricing", "roi"])
def test_the_page_of_12_november_agrees_with_the_recorded_servers(check, key):
    server = _server(check, key)
    section = check.parse_section(PAGE, server)
    assert check.compare(section, _recorded(check, key), server.parameters) == []


def test_the_page_that_listed_five_tools_is_caught(check):
    """The drift this script was written for: three tools and three parameters behind."""
    page = PAGE
    for name in ("compare-model-hosts", "track-llm-price-changes", "estimate-self-hosting-breakeven"):
        line = next(ln for ln in page.splitlines() if ln.startswith(f"- `{name}("))
        page = page.replace(line + "\n", "")
    page = (
        page.replace("volumePreset?, sortBy?, limit?)` - a ranked table", "volumePreset?, limit?)` - a ranked table")
        .replace(", cacheHitRate?, batchEligible?)` - a cost", ")` - a cost")
        .replace("**Eight tools", "**Five tools")
    )
    server = _server(check, "pricing")
    differences = check.compare(check.parse_section(page, server), _recorded(check, "pricing"), True)
    assert differences == [
        "On the server, not on the page: `compare-model-hosts`, "
        "`estimate-self-hosting-breakeven`, `track-llm-price-changes`",
        "`compare-llm-models`: on the server, not on the page: `sortBy`",
        "`estimate-llm-cost`: on the server, not on the page: `batchEligible`, `cacheHitRate`",
    ]


def test_a_tool_or_parameter_the_server_dropped_is_caught(check):
    live = _recorded(check, "pricing")
    live.tools = [t for t in live.tools if t.name != "compare-compute-pricing"]
    del live.tools[0].parameters["limit"]
    differences = check.compare(check.parse_section(PAGE, _server(check, "pricing")), live, True)
    assert "On the page, not on the server: `compare-compute-pricing`" in differences
    assert "`compare-llm-models`: on the page, not on the server: `limit`" in differences


def test_an_optional_mark_that_no_longer_holds_is_caught_both_ways(check):
    live = _recorded(check, "pricing")
    by_name = {t.name: t for t in live.tools}
    by_name["compare-llm-models"].parameters["provider"] = False  # now required
    by_name["compare-model-hosts"].parameters["models"] = True  # now optional
    differences = check.compare(check.parse_section(PAGE, _server(check, "pricing")), live, True)
    assert differences == [
        "`compare-llm-models`: required on the server, marked optional on the page: `provider`",
        "`compare-model-hosts`: optional on the server, not marked `?` on the page: `models`",
    ]


def test_parameters_are_not_compared_where_the_page_lists_none(check):
    live = _recorded(check, "roi")
    assert any(t.parameters for t in live.tools)  # the server has them, the page does not
    assert check.compare(check.parse_section(PAGE, _server(check, "roi")), live, False) == []


# ------------------------------------------------------------------------ the server


def _sse(message):
    return {"content-type": "text/event-stream"}, f"event: message\ndata: {json.dumps(message)}\n\n".encode()


def test_an_answer_is_read_from_json_or_from_an_event_stream(check):
    result = {"jsonrpc": "2.0", "id": 7, "result": {"tools": []}}
    assert check.decode_rpc({"content-type": "application/json"}, json.dumps(result).encode(), 7) == {"tools": []}
    headers, body = _sse(result)
    assert check.decode_rpc(headers, b"data: {not json}\n" + body, 7) == {"tools": []}


@pytest.mark.parametrize(
    "body",
    [b"<html>Not found</html>", json.dumps({"jsonrpc": "2.0", "id": 7, "error": {"message": "no"}}).encode()],
)
def test_something_that_is_not_a_result_is_not_an_outage(check, body):
    with pytest.raises(check.Moved):
        check.decode_rpc({"content-type": "application/json"}, body, 7)


def test_a_server_is_read_through_initialize_then_every_page_of_tools_list(check, monkeypatch):
    recorded = json.loads((FIXTURES / "pricing-tools-list.json").read_text(encoding="utf-8"))
    tools = recorded["response"]["result"]["tools"]
    sent = []

    def fake_post(url, payload, headers):
        sent.append((payload.get("method"), payload.get("params"), dict(headers)))
        if payload["method"] == "initialize":
            answer_headers, body = _sse(
                {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26", "serverInfo": recorded["server"]}}
            )
            return {**answer_headers, "mcp-session-id": "abc"}, body
        if payload["method"] == "notifications/initialized":
            raise check.Moved("HTTP 400")  # some servers refuse it; the list still answers
        first = payload.get("params") is None
        result = {"tools": tools[:5], "nextCursor": "page-2"} if first else {"tools": tools[5:]}
        return _sse({"jsonrpc": "2.0", "id": payload["id"], "result": result})

    monkeypatch.setattr(check, "_post", fake_post)
    live = check.fetch_server("https://example.invalid/mcp")

    assert (live.name, live.version) == ("ai-pricing-hub", "0.11.0")
    assert len(live.tools) == 8
    hosts = next(t for t in live.tools if t.name == "compare-model-hosts")
    assert hosts.parameters == {"models": False, "useCasePreset": True, "volumePreset": True}
    assert [method for method, _, _ in sent] == [
        "initialize", "notifications/initialized", "tools/list", "tools/list",
    ]
    assert sent[3][1] == {"cursor": "page-2"}
    assert sent[2][2] == {"MCP-Protocol-Version": "2025-03-26", "Mcp-Session-Id": "abc"}


class _Answer(io.BytesIO):
    headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code):
    return urllib.error.HTTPError("https://example.invalid/mcp", code, "error", {}, None)


def test_a_throttled_request_is_tried_again(check, monkeypatch):
    answers = [_http_error(429), _http_error(503), _Answer(b'{"ok": true}')]

    def urlopen(request, timeout=None):
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(check.urllib.request, "urlopen", urlopen)
    headers, body = check._post("https://example.invalid/mcp", {}, {})
    assert body == b'{"ok": true}'
    assert headers["content-type"] == "application/json"
    assert answers == []


def test_a_server_that_never_answers_is_unreachable_and_a_404_is_not(check, monkeypatch):
    def down(request, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(check.urllib.request, "urlopen", down)
    with pytest.raises(check.Unreachable, match="connection refused"):
        check._post("https://example.invalid/mcp", {}, {})

    def gone(request, timeout=None):
        raise _http_error(404)

    monkeypatch.setattr(check.urllib.request, "urlopen", gone)
    with pytest.raises(check.Moved, match="HTTP 404"):
        check._post("https://example.invalid/mcp", {}, {})


# -------------------------------------------------------------------------- the runs


@pytest.fixture()
def page(tmp_path):
    path = tmp_path / "INSTALLATION.md"
    path.write_text(PAGE, encoding="utf-8")
    return path


def _answers(check, monkeypatch, by_url):
    def fetch(url):
        answer = by_url[url]
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(check, "fetch_server", fetch)


def test_a_live_run_that_agrees_exits_0_and_says_what_it_read(check, monkeypatch, page):
    pricing, roi = check.SERVERS
    _answers(check, monkeypatch, {pricing.url: _recorded(check, "pricing"), roi.url: _recorded(check, "roi")})
    code, report = check.run_live(page, check.SERVERS)
    assert code == check.EXIT_OK
    assert "Agrees (names, parameters and optional marks). Server: `ai-pricing-hub` 0.11.0, 8 tools." in report
    assert "Agrees (names). Server: `ai-roi-calculator` 1.5.0, 4 tools." in report


def test_a_difference_exits_1_even_when_the_other_server_is_down(check, monkeypatch, page):
    pricing, roi = check.SERVERS
    live = _recorded(check, "roi")
    live.tools.append(check.LiveTool(name="compare-scenarios"))
    _answers(check, monkeypatch, {pricing.url: check.Unreachable("timed out"), roi.url: live})
    code, report = check.run_live(page, check.SERVERS)
    assert code == check.EXIT_DIFFERS
    assert "- On the server, not on the page: `compare-scenarios`" in report
    assert "**Not compared:** the server could not be read (timed out)." in report


def test_an_outage_alone_exits_2(check, monkeypatch, page):
    pricing, roi = check.SERVERS
    _answers(check, monkeypatch, {pricing.url: check.Unreachable("HTTP 503"), roi.url: _recorded(check, "roi")})
    code, report = check.run_live(page, check.SERVERS)
    assert code == check.EXIT_UNREACHABLE
    assert "Differs" not in report


def test_an_endpoint_that_moved_exits_1(check, monkeypatch, page):
    pricing, roi = check.SERVERS
    _answers(check, monkeypatch, {pricing.url: check.Moved("HTTP 404"), roi.url: _recorded(check, "roi")})
    code, report = check.run_live(page, check.SERVERS)
    assert code == check.EXIT_DIFFERS
    assert "did not answer as an MCP endpoint at this URL (HTTP 404)" in report


def test_a_newer_server_that_still_agrees_is_noted_not_failed(check, monkeypatch, page):
    pricing, roi = check.SERVERS
    live = _recorded(check, "pricing")
    live.version = "0.12.0"
    _answers(check, monkeypatch, {pricing.url: live, roi.url: _recorded(check, "roi")})
    code, report = check.run_live(page, check.SERVERS)
    assert code == check.EXIT_OK
    assert "The page says it was read at server 0.11.0; the server is at 0.12.0." in report


def test_the_offline_run_needs_no_network_and_passes_on_a_page_that_parses(check, monkeypatch, page, tmp_path):
    def no_network(*args, **kwargs):
        raise AssertionError("the offline run asked for the network")

    monkeypatch.setattr(check.urllib.request, "urlopen", no_network)
    dependencies = tmp_path / "DEPENDENCIES.md"
    dependencies.write_text(" ".join(s.url for s in check.SERVERS), encoding="utf-8")
    assert check.run_offline(page, dependencies, check.SERVERS) == check.EXIT_OK


def test_the_offline_run_fails_on_a_page_that_would_blind_the_weekly_run(check, page, tmp_path, capsys):
    page.write_text(PAGE.replace("- `", "* `"), encoding="utf-8")  # another bullet style
    dependencies = tmp_path / "DEPENDENCIES.md"
    dependencies.write_text(" ".join(s.url for s in check.SERVERS), encoding="utf-8")
    assert check.run_offline(page, dependencies, check.SERVERS) == check.EXIT_DIFFERS
    assert "lists no tool" in capsys.readouterr().err


def test_the_offline_run_fails_when_the_dependency_map_names_another_url(check, page, tmp_path, capsys):
    dependencies = tmp_path / "DEPENDENCIES.md"
    dependencies.write_text(check.SERVERS[0].url, encoding="utf-8")  # the ROI URL is missing
    assert check.run_offline(page, dependencies, check.SERVERS) == check.EXIT_DIFFERS
    assert "does not name https://airoicalculator-mcp.optimnow.io/mcp" in capsys.readouterr().err


def test_the_repository_page_passes_the_offline_run(check):
    """What CI runs: the real INSTALLATION.md and DEPENDENCIES.md."""
    if not check.INSTALLATION_PATH.is_file():
        pytest.skip("INSTALLATION.md is not part of this checkout")
    assert check.main(["--offline"]) == check.EXIT_OK
