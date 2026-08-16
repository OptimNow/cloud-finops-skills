---
name: finops-ai-dev-tools
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Allocation", "Licensing & SaaS"]
fcp_phases: ["Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Procurement", "Finance"]
fcp_maturity_entry: "Walk"
---

# FinOps for AI Coding Tools

> Cost governance for AI-assisted development tools - covering seat-based IDE assistants
> (Cursor, GitHub Copilot, Windsurf) and BYOK coding agents (Claude Code, OpenAI Codex).
> Billing models, cost drivers, attribution patterns, and optimisation levers.

---

## Why AI dev tools need a distinct FinOps approach

AI coding tools do not fit cleanly into existing cost management categories. They are not
pure SaaS (because variable token costs can exceed the subscription). They are not cloud
infrastructure (because there are no resources to tag or rightsize). They sit in between,
and neither your SaaS management playbook nor your cloud FinOps playbook fully covers them.

The adoption pattern is also distinct. A handful of developers try the tool, productivity
gains spread by word of mouth, and within months the entire engineering organisation is
using it. Spend follows the same curve, but visibility does not. Finance sees a growing
invoice with a single number. Engineering cannot explain what is behind it.

This makes AI dev tools a FinOps blind spot in most organisations - growing fast, poorly
attributed, and governed reactively if at all.

---

## Two billing architectures

The most important structural distinction in this category is who controls the API calls.
This determines what cost data you can access, what attribution is possible, and which
optimisation levers are available.

### Seat + usage (vendor-mediated)

Tools like Cursor, GitHub Copilot, and Windsurf manage the API routing. You pay the tool
vendor, not the model provider. The vendor decides which models are available, how tokens
are consumed, and what cost data to expose through dashboards or APIs.

**Consequence for FinOps:** your cost visibility is limited to what the vendor chooses to
surface. You cannot inject metadata at the request level. Attribution depends on the
vendor's admin tools, which are typically basic - raw data by developer email, no native
team grouping, no trending, no alerting.

### BYOK / API-direct

Tools like Claude Code and OpenAI Codex (in API key mode) use your own API key to call
model providers directly. You pay Anthropic or OpenAI, not the tool vendor. The tool is
a client; the billing relationship is between you and the model provider.

**Consequence for FinOps:** you have full control over the billing pipeline. You can route
requests through an API gateway (like LiteLLM), inject metadata (team, project, cost
centre) at the request level, set per-team budgets, and build custom dashboards. But you
also have no vendor-side cost dashboard unless you build or buy one.

### Architecture comparison

| Dimension | Seat + usage (vendor-mediated) | BYOK / API-direct |
|---|---|---|
| Examples | Cursor, Copilot, Windsurf | Claude Code (API key mode), Codex CLI (API key mode) |
| Who you pay | Tool vendor | Model provider (Anthropic, OpenAI) |
| Billing model | Subscription + token overage | Direct API token consumption |
| Cost visibility | Vendor dashboard / Admin API | API provider billing + custom tooling |
| Attribution control | Limited to vendor-exposed fields | Full (proxy, metadata injection, virtual keys) |
| Team-level allocation | Manual rollup from developer emails | Native via API gateway team tags |
| Budget enforcement | Vendor plan caps (if available) | Per-key or per-team budget caps at the gateway |

---

## Cursor (primary deep-dive)

Cursor is the dominant AI coding assistant by adoption. Understanding its cost mechanics
in detail provides a template for evaluating any seat + usage tool.

### Pricing model

Cursor has two cost layers: a fixed subscription and variable usage-based token charges.

| Plan | Seat cost | Included usage | Overage billing |
|---|---|---|---|
| Hobby (free) | $0 | Limited requests and completions | Not available |
| Pro | $20/month | $20/month usage pool | Per token at model rates |
| Pro+ | Higher individual tier | ~3x the Pro usage pool | Per token at model rates |
| Ultra | Top individual tier | ~20x the Pro usage pool | Per token at model rates |
| Teams Standard (was "Business") | $40/seat/month | Usage pool per seat | Per token at model rates |
| Teams Premium | $120/seat/month | Larger pool per seat | Per token at model rates |
| Enterprise | Custom | Custom | Custom |

