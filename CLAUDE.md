# CLAUDE.md

Project context for AI assistants and human contributors working on this repository.

---

## What this repo is

A structured, model-agnostic FinOps knowledge skill for AI agents. The `skills/cloud-finops/`
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
├── LICENSE.md             <- CC BY-SA 4.0
├── llms.txt               <- Machine-readable "Key files" list (CI-gated)
├── install.sh             <- One-liner installer script
├── server.json            <- MCP Registry manifest
├── .claude-plugin/        <- plugin.json + marketplace.json (versions bump together)
├── .github/workflows/     <- ci, marketplace-version-check, auto-tag-on-plugin-bump,
│                             publish-mcp, mcp-install-smoke, release
├── assets/                <- Screenshots for installation guide
├── skills/cloud-finops/          <- The skill (this is what gets installed)
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
│       ├── finops-ai-dev-tools.md          <- Cursor / Claude Code / Copilot / Windsurf / Codex
│       ├── finops-anthropic.md             <- Anthropic billing
│       ├── finops-aws.md                   <- AWS FinOps core (billing data, rightsizing,
│       │                                     SageMaker, allocation, CloudFront, S3 Files)
│       ├── finops-aws-commitments.md       <- AWS SPs / RIs / Spot, portfolio liquidity, EDP
│       ├── finops-aws-patterns.md          <- AWS enumerated pattern catalogue
│       ├── finops-bedrock.md               <- AWS Bedrock
│       ├── finops-azure.md                 <- Azure FinOps core (cost data, rightsizing, AKS,
│       │                                     Log Analytics, storage, networking, governance)
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
│       ├── finops-sam.md                   <- SaaS asset management
│       ├── greenops-cloud-carbon.md        <- GreenOps + cloud carbon
│       ├── finops-anomaly-management.md    <- Anomaly management (standalone Inform-phase)
│       ├── finops-allocation-showback.md   <- Allocation methodology + showback
│       ├── finops-chargeback.md            <- Chargeback + Finance/accounting prerequisites
│       ├── finops-onboarding-workloads.md  <- Migration-time cost hygiene + M&A
│       ├── finops-kubernetes.md            <- K8s cross-cluster discipline (EKS/GKE/AKS)
│       └── finops-waste-detection-playbooks.md  <- Eight-category waste taxonomy + WasteLine
├── skills/cloud-finops/playbooks/   <- named-pattern runbooks (`<scope>-<pattern>.md`,
│                                ~2-3KB each, Problem/Symptoms/Detection/Fix/
│                                Anti-pattern/See also format) +
│                                README.md index. RAG-friendly chunks routed from
│                                SKILL.md / POWER.md "named waste pattern" rows
├── mcp_server/            <- `cloud-finops-mcp` PyPI package (six MCP tools,
│                             faceted retrieval over references + playbooks;
│                             stdio + streamable-HTTP transports; MCP Apps
│                             `ui://cloud-finops/playbook-viewer` resource)
├── scripts/               <- `fcp-coverage.sh` (parses FCP frontmatter, emits
│                             `fcp-coverage.md` matrix) plus five CI guards run by
│                             the `CI` workflow: check-artefact-size,
│                             check-docs-drift, check-llms-txt,
│                             check-marketplace-version, check-skill-description
├── fcp-coverage.md        <- Generated FCP capability coverage matrix (22 caps)
├── .gitattributes         <- Force LF on *.sh for Windows checkouts
└── pipeline/              <- Content update pipeline (gitignored, private)
    ├── run_scan.py        <- Fortnightly scan entry point
    ├── run_apply.py.FROZEN <- Review and apply entry point, frozen since the
    │                          May 2026 truncation incident (see Roadmap P1)
    ├── run_report.py      <- Per-run report rendering
    ├── smoke_test.py      <- Real-API smoke test, run before any batch
    ├── config.yaml        <- Pipeline configuration
    ├── sources.yaml       <- ~30 content sources (RSS, pricing pages, blogs)
    ├── MONTHLY_WORKFLOW.md <- Operating doctrine for a batch (maintainer-local)
    ├── pipeline-audit-2026-05.md / pipeline-harden-plan.md  <- Phase-1 forensics
    ├── scanner/           <- Fetcher + Sonnet-based classifier
    ├── proposer/          <- CHANGES.md report generator
    ├── applier/           <- Opus-based diff generator and file editor
    ├── alerter/           <- Gmail draft builder
    ├── tests/             <- Unit tests over the guard rails
    └── state/             <- Runtime state (scan results, history, runs/)
