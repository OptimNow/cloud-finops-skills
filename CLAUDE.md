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
- `mcp_server/` - the `cloud-finops-mcp` PyPI package (seven tools); `Dockerfile` + `fly.toml`, at the repository root, for the hosted connector
- `scripts/` - CI guards and generators; `.github/workflows/` - CI, the release chain (see "Releases and the hosted connector") and its manual paths
- `docs/` - `DESIGN.md` (rules, checklist), `ROADMAP.md`, `CONCEPTS.md`, `OVERLAYS.md`, `STRUCTURE.md`
- Root: `INSTALLATION.md`, `README.md`, `llms.txt`, `DEPENDENCIES.md`, `CHANGELOG.md`
- `pipeline/` - gitignored and private: the content pipeline, the probe battery and its harnesses, and
  `provenance-check/`, which tells whether a third-party connector or skill reuses this library with credit

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

Nothing downstream depends on this repo; the dependencies run inward and are prose no PR check verifies
(tool names, read weekly by `scripts/check-companion-tools.py`; endpoint URLs; `provenance` fields) plus one code path, `get_live_figures` in
`mcp_server/src/cloud_finops_mcp/live_figures.py`, which relays a fetched file to the model only
when it is numbers and short labels (`_validate`). Before a PR that touches any of them, use the
"if I change X" table in [`DEPENDENCIES.md`](DEPENDENCIES.md). Two standing rules:

- **Never copy a formula or a rate into this repo.** Route to the tool that owns it.
- **Price figures are not maintained here at all.** See Content rules, "Write mechanics, not price figures".

## Releases and the hosted connector

A release is a change of `version` in `plugins/cloud-finops/.claude-plugin/plugin.json` reaching
`main`, and nothing else. A content PR never touches it, and the maintainer decides when a release
PR exists. That merge starts `.github/workflows/auto-tag-on-plugin-bump.yml`, one line of jobs:

1. Tag and GitHub Release.
2. PyPI publish, which waits for the maintainer's approval of the `pypi` environment.
3. Deploy of the hosted connector to Fly.io from the tag, then a check of what
   `https://mcp.optimnow.io/mcp` serves (`scripts/check-hosted-connector.py`: the version, and the
   names and totals of the two catalogues against the files of the tag).
4. MCP Registry entry, only if step 3 passed.

Rules that follow:

- **Never bump a version, push a tag, run `fly deploy` or start a release or deploy workflow as part
  of other work.** Each one publishes. Prepare a release PR only when the maintainer asks for one.
- **No `fly deploy` by hand after a release.** Read the `deploy-hosted` job. To repair a failed
  deploy or go back a release: `gh workflow run deploy-hosted.yml -f tag=vX.Y.Z`
  (`-f verify_only=true` deploys nothing and only runs the check).
- **The `FLY_API_TOKEN` secret is the maintainer's to create and rotate.** Never ask for its value.
- The hosted image takes its version from `plugin.json` when it is built
  (`mcp_server/scripts/pin_version.py`), so `pyproject.toml` does not decide what the server announces.
- A release that changes a tool's name, description, parameters or what it sends is reported in the
  Claude directory portal before the release PR merges (`docs/directory-submission.md`, section 4).

The checklist and the recovery steps are in "Pull request checklist" in `docs/DESIGN.md`; why the
chain has this shape is in "Lessons learned", entry of 2026-11-12.

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

