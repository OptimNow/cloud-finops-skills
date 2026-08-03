---
name: finops-aws-commitments
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Forecasting"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Finance"]
fcp_personas_collaborating: ["Engineering", "Procurement", "Leadership"]
fcp_maturity_entry: "Walk"
---

# AWS Commitment Discounts

> AWS rate-optimisation instruments and the decisions around them: Savings Plans
> (Compute, EC2 Instance, SageMaker AI, Database), Reserved Instances, Spot, the
> commitment decision tree, portfolio liquidity and phased purchasing, and EDP
> negotiation. Split out of `finops-aws.md` so a commitment question does not load
> the full AWS pattern catalogue. For AWS billing data, rightsizing, allocation and
> service-specific optimisation, see `finops-aws.md`.

---

## Commitment discounts

### Compute commitment instruments

AWS provides six distinct instruments for reducing compute costs, plus a separate
Database Savings Plan (covered in the database section below). Each has different
flexibility, discount depth, and risk profile. The most common mistake is treating
them as alternatives when they are designed to be layered.

AWS now documents **four Savings Plan types** in its plan-types reference: Compute,
EC2 Instance, SageMaker AI, and Database. SageMaker AI Savings Plans are a separate
product from Compute Savings Plans - **Compute Savings Plans no longer cover SageMaker**.
Source: https://docs.aws.amazon.com/savingsplans/latest/userguide/plan-types.html

**Instrument comparison:**

| Instrument | Discount depth | Flexibility | Commitment type | Term | Covers |
|---|---|---|---|---|---|
| EC2 Standard RI | Up to 72% | Lowest - locked to instance type, region, OS, tenancy | Capacity reservation + rate | 1yr or 3yr | EC2 only |
| EC2 Convertible RI | Up to 66% | Medium - can change instance family, OS, tenancy | Rate only (no capacity) | 1yr or 3yr | EC2 only |
| EC2 Instance Savings Plan | Up to 72% | Medium - locked to instance family and region | Spend-based ($/hr) | 1yr or 3yr | EC2 only |
| Compute Savings Plan | Up to 66% | Highest - any instance family, region, OS | Spend-based ($/hr) | 1yr or 3yr | EC2, Fargate, Lambda |
| SageMaker AI Savings Plan | Up to 64% | Flexible across SageMaker AI usage | Spend-based ($/hr) | 1yr or 3yr | SageMaker AI (training, inference, notebooks) |
| Spot Instances | Up to 90% | Variable - can be interrupted with 2 min notice | None (market-priced) | None | EC2, EKS nodes, EMR, SageMaker Training |

**Critical distinctions most teams miss:**

1. **EC2 Instance Savings Plans match Standard RI discount depth** (up to 72%) but
   are spend-based, not capacity-based. They offer the same discount with more
   flexibility (any size within the instance family). For most teams, EC2 Instance
   SPs have replaced Standard RIs as the default choice.

2. **Compute Savings Plans are shallower** (up to 66%) but cover EC2, Fargate, and
   Lambda. The flexibility premium costs ~6% discount depth vs EC2 Instance SPs.
   Compute SPs **do not cover SageMaker** - SageMaker AI workloads need their own
   SageMaker AI Savings Plan, which is a separate purchase.

3. **Standard RIs are the only instrument that reserves capacity.** If you need
   guaranteed capacity in a specific AZ (e.g. GPU instances, high-demand regions),
   Standard RIs with capacity reservation are the only option.

   **EC2 Auto Scaling reservations-first placement (as of July 2026).** EC2 Auto
   Scaling now defaults to a reservations-then-balanced strategy: it prioritises
   consuming existing Capacity Reservations (ODCRs, Capacity Blocks, and
   Interruptible Capacity Reservations) before balancing new capacity across
   Availability Zones. This improves reservation utilisation automatically and
   reduces the risk of idle reserved capacity when Auto Scaling groups scale up
   and down. For teams managing Capacity Reservations and ODCR sharing across
   accounts, this is a relevant governance and optimisation detail: reserved
   capacity is now more likely to be consumed by ASG-launched instances without
   manual placement configuration, which affects how you track capacity
   utilisation. **Sourcing note:** this behaviour is reported by a secondary
   newsletter source and has not been confirmed against AWS documentation. Verify
   against the EC2 Auto Scaling docs before relying on it in a commitment-coverage
   model - if ASGs do not in fact prioritise reservations, idle-reservation risk is
   higher than this section implies.

