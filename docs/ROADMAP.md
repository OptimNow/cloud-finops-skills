# Roadmap

Work that is intentionally not shipped, and the trigger to revisit it. This is the durable
record of "what's deliberately out of scope right now and why" - distinct from GitHub
issues, which track in-flight work.

Split out of `CLAUDE.md` in August 2026. `CLAUDE.md` is read in full at the start of every
agent session on this repo, and this section was roughly a third of it while being needed
only when scoping new work. The `Lessons learned` section deliberately stayed behind: it is
what stops an agent repeating the April-May 2026 truncation incident, so it has to be read
by default.

This file is the public subset of the roadmap: the entries that concern contributors and
users of the skill. Internal product and positioning work is tracked in a private
maintainer file.

## Fortnightly operating rhythm (adopted 2026-10-01)

Since 2026-10-17 the source scan runs weekly, every Saturday (see the "Content
update pipeline" section of `CLAUDE.md`); its digest is triaged within the week.
The lots below stay on the 1st and the 15th. From October 2026 each half-month also carries one *lot*,
alternating in shape so that no single kind of debt accumulates. Every lot
assumes hand-written content from primary sources: the applier stays frozen,
and the September 2026 batch showed that correcting its output costs more than
writing the item by hand (nine applied items, nine corrections).

The constraint this rhythm is built around comes from probe cycles 4 to 7
(the routing record below): **content closes a gap only where the phrasing
already routes.** So roughly a third of the budget goes to measurement and
routing rather than new files, and a lot that does not convert its probe
becomes a routing item, not a reason to write more.

**Run on the 1st (scan plus content):**

1. Triage the scan output; hand-write the accepted items from the provider's
   primary page.
2. Ship one content lot from the ranked list below: two to three playbooks, or
   one reference section.
3. Regenerate the two coverage matrices and the heat maps, update the
   `install.sh` named-pattern routing, open the PR.
4. Before merge, fan out one read-only agent per applied claim to verify it
   against the primary source (the step that caught all nine September
   corrections).

**Run on the 15th (scan plus quality):**

1. Triage the scan output as above.
2. Rotating re-verification: one domain cluster's dated figures and mechanics
   claims against provider docs (rotation table in the maintainer-local
   `pipeline/MONTHLY_WORKFLOW.md`). This moves the pass from the 1st, where
   it sat before October 2026, to the 15th, so that each half-month carries
   one heavy step; the "Content update pipeline" section of `CLAUDE.md` says
   the same, and the maintainer-local doctrine needs the same edit.
3. One probe cycle: the four controls (P11, P12, P13, P31) plus one probe
   targeting the lot shipped on the 1st, on both surfaces, with the
   visible-evidence discipline. Record the verdicts in
   `pipeline/coverage-probes.md`.
4. Hygiene pass: footers, as-of dates older than two quarters, the price-figure
   grep as a review prompt, and the cross-repo table in `CLAUDE.md` for any
   pricing-hub or ROI-calculator claim touched since the last pass.

**Once a quarter, on a 1st:** a release PR after the content lots, a Fly
redeploy verified by calling the endpoint, and a re-read of this file to
re-rank the list below against what engagements actually asked.

### Ranked content list (recoverable spend first, demand evidence second, matrix zeros last)

Written against the 2026-09-30 state: 35 references, 37 playbooks (AWS 21,
Azure 8, GCP 4, cross-cloud 4), 13 of 22 FCP capabilities with a primary owner.
State at 2026-10-13: 36 references, 41 playbooks (AWS 21, Azure 10, GCP 6,
cross-cloud 4), still 13 of 22 with a primary owner.
State at 2026-10-16: 37 references, 42 playbooks (AWS 22, Azure 10, GCP 6,
cross-cloud 4), 14 of 22 with a primary owner (Forecasting moved to [x] with
`finops-forecasting.md`).

1. **Storage tiering for Azure Blob and GCS - SHIPPED 2026-10-01** (lot of
   the 1st). Four playbooks porting the AWS split:
   `azure-blob-version-and-soft-delete-sprawl` (likely),
   `azure-blob-cold-data-in-hot` (possible),
   `gcp-gcs-soft-delete-and-version-sprawl` (likely),
   `gcp-gcs-cold-data-in-standard` (possible). Probe for the 15th: a
   detect-phrased question on GCS soft delete (the default-on trap is the
   one practitioners have not internalised).
2. **Kubernetes over-requested resources and orphaned persistent volumes.**
   Cross-cloud playbooks with per-provider detection queries. The largest
   waste class with one runbook (`gcp-idle-gke-autopilot`).
3. **Schedule blindness beyond compute.** Non-production data platforms always
   on: SQL serverless auto-pause, Fabric capacity pause, Snowflake
   auto-suspend. One cross-cloud playbook plus per-provider variants closes a
   whole zero row of the matrix.
4. **Issue #97 as a mechanics section**, not a table, in
   `finops-azure-openai.md` and `finops-genai-capacity.md`: the break-even
   utilisation formula, the hourly-vs-token shape and the spillover switch,
   with figures routed to the pricing hub. The only open user request, waiting
   since June.
5. **`finops-forecasting.md` - SHIPPED 2026-10-16.** Budget season was the
   trigger named in the deferred table. Forecasting now has a primary owner in
   the FCP matrix. The first version carries the Foundation's three forecast
   measures and the variance bands, the trend-to-driver method ladder, the
   driver-led re-forecast cadence and AI forecast scenarios. Next depth when an
   engagement asks: worked driver models per workload type, and forecast
   collection from owners at Run.
6. **`finops-gcp-patterns.md` split.** The GCP file carries 12 enumerated
   patterns inline against a 1,495-line AWS catalogue; the split mirrors the
   AWS and Azure structure and is a token-efficiency fix as much as a
   coverage one. Priority depends on how much GCP engagements see.

Depth items that ride a quality lot when a content lot is light: OCI (182
lines, six patterns: deepen or label it a foundations file in the routing
table), the GreenOps Azure and GCP pass below, and any further split of
`finops-azure.md` (1,838 lines, above the 1,500-line structural-edit
threshold) before adding to it.

Deliberately not on the list: the last FCP cell (Education & Enablement) and
the modernization and egress zero cells for Azure and GCP, which score well
on the matrices and poorly on recoverable spend; unfreezing the applier; and
non-cloud domains such as the IoT and unmanned-retail request in issue #200.

## Refresh pipeline (P1)

- **P1 - Audit, harden, stabilise, and publish the refresh pipeline.** The pipeline
  in `pipeline/` is currently frozen (`run_apply.py.FROZEN`) since the May 2026
  truncation incident (8 reference files truncated across two runs - see the
  `Lessons learned` section of `CLAUDE.md` for the forensic). Hard guard rails are in
  the applier (`validate_post_apply` with deletion threshold + footer presence +
  double-HR check; `apply_with_guard_rails` with snapshot + rollback; run-level
  fail-safe at 2 failures), and 9 unit tests pass against synthesised failure
  modes. What is missing is end-to-end validation, hardening of the rest of the
  pipeline, and a decision on public release.

  **Phase 1 (Audit) landed:** `pipeline/pipeline-audit-2026-05.md` (maintainer-local;
  `pipeline/` is gitignored, so this is deliberately not a link - it would 404 in
  every public clone)
  covers module-by-module contracts, LLM-call inventory, destructive-actions
  inventory, guard-rails verification (9/9 tests pass; full suite 43/43 green),
  implicit assumptions, gap analysis vs Phase-2 targets, recommended
  remediation order (9 items, 5 blocking unfreeze), and proposed unfreeze
  criteria (U1-U4 below, plus U5-U8 from the audit). Phase 2 (Harden) is partly
  done: the real-API smoke test (`pipeline/smoke_test.py`), the per-run report
  (`pipeline/state/runs/<id>/report.json`) and preview-mode guard rails landed on
  2026-05-15, and since September 2026 the scan records `fetch_failure` when every
  source fails instead of reporting success. The applier stays frozen
  (`run_apply.py.FROZEN`).

  Four phases:

  1. **Audit (week 1).** Read every module - `scanner/` (fetch + classify),
     `proposer/` (CHANGES.md report builder), `applier/` (file rewrite, now
     guard-railed), `alerter/` (Gmail draft builder), `state/`. Document each
     module's contract (inputs, outputs, side effects, failure modes), the
     LLM prompts in use, and any place where the pipeline takes a destructive
     action. Identify implicit assumptions and any other module besides
     `applier/` that can write to `plugins/cloud-finops/skills/cloud-finops/references/` or `plugins/cloud-finops/skills/cloud-finops/playbooks/`
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
     the 2026-05-15 lessons in `CLAUDE.md`). Do not resurrect it. Every
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
     `Lessons learned` section of `CLAUDE.md` so it is auditable.
  4. **Publish (week 3-4, requires separate strategic decision).** The
     pipeline is currently gitignored as "private until public release"
     (per the `## Content update pipeline` section of `CLAUDE.md`). The
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
  section of `CLAUDE.md` and should produce a follow-up Lessons learned entry
  describing the un-freeze evidence.

