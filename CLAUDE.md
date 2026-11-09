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

```
cloud-finops-skills/
├── CLAUDE.md              <- You are here
├── README.md              <- Public-facing documentation
├── AGENTS.md              <- Agent-facing repo brief (truncated tree, defers to CLAUDE.md)
├── INSTALLATION.md        <- Setup instructions (12 tool integrations) + response contract
├── LICENSE.md             <- CC BY-SA 4.0, full legal text (GitHub only detects
│                             the licence from the canonical text; a summary
│                             reads as "Other" and Glama grades it F)
├── glama.json             <- Glama listing manifest (maintainers), read by the
│                             Glama crawler at the repository root
├── PRIVACY.md             <- Privacy policy for the skill, the hosted connector and
│                             the PyPI package (the directory listing asks for its URL)
├── CONTRIBUTING.md        <- Contribution guide (types, process, push-backs)
├── CHANGELOG.md           <- What each version changes for users, newest first
│                             (since 1.50.0; the release body links it)
├── llms.txt               <- llmstxt.org-format index (linked sections; CI-gated)
├── DEPENDENCIES.md        <- Cross-repo dependency map for the five OptimNow repos,
│                             plus the "if I change X, what else needs review" table
├── install.sh             <- One-liner installer script
├── server.json            <- MCP Registry manifest (carries the version TWICE)
├── Dockerfile             <- Image for the hosted MCP connector on Fly.io (builds
│                             from this checkout; bundled data synced at build time)
├── fly.toml               <- Fly.io app config (app cloud-finops-mcp, region cdg,
│                             scale-to-zero); .dockerignore trims the build context
├── .claude-plugin/        <- marketplace.json only (the plugin manifest lives in
│                             plugins/cloud-finops/; both versions bump together)
├── .github/workflows/     <- ci, marketplace-version-check, auto-tag-on-plugin-bump,
│                             publish-mcp, publish-registry, mcp-install-smoke,
│                             release, dependabot-automerge, price-drift (weekly)
├── .github/ISSUE_TEMPLATE/ <- Two issue forms (wrong or incomplete answer,
│                             question not covered) plus the chooser config; each
│                             confirmed report becomes a coverage probe
├── assets/                <- Installation-guide screenshots (embedded in
│                             INSTALLATION.md), the GitHub social preview, the
│                             directory listing icon (icon.png), the OptimNow
│                             logo pair for the README header (optimnow-logo.png
│                             on light, optimnow-logo-dark.png on dark), and
│                             the generated playbook-coverage.svg and
│                             fcp-coverage.svg heat maps (embedded in
│                             README.md; both CI-gated; brand palette, one
│                             green accent each, sized to read at phone width)
├── skills/cloud-finops/   <- One README stub pointing at the new location, so the
│                             old links do not 404. Outside the plugin folder
├── docs/
│   ├── CONCEPTS.md        <- What a skill and an MCP server are, skill vs
│   │                         connector behaviour, plugin and connector kept
│   │                         apart, the seven MCP tools, live prices (moved out
│   │                         of README.md in Oct 2026 so the README leads with
│   │                         coverage)
│   ├── ROADMAP.md         <- Deliberately-deferred work + trigger to revisit
│   │                         (split out of CLAUDE.md, Aug 2026)
│   ├── OVERLAYS.md        <- The private-overlay convention: a second skill
│   │                         folder that cites public sections by heading and
│   │                         never restates a mechanic (published 2026-11-09)
│   ├── overlay-template/  <- Minimal overlay that passes check-overlay.py
│   │                         (SKILL.md, calibration.md, decisions.md); CI-gated
│   ├── mcp-apps-lessons.md <- Chronological forensic of the MCP Apps widget
│   │                         rendering work (split out of CLAUDE.md, Aug 2026)
│   ├── directory-submission.md <- Step-by-step for the two Claude directory
│   │                         listings (plugin bundle + MCP connector), with the
│   │                         prefilled portal answers and the holds to expect
│   └── list-submissions.md <- Submission kit for the curated GitHub lists
│                             (awesome-mcp-servers, awesome-agent-skills, ...):
│                             verified facts, exact entry lines, PR bodies,
│                             hand-fill form drafts and the spacing schedule
├── plugins/cloud-finops/  <- The Claude plugin folder: what the directory scans and
│                             what `cloud-finops@optimnow` installs, and nothing else.
│                             Holds .claude-plugin/plugin.json (the version holder),
│                             README.md (the listing's description), LICENSE, the
│                             listing icon (.claude-plugin/icon.svg, a text file)
│                             and the skill below. Text files only: no raster
│                             image, no script, no `${VAR}` next to a URL, no
│                             download-and-execute
├── plugins/cloud-finops/skills/cloud-finops/   <- The skill (this is what gets installed)
│   ├── SKILL.md           <- Entry point + domain router
│   ├── POWER.md           <- Kiro IDE entry point
│   └── references/        <- reference files, all with YAML FCP frontmatter
│       ├── optimnow-methodology.md         <- OptimNow reasoning lens, 4 pillars
│       ├── finops-framework.md             <- FinOps Foundation framework reference
│       ├── finops-for-ai.md                <- AI cost management discipline
│       ├── finops-agentic.md                 <- Agentic FinOps (agent cost anatomy, x402/MPP)
│       ├── finops-ai-value-management.md   <- AI Investment Council, stage gates
│       ├── finops-genai-capacity.md        <- Provisioned vs shared capacity
│       ├── finops-ai-self-hosted-vs-managed.md  <- Self-host vs managed inference
│       ├── finops-open-weight-vendors.md    <- Open-weight vendor hosted APIs
│       │                                     (DeepSeek, Qwen, Kimi, GLM)
│       ├── finops-ai-dev-tools.md          <- Cursor / Claude Code / Copilot / Windsurf / Codex
│       ├── finops-anthropic.md             <- Anthropic billing
│       ├── finops-aws.md                   <- AWS usage optimisation (rightsizing, SageMaker,
│       │                                     databases, CloudFront, S3 Files)
│       ├── finops-aws-billing.md           <- AWS billing data, allocation, SCPs, Budgets,
│       │                                     billing hierarchy, multi-org (split 2026-10-22)
│       ├── finops-aws-commitments.md       <- AWS SPs / RIs / Spot, portfolio liquidity, EDP
│       ├── finops-aws-patterns.md          <- Index to the AWS pattern catalogue (split by
│       │                                     service family on 2026-10-22)
│       ├── finops-aws-patterns-compute.md  <- AWS compute patterns (EC2, Lambda, EKS, EMR)
│       ├── finops-aws-patterns-storage.md  <- AWS storage patterns (S3, EBS, EFS, snapshots)
│       ├── finops-aws-patterns-databases.md <- AWS database patterns, RDS strategy,
│       │                                     database commitment decision tree
│       ├── finops-aws-patterns-networking.md <- AWS networking patterns (NAT, ELB, cross-AZ)
│       ├── finops-aws-patterns-other.md    <- AWS logging, Config, CloudTrail, EDP, Marketplace
│       ├── finops-bedrock.md               <- AWS Bedrock
│       ├── finops-azure.md                 <- Azure usage optimisation (rightsizing, AKS,
│       │                                     Log Analytics, storage, networking)
│       ├── finops-azure-billing.md         <- Azure billing data, allocation, tagging and
│       │                                     Policy, budgets, EA-to-MCA (split 2026-10-22)
│       ├── finops-azure-commitments.md     <- Azure RIs / SPs / AHB, liquidity, MACC
│       ├── finops-azure-patterns.md        <- Azure enumerated pattern catalogue
│       ├── finops-azure-openai.md          <- Azure OpenAI / PTUs
│       ├── finops-gcp.md                   <- GCP FinOps
│       ├── finops-vertexai.md              <- GCP Vertex AI
│       ├── finops-oci.md                   <- OCI
│       ├── finops-databricks.md            <- Databricks (DBCU, allocation)
│       ├── finops-fabric.md                <- Microsoft Fabric (F-SKU, CU)
│       ├── finops-snowflake.md             <- Snowflake
│       ├── finops-tagging.md               <- Tagging governance + MCP automation
│       ├── finops-itam.md                  <- ITAM / BYOL / marketplace
│       ├── finops-cloud-contracts.md       <- Cloud contract negotiation (EDP / PPA,
│       │                                     MACC / ACD, Google Minimum Commitment)
│       ├── finops-sam.md                   <- SaaS asset management
│       ├── greenops-cloud-carbon.md        <- GreenOps + cloud carbon
│       ├── finops-anomaly-management.md    <- Anomaly management (standalone Inform-phase)
│       ├── finops-kpis-benchmarking.md     <- KPIs, benchmarking, executive reporting
│       ├── finops-forecasting.md           <- Forecasting method, measures, cadence, scenarios
│       ├── finops-allocation-showback.md   <- Allocation methodology + showback
│       ├── finops-chargeback.md            <- Chargeback + Finance/accounting prerequisites
│       ├── finops-practice-operations.md   <- Practice operations: operating model, RACI, forums, ITFM
│       ├── finops-onboarding-workloads.md  <- Migration-time cost hygiene, M&A, divestiture
│       ├── finops-kubernetes.md            <- K8s cross-cluster discipline (EKS/GKE/AKS)
│       ├── finops-on-prem-hybrid.md        <- On-prem and hybrid: internal bill, hybrid platforms, exit fees
│       ├── finops-focus.md                 <- FOCUS multi-cloud normalisation + ingestion
│       └── finops-waste-detection-playbooks.md  <- Eight-category waste taxonomy + WasteLine
├── plugins/cloud-finops/skills/cloud-finops/playbooks/  <- named-pattern runbooks (`<scope>-<pattern>.md`,
│                                ~3-8 KB each, average ~5 KB;
│                                Problem/Symptoms/Detection/Fix/
│                                Anti-pattern/See also format) +
│                                README.md index. RAG-friendly chunks routed from
│                                SKILL.md / POWER.md "named waste pattern" rows
├── mcp_server/            <- `cloud-finops-mcp` PyPI package (seven MCP tools:
│                             faceted retrieval over references + playbooks,
│                             and get_live_figures, the one open-world tool,
│                             which passes through an OptimToken guide's
│                             figures.json (live_figures.py, offline fixtures
│                             in tests/fixtures/live_figures/);
│                             stdio + streamable-HTTP transports; MCP Apps
│                             resources: playbook-viewer, playbook-explorer,
│                             reference-browser - shared JS/CSS in ui/_* is
│                             inlined at import by server._load_ui)
├── scripts/               <- `fcp-coverage.sh` and `playbook-coverage.sh`
│                             (parse frontmatter, emit the two coverage
│                             matrices; their --check modes diff the
│                             committed files in CI), `business-coverage.sh`
│                             (reads the `business_coverage` frontmatter
│                             field and rewrites the "Providers and business
│                             needs" tables between the HTML markers in
│                             README.md; --check gated in CI since Oct
│                             2026), the heat-map renderers
│                             `render-coverage-heatmap.py` and
│                             `render-fcp-heatmap.py` (emit the README SVGs,
│                             --check gated in CI), `render-questions-readme.py`
│                             (rewrites the README "What you can ask, by role"
│                             block from the persona-tagged `questions:`;
│                             --check gated in CI), `build-llms-full.sh`
│                             (inlines the whole library into llms-full.txt
│                             at release time; --smoke gated in CI, the file
│                             itself is not committed) plus the guards:
│                             check-artefact-size, check-chatgpt-instructions
│                             (both ChatGPT builds under the ~8000-char
│                             Instructions limit), check-docs-drift,
│                             check-footers (every reference and playbook
│                             ends with the OptimNow / CC BY-SA footer),
│                             check-llms-txt, check-overlay.py (a private
│                             overlay cites public headings that exist, its
│                             questions follow the public rules and it copies
│                             no public sentence; CI runs it on the template),
│                             check-questions.py (every reference and playbook
│                             carries 4 to 8 `questions:` in the user's words,
│                             no duplicate across files, every `section`
│                             resolves; PyYAML, so after the install),
│                             check-plugin-file-limits (no tracked non-image
│                             file over 256 KiB, at most 480 files),
│                             check-plugin-skill-only (no .mcp.json, no mcpServers),
│                             check-plugin-content (the plugin folder holds
│                             markdown and the licence only: no image, no
│                             `$VAR` beside a URL, no curl-pipe-to-shell, no
│                             package launcher),
│                             check-reference-size (token budget per file:
│                             warns at 15,000, or 6,000 for SKILL.md, fails
│                             at 30,000 and 8,000),
│                             check-skill-description,
│                             check-skill-power-parity (diffs the shared
│                             SKILL.md / POWER.md body so the routing tables
│                             cannot drift apart), check-style (prose only:
│                             no em dash, filler intensifier, corporate verb,
│                             "percent", dash residue or "the single most";
│                             allowlist in check-style-allow.txt),
│                             check-dated-prices (a playbook paragraph that
│                             carries a currency figure also carries a year),
│                             check-prices.py (price-manifest.yaml, every list
│                             price and where it is written, against the live
│                             price lists; --offline in CI, live weekly in
│                             price-drift.yml) and check-marketplace-version
│                             - all twenty-four run by the `CI` workflow, and
│                             check-marketplace-version additionally has its
│                             own path-filtered `marketplace-version-check`
│                             workflow
├── fcp-coverage.md        <- Generated FCP coverage matrix (22 caps; CI-gated)
├── playbook-coverage.md   <- Generated waste-playbook matrix (category x
│                             scope, gaps listed; CI-gated)
├── (llms-full.txt)        <- NOT committed: the whole library (entry point +
│                             all references + all playbooks) inlined for
│                             one-fetch ingestion, ~1.2MB, so over the Claude
│                             directory's 256 KiB per-file limit. The release
│                             workflows build it and attach it to each GitHub
│                             Release (releases/latest/download/llms-full.txt);
│                             a local build lands here and is gitignored
├── .gitattributes         <- Force LF on *.sh and on every generated artefact
│                             (fcp-coverage.md, playbook-coverage.md, the
│                             SVGs) for Windows checkouts with
│                             core.autocrlf=true
└── pipeline/              <- Content update pipeline (gitignored, private)
    ├── run_scan.py        <- Fortnightly scan entry point
    ├── run_monthly.bat    <- Task Scheduler wrapper (both scheduled tasks call it)
    ├── run_apply.py.FROZEN <- Review and apply entry point, frozen since the
    │                          May 2026 truncation incident (see docs/ROADMAP.md P1)
    ├── run_report.py      <- Per-run report rendering
    ├── smoke_test.py      <- Real-API smoke test, run before any batch
    ├── config.yaml        <- Pipeline configuration
    ├── sources.yaml       <- ~30 content sources (RSS, pricing pages, blogs)
    ├── MONTHLY_WORKFLOW.md <- Operating doctrine for a batch (maintainer-local)
    ├── coverage-probes.md <- Behavioural coverage probe battery + run log
    │                         (maintainer-local; see docs/ROADMAP.md backlog)
    ├── drafts/            <- Probe-seeded content drafts awaiting adaptation
    ├── pipeline-audit-2026-05.md / pipeline-harden-plan.md  <- Phase-1 forensics
    ├── scanner/           <- Fetcher + Sonnet-based classifier
    ├── proposer/          <- CHANGES.md report generator
    ├── applier/           <- Opus-based diff generator and file editor
    ├── alerter/           <- Gmail draft builder
    ├── tests/             <- Unit tests over the guard rails
    └── state/             <- Runtime state (scan results, history, runs/)
```

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

