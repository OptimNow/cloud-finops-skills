# FinOps for AI

> AI workloads do not behave like infrastructure workloads. The tools, processes, and
> mental models that have served cloud teams for a decade are insufficient on their own.
> This file covers how to apply and extend FinOps discipline to AI cost management.

---

## AI cost management is no longer optional

The State of FinOps 2026 survey (6th edition, 1,192 respondents representing $83+ billion
in cloud spend, published February 2026) confirms that AI cost management has shifted from
emerging concern to universal priority. The trajectory is striking: 31% of respondents
managed AI spend in 2024, 63% in 2025, and 98% in 2026. AI cost management is now the #1
skillset that FinOps teams need to develop, and 81% of respondents are actively exploring
how AI can improve FinOps efficiency itself. Many organisations report being asked to
self-fund AI investments through efficiency gains - tying FinOps directly to strategic AI
enablement.

---

## Why AI cost signals behave differently
<!-- ref:37b46c22605776cb -->

Traditional FinOps assumes a rhythm: usage happens first, costs are reported later,
decisions follow. AI disrupts this sequence. With LLMs and agentic systems, cost is
incurred at the moment a decision is made - a longer prompt, an extra retry, a different
model, or a poorly bounded loop can change spend materially in seconds, not weeks.

| Dimension | Traditional Cloud | AI Workloads |
|---|---|---|
| Cost unit | vCPU-hour, GB-month | Token, inference call, GPU-second, agent session |
| Predictability | High - instance type × hours | Low - depends on user behavior and model design |
| Billing speed | Hourly/daily accumulation | Per-request, immediate COGS |
| Attribution unit | Infrastructure tag | Application-layer metadata |
| Optimization lever | Rightsizing, reservations | Model selection, prompt design, caching, routing |
| FinOps sequence | Report → Allocate → Optimize | Allocate first → Real-time ingest → Report |
| Variance source | Provisioning decisions | User behavior, prompt length, context window |

**The structural mismatch:** Traditional FinOps was built for predictable infrastructure.
AI workloads behave more like real-time COGS than capacity plans. A feature estimated
at $1,600/month can cost $8,800 without any infrastructure change - the variance comes
entirely from user behavior and model design decisions.

**The critical inversion:** For AI workloads, the FinOps sequence must run in reverse.
Cost allocation must happen *before* the cost is created, not after the bill arrives.
Organizations that wait for monthly invoices to understand AI spend are already operating
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
- Service type (inference / managed agent / fine-tuning)

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
within hours. When calculating cost from token counts, account for context-length pricing
thresholds: all major providers (OpenAI, Anthropic, Google) apply 2× input rates when
input tokens exceed provider-specific thresholds (200K–272K). The API response does not
indicate which pricing tier was applied - your instrumentation must check input token
count against the threshold and apply the correct rate. See anti-pattern #6 for details.

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
| Managed agent runtime | Session hours, compute resources, tool invocations | High - new service category | Provider-specific tagging + session metadata |

**Managed agent services:**
Anthropic Claude Managed Agents (launched March 2026) introduces a new cost category
beyond token-based inference. Managed agents run in provider-controlled sandboxed
environments with persistent sessions and autonomous execution capabilities. Cost drivers
differ fundamentally from standard API calls:

- **Session-based billing** - charged per active session hour, not per token
- **Compute resource allocation** - dedicated CPU/memory for agent execution
- **Tool invocation costs** - each external API call or database query adds cost
- **State persistence** - storage costs for maintaining agent memory between sessions
- **Sandbox overhead** - isolation and security features add baseline cost per agent

Attribution approach for managed agents:
- Tag agent sessions with business metadata at creation time
- Track tool invocation patterns per agent to identify cost drivers
- Monitor session duration and implement timeout policies
- Separate agent runtime costs from underlying model inference costs in reporting

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
| Managed agent attribution | Bedrock agent tags + session metadata | Azure AI agents resource tags + session tracking | Vertex AI agent labels + session monitoring |

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
- Agent session completed

**Step 2 - Calculate the three-layer cost per unit:**

| Layer | What it measures | Example |
|---|---|---|
| Layer 1: Inference | Raw model API cost (tokens × rate) | $0.0003 per conversation |
| Layer 2: Harness | All surrounding infrastructure (compute, storage, retrieval, egress) | $0.0035 per conversation |
| Layer 3: Total unit cost | Layer 1 + Layer 2 + amortized fixed costs | $0.004 per conversation |

For managed agent services, adapt the layers:
- Layer 1: Agent runtime cost (session hours × rate + tool invocations)
- Layer 2: Supporting infrastructure (state storage, monitoring, orchestration)
- Layer 3: Total cost including model inference calls made by the agent

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
- Month 3: Near cost parity - prompts improve, routing optimizes
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

Implement tiered routing: classify query complexity first (cheap), then route to the
appropriate model. Simple queries to small models, complex queries to large models.

**Managed agent optimisation:**
- Define clear session boundaries - don't let agents run indefinitely
- Implement tool invocation budgets - limit external API calls per session
- Use agent orchestration patterns - multiple specialised agents vs. one general agent
- Monitor state size - prune unnecessary memory to reduce storage costs
- Consider hybrid architectures - use managed agents for complex workflows, direct API calls for simple tasks

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
- For managed agents, cache tool responses and intermediate results

**Architecture hygiene:**
- Not every feature needs AI - use deterministic code or standard APIs when they are
  sufficient. A weather API call costs a fraction of a cent. An LLM call to answer
  "what is the weather today?" is waste.
- Audit for zombie features: AI systems still running at full cost after usage has dropped
- Review agentic retry logic - retries multiply token consumption silently
- For managed agents, implement circuit breakers to prevent runaway sessions

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
- For managed agents, implement session-level and daily spending caps

**Governance policies to establish:**
- Require AI cost estimates (COGS modelling) before feature deployment
- Mandate application-layer metadata tagging as a development standard
- Establish a model approval process - preventing shadow AI through procurement
  controls is more effective than prohibition after the fact
- Define escalation paths when unit economics deteriorate
- Create specific policies for managed agent deployments (session limits, tool allowlists)

**Shadow AI:**
Research indicates 90% of employee AI tool usage does not appear in corporate billing
systems. The remainder occurs through personal subscriptions, departmental cards, or
free-tier accounts that bypass procurement. Shadow AI is not only a governance issue -
it destroys cost attribution and makes forecasting impossible.

Detection approach:
- Audit for marketplace subscriptions (AWS, Azure, GCP) that may not appear in
  centralized cost management tools
- Review expense reports for recurring SaaS charges from known AI vendors
- Survey teams on tools in active use before assuming billing