## Standing decisions

- **Live pricing tools inside `cloud-finops-mcp`: will not do (decided 2026-08-17).**
  The idea was to add `get_llm_price` / `get_compute_price` to this server, fetching the
  OptimToken API, so a user installs one server instead of two. Rejected, and the record
  matters because the idea is superficially attractive and will come back.

  The benefit turned out to be nearly nil. Both servers are *hosted*: the user pastes a
  URL, they do not install anything. "One install instead of two" collapses into "one URL
  instead of two", which is not a friction worth engineering for.

  The cost is duplication of a computation, and this organisation has already paid it
  twice. The pricing hub drifted between its website and its MCP (the MCP held a static
  snapshot while the site resolved AWS live). The AI ROI Calculator drifted between its
  web app and its MCP far enough to return a 7-point different ROI for the same preset,
  and now carries a generated-and-CI-checked sync to stop it happening again. A third
  implementation of price retrieval invites the third occurrence.

  There is also a failure-domain argument. On 2026-08-17 `compare-compute-pricing` was
  serving degraded tier-2 data while the LLM tools were fine; because pricing lives in
  its own service, that fault stayed inside pricing answers. Folded into this server, the
  same fault would sit inside knowledge retrieval.

  **The architecture to keep instead:** separate hosted MCP servers, each owning one
  domain, all reading OptimToken as the single price source, with the skill routing
  between them. Revisit only if that composition proves to be real friction for users -
  not because one endpoint feels tidier than two.

