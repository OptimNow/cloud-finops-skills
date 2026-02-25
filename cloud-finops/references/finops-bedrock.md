# FinOps on AWS Bedrock

> AWS Bedrock-specific guidance covering the billing model, model pricing, provisioned
> throughput, token cost management, cost allocation, and governance. Covers on-demand
> vs provisioned capacity trade-offs, model selection economics, cross-region inference,
> and cost visibility within AWS Cost Explorer.
>
> Distilled from: "Navigating GenAI Capacity Options" — FinOps Foundation GenAI Working Group, 2025/2026.
> See also: `finops-genai-capacity.md` for cross-provider capacity concepts.

---

## AWS Bedrock billing model overview

AWS Bedrock is a managed inference service that provides access to foundation models
from multiple publishers (Anthropic, Meta, Mistral, Amazon, Cohere, AI21, and others)
through a unified API.

### Billing dimensions

| Dimension | Description |
|---|---|
| Input tokens | Tokens sent in the prompt (including system prompt and context) |
| Output tokens | Tokens generated in the response |
| Model choice | Each model has its own per-token rate |
| Capacity model | On-demand (PAYG) vs Provisioned Throughput |
| Cross-region inference | Routes to alternate regions for availability; may affect cost |
| Batch inference | Asynchronous processing at discounted rates |

**Key cost driver:** output tokens are approximately 3× more computationally expensive
than input tokens. Workloads with high output ratios (agentic tasks, long-form generation)
carry disproportionately higher costs.

---

## Model pricing reference

### On-demand pricing structure

AWS Bedrock on-demand pricing is per-million tokens, billed per API call. There is no
minimum spend and no upfront commitment.

Pricing varies significantly by model and model size. Representative examples (verify
against current AWS pricing documentation):

| Model family | Relative cost tier | Typical use case |
|---|---|---|
| Amazon Nova Micro / Lite | Low | Classification, summarization, lightweight tasks |
| Amazon Nova Pro | Mid | General purpose, RAG, moderate reasoning |
| Meta Llama 3 (8B–70B) | Low–Mid | Open-weight, cost-sensitive workloads |
| Mistral (7B–Large) | Low–Mid | EU data residency, general purpose |
| Anthropic Claude Haiku | Low | High-volume, latency-tolerant tasks |
| Anthropic Claude Sonnet | Mid | Balanced capability and cost |
| Anthropic Claude Opus | High | Complex reasoning, agentic workflows |

**FinOps principle:** model selection is the single highest-leverage cost decision.
Benchmark task quality across model tiers before defaulting to the most capable model.

### Batch inference discount

AWS Bedrock Batch Inference processes requests asynchronously with up to 50% discount
on token rates. Use for:
- Bulk document processing
- Offline classification or enrichment pipelines
- Non-latency-sensitive evaluation workflows

**Constraint:** not suitable for interactive or real-time workloads.

---

## Provisioned throughput on AWS Bedrock

### How it works

On AWS Bedrock, provisioned throughput is purchased as **model-specific units** for a
fixed term (1 month or 6 months). Each unit provides a defined number of model units
(MUs) — a measure of throughput capacity for that specific model.

### Key characteristics

- **Model-locked:** you reserve capacity for a specific model (e.g., Claude Sonnet 4.5).
  If you want to switch to a newer model, you must wait for the reservation term to end
  or purchase additional capacity.
- **No spillover built in:** if provisioned capacity is exhausted, requests return HTTP 429
  unless you build custom failover logic to route overflow to on-demand.
- **Capacity guarantee:** unlike Azure PTUs, a Bedrock provisioned throughput purchase
  does guarantee availability of that model capacity.

### When provisioned throughput makes sense on Bedrock

| Condition | Recommendation |
|---|---|
| Consistent 24/7 workload, stable model choice | Strong candidate for provisioned |
| Latency-sensitive, user-facing application | Justified for TTFT/OTPS improvement |
| Data privacy requirement | Provisioned endpoints exclude data from training |
| Bursty or unpredictable traffic | On-demand or hybrid with manual failover logic |
| Workload likely to switch models within 6 months | Avoid — model lock is a real risk |

