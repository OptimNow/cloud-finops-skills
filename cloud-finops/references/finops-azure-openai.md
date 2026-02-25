# FinOps on Azure OpenAI Service

> Azure OpenAI Service-specific guidance covering the billing model, PTU (Provisioned
> Throughput Unit) reservations, standard token pricing, spillover mechanics, cost
> allocation, and governance. Covers the PTU pool model, unallocated capacity waste,
> model deployment management, and cost visibility within Azure Cost Management.
>
> Distilled from: "Navigating GenAI Capacity Options" — FinOps Foundation GenAI Working Group, 2025/2026.
> See also: `finops-genai-capacity.md` for cross-provider capacity concepts.
> See also: `finops-azure.md` for general Azure FinOps guidance.

---

## Azure OpenAI Service billing model overview

Azure OpenAI Service (AOAI) provides access to OpenAI models (GPT-4o, GPT-4.1, GPT-5,
o-series reasoning models, DALL-E, Whisper, and others) through Azure's infrastructure.
It is separate from OpenAI's direct API — billing, compliance, and capacity management
are handled through Azure.

### Billing dimensions

| Dimension | Description |
|---|---|
| Input tokens | Tokens in the prompt, including system prompt and context |
| Output tokens | Tokens generated in the response |
| Cached input tokens | Input tokens served from prompt cache (discounted rate) |
| Model choice | Each model has its own per-token rate |
| Capacity model | Standard (PAYG) vs Provisioned Throughput Units (PTUs) |
| Fine-tuning | Training token charges + hosting charges for fine-tuned deployments |
| Image / audio | Billed in units (images per resolution, audio per second) — separate from tokens |

**Key cost driver:** output tokens are approximately 3× more computationally expensive
than input tokens. High output-ratio workloads carry disproportionately higher costs.

---

## Model pricing reference

### Standard (pay-as-you-go) pricing

Standard pricing is per-million tokens, billed per API call. No upfront commitment.

| Model | Relative cost tier | Notes |
|---|---|---|
| GPT-4o mini | Low | High-volume, cost-sensitive workloads |
| GPT-4.1 mini | Low | Lightweight tasks, classification |
| GPT-4o | Mid | General purpose, balanced capability/cost |
| GPT-4.1 | Mid | Updated GPT-4 generation |
| GPT-5 | High | Complex reasoning, frontier capability |
| o3-mini | Mid | Reasoning model, cost-optimized |
| o3 | High | Full reasoning model |

Representative pricing (verify against current Azure pricing documentation):

| Model | Standard input | Cached input | Standard output |
|---|---|---|---|
| GPT-5 | $1.25/MTok | $0.125/MTok | $10.00/MTok |
| GPT-4.1 | $2.00/MTok | $0.50/MTok | $8.00/MTok |

### Provisioned (Scale Tier) pricing vs standard

| Model | Standard input | Provisioned input | Delta at 100% utilization |
|---|---|---|---|
| GPT-5 | $1.25/MTok | $2.08/MTok | +67% |
| GPT-4.1 | $2.00/MTok | $2.55/MTok | +27% |

**Critical insight:** for GPT-5, provisioned capacity is more expensive per token even
at 100% utilization. Provisioned capacity on Azure OpenAI is primarily a performance
and SLA purchase, not a cost-saving mechanism for all models.

---

## Provisioned Throughput Units (PTUs)

### How the PTU model works

Azure OpenAI Service uses a **pool-based reservation model**. You purchase a block of
PTUs for a fixed term (monthly or annual). PTUs are generic capacity units — not tied
to a specific model at purchase time.

You then **deploy models against that pool**, assigning a number of PTUs to each deployment.
Different models have different PTU minimums to operate effectively, with larger models
requiring more PTUs.

**Example:**
- Reserve 500 PTUs
- Deploy: 100 PTUs → GPT-4o, 50 PTUs → GPT-4.1 mini
- Remaining 350 PTUs: unallocated (waste) unless assigned to additional deployments

### Key characteristics

- **Full model flexibility:** when a new model is released, retire the old deployment
  and reassign its PTUs to the new model — no new reservation required
- **Decoupled reservation and deployment:** a PTU reservation does not guarantee that
  model capacity will be available for your chosen model
- **Built-in spillover:** overflow traffic automatically routes to standard (PAYG) tier
  instead of returning HTTP 429
- **Two waste types:** idle allocated capacity (PTUs assigned but underutilized) and
  unallocated capacity (PTUs reserved but not assigned to any deployment)

### PTU deployment guidance from Azure

Azure recommends: **deploy models first, then make the reservation**. This validates
model availability before committing spend. For existing reservations, switching models
requires waiting for capacity availability, which can leave PTUs unallocated and paid
for during the wait.

### When PTUs make sense on Azure OpenAI

| Condition | Recommendation |
|---|---|
| Consistent 24/7 workload, latency-sensitive | Strong candidate |
| Frequent model updates expected | PTU flexibility is the key advantage here |
| Data privacy / PII requirement | Provisioned endpoints exclude data from training |
| Bursty traffic with spillover tolerance | Acceptable — spillover is built in |
| Cost reduction as primary goal (GPT-5) | Caution — provisioned may be more expensive |
| Cost reduction as primary goal (GPT-4.1) | Viable at high utilization (+27% at 100%) |