4. **Convertible RIs provide mid-term liquidity.** EC2 Instance Savings Plans offer
   similar flexibility at equal or better discount depth, but they are locked for
   the full term - no modifications allowed once purchased. Convertible RIs can be
   exchanged mid-term for a different configuration (instance family, OS, tenancy),
   which means you can reshape the commitment as workloads evolve without waiting
   for expiry. They sell in both 1-year and 3-year terms, so mid-term exchange is
   available at either horizon - a 1-year Convertible is the most liquid RI shape
   on offer. This mid-term exchange capability is one of three commitment
   liquidity mechanisms (see "Commitment portfolio liquidity" below). Note:
   Convertible RIs cannot be sold on the RI Marketplace - only Standard RIs can -
   so the liquidity trade-off is mid-term exchange flexibility vs secondary market
   resale.

5. **Standard RI marketplace liquidity is limited for EDP customers.** As of January
   2024, EDP customers cannot sell discounted RIs on the AWS Marketplace. This
   removes the secondary market resale option for EDP organisations, making
   Standard RIs a less liquid instrument. Non-EDP organisations retain the ability
   to sell unused Standard RIs to recover value from over-commitment. For EDP
   customers, phased purchasing with staggered expiry dates becomes the primary
   liquidity strategy (see "Commitment portfolio liquidity" below).

6. **Spot is not a commitment** - it is a market mechanism. It belongs in the compute
   cost strategy but should not be compared directly against commitment instruments.

### Compute commitment decision tree

