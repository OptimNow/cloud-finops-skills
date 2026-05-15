---
name: finops-for-ai
fcp_domain: "Quantify Business Value"
fcp_capability: "Unit Economics"
fcp_capabilities_secondary: ["Usage Optimization", "Allocation"]
fcp_phases: ["Inform", "Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering", "Product"]
fcp_personas_collaborating: ["Finance", "Leadership"]
fcp_maturity_entry: "Walk"
---

# FinOps for AI

> AI workloads do not behave like infrastructure workloads. The tools, processes, and
> mental models that have served cloud teams for a decade are insufficient on their own.
> This file covers how to apply and extend FinOps discipline to AI cost management.

---

## AI cost management is no longer optional

The State of FinOps 2026 survey (6th edition, 1,192 respondents, published February 2026)
confirms that AI cost management has shifted from emerging concern to universal priority.
The trajectory is striking: 31% of respondents managed AI spend in 2024, 63% in 2025,
and 98% in 2026. AI cost management is now the #1 skillset that FinOps teams need to
develop, and 81% of respondents are actively exploring how AI can improve FinOps
efficiency itself. Many organisations report being asked to self-fund AI investments
through efficiency gains - tying FinOps directly to strategic AI enablement.

---

## Why AI cost signals behave differently
<!-- ref:37b46c22605776cb -->

Traditional FinOps assumes a rhythm: usage happens first, costs are reported later,
decisions follow. AI disrupts this sequence. With LLMs and agentic systems, cost is
incurred at the moment a decision is made - a longer prompt, an extra retry, a different
model, or a poorly bounded loop can change spend materially in seconds, not weeks.

| Dimension | Traditional Cloud | AI Workloads |
|---|---|---|
| Cost unit | vCPU-hour, GB-month | Token, inference call, GPU-second |
| Predictability | High - instance type × hours | Low - depends on user behaviour and model design |
| Billing speed | Hourly/daily accumulation | Per-request, immediate COGS |
| Attribution unit | Infrastructure tag | Application-layer metadata |
| Optimisation lever | Rightsizing, reservations | Model selection, prompt design, caching, routing |
| FinOps sequence | Report → Allocate → Optimise | Allocate first → Real-time ingest → Report |
| Variance source | Provisioning decisions | User behaviour, prompt length, context window |

**The structural mismatch:** Traditional FinOps was built for predictable infrastructure.
AI workloads behave more like real-time COGS than capacity plans. A feature estimated
at $1,600/month can cost $8,800 without any infrastructure change - the variance comes
entirely from user behaviour and model design decisions.

**The critical inversion:** For AI workloads, the FinOps sequence must run in reverse.
Cost allocation must happen *before* the cost is created, not after the bill arrives.
Organisations that wait for monthly invoices to understand AI spend are already operating
with a structural disadvantage that compounds with every new model deployment.

---

## The four-phase AI FinOps implementation

### Phase 1: Establish AI cost visibility (prerequisite)

Without request-level attribution, everything downstream is guesswork.

**What is required:**

**Request-level instrumentation** - attach metadata to every API call at the moment of
invocation. Minimum required fields:
- Feature or product name
- User or session identifier
- Model name and version
- Prompt template version or ID
- Environment (prod / staging / dev)

**A proxy or gateway layer** - sits between your application and the AI provider,
attaches metadata before requests execute. Options by complexity:

| Option | Examples | Effort | Metadata richness |
|---|---|---|---|
| Native provider feature | AWS Bedrock inference profiles | Low | Limited |
| Open-source middleware | OpenLLMetry, Langfuse, Helicone | Medium | High |
| API gateway | Kong, NGINX with custom plugins | Medium-High | High |
| Custom application middleware | Direct SDK instrumentation | Low-Medium | Full control |

**Real-time cost ingestion** - token counts must be captured as model responses are
returned, not retrieved from billing exports. Cost Explorer lags 24–48 hours - acceptable
for EC2, not for workloads where a misconfigured agent can generate thousands of dollars
within hours.

