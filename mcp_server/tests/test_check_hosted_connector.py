"""scripts/check-hosted-connector.py decides whether a release reaches the MCP Registry.

The release workflow deploys the hosted connector, runs this script against it and
publishes the registry entry only if it passes. A check that passed on a stale server
would announce a version nobody serves, and one that failed on a slow start would
block a good release, so both directions are pinned here. The script is loaded by
path, since it is not part of the package, and the network is replaced by scripted
replies.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import urllib.error
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check-hosted-connector.py"

pytestmark = pytest.mark.skipif(
    not SCRIPT.is_file(), reason="repository scripts are not part of this checkout"
)

PLUGIN_JSON = "plugins/cloud-finops/.claude-plugin/plugin.json"
REFERENCES = "plugins/cloud-finops/skills/cloud-finops/references"
PLAYBOOKS = "plugins/cloud-finops/skills/cloud-finops/playbooks"


@pytest.fixture()
def hosted(monkeypatch):
    """The script as a module."""
    spec = importlib.util.spec_from_file_location("check_hosted_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "check_hosted_under_test", module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def checkout(tmp_path):
    """A small tree shaped like the repository: version 2.0.0, 2 references, 2 playbooks."""
    (tmp_path / PLUGIN_JSON).parent.mkdir(parents=True)
    (tmp_path / PLUGIN_JSON).write_text(json.dumps({"version": "2.0.0"}), encoding="utf-8")
    for folder, names in ((REFERENCES, ("finops-a", "finops-b")), (PLAYBOOKS, ("aws-x", "aws-y"))):
        (tmp_path / folder).mkdir(parents=True)
        for name in names:
            (tmp_path / folder / f"{name}.md").write_text(
                f"---\nname: {name}\n---\n# {name}\n", encoding="utf-8"
            )
    (tmp_path / PLAYBOOKS / "README.md").write_text("# Format\n", encoding="utf-8")
    return tmp_path


def sse(message: dict) -> str:
    """One JSON-RPC message the way the hosted server sends it."""
    return f"event: message\ndata: {json.dumps(message)}\n\n"


class FakeServer:
    """Answers the three calls from a version and two name lists, and counts them."""

    def __init__(self, version="2.0.0", references=("finops-a", "finops-b"),
                 playbooks=("aws-x", "aws-y")):
        self.version = version
        self.references = list(references)
        self.playbooks = list(playbooks)
        self.calls: list[str] = []

    def reply(self, body: bytes) -> str:
        request = json.loads(body)
        method = request["method"]
        self.calls.append(request["params"].get("name", method))
        if method == "initialize":
            result = {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "cloud-finops", "version": self.version},
            }
        else:
            key = "references" if request["params"]["name"] == "list_references" else "playbooks"
            names = getattr(self, key)
            result = {
                "isError": False,
                "structuredContent": {key: [{"name": n} for n in names], "total": len(names)},
            }
        return sse({"jsonrpc": "2.0", "id": request["id"], "result": result})


def serve(monkeypatch, hosted, *servers):
    """Answer each attempt (three calls) from the next scripted server.

    An exception in place of a server is raised on that attempt's first call.
    The last entry keeps answering once the script runs past the list.
    """
    state = {"posts": 0}

    def fake_post(url, body, headers, timeout):
        index = min(state["posts"] // 3, len(servers) - 1)
        current = servers[index]
        if isinstance(current, Exception):
            state["posts"] += 3  # the attempt ends on this first call
            raise current
        state["posts"] += 1
        return current.reply(body)

    monkeypatch.setattr(hosted, "_post", fake_post)


def run_check(hosted, checkout, attempts=3):
    pauses: list[float] = []
    lines: list[str] = []
    problems = hosted.check(
        "https://example.invalid/mcp",
        hosted.expected_from_checkout(checkout),
        attempts=attempts,
        delay=7,
        sleep=pauses.append,
        log=lines.append,
    )
    return problems, pauses, lines


def test_the_checkout_is_read_the_way_the_bundle_is_built(hosted, checkout):
    """Version from plugin.json, one name per .md file, the playbooks README left out."""
    expected = hosted.expected_from_checkout(checkout)

    assert expected.version == "2.0.0"
    assert expected.references.names == {"finops-a", "finops-b"}
    assert expected.playbooks.names == {"aws-x", "aws-y"}
    assert expected.playbooks.total == 2


def test_a_frontmatter_name_wins_over_the_file_name(hosted, checkout):
    """The server lists the frontmatter name, so the check must expect that one."""
    (checkout / REFERENCES / "finops-b.md").write_text(
        '---\nname: "finops-renamed"\n---\n# b\n', encoding="utf-8"
    )

    assert hosted.expected_from_checkout(checkout).references.names == {
        "finops-a",
        "finops-renamed",
    }


def test_a_server_on_the_checkout_passes_at_once(hosted, checkout, monkeypatch):
    server = FakeServer()
    serve(monkeypatch, hosted, server)

    problems, pauses, _ = run_check(hosted, checkout)

    assert problems == []
    assert pauses == []
    assert server.calls == ["initialize", "list_references", "list_playbooks"]


def test_the_previous_image_answering_first_is_given_time(hosted, checkout, monkeypatch):
    """A rollout that has not settled answers with the old version, then the new one."""
    serve(monkeypatch, hosted, FakeServer(version="1.9.0"), FakeServer())

    problems, pauses, lines = run_check(hosted, checkout)

    assert problems == []
    assert pauses == [7]
    assert "serverInfo.version is 1.9.0, plugin.json says 2.0.0" in lines[0]


def test_a_machine_still_starting_is_given_time(hosted, checkout, monkeypatch):
    serve(monkeypatch, hosted, urllib.error.URLError("timed out"), FakeServer())

    problems, pauses, lines = run_check(hosted, checkout)

    assert problems == []
    assert pauses == [7]
    assert "no answer" in lines[0]


def test_a_stale_server_fails_and_says_what_differs(hosted, checkout, monkeypatch):
    """The August 2026 shape: an older version, a guide missing, one that is gone."""
    serve(monkeypatch, hosted, FakeServer(version="1.9.0", references=("finops-a", "finops-old")))

    problems, pauses, _ = run_check(hosted, checkout)

    assert pauses == [7, 7]  # three attempts, a pause between them, none after the last
    assert "serverInfo.version is 1.9.0, plugin.json says 2.0.0" in problems
    assert "list_references does not list finops-b" in problems
    assert "list_references lists finops-old, absent from the checkout" in problems
    assert not any("list_playbooks" in problem for problem in problems)


def test_the_right_version_with_a_short_catalogue_fails(hosted, checkout, monkeypatch):
    """The version alone is not proof: an image can carry the number and miss a file."""
    serve(monkeypatch, hosted, FakeServer(playbooks=("aws-x",)))

    problems, _, _ = run_check(hosted, checkout)

    assert "list_playbooks total is 1, the checkout has 2 files" in problems
    assert "list_playbooks does not list aws-y" in problems


def test_a_tool_error_is_a_failure_not_an_empty_catalogue(hosted, checkout, monkeypatch):
    def fake_post(url, body, headers, timeout):
        request = json.loads(body)
        if request["method"] == "initialize":
            return FakeServer().reply(body)
        return sse({"jsonrpc": "2.0", "id": request["id"], "result": {"isError": True}})

    monkeypatch.setattr(hosted, "_post", fake_post)

    problems, _, _ = run_check(hosted, checkout, attempts=1)

    assert problems == ["list_references: the tool returned an error"]


def test_a_plain_json_reply_is_read_like_a_stream(hosted):
    message = {"jsonrpc": "2.0", "id": 4, "result": {"ok": True}}

    assert hosted.parse_reply(json.dumps(message), 4) == message
    assert hosted.parse_reply(sse({"jsonrpc": "2.0", "id": 9, "result": {}}) + sse(message), 4) == (
        message
    )
    with pytest.raises(hosted.ConnectorError):
        hosted.parse_reply("<html>502 Bad Gateway</html>", 4)


def test_exit_codes(hosted, checkout, monkeypatch, tmp_path, capsys):
    """0 on a match, 1 on a mismatch, 2 when the checkout cannot be read."""
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(hosted.time, "sleep", lambda seconds: None)
    base = ["--repo-root", str(checkout), "--attempts", "2", "--delay", "0"]

    serve(monkeypatch, hosted, FakeServer())
    assert hosted.main(base) == 0

    serve(monkeypatch, hosted, FakeServer(version="1.9.0"))
    assert hosted.main(base) == 1
    assert "serverInfo.version is 1.9.0" in capsys.readouterr().err

    empty = tmp_path / "not-a-checkout"
    empty.mkdir()
    assert hosted.main(["--repo-root", str(empty)]) == 2


def test_a_failure_is_annotated_and_summarised_in_actions(hosted, checkout, monkeypatch, tmp_path,
                                                          capsys):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    serve(monkeypatch, hosted, FakeServer(version="1.9.0"))

    code = hosted.main(["--repo-root", str(checkout), "--attempts", "1"])

    assert code == 1
    assert "::error title=Hosted connector is not on 2.0.0::serverInfo.version is 1.9.0" in (
        capsys.readouterr().out
    )
    text = summary.read_text(encoding="utf-8")
    assert "**does not serve** version 2.0.0" in text
    assert "- serverInfo.version is 1.9.0, plugin.json says 2.0.0" in text