```
START: What compute service runs the workload?
│
├── EC2 (including self-managed databases, custom AMIs, GPU workloads)
│   │
│   ├── Is the workload fault-tolerant and interruptible?
│   │   ├── YES → Use Spot Instances (up to 90% discount)
│   │   │         - Diversify across 6+ instance types and 3+ AZs
│   │   │         - Implement interruption handling (2-min warning)
│   │   │         - Use ASG mixed instances policy for On-Demand fallback
│   │   │         - Good for: batch, ML training, CI/CD, stateless web tiers
│   │   │
│   │   └── NO → Is the workload stable and predictable (90+ days)?
│   │       ├── NO → Stay On-Demand. Re-evaluate quarterly.
│   │       │
│   │       └── YES → Has it been right-sized?
│   │           ├── NO → Right-size first (see Compute rightsizing below)
│   │           │
│   │           └── YES → Do you need guaranteed capacity in a specific AZ?
│   │               ├── YES → EC2 Standard RI with capacity reservation
│   │               │         (only instrument that reserves capacity)
│   │               │
│   │               └── NO → Will it stay in the same instance family + region?
│   │                   ├── YES → EC2 Instance Savings Plan (up to 72%)
│   │                   │         Best default choice. Same discount as
│   │                   │         Standard RI, but flexible on size within
│   │                   │         the family. Spend-based, no capacity lock.
│   │                   │
│   │                   └── NO / UNSURE → Compute Savings Plan (up to 66%)
│   │                         Covers any instance family and region.
│   │                         ~6% discount penalty vs Instance SP, but
│   │                         protects against architecture changes.
│   │
│   └── Special case: GPU / accelerated compute (P, G, Inf, Trn families)
│       - Capacity scarcity is the primary risk, not just cost
│       - Standard RIs with capacity reservation may be necessary
│       - EC2 Instance SPs work if capacity is available on-demand
│       - Spot is viable for ML training with checkpointing
│       - For SageMaker-based ML: see SageMaker section below
│
├── Fargate (ECS or EKS on Fargate)
│   │
│   ├── Is usage stable and predictable?
│   │   ├── NO → Stay On-Demand. Fargate scales to zero, so idle cost
│   │   │         is already low. Focus on task right-sizing instead.
│   │   │
│   │   └── YES → Compute Savings Plan (only instrument that covers Fargate)
│   │             - Fargate Spot available for fault-tolerant ECS tasks
│   │               (up to 70% discount, but can be interrupted)
│   │             - EC2 Instance SPs and Standard RIs do NOT cover Fargate
│   │
│   └── Consider: would ECS/EKS on EC2 be cheaper?
│       At sustained high utilisation, EC2-backed containers with
│       Savings Plans or RIs can be 30-50% cheaper than Fargate.
│       Trade-off is cluster management overhead.
│
├── Lambda
│   │
│   ├── Is monthly Lambda spend significant (>$5K/month)?
│   │   ├── NO → Lambda cost is likely immaterial. Optimise duration
│   │   │         and memory allocation, but commitment is not worth
│   │   │         the management overhead.
│   │   │
│   │   └── YES → Compute Savings Plan (only instrument for Lambda)
│   │             - Discount applies to Lambda duration charges
│   │             - Does NOT apply to Lambda requests (invocations)
│   │             - Also consider: is the workload better suited to
│   │               Fargate or EC2? High-volume, long-running Lambda
│   │               functions often cost less on Fargate.
│   │
│   └── Lambda Provisioned Concurrency:
│       Charges for allocated concurrency even when idle. Treat this
│       as a form of capacity commitment - only use for latency-critical
│       functions where cold starts are unacceptable.
│
├── SageMaker AI (ML inference and training)
│   │
│   ├── Training jobs → Spot via SageMaker Managed Spot Training
│   │   (up to 90% discount; requires checkpoint support)
│   │
│   └── Inference endpoints
│       ├── Stable, predictable → SageMaker AI Savings Plan
│       │   (Compute Savings Plans no longer cover SageMaker -
│       │   this is the only Savings Plan that does)
│       ├── Variable → SageMaker Serverless Inference (no commitment)
│       └── Real-time with auto-scaling → evaluate Inference Components
│           for multi-model packing before committing
│
└── EKS (Kubernetes)
    │
    ├── EKS on EC2 → commitment applies to the EC2 node group
    │   (use EC2 decision tree above for the underlying instances)
    │   - Karpenter can shift node types dynamically; favour Compute
    │     Savings Plans over Instance SPs if Karpenter is active
    │   - Spot nodes work well for stateless pods with proper
    │     disruption budgets and node affinity rules
    │   - For cost attribution: see Kubernetes cost management below
    │   - EKS Auto Mode GPU fee reduction (see note below) makes
    │     Auto Mode more cost-competitive vs self-managed node groups
    │     for GPU workloads
    │
    └── EKS on Fargate → use Fargate decision tree above
```

### Savings Plan types - detailed comparison

| Dimension | Compute Savings Plan | EC2 Instance Savings Plan | SageMaker AI Savings Plan |
|---|---|---|---|
| Commitment | $/hr spend for 1yr or 3yr | $/hr spend for 1yr or 3yr | $/hr spend for 1yr or 3yr |
| Discount depth | Up to 66% | Up to 72% | Up to 64% |
| Instance family | Any | Locked to one family (e.g. m6i) | Any SageMaker AI instance |
| Region | Any | Locked to one region | Any |
| OS | Any | Any | N/A |
| Tenancy | Any | Any | N/A |
| Size | Any | Any (flexible within family) | Any |
| Covers Fargate | Yes | No | No |
| Covers Lambda | Yes | No | No |
| Covers SageMaker AI | **No** (changed - was previously included) | No | Yes |
| Payment options | No Upfront, Partial Upfront, All Upfront | No Upfront, Partial Upfront, All Upfront | No Upfront, Partial Upfront, All Upfront |
| Discount by payment | All Upfront > Partial > No Upfront | All Upfront > Partial > No Upfront | All Upfront > Partial > No Upfront |