### PTU governance checklist

- [ ] Deploy models first — validate capacity availability before purchasing reservation
- [ ] Calculate break-even utilization for each model (provisioned ÷ standard per-token rate)
- [ ] Load-test to validate effective throughput against your actual token mix
- [ ] Monitor unallocated PTUs — set alerts when PTUs are reserved but undeployed
- [ ] Monitor allocated PTU utilization — target >80%
- [ ] Define spillover policy: what percentage of requests can route to PAYG within SLA?
- [ ] Set spending alerts on PAYG spillover costs (variable component of a provisioned setup)
- [ ] Apply existing Azure EA discounts — verify they apply to PTU reservations

---

## Spillover mechanics

Azure is currently the only hyperscaler with built-in spillover for GenAI capacity.

When provisioned capacity is fully utilized, overflow requests automatically route to
the standard PAYG tier. No HTTP 429 errors are returned unless both provisioned and
PAYG capacity are exhausted.

### Spillover cost implications

- Spillover requests are billed at standard PAYG rates — the variable component of your bill
- Spillover volume depends on traffic spikes relative to your PTU allocation
- Monitor spillover rate to determine whether PTU allocation needs adjustment

### Using spillover to right-size reservations

Spillover allows you to size PTU reservations for **average load**, not peak load.
This is equivalent to the Savings Plan / CUD approach in traditional cloud:
- Set a coverage target (e.g., 70-80% of requests served by PTUs)
- Let spillover handle peaks at PAYG rates
- Adjust PTU allocation over time as traffic patterns evolve

---

## Cost visibility and allocation

### Azure Cost Management integration

Azure OpenAI Service costs appear in Azure Cost Management under the
`Cognitive Services` or `Azure OpenAI` service namespace depending on resource type.

Key filtering dimensions:
- Resource name (OpenAI resource / deployment)
- Meter name (Standard tokens, PTU reservation, fine-tuning)
- Subscription / Resource Group
- Tags

**Limitation:** native Cost Management does not provide token-level granularity per
request. For unit economics, combine billing data with Azure Monitor metrics or
application-level instrumentation.

### Tagging strategy for Azure OpenAI

Azure OpenAI resources support standard Azure resource tags. Apply tags at the
resource level (not deployment level) for Cost Management attribution.

**Recommended allocation approach:**

| Allocation need | Method |
|---|---|
| Team / product attribution | Separate resource groups or subscriptions per team |
| Environment separation | Separate subscriptions (prod/dev/staging) |
| Workload-level unit economics | Application instrumentation + Azure Monitor |
| PTU allocation tracking | Deployment-level monitoring in Azure OpenAI Studio |

### Azure Monitor metrics for OpenAI

| Metric | Use |
|---|---|
| `TokenTransaction` | Input/output token volume by model and deployment |
| `ProvisionedUtilizationRate` | PTU utilization (target >80%) |
| `AzureOpenAIRequests` | Request volume |
| `SuccessfulRequests` | Baseline for error rate calculation |
| `RateLimitErrors` | Signals capacity exhaustion in PAYG or PTU |

---

## Cost optimization patterns

### Model right-sizing

- Define a quality benchmark for your specific task
- Test GPT-4o mini / GPT-4.1 mini before defaulting to GPT-4o or GPT-5
- Reasoning models (o3-mini vs o3) have significant cost differences — benchmark both
- Use the lowest-cost model that meets your quality threshold

### Prompt caching

Azure OpenAI supports prompt caching (cached input tokens billed at ~75% discount).
Effective for:
- Long, repeated system prompts
- RAG pipelines with consistent prefixes
- Multi-turn conversations with stable context

### Prompt optimization

- Audit system prompt length — verbose instructions inflate every API call
- Truncate or summarize conversation history for multi-turn applications
- Avoid sending redundant context in RAG pipelines

### Context window management

Monitor and alert on:
- Average input token count per request
- P95 and P99 input token counts
- Agents or features that silently inflate context (tool results, retrieval dumps)

### Fine-tuning cost awareness

Fine-tuned model deployments incur both training token charges (one-time) and
ongoing hosting charges (per hour, even when idle). Track these separately from
inference token costs.

### Azure Hybrid Benefit and MACC

Azure OpenAI Service spend can count toward Microsoft Azure Consumption Commitments
(MACC) in enterprise agreements. Verify this with your Microsoft account team —
it affects how GenAI spend is credited against existing commitments.

---

## Governance checklist

- [ ] Enable Azure Cost Management for OpenAI resources and configure daily anomaly alerts
- [ ] Define model selection policy — default to lower-cost tiers unless justified
- [ ] Instrument applications with token counts per request (input + output + cached)
- [ ] Use resource groups or subscriptions for team/environment cost separation
- [ ] Tag all OpenAI resources with owner, team, environment, and cost centre
- [ ] Monitor PTU utilization and unallocated PTUs monthly
- [ ] Track spillover volume and cost as a separate budget line
- [ ] Review fine-tuned model hosting charges — decommission idle fine-tuned deployments
- [ ] Verify whether OpenAI spend counts toward MACC commitments
- [ ] Establish a model review cadence — Azure OpenAI model catalog updates frequently

---
