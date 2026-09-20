---
name: finops-vertexai
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Usage Optimization"]
fcp_phases: ["Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Product", "Finance"]
fcp_maturity_entry: "Walk"
---

# FinOps on GCP Vertex AI

> GCP Vertex AI (Gemini Enterprise Agent Platform) guidance covering the billing model,
> model pricing, provisioned throughput, cost allocation, and governance. Covers
> on-demand vs provisioned capacity trade-offs, publisher-scoped reservation
> flexibility, Flexible Savings Plans (FSPs), service tiers and endpoint multipliers,
> the Gemini Developer API (AI Studio) as a second billing door, and cost visibility
> within GCP Billing and BigQuery.
>
> Distilled from: "Navigating GenAI Capacity Options" - FinOps Foundation GenAI Working Group, 2025/2026.
> See also: `finops-genai-capacity.md` for cross-provider capacity concepts.

---

## GCP Vertex AI billing model overview

**Naming - you will meet both names.** Google renamed the product to **Gemini
Enterprise Agent Platform (formerly Vertex AI)**, and the documentation moved with it:
`cloud.google.com/vertex-ai/...` paths now redirect to
`docs.cloud.google.com/gemini-enterprise-agent-platform/...`, and the pricing page is
titled "Agent Platform Pricing". The billing surface has not caught up. Service and SKU
names still carry the old brand - Gemini Enterprise costs sit under the **"Vertex AI
Search" service (ID `74B1-77CF-C302`)** as of 20 September 2026, alongside newer
"Agent Platform" SKUs - so a cost query written against the new name can return
nothing. Do not assume either spelling: check the actual `service.description` and
`sku.description` values in your own billing export before writing a filter, and expect
mixed naming for as long as the transition runs. Source:
https://cloud.google.com/products/gemini-enterprise-agent-platform

This file keeps the Vertex AI name where the mechanics are unchanged, because that is
still what the billing data, the request headers and most existing estates call it.

Vertex AI is GCP's managed ML platform and inference service. For GenAI inference, it
provides access to Google's own models (Gemini family) and selected third-party models
(Anthropic Claude, Meta Llama, Mistral, and others) through a unified API.

### Billing dimensions

| Dimension | Description |
|---|---|
| Input tokens | Tokens in the prompt, including system instructions and context |
| Output tokens | Tokens generated in the response |
| Model choice | Each model and size has its own per-token rate |
| Capacity model | On-demand (PAYG) vs Provisioned Throughput |
| Grounding / tool use | Web grounding and tool call charges are separate from token rates |
| Batch prediction | Asynchronous inference at discounted rates |
| Region | Some models are available only in specific regions |

**Key cost driver:** output tokens are billed at a multiple of the input rate. The
multiplier is the number to size against - it has been more stable than the rates
themselves, and it does not move when you change service tier, because Priority, Flex
and Batch scale input and output by the same factor. As of 20 September 2026, on the
standard tier:

| SKU group | Output : input |
|---|---|
| Gemini 3.8 / 3.7 / 3.6 Flash | 5x |
| Gemini 3.5 Flash | 6x |
| Gemini 3.1 Flash-Lite (text input) | 6x |
| Gemini 3.5 Flash-Lite | about 8x |
| Gemini 3.1 Pro Preview | 6x up to a 200K-token prompt, 4.5x above it |
| Gemini 2.5 Pro | 8x (6x above 200K) |
| Gemini 2.5 Flash | about 8x |
| Gemini 2.5 Flash-Lite | 4x |

The spread is wider than the "cheap models have a low multiplier" intuition suggests:
the newest Flash SKUs are the *tightest* at 5x, while 3.5 Flash-Lite and 2.5 Flash sit
near 8x. Read the multiplier per SKU rather than per tier. High output-ratio workloads
(agentic tasks, long-form generation) carry disproportionately higher costs, so a model
swap that looks cheaper on the input rate can be more expensive in production.

