# CLAUDE.md

Project context for AI assistants and human contributors working on this repository.

---

## What this repo is

A structured, model-agnostic FinOps knowledge skill for AI agents. The `cloud-finops/`
folder contains reference files that give any LLM accurate Cloud FinOps expertise -
Claude, GPT, Gemini, or any MCP-compatible agent.

- **SKILL.md** - entry point for Claude Code and generic agents
- **POWER.md** - entry point for Kiro IDE (same references, different format)
- **references/** - domain-specific content files (billing mechanics, pricing, optimisation patterns)
- **INSTALLATION.md** - one cross-tool installer covering 11 tool integrations, plus
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
├── INSTALLATION.md        <- Setup instructions (11 tool integrations) + response contract
├── LICENSE.md             <- CC BY-SA 4.0
├── install.sh             <- One-liner installer script
├── assets/                <- Screenshots for installation guide
├── cloud-finops/          <- The skill (this is what gets installed)
│   ├── SKILL.md           <- Entry point + domain router
│   ├── POWER.md           <- Kiro IDE entry point
│   └── references/        <- 28 reference files, all with YAML FCP frontmatter
│       ├── optimnow-methodology.md         <- OptimNow reasoning lens, 4 pillars
│       ├── finops-framework.md             <- FinOps Foundation framework reference
│       ├── finops-for-ai.md                <- AI cost management discipline
│       ├── finops-ai-value-management.md   <- AI Investment Council, stage gates
│       ├── finops-genai-capacity.md        <- Provisioned vs shared capacity
│       ├── finops-ai-self-hosted-vs-managed.md  <- Self-host vs managed inference
│       ├── finops-ai-dev-tools.md          <- Cursor / Claude Code / Copilot / Windsurf / Codex
│       ├── finops-anthropic.md             <- Anthropic billing
│       ├── finops-aws.md                   <- AWS FinOps + commitment portfolio
│       ├── finops-bedrock.md               <- AWS Bedrock
│       ├── finops-azure.md                 <- Azure FinOps + commitment portfolio
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
│       └── finops-waste-detection-playbooks.md  <- Seven-category waste taxonomy + WasteLine
└── pipeline/              <- Content update pipeline (gitignored, private)
    ├── run_scan.py        <- Weekly scan entry point
    ├── run_apply.py       <- Review and apply entry point
    ├── config.yaml        <- Pipeline configuration
    ├── sources.yaml       <- 29 content sources (RSS, pricing pages, blogs)
    ├── scanner/           <- Fetcher + Sonnet-based classifier
    ├── proposer/          <- CHANGES.md report generator
    ├── applier/           <- Opus-based diff generator and file editor
    ├── alerter/           <- Gmail draft builder
    └── state/             <- Runtime state (scan results, history)
```

---

## Content update pipeline

The `pipeline/` folder contains a twice-monthly content scanner (around the 1st
and 15th) that detects FinOps-relevant
changes across 29 sources and proposes updates to the reference files. It is gitignored
and not part of the public distribution.

The pipeline is human-in-the-loop: nothing is changed automatically. Every proposed
update goes through review (list, preview diffs, approve/reject) before touching any
reference file. See `pipeline/README.md` for the full workflow.

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
- Before each apply, snapshot the file to `cloud-finops/references/.backups/` with
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
11 tools). The PR-checklist in this file now requires updating AGENTS.md, llms.txt,
and the install.sh per-tool routing whenever a reference is added.

### When in doubt, validate the baseline before comparing

When asked to compare this skill to another repo, an agent that compares against the
truncated state will conclude the other repo is more comprehensive than it really is.
Always check that key reference files end with the OptimNow footer (and not
mid-sentence) before drawing any coverage comparison.

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

  **Phase 1 (Audit) landed:** [`docs/pipeline-audit-2026-05.md`](docs/pipeline-audit-2026-05.md)
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
     `applier/` that can write to `cloud-finops/references/` or `cloud-finops/playbooks/`
     - if anything else writes there, it must inherit the same guard-rail
     contract.
  2. **Harden (week 1-2).** Bring code-level validators to the modules that
     currently rely on prompt instructions. Concrete targets: `scanner/`
     validates fetch results (HTTP status, content-type, minimum payload
     length) so a 200-with-empty-body cannot become a "this source has no
     news" classification; `proposer/` validates that proposed CHANGES.md is
     well-formed before write; the `Anthropic` API calls in
     `applier/file_updater.py` switch to the structured output (tool-use)
     pattern so the model returns a JSON object with explicit fields rather
     than free-form markdown that the Python code parses with regex. Every
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
  seven-category waste taxonomy and references the WasteLine appliance for AWS automation;
  Azure and GCP coverage currently routes to the in-cloud pattern catalogues
  (`finops-azure.md` 48-pattern, `finops-gcp.md` 26-pattern). When WasteLine ships Azure and
  GCP providers, update the operational tooling section to reflect the broader coverage and
  remove the "for Azure and GCP, see in-cloud catalogues" caveat.

- **OptimNow doctrine layer.** Today the reasoning lens lives inside
  `optimnow-methodology.md` (visibility before optimisation, diagnose before prescribing,
  connect cost to value, recommend progressively). The intent is to grow this into a
  named doctrine that takes opinionated, opposable positions vs the FinOps Foundation
  framework rather than restating it. Theses to develop, each as its own short doctrine
  file in a future `cloud-finops/doctrine/` directory:

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

- **Playbooks directory** (`cloud-finops/playbooks/`). Extract the named-pattern
  catalogues currently embedded in `finops-aws.md` (48 patterns), `finops-azure.md`
  (48 patterns), `finops-gcp.md` (26 patterns), and the seven-category taxonomy in
  `finops-waste-detection-playbooks.md` into individual playbook files (~2-3KB each).
  Format per playbook: symptoms / detection (CUR / KQL / BigQuery SQL) / fix /
  anti-pattern / sources. The reference files keep the patterns as in-context narrative
  for linear reading; the `playbooks/` directory exposes them as RAG-friendly chunks
  for ChatGPT / Gemini / generic LLM retrieval. Routing rule to add to SKILL.md and
  POWER.md: "named waste pattern X -> `playbooks/X.md`". Drift risk to manage: changes
  to a pattern must be applied in both places, or the reference file should be updated
  to reference the playbook by an inline Markdown link (e.g.
  `[aws-zombie-nat-gateway](../playbooks/aws-zombie-nat-gateway.md)`) instead of
  duplicating the content.

- **FCP coverage matrix tooling.** Adapt the approach from Cletrics' `fcp-coverage.sh`:
  a small bash script that parses `fcp_domain` / `fcp_capability` /
  `fcp_capabilities_secondary` from every reference frontmatter and emits a top-level
  `fcp-coverage.md` table mapping the 22 FCP capabilities to the references that cover
  them. Adds three benefits: (1) honesty signal vis-a-vis the framework - the matrix
  computes coverage from the actual repo, not from claims; (2) PR check - new
  references with a non-canonical capability or a missing frontmatter trip the script;
  (3) Roadmap-driven view - the matrix shows which capabilities have no primary owner
  yet. Current true gaps after the frontmatter-truth pass: KPIs & Benchmarking,
  Executive Strategy Alignment, FinOps Education & Enablement (all in the deferred
  table below). Budgeting and Automation Tools & Services were initially flagged
  as gaps but are covered dispersed - the matrix now renders them as `[~]`
  secondary-only after the frontmatter was updated to reflect that reality (PR
  following the FCP-2026 migration).

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
  refresh on top of the twice-monthly source updates.

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
- YAML FCP frontmatter pass across all 22 pre-existing references (PR #53)

---

## Model compatibility

The skill files are plain markdown - any LLM can read them. What differs across models
is how well they follow the structure and avoid hallucinating billing rules.

- **Claude** (Code, .ai, API) - reads SKILL.md natively, no extra configuration needed
- **Kiro IDE** - reads POWER.md natively
- **GPT, Gemini, other models** - inject the reference files as context and add the
  response contract from INSTALLATION.md (Option 6) to the system prompt

The response contract ensures consistent output structure (Context, Recommendation,
Metrics, Business impact) and prevents models from inventing pricing figures or
discount mechanics.

---

## How to add a new reference file

Follow these five steps whenever you add a new domain:

1. **Create the reference file** in `cloud-finops/references/`
   - Name it `finops-{domain}.md` (or `{category}-{domain}.md` for non-FinOps topics like `greenops-cloud-carbon.md`)
   - Follow the structure of an existing reference file as a template
   - Include practical guidance, not abstract theory
   - **Open the file with YAML FCP frontmatter** (see "Reference-file frontmatter" section below)

2. **Add a routing entry in SKILL.md**
   - Add a row to the "Domain routing" table with the query topic and file path
   - Add a row to the "Reference files" table with the filename, description, and approximate line count

3. **Add a routing entry in POWER.md**
   - Add a row to the "Domain routing" table (same format as SKILL.md)
   - Add relevant keywords to the `keywords` list in the YAML frontmatter

4. **Update README.md**
   - Add a bullet under "What this skill covers"
   - Add the file to the "Directory structure" listing
   - Add usage examples if applicable

5. **Bump the plugin version**
   - `.claude-plugin/plugin.json` minor version (e.g. 1.19.0 to 1.20.0) for user-visible feature changes
   - `.claude-plugin/marketplace.json` description (update the reference file count and topic list)

---

## Reference-file frontmatter

All 28 reference files carry YAML FCP frontmatter that maps the file to the FinOps Framework
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
would render twice in some tools. The exception is `cloud-finops/SKILL.md` which DOES need
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
- [ ] CLAUDE.md "Repository structure" directory listing updated
- [ ] AGENTS.md and llms.txt updated to reflect the new reference (see "Lessons
      learned" section for the documentation-drift correction)
- [ ] install.sh per-tool routing updated: ChatGPT inline routing table, Gemini
      grouped knowledge, and Cursor description must mention the new domain
- [ ] File ends with the OptimNow footer (`> *Cloud FinOps Skill by [OptimNow]...
      CC BY-SA 4.0...*`); no truncation mid-sentence or mid-table
- [ ] Plugin version bumped in `.claude-plugin/plugin.json` (minor for user-visible feature)
- [ ] Marketplace description in `.claude-plugin/marketplace.json` reflects the new
      reference file count and topic list
- [ ] SKILL.md description stays under 1024 characters
- [ ] No em dashes in any public content
- [ ] No sensitive or internal files included
- [ ] Content is practical and based on how billing actually works, not on documentation summaries
- [ ] If the file deferred or replaced is in the Roadmap section, the Roadmap section is
      updated accordingly
