"""scripts/check-family-jobs.py says what needs a hand, and never calls "not read" fine.

The script reads the scheduled jobs of five repositories in one pass. On the day it was
written two weekly pull requests had waited 17 days and a deploy had stopped behind a
red branch, unseen. These tests hold its verdicts and its exit codes on scripted GitHub
answers: no network. They load the script by path, since it is not part of the package.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import io
import sys
import urllib.error
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


def _scripted(
    check,
    monkeypatch,
    *,
    private_unreadable=False,
    failing=None,
    bot_pull_in=None,
    other_workflows=None,
    issues_in=None,
    owner_comments=(),
):
    """Replace every outside call. All jobs ran this morning unless told otherwise.

    `other_workflows` maps a repository slug to the workflows GitHub lists for it,
    `issues_in` maps a slug to its open issues, and `owner_comments` holds the numbers
    of the issues the owner has commented on.
    """

    def github(path, token):
        # With its slash: the site's slug is a prefix of the pricing MCP's.
        if private_unreadable and f"/repos/{check.SITE.slug}/" in path:
            raise check.NotRead("not found without a token (a private repository reads so)")
        slug = path.split("/repos/")[1].split("/actions")[0].split("/issues")[0].split("/pulls")[0]
        if path.endswith("/actions/workflows?per_page=100"):
            return {"workflows": (other_workflows or {}).get(slug, [])}
        if "/comments" in path:
            number = int(path.split("/issues/")[1].split("/")[0])
            return [{"user": {"login": check.OWNER}}] if number in owner_comments else []
        if "/reviews" in path:
            return []
        if path.endswith("/issues?state=open&per_page=100"):
            return (issues_in or {}).get(slug, [])
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
    # five jobs, the CI, the pull requests, each alarm label of the site, and what
    # other people opened there
    assert len(unread) == 5 + 1 + 1 + len(check.SITE.alarm_labels) + 1
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


# ------------------------------------------------------------- a token that is refused


class _Body(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _refusing(check, monkeypatch, anonymous_answer):
    """GitHub as a scoped token sees it: refused with the token, `anonymous_answer` without."""
    asked = []

    def urlopen(request, timeout=None):
        with_token = request.get_header("Authorization") is not None
        asked.append(with_token)
        if with_token:
            raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)
        if isinstance(anonymous_answer, Exception):
            raise anonymous_answer
        return _Body(anonymous_answer)

    monkeypatch.setattr(check.urllib.request, "urlopen", urlopen)
    return asked


def test_a_public_repository_a_scoped_token_refuses_is_read_without_the_token(check, monkeypatch):
    """The routine's first run, 12 November 2026: 403 on three public repositories."""
    asked = _refusing(check, monkeypatch, b'{"workflow_runs": []}')
    assert check.github("/repos/OptimNow/ai-roi-calculator/actions/runs", "scoped") == {"workflow_runs": []}
    assert asked == [True, False]


def test_a_repository_closed_to_both_is_not_read_and_says_the_token_was_refused(check, monkeypatch):
    gone = urllib.error.HTTPError("https://api.github.example", 404, "Not Found", {}, None)
    asked = _refusing(check, monkeypatch, gone)
    with pytest.raises(check.NotRead, match="HTTP 403"):
        check.github("/repos/OptimNow/ai-pricing-hub/pulls", "scoped")
    assert asked == [True, False]


def test_without_a_token_nothing_is_asked_twice(check, monkeypatch):
    calls = []

    def urlopen(request, timeout=None):
        calls.append(request.get_header("Authorization"))
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(check.urllib.request, "urlopen", urlopen)
    with pytest.raises(check.NotRead, match="without a token"):
        check.github("/repos/OptimNow/ai-pricing-hub/pulls", None)
    assert calls == [None]


# ------------------------------------------- what the daily digest used to read by hand


def _issue(number, login, kind="User", pull=False, day="2026-11-10"):
    item = {
        "number": number,
        "title": f"Item {number}",
        "user": {"login": login, "type": kind},
        "created_at": f"{day}T09:00:00Z",
        "html_url": f"https://github.example/issues/{number}",
    }
    if pull:
        item["pull_request"] = {}
    return item


def test_only_a_person_other_than_the_owner_counts_as_someone_else(check):
    assert check.is_someone_else({"login": "helixoft", "type": "User"})
    assert not check.is_someone_else({"login": check.OWNER, "type": "User"})
    assert not check.is_someone_else({"login": "dependabot[bot]", "type": "Bot"})
    assert not check.is_someone_else({"login": "some-app[bot]", "type": "User"})  # the suffix is enough
    assert not check.is_someone_else(None)