> **Implementation baseline:** Achieving visibility typically requires ~30 minutes of
> design and ~2 hours of implementation. The barrier is lower than most teams expect.

### The full AI cost surface
<!-- ref:ai-cost-allocation-harness -->

The model API invoice is the most visible AI cost. It is rarely the complete picture.

In production RAG architectures, the surrounding infrastructure - referred to as the
harness - includes every component that supports the model call but is not itself a model
call. In observed enterprise deployments, the harness represents 40-60% of total AI
feature cost. In RAG-heavy architectures with multi-region data pipelines, it can exceed
inference cost.

**The emerging SaaS dimension:** Beyond infrastructure harness costs, AI agents are
introducing a new cost category: per-query charges from SaaS vendors. As agents interact
with CRM, ERP, and analytics platforms via APIs, vendors are shifting from seat-based
pricing to consumption models that charge per data query. This fundamentally changes how
organisations budget for SaaS tools - a sales intelligence agent querying Salesforce
thousands of times daily can generate costs that dwarf traditional per-seat licensing.

**Harness cost map:**

| Cost component | Primary driver | Allocation difficulty | Attribution approach |
|---|---|---|---|
| Vector DB (managed) | Storage GB + read/write units | High - marketplace billing | Project isolation, app metering, virtual tagging |
| Embedding generation | Token volume per ingestion + query | Medium | Per-request metadata logging |
| Object storage | Corpus size, retrieval frequency | Low-Medium | Native tags + lifecycle policies |
| GPU compute (self-hosted) | GPU-hours x instance rate | Medium | K8s labels + DCGM + OpenCost/Kubecost |
| KV / in-memory cache | Memory GB-hours | Low | Tags + namespace isolation |
| Data egress | Cross-region transfer volume | High - invisible in model billing | Architecture co-location + networking cost analysis |
| Orchestration layer | Lambda/Fargate invocations, Step Functions | Low-Medium | Tags + application logging |
| Reranking models | Token volume for secondary ranking calls | Medium | Per-request metadata logging |
| Observability and logging | Log ingestion volume | Medium | Tiered logging strategy |
| SaaS API queries | Per-query charges from agent interactions | High - new billing model | Agent-level metering + SaaS cost APIs |

**Vector database marketplace attribution:**
Managed vector databases (Pinecone, Weaviate, Qdrant) purchased through a cloud
marketplace consolidate into your cloud bill as a third-party line item. They do not
carry your internal tags and do not map to a feature or team. Remediation approaches:

- Project-based isolation - separate vector DB projects or tenants per team/product
- Application-layer metering - log every query with metadata, multiply volume by unit rate
- Virtual tagging - apply allocation rules via FinOps platform virtual dimensions
- Self-hosting - running on Kubernetes means underlying compute carries standard tags

**GPU compute attribution on Kubernetes:**
Self-hosted models on GPU clusters (EKS, AKS, GKE) require pod-level attribution.
Cloud billing shows the GPU node cost, not which workload consumed it.

Pod labels at deployment time are the primary mechanism:
```yaml
labels:
  team: nlp-team
  product: contract-summarizer
  environment: prod
  cost-centre: cc-1234
```

These labels flow into Prometheus via kube-state-metrics. Combined with NVIDIA DCGM
Exporter (GPU memory and compute utilisation per pod), attributable cost is:
`GPU memory consumed by pod / total GPU memory x hourly node cost`

The core Kubernetes limitation: GPUs are allocated as whole units. A pod requesting
`nvidia.com/gpu: 1` gets the full physical GPU regardless of actual utilisation. NVIDIA
MIG partitioning creates isolated GPU slices that Kubernetes schedules independently,
reducing waste and improving allocation accuracy.

| Layer | Tool |
|---|---|
| Node hardware labels | NVIDIA GPU Feature Discovery |
| Pod attribution | Kubernetes labels + namespaces |
| GPU utilisation metrics | NVIDIA DCGM Exporter + Prometheus |
| Cost attribution | OpenCost or Kubecost |
| GPU partitioning | NVIDIA MIG + GPU Operator |

**GPU utilisation is misleading - read the right DCGM metrics:**

