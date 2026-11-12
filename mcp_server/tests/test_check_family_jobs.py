"""scripts/check-family-jobs.py says what needs a hand, and never calls "not read" fine.

The script reads the scheduled jobs of five repositories in one pass. On the day it was
written two weekly pull requests had waited 17 days and a deploy had stopped behind a
red branch, unseen. These tests hold its verdicts and its exit codes on scripted GitHub
answers: no network. They load the script by path, since it is not part of the package.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check-family-jobs.py"

pytestmark = pytest.mark.skipif(
    not SCRIPT.is_file(), reason="repository scripts are not part of this checkout"
)

NOW = dt.datetime(2026, 11, 16, 8, 12, tzinfo=dt.timezone.utc)  # a Monday morning


@pytest.fixture()
def check(monkeypatch):
    spec = importlib.util.spec_from_file_location("check_family_jobs_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "check_family_jobs_under_test", module)
    spec.loader.exec_module(module)
    return module


def _run(day: str, conclusion: str = "success", event: str = "schedule", status: str = "completed"):
    return {
        "created_at": f"{day}T06:00:00Z",
        "conclusion": conclusion,
        "event": event,
        "status": status,
        "html_url": f"https://github.example/runs/{day}",
    }


def _weekly(check):
    return next(j for j in check.JOBS if j.workflow == "sync-engine.yml")


def _daily(check):
    return next(j for j in check.JOBS if j.workflow == "refresh-llm-fallback.yml")


# --------------------------------------------------------------------------- one job


def test_a_job_that_ran_this_morning_is_fine(check):
    finding = check.judge_job(_weekly(check), _run("2026-11-16"), NOW)
    assert (finding.level, finding.what) == ("ok", "ran")


def test_a_failed_last_run_needs_a_hand_and_carries_its_link(check):
    finding = check.judge_job(_weekly(check), _run("2026-11-16", "failure"), NOW)
    assert finding.level == "hand"
    assert finding.what == "last run failed"
    assert finding.url.endswith("/runs/2026-11-16")


def test_a_weekly_job_silent_for_two_weeks_is_late_even_though_its_last_run_passed(check):
    finding = check.judge_job(_weekly(check), _run("2026-11-02"), NOW)
    assert (finding.level, finding.what) == ("hand", "late")
    assert "14 days ago" in finding.detail


def test_a_daily_job_is_late_after_two_days(check):
    assert check.judge_job(_daily(check), _run("2026-11-15"), NOW).level == "ok"
    assert check.judge_job(_daily(check), _run("2026-11-13"), NOW).what == "late"


def test_a_job_added_this_week_is_not_due_yet(check):
    added = NOW - dt.timedelta(days=3)
    finding = check.judge_job(_weekly(check), None, NOW, registered=added)
    assert (finding.level, finding.what) == ("ok", "not due yet")


def test_a_job_that_never_ran_after_its_first_week_needs_a_hand(check):
    added = NOW - dt.timedelta(days=30)
    assert check.judge_job(_weekly(check), None, NOW, registered=added).what == "never ran"
    assert check.judge_job(_weekly(check), None, NOW).level == "hand"  # age unknown: say so


def test_a_red_default_branch_is_reported_as_a_stopped_deploy(check):
    finding = check.judge_ci(check.CALCULATOR_MCP, _run("2026-11-12", "failure", "push"))
    assert finding.level == "hand"
    assert "deploy behind it is stopped" in finding.detail
    assert check.judge_ci(check.CALCULATOR_MCP, _run("2026-11-12", event="push")).level == "ok"


# ------------------------------------------------------------- what a job left behind


def test_a_pull_request_opened_by_a_job_waits_for_a_human_and_others_do_not(check):
    pulls = [
        {"number": 52, "title": "Sync the engine", "user": {"login": "github-actions[bot]"},
         "created_at": "2026-10-26T07:00:00Z", "html_url": "https://github.example/pull/52"},
        {"number": 60, "title": "A human's change", "user": {"login": "OptimNow"},
         "created_at": "2026-11-15T07:00:00Z"},
        {"number": 57, "title": "Bump zod", "user": {"login": "dependabot[bot]"},
         "created_at": "2026-11-01T07:00:00Z"},
    ]
    findings = check.judge_pulls(check.CALCULATOR_MCP, pulls, NOW)
    assert [f.where for f in findings] == ["ROI calculator MCP: pull request #52"]
    assert "open for 21 day(s)" in findings[0].detail


def test_an_open_alarm_issue_needs_a_hand_and_a_pull_request_in_the_list_is_skipped(check):
    issues = [
        {"number": 348, "title": "Price drift - 2026-11-14", "created_at": "2026-11-14T12:05:00Z"},
        {"number": 349, "title": "a PR the issues API also lists", "created_at": "2026-11-14T12:05:00Z",
         "pull_request": {}},
    ]
    findings = check.judge_alarms(check.SKILL, "price-drift", issues, NOW)
    assert len(findings) == 1
    assert findings[0].where == "Cloud FinOps skill: issue #348 (`price-drift`)"


def test_scan_issues_are_fine_within_the_week_and_a_backlog_past_it(check):
    def issue(day):
        return {"number": 1, "title": "Content update", "created_at": f"{day}T08:00:00Z"}

    assert check.judge_triage([], NOW).what == "none open"
    assert check.judge_triage([issue("2026-11-14")], NOW).level == "ok"
    assert check.judge_triage([issue("2026-10-24")], NOW).level == "hand"  # one, three weeks old
    piled = [issue("2026-11-14"), issue("2026-11-07"), issue("2026-11-02")]
    assert check.judge_triage(piled, NOW).what == "scan issues are piling up"


def test_the_catalogue_is_stale_once_its_host_prices_are_three_days_old(check):
    assert check.judge_catalogue({"hostPricingAsOf": "2026-11-15", "catalogTotal": 315}, NOW).level == "ok"
    stale = check.judge_catalogue({"hostPricingAsOf": "2026-11-12"}, NOW)
    assert (stale.level, stale.what) == ("hand", "stale")
    assert check.judge_catalogue({}, NOW).level == "unread"


# ------------------------------------------------------------------------ the whole run


def _scripted(check, monkeypatch, *, private_unreadable=False, failing=None, bot_pull_in=None):
    """Replace every outside call. All jobs ran this morning unless told otherwise."""

    def github(path, token):
        # With its slash: the site's slug is a prefix of the pricing MCP's.
        if private_unreadable and f"/repos/{check.SITE.slug}/" in path:
            raise check.NotRead("not found without a token (a private repository reads so)")
        if "/actions/workflows/" in path and "/runs" in path:
            workflow = path.split("/actions/workflows/")[1].split("/")[0]
            event = "push" if workflow == "ci.yml" else "schedule"
            conclusion = "failure" if failing == workflow else "success"
            return {"workflow_runs": [_run("2026-11-16", conclusion, event)]}
        if "/pulls?" in path:
            if bot_pull_in and f"/repos/{bot_pull_in}/" in path:
                return [{"number": 9, "title": "Weekly refresh", "user": {"login": check.BOT},
                         "created_at": "2026-11-16T07:00:00Z"}]
            return []
        if "/issues?" in path:
            return []
        raise AssertionError(f"unexpected call: {path}")

    monkeypatch.setattr(check, "github", github)
    monkeypatch.setattr(check, "server_version", lambda url: "server 1.0.0")
    monkeypatch.setattr(check, "read_json", lambda url: {"meta": {"hostPricingAsOf": "2026-11-16", "catalogTotal": 315}})


def test_a_quiet_monday_exits_0_and_says_so_first(check, monkeypatch):
    _scripted(check, monkeypatch)
    findings = check.collect(NOW, "token")
    report = check.render(findings, NOW, with_token=True)
    assert check.exit_code(findings) == check.EXIT_OK
    assert "**Nothing needs a hand.**" in report
    assert "## Needs a hand" not in report
    assert report.count("\n- ") == len(check.JOBS) + len(check.CI_WORKFLOWS) + 1 + len(check.SERVERS) + 1


def test_one_failed_job_exits_1_and_is_listed_before_everything_that_is_fine(check, monkeypatch):
    _scripted(check, monkeypatch, failing="refresh-elo-scores.yml")
    findings = check.collect(NOW, "token")
    report = check.render(findings, NOW, with_token=True)
    assert check.exit_code(findings) == check.EXIT_NEEDS_A_HAND
    assert "**1 item(s) need a hand.**" in report
    assert report.index("weekly ELO scores refresh") < report.index("## Fine")


def test_a_pull_request_left_by_a_job_is_in_the_report(check, monkeypatch):
    _scripted(check, monkeypatch, bot_pull_in=check.PRICING_MCP.slug)
    findings = check.collect(NOW, "token")
    assert check.exit_code(findings) == check.EXIT_NEEDS_A_HAND
    assert any(f.where == "Pricing MCP: pull request #9" for f in findings)


def test_a_private_repository_that_cannot_be_read_is_never_reported_as_fine(check, monkeypatch):
    _scripted(check, monkeypatch, private_unreadable=True)
    findings = check.collect(NOW, None)
    report = check.render(findings, NOW, with_token=False)
    unread = [f for f in findings if f.level == "unread"]
    # five jobs, the CI, the pull requests and each alarm label of the site
    assert len(unread) == 5 + 1 + 1 + len(check.SITE.alarm_labels)
    assert check.exit_code(findings) == check.EXIT_NOT_READ
    assert "**Nothing wrong was seen, but not everything could be read.**" in report
    assert "## Not read (not the same as fine)" in report
    assert "without a GitHub token (public data only)" in report


def test_a_server_that_does_not_answer_needs_a_hand(check, monkeypatch):
    _scripted(check, monkeypatch)

    def down(url):
        raise check.NotRead("HTTP 503")

    monkeypatch.setattr(check, "server_version", down)
    findings = check.collect(NOW, "token")
    silent = [f for f in findings if f.what == "does not answer"]
    assert len(silent) == len(check.SERVERS)
    assert check.exit_code(findings) == check.EXIT_NEEDS_A_HAND


def test_only_runs_of_the_right_kind_count_as_the_latest(check, monkeypatch):
    """A pull-request run of mcp-parity, or one still in progress, is not the job's last word."""
    runs = [
        _run("2026-11-16", "failure", "pull_request"),
        _run("2026-11-16", "success", "schedule", status="in_progress"),
        _run("2026-11-15", "success", "schedule"),
    ]
    monkeypatch.setattr(check, "github", lambda path, token: {"workflow_runs": runs})
    run = check.latest_finished_run(check.SITE, "mcp-parity.yml", ("schedule", "workflow_dispatch"), "token")
    assert run["created_at"].startswith("2026-11-15")
