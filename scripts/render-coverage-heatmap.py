#!/usr/bin/env python3
"""Render the waste-playbook coverage heat map as a committed SVG.

Companion to playbook-coverage.sh: same source of truth (the playbook
frontmatter), same CI discipline (--check fails when the committed SVG
drifts), different audience - the SVG is embedded in README.md so users see
the coverage shape, including the gaps, before installing. A zero cell is
shown as an explicit dashed gap, not hidden: the deliberate-scope decisions
live publicly in docs/ROADMAP.md.

Usage:
    python scripts/render-coverage-heatmap.py           Write assets/playbook-coverage.svg
    python scripts/render-coverage-heatmap.py --check   Fail if the committed SVG
                                                        differs from a fresh render
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PB_DIR = REPO_ROOT / "skills" / "cloud-finops" / "playbooks"
OUT_FILE = REPO_ROOT / "assets" / "playbook-coverage.svg"

# Canonical vocabularies - kept in step with find_playbooks and
# playbook-coverage.sh (tests/test_conformance.py pins the tool side).
SCOPES = ["aws", "azure", "gcp", "cross-cloud"]
CATEGORIES = [
    "orphaned", "idle", "overprovisioned", "commitment-mismatch",
    "schedule-blindness", "modernization", "ai-ml-inefficiency", "egress",
]

# OptimNow chartreuse ramp on a white card (readable on GitHub light and
# dark, which renders the SVG on its own background).
RAMP = ["#f5fbe6", "#e2f4b8", "#cdec8a", "#ace849", "#8bc32f"]
GAP_FILL = "#ffffff"
GAP_STROKE = "#c9cdd4"
TEXT = "#1a1d23"
MUTED = "#5b6370"

CELL_W, CELL_H = 96, 40
LABEL_W, HEADER_H = 170, 34
PAD = 14
FOOTER_H = 46


def frontmatter(path: Path) -> dict[str, str]:
    fm: dict[str, str] = {}
    fence = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "---":
            fence += 1
            if fence == 2:
                break
            continue
        if fence == 1 and ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def build_counts() -> tuple[dict[tuple[str, str], int], int]:
    counts: dict[tuple[str, str], int] = {}
    total = 0
    for f in sorted(PB_DIR.glob("*.md")):
        if f.name == "README.md":
            continue
        fm = frontmatter(f)
        scope, cat = fm.get("scope", ""), fm.get("waste_category", "")
        if scope not in SCOPES or cat not in CATEGORIES:
            print(f"ERROR: {f.name} has non-canonical scope/waste_category "
                  f"({scope!r}, {cat!r})", file=sys.stderr)
            raise SystemExit(1)
        counts[(cat, scope)] = counts.get((cat, scope), 0) + 1
        total += 1
    return counts, total


def render(counts: dict[tuple[str, str], int], total: int) -> str:
    max_count = max(counts.values(), default=1)
    width = PAD * 2 + LABEL_W + CELL_W * len(SCOPES)
    height = PAD * 2 + HEADER_H + CELL_H * len(CATEGORIES) + FOOTER_H

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Waste playbook coverage: {total} playbooks across '
        f'{len(CATEGORIES)} categories and {len(SCOPES)} providers">',
        f'<rect width="{width}" height="{height}" rx="10" fill="#ffffff" stroke="{GAP_STROKE}"/>',
        f'<text x="{PAD + 2}" y="{PAD + 14}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="13" font-weight="600" fill="{TEXT}">Waste-playbook coverage '
        f'({total} playbooks)</text>',
    ]

    font = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'
    grid_x, grid_y = PAD + LABEL_W, PAD + HEADER_H

    for j, scope in enumerate(SCOPES):
        cx = grid_x + j * CELL_W + CELL_W / 2
        parts.append(
            f'<text x="{cx:.0f}" y="{grid_y - 6}" {font} font-size="11" '
            f'font-weight="600" fill="{MUTED}" text-anchor="middle">{scope}</text>'
        )

    for i, cat in enumerate(CATEGORIES):
        cy = grid_y + i * CELL_H + CELL_H / 2
        parts.append(
            f'<text x="{grid_x - 8}" y="{cy + 4:.0f}" {font} font-size="11" '
            f'fill="{TEXT}" text-anchor="end">{cat}</text>'
        )
        for j, scope in enumerate(SCOPES):
            n = counts.get((cat, scope), 0)
            x, y = grid_x + j * CELL_W + 3, grid_y + i * CELL_H + 3
            w, h = CELL_W - 6, CELL_H - 6
            if n == 0:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
                    f'fill="{GAP_FILL}" stroke="{GAP_STROKE}" stroke-dasharray="4 3"/>'
                )
                parts.append(
                    f'<text x="{x + w / 2:.0f}" y="{y + h / 2 + 4:.0f}" {font} '
                    f'font-size="12" fill="{GAP_STROKE}" text-anchor="middle">-</text>'
                )
            else:
                shade = RAMP[min(len(RAMP) - 1, 1 + (len(RAMP) - 2) * (n - 1) // max(1, max_count - 1))]
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{shade}"/>'
                )
                parts.append(
                    f'<text x="{x + w / 2:.0f}" y="{y + h / 2 + 4:.0f}" {font} '
                    f'font-size="13" font-weight="600" fill="{TEXT}" '
                    f'text-anchor="middle">{n}</text>'
                )

    fy = grid_y + len(CATEGORIES) * CELL_H + 20
    parts.append(
        f'<text x="{PAD + 2}" y="{fy}" {font} font-size="10.5" fill="{MUTED}">'
        f'A dashed cell is a known coverage gap, not missing data - the prioritised '
        f'backlog is public in docs/ROADMAP.md.</text>'
    )
    parts.append(
        f'<text x="{PAD + 2}" y="{fy + 15}" {font} font-size="10.5" fill="{MUTED}">'
        f'Generated by scripts/render-coverage-heatmap.py from the playbook '
        f'frontmatter (CI-gated).</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    check = "--check" in sys.argv[1:]
    counts, total = build_counts()
    fresh = render(counts, total)
    if check:
        if not OUT_FILE.exists():
            print(f"heatmap: {OUT_FILE.name} missing - run the script and commit it.",
                  file=sys.stderr)
            return 1
        if OUT_FILE.read_text(encoding="utf-8") != fresh:
            print(f"heatmap: committed {OUT_FILE.name} is stale - run "
                  f"scripts/render-coverage-heatmap.py and commit the result.",
                  file=sys.stderr)
            return 1
        print(f"OK: {OUT_FILE.name} matches the playbook frontmatter ({total} playbooks).")
        return 0
    OUT_FILE.write_text(fresh, encoding="utf-8")
    print(f"Wrote {OUT_FILE.relative_to(REPO_ROOT)} ({total} playbooks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
