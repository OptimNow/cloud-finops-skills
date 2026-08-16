---
name: finops-anthropic
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_phases: ["Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Product", "Finance"]
fcp_maturity_entry: "Walk"
---

# FinOps on Anthropic

> Anthropic-specific guidance covering the billing model changes introduced in February 2026,
> including Fast mode pricing, long-context cost cliffs, prompt caching multipliers, tool
> charges, service tiers, and the new Claude Managed Agents runtime. Covers governance
> controls, workload segmentation, and cost allocation practices for Claude API, Claude Code,
> and Managed Agents usage.
>
> Distilled from: [Explaining Anthropic billing changes in 2026](https://www.finout.io/blog/anthropic-billing-changes-2026)
> by Asaf Liveanu (Finout), February 24, 2026 and [Anthropic just launched Managed Agents](https://www.finout.io/blog/anthropic-just-launched-managed-agents.-lets-talk-about-how-were-going-to-pay-for-this).
>
> **Source caveat:** Managed Agents and Fast mode mechanics in this file are partly sourced
> from Finout commentary, not Anthropic primary documentation. Where exact pricing,
> activation rules, or feature scope matter for a customer commitment, **verify against
> Anthropic's primary docs** before quoting:
> - https://platform.claude.com/docs/en/about-claude/pricing
> - https://platform.claude.com/docs/en/build-with-claude/prompt-caching
> - https://code.claude.com/docs/en/costs

---

## Anthropic billing model overview

### From simple token pricing to a multi-variable cost model

As of April 2026, Anthropic's billing is no longer a flat "tokens in, tokens out" model.
Total cost is now shaped by a combination of variables that FinOps must track explicitly:

| Variable | What it does |
|---|---|
| Model choice | Base token rate anchor (Opus 5: $5/$25 per MTok input/output) |
| Performance tier | Standard vs Fast mode - 2x price multiplier, and only on the models that offer it |
| Context length | **Per-model**: the current generation prices flat across a 1M-token window with no long-context premium. Older models applied premium rates above 200K input tokens. Verify per model rather than assuming either behaviour. |
| Data residency | US-only inference adds a 1.1× multiplier |
| Prompt caching | Writes are priced (1.25× or 2×), reads are discounted (0.1×) |
| Tool usage | Web search and code execution have separate meters |
| Batch processing | 50% discount via Batch API (Fast mode excluded) |
| Service tier | Standard, Priority, or Batch - affects capacity and pricing |
| Managed Agents | Fully managed runtime with persistent sessions and sandboxed execution |

---

## Pricing reference: Claude models

### Base token pricing (verified against Anthropic model documentation, June 2026)

| Model | Input ($/MTok) | Output ($/MTok) | Context | Notes |
|---|---|---|---|---|
| Claude Fable 5 | $10 | $50 | 1M | Most capable widely released model; above Opus-tier pricing |
| Claude Opus 5 | $5 | $25 | 1M | Current Opus. Same price as Opus 4.8 - a drop-in upgrade |
| Claude Opus 4.8 | $5 | $25 | 1M | Previous Opus |
| Claude Opus 4.7 | $5 | $25 | 1M | |
| Claude Opus 4.6 | $5 | $25 | 1M | |
| Claude Sonnet 5 | $3 | $15 | 1M | Introductory $2/$10 through 31 August 2026 |
| Claude Sonnet 4.6 | $3 | $15 | 1M | |
| Claude Haiku 4.5 | $1 | $5 | 200K | 200K window - the 1M window applies to 4.6-generation and later models only (the still-active Opus 4.5 and Sonnet 4.5 are likewise 200K) |

**Two FinOps consequences of this table.** First, the Opus tier has held $5/$25 across
five generations (4.5 through 5), so a model upgrade inside that tier is a capability change at
constant unit cost - there is no rate negotiation to run, and no reason to stay on an
older Opus for price reasons. Second, Fable 5 sits at 2x Opus pricing, which makes
"use the most capable model" a materially different decision from "use the newest
Opus": route to Fable 5 on evidence, not by default.

The introductory Sonnet 5 rate is a scheduled increase, not a discount to
negotiate: budgets built on $2/$10 rise 50% on 1 September 2026 with no change in
usage. Flag it now if Sonnet 5 carries meaningful volume.

### Fast mode pricing

Fast mode runs the same model at higher output tokens per second, at premium
pricing. It is in **research preview** and it is **not a general tier** - the scope
is narrow enough that it is easy to over-plan for:

| Model | Standard | Fast mode | Premium |
|---|---|---|---|
| Claude Opus 5 | $5 / $25 | $10 / $50 | 2x |
| Claude Opus 4.8 | $5 / $25 | $10 / $50 | 2x |

- **No Sonnet or Haiku Fast tier exists.** Fast mode is Opus-tier only.
- **Opus 4.7 Fast mode has been removed** - requesting it returns an error. On
  **Opus 4.6** the failure mode is quieter: requests with `speed: "fast"` run at
  standard speed and bill at standard rates, so a misconfigured client pays
  nothing extra but silently loses the latency it thinks it bought.
- Fast mode pricing applies **across the full context window**, including
  requests over 200K input tokens - there is no separate long-context tier on top.
- **Claude API only**, including Managed Agents. Not available on Amazon Bedrock,
  Google Cloud, or Microsoft Foundry, so a Bedrock-based estate cannot use it at all.
- **Not compatible with the Batch API or Priority Tier.**
- Fast mode draws on **separate rate limits** from standard Opus.
- Switching speed mid-conversation **invalidates the prompt cache** - a Fast-mode
  fallback path that flips `speed` on retry silently loses cache reads, which can
  cost more than the latency it saves.

### Batch API pricing

50% discount on both input and output for every model. Most batches complete within
an hour; the ceiling is 24 hours. Results are retained 29 days.

| Model | Input ($/MTok) | Output ($/MTok) |
|---|---|---|
| Claude Opus 5 Batch | $2.50 | $12.50 |
| Claude Sonnet 5 Batch | $1.50 | $7.50 ($1 / $5 introductory through 31 August 2026) |
| Claude Haiku 4.5 Batch | $0.50 | $2.50 |

Batch is the single largest rate lever available without a commercial negotiation.
The gating question is never price, it is whether the workload tolerates asynchronous
completion - which makes it a workload-classification exercise, not a procurement one.

### Modifiers

- **US-only inference** (`inference_geo`): x1.1 on all token categories.
  Claude 4.6 and later models only - earlier models return a 400 error if the
  parameter is set
- **5-minute cache writes**: x1.25 on base input price
- **1-hour cache writes**: x2 on base input price
- **Cache reads**: x0.1 on base input price (90% discount)
- **Modifiers stack** - Fast mode plus US-only inference compounds

**Cache break-even depends on the TTL, and the 1-hour TTL is not a free upgrade.**
At the 5-minute TTL a prefix pays for itself on the second request (1.25x write +
0.1x read = 1.35x, versus 2x uncached). At the 1-hour TTL the doubled write cost
needs at least two reads (2x + 0.2x = 2.2x versus 3x uncached). Choose the 1-hour
TTL for bursty traffic with gaps longer than five minutes, not as a default.

### Tool charges

| Tool | Pricing |
|---|---|
| Web search | $10 per 1,000 searches + standard input token costs for search results |
| Code execution | 1,550 free hours/month per org, then $0.05/hour/container (5-minute minimum billed execution time). **Free** when the request also includes web search or web fetch (tool versions `20260209` or later) |

---

## Claude Managed Agents: new cost dimension

> **Status (verified August 2026).** Managed Agents is a documented beta with a
> published API surface and, since this section was last revised, **published
> pricing**: tokens at standard model rates plus session runtime at **$0.08 per
> session-hour**. The architecture and billing model below are from Anthropic's
> documentation.

### What Managed Agents are

A server-managed, stateful agent surface. Anthropic runs the agent loop and hosts a
per-session container where the agent's tools execute. The object model matters for
cost attribution:

| Object | What it is | Cost relevance |
|---|---|---|
| **Agent** | A persisted, versioned config (model, system prompt, tools, MCP servers, skills). Created once, reused | No direct cost; the `model` field on it sets the token rate for every session |
| **Session** | One stateful run against an agent, in an environment | The unit to attribute cost to. Carries `usage` |
| **Environment** | A reusable template for provisioning containers | Cloud (Anthropic-hosted) or self-hosted (your infrastructure) |
| **Container** | Where tools execute - bash, file ops, code | The runtime cost surface, and the reason session cost is not purely token-driven |

Three properties change the cost shape versus plain API calls:

- **Sessions are long-lived and can run autonomously.** A scheduled deployment fires
  sessions on a cron cadence with no human in the loop, so cost accrues without an
  interactive trigger to notice it.
- **Context compaction and prompt caching are built in.** Long sessions do not scale
  cost linearly with turn count the way a naive multi-turn loop does.
- **The self-hosted environment option moves tool execution to your own
  infrastructure**, which shifts that portion of the cost from Anthropic's bill to
  your cloud bill. That is an attribution change, not a saving - budget for it in
  the right place.

### Billing model differences from standard API

> **Corrected against primary documentation (August 2026).** An earlier version of
> this section listed speculative cost drivers - session-persistence storage,
> CPU/memory resource tiers, data-transfer charges, and idle-time costs - sourced
> from pre-pricing community reporting. Anthropic's published billing model has
> exactly **two dimensions**, and the docs contradict the idle-cost claim directly.

| Dimension | Rate | Metering |
|---|---|---|
| Tokens | Standard model rates (see pricing table above) | All tokens consumed by the session. Prompt-caching multipliers apply identically; Fast mode premium applies if the agent's `model.speed` is `"fast"`; the 1.1x US-residency multiplier applies if `model.inference_geo` is `"us"` |
| Session runtime | $0.08 per session-hour | Metered to the millisecond, and **only while the session status is `running`**. Time spent `idle`, `rescheduling`, or `terminated` is not billed |

Two exclusions matter for cost modelling:

- **The Batch API discount does not apply** - sessions are stateful and interactive;
  there is no batch mode.
- **Not available on partner-operated cloud platforms** (Bedrock, Google Cloud).
  On Claude Platform on AWS, session charges convert to CCUs at the standard rate.
- Session runtime **replaces** the code-execution container-hour billing - you are
  not billed container hours on top of it.

### FinOps implications

- **Two meters, not one**: token spend still dominates for most workloads (a
  one-hour Opus 5 session consuming 50K in / 15K out is ~$0.63 of tokens and $0.08
  of runtime), but long-running low-token agents invert that ratio
- **Idle time is free** - there is no always-on charge for a session waiting on
  input, so keeping sessions open is an attribution question, not a cost one
- **Harder attribution**: Agent costs spread across multiple invocations vs discrete API calls

---

## Fast mode: key FinOps risks

> **Corrected against primary documentation (June 2026).** An earlier version of this
> section carried a 6x premium multiplier and per-model Fast tiers for Sonnet and
> Haiku, sourced from Finout reporting rather than Anthropic's own docs. Both were
> wrong: the premium is **2x**, and Fast mode is **Opus-tier only**. The claim that
> switching speed triggers "retroactive context repricing" was also unsupported -
> the documented behaviour is that changing `speed` **invalidates the prompt cache**,
> which raises the cost of the next request rather than repricing earlier ones. The
> practical governance consequence is similar; the mechanism is not, and the
> distinction matters when explaining a bill to a customer.
>
> The governance posture below stands: Anthropic's cost-governance release (model
> entitlements, spend dashboard, threshold alerts) is primary-source confirmation
> that admin-level spend controls are first-class.

### What Fast mode is

Fast mode runs the same model at up to 2.5x higher output tokens per second. It is not
a different model, and it is not a general tier - see the pricing section above for the
model and platform restrictions, which are narrow enough to change whether it is a
governance concern for a given estate at all. It was released in Claude Code v2.1.36
on 7 February 2026.

### Why it is a FinOps risk, not just a developer feature

- **Extra usage channel**: Fast mode tokens do not count against plan included usage.
  They are billed at the Fast mode rate from token one, even if plan usage remains.
- **Sticky across sessions**: Once enabled in Claude Code, Fast mode persists unless
  explicitly disabled. This makes it an unintentional overage driver.
- **Cache loss on speed switch**: Changing `speed` mid-session invalidates the
  prompt cache, so the next request re-reads the whole conversation context at
  full Fast mode uncached input rates. The effect on the bill resembles a
  retroactive repricing, but the mechanism is a lost cache, not a recharge of
  earlier requests.
- **Not available via cloud provider routes**: Fast mode is explicitly unavailable on
  Amazon Bedrock, Google Vertex AI, and Microsoft Azure Foundry. This fragments spend
  away from consolidated cloud agreements toward direct Anthropic invoices.

### Context window pricing - per-model, not uniform

Long-context pricing is **not uniform across the Claude line-up.** Practical state
as of June 2026:

- **The current generation** (Fable 5, Opus 5 / 4.8 / 4.7 / 4.6, Sonnet 5, Sonnet 4.6)
  carries a **1M-token context window at standard rates** - it is both the default and
  the maximum, with no beta header and no long-context premium. For these models the
  "1M context cliff" no longer exists.
- **Haiku 4.5** remains on a 200K window. That is a capacity limit, not a pricing
  tier: there is no premium band above it, the request simply cannot exceed it.
- **Older models reached 1M via a beta header and did apply premium rates above 200K
  input tokens.** Any estate still pinned to one of those is on the old cliff, and the
  migration to a current model removes a pricing tier as well as a capability limit.
- **Features that inflate context** (tool results, retrieval dumps) consume the window
  like any other input. On the current generation they cost the flat rate; the
  exposure is context-window exhaustion and token volume, not a rate cliff.

**FinOps action:** before quoting that "long context is now free", check the specific
model and beta-header combination the customer is using. The per-model picture
matters for forecasts. The AI dev tools reference (`finops-ai-dev-tools.md`) carries
the same warning for Anthropic-backed coding workflows.

Source: https://platform.claude.com/docs/en/about-claude/pricing

---

## Governance controls

### Fast mode controls available to admins

- Fast mode for Teams and Enterprise plans is **disabled by default** and requires
  explicit admin enablement
- Fast mode requires extra usage to be activated

**Recommended policy:**

| Scenario | Fast mode policy |
|---|---|
| Interactive debugging, urgent fixes | Allowed |
| CI/CD pipelines | Not allowed |
| Batch jobs or background agents | Not allowed |
| Production usage | Require approval or alerting |

### Native cost governance tooling (July 2026)

As of July 2026, Anthropic released a set of native cost governance features - without
an accompanying model release - that directly address cost visibility and governance
gaps previously flagged in this file. **Scope note:** the release targets **Claude
Enterprise** plan admins (covering Claude chat, Cowork, and Claude Code seat usage);
it is not a billing surface for raw API platform spend:

| Feature | What it does |
|---|---|
| Spend dashboard | Admin analytics showing usage and cost by group and by user, with output (artifacts, files edited, skills/connectors used) shown next to cost |
| Model entitlements | Admin control over which models are available per role or org-wide, and which model new conversations default to (chat, Cowork, Claude Code) |
| Threshold alerts | Admins notified at 75% and 90% of an org-level spend limit; users notified in-app at 75% and 95%, with in-product limit-increase requests |
| Admin API | Programmatic spend controls - automate limit-increase reviews, flag members near their spend limit, detect rapidly changing usage |

**Assessment (as of July 2026):** this is a meaningful step toward native cost
governance, but Finout's analysis suggests it is not yet a complete solution -
notably around granular allocation and cross-workload attribution, and it does
not cover raw API platform spend.

**Additional native signal (as of August 2026):** Claude Code now surfaces gateway
spend limit warnings proactively - displaying the spending cap, reset time, and
operator message directly in usage warnings, rather than failing silently or only
after the cap is hit. This gives teams enforcing per-user or per-team budget caps
an additional native cost-governance signal alongside the July 2026 Enterprise
admin tooling, reducing surprise overage incidents. See the "Cost tracking for
Claude Code" section in `finops-ai-dev-tools.md` for detail.

Sources: [Anthropic - New analytics and cost controls for Claude Enterprise](https://claude.com/blog/giving-admins-more-visibility-and-control-over-claude-usage-and-spend) (primary),
[Anthropic keeps signaling where AI cost governance needs to go](https://www.finout.io/blog/anthropic-keeps-signaling-where-ai-cost-governance-needs-to-go.-its-not-all-the-way-there-yet) (Finout commentary).

### Managed Agents governance

| Control | Recommendation |
|---|---|
| Agent creation | Require approval for production agents |
| Resource limits | Set maximum runtime hours per agent |
| Session timeout | Configure automatic session termination |
| Cost alerts | Monitor runtime costs separately from API usage |

### Workload segmentation: interactive vs batch vs autonomous

| Workload type | Recommended configuration | Rationale |
|---|---|---|
| Interactive / low-latency | Standard mode | Baseline cost |
| Urgent / developer flow | Fast mode (governed) | Justified premium |
| Batch, async, non-latency-sensitive | Batch API | 50% token discount |
| Autonomous agents | Managed Agents | Persistent state, sandboxed execution |

### Monitoring checklist

- [ ] Track total token usage against the model's context window (1M on the current
      generation, 200K on Haiku 4.5)
- [ ] Monitor cache reads and writes that contribute to the input token count
- [ ] Monitor Fast mode activation per user or team
- [ ] Treat web search and code execution as separate cost centres with their own budgets
- [ ] Detect Fast mode usage in CI/CD or batch jobs (anomaly detection)
- [ ] Track Managed Agent runtime hours and resource utilisation
- [ ] Monitor agent session persistence costs
- [ ] Use Anthropic's native spend dashboard for organisation-level spend visibility (as of July 2026)
- [ ] Configure native threshold alerts for spend limits per team or workload
- [ ] Apply model entitlements to restrict access to premium models/tiers where appropriate
- [ ] Integrate Anthropic's spend and entitlement APIs into existing FinOps tooling

---

## Named risk pattern: enterprise connector-rollout bill shock

A specific, repeatable way Enterprise spend blows past forecast - worth naming because
the mechanics are predictable and the mitigation is entirely pre-emptive.

**Mechanics.** A connector or feature reaches general availability and ships enabled by
default (a new data connector, a broadened context default, an agentic capability).
Multiply three factors:

1. **Default long-context processing.** The connector pulls large context - documents,
   retrieval dumps, connected-app data - into each request by default. Where the model
   and configuration apply premium long-context rates above the 200K input threshold
   (see "Context window pricing - per-model, not uniform" above), every request lands in
   the premium tier; even where pricing is flat, the input volume per call jumps.
2. **Thousands of seats.** Enterprise billing is usage-based and usage cannot be fully
   disabled, so a default-on capability activates across the whole seat count at once,
   not a pilot group.
3. **Low-attention periods.** A rollout timed just before holidays or quarter-end runs
   for days or weeks with nobody watching the console, and the usage compounds silently.

**The detection gap.** None of the three factors trips a spike alert on its own, and the
cost report is daily-grained and lags. The first unambiguous signal is the invoice - by
which point a full period of premium-context spend across the seat base has already
accrued.

**Mitigation - all pre-emptive:**

- **Stage the rollout.** Enable the connector for a pilot cohort first, measure
  cost-per-seat and the context-length distribution, and extrapolate to the full seat
  count before switching it on org-wide. A default-on GA flip across thousands of seats
  is the thing to avoid.
- **Set org-level threshold alerts before the flip, not after.** Use the native
  threshold alerts and Admin API from the native cost governance tooling table above
  (org-level 75% / 90% notifications, programmatic detection of rapidly changing usage)
  so a runaway rollout surfaces within the day rather than on the invoice.
- **Watch the leading indicators from the monitoring checklist above** - total tokens
  across the context window and Fast mode activation - during the rollout window
  specifically, including over holidays.
- **Constrain the default** where the connector allows it: cap default context scope and
  require opt-in for the largest-context modes rather than shipping them default-on.

This is the Anthropic-specific instance of the general discipline in
`finops-anomaly-management.md`: a masked, non-spiky cost increase that only usage-side,
pre-configured detection catches in time.

---

## Cost allocation

### What to allocate

Anthropic billing has distinct cost categories that should map to separate allocation
dimensions:

| Category | Allocation approach |
|---|---|
| Base token usage (input/output) | Team / project / environment |
| Fast mode overage | Developer or workflow that enabled it |
| Model tier usage (Opus/Sonnet/Haiku) | Feature or use case requirements |
| Tool usage (web search, code execution) | Function / use case |
| Batch API usage | Workload type |
| Managed Agent runtime | Agent owner / business process |
| Agent session persistence | Long-running workflow / department |

### Enterprise billing context

- Enterprise billing is usage-based; usage cannot be fully disabled
- Older seat-based enterprise billing models will transition at renewal to a single
  Enterprise seat model with usage-based billing
- Admin controls, spend caps, and usage analytics are available as part of business plans
- Managed Agents have separate billing and may require additional enterprise agreements

---

## FinOps considerations

### Forecasting

A forecast based solely on base token pricing is insufficient:
- Fast mode doubles the unit price, on the Opus-tier models that support it
- Model choice creates a 10x price range across the current lineup (Haiku 4.5 at
  $1/$5 to Fable 5 at $10/$50) - wider than the 5x range of the previous generation,
  because Fable 5 sits above Opus
- Tool usage adds call-based meters that are independent of token volume
- Managed Agents add runtime-based costs that scale differently than token usage
- Behavioural effect: lower latency reduces friction, which increases usage volume
  (more calls, longer sessions, more tool invocations)

### Provider strategy

Fast mode's exclusion from Bedrock, Vertex, and Azure Foundry is a deliberate channel
choice. If your strategy relies on CSP-consolidated billing and commitment vehicles,
this feature gap introduces spend fragmentation that governance must account for.
Managed Agents further fragment spend as they represent a distinct service tier.

### Cross-provider applicability

The same pricing pattern is emerging across providers (OpenAI priority/flex tiers,
batch discounts, managed services). The governance posture built for Anthropic - tier
detection, anomaly detection, cost allocation by feature/team/environment, guardrails
for premium modes and managed services - is reusable across the GenAI vendor landscape.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*