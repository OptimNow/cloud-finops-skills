---
name: finops-genai-capacity
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Usage Optimization", "Architecting & Workload Placement"]
fcp_phases: ["Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Product", "Finance"]
fcp_maturity_entry: "Walk"
---

# FinOps for GenAI: Capacity Models

> Cross-provider reference covering provisioned vs shared (pay-as-you-go) capacity for
> GenAI inference. Covers traffic shape analysis, waste types, spillover mechanics,
> performance trade-offs, and the structural differences between AWS Bedrock, GCP Vertex AI,
> and Azure OpenAI Service provisioned capacity models.
>
> Applies to hyperscaler-managed inference services. Does not cover custom model training
> (SageMaker, Azure ML). For self-hosted serving infrastructure (vLLM/SGLang on rented or
> owned GPUs) and the self-hosted-vs-managed decision framework, see
> `finops-ai-self-hosted-vs-managed.md`.
>
> Distilled from: "Navigating GenAI Capacity Options" - FinOps Foundation GenAI Working Group, 2025/2026.

---

## Capacity model fundamentals

### Shared capacity (pay-as-you-go)

The default model. You pay per token consumed, drawing from a shared provider pool.

- No upfront commitment
- No performance guarantees - latency can spike during peak demand
- Same data-use terms as provisioned on the major hyperscalers: Azure, AWS Bedrock,
  and Google all exclude customer prompts/completions from foundation-model training
  on shared capacity too. The shared-tier trade-off is performance isolation, not
  training exposure
- Suitable for: early adoption, variable/unpredictable workloads, non-latency-sensitive use cases

### Provisioned capacity (reserved)

You purchase a fixed block of throughput for a defined term (monthly or annual). You pay
for that capacity 24/7 regardless of actual utilisation.

- Dedicated throughput - predictable latency
- Workload isolation (training exclusion is not the differentiator - the hyperscalers
  apply it to shared capacity as well)
- Comes with higher uptime SLAs
- Suitable for: consistent high-volume workloads, latency-sensitive applications,
  production workloads needing performance isolation

---

## Traffic shape: the primary decision variable

The core question before any provisioned capacity purchase is: **what does your traffic
look like over 24 hours?**

| Traffic pattern | Provisioned capacity fit | Rationale |
|---|---|---|
| Consistent, high-volume (24/7) | Strong fit - likely cost savings | High utilisation of reserved capacity |
| Business hours peaks, quiet nights | Weak fit - potential trap | Reserved capacity idles 16+ hours/day |
| Bursty, unpredictable | Weak fit without spillover | Must reserve for peak; wastes money otherwise |
| Latency-sensitive regardless of volume | Justified - performance, not savings | Pay premium for SLA and TTFT/OTPS guarantees |

**Key principle:** provisioned capacity is like a Savings Plan or CUD - the break-even
depends on your coverage target and actual utilisation, not just the per-token rate.

---

## Waste types specific to provisioned capacity

### Idle allocated capacity

You have reserved capacity assigned to a model, but your workload does not use it.

- Example: 100% reservation, 15% peak utilisation → paying for 85% idle capacity
- Amplified when running workloads with high output token ratios (output tokens are
  billed at 4-8x the input rate on current models)
- Most common form of GenAI capacity waste

### Unallocated capacity (Azure-specific)

You have reserved a pool of capacity units (PTUs) but have not deployed models against them.

- Reservation and deployment are decoupled on Azure
- New model releases may have no available capacity, leaving PTUs reserved but unused
  while waiting for model availability
- See Azure section for details

---

## Spillover

Spillover automatically routes overflow traffic to shared (pay-as-you-go) capacity when
provisioned capacity is fully utilised, instead of returning a throttle error (HTTP 429).

**Example:** 1,000 TPM reserved. A spike sends 1,200 requests/min. The extra 200 route
to shared capacity at pay-as-you-go rates.