Sources: https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing,
https://ai.google.dev/gemini-api/docs/pricing

---

## Model pricing reference

### On-demand pricing structure

Vertex AI on-demand pricing for Gemini generative models is per-million tokens
(verified August 2026). **Historical note:** Gemini 1.0/1.5-era surfaces billed some
SKUs per 1,000 characters rather than per token; those surfaces are retired and no
character-billed Gemini SKU remains on the current pricing page. If you encounter
character-based line items in an old billing export, that is the era they date from -
do not carry character-math into current capacity planning.

Source: https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing

No minimum spend, no upfront commitment.

| Model family | Relative cost tier | Notes |
|---|---|---|
| Gemini Flash-Lite | Low | Cheapest tier, high-volume simple tasks |
| Gemini Flash | Low-Mid | High throughput, cost-optimised |
| Gemini Pro | High | Complex reasoning, multimodal; roughly an order of magnitude above Flash on input |
| Anthropic Claude Haiku | Low | Available via Vertex Model Garden |
| Anthropic Claude Sonnet | Mid | Available via Vertex Model Garden |
| Anthropic Claude Opus | High | Available via Vertex Model Garden |
| Meta Llama (various) | Low-Mid | Open-weight, available in Model Garden |

**FinOps principle:** model selection is the single highest-leverage cost decision.
Benchmark task quality across model tiers before defaulting to the most capable model.

### Batch prediction discount

Vertex AI Batch Prediction processes requests asynchronously at discounted token rates
(typically 50% off on-demand). Use for:
- Bulk document processing and enrichment
- Offline classification pipelines
- Non-latency-sensitive evaluation workflows

**Constraint:** async processing only - not suitable for interactive workloads.

### Service tiers and endpoint multipliers

Model choice sets the base rate. These multipliers then stack on top of it, and they are
where a well-chosen model still produces a surprising bill. All verified 20 September
2026 against the Agent Platform pricing page.

| Lever | Effect on the standard rate | Notes |
|---|---|---|
| Priority tier | **1.8x**, applied to input, output and cached input alike | Global and us/eu multi-region endpoints only - no regional support |
| Flex tier | **50%** | Synchronous but latency-tolerant; Preview; global endpoint only |
| Batch | **50%** | Asynchronous, up to 24-hour turnaround |
| Non-global (regional) endpoint | **+10%** | GA Gemini 3 and later, from 1 July 2026; also applies to non-global Provisioned Throughput |
| Prompt above 200K tokens (Pro SKUs) | **2x input, 1.5x output** | The whole request reprices, not just the excess |
| Tuned model endpoint | **1.5x** the base model | Gemini 3 and later only; older Gemini tuned endpoints stay at the base price |

Four points that matter more than the numbers:

- **Flex and Batch are both 50% off but are not interchangeable.** Flex is synchronous
  best-effort with longer expected latency and a 30-minute maximum request timeout;
  Batch is asynchronous and is what Google recommends for workloads tolerating 24-hour
  turnaround. Flex is the option for "interactive but nobody is watching the clock";
  Batch is for "come back tomorrow". Routing is by header
  (`X-Vertex-AI-LLM-Shared-Request-Type: flex` or `priority`), so tier choice is a code
  path, not a console setting.
- **Data residency now has a visible price.** Before 1 July 2026 non-global endpoints
  billed at global rates. A 10% premium on every token is a real number to put in front
  of whoever is asking for in-region processing - and Priority and Flex do not support
  regional endpoints at all, so residency and tier are a genuine trade-off, not two
  independent switches.
- **The 200K band is a cliff, not a taper.** Cross the threshold and every token in the
  request, input and output, reprices to the long-context rate. A prompt that drifts from
  195K to 205K tokens roughly doubles its input cost. Alert on prompt-size distribution
  near the boundary, not just on the mean.
- **Priority preserves the output:input ratio.** Because it is a flat 1.8x on everything,
  it does not change which model is cheapest - it changes whether you can afford the tier
  at all.

