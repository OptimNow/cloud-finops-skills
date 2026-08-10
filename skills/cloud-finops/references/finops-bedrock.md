---
name: finops-bedrock
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Rate Optimization"]
fcp_phases: ["Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Product", "Finance"]
fcp_maturity_entry: "Walk"
---

# FinOps on AWS Bedrock

> AWS Bedrock-specific guidance covering the billing model, model pricing, provisioned
> throughput, token cost management, cost allocation, and governance. Covers on-demand
> vs provisioned capacity trade-offs, model selection economics, cross-region inference,
> and cost visibility within AWS Cost Explorer.
>
> Distilled from: "Navigating GenAI Capacity Options" - FinOps Foundation GenAI Working Group, 2025/2026.
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
| Cross-region inference | Routes to alternate regions for availability; may affect cost. For Claude 4.5+ models, regional endpoints carry a 10% premium over global endpoints |
| Batch inference | Asynchronous processing at discounted rates |

**Key cost driver:** output tokens are billed at roughly 4-5x the input rate on
current Bedrock models (4x on Amazon Nova, 5x on Claude - e.g. Claude Sonnet $3/$15
per MTok). Workloads with high output ratios (agentic tasks, long-form generation)
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

On AWS Bedrock, provisioned throughput is purchased as **model-specific units**, either
with **no commitment** (billed hourly, deletable at any time) or for a fixed term
(1 month or 6 months, with deeper hourly discounts for the longer term). Each purchase
provides a defined number of model units (MUs) - a measure of throughput capacity for
that specific model. The no-commitment option changes the risk profile below: model
lock and utilisation risk apply to the term commitments, not to hourly provisioned
capacity spun up for a burst.

### Key characteristics

- **Model-locked:** you reserve capacity for a specific model (e.g., Claude Sonnet 4.5).
  If you want to switch to a newer model, you must wait for the reservation term to end
  or purchase additional capacity.
- **No spillover built in:** if provisioned capacity is exhausted, requests return HTTP 429
  unless you build custom failover logic to route overflow to on-demand.
- **Capacity guarantee:** a Bedrock provisioned throughput purchase guarantees a
  specific throughput level (input plus output tokens per minute) for that model.

### When provisioned throughput makes sense on Bedrock

| Condition | Recommendation |
|---|---|
| Consistent 24/7 workload, stable model choice | Strong candidate for provisioned |
| Latency-sensitive, user-facing application | Justified for TTFT/OTPS improvement |
| Data privacy requirement | Not a provisioned differentiator - Bedrock does not expose prompts or completions to model providers on any capacity mode |
| Bursty or unpredictable traffic | On-demand or hybrid with manual failover logic |
| Workload likely to switch models within 6 months | Avoid - model lock is a real risk |

### Provisioned throughput governance checklist

- [ ] Confirm workload has run stably for 90+ days before committing
- [ ] Load-test to validate vendor TPM estimate against your actual input/output token mix
- [ ] Calculate break-even utilization (provisioned unit cost ÷ on-demand equivalent)
- [ ] Build failover logic to on-demand for overflow traffic (spillover is not built in)
- [ ] Set utilization alerts - target >80% to justify the reservation
- [ ] Assess model roadmap: is a better model likely within your commitment term?
- [ ] Apply existing AWS enterprise discounts - verify they apply to Bedrock reservations

---

## Cost visibility and allocation

### Cost Explorer integration

AWS Bedrock costs appear in AWS Cost Explorer under the Bedrock service namespace.
Key dimensions available for filtering and grouping:

- Model ID
- Operation type (InvokeModel, InvokeModelWithResponseStream, BatchInference)
- Region
- Account (for multi-account organisations)

**Limitation:** native Cost Explorer does not provide token-level granularity. For
unit economics (cost per 1,000 tokens, cost per API call), you need to combine billing
data with application-level metrics from CloudWatch or your own instrumentation.

### Tagging strategy for Bedrock

AWS Bedrock supports resource tagging on provisioned throughput resources. For on-demand
API calls, attribution historically required account separation or application-level
instrumentation. As of 2026, **IAM Principal Cost Allocation** adds a native attribution
path by recording the caller's IAM principal ARN on every billed line item.

**Recommended allocation approach:**

| Allocation need | Method |
|---|---|
| Team / product attribution | Separate AWS accounts per team, or IAM Principal Cost Allocation with team/cost-centre tags on IAM roles |
| Environment separation | Separate accounts (prod/dev/staging) |
| Workload-level unit economics | Application-level instrumentation + CloudWatch metrics |
| Per-user / per-role attribution on shared account | IAM Principal Cost Allocation (see below) |
| Provisioned capacity attribution | Tags on provisioned throughput resources |

#### IAM Principal Cost Allocation