Annual billing on Pro reduces the seat cost to ~$16/month. Cursor renames and
restructures tiers frequently - verify the current lineup at cursor.com/pricing
before building a seat forecast.

### Token rate variability

Token rates depend on which model handles the request. This is the highest-leverage cost
variable. The range is wide:

- **Auto mode** (Cursor's default routing): the earlier flat Auto rate was retired -
  Auto now bills at the API rate of whichever model it routes to, so its cost tracks
  the routing mix rather than a fixed figure
- **First-party models** (Composer, Grok variants): included in the plan's "Cursor
  Models" pool with no separately published per-token rate
- **Premium models** (e.g. the Claude Opus family): $5.00/MTok input, $25.00/MTok output

A 10-50x gap exists between the cheapest and most expensive models available in Cursor.
Even small shifts in model distribution across a team show up on the invoice fast.

### Max mode

Max mode uses the maximum context window for all models, which increases input token
consumption per request. It is a legitimate feature for working with large codebases, but
if enabled organisation-wide by default, the token consumption increase may not be
justified for every use case.

### Cost drivers

Four dimensions explain what is behind a Cursor invoice:

| Dimension | What it reveals | FinOps action |
|---|---|---|
| **Model mix** | Which models are consuming tokens | Steer simple completions to cheaper models |
| **Token type split** (input vs output) | Whether context or generation drives cost | High input = large context windows or max mode; High output = heavy generation tasks |
| **Per-developer variance** | Outliers in usage patterns | Investigate 5x+ gaps between teams - productivity signal or model mismatch |
| **Included vs overage ratio** | Whether the plan tier fits actual usage | If most spend is overages, the plan is undersized or usage patterns have shifted |

### Built-in cost tracking and its limits

Cursor's Admin API (Enterprise only) provides structured data by model, token type, and
developer email. This is useful raw data, but it is not a cost management tool:

- No trending (month-over-month spend changes)
- No alerting (usage spike detection)
- No team grouping (developer emails only, no cost-centre rollup)
- No cross-provider view (Cursor spend is isolated from cloud and direct API spend)

For small teams, pulling Admin API data into a spreadsheet may be sufficient. For
organisations with dozens or hundreds of developers across multiple teams, you need
tooling that handles aggregation, team allocation, and alerting. Third-party FinOps
platforms (Vantage, CloudZero, Finout) support Cursor natively and can provide this
layer.

---

## Claude Code

Claude Code is a terminal-based coding agent built by Anthropic. It has two access paths,
each with a different billing model.

### Subscription access

| Plan | Cost | What you get |
|---|---|---|
| Pro | $20/month | Claude Code access, current Sonnet and Opus models, moderate token budget |
| Max 5x | $100/month | 5x the Pro usage allowance |
| Max 20x | $200/month | 20x the Pro usage allowance |

On subscription plans, usage is included up to the plan limit. You do not see per-token
charges, but you hit rate limits when the budget is consumed.

### API key access (BYOK)

When using an API key, Claude Code bills directly against your Anthropic account at
standard API rates:

| Model | Input ($/MTok) | Output ($/MTok) |
|---|---|---|
| Claude Haiku 4.5 | $1.00 | $5.00 |
| Claude Sonnet 5 / 4.6 | $3.00 | $15.00 (Sonnet 5 introductory $2/$10 through 31 August 2026) |
| Claude Opus 5 / 4.8 / 4.6 | $5.00 | $25.00 |

Anthropic's own data indicates the average Claude Code user on API key mode costs ~$6/day,
with 90% of users staying under $12/day. At sustained full-time usage, expect
$100-$200/developer/month.

**Important cross-reference:** Claude Code usage on API key mode is subject to the same
billing mechanics documented in `finops-anthropic.md` - Fast mode (2x, Opus-tier only),
prompt-caching multipliers, and Batch API discounts. Read the rates there rather than
here; this file states the developer-tool consequences, `finops-anthropic.md` is the
source of truth for the mechanics. Fast mode was introduced in Claude Code and doubles
the unit price of a session on the models that support it, which makes it a governance
question wherever developers can toggle it themselves.

### Cost tracking for Claude Code

- **ClaudeXray** - dedicated cost tracking tool for Claude Code usage
- **LiteLLM proxy** - route Claude Code API calls through LiteLLM to inject metadata
  (team, project, cost centre), enforce per-team budgets, and get usage analytics.
  LiteLLM auto-detects Claude Code via User-Agent header
- **Anthropic Console** - basic usage and billing data at the organisation level

**Native gateway spend-limit warnings (as of August 2026).** Claude Code now surfaces
gateway spend limits proactively in its usage warnings - showing the spending cap, the
reset time, and the operator message - rather than only failing silently or after the
fact. For teams enforcing per-user or per-team budget caps this improves cost-governance
visibility and reduces surprise overage incidents. The practical effect is that ClaudeXray
and LiteLLM are no longer needed *purely* for budget-cap visibility; they remain valuable
for metadata injection, cross-tool aggregation, and analytics, but the cap-and-reset
signal is now available natively.

---

## OpenAI Codex

Codex is OpenAI's coding agent, available through ChatGPT and as a CLI tool.

### Access paths

**ChatGPT subscription (default):** Codex CLI usage draws from your ChatGPT plan limits
at no extra per-token charge. ChatGPT Plus at $20/month is the cheapest access path.

**API key mode:** when switched to API key mode, Codex bills per token at standard
OpenAI API rates for the current Codex-facing models (GPT-5.x-Codex variants).
**This file deliberately does not carry an OpenAI rate card.** A previous
version listed GPT-4o and o1-series rates under an "as of March 2026" heading and then
noted, in the same block, that GPT-5.5 had superseded them - a table that was known to
be stale at the moment it was read is worse than no table, because it invites a
forecast built on retired models.

For OpenAI capacity planning, price against https://openai.com/api/pricing/ at the time
of the exercise. The structural points that do not rot:

- **The Codex-facing models and the general API models are priced separately** - a
  Codex seat estimate built from general API rates will be wrong in both directions
  depending on which model the seat routes to.
- **Reasoning-model output tokens dominate.** Where a reasoning model is in play,
  output volume, not input, drives the bill, which inverts the usual prompt-caching
  advice that assumes input-heavy workloads.
- **Model deprecation is the forecasting risk.** OpenAI retires and repositions models
  faster than most FinOps refresh cycles, so a rate assumption more than a quarter old
  should be treated as unverified regardless of how it was sourced.

Sources: https://www.finout.io/blog/openai-pricing-in-2026,
https://openai.com/index/introducing-gpt-5-5/,
https://help.openai.com/en/articles/20001106,
https://openai.com/api/pricing/

OpenAI claims Codex CLI is approximately 4x more token-efficient than Claude Code, meaning
the same budget covers more work. This claim should be validated against your own workloads
before using it for capacity planning. Note that OpenAI's model naming evolves frequently
(e.g. GPT-5.4, GPT-5.3-Codex, GPT-5.1-Codex-Mini) - verify current model names and rates
against the OpenAI pricing page.

### Cost tracking

Codex in API key mode is subject to the same attribution options as any OpenAI API usage.
LiteLLM proxy supports Codex CLI for metadata injection and budget controls, detecting it
via User-Agent header.

---

## GitHub Copilot and Windsurf (comparison)

These tools are included for reference. Both are seat + usage tools with vendor-mediated
billing.

### GitHub Copilot

| Plan | Seat cost | Notes |
|---|---|---|
| Free | $0 | Limited completions |
| Pro | $10/month | Individual developers (~$15 in AI credits included) |
| Pro+ | $39/month | Higher limits, premium models (~$70 in credits) |
| Max | $100/month | Top individual tier (~$200 in credits) |
| Business | $19/seat/month | Admin controls, audit logs, IP indemnity |
| Enterprise | $39/seat/month | Requires GH Enterprise Cloud ($21/seat/month extra); ~3,900 credits/user |

Overage charges apply at $0.04 per premium request beyond the monthly allocation.

**GitHub AI Credits - transition date passed 1 June 2026.** GitHub moved Copilot
overage from the fixed `$0.04 per premium request` rate to usage-based billing in
GitHub AI Credits, where requests are priced against their underlying model token
cost with the provider margin in the credit rate. **Verify the current rate card
before quoting any per-request figure** - the $0.04 above is the legacy rate and is
retained here only because a customer's historical invoices will show it.

The FinOps consequence is a change in cost *shape*, not just rate: a flat
per-request price made Copilot overage forecastable from request volume alone,
while credit-based pricing makes it a function of volume **and** model mix. A team
that shifts its routing default to a higher-cost model sees spend move with no
change in developer behaviour or headcount.

Post-transition actions: (1) reconcile the first full credit-billed month against
the pre-transition baseline per developer, and expect the variance to be
concentrated in whoever routes to the most expensive models; (2) check whether
Enterprise admin model-routing controls are actually set, rather than left at
default; (3) confirm the variable-spend line is budgeted in the right cost centre,
since a usage-based charge often lands differently from a per-seat one.
Source: https://docs.github.com/en/copilot/how-tos/manage-and-track-spending/prepare-for-your-move-to-usage-based-billing

Enterprise total cost of ownership is $60/seat/month when including the required GitHub
Enterprise Cloud subscription - a detail that often surprises procurement. Note GitHub
flags the $21 GHEC rate as "for the first 12 months", so model the post-year-1 renewal
above $60.

### Windsurf (now "Devin Desktop")

Windsurf overhauled its pricing in March 2026, retiring the credit system in favour of
daily/weekly usage quotas, and rebranded to **Devin Desktop** in June 2026 (windsurf.com
now redirects to devin.ai - expect the vendor name change to surface in invoices and
SaaS-management inventories).

| Plan | Cost | Usage model | Notes |
|---|---|---|---|
| Free | $0 | Limited quota | - |
| Pro | $20/month | Daily/weekly usage quota | The former $40 mid-tier no longer exists |
| Max | $200/month | Larger quota | Top individual tier |
| Teams | $40/seat/month | Quota per seat | Centralised billing, admin analytics |
| Enterprise | Custom | Per-seat allocation | SSO, compliance |

Usage beyond the included quota bills at underlying model API pricing. The legacy
credit mechanics ($0.04/credit with a 20% margin, add-on credit packs) were retired
with the March 2026 overhaul and survive only on historical invoices.

---

## Cost attribution patterns

Cost attribution for AI dev tools is harder than for cloud infrastructure. There are no
resource IDs, no native tagging, and no equivalent of CUR or Cost Management exports. The
approach depends on the billing architecture.

### For vendor-mediated tools (Cursor, Copilot, Windsurf)

**Vendor Admin API** (where available): pull usage data by developer email, model, and
token type. Roll up to teams manually or using virtual tagging in a third-party platform.
Limitations: Enterprise tier often required, no native team grouping, no alerting.

**Third-party FinOps platforms**: tools like Vantage, CloudZero, or Finout support native
Cursor integrations and can aggregate spend, create virtual team tags from developer
emails, provide trending and alerting, and show AI dev tool costs alongside cloud
infrastructure spend.

**Manual spreadsheet**: pull Admin API data periodically, map developer emails to teams,
build charts. Works for small teams. Does not scale.

### For BYOK tools (Claude Code, Codex in API key mode)

**API gateway / proxy (LiteLLM)**: this is the most powerful option. Route all API calls
through a self-hosted LiteLLM proxy to:

- Inject metadata at request level (team ID, project, feature, environment)
- Set per-team or per-project budget caps with automatic enforcement
- Track usage by any dimension you define
- Get unified analytics across Claude Code, Codex, and any other tool using the same
  API keys
- LiteLLM auto-detects tool type via User-Agent header (Claude Code, Codex CLI, etc.)

**Dedicated tracking tools**: ClaudeXray for Claude Code provides purpose-built cost
visibility without requiring a proxy setup.

**Provider console**: Anthropic Console and OpenAI Dashboard provide organisation-level
billing data but limited per-developer or per-team granularity.

### Attribution maturity model

| Maturity | Approach | Granularity |
|---|---|---|
| Crawl | Invoice total, headcount-based allocation | Organisation-level |
| Walk | Admin API or provider console, spreadsheet rollup | Developer-level |
| Run | API gateway with metadata injection + third-party aggregation | Team / project / feature level |

---

## Optimisation levers

### For seat + usage tools (Cursor, Copilot, Windsurf)

**Model routing governance** - the single highest-impact lever. Ensure expensive reasoning
models (Opus, GPT-5) are used for tasks that benefit from them, not for routine code
completions. A team defaulting to the most capable model for every request will spend
10-50x more than one using the auto-routing or budget models for standard work.

**Max mode / premium mode governance** - make premium modes opt-in per task, not default-on
organisation-wide. Max mode increases input token consumption on every request by using the
full context window.

**Plan tier right-sizing** - track the ratio of included usage to overage spend monthly.
If overages consistently exceed the subscription cost, either upgrade the tier or
investigate whether usage patterns can be adjusted. If included usage is consistently
underconsumed, you may be over-provisioned on seats.

**Seat hygiene** - audit active vs licensed seats quarterly. Offboard promptly. Identify
developers who have not used the tool in 30+ days and reclaim seats.

**Context window policies** - large context windows cost more in input tokens. Not every
task requires the full codebase as context. Teams that scope context deliberately spend
less per request.

### For BYOK tools (Claude Code, Codex)

**Model selection** - Sonnet 4.6 at $3/$15 per MTok vs Opus 4.6 at $5/$25 for Claude Code.
codex-mini at $1.50/$6 vs GPT-5 at $1.25/$10 for Codex. Choose the model that matches the
task complexity. Default to the more efficient model and escalate only when needed.

**Prompt caching** (Anthropic) - cache reads cost 0.1x the base input price. Cache writes
cost 1.25x (5-minute TTL) or 2x (1-hour TTL). For repetitive workflows with stable system
prompts, caching provides significant savings. See `finops-anthropic.md` for the full
mechanics.

**Batch API** (Anthropic) - 50% discount on all token costs for asynchronous workloads.
Not applicable to interactive coding sessions, but useful for batch code review, test
generation, or codebase analysis tasks.

**LiteLLM budget caps** - set hard or soft budget limits per team or project at the proxy
level. Prevents runaway spend from a single developer or workflow.

**Context window management** - the 200K repricing cliff applied to older Claude models
that reached 1M context via a beta header; the current generation prices flat across a
1M window (see "Context window pricing" in `finops-anthropic.md`). On current models the
exposure is therefore token *volume* and context exhaustion, not a rate cliff - monitor
input tokens because long contexts cost more in absolute terms, not because a threshold
reprices the request. Check which models the estate actually pins before designing an
alert around a threshold.

---

## The context-load tax: MCP servers, skills, and context files

Every enabled MCP server, skill, and always-on context file is loaded into the model's
context at the **start of every session**, whether or not it is ever used. The model has to
be told a tool exists before it can decide to call it, so the definition is injected as
input tokens up front. A developer who enables twenty MCP servers "just in case" pays for
twenty servers' worth of definitions on every session - most never invoked.

This is not an MCP-specific problem, and framing it as one misdiagnoses the fix. It is
context-window economics, and it applies to anything that lands in the context prefix: MCP
tool definitions, skill instructions, project/memory files (e.g. `CLAUDE.md`), and the base
system prompt itself. MCP is simply the most *visible* case, because the token count jumps
the moment you enable a server.

**Order of magnitude** (from a live Claude Code walkthrough, July 2026; figures approximate):
the base system prompt alone was on the order of ~30K tokens; enabling two small MCP servers
added a few thousand more and roughly doubled the cost of a trivial turn - with the servers
never called. At scale the arithmetic compounds: 1,000 developers x 10 enabled servers x 10
sessions/day is a material daily line item for capability nobody used that day.

**Interaction with prompt caching.** The context prefix is cached, so within the cache window
the marginal cost is small (cache reads are 0.1x base input; see `finops-anthropic.md` for
the full mechanics). Two things break that: (1) the ~5-minute cache TTL - an idle gap longer
than the window forces the whole prefix to be reprocessed at full price on the next turn (in
the walkthrough, a cache miss after a coffee break turned a ~$0.02 turn into ~$0.12), and
(2) enabling a new server mid-prefix invalidates the cache from that point on. Long,
unfocused sessions make it worse: the resent context keeps growing, so every miss reprocesses
a larger blob.

### Levers

- **Scope enablement per project, not globally.** Servers placed in the user-level Claude
  Code config load into *every* session on the machine. Enable servers in the project that
  needs them, not in the global config.
- **Audit all three surfaces, not just MCP.** Unused skills and stale context/memory files
  carry the same per-session tax. Review them together.
- **Keep sessions short and single-purpose,** and complete a unit of work inside one cache
  window rather than trickling prompts in over 20 minutes.
- **Control for cache state when measuring.** Cache-window timing can invert a naive A/B
  comparison - a configuration can look cheaper purely because its run stayed inside the
  window while the baseline crossed the TTL. Compare like for like.

### Visibility: session logs and OpenTelemetry

Two data sources expose this without a third-party tool:

- **Local session logs.** Claude Code writes per-session `.jsonl` files (organised by project
  path) containing token counts, the available tool/MCP definitions, and the system prompt -
  raw but forensic. The `/context` command shows the same breakdown live (system prompt vs
  tools/MCP vs messages), and `/cost` estimates session spend.
- **OpenTelemetry.** Claude Code emits OTel metrics - a vendor-neutral standard also supported
  across other AI dev tools - including session counts and per-session cost. Configure via
  environment variables and point the exporter at a collector (local, or an observability
  backend). Governance note: prompt *text* is **off by default** for confidentiality; you get
  token and metadata signals unless you explicitly opt in. Because OTel is tool-agnostic, one
  pipeline can cover Claude Code alongside other agents.

---

## Cross-tool spend overlap

Many engineering organisations use multiple AI coding tools simultaneously - for example,
Cursor for IDE-based work and Claude Code for terminal-based agentic tasks, with some
developers also using direct Anthropic or OpenAI API keys for custom scripts.

This is not inherently wasteful. Different tools serve different workflows. But it
becomes a cost problem when:

- The same developer is paying for Cursor Business ($40/month) and a Claude Max 5x
  subscription ($100/month) but only actively using one
- Cursor is routing requests to Claude models while the team also pays for direct
  Anthropic API usage for the same models
- Multiple API keys exist across the organisation with no centralised tracking, creating
  shadow AI spend

### How to audit

1. List all AI dev tool subscriptions (Cursor, Copilot, Windsurf seats) and API accounts
   (Anthropic, OpenAI)
2. Map developer overlap - which individuals appear in multiple billing streams
3. Assess whether the overlap is intentional (different tools for different workflows) or
   accidental (tool proliferation without governance)
4. Consolidate API keys where possible and route through a single proxy for unified
   visibility
5. Establish a policy on which tools are sanctioned and for which use cases

---

## Pricing comparison (verified August 2026)

| Tool | Type | Seat cost | Token / usage model | Enterprise option | Proxy-compatible |
|---|---|---|---|---|---|
| **Cursor** | Seat + usage | $20 (Pro) / $40 (Teams Standard) / $120 (Teams Premium) | Usage pool per plan + per-token overage at model rates | Yes (custom) | No (vendor-mediated) |
| **Claude Code** | BYOK or subscription | $20 (Pro) / $100 (Max 5x) / $200 (Max 20x) | API key: $1-$25/MTok depending on model | Via Anthropic Enterprise | Yes (API key mode) |
| **OpenAI Codex** | BYOK or subscription | $20 (ChatGPT Plus) and up | API key: per-token at current Codex-model rates (see OpenAI pricing page) | Via OpenAI Enterprise | Yes (API key mode) |
| **GitHub Copilot** | Seat + usage | $10 (Pro) / $100 (Max) / $19 (Business) / $39 (Enterprise) | AI-credit overage priced on underlying model cost (legacy $0.04/request retired June 2026) | Yes ($60/seat total with GH Enterprise Cloud) | No (vendor-mediated) |
| **Windsurf (Devin Desktop)** | Seat + usage | $20 (Pro) / $200 (Max) / $40 (Teams) | Daily/weekly quota + API-priced overage (credits retired March 2026) | Yes (custom) | No (vendor-mediated) |

---

## Crawl-stage unit ratio: AI spend per merged PR

Before an org has session-level attribution, it still needs one number that says whether
dev-tool spend is tracking output. The cheapest lives at Crawl:

**AI dev-tool spend per merged PR** - the ratio of dev-tool spend to merged pull
requests, per team, per month (per developer where useful). It needs only two inputs most
orgs already have: the tool invoice (or per-developer Admin API rollup) and merged-PR
counts from the git host. Track the ratio over time and run anomaly detection on *the
ratio*, not the raw spend. A step change means either spend outran throughput (a
model-routing regression, a max-mode default, a stuck agent) or throughput dropped while
spend held - both are worth a look.

**Goodhart caveat - this is an allocation signal, never a performance metric.** The moment
"spend per merged PR" is used to rank or appraise developers, it is gamed: PRs get split
to inflate the denominator and the number stops measuring anything. Merged PRs are a
noisy, manipulable proxy for value (a one-line fix and a week-long refactor each count as
one). Use the ratio to spot cost-versus-output drift at the team level and to size the
tool budget; never to evaluate a person. See `finops-for-ai.md` for the unit-economics
framing this approximates.

---

## The governance gap: subscription caps vs API and agentic burn

The two billing architectures above have very different blast radii, and budgets break on
the wrong side of the line from where governance attention usually goes:

- **Subscription / seat plans are self-capping.** A Cursor seat, a Copilot seat, or a
  Claude Code Max plan has a ceiling: once the included usage is consumed, the developer
  hits a rate limit, not an overage cliff. The worst case is a bounded, predictable
  monthly number. This is the safe side, and it draws most of the governance attention
  because the invoice is legible.
- **API-direct (BYOK) and agentic consumption is where budgets actually break.** A raw
  API key with no proxy has no ceiling. An agent looping on that key (see the
  [cross-cloud-agent-loop-burn](../playbooks/cross-cloud-agent-loop-burn.md) playbook) or
  a background job left running bills per token until someone notices, and the overage
  lands 24-48 hours later on the provider bill rather than in a vendor dashboard.

Put the hard controls where the unbounded risk is. Subscription tiers need seat hygiene
and right-sizing (bounded problems). API keys and agentic workloads need per-key or
per-team budget caps at a proxy (LiteLLM), sustained-throughput alarms, and a kill-switch,
because that is the side with no built-in ceiling. Spending governance effort in
proportion to invoice legibility rather than to unbounded risk is the common mistake.

---

## Diagnostic questions for a new engagement

1. Which AI coding tools are in use across the organisation, and is adoption sanctioned or shadow IT?
2. How many seats are active vs licensed? When was the last seat audit?
3. For seat + usage tools: what is the ratio of included usage to overage spend?
4. Are developers also using direct API keys (Anthropic, OpenAI) alongside IDE tools?
5. Is there any cost attribution beyond the total invoice? Can you see spend by team?
6. Are premium modes (max mode, Fast mode) governed or default-on?
7. Is an API gateway or proxy in place for BYOK tools?
8. What is the monthly cost per developer, and how does it compare to the productivity value delivered?

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