**Governance point:** decide explicitly who may enable Priority, and keep it out of batch
jobs and CI. A 1.8x multiplier applied to a nightly evaluation run is pure waste - those
workloads are exactly the Flex and Batch case. This is the same control problem as
Anthropic's service tiers; see `finops-anthropic.md`.

Sources: https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing,
https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/priority-paygo,
https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/flex-paygo

### Introductory pricing on the 3.x Flash SKUs - a dated forecasting item

Gemini 3.8 Flash, 3.7 Flash and 3.6 Flash (and CodeMender using those models) bill at
**50% of their standard rate through 31 December 2026**; standard pricing applies from
**1 January 2027**. At constant volume, the January 2027 bill for these SKUs is **twice**
December's. That is a budget event, not a price rise to negotiate, and it lands in the
first month of many organisations' financial years.

Separately, from **13 August 2026 through 31 December 2026** Google injects a monthly
billing credit equal to 50% of net eligible Provisioned Throughput spend on those three
models. Two details decide whether it is worth anything: the credit is issued on the 7th
of the following month and **expires 30 days after issuance**, and it is applied against
on-demand spend on those models plus Provisioned Throughput across all models. A credit
that expires in 30 days only converts to savings if you have matching spend in that
window - treat it as a discount on continuing usage, not as a rebate.

Neither mechanism alters Provisioned Throughput commitment burndown rates.

*Remove this subsection after January 2027, once both windows have closed and the
repricing has landed in actuals.*

Source: https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing

---

## Provisioned throughput on GCP Vertex AI

### How it works

On GCP Vertex AI, provisioned throughput is purchased as **publisher-specific capacity**
for a fixed term. You reserve throughput for a specific publisher (e.g., Google, Anthropic)
and can switch between models within that publisher's portfolio.

### Key characteristics

- **Publisher-locked, model-flexible:** you can switch between Gemini models within
  the same reservation (a GSU is standard across Google models that support
  Provisioned Throughput), but not from a Google model to an Anthropic model.
  *Sourcing note:* the intra-publisher switch rule comes from a FinOps Foundation
  working-group paper, not Google primary docs - confirm against the current
  Provisioned Throughput purchase docs before quoting in an engagement.
- **Capacity floor, not ceiling:** terms run 1 week to 1 year and unused throughput
  does not carry over; treat reserved capacity as non-reducible mid-term (an explicit
  no-downsize rule is not stated in Google primary docs - verify before committing).
  Efficiency gains reduce your effective cost per output, but the reservation
  commitment remains at the original size.
- **Default spillover to pay-as-you-go** (verified 20 September 2026). If a request
  exceeds the remaining Provisioned Throughput quota, **the entire request** is
  processed on-demand and billed at the pay-as-you-go rate; it shows as *spillover* on
  the monitoring dashboards. Request headers override this, and the header name survived
  the rename - it is still `X-Vertex-AI-LLM-Request-Type`, set to `dedicated` (PT only;
  excess requests return HTTP 429) or `shared` (bypass PT entirely). This is a material
  change vs the older "build your own failover" pattern - capacity planning can size
  reservations to average load, with overage becoming variable PAYG cost during spikes.
- **Spillover is decided on an *estimate*, and that is a cost surprise.** At request
  time the true response size is unknown, so Vertex estimates the output token count. If
  the estimate exceeds available quota the whole request goes PAYG - even if the actual
  response would have fitted. Quota is reconciled afterwards against real usage. Traffic
  sitting near the quota ceiling therefore spills more often than a purely arithmetic
  model predicts, which is one reason measured PT utilisation and billed PAYG overage
  rarely reconcile cleanly. Sources:
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/provisioned-throughput/use-provisioned-throughput,
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/provisioned-throughput/supported-models
- **Capacity guarantee:** a Vertex AI reservation guarantees capacity availability for
  models within the reserved publisher family.

### Comparison to AWS Bedrock and Azure

