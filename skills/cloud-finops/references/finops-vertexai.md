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

> GCP Vertex AI-specific guidance covering the billing model, model pricing, provisioned
> throughput, cost allocation, and governance. Covers on-demand vs provisioned capacity
> trade-offs, publisher-scoped reservation flexibility, Committed Use Discounts (CUDs),
> and cost visibility within GCP Billing and BigQuery.
>
> Distilled from: "Navigating GenAI Capacity Options" - FinOps Foundation GenAI Working Group, 2025/2026.
> See also: `finops-genai-capacity.md` for cross-provider capacity concepts.

---

## GCP Vertex AI billing model overview

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

**Key cost driver:** output tokens are approximately 3× more computationally expensive
than input tokens. High output-ratio workloads (agentic tasks, long-form generation)
carry disproportionately higher costs.

---

## Model pricing reference

### On-demand pricing structure - tokens AND characters

Vertex AI on-demand pricing is per-million tokens for newer Gemini SKUs. **However,
some Gemini APIs and earlier model versions still bill per 1,000 characters (input
and output)** rather than per token. This is a real difference from AWS / OpenAI /
Anthropic, which all bill per token.

**Practical implications:**
- Capacity-planning math from Anthropic or OpenAI engagements does not transpose
  cleanly: 1,000 characters is roughly 250 tokens for English (ratio varies per
  language - East Asian scripts can be 1:1 character-to-token, English is ~4:1).
- Verify the unit on Vertex's pricing page per model before quoting. Two Gemini
  variants on the same product family can use different units depending on model
  version and surface (Vertex Studio, Vertex API, Gemini API).
- For multilingual workloads, the character-based pricing is sometimes cheaper
  than the token-based equivalent (the per-character rate can favour languages
  that tokenise unfavourably under English-trained tokenisers).

Source: https://cloud.google.com/vertex-ai/generative-ai/pricing

No minimum spend, no upfront commitment, regardless of unit.

| Model family | Relative cost tier | Notes |
|---|---|---|
| Gemini Flash (1.5, 2.0) | Low | High throughput, cost-optimised |
| Gemini Pro (1.5, 2.0) | Mid | Balanced capability and cost |
| Gemini Ultra / Advanced | High | Complex reasoning, multimodal |
| Anthropic Claude Haiku | Low | Available via Vertex Model Garden |
| Anthropic Claude Sonnet | Mid | Available via Vertex Model Garden |
| Anthropic Claude Opus | High | Available via Vertex Model Garden |
| Meta Llama (various) | Low–Mid | Open-weight, available in Model Garden |

**FinOps principle:** model selection is the single highest-leverage cost decision.
Benchmark task quality across model tiers before defaulting to the most capable model.

### Batch prediction discount

Vertex AI Batch Prediction processes requests asynchronously at discounted token rates
(typically 50% off on-demand). Use for:
- Bulk document processing and enrichment
- Offline classification pipelines
- Non-latency-sensitive evaluation workflows

**Constraint:** async processing only - not suitable for interactive workloads.

---

## Provisioned throughput on GCP Vertex AI

### How it works

On GCP Vertex AI, provisioned throughput is purchased as **publisher-specific capacity**
for a fixed term. You reserve throughput for a specific publisher (e.g., Google, Anthropic)
and can switch between models within that publisher's portfolio.

### Key characteristics

- **Publisher-locked, model-flexible:** you can switch from Gemini 2.0 Pro to Gemini 2.0 Flash
  within the same reservation, but cannot switch from a Google model to an Anthropic model.
- **Capacity floor, not ceiling:** you cannot reduce reserved capacity mid-term, even if
  a newer model becomes more efficient. Efficiency gains reduce your effective cost per
  output, but the reservation commitment remains at the original size.
