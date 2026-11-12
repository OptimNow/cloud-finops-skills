# Repository structure

Moved out of CLAUDE.md on 2026-11-10 (it had reached 355 lines). `scripts/check-docs-drift.sh`
gates the `references/` block: a reference missing from the tree, or a tree entry with no file
behind it, fails CI. Keep the tree glyphs and the indent under `└── references/` as they are.

```
cloud-finops-skills/
├── CLAUDE.md              <- Project context for agents (short map, defers to docs/)
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
│                             from this checkout; bundled data synced and package
│                             version pinned to plugin.json at build time)
├── fly.toml               <- Fly.io app config (app cloud-finops-mcp, region cdg,
│                             scale-to-zero); .dockerignore trims the build context.
│                             Deployed from each release tag by the release chain
├── .claude-plugin/        <- marketplace.json only (the plugin manifest lives in
│                             plugins/cloud-finops/; both versions bump together)
├── .github/workflows/     <- ci, marketplace-version-check, auto-tag-on-plugin-bump
│                             (the release chain: tag, GitHub Release, PyPI,
│                             hosted connector on Fly.io, MCP Registry),
│                             publish-mcp, publish-registry and deploy-hosted
│                             (manual paths for one surface), mcp-install-smoke,
│                             release, dependabot-automerge, price-drift and
│                             companion-tools (both weekly)
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
│                             green accent each, sized to read at phone width),
│                             and the 46-second demo video with its poster
│                             image (demo-nat-gateway-asked-twice.mp4 and .png,
│                             embedded in README.md, "Usage examples")
├── skills/cloud-finops/   <- One README stub pointing at the new location, so the
│                             old links do not 404. Outside the plugin folder
├── docs/
│   ├── DESIGN.md          <- Rules, lessons, checklist moved out of CLAUDE.md
│   ├── STRUCTURE.md       <- This tree (CI-gated by scripts/check-docs-drift.sh)
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
│   │                         rendering work, and why 1.51.0 removed the widgets
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
│       ├── finops-open-weight-vendors.md    <- Open-weight vendor APIs (DeepSeek, Qwen, Kimi, GLM)
│       ├── finops-ai-dev-tools.md          <- Cursor / Claude Code / Copilot / Windsurf / Codex
│       ├── finops-anthropic.md             <- Anthropic billing
│       ├── finops-aws.md                   <- AWS usage (rightsizing, SageMaker, databases, CloudFront, S3 Files)
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
│       ├── finops-cloud-contracts.md       <- Cloud contracts (EDP / PPA, MACC / ACD, Google commitment)
│       ├── finops-sam.md                   <- SaaS asset management
│       ├── greenops-cloud-carbon.md        <- GreenOps + cloud carbon
│       ├── finops-anomaly-management.md    <- Anomaly management (standalone Inform-phase)
│       ├── finops-kpis-benchmarking.md     <- KPIs, benchmarking, executive reporting
│       ├── finops-forecasting.md           <- Forecasting method, measures, cadence, scenarios
│       ├── finops-allocation-showback.md   <- Allocation methodology + showback
│       ├── finops-chargeback.md            <- Chargeback + Finance/accounting prerequisites
│       ├── finops-practice-operations.md   <- Practice operations: operating model, RACI, forums, ITFM
│       ├── finops-whats-new.md             <- Rolling 90-day digest of verified provider changes (generated block)
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
│                             figures.json once it passes a shape check:
│                             numbers and short labels (live_figures.py, offline fixtures
│                             in tests/fixtures/live_figures/);
│                             stdio + streamable-HTTP transports; no MCP Apps
│                             widget since 1.51.0: a tool that links one is
│                             put behind claude.ai's opt-in step, see
│                             docs/mcp-apps-lessons.md). Its scripts/ holds
│                             sync_references.py (copies the library into the
│                             package at build time) and pin_version.py (sets
│                             pyproject.toml to plugin.json's version when the
│                             hosted image is built)
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
│                             check-skill-description, check-skill-power-parity
│                             (the shared SKILL.md / POWER.md body cannot drift),
│                             check-detection-readonly.py (a playbook's Detection
│                             block only reads), check-style (prose only:
│                             no em dash, filler intensifier, corporate verb,
│                             "percent", dash residue or "the single most";
│                             allowlist in check-style-allow.txt),
│                             check-dated-prices (a price paragraph carries a
│                             year; allowlist in check-dated-prices-allow.txt),
│                             check-prices.py (price-manifest.yaml, every list
│                             price and where it is written, against the live
│                             price lists; --offline in CI, live weekly in
│                             price-drift.yml), check-companion-tools.py (the
│                             companion connectors' tools as INSTALLATION.md
│                             lists them, against each server's own tools/list;
│                             --offline in CI, live weekly in
│                             companion-tools.yml), render-whats-new.py
│                             (provider-changes.yaml into finops-whats-new.md;
│                             --check) and check-marketplace-version
│                             - all twenty-seven run by the `CI` workflow, and
│                             check-marketplace-version additionally has its
│                             own path-filtered `marketplace-version-check`
│                             workflow. One script is not a CI guard:
│                             check-hosted-connector.py calls the hosted
│                             connector and compares its version and its two
│                             catalogues with a checkout; the release chain and
│                             deploy-hosted run it after each deploy
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
    ├── run_scan.py        <- Laptop scan entry point; the live scan is a weekly cloud routine since 2026-10-17
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
    ├── probe-harness/     <- Headless smoke harness (claude -p against a branch server; maintainer-local)
    ├── provenance-check/  <- Reads a third-party connector, skill or text and reports whether it
    │                         reuses this library and whether the reuse is credited, as CC BY-SA
    │                         requires (compare.py + README.md; maintainer-local)
    ├── scanner/           <- Fetcher + Sonnet-based classifier
    ├── proposer/          <- CHANGES.md report generator
    ├── applier/           <- Opus-based diff generator and file editor
    ├── alerter/           <- Gmail draft builder
    ├── tests/             <- Unit tests over the guard rails
    └── state/             <- Runtime state (scan results, history, runs/)
```