```

---

## Content update pipeline

The `pipeline/` folder contains a **fortnightly** content scanner (1st and 15th
of each month at 9:00 AM CET via Windows Task Scheduler) that detects
FinOps-relevant changes across ~30 sources and proposes updates to the reference
files. It is gitignored and not part of the public distribution.

**Cadence note (2026-05-15).** The pipeline was originally twice-monthly (1st
and 15th). After the 2026-05-15 incident-and-recovery session (see Lessons
learned below) it became clear each run requires 2-4 hours of focused human
review for a typical 12-item batch. The 15th-of-month task was disabled
in Task Scheduler and the cadence dropped to monthly, trading some freshness
for sustainable operating effort.

**Cadence update (2026-08-10).** Restored to twice-monthly: the fortnightly
rhythm matches the scan's 15-day lookback window, closing the coverage blind
spots a monthly gap creates. The 1st-of-month runs additionally carry a
rotating **AI-pricing re-verification pass** (one domain cluster per month,
full surface quarterly) - the scan detects news from sources, but it cannot
detect silent staleness in figures already sitting in the reference files,
which is how the June 2025 AWS GPU price cuts went uncorrected for 14 months
(fixed in PR #129). Procedure and rotation table in
`pipeline/MONTHLY_WORKFLOW.md`.

**Scope reduction (2026-08-17).** The re-verification pass exists because absolute
figures sat in the reference files with nothing to correct them. The dated-price
rule (PR #141) and the figure purge (PR #142) remove most of that surface: LLM
token rates are now expressed as ratios and multipliers routed to the AI Pricing
Hub, and the figures that remain (SaaS seat prices, storage and egress rates,
which the hub does not serve) carry an inline as-of date. The rotation still
matters for those, but the pass is now a check on a short dated list rather than
a hunt across every reference. When updating the rotation table, verify the
*dates* on the remaining banners rather than re-pricing tables that no longer
carry absolute rates.

The pipeline is human-in-the-loop: nothing is changed automatically. Every
proposed update goes through preview, approve/reject, and a guard-railed
execute pass before touching any reference file.

**Operational reference:** `pipeline/MONTHLY_WORKFLOW.md` (gitignored,
private; only present in the maintainer's local repo) is the step-by-step
doctrine for running a monthly batch - pre-flight checks, per-item review,
execute, PR management, failure-mode handling, cost guidance. The
`pipeline/README.md` alongside it covers the same workflow at a lower
technical level. Both are intentionally kept out of public Git history -
they document an operating discipline that depends on credentials, file
paths, and infrastructure specific to the maintainer's setup, none of
which belong in the public repo.

---

## Lessons learned

### Pipeline applier truncated 8 reference files (April-May 2026)

The bi-monthly pipeline `applier/` truncated 8 reference files across two runs:
- PR #8 (commit 647a7ef, 15 April 2026) damaged finops-azure.md (later restored
  by commit dfab33b) and introduced the trailing-`> Sources` truncation in
  finops-itam.md and finops-sam.md
- "Content update - 1 May 2026" (commit 3e64f59) made 130 insertions / 5566
  deletions across 6 files (aws, azure, gcp, framework, ai-dev-tools, for-ai)
  in what was supposed to be an additive content update

The recovery (May 2026) restored each file from a pre-truncation commit and
re-injected the few real additions identified in the diffs.

**Why it happened.** The applier prompt instructed the LLM to "preserve the existing
file structure" and "preserve the CC BY-SA 4.0 footer line exactly as it is". On long
files (1500+ lines) the LLM ignored these instructions roughly 5% of the time -
producing diffs whose "after" state was hundreds or thousands of lines shorter than
"before". The instructions were prompts, not enforced guarantees.

**Why it was not caught.** The previous recovery (PR #8 -> commit dfab33b) fixed
symptoms without fixing the pipeline, so the same failure mode recurred 16 days later.
A truncated file looks valid in `git diff` review (the diff stops where the file stops);
the only signal was the missing footer at the end, which no automated check verified.

**Guard rails added (`pipeline/applier/file_updater.py`):**
- Before each apply, snapshot the file to `skills/cloud-finops/references/.backups/` with
  a timestamped name
- After each apply, run `validate_post_apply`:
  - **Deletion threshold**: reject any update whose net change is < -20% of the
    original line count (when original > 100 lines)
  - **Footer presence**: require the last 300 chars to contain both "OptimNow"
    and "CC BY-SA"
  - **Double-HR check**: reject if "---\n\n---" appears in the last 500 chars
    (artefact of an emptied Sources block)
- On any guard rail failure, automatically restore from the backup
- Run-level fail-safe: if more than 2 files fail validation in a single run,
  abort the entire run before committing

**Documentation drift correction.** The same recovery surfaced ~10 spots where doc
had not kept pace with reference growth (AGENTS.md and llms.txt listed only 17
references when 28 existed; install.sh ChatGPT/Gemini routing missed the 6-7 newest
domains; "6 setup options" appeared in 4 files when INSTALLATION.md had moved to
12 tools). The PR-checklist in this file now requires updating AGENTS.md, llms.txt,
and the install.sh per-tool routing whenever a reference is added.

### When in doubt, validate the baseline before comparing

When asked to compare this skill to another repo, an agent that compares against the
truncated state will conclude the other repo is more comprehensive than it really is.
Always check that key reference files end with the OptimNow footer (and not
mid-sentence) before drawing any coverage comparison.

### The May 2026 truncations had a config root cause, not a prompt-instruction one (2026-05-15)

The "Pipeline applier truncated 8 reference files" lesson above states that
the LLM "ignored instructions roughly 5% of the time" on long files. **That
framing was wrong, and the audit doc (`pipeline/pipeline-audit-2026-05.md`)
inherited it.** The actual root cause was `pipeline/config.yaml`
`max_tokens: 4096`. Reference files like `finops-aws.md` (2657 lines, ~12K
output tokens) cannot be returned in full when the model is capped at 4096
output tokens; the model writes from the top, hits the cap, stops mid-file,
and the result reads as "the model ignored the footer instruction". It was
100% deterministic on any file >3K tokens, not "5% of the time".

The fix is one line: `max_tokens: 16384`. The elaborate tool-use migration
that the audit recommended as Phase-2 Item 1 was solving the wrong problem
and was rolled back on 2026-05-15 after Opus regressed to legacy XML format
under `tool_choice` (it emitted XML strings inside the JSON `hunks` field).

**Compounding error: 79 passing tests with hand-crafted mocks of the
Anthropic response gave false confidence.** None of the Harden A or B tests
talked to the real API. The tool-use migration looked correct in tests and
failed in the first production run. Lesson for future LLM-loop work in this
repo: **at least one real-API smoke test must pass before declaring any
batch ready.** `pipeline/smoke_test.py` is the answer; run it before any
production scan.

**A separate guard-rail gap surfaced on the same day.** The three guards in
`validate_post_apply` only ran inside `apply_with_guard_rails`, which only
runs during `--execute`. Preview mode showed proposals without validation,
so a 89%-deletion diff displayed cleanly in the user's terminal. Preview-mode
guard rails were added via `_validate_content` in `_process_change`; a
broken proposal now prints "REJECTED by guard rail" rather than a
1000-line unified diff.

See `pipeline/pipeline-audit-2026-05.md` "Correction (2026-05-15)" and
`pipeline/pipeline-harden-plan.md` "Status update (2026-05-15)" for the full
forensic.

### Content update pipeline is a proposal engine, not an automated updater (2026-05-15)

The 2026-05-15 first-real-run session (~5 hours, ~$13-15 in Anthropic credits,
2 PRs of content shipped + 3 doctrine PRs) clarified the operational reality
of the content-update pipeline. **The pipeline detects, classifies, and
proposes; the human reviews, approves, integrates.** Full automation was
never the goal, but the day's debugging proved it isn't even theoretically
achievable for files >1500 lines without manual intervention.

What the session established:
- **Cadence dropped to monthly** (was twice-monthly). Each run takes 2-4
  hours of focused review; twice-monthly was unsustainable. *Superseded on
  2026-08-10 - the cadence went back to twice-monthly. See the Content update
  pipeline section above for the current schedule.*
- **Architecture: FIND/REPLACE plain-text edits**, not whole-file rewrites
  and not JSON tool-use hunks. Whole-file rewrites hit Opus's 32K output
  token ceiling on big files and silently truncated. Tool-use hunks failed
  because Opus regressed to legacy XML format under `tool_choice`. Plain-
  text FIND/REPLACE blocks with a regex parser is the only approach that
  worked reliably in production.
- **Operating doctrine documented** at `pipeline/MONTHLY_WORKFLOW.md`
  (gitignored, maintainer-local) - step-by-step monthly workflow,
  failure modes with detection criteria, cost guidance, PR conflict
  handling. Read it before running the pipeline manually.
- **Three durable engineering changes** retained from the day:
  - `pipeline/smoke_test.py` - real-API smoke test against the smallest
    reference file. Run before any batch; ~$0.05 catches the issues that
    mock-only unit tests miss.
  - Per-run structured report at `pipeline/state/runs/<id>/report.json` -
    written by every run including failed ones, the audit primitive.
  - Preview-mode guard rails - `_validate_content` runs against the
    proposed content before showing it as a diff, so unsafe proposals
    print "REJECTED by guard rail" instead of a 1000-line broken diff.
- **Big files are at the edge of the auto-edit envelope.** At the time this
  meant `finops-aws.md` (2,657 lines) and `finops-azure.md` (~3,000 lines),
  which routinely produced guard-rail rejections or anchor failures for
  non-additive changes. The August 2026 split (see Closed gaps) removed both
  from that band; the largest files are now `finops-azure.md` (~1,800 lines)
  and `finops-aws-patterns.md` (~1,470). Treat roughly 1,500 lines as the
  threshold above which structural changes need manual integration. Additive
  edits (new subsection, new note) work fine at any size.

The pipeline now sits in a sustainable operating shape. Future work is
about *simplification* (reducing the manual review surface), not adding
more automation.

### MCP Apps rendering in Claude is allowlisted, not earned by conformance (2026-08-16)

The `ui://cloud-finops/playbook-viewer` MCP App shipped in PR #133 had never
been opened in a real host - only against a test harness that simulates the
`postMessage` handshake. The 2026-08-16 session finally validated it, and the
result reorders the whole "publish a remote MCP server" plan.