Full map, including the other four repos and their own blast radius:
[`DEPENDENCIES.md`](DEPENDENCIES.md). The short version for working *in this repo*:

**Nothing downstream depends on this repo.** No other repository imports it, builds
against it, or calls it. That makes it the safest of the five to change, and it means a
content PR here needs no cross-repo coordination at all.

**The dependencies run inward, and they are documentation.** This repo quotes other
repos' facts in prose: MCP tool names and signatures, endpoint URLs, and the
`provenance` field names the dated-price rule tells the model to read. Nothing verifies
any of them. When an upstream repo changes its surface, this repo does not find out -
the text simply becomes wrong, and the first symptom is an agent following an
instruction that no longer matches reality.

One inward dependency is code since 2026-10-25: `get_live_figures`
(`mcp_server/src/cloud_finops_mcp/live_figures.py`) fetches an OptimToken guide's
`figures.json` at request time and reads the "Figures as JSON" lines of OptimToken's
`llms.txt`. It checks only that the envelope carries `guide` and `figures`, so a
reshaped file degrades to an error and the dated figure in the reference, not to a
crash; the tests run against saved copies and do not notice a change upstream.

So the check is one-directional. Before merging, if the PR touches any of these:

| If the PR touches | Verify against | Where it lives here |
|---|---|---|
| An MCP tool name, parameter, or output field of the pricing hub | `ai-pricing-hub-mcp` | INSTALLATION.md companion section; SKILL.md / POWER.md "Price figures" |
| The `provenance` contract (tier semantics, `upstreamTimestamp` / `eloAsOf`, the stale notice) | `ai-pricing-hub-mcp` | "Price figures" rule 5, in SKILL.md, POWER.md and the INSTALLATION.md response contract |
| An MCP tool name or parameter of the ROI calculator | `ai-roi-calculator-mcp` | INSTALLATION.md companion section |
| A value method, an input's meaning, or a documented trap | `ai-roi-calculator` METHODOLOGY.md | `references/finops-ai-value-management.md` |
| The OptimToken guide `figures.json` envelope (`guide`, `url`, `snapshotDate`, `figures`), a guide slug, or the llms.txt "Figures as JSON" line format | OptimToken (`cloud-sparkle-compare`, see DEPENDENCIES.md) | `mcp_server/src/cloud_finops_mcp/live_figures.py`, `mcp_server/tests/fixtures/live_figures/`, the guide figures quoted in `finops-aws-commitments.md`, `finops-azure-commitments.md`, `finops-gcp.md`, SKILL.md / POWER.md "Price figures" rule 6 |
| Any `mcp.optimnow.io`, `*.fly.dev`, `*.alpic.live` or `optimtoken.optimnow.io` URL | the owning repo | README.md, INSTALLATION.md, mcp_server/README.md, server.json, llms.txt, PRIVACY.md, fly.toml, docs/ |

Two standing rules that follow from the map:

- **Never copy a formula or a rate into this repo.** Route to the tool that owns it.
  Duplicated computation is the recurring failure mode across this family: OptimToken
  drifted between its site and its MCP, and the ROI calculator drifted between its web
  app and its MCP far enough to return a 7-point different ROI for the same preset.
- **Price figures are not maintained here at all.** See the Content rules "Write
  mechanics, not price figures" entry.

## Where the rest lives

`docs/DESIGN.md` holds the other sections of this file, moved verbatim on 2026-11-08. It is not
loaded automatically: read the section your task touches. A reference to "CLAUDE.md, <section>"
means that section in `docs/DESIGN.md`. The "Repository structure" tree stays in this file because CI checks it (scripts/check-docs-drift.sh).

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

