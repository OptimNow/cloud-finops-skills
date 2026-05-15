---
name: finops-ai-self-hosted-vs-managed
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Architecting & Workload Placement"
fcp_capabilities_secondary: ["Usage Optimization", "Rate Optimization"]
fcp_phases: ["Inform", "Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Product", "Leadership", "Finance"]
fcp_maturity_entry: "Walk"
---

# AI inference: self-hosted vs managed APIs - a FinOps perspective

> FinOps decision framework for AI inference: self-hosted vLLM/SGLang/llama.cpp on rented or
> owned GPUs versus managed APIs (Anthropic, OpenAI, Bedrock, Vertex AI, Azure OpenAI). Covers
> cost mechanics, hidden cost surfaces, organisational maturity prerequisites, hybrid routing
> patterns, and a maturity-driven decision rubric. Use this reference whenever a client raises
> "should we self-host our LLM?" or "build vs buy" for inference workloads.
>
> Built by OptimNow. Grounded in hands-on enterprise delivery, not abstract frameworks.

---

## TL;DR

Self-hosted inference looks cheaper on paper at every TCO calculator. It rarely is in
practice, because the calculators omit the operational maturity tax. The right question is
not "what is cheaper per million tokens?" but "does the client have the in-house expertise
to operate this stack at production grade without burning the savings on incident response,
re-tuning, and migration debt?"

For most organisations in 2026, managed APIs (Bedrock, Anthropic, OpenAI, Azure OpenAI,
Vertex AI) are the right default. Self-hosting earns its place only when a client has
genuine ML-Ops maturity in-house, runs predictable high-volume workloads, and has compliance
or cost arbitrage reasons that managed APIs cannot meet.

## Why this matters now

Three drivers make this conversation more common in 2026:

1. **Frontier model pricing has stabilised** (Sonnet 4 around $3/M input, $15/M output;
   GPT-5 in similar territory). Clients with predictable workloads can now build credible
   TCO models comparing managed APIs to renting their own GPUs.
2. **Open-weight models have closed the quality gap** for many use cases. Qwen3.6, Llama 4,
   GLM-5.1, Gemma 4 deliver production-grade quality across reasoning, coding, multimodal.
   Self-hosting a capable model is a real option, not a research experiment.
3. **Cloud GPU rental markets are mature**. RunPod, Lambda, CoreWeave, Modal, AWS Capacity
   Blocks, Azure GPU spot. A100/H100/B200 are rentable on-demand or reserved at competitive
   per-hour rates.

The result: more clients ask the question, and many get the answer wrong because they
benchmark on per-token cost without weighing operational reality.

## How each model bills

### Managed APIs (per-token)

| Vendor | Pricing dimension | Optimisation levers |
|---|---|---|
| Anthropic API | Input/output tokens, separate caches, separate batch | Prompt caching (1h TTL, 90% off), Batch API (50% off), model selection (Haiku/Sonnet/Opus), Fast mode for compute-allocated tiers |
| OpenAI API | Input/output tokens, cached tokens, batch, fine-tuned variants | Cached tokens (auto), Batch API (50% off), model selection, fine-tuning vs prompting tradeoff |
| AWS Bedrock | Input/output tokens, provisioned throughput (model units), batch | On-demand vs PT, Application Inference Profiles for cost allocation, prompt caching, batch inference |
| Azure OpenAI | Input/output tokens, PTU reservations, batch | PTU reservations with locality constraint, AOAI spillover, regional placement, fine-tuning costs |
| Vertex AI | Input/output tokens, provisioned throughput, batch | Provisioned throughput with default-PAYG spillover, batch prediction, model garden alternatives |

You pay only for what you generate. Capacity is the vendor's problem. Quality, uptime, model
updates, security patches, all included in the per-token price.

### Self-hosted (per-hour)

You rent or own GPUs. You pay 24/7 for the time the GPU is allocated, regardless of
utilisation.