### When spillover changes the calculus

- Allows you to size reservations for average load, not peak load
- Reduces outage risk without requiring over-provisioning
- Overflowed requests are billed at pay-as-you-go rates - costs become variable again
  during spikes

### Provider availability

| Provider | Spillover support |
|---|---|
| Azure | Built-in feature |
| AWS Bedrock | Must build failover logic yourself |
| GCP Vertex AI | Default pay-as-you-go for supported Gemini models, request headers control dedicated/shared/reject behaviour |

Source for Vertex AI spillover defaults: https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput/use-provisioned-throughput

---

## Performance metrics that matter for GenAI

End-to-end latency is less relevant for streaming applications. The metrics FinOps and
engineering teams should align on are:

| Metric | Definition | Why it matters |
|---|---|---|
| Time to First Token (TTFT) | Time from prompt submission to first token returned | Perceived responsiveness for users |
| Output Tokens Per Second (OTPS) | Speed at which tokens stream to the user | Perceived reading speed; also governs reasoning model "thinking" speed |

Provisioned capacity significantly improves both TTFT and OTPS compared to shared capacity.
For latency-sensitive applications, this performance gain alone may justify higher cost.

---

## Capacity unit pricing: do not assume provisioned is cheaper

Provisioned capacity pricing is expressed in provider-specific units (PTUs, throughput
units, scale tier units). To compare against standard rates, you must normalise to cost
per million tokens at 100% utilisation.

**The result may be higher than pay-as-you-go**, even at full utilisation. In that case,
provisioned capacity is a performance and SLA purchase, not a cost-saving one.

| Model | Provisioned vs standard input, at 100% utilisation |
|---|---|
| GPT-5 | +67% |
| GPT-4.1 | +27% |

*Sourcing note:* these deltas are **derived estimates** (observed August 2026) from a
FinOps Foundation working-group analysis, not Microsoft-published rates - Microsoft
prices PTUs only in $/PTU/hour, and the conversion depends on throughput assumptions
and on which price point (hourly vs 1-month vs 1-year reservation) is used. Treat
the deltas as illustrative of the pattern, and rebuild the math from current
$/PTU/hour rates for any client decision.

**Implication:** always compute your break-even utilisation rate before purchasing.
For some models, provisioned capacity never generates token-cost savings - it is purely
a performance and SLA product.

### Normalisation checklist

- [ ] Identify the capacity unit type (PTU, throughput unit, scale tier unit)
- [ ] Identify billing frequency (hourly, daily, monthly, annual)
- [ ] Obtain vendor TPM estimate for the unit - treat as rough estimate only
- [ ] Load-test your specific workload (realistic input/output token mix + caching)
- [ ] Calculate effective cost per million tokens at your expected utilisation rate
- [ ] Compare against standard rate to determine break-even utilisation
- [ ] Factor in enterprise/EA discounts on provisioned purchases

---

## Hyperscaler capacity model comparison

| Dimension | AWS Bedrock | GCP Vertex AI | Azure OpenAI Service |
|---|---|---|---|
| Reservation unit | Model-specific SKU | Publisher-specific SKU | PTU pool (model-agnostic) |
| Model flexibility | None - locked to specific model | Can switch within same publisher | Full - reassign PTUs to any model |
| Model switching on renewal | Must re-purchase | Can upgrade within publisher family | Reassign PTUs dynamically |
| Capacity guarantee | Yes - reservation = capacity | Yes | No - reservation ≠ guaranteed model availability |
| Waste type | Idle allocated capacity | Idle allocated capacity | Idle allocated + unallocated capacity |
| Spillover | Build yourself | Default PAYG spillover (header-controlled) | Available, opt-in configuration |
| Best for | Stable workloads, known model, cost predictability | GCP-native shops, Gemini ecosystem | Flexibility-first, frequent model updates |

---

## Data privacy and traffic segmentation

