#!/usr/bin/env python3
"""check-detection-readonly.py - a playbook's Detection step only reads.

Why this exists
---------------
The skill tells a model that it may run a playbook's Detection step through an
account connector the user enabled, and never a Fix step
(references/finops-waste-detection-playbooks.md, "Running a detection through a
connected account"). That holds only if no Detection block carries a command
that changes something. Until this check, it held because every author happened
to write read commands: nothing stopped a `delete-volume` pasted one section too
high.

What it checks
--------------
Every fenced block inside the "## Detection" section of every playbook:

  - a provider CLI call (aws, az, gcloud, gsutil, bq, kubectl, oci) uses a read
    verb. The list is closed: a verb this script does not know fails, so a new
    kind of command is a decision somebody makes here, not a silent pass;
  - a SQL block holds only SELECT / WITH / SHOW / DESCRIBE / EXPLAIN statements
    and no INSERT, UPDATE, DELETE, MERGE, DROP, TRUNCATE, ALTER, CREATE, GRANT;
  - a Kusto block holds no control command (a line starting with a dot);
  - PowerShell calls use a reading verb (Get-, Search-, Select-, ...);
  - the fence language is one this script knows.

It also fails a playbook that has no "## Detection" section, since it cannot
vouch for it.

What it does NOT check
----------------------
  - Prose, and commands quoted inline in a sentence.
  - The Fix section, which is allowed to change things: that is its job.
  - Reference files. Their detection examples are illustrations inside a guide;
    the promise above is made for playbooks.
  - What a read costs. A SELECT over a full billing table passes.
  - Local shell plumbing (a temporary file, jq, awk): only cloud CLIs count.

`gcloud container clusters get-credentials` is allowed although it writes a
local kubeconfig entry: it changes nothing in the cloud account, and the kubectl
reads after it cannot run without it.

Usage: python scripts/check-detection-readonly.py [--list]
  --list   print every command and statement found, with its verdict
Exit 0 when clean, 1 on a finding, 2 on a usage or self-test error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYBOOKS = ROOT / "plugins" / "cloud-finops" / "skills" / "cloud-finops" / "playbooks"

CLIS = ("aws", "az", "gcloud", "gsutil", "bq", "kubectl", "oci")
SHELL_LANGS = {"bash", "sh", "shell", "console", "zsh"}
SQL_LANGS = {"sql"}
KUSTO_LANGS = {"kusto", "kql"}
POWERSHELL_LANGS = {"powershell", "pwsh", "ps1"}
# Query languages and samples that cannot change anything.
INERT_LANGS = {"promql", "text", "json", "yaml", "csv", "logql"}

# One read verb is enough for a call to pass; any mutating word fails it first.
READ_VERBS = {
    "list", "show", "describe", "get", "query", "read", "ls", "du", "stat", "top", "logs",
    "search", "lookup", "explain", "version", "view", "cat", "head", "tail", "export",
    "api-resources", "cluster-info", "summarize", "exists",
}
READ_PREFIXES = (
    "describe-", "list-", "get-", "search-", "lookup-", "batch-get-", "select-", "head-",
    "show-", "check-", "estimate-", "preview-",
)
# Read queries whose API verb does not look like one.
READ_EXACT = {
    "start-query",             # aws logs start-query: runs a Logs Insights query
    "start-query-execution",   # aws athena: runs the statement given (checked as SQL when inline)
    "get-credentials",         # gcloud container clusters: local kubeconfig only (see docstring)
    "filter-log-events",
    "simulate-principal-policy",
}
MUTATING_WORDS = {
    "create", "delete", "update", "set", "add", "remove", "patch", "apply", "put", "start", "stop",
    "restart", "run", "exec", "deploy", "resize", "scale", "attach", "detach", "modify", "tag",
    "untag", "purchase", "cancel", "terminate", "reboot", "release", "associate", "disassociate",
    "enable", "disable", "register", "deregister", "import", "rm", "mb", "rb", "cp", "mv", "sync",
    "edit", "replace", "annotate", "label", "drain", "cordon", "uncordon", "rollout", "deallocate",
    "restore", "rotate", "revoke", "grant", "assign", "move", "copy", "insert", "load", "mk",
    "truncate", "exchange", "sell", "buy", "accept", "reject", "invoke", "send", "publish",
}
MUTATING_PREFIXES = tuple(f"{w}-" for w in sorted(MUTATING_WORDS))

SQL_READ_STARTS = {"select", "with", "show", "describe", "desc", "explain"}
SQL_WRITE = re.compile(
    r"\b(insert\s+into|update\s+[\w.`\"]+\s+set|delete\s+from|merge\s+into|truncate\s+table|"
    r"drop\s+(table|view|schema|database|warehouse)|alter\s+\w+|"
    r"create\s+(or\s+replace\s+)?(temp\w*\s+|external\s+)?(table|view|schema|database|function)|"
    r"grant\s+|revoke\s+|copy\s+into|unload\s+)",
    re.I,
)
POWERSHELL_READ = ("Get-", "Search-", "Select-", "Where-", "Sort-", "Group-", "Measure-", "Format-",
                   "ForEach-", "Export-Csv", "ConvertTo-", "ConvertFrom-", "Write-", "Out-", "Test-",
                   "Connect-", "Import-Module", "Invoke-AzResourceGraphQuery", "Search-AzGraph")
POWERSHELL_CMD = re.compile(r"\b([A-Z][a-z]+-[A-Za-z]+)\b")

CLI_CALL = re.compile(r"(?:^|[\s;|&(`{])(" + "|".join(CLIS) + r")\s+")
SEPARATORS = re.compile(r"\s(?:\|\||&&|\||;|>|>>|2>|<)\s|\)|`")


def detection_blocks(text: str):
    """Yield (lang, first_line_number, body) for each fenced block under ## Detection."""
    inside = False
    lang = None
    start = 0
    body: list[str] = []
    found_heading = False
    for number, line in enumerate(text.splitlines(), 1):
        if lang is None and line.startswith("## "):
            inside = line.strip().lower() == "## detection"
            found_heading = found_heading or inside
            continue
        if not inside:
            continue
        fence = re.match(r"^\s*```+\s*([\w+-]*)\s*$", line)
        if fence and lang is None:
            lang, start, body = fence.group(1).lower(), number, []
        elif fence:
            yield lang, start, "\n".join(body)
            lang = None
        elif lang is not None:
            body.append(line)
    if not found_heading:
        yield None, 0, ""


