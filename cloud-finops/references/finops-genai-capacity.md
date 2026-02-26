# FinOps for GenAI: Capacity Models

> Cross-provider reference covering provisioned vs shared (pay-as-you-go) capacity for
> GenAI inference. Covers traffic shape analysis, waste types, spillover mechanics,
> performance trade-offs, and the structural differences between AWS Bedrock, GCP Vertex AI,
> and Azure OpenAI Service provisioned capacity models.
>
> Applies to hyperscaler-managed inference services. Does not cover custom model training
> (SageMaker, Azure ML) or self-hosted serving infrastructure.
>
> Distilled from: "Navigating GenAI Capacity Options"  - FinOps Foundation GenAI Working Group, 2025/2026.

---

## Capacity model fundamentals

### Shared capacity (pay-as-you-go)

The default model. You pay per token consumed, drawing from a shared provider pool.

- No upfront commitment
- No performance guarantees  - latency can spike during peak demand
- No data privacy guarantees (data may be used for model training)
- Suitable for: early adoption, variable/unpredictable workloads, non-latency-sensitive use cases

### Provisioned capacity (reserved)

You purchase a fixed block of throughput for a defined term (monthly or annual). You pay
for that capacity 24/7 regardless of actual utilization.

- Dedicated throughput  - predictable latency
- Typically includes data privacy guarantees (no training on your data)
- Comes with higher uptime SLAs
- Suitable for: consistent high-volume workloads, latency-sensitive applications, production
  workloads with privacy requirements

---

## Traffic shape: the primary decision variable

The core question before any provisioned capacity purchase is: **what does your traffic
look like over 24 hours?**

| Traffic pattern | Provisioned capacity fit | Rationale |
|---|---|---|
| Consistent, high-volume (24/7) | Strong fit  - likely cost savings | High utilization of reserved capacity |
| Business hours peaks, quiet nights | Weak fit  - potential trap | Reserved capacity idles 16+ hours/day |
| Bursty, unpredictable | Weak fit without spillover | Must reserve for peak; wastes money otherwise |
| Latency-sensitive regardless of volume | Justified  - performance, not savings | Pay premium for SLA and TTFT/OTPS guarantees |

**Key principle:** provisioned capacity is like a Savings Plan or CUD  - the break-even
depends on your coverage target and actual utilization, not just the per-token rate.

---

## Waste types specific to provisioned capacity

### Idle allocated capacity

You have reserved capacity assigned to a model, but your workload does not use it.

- Example: 100% reservation, 15% peak utilization → paying for 85% idle capacity
- Amplified when running workloads with high output token ratios (output tokens are ~3×
  more computationally expensive than input tokens)
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
provisioned capacity is fully utilized, instead of returning a throttle error (HTTP 429).

**Example:** 1,000 TPM reserved. A spike sends 1,200 requests/min. The extra 200 route
to shared capacity at pay-as-you-go rates.

### When spillover changes the calculus

- Allows you to size reservations for average load, not peak load
- Reduces outage risk without requiring over-provisioning
- Overflowed requests are billed at pay-as-you-go rates  - costs become variable again
  during spikes

### Provider availability

| Provider | Spillover support |
|---|---|
| Azure | Built-in feature |
| AWS Bedrock | Must build failover logic yourself |
| GCP Vertex AI | Must build failover logic yourself |

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
units, scale tier units). To compare against standard rates, you must normalize to cost
per million tokens at 100% utilization.

**The result may be higher than pay-as-you-go**, even at full utilization. In that case,
provisioned capacity is a performance and SLA purchase, not a cost-saving one.

| Model | Standard input | Provisioned input | Delta at 100% utilization |
|---|---|---|---|
| GPT-5 | $1.25/MTok | $2.08/MTok | +67% |
| GPT-4.1 | $2.00/MTok | $2.55/MTok | +27% |

**Implication:** always compute your break-even utilization rate before purchasing.
For some models, provisioned capacity never generates token-cost savings  - it is purely
a performance and SLA product.