**What the validation established.** Running MCPJam Inspector against the
local stdio server (no hosting, no public endpoint, about an hour of work):

- The viewer **works**. It renders in MCPJam's ChatGPT host emulation:
  frontmatter parsed into badges, the six sections laid out with their
  colour coding, the footer line present. The prototype is a validated
  component, not a hypothesis.
- Two conformance defects were found by auditing the HTML against
  `modelcontextprotocol/ext-apps` `specification/2026-01-26/apps.mdx`
  *before* the first live run, and fixed in PR #135: an incomplete
  `ui/initialize` handshake (missing `protocolVersion` / `clientInfo` /
  `capabilities`; the spec's reference call passes `protocolVersion:
  "2026-01-26"`), and `target="_blank"` links, which the host sandbox
  swallows because it grants `allow-scripts` and `allow-same-origin` but
  not `allow-popups` - clicks now go through the host's `ui/open-link`.
- MCPJam's accepted resource mime types, from its own error message:
  `text/html;profile=mcp-app` (the spec value, which is what the server
  declares), `text/html+skybridge`, `text/html`. A deliberate experiment
  substituting the older `text/html+mcp` disproved the mime-type
  hypothesis cleanly and is *not* retained.

**The finding that changes the plan.** The same server renders as plain
text in Claude - in MCPJam's Claude emulation, and in real Claude Desktop
against the local stdio server. The cause is not conformance. Anthropic's
[Use interactive connectors in Claude](https://support.claude.com/en/articles/13454812-use-interactive-connectors-in-claude)
names the connectors that may render UI (Amplitude, Asana, Box, Canva,
Clay, Figma, Hex, Slack) and states that a self-built interactive
connector "must meet additional design, security, and testing
requirements", pointing at the Connectors Directory submission and review
process. `anthropics/claude-ai-mcp#471` reports exactly this failure for a
spec-correct custom remote connector on Claude Web and was closed as *not
planned* - consistent with intended behaviour rather than a bug.

**So SEP-1865 conformance is an eligibility condition, not an entry
ticket.** A custom connector, remote or local, gets the text fallback no
matter how correct it is. The path to rendering in Claude is: conformant
server, then publicly reachable remote deployment, then Connectors
Directory submission, then Anthropic review - the last two outside the
maintainer's control and on an unpublished timeline.

**Consequences.**

- A remote deployment (Alpic) is **necessary but nowhere near sufficient**
  for interactive rendering. It must therefore be justified on
  distribution grounds alone: letting a non-technical user paste a URL
  into claude.ai instead of installing a PyPI package. That is the
  decision taken on 2026-08-16, with the interactive viewer explicitly
  *not* counted as a benefit.
- Do not treat the "Interactive" badge in the Connectors Directory as
  reachable by shipping correct code.
- The transferable discipline: **validate a host-dependent feature in a
  real host before planning the infrastructure that depends on it.** An
  hour in MCPJam, costing nothing and requiring no deployment, produced a
  finding that would otherwise have surfaced at the end of a multi-day
  hosting project. The prototype had sat unvalidated since PR #133
  precisely because the only test in place asserted the resource existed,
  never that it rendered.

---

## Roadmap

This section lists work that is intentionally not shipped and the trigger to revisit. It is
the durable record of "what's deliberately out of scope right now and why" - distinct from
GitHub issues, which track in-flight work.

### In-flight (write when prerequisites land)

- **P1 - Audit, harden, stabilise, and publish the refresh pipeline.** The pipeline
  in `pipeline/` is currently frozen (`run_apply.py.FROZEN`) since the May 2026
  truncation incident (8 reference files truncated across two runs - see the
  `Lessons learned` section above for the forensic). Hard guard rails are in
  the applier (`validate_post_apply` with deletion threshold + footer presence +
  double-HR check; `apply_with_guard_rails` with snapshot + rollback; run-level
  fail-safe at 2 failures), and 9 unit tests pass against synthesised failure
  modes. What is missing is end-to-end validation, hardening of the rest of the
  pipeline, and a decision on public release.

  **Phase 1 (Audit) landed:** [`pipeline/pipeline-audit-2026-05.md`](pipeline/pipeline-audit-2026-05.md)
  covers module-by-module contracts, LLM-call inventory, destructive-actions
  inventory, guard-rails verification (9/9 tests pass; full suite 43/43 green),
  implicit assumptions, gap analysis vs Phase-2 targets, recommended
  remediation order (9 items, 5 blocking unfreeze), and proposed unfreeze
  criteria (U1-U4 from the Roadmap below, plus U5-U8 from the audit). The
  remaining three phases are still below; Phase 2 (Harden) is the next PR.

  Four phases:

  1. **Audit (week 1).** Read every module - `scanner/` (fetch + classify),
     `proposer/` (CHANGES.md report builder), `applier/` (file rewrite, now
     guard-railed), `alerter/` (Gmail draft builder), `state/`. Document each
     module's contract (inputs, outputs, side effects, failure modes), the
     LLM prompts in use, and any place where the pipeline takes a destructive
     action. Identify implicit assumptions and any other module besides
     `applier/` that can write to `skills/cloud-finops/references/` or `skills/cloud-finops/playbooks/`
     - if anything else writes there, it must inherit the same guard-rail
     contract.
  2. **Harden (week 1-2).** Bring code-level validators to the modules that
     currently rely on prompt instructions. Concrete targets: `scanner/`
     validates fetch results (HTTP status, content-type, minimum payload
     length) so a 200-with-empty-body cannot become a "this source has no
     news" classification; `proposer/` validates that proposed CHANGES.md is
     well-formed before write. **The third target originally listed here -
     switching `applier/file_updater.py` to the structured-output (tool-use)
     pattern - is withdrawn.** It was attempted and rolled back on 2026-05-15
     when Opus regressed to legacy XML format under `tool_choice`; the shipped
     architecture is plain-text FIND/REPLACE blocks with a regex parser (see
     the 2026-05-15 lessons above). Do not resurrect it. Every
     module produces a per-run structured report (one JSON file per run,
     archived under `pipeline/state/runs/<timestamp>/`) so post-hoc audit
     does not depend on stdout scrolling. Add ratchets: secrets handling
     (no API keys in commit messages, no .env in stdout), idempotency
     (re-running the same change produces zero diff), and replay-from-state
     so a partial failure can be resumed.
  3. **Stabilise (week 2-3).** Define the un-freeze criteria explicitly.
     Recommended set: (a) 5 consecutive dry runs against the historical
     change archive produce zero false-positive guard-rail rejections AND
     zero silent truncations; (b) a fresh real run on a synthetic forked
     references directory completes end-to-end without manual intervention;
     (c) the run-level fail-safe correctly aborts a run that injects 3+
     truncations across 3 different files; (d) all `pipeline/tests/`
     unit tests pass on Python 3.10/3.11/3.12. When all four are green,
     `mv pipeline/run_apply.py.FROZEN pipeline/run_apply.py` to unfreeze.
     Document the unfreeze decision and the test evidence in the
     `Lessons learned` section of this CLAUDE.md so it is auditable.
  4. **Publish (week 3-4, requires separate strategic decision).** The
     pipeline is currently gitignored as "private until public release"
     (per the existing `## Content update pipeline` section above). The
     decision is whether public release adds more credibility (dogfooding
     the doctrine that "agentic FinOps must be auditable", letting the
     community contribute guard rails) than complexity (maintaining a
     public repo, exposing internals like `sources.yaml`, prompt
     strategies, .env handling, the OptimNow API key rotation cadence).
     Two viable shapes if the answer is yes:
     - **Same repo, public top-level `pipeline/` directory** (most
       transparent; matches the doctrine). Keeps `.env*` and runtime
       state gitignored. Maximum benefit, maximum maintenance burden.
     - **Separate repo `OptimNow/cloud-finops-skills-pipeline`**
       (compartmentalises the privacy boundary; harder to dogfood).
       Lower exposure, lower transparency.
     Either way, the Lessons learned section becomes the public artefact
     that proves the discipline (the incident, the recovery, the guard
     rails, the unfreeze criteria). Trigger: phases 1-3 must complete
     before this decision is even on the table.

  Cross-references: this work directly extends the `Lessons learned`
  section above and should produce a follow-up Lessons learned entry
  describing the un-freeze evidence.

- **WasteLine extension to Azure and GCP.** `finops-waste-detection-playbooks.md` covers the
  eight-category waste taxonomy and references the WasteLine appliance for AWS automation;
  Azure and GCP coverage currently routes to the in-cloud pattern catalogues
  (`finops-azure-patterns.md`, `finops-gcp.md`). When WasteLine ships Azure and
  GCP providers, update the operational tooling section to reflect the broader coverage and
  remove the "for Azure and GCP, see in-cloud catalogues" caveat.

- **WasteLine egress detection rules.** Category 8 (egress / data transfer) was added to the
  taxonomy in August 2026 as doctrine only - WasteLine implements Categories 1-7. Egress
  waste is attributed from CUR usage types plus VPC Flow Logs rather than from resource-state
  inspection, so it needs a different ingestion path in the appliance. Trigger: an engagement
  where egress is a top-5 line item and manual attribution proves too slow to repeat. Until
  then the operational-tooling section must keep saying so explicitly - the doctrine forbids
  claiming tool coverage that does not exist.

- **Playbook coverage for `commitment-mismatch`.** The waste taxonomy defines the category and
  the MCP `find_playbooks` tool advertises it as a facet value, but no playbook carries it, so
  the query returns empty. Either write the playbooks (RI utilisation gap, expiring commitment
  without renewal decision, Savings Plan covering the wrong family) or accept the gap
  knowingly. Surfaced by the 2026-08-02 repository review (F9).

- **OptimNow doctrine layer.** Today the reasoning lens lives inside
  `optimnow-methodology.md` (visibility before optimisation, diagnose before prescribing,
  connect cost to value, recommend progressively). The intent is to grow this into a
  named doctrine that takes opinionated, opposable positions vs the FinOps Foundation
  framework rather than restating it. Theses to develop, each as its own short doctrine
  file in a future `skills/cloud-finops/doctrine/` directory:

  - **Business value before maturity.** Every recommendation must answer "what business
    outcome does this protect or unlock?" Cost reduction without a value lens is a leak.
  - **Maturity is contextual, not aspirational.** Verticals where cloud is not a revenue
    generator (industrial, public sector, regulated services) do not need to reach Run.
    Crawl + selective Walk is the right state when cloud is a cost centre. Verticals where
    cloud IS the product (SaaS, AI-native, marketplaces) need Run because cloud efficiency
    directly drives gross margin and pricing. Pushing every org toward Run is malpractice.
  - **Recommend progressively, not heroically.** Quick wins that prove the discipline
    earn the right to do structural work. Skipping the quick wins to go straight to
    chargeback or commitment automation creates credibility-burning failures.
  - **WasteLine and an agentic operating model.** FinOps must be agentic - signal-based
    detection (WasteLine), AI-driven recommendation, automation-with-human-confirm. The
    previous era's monthly-spreadsheet-review FinOps does not scale to AI-era spend
    velocity. The operating model has to assume agents in the loop, not periodic human
    audits.
  - **Critical reading of vendor sustainability and FinOps claims.** Especially the claims
    of vendors that fund the FinOps Foundation through dues and sponsorship. Their
    incentives are not aligned with practitioner truth-telling. The doctrine should
    teach a critical-read posture by default and flag vendor-funded claims explicitly.
  - **There is nothing cultural about FinOps - the "FinOps culture" frame is a
    non-sequitur.** FinOps is an operating discipline (allocation, anomaly, commitment,
    rightsizing, governance). Calling it a "culture" is what allows organisations to
    avoid measurable outcomes. In the agentic era this matters even more - culture
    cannot be encoded into agents, but discipline can. The doctrine should oppose the
    FF-central "culture" framing and replace it with explicit operating-discipline
    metrics.
  - **Provider-mechanics-first, FOCUS-aware, vendor-claim-skeptical.** As distinguished
    from a "FOCUS-first" posture (which is a restatement of FF positioning, not a
    practitioner stance). FOCUS is a useful normalisation layer; native columns
    (CUR `unblended_cost`, Azure `costInBillingCurrency`, BigQuery `cost_at_list`) reveal
    biases that FOCUS can hide. Document both, name the trade-off, prefer the lens that
    answers the question.

  When this lands, also remove the "Where this differs from the FinOps Foundation"
  framing from `optimnow-methodology.md` and replace it with a pointer to the doctrine
  layer.

- **Public Custom GPT for ChatGPT users.** The current ChatGPT install path is
  self-host: `./install.sh --tool chatgpt --grouped` produces 10 grouped knowledge
  files the user uploads themselves. A public Cloud FinOps GPT in the OpenAI GPT
  Store would replace that with a single click for non-technical users. Build steps:
  (1) run the grouped installer once to get the artefacts; (2) create the GPT in
  `chatgpt.com/gpts/editor`, paste `instructions.md`, upload the 10 grouped knowledge
  files; (3) set name, category, visibility = Anyone with link / Public; (4) capture
  the resulting `https://chat.openai.com/g/g-XXXXX` URL and replace the placeholder in
  `README.md`'s install table. Maintenance burden: a GitHub Action that re-builds the
  artefacts on each release, plus a manual re-upload to ChatGPT (their API does not
  expose a "publish new version" endpoint for Custom GPTs). Cadence target: monthly
  refresh on top of the monthly source-update batch.

- **Public Gemini Gem for Gemini users.** Same shape as the ChatGPT GPT. Build
  steps: (1) run `./install.sh --tool gemini` to produce the 10 grouped knowledge
  files; (2) at `gemini.google.com/gems/`, create a new Gem, paste `instructions.md`,
  upload the 10 grouped files; (3) set the visibility, capture the public Gem URL and
  replace the placeholder in `README.md`. Maintenance burden: same as the GPT (manual
  re-upload, no API). Trigger: ship the GPT first, see whether the install-time
  friction reduction matters, then mirror to Gemini.

### Depth passes (extend existing files when bandwidth allows)

- **Extend GreenOps depth to Azure and GCP.** The May 2026 GreenOps pass added AWS-specific
  depth to `references/greenops-cloud-carbon.md` (Sustainability Console v2 with Methodology v3
  alignment, the unused-capacity ventilation trap, critical reading of AWS sustainability claims,
  AWS region intensity anchors with the 15x gap, hardware/storage anchors, Well-Architected
  Sustainability Pillar SUS01-SUS06 with critical-read notes). The next pass should bring the
  same depth to Azure and GCP:
  - **Azure**: Emissions Impact Dashboard refresh (current methodology version, scope coverage,
    location-based vs market-based handling), Azure region intensity anchors with concrete
    numbers, Azure-specific hardware anchors (Cobalt 100, Ampere Altra, Spot equivalents), and
    Azure Well-Architected sustainability guidance critical reading.
  - **GCP**: Carbon Footprint refresh (granularity, scope coverage, location-based vs
    market-based view), GCP region intensity anchors, GCP-specific hardware anchors (Axion, Tau
    T2A, Spot/preemptible equivalents).
  - Keep the engagement-framing section vendor-agnostic - it does not need to be duplicated
    per provider. The trade-off tables, four-quadrant cost-vs-carbon framework, and CSRD
    stakeholder roles already apply across all three providers.

### Deferred reference files

These files were identified in the white-space analysis (May 2026) and explicitly deferred,
with the rationale captured here so future work picks them up at the right moment rather
than re-litigating priority. Tracking issue: `OptimNow/cloud-finops-skills#55`.

| Proposed file | Priority | Trigger to revisit | Why deferred |
|---|---|---|---|
| `finops-tools-services.md` | P2 | Next engagement raises a vendor-evaluation question | OptimNow has implicit views (FinOps Toolkit, MCP, OpenCost) but no formal write-up; better to write against a real client question than a generic checklist |
| `finops-practice-operations.md` | P2 | Next Walk to Run client engagement starts | `optimnow-methodology.md` covers the consultancy-positioning lens; this would be the operator-grade discipline below it (three-cadence operating model, per-Capability scorecard, allied-discipline integration charter) |
| `finops-forecasting.md` | P2 | Non-AI forecasting demand emerges | `finops-ai-value-management.md` covers AI forecasting; non-AI demand has not surfaced in current engagements |
| `finops-unit-economics.md` | P2 | Non-AI unit-economics demand emerges | Same reasoning as forecasting; AI-side covered by AI value management and finops-for-ai files |
| `finops-education-enablement.md` | P2 | Demand emerges; consider folding into practice-operations | Smaller scope than the other P2 files; could double as a section in practice-operations |
| `finops-benchmarking.md` | P3 | Client engagement specifically requires it | Clients rarely ask; external benchmarking has well-known data-quality issues. Could be a section in `finops-framework.md` |
| `finops-cost-warehouse.md` | P3 | Engagement requires it (e.g. Snowflake-FinOps integration) | Heavy lift, specialist content (FOCUS conformed-dim modelling, dbt + semantic layer, CUR2 / Azure Cost Mgmt / BigQuery loading patterns, late-binding analytics) |
| `finops-executive-strategy-alignment.md` | **Will not write** | (no trigger - deliberately not covering) | The 2026 FCP added "Executive Strategy Alignment" as a capability. The OptimNow doctrine ("connect cost to business value", the CFO test) already covers the practitioner-grade version of executive engagement; the FCP framing reads as a positioning concept rather than an operating discipline. If a client engagement specifically asks for the FCP-aligned executive-strategy artefact, it can be written then; the Roadmap-default position is not to ship it as a separate reference. |

**Note on Budgeting**: Budgeting is NOT a deferred capability. It is covered as a
secondary in `finops-anomaly-management.md`, `finops-allocation-showback.md`,
`finops-chargeback.md`, and `finops-onboarding-workloads.md` because each of
those files has a substantive Budgeting section (AWS Budgets, Azure Budgets and
Alerts, GCP budget anomaly alerts, OCI Budgets, Snowflake Budgets, Databricks
budget policies, AI investment budgets, the 60-90 day forecast-then-commit rule
at intake, the soft-to-hard chargeback budget enforcement). The FCP coverage
matrix renders Budgeting as `[~]` (any-coverage via secondary) rather than
`[ ]` (true gap) once the frontmatter declares it. There is no plan to ship a
dedicated `finops-budgeting.md` because the cross-cutting nature of budgeting
is better served by the dispersed coverage.

**Note on Automation, Tools & Services**: same shape as Budgeting. Covered as
secondary in `finops-tagging.md` (MCP automation, IaC enforcement) and
`finops-waste-detection-playbooks.md` (WasteLine appliance). Plus the
`finops-tools-services.md` deferred entry above which would be the dedicated
write-up if engagement demand emerges.

When picking up a deferred item: read the rationale above, check the white-space analysis
context (Cletrics comparison report dated 2026-05-03 in `~/Downloads/`, plus implementation
plan in `~/.claude/plans/optimnow-cloud-finops-recommendations-followup.md`), and confirm
the trigger is real before starting the file.

### Closed gaps (May 2026 batch)

These files shipped during the white-space analysis follow-up (PRs #48, #50, #51, #52, #54,
#56) and now exist in the catalogue. Listed here for the record:

- `finops-anomaly-management.md` (PR #48) - Anomaly Management as standalone Inform capability
- `finops-allocation-showback.md` (PR #50) - Allocation methodology + showback delivery
- `finops-chargeback.md` (PR #51) - Chargeback + Finance/accounting prerequisites
- `finops-onboarding-workloads.md` (PR #52) - Migration-time cost hygiene + M&A
- `finops-kubernetes.md` (PR #54) - Cross-cluster K8s discipline (EKS/GKE/AKS)
- `finops-waste-detection-playbooks.md` (PR #56) - Seven-category waste taxonomy + WasteLine
  (extended to eight categories in August 2026 with egress / data transfer)
- Split of `finops-aws.md` and `finops-azure.md` (August 2026) - the second-level
  progressive-disclosure fix from the 2026-08-02 review (F15). Each became core /
  commitments / patterns: AWS 2,893 lines -> 899 + 604 + 1,463; Azure 3,211 -> 1,810 +
  983 + 478. A routine AWS Savings Plans question now loads ~8.3K tokens instead of
  ~44K (-82%); an Azure commitment question ~13.6K instead of ~43K (-69%).

  Two things the pre-split analysis got wrong, recorded so the next restructure does
  not repeat them. First, Azure's two rightsizing sections were **not** duplicated -
  they were complementary and mis-ordered, with the fundamentals sitting ~1,200 lines
  *after* the advanced Advisor material and a note in the later section explaining the
  relationship. They were merged and reordered, not deduplicated. Second, the repeated
  liquidity table **was** a real duplication but a deliberate one: the file said so
  explicitly, justifying it because the two sections sat ~2,000 lines apart. Once both
  landed in `finops-azure-commitments.md` that rationale disappeared, so the duplicate
  collapsed to a cross-reference. The lesson is to read the seam before assuming drift -
  "duplicated content" in a long file is as often deliberate redundancy or bad ordering
  as it is pipeline damage.

- YAML FCP frontmatter pass across all 22 pre-existing references (PR #53)
- `skills/cloud-finops/playbooks/` directory (PRs #64, #66, #67, #83) - RAG-friendly
  named-pattern playbooks (`<scope>-<pattern>.md`, ~2-3KB each,
  Problem/Symptoms/Detection/Fix/Anti-pattern/See also format) covering AWS (incl. SageMaker + GPU), Azure, GCP, and cross-cloud waste patterns.
  Routed from SKILL.md and POWER.md "named waste pattern" rows
- `scripts/fcp-coverage.sh` + top-level `fcp-coverage.md` (PR #64) - bash matrix that
  parses FCP frontmatter from every reference and renders a 22-capability coverage table.
  Run on each PR; `[~]` secondary-only cells distinguish dispersed coverage from true gaps

---

## Model compatibility

The skill files are plain markdown - any LLM can read them. What differs across models
is how well they follow the structure and avoid hallucinating billing rules.

- **Claude** (Code, .ai, API) - reads SKILL.md natively, no extra configuration needed
- **Kiro IDE** - reads POWER.md natively
- **GPT, Gemini, other models** - inject the reference files as context and add the
  response contract from INSTALLATION.md ("API integration (system-prompt injection)" ->
  "Recommended response contract") to the system prompt

The response contract ensures consistent output structure (Context, Recommendation,
Metrics, Business impact) and prevents models from inventing pricing figures or
discount mechanics.

---

## How to add a new reference file

Follow these five steps whenever you add a new domain:

1. **Create the reference file** in `skills/cloud-finops/references/`
   - Name it `finops-{domain}.md` (or `{category}-{domain}.md` for non-FinOps topics like `greenops-cloud-carbon.md`)
   - Follow the structure of an existing reference file as a template
   - Include practical guidance, not abstract theory
   - **Open the file with YAML FCP frontmatter** (see "Reference-file frontmatter" section below)

2. **Add a routing entry in SKILL.md**
   - Add a row to the "Domain routing" table with the query topic and file path
   - (The old "Reference files" descriptive table was removed in the 2026-08
     token-efficiency pass - the routing table is now the single catalogue.
     Do not reintroduce a second per-file table.)

3. **Add a routing entry in POWER.md**
   - Add a row to the "Domain routing" table (same format as SKILL.md)
   - Add relevant keywords to the `keywords` list in the YAML frontmatter

4. **Update README.md**
   - Add a bullet under "What this skill covers"
   - Add the file to the "Directory structure" listing
   - Add usage examples if applicable

5. **Do NOT bump versions in the content PR (release-train rule, 2026-08)**
   - Content PRs never touch `.claude-plugin/plugin.json`,
     `.claude-plugin/marketplace.json` versions, or `mcp_server/pyproject.toml`.
     Every `plugin.json` bump that reaches main triggers one tag + GitHub
     Release + PyPI publish, so per-PR bumps mean one publish per content PR
     and version-number collisions between parallel branches (the
     1.27/1.28/1.29/1.30 collision resolved by combined release PR #110).
   - Releasing is a separate, deliberate act: a small dedicated release PR
     bumps all three together - `plugin.json` version (minor for user-visible
     features), `marketplace.json` `metadata.version` (must match plugin.json;
     CI-gated by `scripts/check-marketplace-version.sh`), and
     `mcp_server/pyproject.toml` version. Update the marketplace plugin
     description topic list in the same release PR if new domains shipped.
     The version number is decided at release time, never pre-assigned on
     content branches. Natural release moment: after the monthly content
     batch, or whenever accumulated merged content should ship.

---

## Reference-file frontmatter

All reference files carry YAML FCP frontmatter that maps the file to the FinOps Framework
Capability it serves. New files must follow the same convention. Minimum schema:

```yaml
---
name: {file-identifier}                              # e.g. finops-aws
fcp_domain: "{one of 4 FCP domains}"                 # Understand Usage & Cost / Quantify Business Value / Optimize Usage & Cost / Manage the FinOps Practice
fcp_capability: "{primary capability}"               # the capability the file serves first
fcp_capabilities_secondary: ["{cap}", "{cap}"]       # optional - other capabilities the file touches
fcp_phases: ["{Inform}" or "{Optimize}" or "{Operate}", ...]   # one or more
fcp_personas_primary: ["{persona}", ...]             # FinOps Practitioner / Engineering / Finance / Product / Procurement / Leadership / SRE / Platform Engineering / Sustainability / Security / ITAM / etc.
fcp_personas_collaborating: ["{persona}", ...]       # optional
fcp_maturity_entry: "Crawl" | "Walk" | "Run"         # the gate below which the file is premature
---
```

Why this matters:
- Programmatic routing (future "load all references where fcp_capability=Anomaly Management"
  filter is feasible)
- Maturity gates (downstream tools and readers can detect when a reference is premature for
  their organisation's stage)
- Persona awareness (makes it explicit who each reference is written for, useful when
  curating subsets for specific audiences)
- Author discipline (declaring the FCP capability forces a check on whether the file
  actually serves what it claims to serve)

Do **not** add a `description` field to reference-file frontmatter. The visible blockquote
description on line 3 (after the H1) already serves that role; a frontmatter description
would render twice in some tools. The exception is `skills/cloud-finops/SKILL.md` which DOES need
a `description` field for the Claude.ai upload skill loader (see "Content rules" below).

---

## Content rules

**Writing style**
- Use straight dashes (`-`), never em dashes
- Use British spelling for public-facing content (optimisation, organisation, behaviour)
- Be direct and practical. Diagnose before prescribing
- Connect cost recommendations to business outcomes

**SKILL.md frontmatter**
- The `description` field must be **under 1024 characters** (Claude.ai upload limit)
- Only `name` and `description` are required in the YAML frontmatter
- Do not add a `license` field to the frontmatter (it renders as visible text in Claude.ai)

**Sourcing**
- **Mechanics claims cite provider documentation, not newsletters.** Anything that
  states how billing actually works - eligibility, payment options, retirement dates,
  retention windows, rate multipliers - must link to the provider's own docs. A
  secondary source (newsletter, vendor blog, community post) is acceptable only as a
  *lead*, and the claim must then either be confirmed primarily or carry an explicit
  sourcing note saying it is unconfirmed. The 2026-08 review found a Redshift RI claim
  that a newsletter had scoped wrongly (the change applied to RG instances, not to
  1-year RIs generally) - that class of error is what this rule prevents.
- **Cite papers by title, not by bare identifier.** An `arXiv:NNNN.NNNNN` with no title
  cannot be sanity-checked by a reader and looks indistinguishable from a hallucinated
  citation. Include author, title, and link.
- **Name a vendor only with a viability caveat** if it is early-stage. Recommending a
  seed-stage tool into a client's production path is a continuity risk the reference
  should flag, not bury.

**License**
- All content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- Credit OptimNow as the original author
- Include the license footer on new reference files if following the existing pattern

**Do not commit**
- `INTERNAL_NOTES.md` is gitignored and must never be committed
- `pipeline/` is gitignored and must not be made public without explicit decision

---

## Testing changes

After editing reference files, verify them by asking questions in the domain you changed.
Good test patterns:

- Ask a question that requires specific billing mechanics (pricing, break-even, discount rules)
- Ask a maturity-sensitive question (the response should adapt to Crawl/Walk/Run context)
- Ask a cross-domain question that requires loading multiple references
- Test with a non-Claude model using the response contract to verify portability

---

## Pull request checklist

- [ ] New reference file follows the `finops-{domain}.md` naming convention
- [ ] YAML FCP frontmatter included on the new file (see "Reference-file frontmatter")
- [ ] Routing table updated in both SKILL.md and POWER.md
- [ ] README directory listing and "What this skill covers" section updated
- [ ] CLAUDE.md "Repository structure" directory listing updated (CI-gated by
      `scripts/check-docs-drift.sh` - a reference missing from the tree, or a
      tree entry with no file behind it, fails the `CI` workflow)
- [ ] AGENTS.md and llms.txt updated to reflect the new reference (the llms.txt
      "Key files" list is CI-gated by `scripts/check-llms-txt.sh` - a missing or
      stale entry fails the `CI` workflow, so this can't drift silently).
      AGENTS.md deliberately does not enumerate references - it shows a
      truncated tree and defers to CLAUDE.md - so there is nothing to update
      there unless the new file changes what AGENTS.md says about the repo.
- [ ] install.sh per-tool routing updated: ChatGPT inline routing table, Gemini
      grouped knowledge, and Cursor description must mention the new domain
- [ ] File ends with the OptimNow / CC BY-SA footer. References use
      `> *Cloud FinOps Skill by [OptimNow]... CC BY-SA 4.0...*`; playbooks use
      `> *Cloud FinOps Playbook by [OptimNow]... CC BY-SA 4.0...*`. No
      truncation mid-sentence or mid-table.
- [ ] If adding a new playbook, follow the format in
      `skills/cloud-finops/playbooks/README.md` (frontmatter schema, Problem /
      Symptoms / Detection / Fix / Anti-pattern / See also sections, OptimNow
      CC BY-SA footer), and update the named-
      pattern parenthetical in the ChatGPT / grouped routing tables in
      install.sh. SKILL.md and POWER.md carry representative examples only
      (since the 2026-08 token-efficiency pass) and defer to
      `playbooks/README.md` for the full list - only extend their examples
      if the new pattern is a distinct new family (new provider or new
      waste category), not for every added playbook.
      (Exact reference/playbook counts were removed from prose across the repo in
      2026-07 precisely so they no longer need hand-bumping - do not reintroduce
      hardcoded "N references / N playbooks" counts; use "the reference library"
      phrasing. `llms.txt` is the one list to keep current.)
- [ ] **Content PR: no version bump.** `.claude-plugin/plugin.json`,
      `.claude-plugin/marketplace.json` `metadata.version`, and
      `mcp_server/pyproject.toml` are untouched (release-train rule - see step 5
      of "How to add a new reference file"). A `plugin.json` bump reaching main
      publishes to PyPI, so bumps live only in dedicated release PRs.
- [ ] **Release PR only: bump all three versions together** - `plugin.json`
      (minor for user-visible features), `marketplace.json` `metadata.version`
      (must match; CI-gated by `scripts/check-marketplace-version.sh` via the
      `marketplace version in sync` workflow), `mcp_server/pyproject.toml`.
- [ ] Marketplace description in `.claude-plugin/marketplace.json` reflects the new
      topic list (can ride the release PR). It carries no reference count by design -
      see the no-hardcoded-counts rule above.
- [ ] SKILL.md description stays under 1024 characters (CI-gated by
      `scripts/check-skill-description.sh`, which also warns above 950 so the
      ceiling is visible before it is hit)
- [ ] No em dashes in any public content
- [ ] No sensitive or internal files included
- [ ] Content is practical and based on how billing actually works, not on documentation summaries
- [ ] If the file deferred or replaced is in the Roadmap section, the Roadmap section is
      updated accordingly