The single biggest mistake in GPU FinOps is trusting `nvidia-smi`'s
`GPU-Util` percentage (also surfaced as CloudWatch `GPUUtilization` on EC2,
and as the default in many monitoring stacks). The metric reports whether
the GPU did **anything** during the sampling interval, not how much of its
compute capacity was used. A workload occupying 1 streaming multiprocessor
(SM) out of 108 on an H100 reports `GPU-Util: 100%`. Rightsizing decisions
based on that signal are systematically wrong.

A GPU can appear busy while being significantly underused. The real
signals come from NVIDIA DCGM (Data Center GPU Manager) profiling metrics,
exposed via DCGM Exporter:

| DCGM metric | What it measures | When to use it |
|---|---|---|
| `DCGM_FI_DEV_GPU_UTIL` | (legacy) GPU did something this interval | **Ignore** for rightsizing decisions |
| `DCGM_FI_PROF_GR_ENGINE_ACTIVE` | Fraction of time the graphics engine is active | First honest signal of compute usage |
| `DCGM_FI_PROF_SM_ACTIVE` | Fraction of SMs with at least one warp resident | Parallel-occupancy signal |
| `DCGM_FI_PROF_SM_OCCUPANCY` | Resident warps / max warps per SM | Density of SM utilisation |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | Tensor core pipeline activity | Critical for ML inference / training - separates "doing matrix maths" from "doing kernel launches" |
| `DCGM_FI_PROF_DRAM_ACTIVE` | GPU memory bandwidth in use | Detects memory-bound workloads (signal to move to higher-bandwidth SKU or batch differently) |
| `DCGM_FI_DEV_FB_USED` | Frame buffer (GPU memory) used | Sizing decisions, MIG candidacy, OOM risk |

A workload is genuinely well-sized when `DCGM_FI_PROF_GR_ENGINE_ACTIVE` and
`DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` are both > 40-60% during steady-state
traffic. If `GR_ENGINE_ACTIVE` is high but `PIPE_TENSOR_ACTIVE` is low for
an ML workload, the GPU is doing work that is not matrix multiplication -
usually a sign of poor batching, memory copies, or framework overhead, and
a candidate for code optimisation before infrastructure rightsizing.

**Practical deployment:**

- **On Kubernetes (EKS/AKS/GKE)**: install NVIDIA GPU Operator, which
  bundles DCGM Exporter. Metrics scrape into Prometheus with `gpu` and pod
  labels for per-workload attribution.
- **On bare EC2**: deploy DCGM Exporter via systemd or SSM Run Command,
  scrape with a CloudWatch agent or Prometheus.
- **On SageMaker managed endpoints**: DCGM is not exposed natively. The
  available CloudWatch metrics (`GPUUtilization`, `GPUMemoryUtilization`)
  are the legacy signals and overestimate real usage. For honest GPU
  telemetry on SageMaker, either run a custom container that emits DCGM
  metrics, or run inference on self-managed EKS with DCGM and use
  SageMaker only for training / Studio / managed catalogue features.

This metric reference is the foundation for the GPU rightsizing
playbooks: [aws-gpu-instance-oversized](../playbooks/aws-gpu-instance-oversized.md),
[aws-multi-gpu-underutilized](../playbooks/aws-multi-gpu-underutilized.md),
[aws-mig-candidate](../playbooks/aws-mig-candidate.md),
[aws-gpu-for-cpu-bound-workload](../playbooks/aws-gpu-for-cpu-bound-workload.md).

**Observability cost feedback loop:**
Token-level logging for every AI request generates large log volumes. Cloud observability
platforms charge by the GB for ingestion and retention. A production AI system with full
request-level logging can generate observability costs that rival inference costs. Use
tiered logging: always log metadata (token counts, feature identifier, latency, model
version); log full request and response content only for sampled traffic or error cases.

**Cross-provider allocation summary:**