| Dimension | GCP Vertex AI | AWS Bedrock | Azure OpenAI |
|---|---|---|---|
| Flexibility | Publisher-scoped | Model-locked | Full PTU pool |
| Model upgrade within reservation | Yes (same publisher) | No | Yes (any model) |
| Publisher switch within reservation | No | No | Yes |
| Spillover | Default PAYG (header-controlled) | Build yourself | Built-in |

### When provisioned throughput makes sense on Vertex AI

| Condition | Recommendation |
|---|---|
| Consistent 24/7 workload, Gemini-native stack | Strong candidate |
| Latency-sensitive, user-facing application | Justified for TTFT/OTPS improvement |
| Data privacy requirement | Not a provisioned differentiator - verify data-use terms, which apply per service, not per capacity mode |
| Likely to upgrade Gemini versions mid-term | GCP reservation accommodates this |
| Workload requiring cross-publisher flexibility | Azure PTU model better suited |
| Bursty or unpredictable traffic | On-demand or hybrid with manual failover |

### Provisioned throughput governance checklist

- [ ] Confirm workload has run stably for 90+ days before committing
- [ ] Load-test to validate vendor TPM estimate against actual input/output token mix
- [ ] Calculate break-even utilization (provisioned unit cost ÷ on-demand equivalent)
- [ ] Verify reserved publisher matches the model families your workloads will use
- [ ] Decide the overflow policy explicitly: default spillover bills overage as PAYG;
      use the `X-Vertex-AI-LLM-Request-Type` header (`dedicated` / `shared`) where
      you need hard routing instead of silent variable cost
- [ ] Set utilization alerts - target >80% to justify the reservation
- [ ] Assess whether new model efficiency gains offset the fixed capacity floor

---

## Gemini Developer API (AI Studio) vs Vertex AI: same token price, different mechanics

Google sells Gemini through two doors, and most estates end up using both without
deciding to. The **Gemini Developer API** (keys issued in Google AI Studio) is the
self-serve door; **Vertex AI** is the enterprise door. Teams routinely assume one is
cheaper. It is not.

**Token rates are identical** on the Gemini Developer API and the Vertex AI global
endpoint, SKU for SKU - verified 20 September 2026 across the Flash, Flash-Lite and Pro
families, including the long-context bands, the 1.8x Priority multiplier, the 50%
Flex/Batch discount and the 90% cache-read discount. The choice is a governance and
capacity decision, not a rate one.

Three real differences sit underneath the identical headline rates:

- **Explicit cache storage is cheaper on the Developer API until 1 January 2027.** On
  the 3.8 / 3.7 / 3.6 Flash SKUs it bills at half the Agent Platform rate per token-hour
  through 31 December 2026, then converges. A cache-heavy workload is genuinely cheaper
  through the Developer API today, and stops being so in January.
- **Grounding bills on a different unit.** The Developer API charges per *search query*,
  and a single prompt may issue several. Vertex AI charges per *grounded prompt* - one
  charge even when Gemini issues multiple queries - with a separate free daily
  allowance. For agentic search workloads these produce materially different bills from
  identical traffic, and the per-query model is the one that scales badly.
- **The free tier is not free of consequences** (below).

### Gemini Developer API specifics

- **A free tier** on the Flash and Flash-Lite SKUs and on Gemini 2.5 Pro, but not on the
  current Pro preview SKU. Free-tier content is **used to improve Google products**;
  paid-tier content is not.
- **Billing** runs through a Cloud Billing account linked in AI Studio. Since
  **23 March 2026** there is a choice of **prepay** (buy credits, bounded purchase size)
  or **postpay**.
- **Usage tiers 1 to 3**, each with a monthly spend cap. An account qualifies for a
  higher tier by cumulative payment and account age; the cap rises with the tier. Cap
  amounts change - read them from the billing doc rather than from a figure written
  down here.