def test_an_issue_by_someone_else_waits_until_the_owner_answers(check, monkeypatch):
    skill = check.SKILL.slug
    issues = {
        skill: [
            _issue(11, "helixoft"),                      # nobody answered
            _issue(12, "crmvet", pull=True),             # the owner commented
            _issue(13, "dependabot[bot]", "Bot", True),  # a bot: not someone waiting
            _issue(14, check.OWNER),                     # the owner's own
        ]
    }
    _scripted(check, monkeypatch, issues_in=issues, owner_comments=(12,))
    findings = check.collect(NOW, "token")
    external = {f.where: f for f in findings if " by " in f.where}
    assert set(external) == {
        "Cloud FinOps skill: issue #11 by helixoft",
        "Cloud FinOps skill: pull request #12 by crmvet",
    }
    waiting = external["Cloud FinOps skill: issue #11 by helixoft"]
    assert (waiting.level, waiting.what) == ("hand", "someone is waiting for your answer")
    assert "open for 5 day(s)" in waiting.detail  # opened on the 10th at 09:00, read on the 16th at 08:12
    assert external["Cloud FinOps skill: pull request #12 by crmvet"].level == "ok"
    assert check.exit_code(findings) == check.EXIT_NEEDS_A_HAND


def test_a_review_by_the_owner_answers_a_pull_request(check, monkeypatch):
    def github(path, token):
        if "/comments" in path:
            return [{"user": {"login": "someone"}}]
        if "/reviews" in path:
            return [{"user": {"login": check.OWNER}}]
        raise AssertionError(path)

    monkeypatch.setattr(check, "github", github)
    assert check.owner_answered(check.SKILL, _issue(5, "crmvet", pull=True), "token")
    assert not check.owner_answered(check.SKILL, _issue(6, "crmvet"), "token")  # an issue has no review


def test_a_smaller_repository_is_read_for_its_own_workflows_only(check, monkeypatch):
    repo = next(r for r in check.OTHER_REPOS if r.label == "cost-per-task")
    workflows = {
        repo.slug: [
            {"path": ".github/workflows/ci.yml", "state": "active"},
            {"path": ".github/workflows/old.yml", "state": "disabled_manually"},
            {"path": "dynamic/dependabot/dependabot-updates", "state": "active"},
        ]
    }
    _scripted(check, monkeypatch, other_workflows=workflows, failing="ci.yml")
    findings = [f for f in check.collect(NOW, "token") if f.where.startswith("cost-per-task")]
    assert [(f.where, f.level, f.what) for f in findings] == [
        ("cost-per-task: `ci.yml` on `main`", "hand", "last run failed")
    ]


def test_a_workflow_with_no_run_on_the_default_branch_says_nothing(check):
    repo = check.OTHER_REPOS[0]
    assert check.judge_other_workflow(repo, {"path": ".github/workflows/ci.yml"}, None) is None
    green = check.judge_other_workflow(repo, {"path": ".github/workflows/ci.yml"}, _run("2026-11-08", event="push"))
    assert (green.level, green.what) == ("ok", "green")


def test_a_late_job_that_github_switched_off_says_so(check):
    """GitHub disables a scheduled workflow after 60 days without activity in the repository."""
    late = check.judge_job(_weekly(check), _run("2026-10-05"), NOW, None, "disabled_inactivity")
    assert late.what == "late"
    assert "GitHub has this workflow as `disabled_inactivity`" in late.detail
    # A job that is off is not "new, not due yet", however recently it was added.
    added = NOW - dt.timedelta(days=2)
    assert check.judge_job(_weekly(check), None, NOW, added, "disabled_manually").what == "never ran"
    assert "GitHub has" not in check.judge_job(_weekly(check), _run("2026-10-05"), NOW, None, "active").detail


def test_the_state_of_a_workflow_is_asked_only_when_a_job_is_late_or_never_ran(check, monkeypatch):
    _scripted(check, monkeypatch)
    asked = []
    monkeypatch.setattr(check, "workflow_info", lambda repo, workflow, token: asked.append(workflow) or (None, ""))
    check.collect(NOW, "token")
    assert asked == []  # every job ran this morning: no extra call

    late = {"workflow_runs": [_run("2026-10-05")]}
    original = check.github
    monkeypatch.setattr(
        check, "github", lambda path, token: late if "/sync-engine.yml/runs" in path else original(path, token)
    )
    check.collect(NOW, "token")
    assert asked == ["sync-engine.yml"]