| Allocation need | AWS | Azure | GCP |
|---|---|---|---|
| Team / product boundary | Separate accounts | Separate subscriptions / resource groups | Separate projects |
| Training job attribution | SageMaker tags -> CUR | AzureML resource group + tags -> Cost Management | Vertex AI project labels -> BigQuery |
| Inference attribution | Tags on provisioned throughput + app instrumentation | Separate AOAI accounts + tags + app instrumentation | Project labels + API call labels + Cloud Monitoring |
| Token-level unit economics | App instrumentation + CloudWatch | App instrumentation + Azure Monitor | App instrumentation + Cloud Monitoring |
| AI cost visibility | Bedrock inference profiles (limited) | Cost Management AI views | AI Cost Summary Agent (preview) |

The common thread: native billing does not provide feature-level or user-level cost
attribution for inference out of the box. Account and project separation handles
team-level allocation. Application-layer instrumentation is required for feature-level
and per-request attribution.

---

### Phase 2: Establish unit economics

Once costs are attributed, translate them from infrastructure metrics to business metrics.

**Step 1 - Define your unit of value:**
- Customer conversation
- Document processed
- Task completed
- Query answered
- Report generated

**Step 2 - Calculate the three-layer cost per unit:**

| Layer | What it measures | Example |
|---|---|---|
| Layer 1: Inference | Raw model API cost (tokens × rate) | $0.0003 per conversation |
| Layer 2: Harness | All surrounding infrastructure (compute, storage, retrieval, egress) | $0.0035 per conversation |
| Layer 3: Total unit cost | Layer 1 + Layer 2 + amortized fixed costs | $0.004 per conversation |

**Step 3 - Define value per unit** (pick the most relevant method):

- **Cost displacement** - what does the equivalent human action cost?
  `Value = human cost × deflection rate`
- **Revenue generation** - does the feature increase conversion or order value?
  `Value = uplift × average transaction value`
- **Retention improvement** - does the feature reduce churn?
  `Value = retained customers × LTV delta`
- **Premium monetisation** - is the feature sold as a paid tier?
  `Value = subscription price − unit cost`

**Step 4 - Track unit economics weekly**, not monthly. AI cost patterns shift faster
than monthly reporting cycles can capture.

**Core formula:**
```
Unit margin = (Value per output × success_rate) − cost_per_unit
Monthly profit = (unit_margin × volume) − fixed_costs
ROI% = monthly_profit / fixed_costs × 100
Payback period = fixed_costs / monthly_profit (months)
```

**ROI time dimension:** AI systems follow a predictable ramp.
- Month 1: Negative ROI - integration costs dominate
- Month 3: Near cost parity - prompts improve, routing optimises
- Month 6+: Positive ROI - learning effects compound, volume absorbs fixed costs

Tolerating early losses is rational if the weekly trajectory toward breakeven is positive.
Systems showing no improvement after 8–12 weeks warrant scrutiny.

### Phase 3: Optimize

**Model selection** (highest impact lever):

Treat model selection like instance rightsizing. Defaulting to the largest or latest model
for every feature is the AI equivalent of running all workloads on ml.p4d.24xlarge.

| Model tier | Use case | Cost ratio example |
|---|---|---|
| Small / fast (e.g. Claude Haiku, GPT-4o mini) | Classification, routing, simple Q&A | 1× |
| Mid-tier (e.g. Claude Sonnet, GPT-4o) | Complex reasoning, code generation | 12× |
| Large (e.g. Claude Opus, GPT-4) | Research, nuanced judgment | 60× |

As of March 2026, OpenAI's pricing structure demonstrates the cost impact of model selection:

| Model tier | Use case | Cost ratio example | OpenAI example (per 1M tokens) |
|---|---|---|---|
| Small / fast (e.g. GPT-4o mini) | Classification, routing, simple Q&A | 1x | $0.15 input / $0.60 output |
| Mid-tier (e.g. GPT-4o) | Complex reasoning, code generation | 17x | $2.50 input / $10.00 output |
| Large (e.g. o1) | Research, nuanced judgment | 100x | $15.00 input / $60.00 output |

Implement tiered routing: classify query complexity first (cheap), then route to the
appropriate model. Simple queries to small models, complex queries to large models.

