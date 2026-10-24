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

# OptimNow palette (brand guide, closed palette): charcoal text, light-grey
# card, #C1C1C1 borders, and exactly one chartreuse accent per visual, which
# here is the pill behind the headline count. Coverage levels are greys, not
# greens, so the green carries one meaning only. Same constants as
# render-coverage-heatmap.py so the two README cards read as one family.
CARD_FILL = "#F4F4F4"
PRIMARY_FILL = "#2C2C2C"      # owned by at least one reference
SECONDARY_FILL = "#C1C1C1"    # covered as a secondary capability only
GAP_FILL = "#FFFFFF"
GAP_STROKE = "#C1C1C1"
TEXT = "#2C2C2C"
MUTED = "#2C2C2C"
ACCENT = "#ACE849"

# 440 px wide so that the card still reads on a phone: GitHub scales the image
# to the column width (about 343 px at 375 px viewport), which keeps the 13 px
# labels above 10 px. The previous 700 px card dropped them under 7 px.
WIDTH = 440
PAD = 14
TITLE_H = 30
DOMAIN_H = 30
ROW_H = 24
CELL = 14
FOOTER_H = 70

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

    title = "FinOps Framework capability coverage"
    pill_label = f"{covered} of {total}"
    # Approximate text widths (0.56 em per character for this font stack) to
    # place the accent pill right after the title.
    pill_x = PAD + 2 + int(len(title) * 13 * 0.56) + 10
    pill_w = int(len(pill_label) * 12 * 0.6) + 18
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" '
        f'aria-label="FinOps Framework capability coverage: {covered} of {total} '
        f'capabilities covered by the reference library">',
        f'<rect width="{WIDTH}" height="{height}" rx="10" fill="{CARD_FILL}" stroke="{GAP_STROKE}"/>',
        f'<text x="{PAD + 2}" y="{PAD + 16}" {font} font-size="13" font-weight="700" '
        f'fill="{TEXT}">{title}</text>',
        f'<rect x="{pill_x}" y="{PAD + 3}" width="{pill_w}" height="20" rx="10" '
        f'fill="{ACCENT}"/>',
        f'<text x="{pill_x + pill_w / 2:.0f}" y="{PAD + 17}" {font} font-size="12" '
        f'font-weight="700" fill="{TEXT}" text-anchor="middle">{pill_label}</text>',
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
                f'<text x="{cx + CELL + 10}" y="{cy + 4:.0f}" {font} font-size="13" '
                f'fill="{TEXT}">{escape(cap)}</text>'
            )
            parts.append(
                f'<text x="{WIDTH - PAD - 4}" y="{cy + 4:.0f}" {font} font-size="10.5" '
                f'fill="{MUTED}" text-anchor="end">{escape(note)}</text>'
            )
            y += ROW_H

    # Footer lines stay under about 70 characters so they fit the 440 px card.
    fy = y + 22
    footer = (
        "Dark = owned by a reference; grey = covered as a secondary capability;",
        "dashed = deferred gap, with its reasoning in docs/ROADMAP.md.",
        "Generated from fcp-coverage.md by scripts/render-fcp-heatmap.py (CI-gated).",
    )
    for i, line in enumerate(footer):
        parts.append(
            f'<text x="{PAD + 2}" y="{fy + 15 * i}" {font} font-size="10" '
            f'fill="{MUTED}">{escape(line)}</text>'
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