| Cost line | Per-hour rate (typical 2026) | Notes |
|---|---|---|
| A100 80GB | $1.50 to $2.00 on-demand | Sweet spot for 27B-32B BF16 models |
| H100 80GB | $2.50 to $4.00 on-demand | Faster than A100, premium for large models or low-latency |
| H200 141GB | $3.50 to $5.50 on-demand | Larger memory for 70B+ at full precision |
| B200 192GB | $5.00 to $8.00 on-demand | Frontier hardware, 70B+ MoE workloads |
| RTX PRO 6000 96GB | $1.80 to $2.20 on-demand | Blackwell consumer-class, NVFP4 quants |

These rates are **on-demand**. Reserved or spot can be 40-60% cheaper, with the same caveats
as cloud compute commitments: liquidity risk on reserved, preemption risk on spot.

To this you add:
- **Volume disk** (model weights, caches): $0.05 to $0.10 per GB-month, often $50-200/month
- **Egress** if your traffic leaves the GPU provider
- **Engineer time** (the dominant hidden cost, see below)

## The hidden cost surface of self-hosting

This is the part TCO calculators omit. It is also where most self-hosting projects bleed
their savings.

### Operational costs

- **Infrastructure debugging time**: driver/CUDA/vLLM/transformers version mismatches are
  the norm, not the exception. Expect 5-20 hours per upgrade cycle.
- **Capacity planning**: you have to size GPUs, KV cache budgets, batch sizes,
  concurrency limits. Get it wrong and you under-utilise (waste money) or over-commit
  (queue, drop requests).
- **Migration friction**: GPU providers preempt or migrate your pods. Each migration changes
  endpoints, breaks downstream clients unless you have a load balancer or DNS layer.
- **Model lifecycle**: every model update requires re-quantization, re-validation,
  re-deployment. New SOTA models drop monthly.
- **Observability**: logging, metrics, alerting, anomaly detection - all DIY. Managed APIs
  ship this in their console.

### Reliability costs

- **SLA**: managed APIs commit to 99.9% or better, with credits if breached. Your self-hosted
  endpoint is as reliable as your engineers and your GPU provider. Without redundancy and
  failover, expect 95-99% in practice.
- **Latency variance**: cold starts after preemption, queue buildup at peak, GPU memory
  fragmentation. Managed APIs absorb this through their fleet.
- **Incident cost**: when the endpoint goes down at 2am, someone fixes it. Managed: the
  vendor. Self-hosted: your team, on call.

### Compliance and security costs

- **Data residency**: you control where the data sits, which is sometimes a benefit and
  sometimes an obligation (EU clients, HIPAA, regulated industries).
- **Audit trail**: you build it. Managed APIs ship logging, IAM, billing-as-cost-allocation.
- **Network architecture**: PrivateLink, VPC peering, egress control, you design and pay for
  it. Bedrock/Azure OpenAI ship this with the service.
- **Model licensing**: open-weight models have licences (Llama Community, Apache, Qwen).
  Some restrict commercial use, redistribution, or specific industries. You verify and
  comply. Vendors do this for you on managed APIs.

### Talent costs

- **Engineering FTEs**: a credible self-hosted production stack typically requires 0.5-2
  FTE of dedicated ML-Ops/platform engineering. At loaded cost of $150-250k/year per FTE in
  Western Europe or North America, this alone exceeds many clients' projected savings.
- **Specialised expertise**: Triton/TensorRT, vLLM tuning, Kubernetes for GPU workloads,
  model quantization, observability for LLM-specific metrics (TTFT, ITL, throughput per GPU).
  This skill set is scarce and expensive in 2026.

## Where self-hosted wins (when it does)

When the conditions align, self-hosted is meaningfully cheaper and operationally sensible.
The conditions are stricter than vendors of GPU compute would have you believe.

1. **High-volume, predictable workloads.** A workload that consistently consumes
   100M+ tokens per day, 24/7, with low variance, justifies dedicated GPU capacity. The
   per-token math tips around 200-500M tokens/day depending on model size and quant.
2. **Strict latency SLOs.** Sub-100ms TTFT requirements that cross-region API calls cannot
   meet. Dedicated GPU close to your application stack wins on tail latency.
