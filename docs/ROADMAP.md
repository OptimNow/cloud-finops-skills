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

## In-flight (write when prerequisites land)

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
  criteria (U1-U4 below, plus U5-U8 from the audit). The
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

- **Host `cloud-finops-mcp` on Alpic - DONE (2026-08-17).** Live at
  <https://cloud-finops-skills-590a051d.alpic.live/mcp>, published in README.md,
  INSTALLATION.md and the `remotes` block of `server.json`. The decision to deploy
  remotely was taken on 2026-08-16 on distribution grounds alone (let a non-technical
  user paste a URL into claude.ai instead of installing a PyPI package), explicitly
  *not* on interactive rendering - see [`mcp-apps-lessons.md`](./mcp-apps-lessons.md) for
  the full record of what actually gates widget rendering. (The 2026-08-16 reading, that
  the Connectors Directory is the gate, was overturned on 2026-08-20: the gate is
  implementation shape, and a remote deployment is neither necessary nor sufficient for
  rendering. The distribution argument for hosting stands regardless.)

  **Verified against the deployed endpoint**, not just against a build log:
  `initialize` returns `serverInfo {"name":"cloud-finops","version":"1.29.0"}` and
  `tools/call list_references` returns `"total":33`. The reference count is the check
  that matters - see constraint 1 below for why a deployment can come up healthy with
  an empty catalogue.

  **Staleness confirmed (2026-08-27).** The same two calls still return 1.29.0 and 33
  references, so the deployment has not effectively picked up a release since
  2026-08-17 - four releases and two new references (`finops-kpis-benchmarking`,
  `finops-open-weight-vendors`) behind PyPI, and serving pre-price-purge content. This
  is what the release-checklist item "redeploy the hosted MCP (Alpic) after the tag,
  then verify by calling it" exists to prevent, and it is evidence that the redeploy
  cannot be assumed to happen on its own. Re-verify with `initialize` plus
  `list_references` after every release; expect the current version and a total of 35.

  **Staleness resolved (2026-08-29).** Redeployed after the 1.34.0 release and verified
  by calling the hosted connector: `list_references` returns 35 (including
  `finops-kpis-benchmarking` and `finops-open-weight-vendors`), and
  `get_reference(name="finops-aws", section="AWS billing hierarchy and separate
  invoices")` serves the 1.34.0 section through the section parameter shipped in
  PR #180 - so the deployment carries both of the releases it was behind on. The
  re-verify-after-every-release rule stands unchanged; this entry records one
  verified pass of it, not a reason to skip the next one. Lot C in the batch
  sequence below is no longer gated on this redeploy.

  One behavioural difference from the local run, worth knowing before writing a health
  check: **the hosted endpoint is session-based.** A bare `tools/call` returns HTTP 400
  even though `stateless_http = True` is set in the code; Alpic's ingress front-ends the
  server with its own session layer. You must `initialize` first and pass the returned
  `mcp-session-id` header on subsequent calls. Real MCP clients do this automatically;
  a hand-rolled `curl` one-liner does not.

  Four things about this repo that a deployment has to respect, all verified locally
  before the config was written:

  1. **Build from the repo root, never from `mcp_server/` in isolation.** The bundled
     `data/*.md` are gitignored, so a fresh clone has none. They are produced at build
     time by the `hatch-build-scripts` hook running `scripts/sync_references.py`, which
     resolves the repo root from `__file__` and reads `skills/cloud-finops/`. Point the
     build at `mcp_server/` alone and it will happily build a server with an empty
     catalogue - a silent failure, not a build error.
  2. **The start command must name the transport explicitly.** Alpic detects Python
     transport by looking for `mcp.run()` / `mcp.http_app()` with an explicit transport
     argument. This server routes through argparse in `__main__.py` and defaults to
     stdio, so auto-detection would get it wrong. Hence `--transport http` in
     `startCommand` rather than relying on detection.
  3. `$PORT` and `0.0.0.0` are already handled in `__main__._env_port()` and
     `run_http()`, and `stateless_http = True` is set deliberately so there is no
     session affinity to preserve across instances.
  4. The route is FastMCP's default `/mcp`. Do not move it.

  Verified 2026-08-17 on a clean tree: `uv build --wheel` runs the sync hook and produces
  a wheel carrying 33 references + 25 playbooks + the viewer HTML; `python -m
  cloud_finops_mcp --transport http` binds and answers `initialize` and `tools/list` over
  streamable HTTP.

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

