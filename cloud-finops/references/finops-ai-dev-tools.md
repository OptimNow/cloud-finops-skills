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
| Pro | $20/month | $20 in usage credits | Per token at model rates |
| Business | $40/seat/month | $20 in usage credits per seat | Per token at model rates |
| Enterprise | Custom | Custom | Custom |

Annual billing on Pro reduces the seat cost to ~$16/month.

### Token rate variability

Token rates depend on which model handles the request. This is the highest-leverage cost
variable. The range is wide:

- **Auto mode** (Cursor's default routing): ~$1.25/MTok input, ~$6.00/MTok output
- **Budget models** (e.g. Composer 2 Standard): ~$0.50/MTok input
- **Premium models** (e.g. Claude Opus 4.6): ~$5.00/MTok input, ~$25.00/MTok output

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
| Pro | $20/month | Claude Code access, Sonnet 4.6 and Opus 4.6, moderate token budget |
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
| Claude Sonnet 4.6 | $3.00 | $15.00 |
| Claude Opus 4.6 | $5.00 | $25.00 |

Anthropic's own data indicates the average Claude Code user on API key mode costs ~$6/day,
with 90% of users staying under $12/day. At sustained full-time usage, expect
$100-$200/developer/month.

**Important cross-reference:** Claude Code usage on API key mode is subject to the same
billing mechanics documented in `finops-anthropic.md` - including Fast mode (6x price
multiplier), long-context pricing cliffs (200K input token threshold), prompt caching
multipliers, and Batch API discounts. These are not theoretical risks. Fast mode was
introduced in Claude Code and can silently reprice an entire session.

### Cost tracking for Claude Code

- **ClaudeXray** - dedicated cost tracking tool for Claude Code usage
- **LiteLLM proxy** - route Claude Code API calls through LiteLLM to inject metadata
  (team, project, cost centre), enforce per-team budgets, and get usage analytics.
  LiteLLM auto-detects Claude Code via User-Agent header
- **Anthropic Console** - basic usage and billing data at the organisation level

---

## OpenAI Codex

Codex is OpenAI's coding agent, available through ChatGPT and as a CLI tool.

### Access paths

**ChatGPT subscription (default):** Codex CLI usage draws from your ChatGPT plan limits
at no extra per-token charge. ChatGPT Plus at $20/month is the cheapest access path.

**API key mode:** when switched to API key mode, Codex bills per token at standard OpenAI
API rates:

| Model | Input ($/MTok) | Output ($/MTok) |
|---|---|---|
| codex-mini-latest | $1.50 | $6.00 |
| GPT-5 | $1.25 | $10.00 |

API rates. As of March 2026, OpenAI's API pricing structure includes:

| Model | Input ($/1M tokens) | Output ($/1M tokens) |
|---|---|---|
| GPT-4o | $2.50 | $10.00 |
| GPT-4o mini | $0.15 | $0.60 |
| o1 | $15.00 | $60.00 |
| o1-mini | $3.00 | $12.00 |

**Note:** OpenAI announced GPT-5.5 availability in API and Codex on 24 April 2026. Verify
current rates for GPT-5.5 and other models against the live pricing page before capacity
planning.

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
| Pro | $10/month | Individual developers |
| Pro+ | $39/month | Higher limits, premium models |
| Business | $19/seat/month | Admin controls, audit logs, IP indemnity |
| Enterprise | $39/seat/month | Requires GH Enterprise Cloud ($21/seat/month extra) |

Overage charges apply at $0.04 per premium request beyond the monthly allocation.

**Imminent change - GitHub AI Credits (1 June 2026).** GitHub is moving Copilot
overage from a fixed-rate `$0.04 per premium request` to **usage-based billing in
GitHub AI Credits**. After 1 June 2026, requests are priced per their underlying
model token cost (with the provider margin baked into the credit rate) rather
than at the flat $0.04. This is a material shift for FinOps teams running
Copilot at scale: cost forecasts based on the historical $0.04 rate will drift
once developers route to higher-cost models (Claude Sonnet, GPT-5 family) where
the credit price exceeds the legacy flat rate. Recommendations: (1) capture the
last 90 days of premium-request volume per developer and project the AI Credits
spend at the new rates before 1 June, (2) review Copilot model-routing defaults
and Enterprise admin controls before the cutover, (3) validate that procurement
budgets allow for variable usage-based billing in the relevant tax / cost-centre
structure. Source: https://docs.github.com/en/copilot/how-tos/manage-and-track-spending/prepare-for-your-move-to-usage-based-billing

Enterprise total cost of ownership is $60/seat/month when including the required GitHub
Enterprise Cloud subscription - a detail that often surprises procurement.

### Windsurf

Windsurf overhauled its pricing in March 2026, replacing variable credits with fixed quota
tiers:

| Plan | Cost | Credits | Notes |
|---|---|---|---|
| Individual tiers | $20 / $40 / $200 per month | Fixed quota per tier | More predictable than token-based |
| Teams | $40/seat/month | 500 credits/seat | Centralised billing, admin analytics |
| Enterprise | Custom | Per-seat allocation | SSO, compliance |

Windsurf uses a credit system where each credit costs $0.04 and maps to the underlying
model provider's API price plus a 20% margin. Add-on credits are available at $10 for 250
(individual) or $40 for 1,000 (Teams/Enterprise).

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

**Context window management** - for Anthropic specifically, crossing the 200K input token
threshold reprices the entire request at premium rates. Monitor input token counts and
configure alerts before the cliff.

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

## Pricing comparison (March 2026)

| Tool | Type | Seat cost | Token / usage model | Enterprise option | Proxy-compatible |
|---|---|---|---|---|---|
| **Cursor** | Seat + usage | $20 (Pro) / $40 (Business) | $20 included credits + per-token overage | Yes (custom) | No (vendor-mediated) |
| **Claude Code** | BYOK or subscription | $20 (Pro) / $100 (Max 5x) / $200 (Max 20x) | API key: $3-$25/MTok depending on model | Via Anthropic Enterprise | Yes (API key mode) |
| **OpenAI Codex** | BYOK or subscription | $20 (ChatGPT Plus) and up | API key: $1.25-$10/MTok depending on model | Via OpenAI Enterprise | Yes (API key mode) |
| **GitHub Copilot** | Seat + usage | $10 (Pro) / $19 (Business) / $39 (Enterprise) | $0.04/premium request overage | Yes ($60/seat total with GH Enterprise Cloud) | No (vendor-mediated) |
| **Windsurf** | Seat + usage | $20-$200 (individual) / $40 (Teams) | Credit-based ($0.04/credit, provider cost + 20% margin) | Yes (custom) | No (vendor-mediated) |

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
