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
├── llms.txt               <- llmstxt.org-format index (linked sections; CI-gated)
├── DEPENDENCIES.md        <- Cross-repo dependency map for the five OptimNow repos,
│                             plus the "if I change X, what else needs review" table
├── install.sh             <- One-liner installer script
├── server.json            <- MCP Registry manifest (carries the version TWICE)
├── alpic.json             <- Alpic build contract for the hosted MCP deployment
├── .claude-plugin/        <- plugin.json + marketplace.json (versions bump together)
├── .github/workflows/     <- ci, marketplace-version-check, auto-tag-on-plugin-bump,
│                             publish-mcp, publish-registry, mcp-install-smoke,
│                             release
├── assets/                <- Installation-guide screenshots (embedded in
│                             INSTALLATION.md), the GitHub social preview, and
│                             the generated playbook-coverage.svg and
│                             fcp-coverage.svg heat maps (embedded in
│                             README.md; both CI-gated)
├── docs/
│   └── ROADMAP.md         <- Deliberately-deferred work + trigger to revisit
│                             (split out of CLAUDE.md, Aug 2026)
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
│                             resources: playbook-viewer, playbook-explorer,
│                             reference-browser - shared JS in ui/_*.js is
│                             inlined at import by server._load_ui)
├── scripts/               <- `fcp-coverage.sh` and `playbook-coverage.sh`
│                             (parse frontmatter, emit the two coverage
│                             matrices; their --check modes diff the
│                             committed files in CI), the heat-map renderers
│                             `render-coverage-heatmap.py` and
│                             `render-fcp-heatmap.py` (emit the README SVGs,
│                             --check gated in CI) plus the guards:
│                             check-artefact-size, check-docs-drift,
│                             check-llms-txt, check-skill-description (run by
│                             the `CI` workflow) and check-marketplace-version
│                             (its own `marketplace-version-check` workflow)
├── fcp-coverage.md        <- Generated FCP coverage matrix (22 caps; CI-gated)
├── playbook-coverage.md   <- Generated waste-playbook matrix (category x
│                             scope, gaps listed; CI-gated)
├── .gitattributes         <- Force LF on *.sh for Windows checkouts
└── pipeline/              <- Content update pipeline (gitignored, private)
    ├── run_scan.py        <- Fortnightly scan entry point
    ├── run_apply.py.FROZEN <- Review and apply entry point, frozen since the
    │                          May 2026 truncation incident (see docs/ROADMAP.md P1)
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
doctrine for running a batch - pre-flight checks, per-item review,
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

**Update (2026-08-19): the gate now has an observable mechanism.** Claude
Desktop's `mcp-ext-apps-host` attempts to set up MCP Apps for custom
connectors and validates a `ui.domain` on the widget resource:
sha256(connector URL exactly as the host displays it in its error log -
for a root-entered connector that is the ROOT url WITH its trailing
slash)[:32] + `.claudemcpcontent.com`. (Corrected 2026-08-20: the
original "no trailing slash" note here was wrong - hashing `/mcp` while
the host saw `https://.../` reproduced the failure on this repo's own
connector; Skybridge, which passes, hashes https://<host><pathname> per
request.) A wrong or missing value logs
`ui.domain validation failed for connector "<url>"` in the Desktop logs
(observed live for ai-pricing-hub on 2026-08-19, including the fix-it
one-liner the error prints). So the 2026-08-16 claim that a custom
connector "gets the text fallback no matter how correct it is" is no
longer the whole story - but whether a correct `ui.domain` is *sufficient*
for rendering is still unproven for this repo's connector: the render test
needs the connector added to the account and the Alpic deployment current.
The real render attempt happened on 2026-08-19 (four prompts through the
connector on claude.ai): tools executed, the host reserved the widget
iframe, the frame stayed blank - the predicted failure. `ui.domain` was
therefore applied on 2026-08-20: the three widget resources declare
`meta={"ui": {"domain": ...}}` where the value is DERIVED in server.py
from `CANONICAL_CONNECTOR_URL` (sha256 of the URL exactly as users enter
it, no trailing slash, first 32 hex chars + `.claudemcpcontent.com`) and
pinned by tests. When touching this, never hash an internal path instead
of the public URL - that wrong-input variant is exactly what broke
ai-pricing-hub-mcp. Correction to an earlier note in this entry:
ai-pricing-hub was NOT fixed on 2026-08-19 - no such fix exists in that
repo and its failures were still logging at 17:30 that day; it needs the
same change as this one.