def positional(rest: str) -> list[str]:
    """The words of one CLI call up to its first shell separator, options dropped."""
    rest = SEPARATORS.split(" " + rest + " ", 1)[0]
    words: list[str] = []
    skip_value = False
    for token in rest.split():
        if skip_value:
            skip_value = False
            continue
        if token.startswith("-"):
            # `--region eu-west-1` carries a value; `--region=eu-west-1` and flags do not.
            skip_value = "=" not in token and token.lstrip("-") in {
                "region", "profile", "output", "o", "n", "namespace", "context", "project",
                "subscription", "format", "query", "filters", "filter", "g", "resource-group",
            }
            continue
        if re.match(r"^[\"'$\[{(]", token):
            break  # a quoted argument or a substitution: the verb is behind us
        words.append(token)
    return words


def judge_cli(cli: str, rest: str) -> tuple[bool, str]:
    words = positional(rest)
    shown = f"{cli} {' '.join(words[:5])}".strip()
    if cli == "aws":
        # aws <service> <operation>; `aws s3 ls` and friends use bare words.
        if len(words) < 2:
            return False, f"{shown}: no operation found"
        operation = words[1]
        if operation in READ_EXACT or operation in READ_VERBS or operation.startswith(READ_PREFIXES):
            return True, shown
        return False, f"{shown}: '{operation}' is not a read operation"
    lowered = [w.lower() for w in words]
    for word in lowered:
        if word in READ_EXACT:
            return True, shown
        if word in MUTATING_WORDS or word.startswith(MUTATING_PREFIXES):
            return False, f"{shown}: '{word}' changes something"
    for word in lowered:
        if word in READ_VERBS or word.startswith(READ_PREFIXES):
            return True, shown
    return False, f"{shown}: no known read verb (teach READ_VERBS if this one only reads)"


def check_shell(body: str):
    joined = re.sub(r"\\\r?\n\s*", " ", body)
    for line in joined.splitlines():
        code = line.split(" #", 1)[0] if not line.lstrip().startswith("#") else ""
        calls = list(CLI_CALL.finditer(code))
        for index, match in enumerate(calls):
            # One call runs to the next CLI name on the line: `aws ... | xargs aws ...` is two.
            end = calls[index + 1].start() if index + 1 < len(calls) else len(code)
            yield judge_cli(match.group(1), code[match.end():end])


def check_sql(body: str):
    code = re.sub(r"/\*.*?\*/", " ", body, flags=re.S)
    code = "\n".join(line.split("--", 1)[0] for line in code.splitlines())
    code = re.sub(r"'(?:[^']|'')*'", "''", code)  # string literals cannot hide a keyword
    for statement in (s.strip() for s in code.split(";")):
        if not statement:
            continue
        first = re.match(r"[A-Za-z]+", statement.lstrip("( \n\t"))
        head = " ".join(statement.split())[:60]
        if not first or first.group(0).lower() not in SQL_READ_STARTS:
            yield False, f"SQL statement does not start with a read keyword: {head}"
            continue
        write = SQL_WRITE.search(statement)
        if write:
            yield False, f"SQL statement writes ({write.group(0).strip()}): {head}"
        else:
            yield True, f"SQL {first.group(0).upper()}: {head}"


def check_kusto(body: str):
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(".") and not stripped.startswith(".."):
            yield False, f"Kusto control command: {stripped[:60]}"
    yield True, "Kusto query"