**Prompt engineering as cost control:**
- System prompts are billed on every request - keep them lean and precise
- Context windows accumulate cost - manage conversation history length explicitly
- Always define `max_tokens` on every model call - unbounded responses are a common
  and avoidable source of cost overruns
- Tune `temperature`, `top_p`, `top_k` for concise output on structured tasks

**Caching:**
- Cache system prompts and static context (Anthropic and OpenAI support prompt caching)
- Cache embedding results for repeated documents in RAG systems
- Cache responses for deterministic or near-deterministic queries
- Cache at the application layer before hitting the model API

**Architecture hygiene:**
- Not every feature needs AI - use deterministic code or standard APIs when they are
  sufficient. A weather API call costs a fraction of a cent. An LLM call to answer
  "what is the weather today?" is waste.
- Audit for zombie features: AI systems still running at full cost after usage has dropped
- Review agentic retry logic - retries multiply token consumption silently

**Model parameters:**
The following inference parameters directly affect output length and therefore cost:
- `temperature` - higher values produce longer, more varied outputs
- `top_p` / `top_k` - affect output distribution and length
- `max_tokens` - the single most important cost guardrail; always set it

### Phase 4: Govern

**Budget guardrails:**
- Set spending limits at the feature level, not just the account level
- Anomaly alerts should trigger within minutes, not surface on the monthly bill
- Define thresholds that require review before spend, not after

**Governance policies to establish:**
- Require AI cost estimates (COGS modelling) before feature deployment
- Mandate application-layer metadata tagging as a development standard
- Establish a model approval process - preventing shadow AI through procurement
  controls is more effective than prohibition after the fact
- Define escalation paths when unit economics deteriorate

**Shadow AI:**
Research indicates 90% of employee AI tool usage does not appear in corporate billing
systems. The remainder occurs through personal subscriptions, departmental cards, or
free-tier accounts that bypass procurement. Shadow AI is not only a governance issue -
it destroys cost attribution and makes forecasting impossible.

Detection approach:
- Audit for marketplace subscriptions (AWS, Azure, GCP) that may not appear in
  centralized cost management tools
- Review expense reports for recurring SaaS charges from known AI vendors
- Survey teams on tools in active use before assuming billing systems are complete

---

## The five AI cost anti-patterns

These patterns generate significant financial impact within hours, but remain invisible
to monthly dashboards until the bill arrives.

### 1. Zombie AI features
A feature loses adoption but continues processing in the background - pre-processing
documents, indexing content, maintaining persistent connections, or retrying failed calls.
Cost persists while value delivered collapses.

*Real example:* An AI summarization feature was used heavily at launch, then dropped to
fewer than 5 active users per day. The feature continued pre-processing every uploaded
document regardless of whether a summary was requested - 2.8M tokens/month, $1,400.
Actual value delivered: negligible.

*Detection signal:* Token consumption stable or rising while active user sessions decline.

### 2. Technology churn debt
Each AI provider or framework migration leaves behind infrastructure that continues
incurring charges: API keys, Lambda functions, S3 buckets, committed capacity reservations.
Organisations running 3+ AI providers simultaneously often find 30–40% of AI spend
supports abandoned experiments rather than production features.

*Detection signal:* Active resources in accounts or regions with no recent deployments;
committed capacity with low utilization.

### 3. Agentic loops
AI agents calling other agents create multiplicative cost patterns. Retry logic, recursive
calls, validation loops, or agents that invoke themselves multiply token consumption by
5–50× per user request. This compounds when agents interact with SaaS APIs that charge
per query - each retry or validation loop triggers additional SaaS charges alongside
model costs.

*Real example:* A sales intelligence agent validated its own output with a second API
call. When validation failed, it retried the full sequence. A single user query generated
47 API calls at $2.30 each. At 12,000 queries/month: $27,600 in unintended cost. When
the same agent began querying Salesforce data, per-query charges added another $18,000/month
that appeared in the SaaS bill, not the AI infrastructure budget.