A separate **Database Savings Plan** also exists (see the AWS database commitment
section below). Plan-types reference:
https://docs.aws.amazon.com/savingsplans/latest/userguide/plan-types.html

**Payment option guidance:**
- **No Upfront** - lowest risk, lowest discount. Best starting point for organisations
  new to commitments or with cash flow constraints.
- **Partial Upfront** - moderate risk, ~2-4% deeper discount. Good for steady-state
  workloads with 6+ months of stable history.
- **All Upfront** - highest discount (~5-8% deeper than No Upfront) but full capital
  outlay. Only justified for workloads with multi-year stability AND when the discount
  delta exceeds your cost of capital.

### Spot Instances

For fault-tolerant, interruptible workloads, Spot offers up to 90% discount over On-Demand.

**Appropriate workloads for Spot:**
- Batch processing, data pipelines, ML training jobs
- CI/CD build environments
- Stateless web tier behind a load balancer (with proper drain handling)
- Development and test environments
- EKS worker nodes for stateless pods (with pod disruption budgets)

**Not appropriate for Spot:**
- Stateful applications without checkpoint/resume logic
- Production databases
- Workloads with strict latency or availability SLAs
- Single-instance workloads with no failover

**Spot best practices:**
- Use Spot Instance pools across 6+ instance types and 3+ AZs to reduce interruption risk
- Implement interruption handling (2-minute warning via EC2 metadata or EventBridge)
- Use EC2 Auto Scaling mixed instances policy for automatic On-Demand fallback
- Set maximum price at On-Demand rate (never bid above OD - you lose the cost advantage)
- For containers: use Karpenter (EKS) or Fargate Spot (ECS) for managed Spot lifecycle
- Monitor Spot interruption frequency by instance type - some types are more stable

**Spot savings estimation:**
Spot discounts vary by instance type, region, and AZ. The Spot Placement Score API
indicates how likely a Spot request will be fulfilled. Use the EC2 Spot Advisor for
historical interruption rates. Typical realised savings are 60-80% (not the theoretical
90% maximum).

### Compute commitment layering strategy

The instruments are designed to be stacked, not chosen in isolation. The layering
order matters because AWS applies discounts in a specific sequence.

**Discount application order (AWS-defined):**
1. Spot pricing (market rate, applied first)
2. Reserved Instances (capacity + rate, applied to matching On-Demand usage)
3. Savings Plans (spend-based, applied to remaining eligible On-Demand usage)
4. EDP (portfolio discount, applied last to remaining spend)

**Recommended layering approach:**

```
Layer 1: Spot (for interruptible workloads)
  ↓ removes 15-40% of compute from the commitment equation entirely
Layer 2: Compute Savings Plans (broad baseline)
  ↓ covers the predictable floor across EC2 / Fargate / Lambda
Layer 3: EC2 Instance Savings Plans (high-stability EC2 workloads)
  ↓ captures the extra ~6% discount for workloads locked to a family+region
Layer 4: SageMaker AI Savings Plan (if SageMaker spend is material)
  ↓ separate purchase - Compute SPs no longer cover SageMaker AI
Layer 5: Database Savings Plan (if RDS/Aurora spend is material - see DB section)
  ↓ separate purchase - Compute SPs do not cover managed databases
Layer 6: Standard RIs (capacity reservation needs only)
  ↓ only where guaranteed AZ capacity is required (GPU, scarce types)
Layer 7: EDP (portfolio-wide, if eligible)
  ↓ applies on top of everything above for remaining On-Demand spend
Layer 8: On-Demand (variable / new workloads)
  ↓ buffer for growth, experimentation, and workloads under evaluation
```

**Sizing the commitment - the 70/20/10 guideline:**
- **70% of steady-state compute:** covered by Savings Plans and/or RIs. This is the
  floor that will not change during the commitment term.