- **Default spillover to pay-as-you-go.** As of current Google docs, supported Gemini
  Provisioned Throughput overages are billed as pay-as-you-go by default. Request
  headers control whether traffic is routed to dedicated capacity, shared/on-demand,
  or rejected. This is a material change vs the older "build your own failover"
  pattern - capacity planning can size reservations to average load, with overage
  becoming variable PAYG cost during spikes. Sources:
  https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput/use-provisioned-throughput,
  https://docs.cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput/supported-models
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
| Data privacy requirement | Provisioned endpoints exclude data from training |
| Likely to upgrade Gemini versions mid-term | GCP reservation accommodates this |
| Workload requiring cross-publisher flexibility | Azure PTU model better suited |
| Bursty or unpredictable traffic | On-demand or hybrid with manual failover |

### Provisioned throughput governance checklist

- [ ] Confirm workload has run stably for 90+ days before committing
- [ ] Load-test to validate vendor TPM estimate against actual input/output token mix
- [ ] Calculate break-even utilization (provisioned unit cost ÷ on-demand equivalent)
- [ ] Verify reserved publisher matches the model families your workloads will use
- [ ] Build failover logic to on-demand for overflow traffic (spillover is not built in)
- [ ] Set utilization alerts - target >80% to justify the reservation
- [ ] Assess whether new model efficiency gains offset the fixed capacity floor

---

## Cost visibility and allocation

### GCP Billing and BigQuery export

GCP Billing exports to BigQuery are the standard mechanism for detailed cost analysis.
For Vertex AI:
- Enable detailed billing export to BigQuery
- Filter on `service.description = "Vertex AI"` for all Vertex costs
- Use `sku.description` to differentiate model inference, batch prediction, and
  provisioned throughput charges

**AI Cost Summary Agent (Preview):** As of May 2026, GCP launched the AI Cost Summary
Agent in preview, providing dedicated AI spend analysis across Gemini API and Vertex AI
services through a Billing Overview widget. This native tool addresses the AI cost
visibility gap, offering spend attribution and insights specifically for AI workloads.

**Limitation:** native billing does not provide token-level granularity per request.
For unit economics, combine billing data with application-level metrics from
Cloud Monitoring or your own instrumentation.

### Labels for cost allocation

GCP uses resource labels for cost allocation. Vertex AI API calls support labels via
request metadata, which propagate to BigQuery billing exports. Apply labels at the
API call level: `feature`, `team`, `environment`.

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
- Test Gemini Flash vs Gemini Pro vs Gemini Ultra against that benchmark
- Use the lowest-cost model that meets your quality threshold
- For third-party models (Claude, Llama), apply the same benchmark process

### Prompt optimisation

- Audit system prompt length - verbose instructions inflate every API call
- Implement **Vertex AI Context Caching** where supported (Gemini Pro, Flash 1.5+) - see below
- Truncate or summarize conversation history for multi-turn applications
- Avoid sending redundant context in RAG pipelines

### Vertex AI Context Caching - direct lever for long-context workloads

Vertex AI supports **explicit context caching** for selected Gemini models (Gemini
Pro, Flash 1.5 and later). Equivalent in spirit to Anthropic / Bedrock prompt
caching - cache a stable context once, reuse it across many requests at a steeply
discounted input-token rate.

**Mechanics:**
- Cache write: priced per cached token (or character) at a small premium over the
  base input rate.
- Cache hit (read): priced at a meaningfully lower rate than full input.
- TTL: configurable cache lifetime (typically minutes to hours, model-dependent).
- Minimum context size: caching is only beneficial above a token / character
  threshold the model documents - small contexts do not break even.

**Where it matters:**
- RAG pipelines with stable retrieved context across many user queries.
- Long system prompts (>1,000 tokens) reused across an interactive session.
- Agentic loops re-sending tool definitions and conversation history.
- Batch evaluation against a stable corpus.

**Where it does not help:**
- One-shot calls with unique input.
- Workloads where the context changes substantively each request.
- Models that do not support caching (verify per model and per region).

Source: https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview

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

### Committed Use Discounts (CUDs)

GCP offers CUDs on some Vertex AI workloads. Evaluate CUDs for:
- Sustained, predictable inference volume
- Workloads that have already validated their traffic shape over 90+ days

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

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