def check_powershell(body: str):
    for line in body.splitlines():
        code = line.split("#", 1)[0]
        for name in POWERSHELL_CMD.findall(code):
            ok = name.startswith(POWERSHELL_READ) or name in POWERSHELL_READ
            yield ok, (f"PowerShell {name}" if ok else f"PowerShell {name}: not a reading cmdlet")


def check_block(lang: str, body: str):
    if lang in SQL_LANGS:
        yield from check_sql(body)
    elif lang in KUSTO_LANGS:
        yield from check_kusto(body)
    elif lang in POWERSHELL_LANGS:
        yield from check_powershell(body)
    elif lang in SHELL_LANGS or lang == "":
        # An unlabelled block is an output sample unless it calls a CLI.
        yield from check_shell(body)
    elif lang in INERT_LANGS:
        return
    else:
        yield False, f"fence language '{lang}' is unknown to this check"


SELF_TEST = [
    ("bash", "aws ec2 describe-volumes --filters Name=status,Values=available", True),
    ("bash", "for b in $(aws s3api list-buckets --query 'Buckets[].Name' --output text); do\n"
             "  aws s3api get-bucket-versioning --bucket \"$b\"\ndone", True),
    ("bash", "aws ec2 delete-volume --volume-id vol-1", False),
    ("bash", "aws ec2 describe-volumes | xargs -I{} aws ec2 delete-volume --volume-id {}", False),
    ("bash", "aws --region eu-west-1 ec2 \\\n  describe-nat-gateways", True),
    ("bash", "az disk list --query \"[?diskState=='Unattached']\" -o table", True),
    ("bash", "az disk delete --name d1 --resource-group rg --yes", False),
    ("bash", "az graph query -q \"Resources | where type =~ 'microsoft.compute/disks'\"", True),
    ("bash", "gcloud compute disks list --filter='-users:*'", True),
    ("bash", "gcloud compute disks delete d1 --zone europe-west1-b", False),
    ("bash", "gcloud container clusters get-credentials c1 --region europe-west1", True),
    ("bash", "kubectl get pods -A -o json", True),
    ("bash", "kubectl delete pod p1", False),
    ("bash", "kubectl frobnicate pods", False),
    ("", "vol-0abc  500  2025-03-02", True),
    ("sql", "-- a comment\nSELECT a FROM t WHERE b = 'delete from x';", True),
    ("sql", "WITH x AS (SELECT 1) SELECT * FROM x", True),
    ("sql", "DELETE FROM t WHERE a = 1", False),
    ("sql", "SELECT 1; DROP TABLE t", False),
    ("sql", "CREATE TABLE t AS SELECT 1", False),
    ("kusto", "Resources\n| where type =~ 'microsoft.compute/disks'\n| project name", True),
    ("kusto", ".drop table T", False),
    ("powershell", "Get-AzDisk | Where-Object { $_.DiskState -eq 'Unattached' }", True),
    ("powershell", "Get-AzDisk | Remove-AzDisk -Force", False),
    ("promql", "sum(rate(container_cpu_usage_seconds_total[5m]))", True),
    ("python", "boto3.client('ec2').delete_volume(VolumeId='vol-1')", False),
]


def self_test() -> list[str]:
    problems = []
    for lang, body, expected in SELF_TEST:
        verdicts = list(check_block(lang, body))
        passed = all(ok for ok, _ in verdicts)
        if passed != expected:
            problems.append(f"self-test: {lang or 'unlabelled'} block {body[:50]!r} "
                            f"{'passed' if passed else 'failed'}, expected the opposite")
    return problems


def main() -> int:
    show = "--list" in sys.argv[1:]
    unknown = [a for a in sys.argv[1:] if a != "--list"]
    if unknown:
        print(f"usage: {Path(__file__).name} [--list]", file=sys.stderr)
        return 2
    broken = self_test()
    if broken:
        print("\n".join(broken), file=sys.stderr)
        print("FAIL: the check no longer tells a read from a write; fix it before trusting it.", file=sys.stderr)
        return 2

    files = sorted(p for p in PLAYBOOKS.glob("*.md") if p.name != "README.md")
    findings: list[str] = []
    blocks = commands = 0
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        for lang, line, body in detection_blocks(path.read_text(encoding="utf-8")):
            if lang is None:
                findings.append(f"{rel}: no '## Detection' section")
                continue
            blocks += 1
            for ok, what in check_block(lang, body):
                commands += 1
                if show:
                    print(f"{'ok  ' if ok else 'FAIL'} {rel}:{line} {what}")
                if not ok:
                    findings.append(f"{rel}:{line}: {what}")
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        print(
            f"\n{len(findings)} finding(s). A Detection step must be safe to run through an account "
            "connector: move the command to the Fix section, or, if it only reads, teach this script "
            "its verb.",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {len(files)} playbooks, {blocks} Detection blocks, {commands} commands and statements, all read-only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