**Update (2026-08-20): rendering for custom connectors IS possible - the
gate is implementation shape, not the Directory.** Two facts landed the
same day. First, a Desktop render test on this repo's connector called
`find_playbooks` (visible as `tool_approval_gate` log entries, MCP Apps
runtime activating right after), logged NO `ui.domain` error - and still
showed no widget. Second, and decisive: the Skybridge-built companions
(`ai-pricing-hub-mcp`, `ai-roi-calculator-mcp`) DO render their widgets
in Claude as plain custom connectors (user-confirmed with a screenshot of
`compare-models-side-by-side` rendering in the chat). So the 2026-08-16
"Directory review is the gate" conclusion is wrong for widgets. What
Skybridge does that this server does not, in likely order of relevance:
(a) registers each widget TWICE - an apps-sdk variant (mime
`text/html+skybridge`, `openai/*` meta, tool `openai/outputTemplate`
pointing at it) alongside the spec variant (`text/html;profile=mcp-app`,
`ui.resourceUri`); (b) computes `ui.domain` per request from the URL
Claude actually calls (sha256 of host+path), instead of a static
precomputed hash; (c) declares a `ui.csp` block ({resourceDomains,
connectDomains}) in the resource-read `_meta`. (a) and (c) were mirrored
in server.py the same day (PR #174), which moved the failure forward to a
ui.domain mismatch on the ROOT connector URL, fixed by hashing the
root-with-slash form (PR #175). Keep `ui.domain`; it stays required.

### A packaged artefact cannot own volatile data (2026-08-17)

Shipped across twelve PRs (#141 to #153, released as 1.30.0). The change is small to
describe and it removes a whole class of defect.

**The defect.** Price figures sat in the reference files. Those files ship frozen inside
a PyPI package, a Claude Code plugin, an Alpic deployment and a dozen tool integrations,
and nothing in that chain corrects a number after it is written. The June 2025 AWS GPU
price cuts stayed wrong for 14 months. The pipeline could not catch it either: the scan
detects news from sources, it cannot detect silent staleness in a figure already sitting
in a file.

**The fix.** Split mechanics from figures. Ratios, multipliers, commitment term structure
and the shape of a break-even calculation are durable, and they are what a practitioner
actually reasons with - so they stay. Absolute prices route to a live source (OptimToken),
and where a worked example genuinely needs a number, it carries an inline as-of date.
After the purge, `grep -E '\$[0-9.]+\s*(/|per )\s*(1M|MTok)'` over `references/` returns
nothing.

Two things this bought beyond correctness: the answer now carries its own date and source,
which is what makes it usable in a client deliverable; and the pipeline's rotating
AI-pricing re-verification pass shrank from a hunt across every reference to a date check
on a short list.

**The alternative that was rejected**, because it will be proposed again: adding
OptimToken to the pipeline sources so the applier refreshes figures on a cron. That puts
an LLM back in the write loop on 1,500-line files - the April-May 2026 truncation failure
mode - to solve a synchronisation problem the API already solves in real time. The hub is
queried, never copied.

**The generalisation, which is the part worth keeping.** Duplicated computation is this
family's recurring failure, now observed twice independently: OptimToken drifted between
its website and its MCP, and the ROI calculator drifted between its web app and its MCP
far enough to return a 7-point different ROI for the same preset. One person cannot keep
two implementations of the same computation in sync without automation. **Route, do not
copy** - and that is why live pricing tools inside `cloud-finops-mcp` were declined even
though the idea sounds tidier (see the entry in [`docs/ROADMAP.md`](docs/ROADMAP.md)).

**Verification discipline paid off three times in one day.** Each of these was invisible
from reading the source and only appeared by calling the thing:

- The pricing hub's three MCP tools failed in Claude Code on a JSON Schema dialect
  mismatch. They worked in MCPJam, so the defect was host-specific and no test caught it.
- `compare-compute-pricing` was silently serving a dated snapshot instead of live data.
  It was detectable only because the server had been asked to report `provenance`.
- The hosted MCP endpoint is session-based despite `stateless_http = True` in the code,
  because Alpic's ingress front-ends it. A health check written from the source alone
  would have shipped broken.

The rule generalises the 2026-08-16 MCP Apps lesson: **do not document, route to, or
monitor a remote surface you have not called.**

**Small but sharp.** `git grep "Cloud FinOps Skill"` reported 40 files, which made the
rename look expensive. 36 of them were the CC BY-SA attribution footer, which must not
change - it is the string third-party reusers carry. The real surface was 8 occurrences
in 5 files. Count the *kind* of hit before estimating effort from a grep total.

---

## Roadmap

Moved to [`docs/ROADMAP.md`](docs/ROADMAP.md): deliberately-deferred work, the reasoning
behind each deferral, and the trigger that should reopen it. Read it before starting a new
reference file, proposing a new capability, or reviving an idea that looks obviously good -
several of them were already considered and declined for recorded reasons.

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
     bumps all four together - `plugin.json` version (minor for user-visible
     features), `marketplace.json` `metadata.version` (must match plugin.json;
     CI-gated by `scripts/check-marketplace-version.sh`),
     `mcp_server/pyproject.toml` version, and **`server.json`, which carries the
     version twice** - the top-level `version` and `packages[0].version`, the
     PyPI package version the MCP Registry advertises. `server.json` used to be
     ungated and was therefore the file that drifted (it was missing from this
     checklist until the 1.30.0 release); since August 2026 the `verify-package`
     job in `auto-tag-on-plugin-bump.yml` fails the release if either of its two
     version fields disagrees with `plugin.json`, before any tag is pushed.
     Update the marketplace plugin
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

`fcp_phases` is deliberately independent of `fcp_domain`: a file whose primary
domain is Understand Usage & Cost (e.g. finops-kubernetes) legitimately carries
the Optimize phase when it also serves optimisation work. Audited and confirmed
intentional on 2026-08-20 (kubernetes, oci, for-ai) - do not "fix" this apparent
mismatch.

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
- **Write mechanics, not price figures.** A reference file is the wrong container for
  a volatile number: it ships frozen inside a PyPI package and a dozen tool
  integrations, so an absolute price goes stale there within weeks and nothing in the
  distribution chain corrects it (the June 2025 AWS GPU price cuts sat uncorrected for
  14 months for exactly this reason). Ratios and mechanics are durable and belong here:
  the batch discount, the cache-read multiplier, commitment term structure, the shape of
  a break-even calculation. Absolute $/1M-token and $/hour figures belong in the AI
  Pricing Hub (<https://optimtoken.optimnow.io>), which is queried live. Where a worked
  example genuinely needs a number to be legible, keep one, mark it illustrative, and
  date it inline. The reader-facing version of this rule is the "Price figures" section
  in SKILL.md and POWER.md.

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

So the check is one-directional. Before merging, if the PR touches any of these:

| If the PR touches | Verify against | Where it lives here |
|---|---|---|
| An MCP tool name, parameter, or output field of the pricing hub | `ai-pricing-hub-mcp` | INSTALLATION.md companion section; SKILL.md / POWER.md "Price figures" |
| The `provenance` contract (tier semantics, `upstreamTimestamp` / `eloAsOf`, the stale notice) | `ai-pricing-hub-mcp` | "Price figures" rule 5, in SKILL.md, POWER.md and the INSTALLATION.md response contract |
| An MCP tool name or parameter of the ROI calculator | `ai-roi-calculator-mcp` | INSTALLATION.md companion section |
| A value method, an input's meaning, or a documented trap | `ai-roi-calculator` METHODOLOGY.md | `references/finops-ai-value-management.md` |
| Any `*.alpic.live` or `optimtoken.optimnow.io` URL | the owning repo | README.md, INSTALLATION.md, server.json |

Two standing rules that follow from the map:

- **Never copy a formula or a rate into this repo.** Route to the tool that owns it.
  Duplicated computation is the recurring failure mode across this family: OptimToken
  drifted between its site and its MCP, and the ROI calculator drifted between its web
  app and its MCP far enough to return a 7-point different ROI for the same preset.
- **Price figures are not maintained here at all.** See the Content rules "Write
  mechanics, not price figures" entry.

---

## Pull request checklist

- [ ] New reference file follows the `finops-{domain}.md` naming convention
- [ ] YAML FCP frontmatter included on the new file (see "Reference-file frontmatter")
- [ ] Routing table updated in both SKILL.md and POWER.md
- [ ] README directory listing and "What this skill covers" section updated
- [ ] CLAUDE.md "Repository structure" directory listing updated (CI-gated by
      `scripts/check-docs-drift.sh` - a reference missing from the tree, or a
      tree entry with no file behind it, fails the `CI` workflow. The same
      script also gates the playbook catalogue in `playbooks/README.md`)
- [ ] AGENTS.md and llms.txt updated to reflect the new reference (the llms.txt
      References section is CI-gated by `scripts/check-llms-txt.sh` - a missing
      or stale entry fails the `CI` workflow, so this can't drift silently).
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
      CC BY-SA footer), add it to that README's catalogue table (CI-gated by
      `scripts/check-docs-drift.sh`), regenerate `playbook-coverage.md`
      and the README heat map (`./scripts/playbook-coverage.sh` and
      `python scripts/render-coverage-heatmap.py` - both CI-gated, so the
      coverage change shows in the PR diff), and update the named-
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
- [ ] **Release PR only: bump all four versions together** - `plugin.json`
      (minor for user-visible features), `marketplace.json` `metadata.version`
      (must match; CI-gated by `scripts/check-marketplace-version.sh` via the
      `marketplace version in sync` workflow), `mcp_server/pyproject.toml`, and
      `server.json` (two fields: top-level `version` and `packages[0].version`).
      `marketplace.json` is gated by `scripts/check-marketplace-version.sh` and
      `server.json` by the `verify-package` job in `auto-tag-on-plugin-bump.yml`;
      `pyproject.toml` is auto-pinned to `plugin.json` at build time, so bump it
      for tidiness rather than correctness.
- [ ] **Release PR only: no manual MCP Registry step.** Publishing `server.json`
      to the registry is automated by the `publish-registry` job in
      `auto-tag-on-plugin-bump.yml` (GitHub OIDC, no secret). It runs after the
      PyPI publish and waits for the version to be visible on PyPI, because the
      registry validates the package before accepting the entry. Verify it landed
      at <https://registry.modelcontextprotocol.io/v0/servers?search=finops>.
- [ ] **Release PR only: redeploy the hosted MCP (Alpic) after the tag, then verify
      by calling it.** The Alpic deployment does not reliably pick up releases on its
      own - the 2026-08-19 audit found it serving 1.29.0 content (pre price-purge)
      while PyPI was already at 1.31.0. After the PyPI publish, trigger a redeploy on
      Alpic, then call the hosted endpoint
      (`https://cloud-finops-skills-590a051d.alpic.live/mcp`) and confirm it serves
      the released content: the server's startup log names the bundle stamp
      (`data/content_version.txt`, version + sync date, written by
      `sync_references.py` since 1.32), or compare a `list_references` line count
      against the tag. Do not tick this from the source alone - the audit found the
      staleness only by calling the surface.
- [ ] Marketplace description in `.claude-plugin/marketplace.json` reflects the new
      topic list (can ride the release PR). It carries no reference count by design -
      see the no-hardcoded-counts rule above.
- [ ] SKILL.md description stays under 1024 characters (CI-gated by
      `scripts/check-skill-description.sh`, which also warns above 950 so the
      ceiling is visible before it is hit)
- [ ] **Cross-repo impact checked.** If the PR quotes another OptimNow repo's tool
      names, parameters, endpoint URLs, `provenance` fields, or ROI methodology, it was
      verified against that repo. See "Cross-repo dependencies" above and
      [`DEPENDENCIES.md`](DEPENDENCIES.md). Nothing in CI catches this class of drift
- [ ] **MCP tool surface changed? Move all three copies together.** Renaming a tool,
      changing a parameter, or adding one touches `README.md` (the canonical
      description of what the six tools do), `mcp_server/README.md` (the PyPI page,
      which must stay self-contained), and the `instructions` string in
      `mcp_server/src/cloud_finops_mcp/server.py` (the contract the agent reads at
      runtime). INSTALLATION.md deliberately no longer describes the tools - it links
      to the README and documents the wiring - so it is not a fourth copy. Nothing in
      CI catches this either
- [ ] No em dashes in any public content
- [ ] No sensitive or internal files included
- [ ] Content is practical and based on how billing actually works, not on documentation summaries
- [ ] If the file deferred or replaced is listed in [`docs/ROADMAP.md`](docs/ROADMAP.md),
      that entry is updated accordingly