- **20% variable buffer:** On-Demand capacity for scaling, new workloads, and seasonal
  variation. This is deliberately uncommitted.
- **10% Spot opportunity:** workloads that can tolerate interruption, running on Spot
  to capture the deepest discounts.

These ratios are starting points, not targets. Mature organisations (Run maturity) may
push committed coverage to 80%+ while maintaining Spot at 10-15%.

### Commitment portfolio liquidity

The deepest discount means nothing if you cannot adapt when workloads change.
Commitment liquidity - the ability to reshape, rebalance, or exit your commitment
portfolio without wasting money - is as important as discount depth. Every commitment
purchase decision should be evaluated on two axes: how much does it save, and how
much flexibility does it preserve?

AWS commitment instruments offer three forms of liquidity:

| Liquidity mechanism | How it works | Available on |
|---|---|---|
| **Secondary market resale** | Sell unused Standard RIs on the RI Marketplace to recover value | Standard RIs only (not available to EDP customers since Jan 2024) |
| **Mid-term exchange** | Exchange a Convertible RI for a different configuration (family, OS, tenancy) without losing the commitment value | Convertible RIs only |
| **Staggered expiry** | Purchase commitments in phased blocks so that only a fraction of the portfolio expires in any given quarter | All instruments (SPs, RIs) |

The first two are instrument-specific. The third - staggered expiry through phased
purchasing - is a portfolio management discipline that works with any instrument and
is the most reliable way to maintain liquidity.

Organisations that buy their full commitment in a single transaction have zero
liquidity until the term expires. If workloads shift, they pay for unused commitment
with no recourse. Organisations that build a diversified portfolio with staggered
expiry dates always have a portion of their commitment approaching renewal, creating
a natural rebalancing rhythm.

### Phased purchasing

Never buy the full commitment in a single transaction. Purchase in blocks to create
a portfolio of overlapping terms with staggered expiry dates. The cadence and block
size should match your consumption profile - not a fixed rule.

**Why phased purchasing matters:**
- **Reduces lock-in risk:** if architecture changes mid-term, only the current block
  is at risk - not the entire commitment
- **Creates natural re-evaluation points:** each purchase cycle forces a review of
  utilisation, workload stability, and architecture direction
- **Smooths cash flow:** Upfront payments are spread over time instead of concentrated
  in a single month
- **Enables course correction:** if utilisation drops on existing commitments, you
  can pause or reduce the next block instead of over-committing further
- **Captures pricing improvements:** newer instance families and Graviton adoption
  can be reflected in subsequent blocks

<!-- Deliberate mirror: this cadence/block-size table also appears in
finops-azure-commitments.md. Each commitments file is loaded standalone
(one provider per query), so the duplication is intentional - do not
deduplicate into a shared file. -->
**Cadence and block size by consumption profile:**

The purchasing cadence should follow consumption volatility. The more variable the
workload, the shorter the purchase cycle and the smaller each block. The principle:
your commitment refresh rate should be faster than your workload change rate.

| Consumption profile | Examples | Cadence | Block size | Rationale |
|---|---|---|---|---|
| Steady, predictable | Enterprise ERP, internal tools, back-office systems | Quarterly | 20-25% | Workloads barely move quarter to quarter. Larger blocks capture deeper coverage faster. |
| Moderate growth or gradual shifts | SaaS platforms, B2B applications, steady API services | Monthly to bi-monthly | 10-15% | Growth adds new capacity regularly. Smaller blocks incorporate new workloads without over-committing to the old baseline. |
| Seasonal or event-driven | Retail (holiday peaks), media (live events), gaming (launches) | Monthly to weekly | 5-10% | Demand swings mean the baseline shifts frequently. Small blocks commit only to the proven floor; peaks stay on On-Demand/Spot. |
| Highly volatile or early-stage | Startups, experimental workloads, pre-product-market-fit | Weekly or do not commit | 5% or less | If you cannot predict next month, do not lock in for a year. Stay on On-Demand with Spot until patterns stabilise. |