When enabled, AWS records the calling IAM principal ARN for each Bedrock API call and
propagates tags applied to that principal into the Cost and Usage Report and Cost Explorer.

**How it shows up in CUR 2.0:**

- A caller-identity column containing the ARN of the caller (IAM user, role, or
  assumed-role session) - verify the exact column name in your export, as AWS
  documentation describes the mechanism without naming the column
- Tags applied to the IAM principal appear with an `iamPrincipal/` prefix  -
  e.g. `iamPrincipal/team`, `iamPrincipal/cost-centre`, `iamPrincipal/environment`
- In Cost Explorer, these tags become available as a grouping and filter dimension

**Activation (three steps, ~48h end-to-end):**

1. Apply tags to IAM users and roles in the IAM console
2. Activate those tag keys in Billing > Cost Allocation Tags (up to 24h propagation)
3. Enable "Include caller identity (IAM principal) allocation data" in CUR 2.0 Data Exports

**Structural consequences to plan for:**

- **CUR size grows significantly.** Row count multiplies roughly by the number of distinct
  calling principals per model per day. Budget for larger S3 storage, longer Athena scans,
  and potentially higher query cost on CUR
- Tags only become visible after the principal has made at least one API call - new roles
  will not appear in cost allocation UI until used
- Follow standard tag hygiene: avoid high-cardinality values (session IDs, timestamps,
  GUIDs) as they inflate CUR without analytical value
- The feature gives visibility, not chargeback automation - downstream showback or
  chargeback still needs to be built on top of the CUR

**Coverage caveat:** some Bedrock features do not execute under the calling IAM role.
**Guardrails** usage, notably, may appear in CUR without the caller-identity value -
only resource tags carry the attribution (unconfirmed in AWS documentation; validate
in your own CUR before relying on it). IAM Principal Cost Allocation therefore does
not eliminate the tagging requirement: teams still need tag discipline for guardrails
and similar non-principal line items. Note that a CUR 2.0 export created **before**
enabling IAM principal attribution must be **recreated** - existing exports do not
retroactively include identity data.

**When to use it vs. account separation:**

| Scenario | Preferred approach |
|---|---|
| Multiple teams share one account and need per-team Bedrock attribution | IAM Principal Cost Allocation |
| Teams need independent budgets, IAM boundaries, and quota ceilings | Separate accounts |
| Per-user chargeback inside a team (e.g. internal AI sandbox) | IAM Principal Cost Allocation on user tags |
| Per-feature attribution inside a single application | Still needs SDK/proxy wrapper - IAM principal is too coarse |

**Feature-level attribution (still relevant):** IAM principals identify *who* called the
API, not *which feature*. For per-feature unit economics inside one application, keep
using an SDK wrapper that attaches feature/tier/model metadata and combines with
CloudWatch `InputTokenCount` / `OutputTokenCount` metrics.

#### Application Inference Profiles - native per-application attribution

AWS introduced **Application Inference Profiles** as the first-party way to attribute
Bedrock costs across applications, features, or teams without an SDK wrapper. An
Application Inference Profile is a tagged inference profile that callers reference
instead of (or in addition to) raw model IDs - the tags propagate to CUR 2.0 and
Cost Explorer alongside `line_item_iam_principal`.

**What this unlocks that IAM Principal alone does not:**
- **Cross-region inference attribution.** Cross-region inference profiles route to
  alternate regions for availability. Without an Application Inference Profile, the
  resulting cost lines do not carry the originating application context. With one,
  the application tag survives the cross-region routing.
- **Per-feature attribution within a single IAM principal.** A single role can call
  Bedrock from multiple features, each via a different Application Inference Profile,
  and CUR will distinguish them.
- **Tag-based budget alerts at the application level**, not just the principal level.

**Setup pattern:**

1. Create an inference profile per application (or per feature within an application)
   with tags like `application`, `feature`, `cost-centre`, `environment`.
2. Update application code to call Bedrock with the inference profile ARN instead of
   the raw model ID.
3. Activate the relevant tag keys in Billing > Cost Allocation Tags.
4. Verify tags appear in CUR 2.0 and Cost Explorer (24-48h propagation).

**When to choose IAM Principal vs Application Inference Profiles:**

| Scenario | Preferred approach |
|---|---|
| Per-user chargeback or shared-account team attribution | IAM Principal Cost Allocation |
| Per-application or per-feature unit economics | Application Inference Profiles |
| Cross-region inference cost attribution | Application Inference Profiles (only path) |
| Maximum granularity | Both - they compose (principal X via app Y) |

Sources: https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-application-inference-profiles.html, https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-understanding-cur-data.html

#### Bedrock Projects (organisational primitive, not a billing primitive)

