#!/usr/bin/env python3
"""Render the FinOps Framework capability coverage as a committed SVG.

Companion to fcp-coverage.sh: that script is the source of truth (it parses
the reference frontmatter and emits fcp-coverage.md, CI-gated), this one
renders the committed matrix as assets/fcp-coverage.svg for the README.
Parsing fcp-coverage.md rather than the frontmatter keeps a single chain:
frontmatter -> fcp-coverage.md (--check) -> SVG (--check). A dashed cell is
a deliberate gap recorded in docs/ROADMAP.md, not missing data.

Usage:
    python scripts/render-fcp-heatmap.py           Write assets/fcp-coverage.svg
    python scripts/render-fcp-heatmap.py --check   Fail if the committed SVG
                                                   differs from a fresh render
"""

from __future__ import annotations

import re
import sys
from xml.sax.saxutils import escape
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_FILE = REPO_ROOT / "fcp-coverage.md"
OUT_FILE = REPO_ROOT / "assets" / "fcp-coverage.svg"

# The FinOps Framework 2026 has 4 Domains and 22 Capabilities, and
# fcp-coverage.sh renders a line for every one of them - so a parse that yields
# any other number means the matrix format moved, not that the framework did.
# Asserted because the row regex silently skips what it does not match: a
# formatting change in fcp-coverage.md would have shrunk the SVG on both sides
# of --check (fresh render and committed file agree, both wrong) and passed CI
# green with capabilities missing from the README card. Update these two
# constants only when the FinOps Foundation actually changes the framework, in
# step with the CANONICAL table in scripts/fcp-coverage.sh.
CANONICAL_DOMAINS = 4
CANONICAL_CAPABILITIES = 22

# Same palette as render-coverage-heatmap.py so the two READMEs cards read
# as one family.
PRIMARY_FILL = "#ace849"
SECONDARY_FILL = "#e2f4b8"
GAP_FILL = "#ffffff"
GAP_STROKE = "#c9cdd4"
TEXT = "#1a1d23"
MUTED = "#5b6370"

WIDTH = 700
PAD = 14
TITLE_H = 24
DOMAIN_H = 30
ROW_H = 24
CELL = 14
FOOTER_H = 62

ROW_RE = re.compile(r"^- \[(x|~| )\] \*\*(.+?)\*\*(.*)$")


def parse_matrix() -> list[tuple[str, list[tuple[str, str, int, int]]]]:
    """Return [(domain, [(capability, state, n_primary, n_secondary), ...])]."""
    domains: list[tuple[str, list[tuple[str, str, int, int]]]] = []
    current: list[tuple[str, str, int, int]] | None = None
    for line in SRC_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = []
            domains.append((line[3:].strip(), current))
            continue
        m = ROW_RE.match(line)
        if not m or current is None:
            continue
        state, cap, rest = m.group(1), m.group(2), m.group(3)
        sec = re.search(r"_\(secondary: ([^)]+)\)_", rest)
        n_secondary = len(sec.group(1).split(";")) if sec else 0
        primary_part = re.sub(r"_\(secondary: [^)]+\)_", "", rest).strip(" -")
        n_primary = (
            len([p for p in primary_part.split(";") if p.strip()])
            if state == "x"
            else 0
        )
        current.append((cap, state, n_primary, n_secondary))
    if not domains:
        print(f"ERROR: no domains parsed from {SRC_FILE.name}", file=sys.stderr)
        raise SystemExit(1)

    n_domains = len(domains)
    n_caps = sum(len(rows) for _, rows in domains)
    if n_domains != CANONICAL_DOMAINS or n_caps != CANONICAL_CAPABILITIES:
        print(
            f"ERROR: parsed {n_domains} domains / {n_caps} capabilities from "
            f"{SRC_FILE.name}, expected {CANONICAL_DOMAINS} / "
            f"{CANONICAL_CAPABILITIES}.",
            file=sys.stderr,
        )
        print(
            "       Either fcp-coverage.md is truncated, or its row format "
            "changed and this script's ROW_RE no longer matches every "
            "capability line. Rows that do not match are skipped silently, so "
            "fix the parse - do not lower the constant to make this pass.",
            file=sys.stderr,
        )
        for domain, rows in domains:
            print(f"       {len(rows):>2} - {domain}", file=sys.stderr)
        raise SystemExit(1)
    return domains


