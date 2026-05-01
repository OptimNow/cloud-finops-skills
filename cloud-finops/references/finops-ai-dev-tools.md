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

Cursor restructured its pricing in early 2026, moving from the older Pro / Business
two-tier layout to a four-tier individual + team structure. As of April 2026 the
canonical tiers are **Pro**, **Ultra**, **Teams**, and **Enterprise**:

| Plan | Tier focus | Notes |
|---|---|---|
| Hobby (free) | Trial | Limited requests and completions |
| Pro | Individual | Includes a request allotment plus usage-based pricing after limits; some current marketing wording emphasises "unlimited agent requests" within fair-use bounds |
| Ultra | Heavy individual | Larger request allotment, designed for full-time agentic use |
| Teams | Team | Per-seat pricing, centralised billing, admin analytics, request allotment per seat with usage-based pricing on top |
| Enterprise | Org | Custom contract, SSO, compliance, procurement-friendly billing |

**Verify live dollar amounts** against the official pricing page before quoting -
Cursor has shipped multiple pricing changes in the past 12 months and absolute
numbers move. Sources: https://www.cursor.com/en/pricing, https://docs.cursor.com/en/account/teams/pricing

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
API rates. As of March 2026, OpenAI's API pricing structure includes:

| Model | Input ($/MTok) | Output ($/MTok) |
|---|---|---|
| GPT-4o | $2.50 | $10.00 |
| GPT-4o mini | $0.15 | $0.60 |
| o1 | $15.00 | $60.00 |
| o1-mini | $3.00 | $12.00 |

**Note:** OpenAI announced GPT-5.5 availability in API and Codex on 24 April 2026. Verify
current rates for GPT-5.5 and other models against the live pricing page before capacity
planning.

OpenAI claims Codex CLI is approximately 4x more token-efficient than Claude Code, meaning
the same budget covers more work. This claim should be validated against your own workloads
before using it for capacity planning - the comparison is sensitive to which models the
two tools route to and how each handles context.

Sources: https://www.finout.io/blog/openai-pricing-in-2026, https://openai.com/index/introducing-gpt-5-5/, https://help.openai.com/en/articles/20001106, https://openai.com/api/pricing/

### Cost tracking

Codex in API key mode is subject to the same attribution options as any OpenAI API usage.
LiteLLM proxy supports Codex CLI for metadata injection and budget controls, detecting it
via User-Agent header.

---

## GitHub Copilot and Windsurf (comparison)

These tools are included for reference. Both are seat + usage tools with vendor-mediated
billing.

### GitHub Copilot

GitHub Copilot is in the middle of a billing model transition. Plan accordingly when
quoting in customer engagements.

**Current model (until 31 May 2026) - premium-request billing:**

| Plan | Seat cost | Notes |
|---|---|---|
| Free | $0 | Limited completions |
| Pro | $10/month | Individual developers |
| Pro+ | $39/month | Higher limits, premium models |
| Business | $19/seat/month | Admin controls, audit logs, IP indemnity |
| Enterprise | $39/seat/month | Requires GH Enterprise Cloud ($21/seat/month extra) |

Overage at $0.04 per premium request beyond the monthly allocation. Enterprise total
cost of ownership is $60/seat/month including the required GitHub Enterprise Cloud
subscription - a detail that often surprises procurement.

**New model (from 1 June 2026) - usage-based billing with GitHub AI Credits:**

GitHub announced on 27 April 2026 that Copilot is moving to **usage-based billing
with GitHub AI Credits** starting **1 June 2026**, replacing the premium-request
model. Subscription tiers continue to exist; the metered layer changes from "premium
requests" to AI Credits consumed against the included allowance with overage billing
on top.

**FinOps implications during transition:**
- Forecasts built on the premium-request model break for usage from June onwards.
  Re-baseline using post-1-June consumption, not pre-1-June extrapolation.
- Customers with custom enterprise contracts may retain the premium-request model
  longer - confirm per contract before assuming the new model applies.
- Allocation logic that maps premium requests to teams must be replaced with
  AI-Credit accounting.

Sources: https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/, https://docs.github.com/copilot/concepts/billing/usage-based-billing-for-individuals, https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing

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

### Gemini Code Assist

Gemini Code Assist is Google's AI coding tool, distributed primarily via Google
Cloud and Google Workspace channels rather than as a standalone subscription.
Two distinct entitlement paths matter for FinOps:

- **Bundled with Google Workspace / Google Cloud editions.** Some Workspace and
  GCP editions include Gemini Code Assist in the seat licence. The marginal cost
  of enabling it for already-licensed users is zero - which makes adoption
  economics very different from the seat + usage model of Cursor or Copilot.
- **Standalone subscription tiers** (Standard, Enterprise) for organisations
  without bundling. Per-user monthly pricing; verify current rate against the
  Google Cloud pricing page.

**FinOps angle:**
- For organisations already on a Workspace edition that includes Code Assist,
  pay-per-seat tools (Cursor / Copilot) become harder to justify on cost alone -
  the comparison is "Code Assist for $0 marginal cost" vs "Cursor at $X / month
  per seat". Quality benchmarking still matters; cost is no longer the only
  driver.
- For BYOK comparisons, Gemini Code Assist's token consumption against your
  Vertex AI quota is the relevant cost line - similar to how Claude Code on API
  key mode bills against your Anthropic account. Apply the same cost-attribution
  patterns documented for BYOK tools earlier in this file.
- Gemini API context-caching pricing differs from token billing - see
  `finops-vertexai.md` for Vertex AI Context Caching mechanics.

Source: https://cloud.google.com/products/gemini/code-assist

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
emails, provide trending and alerting, and show