Bedrock **Projects** group agents, knowledge bases, prompt flows, and other resources
under a named container with shared IAM and resource policies. Since this section was
first written, Projects have grown into a **billing attribution primitive** as well:
tags assigned to a Bedrock Project are now listed as a first-class cost-attribution
method in CUR, and AWS recommends Projects for application-level attribution on the
newer Bedrock APIs. Cost attribution therefore flows through four channels: IAM
principals, resource tags, Application Inference Profiles, and Project tags.

Useful FinOps angle: when a team adopts Projects, standardise the project name as a
tag value across IAM roles and Application Inference Profiles under that project, so
the project tag in CUR and the principal/profile tags reconcile cleanly.

### SageMaker training job allocation

SageMaker training jobs support resource tagging at job creation. Apply tags for `team`,
`project`, `environment`, and `cost-centre` directly on the training job. These tags
propagate to Cost Explorer and the Cost and Usage Report (CUR), enabling per-project GPU
spend breakdowns without post-processing.

Account-level separation remains the cleanest boundary for training workloads. One AWS
account per team or product line eliminates tag compliance risk - costs flow to the right
owner by construction, not by discipline.

### CloudWatch metrics for Bedrock

Key metrics to monitor for cost and performance:

| Metric | Use |
|---|---|
| `InputTokenCount` | Track input token volume by model |
| `OutputTokenCount` | Track output token volume by model |
| `InvocationLatency` | End-to-end latency baseline |
| `InvocationsThrottled` | Signals capacity exhaustion (on-demand or provisioned) |
| `ProvisionedModelThroughputUtilization` | Utilization of provisioned capacity (target >80%) |

### Bedrock model invocation logging - the missing FinOps data source

By default, Bedrock emits only high-level aggregates to CloudWatch (token counts and
latency per model). **Model invocation logging** is off by default, enabled per account
and per region, and pushes full request-level records - prompts, completions, input and
output token counts, and caller identity - to S3 and/or CloudWatch Logs.

Without it, several optimisation decisions are guesswork. With it, the logs answer:

| Question | Optimisation decision it unlocks |
|---|---|
| Are the same prompts (or prefixes) recurring? | Prompt caching candidacy - quantify expected hit rate before enabling |
| Which roles/services call which models, at what avg token counts? | Model right-sizing per workload, chargeback sanity checks |
| Is prompt routing actually sending traffic to the cheaper model? | Verify routing policies deliver the promised mix |
| What is the real input:output token ratio per application? | Capacity and commitment sizing (ratios drive provisioned throughput maths) |

**Operational notes:**

- A default **automatic CloudWatch dashboard for Bedrock** exists in every account
  (Dashboards > Automatic dashboards > Bedrock): per-model invocations, token counts,
  latency. Zero setup - useful as the first artefact to show a client.
- CloudWatch Logs Insights includes a **natural-language query generator** - practitioners
  can query invocation logs (e.g. "prompts with total input/output tokens") without
  writing Logs Insights syntax.
- Full request/response logging at scale has its own ingestion cost. Apply the tiered
  logging strategy from `finops-for-ai.md`: metadata always, full content sampled.

---

## Cost optimisation patterns

### Model right-sizing

The highest-impact optimisation. Before committing to a model tier:
- Define a quality benchmark for your specific task (not a generic leaderboard score)
- Test Haiku, Sonnet, and Opus (or equivalent tiers for other publishers) against that benchmark
- Use the lowest-cost model that meets your quality threshold

### Model evaluation tooling - make selection an evidence decision

Two AWS tools operationalise the benchmarking step behind model right-sizing:

| Tool | What it does | When to use |
|---|---|---|
| **Amazon Bedrock Evaluations** | Built-in; evaluates multiple models against your prompts/data; supports LLM-as-judge scoring | First pass, no tooling investment |
| **FMBench** (open source, AWS) | Benchmarks cost AND performance across Bedrock, SageMaker, EC2; per-instance-type comparisons, charts | Deeper analysis; also serves GPU serving instance selection |

Evaluate on three axes: **modality** (does the workload need vision/audio, or is a
text-only model sufficient and cheaper?), **domain strengths** (code, finance), and
**efficacy on your own data** - not leaderboard scores.

### Intelligent Prompt Routing

Native Bedrock feature: routes each request within one model family (e.g. between
Haiku and Sonnet) based on predicted response quality at lowest cost. AWS-reported
savings up to 30% versus sending everything to the larger model, with internal tests
reaching higher on some workloads. Complements - does not replace - explicit tiered
routing logic. For cross-family or cross-provider routing, use a gateway
(LiteLLM, Portkey, OpenRouter - see `finops-ai-self-hosted-vs-managed.md`).