3. **Compliance requirements that managed APIs do not satisfy.** Air-gapped environments,
   national security, specific certifications. Note: Bedrock, Azure OpenAI, Vertex AI cover
   most enterprise compliance scenarios in 2026 (HIPAA, FedRAMP, IRAP, ISO 27001, PCI DSS).
4. **Custom model requirements.** Heavily fine-tuned models, abliterated variants, specific
   domain models (legal, biomedical, code) that managed vendors do not host.
5. **IP and data sovereignty as a competitive moat.** Some clients sell trust as a feature
   (defence, healthcare, sovereign clouds). Self-hosting is part of their value proposition.

## Where managed APIs win (most cases)

1. **Variable or growing workloads.** Pay-as-you-go scales naturally. No capacity decisions
   to revisit monthly.
2. **Multi-model needs.** Routing across Sonnet/GPT-5/Gemini/Claude based on task is trivial
   on managed APIs, expensive to replicate self-hosted.
3. **Frontier model requirements.** Anthropic Claude Opus, OpenAI GPT-5, Google Gemini 3 Pro
   are not available as open weights. Self-hosting cannot replicate them.
4. **Limited engineering bandwidth.** Most organisations cannot dedicate 1-2 FTE to ML-Ops.
   Managed APIs let small teams ship.
5. **Fast-moving roadmap.** Vendors update models monthly. Managed APIs give you the new
   model with a config change. Self-hosted requires a deployment and validation cycle.

## The hybrid pattern (often the right answer)

Mature organisations rarely pick one and stick with it. They route:

- **Frontier reasoning, agentic workflows, code generation**: managed API (Claude Opus,
  GPT-5, Gemini 3 Pro) where quality matters most
- **High-volume RAG, classification, routing, summarisation**: self-hosted (Qwen3.6, Llama 4,
  Gemma 4) where token volume justifies dedicated capacity
- **Fallback and burst**: managed API absorbs spillover when self-hosted capacity saturates

This requires a routing layer (LiteLLM, custom proxy, or commercial gateway like Portkey,
Helicone). It also requires the team to operate both stacks. The complexity is real and
should be priced into the decision.

## The maturity-driven decision rubric

This is the OptimNow point of view. Cost mechanics matter. Compliance matters. But the
single best predictor of self-hosted success is the client's in-house ML-Ops maturity.

### Recommend self-hosted only when **all** of the following are true:

1. **Dedicated platform/ML-Ops team in place.** Not "the data team will pick it up."
   Not "our DevOps engineer is curious." A dedicated function with budget and accountability.
2. **The team has shipped GPU workloads in production before.** Not just experimented in a
   notebook. Real production traffic on GPU-backed services, with documented SLOs and
   incident history.
3. **Observability and CI/CD for ML are already running.** If basic ML platform hygiene
   (model registry, evaluation harness, deployment pipelines, drift monitoring) is
   missing, self-hosted inference will exacerbate, not solve, operational problems.
4. **Workload pattern is high-volume and predictable.** Backed by 90 days of usage data
   showing consistent traffic, not aspirational projections.
5. **Cost arbitrage is meaningful, not marginal.** A credible TCO model showing 30%+ savings
   net of operational overhead. If the savings are 10-15%, the operational risk almost
   always outweighs them.

If any of the above is missing, default to managed APIs. Revisit in 12-18 months.

### Recommend managed APIs when:

- The client is at FinOps Crawl or Walk maturity on AI workloads
- The team is small (<10 engineers total, <2 dedicated to AI)
- Workload is variable, exploratory, or under 50M tokens/day per model
- Compliance is met by Bedrock, Azure OpenAI, Vertex AI, or Anthropic Enterprise
- Speed-to-market matters more than per-token cost optimisation
- The client wants frontier model access (Opus, GPT-5, Gemini Ultra)

### Consider hybrid when:

- The client is at FinOps Run maturity with a dedicated AI platform team
- They have at least one workload meeting all five self-hosted criteria
- They also have variable or frontier workloads better suited to managed
- They have or are willing to build a routing layer with operational maturity to match

## What to ask a client before recommending

Before pricing self-hosted vs managed, run these diagnostic questions:

