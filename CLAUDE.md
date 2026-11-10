# CLAUDE.md

Project context for AI assistants and human contributors working on this repository.

---

## Commits and pull requests

Do not add `Co-Authored-By`, `Claude-Session` or "Generated with Claude Code" lines to commit messages or pull request descriptions.

## What this repo is

A structured, model-agnostic FinOps knowledge skill for AI agents. The `plugins/cloud-finops/skills/cloud-finops/`
folder contains reference files that give any LLM accurate Cloud FinOps expertise -
Claude, GPT, Gemini, or any MCP-compatible agent.

- **SKILL.md** - entry point for Claude Code and generic agents
- **POWER.md** - entry point for Kiro IDE (same references, different format)
- **references/** - domain-specific content files (billing mechanics, pricing, optimisation patterns)
- **INSTALLATION.md** - one cross-tool installer covering 12 tool integrations, plus
  a model-agnostic response contract (system-prompt-injection section) for non-Claude
  models

Both entry points route to the same reference files. No content is duplicated.
The response contract in INSTALLATION.md (the "API integration" section) ensures
structured, billing-grounded answers across all models, even when model defaults
differ.

---

## Repository structure

Full annotated tree, every reference file, CI-gated: [`docs/STRUCTURE.md`](docs/STRUCTURE.md). Key places:

- `plugins/cloud-finops/skills/cloud-finops/` - the skill: `SKILL.md`, `POWER.md`, `references/`, `playbooks/`
- `plugins/cloud-finops/.claude-plugin/plugin.json` - the version holder (bumps with marketplace.json, pyproject, server.json x2)
- `mcp_server/` - the `cloud-finops-mcp` PyPI package (seven tools); `Dockerfile` + `fly.toml` for the hosted connector
- `scripts/` - CI guards and generators; `.github/workflows/` - CI, release and publish chains
- `docs/` - `DESIGN.md` (rules, checklist), `ROADMAP.md`, `CONCEPTS.md`, `OVERLAYS.md`, `STRUCTURE.md`
- Root: `INSTALLATION.md`, `README.md`, `llms.txt`, `DEPENDENCIES.md`, `CHANGELOG.md`; `pipeline/` is gitignored and private

---

## Testing changes

After editing reference files, verify them by asking questions in the domain you changed.
Good test patterns:

- Ask a question that requires specific billing mechanics (pricing, break-even, discount rules)
- Ask a maturity-sensitive question (the response should adapt to Crawl/Walk/Run context)
- Ask a cross-domain question that requires loading multiple references
- Test with a non-Claude model using the response contract to verify portability

---

## Cross-repo dependencies (check before every PR)

Nothing downstream depends on this repo; the dependencies run inward and are prose nobody verifies
(tool names, endpoint URLs, `provenance` fields) plus one code path, `get_live_figures` in
`mcp_server/src/cloud_finops_mcp/live_figures.py`. Before a PR that touches any of them, use the
"if I change X" table in [`DEPENDENCIES.md`](DEPENDENCIES.md). Two standing rules:

- **Never copy a formula or a rate into this repo.** Route to the tool that owns it.
- **Price figures are not maintained here at all.** See Content rules, "Write mechanics, not price figures".

## Where the rest lives

`docs/DESIGN.md` holds the other sections of this file, moved verbatim on 2026-11-08. It is not
loaded automatically: read the section your task touches. A reference to "CLAUDE.md, <section>"
means that section in `docs/DESIGN.md`. The "Repository structure" tree lives in `docs/STRUCTURE.md` (CI-gated by scripts/check-docs-drift.sh).

Sections in `docs/DESIGN.md`:

- Content update pipeline
- Lessons learned
- Roadmap
- Model compatibility
- How to add a new reference file
- Reference-file frontmatter
- Content rules
- Private overlays
- Claude directory listing
- Pull request checklist

## Maintaining this file

Keep this file under 200 lines. It holds what an agent needs in every session. A new decision, its reasoning or its history goes into the matching section of `docs/DESIGN.md`, or a new section listed above. Add a rule here only if an agent would break something without it.