On the major hyperscalers, training exclusion applies to shared and provisioned
capacity alike - do not buy provisioned capacity to obtain it. What provisioned
capacity does add is workload isolation and, in some regulated contexts, a cleaner
compliance narrative.

**Traffic affinitisation strategy:** where isolation (not training exclusion) is the
requirement, route requests containing PII or confidential data to provisioned
endpoints and non-sensitive traffic to shared capacity. This reduces the required
reservation size (and cost) while keeping sensitive workloads on isolated capacity.

---

## The capacity cliff and the pool-siloing anti-pattern

**The cliff (rule of thumb, Pay-i-reported):** around $3M annual spend concentrated
on a single provider + single model, shared (PAYG) infrastructure starts failing in
production - time-outs, rate limits, shortages - and provisioned capacity becomes
forced, not optional. Failures typically surface when a new agent or team is
onboarded, because provisioned capacity does not degrade gracefully.

**Treat the transition as a graduation:** the variable-cost line becomes a
fixed-cost line, with the planning discipline that implies (utilisation targets,
break-even analysis, renewal governance - see sections above). Load-test against
the real production traffic mix *before* crossing the threshold, and negotiate
mid-commitment model refresh terms - a newer model will ship during your term.

**The pool-siloing anti-pattern.** Defensive engineering teams provision a separate
capacity pool per use case so no agent can starve another. This destroys the
economics of provisioning, which depend on diverse workloads sharing peaks.
Observed result: paying for 2-3x the capacity actually needed (Pay-i-reported).

- Default: shared pools mixing workloads with different traffic shapes, spillover
  used deliberately (sized for average, spill the peaks) - not as a failover accident
- Silo only for regulatory or hard-isolation reasons, and price the silo premium
  explicitly so the requesting team sees it
- Same portfolio logic as commitment management: capacity is a portfolio, reviewed
  as one

---

## Decision framework

### Step 1 - Qualify the workload

- [ ] Has the workload run in production for 90+ days with measurable traffic patterns?
- [ ] Is the traffic shape consistent enough to estimate average and peak TPM?
- [ ] Is the workload latency-sensitive (user-facing, streaming)?
- [ ] Are there data privacy or compliance requirements?

### Step 2 - Model the economics

- [ ] Calculate cost at standard (PAYG) rates at current and projected volume
- [ ] Obtain provisioned capacity unit pricing from the provider
- [ ] Normalise to cost per million tokens at 100%, 80%, and 50% utilisation
- [ ] Determine break-even utilisation rate
- [ ] Estimate realistic utilisation based on traffic shape

### Step 3 - Choose capacity model

| Condition | Recommendation |
|---|---|
| High utilisation + break-even favourable | Provisioned - cost + performance |
| Latency-sensitive regardless of economics | Provisioned - performance justifies premium |
| Data privacy requirements | Provisioned - segmented by sensitivity |
| Bursty traffic, no spillover available | PAYG or hybrid with manual failover |
| Uncertain workload, early stage | PAYG until traffic patterns are established |

### Step 4 - Choose provider model

| Priority | Provider preference |
|---|---|
| Cost predictability, stable model choice | AWS Bedrock or GCP Vertex AI |
| Model flexibility, frequent updates | Azure OpenAI Service (PTU) |
| Multi-model / multi-publisher portfolio | Split reservations across providers |

---

## Governance checklist

- [ ] Treat provisioned capacity utilisation as a tracked metric (target >80%)
- [ ] Alert on unallocated PTUs (Azure) - treat as idle reserved capacity
- [ ] Load-test before purchasing - vendor TPM figures are rough estimates
- [ ] Do not commit to a model you expect to replace within the reservation term (AWS/GCP)
- [ ] Define a spillover policy: what percentage of requests can spill to PAYG within SLA?
- [ ] Apply enterprise discounts to provisioned purchases - verify they apply
- [ ] Review reservations at renewal - model landscape changes fast

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