### Normalization checklist

- [ ] Identify the capacity unit type (PTU, throughput unit, scale tier unit)
- [ ] Identify billing frequency (hourly, daily, monthly, annual)
- [ ] Obtain vendor TPM estimate for the unit  - treat as rough estimate only
- [ ] Load-test your specific workload (realistic input/output token mix + caching)
- [ ] Calculate effective cost per million tokens at your expected utilization rate
- [ ] Compare against standard rate to determine break-even utilization
- [ ] Factor in enterprise/EA discounts on provisioned purchases

---

## Hyperscaler capacity model comparison

| Dimension | AWS Bedrock | GCP Vertex AI | Azure OpenAI Service |
|---|---|---|---|
| Reservation unit | Model-specific SKU | Publisher-specific SKU | PTU pool (model-agnostic) |
| Model flexibility | None  - locked to specific model | Can switch within same publisher | Full  - reassign PTUs to any model |
| Model switching on renewal | Must re-purchase | Can upgrade within publisher family | Reassign PTUs dynamically |
| Capacity guarantee | Yes  - reservation = capacity | Yes | No  - reservation ≠ guaranteed model availability |
| Waste type | Idle allocated capacity | Idle allocated capacity | Idle allocated + unallocated capacity |
| Spillover | Build yourself | Build yourself | Built-in |
| Best for | Stable workloads, known model, cost predictability | GCP-native shops, Gemini ecosystem | Flexibility-first, frequent model updates |

---

## Data privacy and traffic segmentation

Provisioned capacity typically guarantees that your data is not used to train future models.
Shared capacity does not offer this guarantee.

**Traffic affinitization strategy:** route requests containing PII or confidential data
to provisioned endpoints; route non-sensitive traffic to shared capacity. This reduces
the required reservation size (and cost) while maintaining data privacy for sensitive workloads.

---

## Decision framework

### Step 1  - Qualify the workload

- [ ] Has the workload run in production for 90+ days with measurable traffic patterns?
- [ ] Is the traffic shape consistent enough to estimate average and peak TPM?
- [ ] Is the workload latency-sensitive (user-facing, streaming)?
- [ ] Are there data privacy or compliance requirements?

### Step 2  - Model the economics

- [ ] Calculate cost at standard (PAYG) rates at current and projected volume
- [ ] Obtain provisioned capacity unit pricing from the provider
- [ ] Normalize to cost per million tokens at 100%, 80%, and 50% utilization
- [ ] Determine break-even utilization rate
- [ ] Estimate realistic utilization based on traffic shape

### Step 3  - Choose capacity model

| Condition | Recommendation |
|---|---|
| High utilization + break-even favorable | Provisioned  - cost + performance |
| Latency-sensitive regardless of economics | Provisioned  - performance justifies premium |
| Data privacy requirements | Provisioned  - segmented by sensitivity |
| Bursty traffic, no spillover available | PAYG or hybrid with manual failover |
| Uncertain workload, early stage | PAYG until traffic patterns are established |

### Step 4  - Choose provider model

| Priority | Provider preference |
|---|---|
| Cost predictability, stable model choice | AWS Bedrock or GCP Vertex AI |
| Model flexibility, frequent updates | Azure OpenAI Service (PTU) |
| Multi-model / multi-publisher portfolio | Split reservations across providers |

---

## Governance checklist

- [ ] Treat provisioned capacity utilization as a tracked metric (target >80%)
- [ ] Alert on unallocated PTUs (Azure)  - treat as idle reserved capacity
- [ ] Load-test before purchasing  - vendor TPM figures are rough estimates
- [ ] Do not commit to a model you expect to replace within the reservation term (AWS/GCP)
- [ ] Define a spillover policy: what percentage of requests can spill to PAYG within SLA?
- [ ] Apply enterprise discounts to provisioned purchases  - verify they apply
- [ ] Review reservations at renewal  - model landscape changes fast

---

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io)  - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
