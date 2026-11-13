#!/usr/bin/env python3
"""
check-family-jobs.py - One reading of every scheduled job in the five OptimNow
repositories, and of what each one left for a human.

Why: the family runs a dozen scheduled jobs in five repositories (DEPENDENCIES.md,
"The scheduled jobs"), and each reports trouble its own way: a red run, an issue with
a label, a pull request assigned to the maintainer. On 12 November 2026 two weekly pull
requests had been open for 17 days, a deploy had stopped behind a red default branch,
and nobody had been told. A failed scheduled run sends no mail anyone reads. This
script reads all of it in one pass and says, first, what needs a hand.

What it reads, through the GitHub REST API and four public endpoints:

  - the latest finished run of each scheduled workflow: failed, late (no run inside the
    age its cadence allows) or never run;
  - the latest CI run on each default branch: a red one stops that repository's deploy;
  - open pull requests a job opened (`github-actions[bot]`): each is a job that could
    not land its change and waits for a human;
  - open issues carrying an alarm label (`price-drift`, `companion-tools`, `mcp-parity`,
    `price-anomaly`, ...), and the open `content-update` issues waiting for triage;
  - in those five repositories and in seven smaller ones: every open issue or pull
    request written by someone else (not the owner, not a bot) that the owner has not
    answered, and, in the seven, the latest run of each workflow on the default branch;
  - the three hosted MCP servers (do they answer, with which version) and the day of
    the OptimToken catalogue.

What it never does: fix, merge, re-run or edit anything. Exit codes:

  0  nothing needs a hand
  1  at least one item needs a hand
  2  nothing wrong was seen, and part of it could not be read (no token for the
     private repository, a rate limit, an outage): "not read" is never "fine"

Token: GH_TOKEN or GITHUB_TOKEN, else `gh auth token` when the CLI is signed in, else
none. Without one the four public repositories are still read; the private one
(OptimToken's site) is reported as not read. A token that a repository refuses is
asked again without one, so a token scoped to a few repositories never hides a public
one. In a cloud routine the token covers the repositories checked out for the run:
the Monday routine checks out all five, which is what lets it read the private one.

  python scripts/check-family-jobs.py               report on stdout
  python scripts/check-family-jobs.py --output f.md also write it to a file
  python scripts/check-family-jobs.py --no-token    what an anonymous caller reads

Standard library only. Run by the Monday-morning routine (docs/DESIGN.md, "Family jobs
check"), and by hand whenever the question is "is everything running?".
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXIT_OK, EXIT_NEEDS_A_HAND, EXIT_NOT_READ = 0, 1, 2

API = "https://api.github.com"
USER_AGENT = "family-jobs-check/1.0"
TIMEOUT_SECONDS = 30
BOT = "github-actions[bot]"
PROTOCOL_VERSION = "2025-06-18"

DAILY, WEEKLY = 2, 8  # days a daily or weekly job may go without a finished run


@dataclass(frozen=True)
class Repo:
    slug: str  # owner/name as GitHub knows it today
    label: str
    branch: str
    alarm_labels: tuple[str, ...] = ()


SITE = Repo(
    "OptimNow/ai-pricing-hub",  # the checkout is still called cloud-sparkle-compare
    "OptimToken site",
    "main",
    ("mcp-parity", "price-anomaly", "price-provenance", "unpriced-namespace", "pipeline-watchdog"),
)
PRICING_MCP = Repo("OptimNow/ai-pricing-hub-mcp", "Pricing MCP", "master")
CALCULATOR = Repo("OptimNow/ai-roi-calculator", "ROI calculator", "main")
CALCULATOR_MCP = Repo("OptimNow/ai-roi-calculator-mcp", "ROI calculator MCP", "master")
SKILL = Repo("OptimNow/cloud-finops-skills", "Cloud FinOps skill", "main", ("price-drift", "companion-tools"))
REPOS = (SITE, PRICING_MCP, CALCULATOR, CALCULATOR_MCP, SKILL)

# Seven smaller repositories of the same account. They have no scheduled job on
# 2026-11-13 (one has a CI and a PyPI publish, the others nothing of their own), so
# they are read for two things only: a workflow whose last run on the default branch
# failed, and what other people opened there. A scheduled job added to one of them
# belongs in JOBS, with its cadence.
OTHER_REPOS = tuple(
    Repo(f"OptimNow/{name}", name, "main")
    for name in (
        "tagging-policy-generator",
        "finopsselfassessment",
        "ai-self-assessment",
        "awesome-finops-jmfontaine",
        "cost-per-task",
        "finops-mcp-resources",
        "awesome-remote-mcp-servers",
    )
)
OWNER = "OptimNow"  # what this login wrote or answered is not "someone else waiting"


@dataclass(frozen=True)
class Job:
    repo: Repo
    workflow: str  # file name under .github/workflows/
    what: str
    max_age_days: int


JOBS = (
    Job(SITE, "refresh-llm-fallback.yml", "daily catalogue refresh", DAILY),
    Job(SITE, "mcp-parity.yml", "daily comparison of the pricing MCP with the site", DAILY),
    Job(SITE, "refresh-bedrock-matrix.yml", "weekly Bedrock matrix refresh", WEEKLY),
    Job(SITE, "refresh-elo-scores.yml", "weekly ELO scores refresh", WEEKLY),
    Job(SITE, "refresh-aws-savings-plans.yml", "weekly AWS Savings Plan rates refresh", WEEKLY),
    Job(CALCULATOR, "refresh-model-snapshot.yml", "weekly price snapshot", WEEKLY),
    Job(CALCULATOR_MCP, "sync-engine.yml", "weekly engine sync from the calculator", WEEKLY),
    Job(PRICING_MCP, "refresh-fallback.yml", "weekly refresh of the fallback snapshots", WEEKLY),
    Job(SKILL, "price-drift.yml", "weekly check of the written list prices", WEEKLY),
    Job(SKILL, "companion-tools.yml", "weekly check of the companion tool lists", WEEKLY),
    Job(SKILL, "mcp-install-smoke.yml", "weekly clean-install smoke of the PyPI package", WEEKLY),
)

# A red default branch stops the deploy that follows it.
CI_WORKFLOWS = ((SITE, "ci.yml"), (PRICING_MCP, "ci.yml"), (CALCULATOR_MCP, "ci.yml"), (SKILL, "ci.yml"))

SERVERS = (
    ("Cloud FinOps connector", "https://mcp.optimnow.io/mcp"),
    ("Pricing MCP", "https://optimtoken-mcp.optimnow.io/mcp"),
    ("ROI calculator MCP", "https://airoicalculator-mcp.optimnow.io/mcp"),
)
CATALOGUE_URL = "https://optimtoken.optimnow.io/api/llm-models?limit=1"
CATALOGUE_MAX_AGE_DAYS = 2
TRIAGE_LABEL = "content-update"  # in the skill repository: scan issues waiting for a human


class NotRead(Exception):
    """The answer could not be obtained: an outage, a rate limit, no access."""


@dataclass
class Finding:
    """One line of the report. `level` is "hand", "unread" or "ok"."""

    level: str
    where: str
    what: str
    detail: str
    url: str = ""


# ----------------------------------------------------------------------------- reading


def find_token() -> str | None:
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(name):
            return os.environ[name]
    if shutil.which("gh"):
        try:
            out = subprocess.run(
                ["gh", "auth", "token"], capture_output=True, text=True, timeout=15, check=False
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    return None


def _get(path: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def github(path: str, token: str | None) -> Any:
    """GET one GitHub API path. Raises :class:`NotRead` with the reason.

    A token that is refused is not the end of it. A cloud routine's token covers the
    repositories checked out for the run and nothing else: on 2026-11-12 it answered 403
    for the three public repositories it had not been given, which an anonymous caller
    reads freely. So a refusal with a token is asked again without one, and only a
    repository that is closed to both (the site's, when it was not checked out) is
    reported as not read.
    """
    try:
        return _get(path, token)
    except urllib.error.HTTPError as exc:
        if token and exc.code in (401, 403, 404):
            try:
                return _get(path, None)
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                pass  # the first refusal is the one worth reporting
        if exc.code == 404:
            reason = "not found" if token else "not found without a token (a private repository reads so)"
        elif exc.code in (401, 403, 429):
            reason = f"refused, HTTP {exc.code} (rate limit, or a token that does not cover this repository)"
        else:
            reason = f"HTTP {exc.code}"
        raise NotRead(reason) from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise NotRead(type(exc).__name__) from None


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def latest_finished_run(repo: Repo, workflow: str, events: tuple[str, ...], token: str | None) -> dict | None:
    """The newest completed run of a workflow on the default branch, for these events."""
    query = urllib.parse.urlencode({"branch": repo.branch, "per_page": 20})
    data = github(f"/repos/{repo.slug}/actions/workflows/{workflow}/runs?{query}", token)
    for run in data.get("workflow_runs", []):
        if run.get("status") == "completed" and run.get("event") in events:
            return run
    return None


def workflow_info(repo: Repo, workflow: str, token: str | None) -> tuple[dt.datetime | None, str]:
    """When GitHub first saw this workflow file, and its state ("active",
    "disabled_inactivity", "disabled_manually", ...). `(None, "")` when it does not say."""
    try:
        data = github(f"/repos/{repo.slug}/actions/workflows/{workflow}", token)
        return parse_time(data["created_at"]), str(data.get("state") or "")
    except (NotRead, KeyError, ValueError):
        return None, ""


def is_someone_else(user: dict | None) -> bool:
    """Not the owner and not an automation: a person whose issue is waiting for an answer."""
    user = user or {}
    login = str(user.get("login") or "")
    return bool(login) and login != OWNER and user.get("type") != "Bot" and not login.endswith("[bot]")


def owner_answered(repo: Repo, item: dict, token: str | None) -> bool:
    """Has the owner commented on this issue or pull request, or reviewed the pull request?"""
    number = item["number"]
    comments = github(f"/repos/{repo.slug}/issues/{number}/comments?per_page=100", token)
    if any((c.get("user") or {}).get("login") == OWNER for c in comments):
        return True
    if "pull_request" in item:
        reviews = github(f"/repos/{repo.slug}/pulls/{number}/reviews?per_page=100", token)
        return any((r.get("user") or {}).get("login") == OWNER for r in reviews)
    return False


# ----------------------------------------------------------------------------- judging


def judge_job(
    job: Job,
    run: dict | None,
    now: dt.datetime,
    registered: dt.datetime | None = None,
    state: str = "",
) -> Finding:
    """`registered` is when GitHub first saw the workflow file; it only matters when
    there is no run: a job added this week has not had its turn yet. `state` is what
    GitHub says of the workflow: it switches a scheduled one off after 60 days without
    activity in the repository, and a job that is off is the reason it is late."""
    where = f"{job.repo.label}: {job.what} (`{job.workflow}`)"
    off = ""
    if state not in ("", "active"):
        off = f" GitHub has this workflow as `{state}`: it will not run until it is enabled again."
    if run is None:
        if not off and registered is not None and now - registered <= dt.timedelta(days=job.max_age_days):
            return Finding(
                "ok", where, "not due yet", f"added on {registered.strftime('%Y-%m-%d')}, no run so far"
            )
        return Finding("hand", where, "never ran", "no finished run on the default branch." + off)
    started = parse_time(run["created_at"])
    age = now - started
    day = started.strftime("%Y-%m-%d")
    url = run.get("html_url", "")
    if run.get("conclusion") != "success":
        return Finding("hand", where, "last run failed", f"{run.get('conclusion')} on {day}", url)
    if age > dt.timedelta(days=job.max_age_days):
        return Finding(
            "hand",
            where,
            "late",
            f"last run {day}, {age.days} days ago; expected within {job.max_age_days}." + off,
            url,
        )
    return Finding("ok", where, "ran", f"success on {day}", url)


def judge_ci(repo: Repo, run: dict | None) -> Finding:
    where = f"{repo.label}: CI on `{repo.branch}`"
    if run is None:
        return Finding("unread", where, "no finished run found", "nothing to judge")
    day = parse_time(run["created_at"]).strftime("%Y-%m-%d")
    url = run.get("html_url", "")
    if run.get("conclusion") != "success":
        return Finding(
            "hand", where, "default branch is red", f"{run.get('conclusion')} on {day}: the deploy behind it is stopped", url
        )
    return Finding("ok", where, "green", f"success on {day}", url)


def judge_pulls(repo: Repo, pulls: list[dict], now: dt.datetime) -> list[Finding]:
    """A pull request opened by a job is a change that could not land by itself."""
    findings = []
    for pull in pulls:
        if (pull.get("user") or {}).get("login") != BOT:
            continue
        days = (now - parse_time(pull["created_at"])).days
        findings.append(
            Finding(
                "hand",
                f"{repo.label}: pull request #{pull['number']}",
                "a job's change waits for you",
                f"\"{pull['title']}\", open for {days} day(s)",
                pull.get("html_url", ""),
            )
        )
    return findings


def judge_alarms(repo: Repo, label: str, issues: list[dict], now: dt.datetime) -> list[Finding]:
    findings = []
    for issue in issues:
        if "pull_request" in issue:  # the issues API lists pull requests too
            continue
        days = (now - parse_time(issue["created_at"])).days
        findings.append(
            Finding(
                "hand",
                f"{repo.label}: issue #{issue['number']} (`{label}`)",
                "an alarm is open",
                f"\"{issue['title']}\", open for {days} day(s)",
                issue.get("html_url", ""),
            )
        )
    return findings


def judge_other_workflow(repo: Repo, workflow: dict, run: dict | None) -> Finding | None:
    """One workflow of a smaller repository: only its last run on the default branch."""
    name = str(workflow.get("path") or "").rsplit("/", 1)[-1]
    where = f"{repo.label}: `{name}` on `{repo.branch}`"
    if run is None:
        return None  # nothing ran on the default branch: nothing to say
    day = parse_time(run["created_at"]).strftime("%Y-%m-%d")
    if run.get("conclusion") != "success":
        return Finding("hand", where, "last run failed", f"{run.get('conclusion')} on {day}", run.get("html_url", ""))
    return Finding("ok", where, "green", f"success on {day}", run.get("html_url", ""))


def judge_external(repo: Repo, item: dict, answered: bool, now: dt.datetime) -> Finding:
    """An open issue or pull request written by someone else."""
    kind = "pull request" if "pull_request" in item else "issue"
    days = (now - parse_time(item["created_at"])).days
    where = f"{repo.label}: {kind} #{item['number']} by {item['user']['login']}"
    detail = f"\"{item['title']}\", open for {days} day(s)"
    if answered:
        return Finding("ok", where, "open, and you have answered", detail, item.get("html_url", ""))
    return Finding("hand", where, "someone is waiting for your answer", detail, item.get("html_url", ""))


def judge_triage(issues: list[dict], now: dt.datetime) -> Finding:
    where = f"{SKILL.label}: `{TRIAGE_LABEL}` issues"
    issues = [i for i in issues if "pull_request" not in i]
    if not issues:
        return Finding("ok", where, "none open", "nothing waits for triage")
    oldest = min(parse_time(i["created_at"]) for i in issues)
    days = (now - oldest).days
    detail = f"{len(issues)} open, the oldest for {days} day(s)"
    # One scan issue a week is the normal state; three, or one past a fortnight, is a backlog.
    if len(issues) >= 3 or days > 15:
        return Finding("hand", where, "scan issues are piling up", detail, issues[-1].get("html_url", ""))
    return Finding("ok", where, "within the week's triage", detail)


def judge_catalogue(meta: dict, now: dt.datetime) -> Finding:
    where = "OptimToken catalogue (live API)"
    day = str(meta.get("hostPricingAsOf") or "")
    try:
        age = (now.date() - dt.date.fromisoformat(day)).days
    except ValueError:
        return Finding("unread", where, "no usable date", f"hostPricingAsOf is {day!r}")
    if age > CATALOGUE_MAX_AGE_DAYS:
        return Finding("hand", where, "stale", f"host prices read on {day}, {age} days ago: the daily refresh has stopped")
    return Finding("ok", where, "fresh", f"host prices read on {day}, {meta.get('catalogTotal', '?')} models")


# -------------------------------------------------------------------------- live calls


def read_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise NotRead(getattr(exc, "reason", None) and str(exc.reason) or type(exc).__name__) from None


def server_version(url: str) -> str:
    """`name version` as the MCP server announces itself. Raises :class:`NotRead`."""
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "family-jobs-check", "version": "1.0"},
            },
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise NotRead(f"HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise NotRead(getattr(exc, "reason", None) and str(exc.reason) or type(exc).__name__) from None
    payloads = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")] or [text]
    for payload in payloads:
        try:
            info = json.loads(payload)["result"]["serverInfo"]
            return f"{info['name']} {info['version']}"
        except (ValueError, KeyError, TypeError):
            continue
    raise NotRead("no serverInfo in the answer")


# -------------------------------------------------------------------------- the report


def collect(now: dt.datetime, token: str | None) -> list[Finding]:
    findings: list[Finding] = []

    for job in JOBS:
        where = f"{job.repo.label}: {job.what} (`{job.workflow}`)"
        try:
            run = latest_finished_run(job.repo, job.workflow, ("schedule", "workflow_dispatch"), token)
            finding = judge_job(job, run, now)
            if finding.level == "hand" and finding.what in ("late", "never ran"):
                # Only then is it worth one more call: is the job new, or switched off?
                registered, state = workflow_info(job.repo, job.workflow, token)
                finding = judge_job(job, run, now, registered, state)
            findings.append(finding)
        except NotRead as exc:
            findings.append(Finding("unread", where, "not read", str(exc)))

    for repo, workflow in CI_WORKFLOWS:
        try:
            run = latest_finished_run(repo, workflow, ("push", "workflow_dispatch"), token)
            findings.append(judge_ci(repo, run))
        except NotRead as exc:
            findings.append(Finding("unread", f"{repo.label}: CI on `{repo.branch}`", "not read", str(exc)))

    for repo in REPOS:
        try:
            pulls = github(f"/repos/{repo.slug}/pulls?state=open&per_page=100", token)
            findings.extend(judge_pulls(repo, pulls, now))
        except NotRead as exc:
            findings.append(Finding("unread", f"{repo.label}: open pull requests", "not read", str(exc)))
        for label in repo.alarm_labels:
            try:
                query = urllib.parse.urlencode({"state": "open", "labels": label, "per_page": 50})
                findings.extend(judge_alarms(repo, label, github(f"/repos/{repo.slug}/issues?{query}", token), now))
            except NotRead as exc:
                findings.append(Finding("unread", f"{repo.label}: `{label}` issues", "not read", str(exc)))

    for repo in OTHER_REPOS:
        try:
            workflows = github(f"/repos/{repo.slug}/actions/workflows?per_page=100", token).get("workflows", [])
        except NotRead as exc:
            findings.append(Finding("unread", f"{repo.label}: workflows", "not read", str(exc)))
            continue
        for workflow in workflows:
            # GitHub's own (Dependabot, the dependency graph) live under dynamic/: not ours.
            path = str(workflow.get("path") or "")
            if not path.startswith(".github/workflows/") or workflow.get("state") != "active":
                continue
            name = path.rsplit("/", 1)[-1]
            try:
                run = latest_finished_run(repo, name, ("push", "schedule", "workflow_dispatch"), token)
            except NotRead as exc:
                findings.append(Finding("unread", f"{repo.label}: `{name}`", "not read", str(exc)))
                continue
            finding = judge_other_workflow(repo, workflow, run)
            if finding:
                findings.append(finding)

    for repo in REPOS + OTHER_REPOS:
        try:
            items = github(f"/repos/{repo.slug}/issues?state=open&per_page=100", token)
            for item in items:
                if is_someone_else(item.get("user")):
                    findings.append(judge_external(repo, item, owner_answered(repo, item, token), now))
        except NotRead as exc:
            findings.append(
                Finding("unread", f"{repo.label}: issues and pull requests by others", "not read", str(exc))
            )

    try:
        query = urllib.parse.urlencode({"state": "open", "labels": TRIAGE_LABEL, "per_page": 50})
        findings.append(judge_triage(github(f"/repos/{SKILL.slug}/issues?{query}", token), now))
    except NotRead as exc:
        findings.append(Finding("unread", f"{SKILL.label}: `{TRIAGE_LABEL}` issues", "not read", str(exc)))

    for label, url in SERVERS:
        try:
            findings.append(Finding("ok", f"Live server: {label}", "answers", server_version(url), url))
        except NotRead as exc:
            findings.append(Finding("hand", f"Live server: {label}", "does not answer", str(exc), url))

    try:
        findings.append(judge_catalogue(read_json(CATALOGUE_URL).get("meta", {}), now))
    except NotRead as exc:
        findings.append(Finding("hand", "OptimToken catalogue (live API)", "does not answer", str(exc), CATALOGUE_URL))

    return findings


def render(findings: list[Finding], now: dt.datetime, with_token: bool) -> str:
    hand = [f for f in findings if f.level == "hand"]
    unread = [f for f in findings if f.level == "unread"]
    fine = [f for f in findings if f.level == "ok"]

    def line(finding: Finding) -> str:
        link = f" ({finding.url})" if finding.url else ""
        return f"- **{finding.where}**: {finding.what}. {finding.detail}{link}"

    out = [
        "# Scheduled jobs of the OptimNow repositories",
        "",
        f"Read on {now.strftime('%Y-%m-%d %H:%M')} UTC, "
        + ("with a GitHub token." if with_token else "without a GitHub token (public data only)."),
        "",
    ]
    if hand:
        out.append(f"**{len(hand)} item(s) need a hand.**")
    elif unread:
        out.append("**Nothing wrong was seen, but not everything could be read.**")
    else:
        out.append("**Nothing needs a hand.**")
    if hand:
        out += ["", "## Needs a hand", ""] + [line(f) for f in hand]
    if unread:
        out += ["", "## Not read (not the same as fine)", ""] + [line(f) for f in unread]
    out += ["", f"## Fine ({len(fine)})", ""] + [line(f) for f in fine]
    return "\n".join(out) + "\n"


def exit_code(findings: list[Finding]) -> int:
    if any(f.level == "hand" for f in findings):
        return EXIT_NEEDS_A_HAND
    if any(f.level == "unread" for f in findings):
        return EXIT_NOT_READ
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--output", type=Path, help="also write the markdown report to this file")
    parser.add_argument("--no-token", action="store_true", help="read as an anonymous caller would: public data only")
    args = parser.parse_args(argv)

    now = dt.datetime.now(dt.timezone.utc)
    token = None if args.no_token else find_token()
    findings = collect(now, token)
    report = render(findings, now, with_token=bool(token))
    sys.stdout.write(report)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
