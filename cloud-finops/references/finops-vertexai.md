# FinOps on GCP Vertex AI

> GCP Vertex AI-specific guidance covering the billing model, model pricing, provisioned
> throughput, cost allocation, and governance. Covers on-demand vs provisioned capacity
> trade-offs, publisher-scoped reservation flexibility, Committed Use Discounts (CUDs),
> and cost visibility within GCP Billing and BigQuery.
>
> Distilled from: "Navigating GenAI Capacity Options"  - FinOps Foundation GenAI Working Group, 2025/2026.
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

### On-demand pricing structure

Vertex AI on-demand pricing is per-million tokens, billed per API call. No minimum spend,
no upfront commitment.

| Model family | Relative cost tier | Notes |
|---|---|---|
| Gemini Flash (1.5, 2.0) | Low | High throughput, cost-optimized |
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

**Constraint:** async processing only  - not suitable for interactive workloads.

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
- **No spillover built in:** overflow traffic returns HTTP 429 unless you build custom
  failover logic to route excess to on-demand capacity.
- **Capacity guarantee:** a Vertex AI reservation guarantees capacity availability for
  models within the reserved publisher family.

### Comparison to AWS Bedrock and Azure

| Dimension | GCP Vertex AI | AWS Bedrock | Azure OpenAI |
|---|---|---|---|
| Flexibility | Publisher-scoped | Model-locked | Full PTU pool |
| Model upgrade within reservation | Yes (same publisher) | No | Yes (any model) |
| Publisher switch within reservation | No | No | Yes |
| Spillover | Build yourself | Build yourself | Built-in |

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
- [ ] Set utilization alerts  - target >80% to justify the reservation
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

**Limitation:** native billing does not provide token-level granularity per request.
For unit economics, combine billing data with application-level metrics from
Cloud Monitoring or your own instrumentation.

### Labels for cost allocation

GCP uses resource labels for cost allocation. Vertex AI API calls can be tagged via
request metadata.

**Recommended allocation approach:**

| Allocation need | Method |
|---|---|
| Team / product attribution | GCP projects per team (preferred) or labels |
| Environment separation | Separate GCP projects (prod/dev/staging) |
| Workload-level unit economics | Application instrumentation + Cloud Monitoring |
| Provisioned capacity attribution | Labels on provisioned throughput resources |

### Cloud Monitoring metrics for Vertex AI

| Metric | Use |
|---|---|
| `aiplatform.googleapis.com/prediction/online/token_count` | Input/output token volume |
| `aiplatform.googleapis.com/prediction/online/request_count` | Request volume |
| `aiplatform.googleapis.com/prediction/online/latencies` | End-to-end latency |
| `aiplatform.googleapis.com/prediction/online/error_count` | Throttle and error signals |

---

## Cost optimization patterns

### Model right-sizing

- Define a quality benchmark for your specific task
- Test Gemini Flash vs Gemini Pro vs Gemini Ultra against that benchmark
- Use the lowest-cost model that meets your quality threshold
- For third-party models (Claude, Llama), apply the same benchmark process

### Prompt optimization

- Audit system prompt length  - verbose instructions inflate every API call
- Implement context caching where supported (Vertex AI supports context caching for Gemini)
- Truncate or summarize conversation history for multi-turn applications
- Avoid sending redundant context in RAG pipelines

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
- [ ] Define model selection policy  - default to Gemini Flash unless higher capability is justified
- [ ] Instrument applications with token counts per request (input + output)
- [ ] Use GCP projects for team/environment cost separation
- [ ] Review provisioned throughput utilization monthly
- [ ] Track grounding and tool usage as separate cost centres
- [ ] Document which workloads use provisioned vs on-demand and why
- [ ] Establish a model review cadence  - Vertex AI model catalog updates frequently

---

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io)  - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