*Detection signal:* Average tokens per request significantly above design estimate; high
variance in cost per session; cost growing faster than user volume; unexpected increases
in SaaS API usage charges.

### 4. Data egress in AI pipelines
RAG systems that store data in one region, generate embeddings in another, and run
inference in a third create multi-directional transfer costs invisible in model-level
reporting. For high-volume applications, data movement can represent 15–25% of total
AI costs.

*Detection signal:* S3 or network costs rising in proportion with AI feature usage;
cross-region data transfer appearing in billing without a clear infrastructure change.

### 5. Negative unit economics at scale
A feature appears viable at low volume. Each interaction loses money, but losses are
small and unnoticed. As adoption grows, the scale-up accelerates the loss.

*Real example:* An AI-powered search feature was included in a standard $15/user/month
subscription. Each user performed 120 searches/month at $0.08 each - $9.60 in AI costs
per user, against $15 in subscription revenue. Profitable only for users performing fewer
than 25 searches/month. Feature adoption growth increased losses, not margins.

*Detection signal:* AI costs growing proportionally with user adoption; unit margin
declining as volume increases.

---

## AI cost readiness assessment

Use this to diagnose an organisation's current state before recommending solutions.

**Visibility (prerequisite - assess first):**
- [ ] Token counts captured per feature, not just per account or model
- [ ] Request-level cost attribution with application metadata at invocation time
- [ ] Cost data available within minutes, not 24–48 hours

**Unit economics:**
- [ ] Cost per unit defined and tracked (conversation / task / document)
- [ ] Unit cost trend tracked weekly
- [ ] Value metric defined and measured alongside cost metric

**Optimization:**
- [ ] Model selection reviewed per use case (not defaulting to largest model)
- [ ] Maximum token limits set on all model calls
- [ ] System prompts and repeated context cached where provider supports it

**Governance:**
- [ ] AI COGS estimated before feature deployment
- [ ] Budget alerts configured at feature level
- [ ] Process exists to detect and decommission zombie features
- [ ] Shadow AI audit conducted in last 12 months
- [ ] SaaS API query costs included in agent budget planning
- [ ] Monitoring for agent-driven SaaS consumption spikes

**Scoring:**
- 0–4 ✓: Crawl - start with visibility. Nothing else is meaningful without it.
- 5–8 ✓: Walk - focus on unit economics and model optimisation.
- 9–14 ✓: Run - focus on governance automation and agentic FinOps patterns.

---

## Agentic FinOps

Agentic systems introduce cost patterns that require a different governance model. Unlike
static applications, agents make runtime decisions that directly affect spend - model
selection, context retention, tool invocation frequency, and retry behaviour all create
variable costs that no static budget can fully anticipate.

**Three architectural pillars for cost-safe agents:**

**1. Data connectivity with cost awareness**
Agents require access to real-time cost data alongside operational data. An agent that
can identify a spending anomaly but cannot correlate it to a specific resource, workflow,
or decision point is only half useful. MCP-based connectivity (e.g., OptimNow's finops-tagging
MCP server) provides standardized interfaces for cost data, tagging, and governance without
custom integration code per data source.

**2. Memory with cost controls**
Stateful agents accumulate context over time - necessary for meaningful investigation but
expensive if unbounded. Naive implementations store entire conversation histories, creating
context windows that balloon to hundreds of thousands of tokens. Effective architectures
use short-term memory for recent exchanges and long-term memory for persistent preferences
and organisational context, with explicit token budgets for each layer.

**3. Policy-generation over direct mutation**
The safest agentic architecture for FinOps generates governance policies for human review
rather than executing infrastructure changes directly. An agent that identifies idle
resources and drafts a Cloud Custodian policy or OpenOps rule for review is production-safe.
An agent that stops instances autonomously is not - regardless of how sophisticated its
reasoning is. Governance, not technology capability, is the real constraint on autonomous
FinOps agents.

**Key insight:** Agents will be advisory long before they are autonomous. Organisations
making progress treat agent development as iterative learning, not project delivery.

---

> Sources: FinOps Foundation (State of FinOps 2026), OptimNow methodology.

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
