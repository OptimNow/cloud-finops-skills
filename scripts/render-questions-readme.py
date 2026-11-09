#!/usr/bin/env python3
"""Render the README's "What you can ask, by role" block from the question index.

Every question tagged with a `persona` in a reference's or playbook's
`questions:` frontmatter is listed under its role, linked to the file that
declares it and to the files its `also` entry names. The block sits between
two HTML markers in README.md; the heading and the prose around it stay
hand-written. Same pattern as scripts/business-coverage.sh: the frontmatter is
the source of truth, the README is generated, and CI fails on a stale block.

Usage:
    python scripts/render-questions-readme.py           Rewrite the block in README.md
    python scripts/render-questions-readme.py --check   Exit 1 if the block is stale

Needs PyYAML (installed with the MCP server's dev extras).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "plugins" / "cloud-finops" / "skills" / "cloud-finops"
README = REPO_ROOT / "README.md"
START = "<!-- questions-by-role:start -->"
END = "<!-- questions-by-role:end -->"
ROLES = (
    ("FinOps lead", "FinOps lead"),
    ("Finance and procurement", "Finance and procurement"),
    ("Engineering and platform", "Engineering and platform"),
    ("AI product owner", "AI product owner"),
    ("Executive", "Executive (CTO, CIO, CFO)"),
)


def fail_run(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(2)


def frontmatter(path: Path) -> dict:
    import yaml

    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    return yaml.safe_load(text[4:end]) or {} if end != -1 else {}


def link(name: str, kinds: dict[str, str]) -> str:
    kind = kinds[name]
    rel = f"plugins/cloud-finops/skills/cloud-finops/{kind}/{name}.md"
    label = f"{name}.md" if kind == "references" else name
    return f"[{label}]({rel})"


def render() -> str:
    try:
        import yaml  # noqa: F401
    except ImportError:
        fail_run("PyYAML is required (pip install pyyaml).")
    kinds: dict[str, str] = {}
    entries: dict[str, list[tuple[str, str, list[str]]]] = {role: [] for role, _ in ROLES}
    for kind in ("references", "playbooks"):
        for path in sorted((SKILL / kind).glob("*.md")):
            if path.name == "README.md":
                continue
            kinds[path.stem] = kind
    for name, kind in sorted(kinds.items()):
        value = frontmatter(SKILL / kind / f"{name}.md").get("questions") or []
        for entry in value:
            if not isinstance(entry, dict) or not entry.get("persona"):
                continue
            persona = entry["persona"]
            if persona not in entries:
                fail_run(f"{kind}/{name}.md: persona {persona!r} is not a README role")
            also = entry.get("also") or []
            for other in also:
                if other not in kinds:
                    fail_run(f"{kind}/{name}.md: `also` names {other!r}, which does not exist")
            entries[persona].append((name, entry["q"], list(also)))

    lines = [START]
    for role, heading in ROLES:
        if not entries[role]:
            continue
        lines += ["", f"**{heading}**", ""]
        for name, question, also in entries[role]:
            links = ", ".join(link(n, kinds) for n in [name, *also])
            lines.append(f'- "{question}" ({links})')
    lines += ["", END]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    check = "--check" in argv[1:]
    text = README.read_text(encoding="utf-8").replace("\r\n", "\n")
    start, end = text.find(START), text.find(END)
    if start == -1 or end == -1 or end < start:
        fail_run(f"README.md has no {START} / {END} markers in order.")
    block = render()
    new_text = text[:start] + block + text[end + len(END) :]
    if new_text == text:
        print("OK: README role block is in sync with the question index.")
        return 0
    if check:
        print(
            "FAIL: README \"What you can ask, by role\" block is stale. Run "
            "`python scripts/render-questions-readme.py` and commit README.md.",
            file=sys.stderr,
        )
        return 1
    README.write_text(new_text, encoding="utf-8", newline="\n")
    print("README role block rewritten from the question index.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