- **Hitting the cap pauses service for every project linked to that billing account**,
  until the start of the next billing cycle (the 1st of the month).
- **Project-level caps can be set lower** in AI Studio, on the Spend page. Billing data
  can lag by around 10 minutes, so a batch job can overshoot its project cap before the
  cap registers.

**FinOps reading.** The tier cap is a free budget guardrail and an availability risk in
the same mechanism. One shared billing account across prototypes and a production key
means **a runaway prototype can pause production** - and it pauses on a billing
threshold, so it will not look like an outage to anyone reading service dashboards. Two
mitigations, in order: separate billing accounts for production, or at minimum a
project-level cap set below the tier cap so the prototype hits its own ceiling first.

The free tier's data-use terms make it unsuitable for client or personal data. That puts
AI Studio keys on the shadow-AI checklist: an individually-created free-tier key
processing client material is a confidentiality exposure that never appears on an
invoice, because there is no invoice. Inventory them the way you would any other
unsanctioned SaaS.

### Vertex AI specifics

Regional and multi-region endpoints with the residency premium and tier restrictions
covered under "Service tiers and endpoint multipliers"; IAM and service accounts instead
of API keys; Provisioned Throughput; Flexible Savings Plans; request labels for
allocation; and a single GCP invoice.

### What is the same

Both doors bill to Cloud Billing, so **one BigQuery billing export covers both** - the
unified analysis path does not fork. The AI Cost Summary Agent described below spans
Gemini API and Vertex AI services for the same reason.

Sources: https://ai.google.dev/gemini-api/docs/pricing,
https://ai.google.dev/gemini-api/docs/billing

### Project-level spend caps for agent workloads

Announced 26 August 2026 alongside FSPs: a firm **monthly spend limit set per project in
the Cloud Billing console**, with automated email alerts at **50%, 80% and 100%** of the
limit. When a project hits its limit the agent's API calls temporarily pause; where
overages are enabled, excess usage transitions to consumption rates instead and can draw
against an FSP.

*Scope caveat:* the announcement describes this in the context of Gemini Enterprise
agent projects, not as a blanket control over all Agent Platform API traffic. Confirm it
covers the specific APIs you intend to cap before relying on it as the guardrail for an
estate. Source:
https://cloud.google.com/blog/products/ai-machine-learning/flexible-billing-and-cost-controls-for-agents-on-google-cloud

---

## Cost visibility and allocation

### GCP Billing and BigQuery export

GCP Billing exports to BigQuery are the standard mechanism for detailed cost analysis.
For Vertex AI:
- Enable detailed billing export to BigQuery
- Filter on `service.description = "Vertex AI"` for all Vertex costs
- Use `sku.description` to differentiate model inference, batch prediction, and
  provisioned throughput charges

**AI Cost Summary Agent:** GCP's AI Cost Summary Agent provides dedicated AI spend
analysis across Gemini API and Vertex AI services through a Billing Overview widget
(check current preview/GA status in the Cloud Billing docs before relying on it in
an engagement). This native tool addresses the AI cost
visibility gap, offering spend attribution and insights specifically for AI workloads.

**Originating products attribution (Cloud Billing):** as of August 2026, Cloud Billing
adds an "Originating products" filter/group-by dimension plus a Gemini Enterprise preset
report, giving more precise native attribution of AI-related consumption directly in
Billing Reports. It groups related SKUs and services into logical product families
independent of the underlying Google Cloud service, which is what makes it useful here:
Gemini Enterprise costs otherwise sit under the "Vertex AI Search" service and blend
into unrelated spend.

**Console only - it is not in the BigQuery export** (verified 20 September 2026). The
"Originating products" field has not been added to the billing export schema, and the
console's "Generate query" button is disabled when the dimension is in use. So this is
not a building block for a BigQuery dashboard: use it for interactive investigation in
Billing Reports, and fall back to `service.description` plus `sku.description` filters
for anything automated. Teams that standardise on the export will not see this dimension
at all, which is worth knowing before someone is asked to reproduce a console figure in
SQL. Sources: https://cloud.google.com/billing/docs,
https://docs.cloud.google.com/billing/docs/how-to/reports/gemini-enterprise-costs