**The cadence can shift over time for the same company.** A retail company might buy
quarterly in Q1-Q3 (steady baseline) and switch to weekly in Q4 (holiday ramp) to
avoid committing to peak capacity that evaporates in January. A SaaS company might
start with monthly cadence during a growth phase and shift to quarterly once the
growth rate stabilises.

**Block size and cadence are inversely related:** higher frequency = smaller blocks.
This keeps the total portfolio size similar but distributes the risk across more,
smaller decisions.

**Phased purchasing framework (quarterly example for steady consumption):**

```
Quarter 1: Buy 20-25% of target commitment (the floor you are certain about)
  → Monitor utilisation for 30 days
  → If utilisation >80%: proceed to next block
  → If utilisation <80%: investigate before buying more

Quarter 2: Buy next 15-20% block
  → Reassess workload stability and architecture plans
  → Adjust instrument mix if workload profile has shifted

Quarter 3: Buy next 15-20% block
  → By now you have 50-65% of target covered
  → Remaining gap is intentional On-Demand buffer

Quarter 4: Evaluate whether to buy more or hold
  → Early blocks from Q1 of previous year start approaching renewal
  → Begin planning the next cycle
```

**Phased purchasing framework (monthly example for moderate growth):**

```
Month 1: Buy 10-12% of target (proven steady-state floor)
  → Monitor utilisation for 2 weeks
Month 2: Buy next 10-12% block
  → Incorporate any new workloads that stabilised last month
Month 3: Buy next 10-12% block
  → Review: are earlier blocks still >80% utilised?
Months 4-8: Continue at 10-12% per month, pausing if utilisation drops
Month 9+: Evaluate - early blocks approaching renewal
  → Shift to maintenance mode: renew justified blocks, drop the rest
```

**Portfolio view - staggered expiry example (1-year terms, quarterly cadence):**

| Block | Purchased | Expires | % of total | Instrument |
|---|---|---|---|---|
| Block 1 | Jan 2026 | Jan 2027 | 25% | Compute SP (broad baseline) |
| Block 2 | Apr 2026 | Apr 2027 | 20% | EC2 Instance SP (stable m6i workloads) |
| Block 3 | Jul 2026 | Jul 2027 | 15% | EC2 Instance SP (stable r6g workloads) |
| Block 4 | Oct 2026 | Oct 2027 | 10% | Compute SP (new Fargate workloads) |
| On-Demand | - | - | 30% | Buffer for variable / new workloads |

With staggered expiry, no more than 25% of your commitment portfolio expires in any
single quarter. This means you are never forced into a large, rushed repurchase
decision.

**3-year term phasing:**
For 3-year commitments (deeper discounts), phasing is even more critical. Buy in
smaller blocks (10-15% each) and stagger across 6-month intervals. The longer the
term, the smaller each block should be - because the risk of architecture change
over 3 years is substantially higher than over 1 year.

**Portfolio management cadence:**
- **At each purchase cycle** (weekly/monthly/quarterly depending on profile): review
  SP/RI utilisation dashboard. Flag any commitment below 80%. Decide whether to buy
  the next block, adjust the instrument mix, or pause.
- **At each expiry:** do not auto-renew. Re-evaluate the workload: has it grown,
  shrunk, migrated to a different service, or been decommissioned? Renew only what
  is still justified.
- **Quarterly (regardless of purchase cadence):** strategic review of commitment
  coverage ratio, instrument mix, and upcoming expiries.
- **Annually:** review the overall commitment strategy against the organisation's
  cloud roadmap. Adjust the target coverage ratio, cadence, and instrument mix.

**Common commitment mistakes:**
- Buying commitments before right-sizing (committing to waste)
- Over-committing: purchasing for peak usage instead of steady-state floor
- Ignoring architecture changes: migrating from EC2 to Fargate mid-term while holding
  EC2 Instance SPs that no longer apply
- Treating Spot savings as guaranteed in financial forecasts (Spot availability fluctuates)
- Purchasing All Upfront without comparing the discount delta to the organisation's
  cost of capital