- **Playbook coverage for `commitment-mismatch` - CLOSED (2026-08-21).** One playbook
  per provider shipped: `aws-expiring-commitment-no-decision` (obvious),
  `azure-unused-reservation` (obvious), `gcp-cud-mismatch` (likely). The deeper
  sizing/portfolio reasoning stays in the commitments references, which the playbooks
  link. Originally surfaced by the 2026-08-02 repository review (F9); priority
  confirmed by the 2026-08-19 field test and by probe P12 (cycle 3, 2026-08-20),
  where the model asked for account data instead of handing over a runbook.

- **Playbook backlog from the 2026-08-19 connector field test.** Four probe prompts run
  through the hosted MCP produced a coverage read worth keeping. The ordering principle it
  validated: **weight gaps by expected recoverable spend, not by category count** - a missing
  storage-tiering playbook is worth more in a typical estate than several narrow GPU
  sub-patterns. Prioritised backlog, one playbook each unless noted:
  1. **Storage tiering** - *AWS side SHIPPED 2026-08-21* as three playbooks from the
     P11 seed: `aws-s3-incomplete-multipart-uploads` (obvious),
     `aws-s3-noncurrent-version-sprawl` (likely), `aws-s3-cold-data-in-standard`
     (possible, carries the prerequisite-finding pattern - rule 3 of the seed - and
     folds rule 4, expire-don't-transition, into its Fix/Anti-pattern). Azure Blob
     access tiers and GCS storage classes remain open; port the same three-way split
     rather than one catch-all playbook.
  2. **Commitment-mismatch x3 providers** - CLOSED 2026-08-21, see the entry above.
  3. **NAT-to-gateway-endpoint substitution (AWS)** - the high-traffic end of the NAT
     distribution, which the zombie-NAT playbook deliberately scopes out: a NAT moving
     mostly S3/DynamoDB data pays a per-GB processing fee a gateway endpoint eliminates
     entirely. Larger recoverable than the idle end.
  4. **Azure idle VM + orphaned NICs / public IPs + snapshot sprawl** - the Azure set is
     four playbooks against fourteen for AWS; these three are the everyday-estate gaps.
  5. **Schedule blindness beyond compute** - databases and non-production data platforms
     (SQL pause/resume, Fabric capacity pause, warehouse auto-suspend).
  6. **Modernization beyond GPU generations** - Graviton/ARM migration, gp2-to-gp3,
     Azure v-series refresh.
  7. **Egress beyond AWS cross-AZ** - NAT-path egress, Azure/GCP equivalents, CDN bypass.
  8. **GCP depth** - BigQuery slot and storage waste, Cloud SQL idle, CUD mismatch (also
     covered by item 2).
  9. **Kubernetes beyond one playbook** (added by the 2026-08-20 probe run) - only
     gcp-idle-gke-autopilot exists. Missing: EKS/AKS equivalents, over-requested
     CPU/memory vs actual usage, idle node pools, orphaned persistent volumes.

  Product note from the same run: of the nine obvious-tier playbooks, one is Azure
  and one is GCP. If WasteLine gates auto-remediation proposals on the obvious tier,
  the non-AWS product is effectively two checks - weight new non-AWS playbooks
  towards patterns that can honestly carry the obvious tier. *Update 2026-08-21: PR
  #177 added `azure-unused-reservation` (obvious) and two AWS obvious playbooks; the
  count is now 12 obvious of 31, Azure 2, GCP 1 - the weighting rule still applies.*

- **Next content batches, sequenced (2026-08-21).** Written after PR #177 closed
  backlog items 1 (AWS side) and 2. Ordering principle unchanged: recoverable spend
  first, demand evidence (probe or issue) second, matrix zeros last. Post-#177 the
  playbook matrix is 18 AWS / 5 Azure / 4 GCP / 4 cross-cloud, and schedule-blindness,
  modernization and egress each have a single playbook.

  **Lot A - everyday-estate playbooks (next batch).** Five files, all able to carry
  the obvious tier, all high-value:
  1. `aws-nat-gateway-endpoint-substitution` (egress) - backlog item 3. Urgent because
     it is a dangling pointer: `aws-zombie-nat-gateway` explicitly scopes it out as
     "a larger finding", and probe P13 is waiting for it. CUR detection: NatGateway-Bytes
     vs S3/DynamoDB-destined traffic; gateway endpoints remove the per-GB fee entirely.
  2. `azure-idle-vm`, `azure-orphaned-public-ips-and-nics`, `azure-snapshot-sprawl` -
     backlog item 4, all Resource Graph single-signal, all obvious. Takes Azure from 5
     to 8 playbooks and from 2 to 5 obvious-tier.
  3. `aws-gp2-to-gp3` (modernization, obvious - pure gain, no risk) and, second,
     `aws-graviton-candidate` (likely) - backlog item 6.
  Then, in later batches: storage tiering ported to Azure Blob and GCS (one playbook
  per cloud: soft-delete/versions and abandoned resumable uploads as the GC rules,
  cold Hot/Standard data at `possible`); `cross-cloud-nonprod-data-platform-always-on`
  (schedule blindness beyond compute: SQL serverless auto-pause, Fabric pause,
  Snowflake auto-suspend - backlog item 5); Kubernetes `eks-aks-overrequested-resources`
  and `orphaned-persistent-volumes` (backlog item 9).

  **Lot B - references with demand evidence.**
  1. Issue #97 (Azure OpenAI PTU vs PAYG break-even) - a real user request open since
     July, and probe P23 targets the same question. Not a new file: a mechanics section
     in `finops-azure-openai.md` + `finops-genai-capacity.md` (break-even utilisation
     formula, hourly-vs-token shape, spillover switch), figures routed to the pricing
     hub. A priced *table* is the wrong container under the dated-price rule.
  2. `finops-forecasting.md` - `finops-kpis-benchmarking.md` now names forecast
     variance as the single best maturity proxy but nothing teaches forecasting
     (driver-based, commitment-aware, the 60-90 day rule at intake). Budget season
     (September-November) is the natural trigger; it was listed as "non-AI demand
     emerges" in the deferred table below.
  3. GreenOps Azure/GCP depth pass (see Depth passes below).
  4. Education & Enablement - the last true FCP gap after #177 (21/22 any-coverage).
     Low spend impact; a section inside a future practice-operations file closes the
     matrix to 22/22. Only worth doing if the 100% badge matters for positioning.
  Not now: `finops-unit-economics.md` and `finops-practice-operations.md` - the KPI
  file covers their useful parts and their Walk-to-Run engagement triggers have not
  fired.

  **Lot C - measurement: DONE 2026-08-29, and it changes the ordering rule.**

  The original wording of this item ("run the 24 never-played probes ... with Sonnet")
  was already stale when it was written: cycle 3 ran the FULL battery P01-P32 on
  2026-08-20, one day earlier. What was actually needed, and what ran, is a *regression*
  cycle - only the probes whose content shipped since c3, plus one new probe for the
  #181 invoice-unit material. Deployment was verified first by calling the connector.

  Result (c4, Sonnet 5 Medium, 4 probes): **content closes a gap only where the phrasing
  already routed.**

  - **P11** (S3 lifecycle, "how do I *detect*...") - 2 empty library calls in c3, now
    GROUNDED: `find_playbooks` then `get_playbook(aws-s3-cold-data-in-standard)`, and the
    answer carries the prerequisite-first rule, expire-don't-transition, the 128 KiB
    threshold and weight-by-bytes. **PR #177 closed the trap.**
  - **P12** ("which of *my* RIs are about to expire...") and **P13** ("*my* NAT processes
    10TB/month...") - **unchanged, zero library calls each**, even though
    `aws-expiring-commitment-no-decision` (#177) and
    `aws-nat-gateway-endpoint-substitution` (#182) are both live on Alpic and the
    connector toggle was verified ON. This is routing, not availability.
  - **P33** (new, the real client question behind #181: "their AWS contact suggested Cost
    Categories - is that right?") - GROUNDED via the claude.ai skill surface; the
    anti-confusion framing holds ("they change how spend is sliced in reports, not how
    AWS bills") and anchor sentence 3 comes back near-verbatim.

  **Consequence for how this backlog is ordered.** The rule "every IMPROVISED verdict
  becomes a content item with demand evidence" is now known to be wrong for one class:
  account-data phrasing ("which of MY x") and symptom phrasing ("my NAT does X") do not
  route, so shipping their playbook does not convert them. Those two probes are demand
  evidence for **routing work** - tool descriptions, SKILL.md phrasing - not for more
  playbooks. Only discovery- and advisory-phrased gaps are content items. The remaining
  c3 IMPROVISED probes (P06, P23 provider-billing-news; P25 finops-itam orphaned) were
  not re-run: nothing shipped for them, so their verdict stands unchanged.

  Standing incident, third cycle running: every connector call renders "Unable to reach
  AI Cloud FinOps Skill & MCP" while the data arrives intact, and a tool-approval gate
  now appears per call. Full per-probe notes in `pipeline/coverage-probes.md`.

  Two composition notes from the same test, recorded as positioning decisions rather than
  defects until decided otherwise: (a) the library reads AI-workload-heavy (8 of 14 AWS
  playbooks are GPU/SageMaker; ~43% of engineering-primary Optimize references are
  AI-specific) - that is the OptimNow positioning, but new playbooks should rebalance
  towards everyday-estate patterns; (b) users read the skill description's topic list as a
  playbook promise (e.g. "Azure OpenAI PTUs" is covered by references, not by a playbook) -
  a wording nuance to keep in mind when the description is next touched.

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
than re-litigating priority. Tracking issue: `OptimNow/cloud-finops-skills#55`.

| Proposed file | Priority | Trigger to revisit | Why deferred |
|---|---|---|---|
| `finops-tools-services.md` | P2 | Next engagement raises a vendor-evaluation question | OptimNow has implicit views (FinOps Toolkit, MCP, OpenCost) but no formal write-up; better to write against a real client question than a generic checklist |
| `finops-practice-operations.md` | P2 | Next Walk to Run client engagement starts | `optimnow-methodology.md` covers the consultancy-positioning lens; this would be the operator-grade discipline below it (three-cadence operating model, per-Capability scorecard, allied-discipline integration charter) |
| `finops-forecasting.md` | P2 | Non-AI forecasting demand emerges | `finops-ai-value-management.md` covers AI forecasting; non-AI demand has not surfaced in current engagements |
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
- `skills/cloud-finops/playbooks/` directory (PRs #64, #66, #67, #83) - RAG-friendly
  named-pattern playbooks (`<scope>-<pattern>.md`, ~2-3KB each,
  Problem/Symptoms/Detection/Fix/Anti-pattern/See also format) covering AWS (incl. SageMaker + GPU), Azure, GCP, and cross-cloud waste patterns.
  Routed from SKILL.md and POWER.md "named waste pattern" rows
- `scripts/fcp-coverage.sh` + top-level `fcp-coverage.md` (PR #64) - bash matrix that
  parses FCP frontmatter from every reference and renders a 22-capability coverage table.
  Run on each PR; `[~]` secondary-only cells distinguish dispersed coverage from true gaps

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