**Limitation:** native billing does not provide token-level granularity per request.
For unit economics, combine billing data with application-level metrics from
Cloud Monitoring or your own instrumentation.

### Labels for cost allocation

GCP uses resource labels for cost allocation. Vertex AI API calls support labels via
request metadata: label information is forwarded to the billing system, can be filtered
and grouped in the built-in billing reports, and **can be queried in the BigQuery
billing export** (confirmed 20 September 2026). Apply labels at the API call level:
`feature`, `team`, `environment`. Labels attach to `generateContent` and
`streamGenerateContent` for Google models, and to `rawPredict` / `streamRawPredict` for
supported partner models - labelling a request to an unsupported model returns an error.

**The cardinality limit is an allocation trap.** Each label key may carry up to **1,000
unique values over the life of the billing account**, and beyond that *the key can be
dropped without notice*. A key like `session_id`, `user_id` or `request_id` will blow
through that in days, and the failure is silent: allocation simply stops arriving for
that key, and the spend lands in the unallocated bucket. Keep label keys to bounded
dimensions - team, environment, feature, cost centre - and push per-request identifiers
into application logs, where the earlier unit-economics pattern already puts them.
Limits are 64 labels per call for Google models, 32 for partner models.

Source:
https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/add-labels-to-api-calls

**Recommended allocation approach:**

| Allocation need | Method |
|---|---|
| Team / product attribution | GCP projects per team (preferred) or labels |
| Environment separation | Separate GCP projects (prod/dev/staging) |
| Workload-level unit economics | Application instrumentation + Cloud Monitoring |
| Provisioned capacity attribution | Labels on provisioned throughput resources |
| Feature-level inference attribution | API call labels -> BigQuery export + Cloud Monitoring |

**GCP project boundary advantage:** the GCP project is a stronger isolation mechanism
than AWS tags or Azure resource groups. It is enforced at the infrastructure level, not
through tag compliance. When in doubt, separate projects.

**Training job attribution:** for Vertex AI training jobs, enable detailed billing
export to BigQuery and filter on `service.description = "Vertex AI"`. Use
`sku.description` to separate training compute charges from inference charges.
Separate GCP projects per team make training costs directly attributable without
post-processing.

**Unit economics from labels:** combining API call labels with Cloud Monitoring metrics
(`aiplatform.googleapis.com/prediction/online/token_count`) and application-level
session logging enables per-feature cost calculations (e.g., cost per summarised
contract, cost per generated email) for margin modelling as usage scales.

### Cloud Monitoring metrics for Vertex AI

| Metric | Use |
|---|---|
| `aiplatform.googleapis.com/prediction/online/token_count` | Input/output token volume |
| `aiplatform.googleapis.com/prediction/online/request_count` | Request volume |
| `aiplatform.googleapis.com/prediction/online/latencies` | End-to-end latency |
| `aiplatform.googleapis.com/prediction/online/error_count` | Throttle and error signals |

---

## Cost optimisation patterns

### Model right-sizing

- Define a quality benchmark for your specific task
- Test Gemini Flash-Lite vs Gemini Flash vs Gemini Pro against that benchmark
- Use the lowest-cost model that meets your quality threshold
- For third-party models (Claude, Llama), apply the same benchmark process

### Prompt optimisation

- Audit system prompt length - verbose instructions inflate every API call
- Implement **Vertex AI Context Caching** where supported (current Gemini Flash and Pro models) - see below
- Truncate or summarize conversation history for multi-turn applications
- Avoid sending redundant context in RAG pipelines

### Vertex AI Context Caching - direct lever for long-context workloads

Vertex AI supports **explicit context caching** for selected Gemini models.
Equivalent in spirit to Anthropic / Bedrock prompt caching - cache a stable context
once, reuse it across many requests at a steeply discounted input-token rate - but
the pricing shape differs (verified August 2026):