def render(domains: list[tuple[str, list[tuple[str, str, int, int]]]]) -> str:
    caps = [row for _, rows in domains for row in rows]
    total = len(caps)
    covered = sum(1 for _, state, _, _ in caps if state in ("x", "~"))
    height = (
        PAD * 2 + TITLE_H
        + sum(DOMAIN_H + ROW_H * len(rows) for _, rows in domains)
        + FOOTER_H
    )
    font = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" '
        f'aria-label="FinOps Framework capability coverage: {covered} of {total} '
        f'capabilities covered by the reference library">',
        f'<rect width="{WIDTH}" height="{height}" rx="10" fill="#ffffff" stroke="{GAP_STROKE}"/>',
        f'<text x="{PAD + 2}" y="{PAD + 14}" {font} font-size="13" font-weight="600" '
        f'fill="{TEXT}">FinOps Framework capability coverage '
        f'({covered} of {total} capabilities)</text>',
    ]

    y = PAD + TITLE_H
    for domain, rows in domains:
        y += DOMAIN_H
        parts.append(
            f'<text x="{PAD + 2}" y="{y - 10}" {font} font-size="11" '
            f'font-weight="600" fill="{MUTED}">{escape(domain)}</text>'
        )
        for cap, state, n_primary, n_secondary in rows:
            cy = y + ROW_H / 2
            cx, sq_y = PAD + 10, y + (ROW_H - CELL) / 2
            if state == "x":
                parts.append(
                    f'<rect x="{cx}" y="{sq_y:.0f}" width="{CELL}" height="{CELL}" '
                    f'rx="3" fill="{PRIMARY_FILL}"/>'
                )
                note = (
                    f"{n_primary} primary"
                    + (f" + {n_secondary} secondary" if n_secondary else "")
                )
            elif state == "~":
                parts.append(
                    f'<rect x="{cx}" y="{sq_y:.0f}" width="{CELL}" height="{CELL}" '
                    f'rx="3" fill="{SECONDARY_FILL}" stroke="{GAP_STROKE}"/>'
                )
                note = f"secondary only ({n_secondary})"
            else:
                parts.append(
                    f'<rect x="{cx}" y="{sq_y:.0f}" width="{CELL}" height="{CELL}" '
                    f'rx="3" fill="{GAP_FILL}" stroke="{GAP_STROKE}" '
                    f'stroke-dasharray="3 2"/>'
                )
                note = "deferred (ROADMAP)"
            parts.append(
                f'<text x="{cx + CELL + 10}" y="{cy + 4:.0f}" {font} font-size="12" '
                f'fill="{TEXT}">{escape(cap)}</text>'
            )
            parts.append(
                f'<text x="{WIDTH - PAD - 4}" y="{cy + 4:.0f}" {font} font-size="10.5" '
                f'fill="{MUTED}" text-anchor="end">{escape(note)}</text>'
            )
            y += ROW_H

    fy = y + 22
    parts.append(
        f'<text x="{PAD + 2}" y="{fy}" {font} font-size="10.5" fill="{MUTED}">'
        f'Filled = owned by at least one reference; pale = touched as a secondary '
        f'capability only; dashed = deliberate gap,</text>'
    )
    parts.append(
        f'<text x="{PAD + 2}" y="{fy + 15}" {font} font-size="10.5" fill="{MUTED}">'
        f'deferred with its reasoning in docs/ROADMAP.md. Generated by '
        f'scripts/render-fcp-heatmap.py from fcp-coverage.md (CI-gated).</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    check = "--check" in sys.argv[1:]
    fresh = render(parse_matrix())
    if check:
        if not OUT_FILE.exists():
            print(f"fcp-heatmap: {OUT_FILE.name} missing - run the script and "
                  f"commit it.", file=sys.stderr)
            return 1
        if OUT_FILE.read_text(encoding="utf-8") != fresh:
            print(f"fcp-heatmap: committed {OUT_FILE.name} is stale - run "
                  f"scripts/render-fcp-heatmap.py and commit the result.",
                  file=sys.stderr)
            return 1
        print(f"OK: {OUT_FILE.name} matches fcp-coverage.md.")
        return 0
    # newline="\n" so the artefact is byte-identical wherever it is generated.
    # Without it Python's text mode translates every \n to \r\n on Windows, and
    # the committed SVG then differs from a CI (Linux) render by every line
    # ending. The --check above reads with universal newlines and so never
    # noticed.
    OUT_FILE.write_text(fresh, encoding="utf-8", newline="\n")
    print(f"Wrote {OUT_FILE.relative_to(REPO_ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