1. Who would own this stack day-to-day? Name them. What else is on their plate?
2. What is your current incident response capability for production AI services?
3. Show me 90 days of token usage data, broken down by use case and model.
4. What is the latency SLO of your end-user application? Have you measured tail latencies on
   managed APIs vs your candidate self-hosted setup?
5. What compliance requirements does your AI workload have, specifically? (Not generic
   "we are regulated.")
6. If you go self-hosted and the model needs an upgrade in 6 months, who validates,
   re-deploys, and rolls back if needed?
7. What is the cost of one hour of downtime on this service to the business?
8. Have you priced the routing/fallback layer if you go hybrid?

If they cannot answer 1, 2, 3, 6 with concrete specifics, they are not ready for
self-hosted. Frame this honestly. Recommending self-hosted to a client who cannot operate it
is not a cost-optimisation strategy. It is creating future technical debt that will be
billed to the same FinOps budget as remediation.

## Common anti-patterns

These are the failure modes seen repeatedly in 2024-2026:

- **TCO calculator without operational tax.** Comparing $0.50/M tokens self-hosted to $3/M
  managed, omitting the FTE cost, oncall burden, migration overhead, retuning cycles. The
  TCO model is wrong by a factor of 2-5x.
- **"We will figure it out" sizing.** Provisioning A100s without 90 days of usage data,
  ending up at 15-25% utilisation. The per-token math collapses immediately.
- **No fallback plan.** Single-pod self-hosted in one region, no redundancy. First
  preemption causes a P1 incident and a panicked email to the FinOps team about "why is
  managed API so expensive in this report?"
- **Decision driven by data residency theatre.** "We must self-host because EU." Bedrock has
  EU regions. Azure OpenAI has EU regions. Anthropic offers EU data residency. Verify the
  actual requirement before assuming managed APIs cannot meet it.
- **Custom model when off-the-shelf would do.** Self-hosting a fine-tuned model that
  marginally beats Claude Sonnet on a narrow benchmark, while costing 3x more all-in.
- **Self-hosting frontier alternatives.** "We will run Llama 4 405B instead of Claude
  Opus." The infrastructure cost of running a 405B model in production is brutal. Most
  clients underestimate it by an order of magnitude.

## Connecting back to FinOps phases

| Phase | Self-hosted vs managed posture |
|---|---|
| Inform | Default to managed APIs. Establish token usage visibility, model cost allocation, by use case and team. Without this data, the self-hosted question cannot be answered. |
| Optimize | Apply commitment, caching, batch, model selection on managed APIs. Most savings come from these levers, not from self-hosting. |
| Operate | Now, and only now, evaluate self-hosted for specific workloads meeting the criteria above. Build routing/fallback layers. Treat self-hosted inference as a capability the FinOps practice manages alongside cloud commitments. |

## Connecting back to OptimNow methodology

This sits squarely in the **diagnose before prescribing** principle. The self-hosted vs
managed question is one of the most common AI FinOps questions, and one of the most common
sources of bad recommendations from generic consultants. The OptimNow approach is to:

1. Refuse to answer the question without 90 days of usage data and a clear view of the
   client's ML-Ops maturity.
2. Use managed APIs as the default unless the client demonstrably meets all five
   self-hosted criteria.
3. Frame the operational tax honestly. Hidden costs are real costs. A 30% TCO saving that
   requires hiring two engineers is not a 30% saving.
4. When self-hosted is justified, recommend hybrid first: self-host the predictable
   high-volume workloads, keep managed APIs for frontier and variable workloads.
5. Treat the routing layer (LiteLLM, gateway) as part of the self-hosted commitment, not an
   afterthought.

## References (other files in this skill)

- `finops-for-ai.md` for AI cost mechanics, allocation, ROI framework
- `finops-genai-capacity.md` for provisioned vs shared capacity and traffic shape
- `finops-anthropic.md`, `finops-bedrock.md`, `finops-azure-openai.md`, `finops-vertexai.md`
  for managed API specifics
- `finops-ai-value-management.md` for AI investment governance, stage gates

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