**Mechanics** (verified 20 September 2026):
- **Two kinds of caching, and one of them is free.** *Implicit* caching is on by default
  for every GCP project and gives the same 90% discount on cached tokens **with no
  storage charge at all**. *Explicit* caching is the one you declare and manage, and the
  one that bills for storage. Before designing an explicit cache, check whether implicit
  hits are already covering the workload - placing large, stable content at the start of
  the prompt and sending similar-prefix requests close together is enough to raise the
  implicit hit rate, at zero storage cost.
- Cache write: charged at **standard input-token rates** - unlike Anthropic and
  Bedrock, there is no write premium.
- Cache **storage** (explicit only): bills per hour the cache is held, per cached token.
  The rate is flat across prompt size but varies by model class: **Pro SKUs cost 4.5x
  the Flash and Flash-Lite rate** per token-hour. This is the cost component to watch,
  and the one most often missed: a large cache held for hours can outweigh the read
  savings if traffic is thin. Current rates are on the pricing page; the ratio is the
  durable part.
- Cache hit (read): 90% off the standard input rate on 2.5-generation and later
  models (75% on 2.0-era models).
- TTL: default **60 minutes**, extendable through the API. Minimum lifetime 1 minute,
  no maximum. Maximum cacheable blob or text payload 10 MB.
- **Minimum cache size is now model-dependent** - the old flat 2,048-token floor only
  applies to the Gemini 2 family. Gemini 3 family models require **4,096 tokens**, and
  Gemini 3.0 Flash Preview, 3.1 Pro Preview, 3.7 Flash and 3.8 Flash require **6,144
  tokens** for implicit caching. A caching design sized against the old floor can
  silently fail to qualify after a model upgrade - the requests still succeed, they just
  stop being discounted, which shows up as a quiet unit-cost regression rather than an
  error.
- Caches work **across traffic types**: a cache created while using Provisioned
  Throughput also works with PayGo.

**Where it matters:**
- RAG pipelines with stable retrieved context across many user queries.
- Long system prompts (>1,000 tokens) reused across an interactive session.
- Agentic loops re-sending tool definitions and conversation history.
- Batch evaluation against a stable corpus.

**Where it does not help:**
- One-shot calls with unique input.
- Workloads where the context changes substantively each request.
- Models that do not support caching (verify per model and per region).

Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/context-cache/context-cache-overview

### Context window management

Monitor and alert on:
- Average input token count per request
- P95 and P99 input token counts
- Features or agents that silently inflate context (tool results, grounding results)

### Grounding and tool use costs

Web grounding and tool calls generate charges separate from token rates.
Track these as distinct cost dimensions, not as miscellaneous token overhead.

### Batch where latency is not required

Route non-interactive workloads to Batch Prediction for up to 50% token discount.
Candidates: document enrichment, bulk classification, evaluation pipelines.

### Flexible Savings Plans (FSPs) - commitment discounts on token spend

Announced 26 August 2026, **Gemini Enterprise Flexible Savings Plans** are spend-based
committed use discounts covering generative AI consumption. This is the first commitment
instrument that applies to pay-as-you-go *token* spend on GCP, so it changes a decision
that used to have only one answer.

**Mechanics** (verified 20 September 2026):

| Attribute | Detail |
|---|---|
| Commitment shape | A monthly spend amount, not a resource or a throughput unit |
| Terms and depth | **1 year = 10% off**, **3 years = 20% off** |
| Minimum / maximum | None |
| Who can buy | Self-serve through the Cloud console, and customers on enterprise agreements |
| Interaction with an EA | FSP spend draws down against the existing Google Cloud enterprise commitment rather than fragmenting it |

**Eligible for the discount:** Google first-party models such as Gemini, open-source
Model-as-a-Service offerings, and participating third-party foundation models available
through Vertex AI and Cloud Marketplace. The eligible-SKU group page is authoritative -
check it before sizing, because the boundary is where the money is.