- Buying 3-year terms for workloads that may be re-architected within 18 months
- Not monitoring utilisation: an SP or RI below 80% utilisation means you are paying
  for unused commitment and should adjust the next purchase

**Key metrics:**
- **SP/RI Utilisation:** Target >80%. Below this, the commitment is oversized.
- **SP/RI Coverage:** Target 70% (Walk maturity), 80%+ (Run maturity).
- **Effective Savings Rate:** actual savings / theoretical maximum savings. Measures
  how well commitments are matched to real usage.
- **Break-even period:** should be <9 months for 1-year terms, <15 months for 3-year.
- **Commitment waste:** hours where committed capacity had no matching usage.

**Pre-purchase checklist:**
- [ ] Workload has run stably for 90+ days
- [ ] Workload has been right-sized (do not commit to waste)
- [ ] No planned architecture changes during the commitment term
- [ ] All resources are tagged and attributable to an owner
- [ ] Utilisation will sustain through the full term
- [ ] Finance has approved the capital outlay (for Upfront payments)
- [ ] Break-even period is acceptable given the workload risk profile
- [ ] Existing SP/RI utilisation is >80% before purchasing more

**Diagnostic questions:**
- What is your current SP/RI utilisation rate? If below 80%, do not buy more - fix
  the mismatch first.
- What percentage of EC2 spend is On-Demand vs committed vs Spot? The goal is to
  minimise On-Demand for steady-state workloads.
- Are any Compute Savings Plans covering workloads that could be on cheaper EC2
  Instance Savings Plans instead? (leaving ~6% on the table)
- Do you have Convertible RIs? If so, are you actively exchanging them as workloads
  shift, or should they be allowed to expire and replaced with EC2 Instance SPs?
- Are engineering teams launching new instance families (Graviton, AMD) that might
  invalidate existing EC2 Instance SP commitments?
- Is Karpenter or Cluster Autoscaler shifting EKS node types dynamically? If yes,
  Compute SPs are safer than Instance SPs for the underlying EC2.
- Are there workloads on Fargate or Lambda that appear small individually but add
  up to significant monthly spend when aggregated?
- Are you buying commitments in phased blocks (10-25%) with staggered expiry dates,
  or purchasing the full amount in a single transaction? Single-purchase strategies
  concentrate renewal risk and reduce flexibility.
- What percentage of your commitment portfolio expires in any single quarter? If
  more than 30%, the portfolio is insufficiently diversified.

### Enterprise Discount Program (EDP)
<!-- src:optimnow-edp-guide -->

The AWS Enterprise Discount Program (EDP) - also referred to as a Private Pricing
Agreement (PPA) - is a contractual commitment where an organisation pledges a
specific dollar amount of spend over a one-to-five-year term. In return, AWS provides
a percentage discount that applies broadly across more than 200 services. Unlike
Savings Plans or Reserved Instances that target specific compute or database
resources, an EDP acts as a portfolio-wide discount covering compute, storage,
databases, networking, and eligible AWS Marketplace purchases.

**Who it is for:**
EDP is designed for organisations spending $1 million or more annually on AWS.
Smaller organisations with a strong growth trajectory may negotiate entry via the
AWS Private Pricing Term Sheet (PPTS), which lowers the threshold to approximately
$500,000 in annual spend.

**How the discount is applied:**
The EDP discount is applied after Reserved Instance and Savings Plan discounts. This
means the EDP provides additional savings on top of already-discounted compute. When
combined with aggressive rate optimisation (RIs, Savings Plans, Spot), mature
organisations can achieve an overall effective discount of 40-70% off On-Demand rates.

**Eligibility requirements and hidden costs:**
- Minimum annual spend of $1 million (negotiable for high-growth accounts)
- AWS requires a growth commitment - typically 10-20% year-over-year increase
  over trailing spend. This growth tax is non-negotiable and creates risk for
  organisations with unpredictable workloads