### Provisioned throughput governance checklist

- [ ] Confirm workload has run stably for 90+ days before committing
- [ ] Load-test to validate vendor TPM estimate against your actual input/output token mix
- [ ] Calculate break-even utilization (provisioned unit cost ÷ on-demand equivalent)
- [ ] Build failover logic to on-demand for overflow traffic (spillover is not built in)
- [ ] Set utilization alerts — target >80% to justify the reservation
- [ ] Assess model roadmap: is a better model likely within your commitment term?
- [ ] Apply existing AWS enterprise discounts — verify they apply to Bedrock reservations

---

## Cost visibility and allocation

### Cost Explorer integration

AWS Bedrock costs appear in AWS Cost Explorer under the Bedrock service namespace.
Key dimensions available for filtering and grouping:

- Model ID
- Operation type (InvokeModel, InvokeModelWithResponseStream, BatchInference)
- Region
- Account (for multi-account organizations)

**Limitation:** native Cost Explorer does not provide token-level granularity. For
unit economics (cost per 1,000 tokens, cost per API call), you need to combine billing
data with application-level metrics from CloudWatch or your own instrumentation.

### Tagging strategy for Bedrock

AWS Bedrock supports resource tagging on provisioned throughput resources. On-demand
API calls are attributed at the account/region level.

**Recommended allocation approach:**

| Allocation need | Method |
|---|---|
| Team / product attribution | Separate AWS accounts per team (preferred) or cost allocation tags |
| Environment separation | Separate accounts (prod/dev/staging) |
| Workload-level unit economics | Application-level instrumentation + CloudWatch metrics |
| Provisioned capacity attribution | Tags on provisioned throughput resources |

### CloudWatch metrics for Bedrock

Key metrics to monitor for cost and performance:

| Metric | Use |
|---|---|
| `InputTokenCount` | Track input token volume by model |
| `OutputTokenCount` | Track output token volume by model |
| `InvocationLatency` | End-to-end latency baseline |
| `InvocationsThrottled` | Signals capacity exhaustion (on-demand or provisioned) |
| `ProvisionedModelThroughputUtilization` | Utilization of provisioned capacity (target >80%) |

---

## Cost optimization patterns

### Model right-sizing

The highest-impact optimization. Before committing to a model tier:
- Define a quality benchmark for your specific task (not a generic leaderboard score)
- Test Haiku, Sonnet, and Opus (or equivalent tiers for other publishers) against that benchmark
- Use the lowest-cost model that meets your quality threshold

### Prompt optimization

Input token volume is directly controllable:
- Audit system prompt length — verbose instructions inflate every API call
- Implement prompt caching where supported (reduces repeated context costs)
- Truncate or summarize conversation history for multi-turn applications
- Avoid sending redundant context in retrieval-augmented generation (RAG) pipelines

### Context window management

Longer context = higher input token cost per call. Monitor:
- Average input token count per request
- P95 and P99 input token counts (outliers can dominate cost)
- Features or agents that silently inflate context (tool results, retrieval dumps)

### Batch where latency is not required

Route non-interactive workloads to Batch Inference for up to 50% token discount.
Candidates: document enrichment, bulk classification, evaluation pipelines, report generation.

---

## Governance checklist

- [ ] Enable Cost Explorer for Bedrock and set up daily cost anomaly alerts
- [ ] Define model selection policy — default to lower-cost tiers unless justified
- [ ] Instrument applications with token counts per request (input + output)
- [ ] Separate accounts or use tags for team/product cost attribution
- [ ] Review provisioned throughput utilization monthly
- [ ] Establish a model review cadence — AWS Bedrock model catalog changes frequently
- [ ] Document which workloads use provisioned vs on-demand capacity and why

---