**Draws down the commitment but earns no incremental discount:** Provisioned Throughput
subscriptions, full fine-tuning, the Gemini Enterprise app subscriptions (Business,
Standard, Plus, Frontline), Gemini Notebook Enterprise, and the on-device speech
subscriptions. This list is the one to internalise. It means a plan sized against total
Gemini spend will be *satisfied* by Provisioned Throughput and seat subscriptions while
discounting none of it - the commitment is met, and the saving never arrives.

**Not documented as eligible: the Gemini Developer API (AI Studio).** The FSP
documentation does not mention it either way. Treat that as undocumented rather than as
an exclusion, and confirm with your account team before assuming AI Studio spend counts.

**FinOps reading.** The discount is shallow next to compute CUDs (10-20% against up to
57% on resource-based CUDs) and the term is long next to the pace at which model prices
move - Gemini SKU rates changed several times during 2026, and three of them are
scheduled to double on 1 January 2027. The usual commitment discipline therefore applies
with more force, not less:

- Commit on **90+ days of observed stable spend**, at the **floor of the run-rate**,
  never on a forecast. Token spend is more volatile than compute spend, and a model
  migration can halve it overnight.
- **Decide FSP versus Provisioned Throughput on different grounds.** They are not
  competing discounts: PT buys latency and capacity assurance and draws down an FSP
  without discounting, while an FSP discounts the PAYG spend that PT does not cover. A
  steady workload usually wants PT for the baseline and an FSP sized only to the
  *remaining* on-demand tail.
- A **3-year plan on token spend carries model-price and model-mix drift risk** that a
  3-year compute CUD does not. Per-token prices fall as new SKUs land, and the discount
  is applied to spend, not to a rate - so a price cut mid-term erodes the commitment's
  value while the obligation stands. Write that risk down explicitly before signing;
  1-year at 10% is the defensible default unless spend is both large and demonstrably
  flat.
- **Maturity gate: not a Crawl-stage action.** An organisation without allocation,
  90 days of clean token-spend history and a settled model policy cannot size this
  safely. Get the Inform phase working first.

Sources: https://docs.cloud.google.com/docs/cuds-flexible-savings-plans,
https://cloud.google.com/skus/sku-groups/gemini-enterprise-flexible-savings-plan-eligible-skus,
https://cloud.google.com/blog/products/ai-machine-learning/flexible-billing-and-cost-controls-for-agents-on-google-cloud

See `finops-gcp.md` for spend-based CUDs on Compute Engine, which are a separate
instrument with different eligibility.

---

## Governance checklist

- [ ] Enable BigQuery billing export and configure Vertex AI cost dashboards
- [ ] Set up cost anomaly alerts in GCP Billing
- [ ] Define model selection policy - default to Gemini Flash unless higher capability is justified
- [ ] Instrument applications with token counts per request (input + output)
- [ ] Use GCP projects for team/environment cost separation
- [ ] Review provisioned throughput utilization monthly
- [ ] Track grounding and tool usage as separate cost centres
- [ ] Document which workloads use provisioned vs on-demand and why
- [ ] Establish a model review cadence - Vertex AI model catalog updates frequently
- [ ] Decide who may enable the Priority tier, and exclude batch jobs and CI from it
- [ ] Inventory Gemini Developer API (AI Studio) keys - free-tier content is used to
      improve Google products, so treat client data on a free key as a shadow-AI finding
- [ ] Separate billing accounts, or set project caps below the tier cap, so a runaway
      prototype cannot pause production
- [ ] Keep label keys to bounded dimensions - a key exceeding 1,000 unique values can be
      dropped without notice, silently breaking allocation
- [ ] Diarise the 1 January 2027 repricing of the 3.8 / 3.7 / 3.6 Flash SKUs in the
      budget, and re-size any FSP against the post-repricing run-rate

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