Verification step: use invocation logging (see "Cost visibility and allocation") to
confirm the realised routing mix and savings - routers are probabilistic, not
guaranteed.

### Model distillation

Train a small "student" model on outputs of a large "teacher" model for a specific
task. AWS-reported results for Bedrock Model Distillation: distilled models up to
500% faster and up to 75% less expensive than the teacher, with <2% accuracy loss on
use cases like RAG. FinOps positioning: distillation converts a recurring per-token
premium into a one-off training cost - a candidate when a task is narrow, stable, and
high-volume. Contrast with fine-tuning (static-knowledge injection) and RAG
(fresh-data injection): distillation targets capability transfer at lower unit cost.

### Related patterns: MoE and plan/execute model splitting

- **Mixture-of-experts models** (DeepSeek, Qwen) activate sub-models per query -
  often cheaper and faster per token, and viable on smaller hardware.
- **Plan/execute splitting**: e.g. Claude Code "Opus Plan" mode uses Opus to plan and
  Sonnet to execute, cutting cost versus Opus-only (no primary-source savings figure
  is published; benchmark on your own workload). The general pattern
  (expensive model for decomposition, cheap model for execution) applies to any
  agentic architecture (see task decomposition in `finops-for-ai.md`).

### Prompt optimisation

Input token volume is directly controllable:
- Audit system prompt length - verbose instructions inflate every API call
- Truncate or summarize conversation history for multi-turn applications
- Avoid sending redundant context in retrieval-augmented generation (RAG) pipelines
- For repetitive context, use **prompt caching** (see below) - this is the highest-
  leverage prompt-side lever for long-context and agentic workflows

### Prompt caching - direct FinOps lever for long-context and agentic workloads

Bedrock supports prompt caching for selected models, with two distinct token types
that bill differently from regular input tokens:

| Token type | Description | Pricing relative to regular input |
|---|---|---|
| **Cache write** | First time a cache breakpoint is created | ~1.25x base input price (5-min TTL) or ~2x (1-hour TTL) |
| **Cache read** | Subsequent requests that hit the cached prefix | ~0.1x base input price |

**TTL options.** Selected Claude models on Bedrock support both **5-minute** and
**1-hour** cache TTLs. The 1-hour duration was announced for Bedrock prompt caching
in early 2026, extending the original 5-minute window. Choose based on workflow
cadence:

- **5-minute TTL** for interactive sessions where the same context is reused within
  a few minutes (chat, agent loops with tool calls).
- **1-hour TTL** for longer-running workflows: persistent agents, batch evaluation
  passes over the same corpus, multi-step task chains where the system prompt and
  context are stable across hours.

**FinOps math:** the 1-hour write costs ~2x base, but a single cache write that
serves 100 reads at 0.1x base saves roughly 90% on those input tokens. Break-even
versus not caching comes fast: **1 cache hit** at the 5-minute TTL (1.25x write +
0.1x read = 1.35x, versus 2x uncached) and **2 cache hits** at the 1-hour TTL
(2x + 0.2x = 2.2x, versus 3x uncached). For agentic workflows that loop on the
same context dozens of times, the savings are material - often the difference
between economic and uneconomic at scale.

**Where caching matters most:**
- Long system prompts (>1k tokens) reused across many requests
- RAG pipelines with stable retrieved context across user queries
- Agentic loops that repeatedly send the same tool definitions and conversation history
- Batch evaluation against a stable corpus

**Where caching does not help:**
- One-shot calls with unique input
- Workloads where context changes substantively between requests
- Models that do not support caching (verify per model in the Bedrock docs)

Sources: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html, https://aws.amazon.com/about-aws/whats-new/2026/01/amazon-bedrock-one-hour-duration-prompt-caching/

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
- [ ] Define model selection policy - default to lower-cost tiers unless justified
- [ ] Instrument applications with token counts per request (input + output)
- [ ] Separate accounts or use tags for team/product cost attribution
- [ ] Review provisioned throughput utilization monthly
- [ ] Establish a model review cadence - AWS Bedrock model catalog changes frequently
- [ ] Document which workloads use provisioned vs on-demand capacity and why
- [ ] SCPs / IAM policies enforcing a **model allowlist** (deny unapproved Bedrock
      models) and denying unapproved GPU instance families - with a documented,
      fast approval path communicated to developers
- [ ] **Cost-safe IaC defaults**: Terraform modules / blueprints default to a small
      model, prompt caching enabled, low temperature, `max_tokens` set. Developers
      must actively opt into expensive configurations (the gp3-as-default pattern
      applied to GenAI)
- [ ] Bedrock invocation logging enabled (S3/CloudWatch) with tiered retention
- [ ] Post-optimisation observability: after each change (model swap, routing,
      caching), verify impact in invocation logs and token metrics - optimisations
      regress silently

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