## Routing record (probe cycles 4 to 7)

Probe cycles 4 to 7 (August 2026) measured how the same library grounds answers
through the hosted connector and through the skill loaded on claude.ai. The durable
rules are in the "Skills inject, MCP tools decide" lesson in `CLAUDE.md`; per-probe
notes are in the maintainer-local `pipeline/coverage-probes.md`; the cycle-by-cycle
narrative is in this file's git history (before October 2026). Baselines to compare
future runs against:

| Probe | Connector (best, cycles 4-6) | Skill alone (cycle 7) |
|---|---|---|
| P11 detect phrasing | GROUNDED | GROUNDED via skill |
| P13 symptom | GROUNDED only after two routing iterations | GROUNDED first try |
| P31 naive symptom | never converted | GROUNDED first try, playbook verbatim |
| P12 account data | never | never - no surface triggers |

P12 ("which of my RIs...") is closed as structural: no surface picks up account-data
phrasing, and the reachable ceiling is the model offering to check the library.

## Planned distribution

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
  expose a "publish new version" endpoint for Custom GPTs). Cadence target: a monthly
  refresh, after the content lot of the 1st.

- **Public Gemini Gem for Gemini users.** Same shape as the ChatGPT GPT. Build
  steps: (1) run `./install.sh --tool gemini` to produce the 10 grouped knowledge
  files; (2) at `gemini.google.com/gems/`, create a new Gem, paste `instructions.md`,
  upload the 10 grouped files; (3) set the visibility, capture the public Gem URL and
  replace the placeholder in `README.md`. Maintenance burden: same as the GPT (manual
  re-upload, no API). Trigger: ship the GPT first, see whether the install-time
  friction reduction matters, then mirror to Gemini.