- The commitment floor only moves upward - you cannot reduce your pledge in
  subsequent years of the contract
- Mandatory Enterprise Support (3-10% of monthly usage). For mid-sized
  organisations, support fees can erode a significant portion of the EDP savings
  if not factored into the financial model

**Discount tiers and negotiation leverage:**
Discount rates are determined by annual commitment level and contract duration.
Longer terms yield deeper discounts. Strategic pricing breaks occur at specific
annual spend milestones. A modest increase in committed volume near a tier
boundary can yield a disproportionate jump in discount rate.

**EDP negotiation checklist:**
- [ ] Conduct a forensic cost audit before negotiation - eliminate waste to lower
      your baseline commitment (do not commit to inefficiency)
- [ ] Clarify pre- vs post-discount commitment measurement. If you commit $2M and
      receive $200K in discounts, negotiate for the full $2M to count toward
      retiring your commitment, not just the $1.8M net spend
- [ ] Negotiate Marketplace inclusion terms. Default is 25% of committed spend;
      negotiate to 30-35% if your stack relies on third-party SaaS from AWS
      Marketplace
- [ ] Request quarterly true-ups rather than annual ones for better pacing
      visibility
- [ ] Define which services are excluded from the discount - data transfer fees
      and specialised managed services can represent hidden costs
- [ ] Confirm that your EDP covers Marketplace SKUs for key vendors -
      not all Marketplace transactions are EDP-eligible
- [ ] Factor Enterprise Support cost into the total cost of ownership before
      signing

**EDP preparation roadmap (source: OptimNow):**

| Stage | Timeline | Key activities |
|---|---|---|
| Suitability assessment | Months 1-2 | Review current AWS spend, evaluate growth trajectory (minimum 10% YoY), initial discussions with AWS |
| Preparation | Months 2-5 | Build 3-5 year cloud usage forecast (include Marketplace SaaS), optimise resources before baseline is set, internal stakeholder alignment |
| Negotiation | Months 5-11 | Negotiate commitment levels, term lengths, growth expectations; legal and financial review of proposed agreement |
| Implementation | Month 12 | Sign and activate the EDP, communicate terms internally |
| Management and optimisation | Months 13-15 | Monitor usage against commitment, layer RIs/Savings Plans, use FinOps tooling for continuous optimisation |
| Review and adaptation | Month 16+ | Quarterly performance reviews, strategy adjustments, renewal preparation |

**Internal alignment - who must be at the table:**
- Engineering/business units: confirm AWS is the right platform for the workload
- Finance: evaluate multi-year commitment impact on P&L and margins
- Procurement: coordinate negotiation process and define success criteria
- Legal: review all terms, ensure specific requirements are included
- CEO/CTO/CFO: must be in complete agreement before signing. Without this
  alignment, an EDP can create strategic misalignment and financial risk

**Common EDP mistakes:**
- Committing before optimising. AWS calculates EDP offers based on gross spend,
  which often includes significant waste. Clean the house first
- Choosing an overly long term (4-5 years) with aggressive growth targets. As
  FinOps maturity improves and cost optimisation becomes more effective, meeting
  high growth commitments becomes harder - the more efficient you become, the
  harder it is to meet the spend floor
- Failing to include Marketplace SaaS in the EDP forecast. Marketplace purchases
  count toward commitment but are often planned by different teams
- Not considering alternatives: AWS Savings Plans, Reserved Instances, or the
  PPTS may be more appropriate for organisations with unpredictable usage patterns
  or in early growth stages

**EDP and rate optimisation layering:**
An EDP is not a substitute for active resource management. It is a foundation that
works best when stacked with other instruments:
- Use the EDP as the portfolio-wide base discount
- Layer Savings Plans and Reserved Instances on top for steady-state compute
- Use Spot Instances for fault-tolerant workloads
- Note: as of January 2024, EDP customers are prohibited from selling discounted
  RIs on the AWS Marketplace, making internal commitment forecasting and liquidity
  management more critical

---


---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
