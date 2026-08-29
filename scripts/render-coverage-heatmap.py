#!/usr/bin/env python3
"""Render the waste-playbook coverage heat map as a committed SVG.

Downstream of playbook-coverage.sh: that script is the source of truth (it
parses the playbook frontmatter and emits playbook-coverage.md, CI-gated),
this one renders the committed matrix as assets/playbook-coverage.svg for the
README. The audience differs - the SVG is embedded in README.md so users see
the coverage shape, including the gaps, before installing. A zero cell is
shown as an explicit dashed gap, not hidden: the deliberate-scope decisions
live publicly in docs/ROADMAP.md.

Parsing playbook-coverage.md rather than the frontmatter is deliberate, and it
is the same chain render-fcp-heatmap.py already uses for the FCP pair:

    frontmatter -> playbook-coverage.md (--check) -> SVG (--check)

Until August 2026 this script re-derived the counts from the frontmatter and
carried its own copy of the SCOPES / CATEGORIES vocabularies, kept in step with
playbook-coverage.sh by a comment asking the next editor to remember. That is a
sync contract with no enforcement: adding a ninth waste category to one file and
not the other would have left the .md and the .svg describing different
taxonomies while both --check modes passed, because each compared its own
artefact against its own generator. Reading the .md removes the second
vocabulary entirely - there is nothing left to keep in step.

Usage:
    python scripts/render-coverage-heatmap.py           Write assets/playbook-coverage.svg
    python scripts/render-coverage-heatmap.py --check   Fail if the committed SVG
                                                        differs from a fresh render
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_FILE = REPO_ROOT / "playbook-coverage.md"
OUT_FILE = REPO_ROOT / "assets" / "playbook-coverage.svg"

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


def _cells(line: str) -> list[str]:
    """Split a markdown table row into its cells."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_matrix() -> tuple[list[str], list[str], dict[tuple[str, str], int], int]:
    """Return (scopes, categories, counts, total) from playbook-coverage.md.

    The scope columns and category rows come from the table itself, so this
    script has no vocabulary of its own to drift from playbook-coverage.sh's.
    """
    scopes: list[str] = []
    categories: list[str] = []
    counts: dict[tuple[str, str], int] = {}
    total: int | None = None

    lines = SRC_FILE.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("| waste_category |"):
            # Header row: strip the leading label and the trailing "total".
            scopes = _cells(line)[1:-1]
            body = lines[i + 2:]  # skip the |---|---| divider
            break
    else:
        print(f"ERROR: no '| waste_category |' header found in {SRC_FILE.name} - "
              f"the matrix format changed, update this script.", file=sys.stderr)
        raise SystemExit(1)

    for line in body:
        if not line.startswith("|"):
            break
        cells = _cells(line)
        label = cells[0]
        if label.startswith("**"):  # the totals row closes the table
            total = int(cells[-1])
            break
        if len(cells) != len(scopes) + 2:
            print(f"ERROR: row {label!r} in {SRC_FILE.name} has {len(cells)} cells, "
                  f"expected {len(scopes) + 2}", file=sys.stderr)
            raise SystemExit(1)
        categories.append(label)
        for scope, cell in zip(scopes, cells[1:-1]):
            counts[(label, scope)] = 0 if cell == "-" else int(cell)

    if not scopes or not categories or total is None:
        print(f"ERROR: could not parse the coverage matrix out of {SRC_FILE.name} "
              f"({len(scopes)} scopes, {len(categories)} categories, total={total})",
              file=sys.stderr)
        raise SystemExit(1)

    # The table states its own total; if the cells do not add up to it, the .md
    # is internally inconsistent and the SVG would quietly disagree with it.
    summed = sum(counts.values())
    if summed != total:
        print(f"ERROR: {SRC_FILE.name} cells sum to {summed} but the totals row "
              f"says {total}", file=sys.stderr)
        raise SystemExit(1)

    return scopes, categories, counts, total


def render(
    scopes: list[str],
    categories: list[str],
    counts: dict[tuple[str, str], int],
    total: int,
) -> str:
    max_count = max(counts.values(), default=1)
    width = PAD * 2 + LABEL_W + CELL_W * len(scopes)
    height = PAD * 2 + HEADER_H + CELL_H * len(categories) + FOOTER_H

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Waste playbook coverage: {total} playbooks across '
        f'{len(categories)} categories and {len(scopes)} providers">',
        f'<rect width="{width}" height="{height}" rx="10" fill="#ffffff" stroke="{GAP_STROKE}"/>',
        f'<text x="{PAD + 2}" y="{PAD + 14}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="13" font-weight="600" fill="{TEXT}">Named waste-pattern '
        f'runbook coverage ({total} playbooks)</text>',
    ]

    font = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'
    grid_x, grid_y = PAD + LABEL_W, PAD + HEADER_H

    for j, scope in enumerate(scopes):
        cx = grid_x + j * CELL_W + CELL_W / 2
        parts.append(
            f'<text x="{cx:.0f}" y="{grid_y - 6}" {font} font-size="11" '
            f'font-weight="600" fill="{MUTED}" text-anchor="middle">{scope}</text>'
        )

    for i, cat in enumerate(categories):
        cy = grid_y + i * CELL_H + CELL_H / 2
        parts.append(
            f'<text x="{grid_x - 8}" y="{cy + 4:.0f}" {font} font-size="11" '
            f'fill="{TEXT}" text-anchor="end">{cat}</text>'
        )
        for j, scope in enumerate(scopes):
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

    fy = grid_y + len(categories) * CELL_H + 20
    parts.append(
        f'<text x="{PAD + 2}" y="{fy}" {font} font-size="10.5" fill="{MUTED}">'
        f'Runbook coverage only - the reference library covers these themes even '
        f'where no runbook exists. A dashed cell is a known gap</text>'
    )
    parts.append(
        f'<text x="{PAD + 2}" y="{fy + 15}" {font} font-size="10.5" fill="{MUTED}">'
        f'with its backlog public in docs/ROADMAP.md. Generated by '
        f'scripts/render-coverage-heatmap.py from the playbook frontmatter (CI-gated).</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    check = "--check" in sys.argv[1:]
    scopes, categories, counts, total = parse_matrix()
    fresh = render(scopes, categories, counts, total)
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
        print(f"OK: {OUT_FILE.name} matches {SRC_FILE.name} ({total} playbooks).")
        return 0
    # newline="\n" so the artefact is byte-identical wherever it is generated.
    # Without it Python's text mode translates every \n to \r\n on Windows, and
    # the committed SVG then differs from a CI (Linux) render by every line
    # ending - invisible in review, and a diff that .gitattributes has to clean
    # up after. The --check above reads with universal newlines and so never
    # noticed.
    OUT_FILE.write_text(fresh, encoding="utf-8", newline="\n")
    print(f"Wrote {OUT_FILE.relative_to(REPO_ROOT)} ({total} playbooks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