## Depth passes (extend existing files when bandwidth allows)

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

## Deferred reference files

These files were identified in the white-space analysis (May 2026) and explicitly deferred,
with the rationale captured here so future work picks them up at the right moment rather
than re-litigating priority. Tracking issue: `OptimNow/cloud-finops-skills#55` (closed;
this table is now the record).

| Proposed file | Priority | Trigger to revisit | Why deferred |
|---|---|---|---|
| `finops-tools-services.md` | P2 | Next engagement raises a vendor-evaluation question | OptimNow has implicit views (FinOps Toolkit, MCP, OpenCost) but no formal write-up; better to write against a real client question than a generic checklist |
| `finops-practice-operations.md` | P2 | Next Walk to Run client engagement starts | `optimnow-methodology.md` covers the consultancy-positioning lens; this would be the operator-grade discipline below it (three-cadence operating model, per-Capability scorecard, allied-discipline integration charter) |
| `finops-forecasting.md` | **Shipped 2026-10-16** | (closed) | Shipped on the budget-season trigger. Built from the Foundation's Forecasting, Budgeting and Planning & Estimating capability pages and two FinOps X 2026 practitioner talks; AI-specific budgeting stays in `finops-ai-value-management.md` |
| `finops-unit-economics.md` | P2 | Non-AI unit-economics demand emerges | Same reasoning as forecasting; AI-side covered by AI value management and finops-for-ai files |
| `finops-education-enablement.md` | P2 | Demand emerges; consider folding into practice-operations | Smaller scope than the other P2 files; could double as a section in practice-operations |
| `finops-benchmarking.md` | **Shipped 2026-08-21** | (closed) | Shipped as `finops-kpis-benchmarking.md` (primary capability: KPIs & Benchmarking), reopened by maintainer decision 2026-08-20. The data-quality caveats that justified the deferral became the file's benchmarking section |
| `finops-cost-warehouse.md` | P3 | Engagement requires it (e.g. Snowflake-FinOps integration) | Heavy lift, specialist content (FOCUS conformed-dim modelling, dbt + semantic layer, CUR2 / Azure Cost Mgmt / BigQuery loading patterns, late-binding analytics) |
| `finops-executive-strategy-alignment.md` | **Covered as secondary (2026-08-21)** | Split into its own file only if the executive content in `finops-kpis-benchmarking.md` outgrows a section | Maintainer reopened the capability on 2026-08-20. It now lives as the "executive conversation" treatment inside `finops-kpis-benchmarking.md` (declared in `fcp_capabilities_secondary`, so the FCP matrix shows `[~]` rather than a gap). The original concern stands: a standalone executive-strategy file risks positioning prose, so the practitioner-grade version rides the KPI file where the numbers live. |

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

**Note on Governance, Policy & Risk**: no primary owner, and no deferral was
recorded for it until now. It is covered as secondary in `finops-agentic.md` and
`finops-tagging.md`. The provider files carry policy mechanics without declaring
the capability: Azure Policy patterns and budgets in `finops-azure.md`, the spend
limits and guardrail SCPs in `finops-aws.md`. A cheap first step is to declare it
as secondary in those provider files. Trigger for a primary owner: an engagement
that asks for a cross-provider guardrail or policy-as-code design.

When picking up a deferred item: read the rationale above and confirm the trigger is real
before starting the file.

## Closed gaps (May 2026 batch)

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
- `plugins/cloud-finops/skills/cloud-finops/playbooks/` directory (PRs #64, #66, #67, #83) - RAG-friendly
  named-pattern playbooks (`<scope>-<pattern>.md`, ~2-3KB each,
  Problem/Symptoms/Detection/Fix/Anti-pattern/See also format) covering AWS (incl. SageMaker + GPU), Azure, GCP, and cross-cloud waste patterns.
  Routed from SKILL.md and POWER.md "named waste pattern" rows
- `scripts/fcp-coverage.sh` + top-level `fcp-coverage.md` (PR #64) - bash matrix that
  parses FCP frontmatter from every reference and renders a 22-capability coverage table.
  Run on each PR; `[~]` secondary-only cells distinguish dispersed coverage from true gaps

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
