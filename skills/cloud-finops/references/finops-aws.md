---
name: finops-aws
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Usage Optimization", "Data Ingestion", "Reporting & Analytics"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "Procurement"]
fcp_maturity_entry: "Walk"
---

# FinOps on AWS

> AWS-specific guidance covering cost management tools, commitment discounts, compute
> rightsizing, cost allocation, and governance. Covers CUR, Cost Explorer, Compute
> Optimizer, Trusted Advisor, Savings Plans, Reserved Instances, Enterprise Discount
> Program (EDP) negotiation, RDS cost management strategy, and AWS-native FinOps patterns.

---

## AWS cost data foundation
<!-- src:37b46c22605776cb -->

### Cost and Usage Report (CUR)

CUR is the most granular billing data source AWS provides. It is the correct data source
for any serious FinOps implementation on AWS.

**Why CUR over Cost Explorer API:**
- Line-item granularity - every resource charge, every hour
- Includes resource tags, usage types, and pricing details not available in Cost Explorer
- Exportable to S3 for integration with third-party tools, Athena, or Redshift

**CUR setup checklist:**
- [ ] Enable CUR (or CUR 2.0 via AWS Data Exports - see below) in the management (payer) account
- [ ] Configure S3 bucket with appropriate retention and access policies
- [ ] Enable resource IDs (required for tag-level allocation)
- [ ] Select hourly granularity (daily is insufficient for anomaly detection)
- [ ] Enable Athena integration for SQL-based analysis

### AWS Data Exports for FOCUS 1.2

AWS Data Exports is the modern delivery mechanism for billing data, replacing the legacy
CUR for new deployments. As of **19 November 2025**, AWS Data Exports for FOCUS 1.2 is
generally available - the canonical path for FOCUS-conformant cost data on AWS.

**What this means in practice:**
- New customers should set up Data Exports for FOCUS 1.2 directly, not legacy CUR + FOCUS
  format flag.
- Existing CUR consumers can run CUR and Data Exports in parallel during transition.
- FOCUS 1.2 data flows into the same S3-backed pattern: configure once, query via Athena
  or any FOCUS-aware tool.
- For multi-cloud customers, the FOCUS 1.2 schema aligns with Azure Cost Management's
  FOCUS 1.2 export and GCP's FOCUS 1.0 export, enabling true cross-cloud
  normalisation in a single warehouse.

**Cross-account delivery (March 2026, GA).** AWS Data Exports now supports
delivery directly to an S3 bucket in a different (authorised) account. This is
the path AWS-native landing zones and centralised FinOps warehouses have been
asking for: payer accounts can publish FOCUS 1.2 / CUR 2.0 exports straight into
the FinOps team's analytics account without an intermediate copy step or a
cross-account replication rule. Configure via the destination bucket policy on
the receiving side and the export configuration on the source side.
- Removes the previous "copy from payer S3 to analytics S3" pipeline that many
  organisations had to operate themselves.
- Simplifies the IAM model: one bucket policy on the analytics side rather than
  per-payer-account IAM roles.
- Especially useful for organisations that consolidate billing across multiple
  AWS Organizations (M&A integrations, multi-payer setups, partner-resold
  accounts).

Sources: https://aws.amazon.com/about-aws/whats-new/2025/11/aws-data-exports-focus-1-2-available/
and https://aws.amazon.com/about-aws/whats-new/2026/03/aws-data-exports-cross-account-delivery-cost/

**Common CUR analysis queries (Athena):**
```sql
-- Top 10 services by cost, current month
SELECT line_item_product_code,
       ROUND(SUM(line_item_unblended_cost), 2) AS total_cost
FROM cur_table
WHERE month = MONTH(CURRENT_DATE) AND year = YEAR(CURRENT_DATE)
GROUP BY line_item_product_code
ORDER BY total_cost DESC
LIMIT 10;

-- Untagged resources by cost
SELECT line_item_resource_id,
       line_item_product_code,
       ROUND(SUM(line_item_unblended_cost), 2) AS cost
FROM cur_table
WHERE resource_tags_user_environment IS NULL
  AND line_item_line_item_type = 'Usage'
GROUP BY 1, 2
ORDER BY cost DESC;
```

### AWS Cost Explorer

Cost Explorer provides pre-built visualizations and the Cost Explorer API for
programmatic access. It is the right tool for quick analysis and reporting; CUR is the
right tool for detailed attribution and custom tooling.

**Cost Explorer capabilities and limitations (as of April 2026):**
- 24-48 hour data lag (unacceptable for real-time AI cost management)
- **Hourly granularity** is now an opt-in feature in Cost Explorer (no longer API-only).
  Enable per management account; data retained 14 days. Source:
  https://docs.aws.amazon.com/cost-management/latest/userguide/ce-services-hourly.html
- **Resource-level daily granularity** is also an opt-in feature - exposes per-resource
  daily cost without requiring the legacy "resource-level data" paid tier. Retention
  and limits documented per service. Source:
  https://docs.aws.amazon.com/cost-management/latest/userguide/ce-resource-daily.html
- API queries are charged ($0.01 per request)
- For programmatic deep analysis, CUR / Data Exports remain the right tool - Cost
  Explorer is for visualisation and pre-built recommendations

**Useful Cost Explorer features:**
- **Rightsizing recommendations** - EC2 rightsizing based on CloudWatch utilization
- **Savings Plans recommendations** - commitment purchase recommendations based on usage
- **Cost anomaly detection** - ML-based anomaly alerts (set up before you need them)
- **Cost categories** - virtual tags for billing-layer cost allocation

### AWS Cost Anomaly Detection

Set up before an incident occurs. AWS Cost Anomaly Detection uses ML to identify
unexpected spending increases and sends alerts via SNS or email.

**Configuration recommendations:**
- Create monitors at the service level and the linked account level
- Set alert threshold at an absolute dollar amount, not just percentage
  (a 100% increase on $10 is $10; a 20% increase on $50,000 is $10,000)
- Route alerts to both the FinOps practitioner and the engineering team lead
- Review alert history monthly - tune thresholds to reduce false positives

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
| EC2 Convertible RI | Up to 66% | Medium - can change instance family, OS, tenancy | Rate only (no capacity) | 3yr only | EC2 only |
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

4. **Convertible RIs provide mid-term liquidity.** EC2 Instance Savings Plans offer
   similar flexibility at equal or better discount depth, but they are locked for
   the full term - no modifications allowed once purchased. Convertible RIs can be
   exchanged mid-term for a different configuration (instance family, OS, tenancy),
   which means you can reshape the commitment as workloads evolve without waiting
   for expiry. This mid-term exchange capability is one of three commitment
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

## Compute rightsizing

### EC2 rightsizing

Rightsizing is the highest-ROI optimisation for most AWS environments at Crawl/Walk maturity.

**Data sources for rightsizing analysis:**
- AWS Compute Optimizer - ML-based recommendations using CloudWatch metrics
- AWS Cost Explorer rightsizing recommendations (simpler, less granular)
- Third-party tools (CloudHealth, Apptio, cast.ai for containers)

**Rightsizing process:**
1. Enable Compute Optimizer in all accounts (free for EC2 recommendations)
2. Wait 14 days minimum for sufficient utilization data
3. Export recommendations and filter for "Over-provisioned" findings
4. Prioritize by potential monthly savings
5. Validate recommendations with workload owners - check peak utilization, not average
6. Apply changes in non-production first, then production with monitoring period

**Common rightsizing mistakes:**
- Acting on CPU metrics alone without checking memory (CloudWatch memory requires agent)
- Downsizing during off-peak analysis periods without accounting for peak loads
- Rightsizing stateful databases without testing failover behaviour
- Missing network-intensive workloads that appear CPU-idle but are IO-bound

### Container rightsizing (ECS / EKS)

Container rightsizing requires different tooling than EC2 rightsizing.

- AWS Compute Optimizer provides ECS on Fargate recommendations
- For EKS, use Kubernetes VPA (Vertical Pod Autoscaler) recommendations or cast.ai
- Right-size the pod requests/limits before right-sizing the underlying node group
- Node group rightsizing savings are partially offset by bin-packing efficiency changes

### GPU instance rightsizing

GPU instances (G4dn, G5, G6, P3, P4d/P4de, P5/P5e/P5en, Inf2, Trn1) are
the highest-dollar rightsizing candidates in any AWS account running ML.
GPU rightsizing is **not** the same problem as CPU rightsizing because the
basic `nvidia-smi` / CloudWatch `GPUUtilization` metric reports whether
the GPU did anything in the interval, not how much of its capacity was
used. A workload using 1 SM out of 108 on an H100 reports `GPU-Util: 100%`.
For real signals, use NVIDIA DCGM Exporter metrics (`DCGM_FI_PROF_GR_ENGINE_ACTIVE`,
`DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`, `DCGM_FI_PROF_DRAM_ACTIVE`,
`DCGM_FI_DEV_FB_USED`). See `finops-for-ai.md` section "GPU utilization is
misleading" for the metric reference.

The four highest-leverage GPU rightsizing patterns, each with a dedicated
playbook:

- **Oversized GPU instance** - workload uses < 30% of GPU compute and
  < 40% of GPU memory.
  [aws-gpu-instance-oversized](../playbooks/aws-gpu-instance-oversized.md)
- **Multi-GPU instance running single-GPU workload** - 7 of 8 GPUs idle
  on a `g5.48xlarge` or `p4d.24xlarge`.
  [aws-multi-gpu-underutilized](../playbooks/aws-multi-gpu-underutilized.md)
- **MIG candidate** - workload uses < 1/7 of an A100 or H100; partition
  via NVIDIA Multi-Instance GPU.
  [aws-mig-candidate](../playbooks/aws-mig-candidate.md)
- **GPU for CPU-bound workload** - the GPU is idle while the CPU is
  saturated; migrate to a `c7i` or `inf2` instance.
  [aws-gpu-for-cpu-bound-workload](../playbooks/aws-gpu-for-cpu-bound-workload.md)
- **Outdated GPU generation** - P3 (V100) or G4dn (T4) workloads that
  would run cheaper per inference on G5, G6, P4d, or P5.
  [aws-outdated-gpu-generation](../playbooks/aws-outdated-gpu-generation.md)

---

## SageMaker operational FinOps

SageMaker spend has two cost shapes that differ from generic EC2 and need
their own operational discipline.

### The billed-while-idle trap

SageMaker real-time endpoints and notebook instances are billed at the
underlying instance hourly rate **as long as they are provisioned**,
whether traffic flows through them or not. This differs from
consumption-based services like Lambda or Bedrock on-demand. A small
endpoint at `ml.m5.xlarge` costs ~$170/month if left running; a GPU
endpoint at `ml.g4dn.xlarge` is ~$540/month; a `p4d.24xlarge` endpoint
is ~$27,500/month. Forgotten POC endpoints, never-decommissioned A/B
variants, and notebook instances left `InService` over a weekend are the
two highest-density waste patterns in any account running SageMaker.

Detection and remediation playbooks:
- [aws-sagemaker-idle-endpoint](../playbooks/aws-sagemaker-idle-endpoint.md)
- [aws-sagemaker-notebook-always-on](../playbooks/aws-sagemaker-notebook-always-on.md)

### Inference deployment pattern selection

SageMaker offers four deployment patterns. The right choice is workload-
driven: matching the wrong pattern to the wrong workload is itself a waste
pattern (a real-time endpoint serving bursty traffic, a serverless endpoint
behind a strict latency SLA).

| Pattern | Best fit | Optimisation focus | When to avoid |
|---|---|---|---|
| **Real-time endpoint** | User-facing API, strict latency, steady traffic | Rightsizing, autoscaling, GPU vs CPU choice | Intermittent or bursty traffic; long-running batch |
| **Serverless inference** | Intermittent or low-volume traffic, no dedicated capacity needed | Memory configuration, cold-start tolerance, cost per request | Strict p99 SLA; high sustained throughput |
| **Asynchronous inference** | Bursty traffic, large payloads, tolerable response delay | Queue depth, scale-down settings, scale-to-zero | Synchronous request-response APIs |
| **Batch transform** | Offline scoring, scheduled jobs, large datasets | Spot, partitioning, instance type for throughput | Interactive inference; user-facing immediate response |

The default in most teams is real-time. The most common silent waste is a
real-time endpoint serving traffic that would be a clean fit for
serverless or asynchronous - keeping the endpoint always-on for what is
actually a few requests per hour or per day.

### Endpoint consolidation - MME and Inference Components

When several lightly-used real-time endpoints exist in the same account
and region (each on its own dedicated instance), consolidation onto a
shared endpoint is one of the largest savings opportunities in SageMaker.
Two consolidation mechanisms:

- **Multi-Model Endpoints (MME)** - one container, multiple models loaded
  dynamically from S3 on demand. Best for tens to thousands of small,
  homogeneous models that share a runtime (all sklearn, all XGBoost, all
  TensorFlow Serving). Cold-start on cache-miss adds 100 ms - 2 s of
  latency.
- **Inference Components (IC)** - newer mechanism (introduced 2023). Each
  Inference Component is a model + container deployed onto a shared
  instance pool with per-component autoscaling. Best for 5-50 models with
  heterogeneous frameworks or different scaling characteristics. IC is
  generally the right default for new builds unless MME's homogeneous-
  runtime model is a genuine fit.

Decision: same container + same framework + many small models → MME;
heterogeneous frameworks or per-model scaling needs → Inference Components.

Detection and remediation playbook:
[aws-sagemaker-mme-consolidation](../playbooks/aws-sagemaker-mme-consolidation.md)

### Notebook hygiene

SageMaker notebook instances are valuable while someone is actively
working in them and a pure cost drag when they are not. The practical
controls:

- **Lifecycle Configurations (LCC)** with the standard
  `auto-stop-idle` script (AWS publishes the reference in the
  `amazon-sagemaker-notebook-instance-lifecycle-config-samples` repo).
  Run every 5 minutes, stop the instance after N hours of kernel
  inactivity. A 2-hour idle threshold is the practical default; 4 hours
  for teams running long evaluations.
- **EventBridge scheduled stop/start** for predictable office-hours
  patterns (start 09:00 weekday, stop 19:00 weekday, never weekends).
  Cheaper and more predictable than LCC for teams that never use
  notebooks off-hours.
- **Migrate new work to SageMaker Studio**. Studio bills the Studio app
  per-second, supports native idle shutdown via the Studio admin console,
  and avoids the per-notebook EBS footprint. Existing notebook instances
  do not need in-place migration.

Detection and remediation playbook:
[aws-sagemaker-notebook-always-on](../playbooks/aws-sagemaker-notebook-always-on.md)

---

## AWS cost allocation

### Account structure for cost allocation

The cleanest cost allocation model uses AWS accounts as the primary allocation boundary.

**Recommended patterns:**
- One account per environment per workload (prod, staging, dev separate accounts)
- Shared services in a dedicated account with cross-account cost sharing methodology defined
- Sandbox accounts with budget limits and auto-termination policies

**Multi-account cost aggregation:**
Use AWS Organizations and the management account CUR for consolidated billing.
Cost Categories in Cost Explorer can create virtual tags across accounts.

### Tagging for AWS cost allocation

See `finops-tagging.md` for the full tagging strategy. AWS-specific notes:

- AWS propagates some tags to billing automatically - verify which tags appear in CUR
- Tag propagation is not instant - allow 24 hours for new tags to appear in billing
- Some services do not support tagging (AWS Support, Route 53 Hosted Zones, some
  data transfer charges) - use Cost Categories for virtual allocation of untaggable costs
- Enable "Tag policies" in AWS Organizations to enforce tag key capitalization consistency
- **IAM Principal Cost Allocation (2026):** tags applied to IAM users and roles can be
  propagated to CUR 2.0 and Cost Explorer with an `iamPrincipal/` prefix, enabling
  caller-based attribution when resource-level tags are not sufficient. Primary use case
  today is Amazon Bedrock  - see `finops-bedrock.md` for setup, CUR size implications,
  and when to use it vs. account separation

### Cost Categories

AWS Cost Categories create billing-layer allocation rules without requiring physical tags.
Use them for:
- Shared service allocation (split NAT Gateway cost by team account usage)
- Account-level allocation when resource-level tagging is incomplete
- Retroactive allocation adjustments

---

## AWS governance tools

### AWS Config

Use AWS Config for continuous compliance monitoring of tagging and configuration standards.

**Useful managed rules for FinOps:**
- `required-tags` - flags resources missing specified mandatory tags
- `ec2-instance-no-public-ip` - governance + potential cost reduction (NAT vs public IP)
- `s3-bucket-versioning-enabled` - data protection governance
- `restricted-ssh` - security governance

### Service Control Policies (SCPs)

SCPs in AWS Organizations can prevent resource creation without required tags.

**Example SCP - deny EC2 launch without Environment tag:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyEC2WithoutEnvTag",
    "Effect": "Deny",
    "Action": "ec2:RunInstances",
    "Resource": "arn:aws:ec2:*:*:instance/*",
    "Condition": {
      "Null": {
        "aws:RequestTag/Environment": "true"
      }
    }
  }]
}
```

**Important:** Test SCPs in a sandbox OU before applying to production. SCPs cannot be
overridden by account-level IAM policies - a misconfigured SCP can block legitimate
operations across all accounts in the OU.

### AWS Budgets

Configure at minimum:
- Account-level monthly cost budget with 80% and 100% alerts
- Service-level budgets for top 3–5 cost drivers
- Anomaly detection monitor linked to cost anomaly detection

**Recommended alert recipients:** Both the FinOps practitioner and the engineering team
lead for the relevant account. FinOps-only alerts create a bottleneck; engineering-only
alerts lack financial context.

---

## AWS-specific quick wins

These actions typically deliver savings within 30 days with low risk.

| Action | Typical savings | Risk | Effort |
|---|---|---|---|
| Delete unattached EBS volumes | 100% of volume cost | None | Low |
| Release unassociated Elastic IPs | $3.65/IP/month | None | Low |
| Delete unused snapshots (>90 days old) | Variable | Low (verify no restore needed) | Low |
| Schedule dev/test EC2 stop outside business hours | 60–70% of instance cost | Low | Low |
| Move S3 infrequently accessed data to Infrequent Access | 40% storage cost | Low | Low |
| Right-size over-provisioned RDS instances | 20–50% RDS cost | Medium (test first) | Medium |
| Convert gp2 EBS volumes to gp3 | 20% EBS cost (same IOPS baseline) | Low | Low |
| Review and right-size NAT Gateway usage | Variable | Medium | Medium |

---

## Database cost optimisation
<!-- src:holori-database-optimization -->

Database services often represent 20-40% of cloud spend, yet many organisations treat them as black boxes from a cost perspective. The following patterns apply across AWS RDS, Azure SQL Database, and GCP Cloud SQL.

### Common database cost drivers

**1. Overprovisioning for peak load**
- Databases sized for Black Friday traffic that run at 10% utilisation for 11 months
- Solution: Implement auto-scaling (where supported) or scheduled scaling for predictable patterns
- AWS: Aurora Serverless v2, RDS Proxy for connection pooling
- Azure: SQL Database serverless compute tier, elastic pools
- GCP: Cloud SQL automatic storage increases, read replica auto-scaling

**2. High availability in non-production**
- Multi-AZ/zone deployments double infrastructure costs
- Dev/test rarely needs synchronous replication
- Solution: Single-zone deployments for non-prod, with automated backups for recovery

**3. Storage inefficiencies**
- Provisioned IOPS when standard storage suffices (AWS: gp3 vs io1/io2)
- Retained backups and snapshots beyond business requirements
- Uncompressed or poorly indexed tables driving storage growth
- Solution: Regular storage audits, lifecycle policies, compression strategies

**4. Backup retention overkill**
- 35-day retention when 7 days meets actual RTO/RPO
- Manual snapshots never deleted after migrations
- Solution: Align retention to documented recovery requirements, automate cleanup

### Database-specific optimisation strategies

**For transactional workloads (OLTP):**
- Right-size based on connection count and active sessions, not just CPU/memory
- Implement connection pooling to reduce instance size requirements
- Consider managed connection proxies (RDS Proxy, Azure SQL Database built-in pooling)

**For analytical workloads (OLAP):**
- Evaluate columnar storage options (Redshift, BigQuery, Synapse)
- Implement result caching to reduce repeated query costs
- Schedule large queries during off-peak for better pricing (BigQuery flex slots)

**For mixed workloads:**
- Separate OLTP and OLAP with read replicas or data warehouse offload
- Use change data capture (CDC) for real-time sync instead of expensive ETL

### Commitment strategies by database type

**Open-source engines (MySQL, PostgreSQL, MariaDB):**
- Maximum flexibility for commitments due to version compatibility
- Size flexibility within instance families on AWS RDS
- Consider Aurora for better price-performance at scale

**Commercial engines (Oracle, SQL Server):**
- License costs often exceed infrastructure costs
- BYOL can save 40-80% if you have existing licenses
- Evaluate migration to open-source for non-critical workloads

**NoSQL and managed services:**
- DynamoDB: On-Demand vs Provisioned can be 5-10x cost difference
- Cosmos DB: Request unit (RU) optimisation more impactful than storage
- Firestore/Datastore: Document size and index strategy drive costs

### Quick wins checklist

- [ ] Identify databases with <20% average CPU utilisation for downsizing
- [ ] Review Multi-AZ/HA configurations in non-production environments  
- [ ] Audit backup retention policies against actual recovery requirements
- [ ] Check for orphaned snapshots from deleted databases
- [ ] Evaluate storage tier options (standard vs provisioned IOPS/throughput)
- [ ] Implement connection pooling for high-connection workloads
- [ ] Schedule non-production databases to stop outside business hours
- [ ] Review commercial database licenses for BYOL opportunities

---

## CloudFront flat-rate pricing plans

AWS introduced per-distribution flat-rate plans for CloudFront in late 2025. They
bundle CDN, WAF, Route 53, CloudWatch Logs ingest, ACM, CloudFront Functions and
S3 storage credits into a single monthly price, removing the bill variance that
made CloudFront costs hard to forecast.

### Tier summary

| Plan | Monthly cost | Data transfer out | Requests | S3 credit | WAF rules | Cache behaviours |
|---|---|---|---|---|---|---|
| Free | $0 | 100 GB | 1M | 5 GB | 5 | 5 |
| Pro | $15 | 50 TB | 10M | 50 GB | 25 | 10 |
| Business | $200 | 50 TB | 125M | 1 TB | 50 | 50 |
| Premium | $1,000 | 50 TB | 500M | 5 TB | 75 | 100 |

Pay-as-you-go pricing for 50 TB of data transfer out from North America runs
roughly $4,250 at $0.085/GB. The Pro plan delivers the same 50 TB for $15. For
bandwidth-heavy workloads the effective discount is at the 99% mark - this is
not the usual "simplified pricing" code for "we repriced the meter". It is a
genuine offer aimed at mid-market customers who would otherwise move to
Cloudflare.

### Request-bound vs bandwidth-bound

The break-even average response size (bandwidth cap / request cap) is the number
that decides which tier fits:

| Plan | Break-even avg response size |
|---|---|
| Free | 100 KB |
| Pro | 5 MB |
| Business | 400 KB |
| Premium | 100 KB |

If your average response is smaller than the break-even, you hit the request
ceiling first - you are request-bound. Pro is designed for software binaries,
video chunks, large assets. For API responses or web pages averaging under
400 KB you will exhaust the 10M request budget long before the 50 TB bandwidth,
and Business becomes the real entry point.

**Model the p95 month, not the average.** Flat-rate tiers care about worst-case
volume - a traffic spike during a launch can push you past the cap exactly when
performance matters.

### What is included

- CloudFront CDN distribution
- AWS WAF with bot management (**mandatory** - WebACL must be associated, you
  cannot opt out)
- DDoS protection (blocked attack traffic does not count against allowances)
- Route 53 DNS, with caveats (see below)
- CloudWatch Logs ingestion (storage and queries still billed separately)
- ACM TLS certificates
- CloudFront Functions (serverless edge compute)
- S3 storage credit at the bundled tier

The WAF inclusion is load-bearing for the value math. 25 WAF rules at $1/rule/month
is $25/month of standalone WAF value, which by itself exceeds the $15 Pro price.
If you were going to adopt WAF anyway, Pro pays for itself on that line alone.

### Route 53 gotchas

- Hosted zone must live in the same AWS account as the CloudFront distribution.
  Cross-account Route 53 setups disqualify you from flat-rate entirely.
- ALIAS records pointing at CloudFront or other supported AWS services do not
  count against the DNS query allowance. CNAME records do count.
- If you exceed the DNS query limit AWS may automatically transition the hosted
  zone back to pay-as-you-go without prompting.
- DNSSEC KMS charges and health checks are billed separately.

### What is not included (the real filter)

Lambda@Edge is not supported. There is no migration path, no compatibility
shim, and CloudFront Functions is not a replacement for most Lambda@Edge
workloads (2 MB memory, 10 KB code, JavaScript only, no network access, no AWS
SDK). If your architecture relies on Lambda@Edge - even accidentally after
years of incremental drift - flat-rate is off the table until you can remove or
replace that dependency.

Other exclusions that will disqualify real distributions:

- Real-time logs (Kinesis streaming), Parquet log format
- Continuous deployment, staging distributions, multi-tenant distributions
- Anycast IP list configuration, dedicated IP/SSL, field-level encryption
- Shield Advanced combined subscriptions, Firewall Manager
- WAF targeted bots, CAPTCHA (challenge only), Partner Managed Rules, Account
  Takeover Protection, WAF Rule Groups (must be individual rules)
- Shared CloudFront Functions or WAF WebACLs across distributions - each plan
  requires dedicated, non-shared resources
- Legacy cache settings and origin access identity (OAI) - must migrate to
  cache policies and origin access control (OAC)

### The tier-locked features that drive up-tier selection

| Feature | Minimum tier |
|---|---|
| Geographic restrictions, rate limiting | Free |
| Common bot detection, Origin Shield, custom response headers, private VPC origins | Business |
| Automatic origin failover (origin groups) | Premium |
| Mutual TLS (mTLS) | Premium |

Origin failover is the biggest one. If high availability to multiple origins
matters to you (the December 2021 us-east-1 event is the usual reference), you
are looking at Premium at $1,000/month or staying on pay-as-you-go.

### Multi-tenant SaaS constraint

One apex domain per plan. If every customer runs on a subdomain of your platform
(`customer1.yourplatform.com`) you are fine, all subdomains share the same plan.
If customers bring their own apex domains (`customer1.com`, `customer2.com`),
you need one plan per customer, capped at 100 plans per AWS account. For custom-
domain SaaS at any meaningful scale, flat-rate does not fit - stay on
pay-as-you-go.

### Overages mean throttling, not a bill

AWS does not charge overage fees. When you exceed allowances they **degrade
performance** - fewer or more distant edge locations serve your traffic. There
is no operational signal distinguishing "hit the cap" from "CloudFront is just
slow". Notifications at 50%, 80% and 100% are explicitly "may be delayed". The
failure mode is a P1 investigation that ends with "we forgot about a pricing
tier limit", which is much harder to explain than an invoice.

**Build your own alerting.** CloudWatch metrics for `Requests` and
`BytesDownloaded` with alarms at 50%, 80% and 90% of the plan limits. Do not
rely on AWS's email cadence.

### Ecosystem lock-in is part of the price

AWS can offer 50 TB for $15 because origin traffic from S3 or EC2 to CloudFront
is free. Moving that same workload to Cloudflare triggers standard AWS data
transfer out charges at roughly $0.09/GB - 50 TB/month becomes $4,500 in egress
alone, every month. The real price of CloudFront Pro is $15 plus the AWS
dependency you have already accepted.

For greenfield workloads with no AWS origins, Cloudflare's unlimited-bandwidth
Pro plan at $25/month is the correct comparison. For existing AWS shops the
comparison is not close.

### Operational gotchas

- **Historical usage affects eligibility.** AWS checks recent distribution
  traffic when you subscribe. You cannot subscribe to Pro when your usage
  clearly puts you in Business territory.
- **Disabled distributions still incur plan charges.** Disable without
  cancelling the plan and you keep paying the monthly fee for nothing.
- **Plans must be cancelled before deletion.** You cannot delete a distribution
  while a plan is attached.
- **Upgrades are immediate and prorated. Downgrades take effect next billing
  cycle.**
- **You can mix pricing models.** Keep experimental or low-traffic distributions
  on pay-as-you-go (effectively free at low volume) and move only the
  high-volume production distributions to flat-rate.
- **Unsupported features block subscription.** The console refuses to attach a
  plan while the distribution still has Lambda@Edge, real-time logs or any
  other unsupported feature active.
- **Maximum 100 plans per AWS account, 3 Free plans maximum. AWS Free Tier
  accounts are not eligible.**

### Decision flow

1. Audit existing distributions. Most accounts have zombie distributions -
   identify which ones actually serve traffic.
2. Check blockers per distribution: Lambda@Edge, shared Functions or WebACLs,
   real-time logs, Shield Advanced, cross-account Route 53. Any of these keep
   you on pay-as-you-go for that distribution.
3. Calculate average response size. Under 400 KB you are request-bound - Pro
   will not fit a high-traffic distribution.
4. Model p95 volume, not average. Pick the tier that fits your worst month.
5. Count cache behaviours. Over 10 means Pro is off the table regardless.
6. Build CloudWatch alarms at 50/80/90% of plan limits before subscribing.
7. Migrate one non-critical distribution first, watch usage counters across a
   full billing cycle, then expand.

The downside risk is low - no annual commitment, downgrades and cancellations
are supported. The upside is the first AWS pricing mechanism in years where
predictability and cost both move in the right direction for mid-market
workloads.

---

## S3 Files - filesystem access over S3

S3 Files (launched 2026) lets you mount an S3 bucket as an NFS 4.1/4.2
filesystem on EC2, Lambda, EKS or ECS. The filesystem maintains a view of your
objects and translates POSIX operations into S3 requests. Writes are synced back
to the underlying bucket. S3 itself is still not a filesystem - S3 Files is a
real filesystem layer in front of it, built on EFS infrastructure, with the
original S3 bucket as durable backing store.

### What it replaces

- FUSE-based workarounds: s3fs-fuse, goofys, Mountpoint for Amazon S3 for
  workloads that need genuine POSIX semantics
- Cases where teams ran EFS or FSx purely to give legacy applications something
  to mount, while the data of record actually lived in S3
- Ad-hoc proxy layers between S3 and ML training pipelines or agentic workloads
  that need shared file storage

### Pricing mechanics

Two cost dimensions on top of the underlying S3 bucket:

| Dimension | Rate |
|---|---|
| Filesystem storage (hot tier) | $0.30/GB-month |
| Reads | $0.03/GB |
| Writes | $0.06/GB |

Rates are identical to EFS Performance-optimised Standard. The underlying
infrastructure is the same.

**The design that makes it cheap:** you mount a petabyte bucket and pay S3 Files
rates only on the small slice you actually touch. Everything else stays at
standard S3 pricing ($0.023/GB-month Standard, or less on Intelligent-Tiering or
Infrequent Access). The hot tier is an opt-in cache, not a whole-bucket storage
class.

### The 128 KB threshold

Files below the threshold (default 128 KB, configurable) get pulled into the
hot tier on first access - small-file latency is where filesystems actually
beat object stores, so S3 Files caches them.

**Reads of 128 KB or larger stream directly from S3 even when the file is
already on the hot tier.** No S3 Files access charge. This is the key mechanic
that makes the economics work for mixed workloads - your Parquet files and
video chunks go through the free path.

### Metering minimums (the gotcha)

Every data access operation has minimums that round up:

| Operation | Metered as |
|---|---|
| Read of any size | 32 KB minimum |
| Write of any size | 32 KB minimum |
| Metadata op (list, stat, create, delete) | 4 KB read |
| Commit (fsync or close-after-write) | 4 KB write |
| Everything above minimums | Rounds up to next 1 KB |

If your workload is millions of tiny metadata-heavy operations - ML training
checkpointing and some agentic workflows fit this profile exactly - the
minimums dominate the bill. `ls` on a directory with 10,000 files is 10,000
metadata reads at 4 KB each; if that triggers prefetch it is another 10,000
writes at 32 KB minimum each. Model these patterns before you mount anything
production.

**First-read cost for small files:** $0.06/GB (the import write), not $0.03/GB.
The read is included in the import operation. Subsequent reads of the same
cached file are $0.03/GB. AWS's pricing examples were misleading on this
initially - cost the workload on your real access patterns.

**Rename cost:** a file rename is an S3 PUT plus a filesystem read (32 KB
minimum). Renaming a directory meters every object with that prefix - moving
50,000 files is 50,000 individual metered operations.

### Expiration and eviction

Untouched data on the hot tier is evicted after a configurable window (1 to
365 days, default 30). This bounds your hot-tier storage cost automatically -
you are charged for actively-used files, not for every file that has ever been
touched.

### Base storage tier constraints

S3 Files works with Standard, Intelligent-Tiering and Infrequent Access as the
underlying bucket tier. It does **not** work with Glacier Flexible Retrieval,
Glacier Deep Archive or the Intelligent-Tiering archive tiers - those require a
standard S3 restore first.

This means you can put the authoritative data on Intelligent-Tiering at roughly
$0.0125/GB-month in the infrequent tier and still mount it as a filesystem,
paying hot-tier rates only on the active working set. S3 Intelligent-Tiering
transitions between classes are free, which matters because EFS equivalents
charge per-GB tiering fees.

### S3 Files vs EFS comparison

For an illustrative 10 TB workload with 90% cold data, 500 GB hot working set,
500 GB/month reads (90% large files / 10% small files), 100 GB/month writes:

| | EFS Legacy + IA | EFS Performance-optimised + Archive | S3 Intelligent-Tiering + S3 Files |
|---|---|---|---|
| Cold storage (9 TB) | ~$225 ($0.025/GB IA) | ~$72 ($0.008/GB Archive) | ~$115 ($0.0125/GB IT infrequent) |
| Hot working set (500 GB) | $150 ($0.30/GB Std) | $150 ($0.30/GB Std) | $12 (S3 IT) + Files surcharge on sub-128 KB portion only |
| Read 500 GB large | Included in throughput | ~$15 ($0.03/GB) | $0 (direct from S3) |
| Read 50 GB small | ~$0.50 IA reads | ~$4 ($0.03 + tier surcharge) | ~$3 ($0.06/GB first read) |
| Write 100 GB | Included | $6 ($0.06/GB) | $6 ($0.06/GB via Files) |
| Tiering transitions | $0.01/GB in and out | $0.01-$0.03/GB per transition | Free (S3 IT) |

EFS wins when the workload is metadata-heavy and small-file-dominated (no 32 KB
minimums on EFS). S3 Files wins on cold storage, large-file reads (free),
tiering flexibility, and any workload where the authoritative data already
lives in S3.

### When S3 Files fits

- ML training pipelines that chew through millions of small checkpoint files
  scattered across S3 - the existing duct-tape of Mountpoint and prayer
- Agentic AI workloads that need shared storage accessible by a mount command
  without the team becoming S3 API experts
- Legacy applications assuming POSIX semantics where the data of record needs
  to stay in S3 for durability, audit or downstream processing
- Any case where data gravity sits in S3 but one access path needs filesystem
  semantics

### When to stay on S3 API or EFS

- Current workloads happy with native S3 APIs - S3 Files does not replace them,
  it adds an access pattern
- Metadata-heavy workloads (directory listings, frequent stats, mass renames)
  where 4 KB per metadata op dominates the bill
- Ultra-latency-sensitive small-file reads where the $0.06/GB first-read import
  is a recurring hit
- Use cases that need filesystem features EFS supports but S3 Files does not

### Decision checklist

- [ ] Is the data already in S3 and does it need to stay there?
- [ ] What is the read/write mix between files above and below 128 KB?
- [ ] How metadata-heavy is the workload (listings, stats, renames)?
- [ ] Can the base tier run on Intelligent-Tiering or IA for the cold bulk?
- [ ] Are the 32 KB/4 KB minimums going to dominate or not?

The rate card matches EFS Performance-optimised. The savings come from the
design - free large-file reads straight from S3, pay-only-for-hot-slice
storage, and free Intelligent-Tiering transitions underneath. For workloads
with meaningful cold storage and large-file reads, this is a structurally
cheaper filesystem than EFS.

## AWS Optimization Patterns

> 128 cloud inefficiency patterns covering compute, storage, databases, networking,
> and other AWS services. Use to diagnose waste, validate architecture, or build
> optimization roadmaps. Source: PointFive Cloud Efficiency Hub.

---

### Compute Optimization Patterns (42)

**Idle Emr Cluster Without Auto Termination Policy**
Service: AWS EMR | Type: Inactive Resource

Amazon EMR clusters often run on large, multi-node EC2 fleets, making them costly to leave running unnecessarily. If a cluster becomes idle -no longer processing jobs -but is not terminated, it continues accruing EC2 and EMR service charges.

- Enable an auto-termination policy on EMR clusters that are intended to be short-lived or batch-oriented
- Review and shut down idle clusters that are no longer actively running jobs
- Educate data engineering teams on the cost implications of leaving clusters running

**Inactive Aws Workspace**
Service: AWS WorkSpaces | Type: Inactive Resource

If an AWS WorkSpace has been provisioned but not accessed in a meaningful timeframe, it may represent waste -particularly if it is set to monthly billing. Many organizations leave WorkSpaces active for users who no longer need them or have shifted roles, leading to persistent charges without corresponding business value.

- Decommission WorkSpaces that are no longer needed
- Switch billing mode from monthly to auto-stop for WorkSpaces with intermittent usage
- Automate reviews of WorkSpaces based on last login data to flag stale resources for cleanup or conversion

**Suboptimal Region For Ec2 Instance**
Service: AWS EC2 | Type: Inefficient Architecture

Workloads are sometimes deployed in specific AWS regions based on legacy decisions, developer convenience, or perceived performance requirements. However, regional EC2 pricing can vary significantly, and placing instances in a suboptimal region can lead to higher compute costs, increased data transfer charges, or both.

- Identify EC2 instances that generate significant cross-region or cross-AZ data transfer
- Review the current region’s EC2 pricing compared to other AWS regions supporting the same instance type
- Evaluate whether the instance communicates heavily with services or users located in another region

**Suboptimal Region For Internet Only Ec2 Instance**
Service: AWS EC2 | Type: Inefficient Architecture

When an EC2 instance is dedicated primarily to internet-facing traffic, regional differences in data transfer pricing can drive a substantial portion of total costs. Hosting such workloads in a region with higher egress rates leads to elevated expenses without improving performance.

- Identify EC2 instances whose primary traffic flows are outbound to the public internet rather than within AWS or private networks
- Review the region associated with each instance and compare public Data Transfer Out pricing against lower-cost regions
- Assess latency requirements, regulatory considerations, and service availability constraints that may impact regional choices

**Suboptimal Use Of On Demand Instances In A Non Production Eks Cluster**
Service: AWS EKS | Type: Inefficient Architecture

Running non-production clusters solely on On-Demand Instances results in unnecessarily high compute costs. Development, testing, and QA environments typically tolerate interruptions and do not require the continuous availability guaranteed by On-Demand capacity.

- Identify non-production EKS clusters based on environment tagging, naming conventions, or cluster metadata
- Review node group configurations to determine whether all nodes use On-Demand Instances
- Assess workload criticality and tolerance for Spot interruptions based on application requirements

**Excessive Lambda Duration From Synchronous Waiting**
Service: AWS Lambda | Type: Inefficient Configuration

Some Lambda functions perform synchronous calls to other services, APIs, or internal microservices and wait for the response before proceeding. During this time, the Lambda is idle from a compute perspective but still fully billed.

- Redesign functions to offload synchronous calls using asynchronous patterns (e.g., queues, event buses, Step Functions)
- Break apart long-running workflows into smaller chained or event-driven Lambdas
- Optimize memory allocation to minimize idle cost when waiting cannot be avoided

**Idle Ecs Container Instances Due To Asg Minimum Capacity**
Service: AWS ECS | Type: Inefficient Configuration

When ECS clusters are configured with an Auto Scaling Group that maintains a minimum number of EC2 instances (e.g., min = 1 or higher), the instances remain active even when there are no tasks scheduled. This leads to idle compute capacity and unnecessary EC2 charges. Instead, ECS Capacity Providers support target tracking scaling policies that can scale the ASG to zero when idle and automatically increase capacity when new tasks or services are scheduled.

- Configure an ECS Capacity Provider for the cluster and attach a target tracking scaling policy
- Set the ASG minimum capacity to 0 to allow scale-down during idle periods
- Ensure ECS services are configured with appropriate scaling triggers (e.g., CPU or memory utilization)

**Missing Scheduled Shutdown For Non Production Ec2 Instances**
Service: AWS EC2 | Type: Inefficient Configuration

Non-production EC2 instances are often provisioned for daytime-only usage but remain running 24/7 out of convenience or oversight. This results in unnecessary compute charges, even if the workload is inactive for 16+ hours per day.

- Implement scheduled shutdowns using AWS Instance Scheduler or EventBridge rules
- Ensure stateful data is retained via attached EBS volumes or AMIs
- Set start/stop windows aligned to working hours (e.g., 8 a.m.–6 p.m. weekdays)

**Orphaned And Overprovisioned Resources In Eks Clusters**
Service: AWS EKS | Type: Inefficient Configuration

In EKS environments, cluster sprawl can occur when workloads are removed but underlying resources remain. Common issues include persistent volumes no longer mounted by pods, services still backed by ELBs despite being unused, and overprovisioned nodes for workloads that no longer exist.

- Remove unused PVCs to deprovision backing EBS volumes
- Delete idle Services to release associated ELBs and IP addresses
- Clean up inactive namespaces and workloads

**Outdated Eks Cluster Incurring Extended Support Charges**
Service: AWS EKS | Type: Inefficient Configuration

When an EKS cluster remains on a Kubernetes version that has reached the end of standard support, AWS begins charging an additional Extended Support fee. These charges often arise from delays in upgrade cycles, uncertainty about workload compatibility, or overlooked legacy clusters.

- Identify clusters running Kubernetes versions that have reached end of standard support
- Confirm whether the cluster is incurring Extended Support charges
- Review upgrade history and backlog to understand why the version was not updated

**Suboptimal Appstream Fleet Auto Scaling Policies**
Service: AWS AppStream 2.0 | Type: Inefficient Configuration

When fleet auto scaling policies maintain more active instances than are required to support current usage -particularly during off-peak hours -organizations incur unnecessary compute costs. Fleets often remain oversized due to conservative default configurations or lack of schedule-based scaling.

- Adjust minimum instance counts in auto scaling policies to reflect observed demand
- Implement schedule-based scaling to reduce instance counts during predictable low-usage periods and increase during peak hours
- Regularly review and update scaling policies based on current usage data to ensure ongoing efficiency

**Suboptimal Memory To Cpu Ratio In Eks Cluster Node**
Service: AWS EKS | Type: Inefficient Configuration

When the EC2 instance types used for EKS node groups have a memory-to-CPU ratio that doesn’t match the workload profile, the result is poor bin-packing efficiency. For example, if memory-intensive containers are scheduled on compute-optimized nodes, memory may run out first while CPU remains unused.

- Review container-level memory and CPU requests and limits across the cluster
- Assess node-level resource utilization to detect fragmentation (e.g., memory maxed out while CPU remains idle)
- Compare the vCPU-to-memory ratio of node types to the average resource profile of scheduled workloads

**Inefficient Workflow Design In Aws Step Functions**
Service: AWS Step Functions | Type: Misconfiguration

Improper design choices in AWS Step Functions can lead to unnecessary charges. For example, using Standard Workflows for short-lived, high-frequency executions leads to excessive per-transition charges, while complex workflows with many state transitions multiply per-transition cost across the lifetime of the application.

- Choose Express workflows for short-lived, high-volume executions
- Use Standard workflows for long-running, infrequent executions
- Combine simple logic steps into a single Lambda or use intrinsic functions

**Recursive Invocation Loop Between Lambda And Sqs**
Service: AWS Lambda | Type: Misconfigured Architecture

When a Lambda function processes messages from an SQS queue but fails to handle certain messages properly, the same messages may be returned to the queue and retried repeatedly. In some cases, especially if the Lambda is also writing messages back to the same or a chained queue, this can create a recursive invocation loop.

- Introduce a dead-letter queue (DLQ) to route failed messages after a maximum number of retries
- Set a maximumReceiveCount on the SQS redrive policy to avoid indefinite reprocessing
- Refactor the Lambda logic to prevent re-enqueuing the same message unintentionally

**Inefficient Snapstart Configuration In Lambda**
Service: AWS Lambda | Type: Misconfigured Performance Optimization

SnapStart reduces cold-start latency, but when configured inefficiently, it can increase costs. High-traffic workloads can trigger frequent snapshot restorations, multiplying costs.

- Implement concurrency controls to reduce excess restorations during high traffic bursts
- Optimize function initialization to minimize Init phase duration by loading only essential dependencies
- Use pre-snapshot hooks (for Java) to prepare code execution and reduce overhead before the snapshot is taken

**Unnecessary Multi Az Deployment For Non Production Ec2 Instances**
Service: AWS EC2 | Type: Misconfigured Redundancy

Multi-AZ deployment is often essential for production workloads, but its use in non-production environments (e.g., development, test, QA) offers minimal value. These environments typically do not require high availability, yet still incur the full cost of redundant compute, storage, and data transfer.

- Reconfigure EC2 workloads in non-production environments to use a single Availability Zone
- Avoid distributing instances or traffic across multiple AZs unless justified by a specific requirement
- Establish environment-based architectural guidelines to limit Multi-AZ usage

**Unconverted Convertible Ec2 Reserved Instances**
Service: AWS EC2 | Type: Misconfigured Reservation

Convertible Reserved Instances provide valuable pricing flexibility  - but that flexibility is often underused. When EC2 workloads shift across instance families or OS types, the original RI may no longer apply to active usage.

- Use the AWS Management Console or CLI to convert unused Convertible RIs to match current EC2 instance usage
- Ensure the new reservation configuration has equal or greater value, as required by AWS
- Monitor usage regularly to identify when new conversions may be needed

**Unmanaged Growth Of Athena Query Output Buckets**
Service: AWS Athena | Type: Missing Lifecycle Policy

Athena generates a new S3 object for every query result, regardless of whether the output is needed long term. Over time, this leads to uncontrolled growth of the output bucket, especially in environments with repetitive queries such as cost and usage reporting.

- Implement S3 Lifecycle Policies on Athena output buckets to automatically expire objects after a set period (e.g., 30, 60, 90 days)
- Use prefixes or tags to differentiate between temporary query outputs and long-term reports, applying tailored retention rules
- Regularly review and adjust retention policies to balance cost efficiency with business and compliance needs

**Orphaned Kubernetes Resources E7E68**
Service: AWS EKS | Type: Orphaned Resource

In Kubernetes environments, resources such as ConfigMaps, Secrets, Services, and Persistent Volume Claims (PVCs) are often created dynamically by applications or deployment pipelines. When applications are removed or reconfigured, these resources may be left behind if not explicitly cleaned up.

- Delete orphaned Persistent Volume Claims to release underlying storage (e.g., EBS volumes)
- Remove unused Services, especially those of type LoadBalancer, to eliminate unnecessary networking charges
- Clean up ConfigMaps and Secrets that are no longer referenced by any active workloadImplement tagging/labeling standards for all workloads to simplify orphan detection.

**Stale Dedicated Hosts For Stopped Ec2 Mac Instances**
Service: AWS EC2 | Type: Orphaned Resource

When an EC2 Mac instance is stopped or terminated, its associated dedicated host remains allocated by default. Because Mac instances are the only EC2 type billed at the host level, charges continue to accrue as long as the host is retained.

- Release Mac dedicated hosts after stopping or terminating Mac EC2 instances if no longer needed
- Update automation workflows to include host deallocation logic when applicable
- Enable lifecycle tracking of dedicated hosts to avoid forgotten allocations

**Underutilized Ec2 Commitment Due To Workload Drift**
Service: AWS EC2 | Type: Overcommitted Reservation

When EC2 usage declines, shifts to different instance families, or moves to other services (e.g., containers or serverless), organizations may find that previously purchased Standard Reserved Instances or Savings Plans no longer match current workload patterns. This misalignment results in underutilized commitments -where costs are still incurred, but no usage is benefiting from the associated discounts.

- Review existing workloads to identify candidates that could migrate to the underutilized instance families
- For new or scaling workloads, prioritize launching on instance types that align with unused commitments
- Where possible, upgrade existing workloads to fit larger reserved types  - while tracking the change to avoid overcommitment in future renewals

**Overprovisioned Memory Allocation For Lambda Functions**
Service: AWS Lambda | Type: Overprovisioned Resource

Each Lambda function must be configured with a memory setting, which indirectly controls the amount of CPU and networking performance allocated. In many environments, memory settings are defined arbitrarily or left unchanged as functions evolve.

- Use tools like AWS Lambda Power Tuning to benchmark and optimize memory and vCPU settings
- Incorporate right-sizing into CI/CD workflows to evaluate configuration during deployment
- Apply consistent tagging or governance to track functions requiring periodic review

**Underutilized Ec2 Instance**
Service: AWS EC2 | Type: Overprovisioned Resource

EC2 instances are often overprovisioned based on rough estimates, legacy patterns, or performance buffer assumptions. If an instance consistently uses only a small fraction of its provisioned CPU or memory, it likely represents an opportunity for rightsizing.

- Review average CPU and memory utilization of running EC2 instances.
- Determine whether actual usage justifies the selected instance type or size
- Confirm whether performance buffers, licensing rules, or other constraints require overprovisioning

**Underuse Of Fargate Spot For Interruptible Workloads**
Service: AWS Fargate | Type: Pricing Model Misalignment

Many teams run workloads on standard Fargate pricing even when the workload is fault-tolerant and could tolerate interruptions. Fargate Spot provides the same performance characteristics at up to 70% lower cost, making it ideal for stateless jobs, batch processing, CI/CD runners, or retry-friendly microservices.

- Update ECS/EKS task definitions or profiles to enable Fargate Spot
- For mixed environments, use capacity providers or placement strategies to route eligible tasks to Spot
- Monitor interruption rates and implement retry logic where necessary

**Recursive Lambda Function Invocation**
Service: AWS Lambda | Type: Recursive Invocation Misconfiguration

Recursive invocation occurs when a Lambda function triggers itself directly or indirectly, often through an event source like SQS, SNS, or another Lambda. This loop can be unintentional  - for example, when the function writes output to a queue it also consumes.

- Refactor logic to prevent self-invocation or recursive event loops
- Avoid writing to the same queue or stream that triggers the function
- Implement Dead Letter Queues to prevent retry loops

**Excessive Lambda Retries Retry Storms**
Service: AWS Lambda | Type: Retry Misconfiguration

Retry storms occur when a function fails and is automatically retried repeatedly due to default retry behavior for asynchronous events (e.g., SQS, EventBridge). If the error is persistent and unhandled, retries can accumulate rapidly  - often invisibly  - creating a large volume of billable executions with no successful outcome.

- Configure DLQs to isolate and inspect failed invocations
- Implement exponential backoff or circuit breaker patterns in retry logic
- Set appropriate retry limits on event source mappings

**Suboptimal Architecture Selection In Aws Fargate**
Service: AWS Fargate | Type: Suboptimal Architecture Selection

AWS Fargate supports both x86 and Graviton2 (ARM64) CPU architectures, but by default, many workloads continue to run on x86. Graviton2 delivers significantly better price-performance, especially for stateless, scale-out container workloads.

- Update Fargate task definitions to use `"runtimePlatform": { "cpuArchitecture": "ARM64" }` where supported
- Rebuild container images for multi-architecture compatibility if needed
- Benchmark ARM-based performance to validate expected savings

**Suboptimal Architecture Configuration For Lambda Functions**
Service: AWS Lambda | Type: Suboptimal Configuration

While many AWS customers have migrated EC2 workloads to Graviton to reduce costs, Lambda functions often remain on the default x86 architecture. AWS Graviton2 (ARM) offers lower pricing and equal or better performance for most supported runtimes  - yet adoption remains uneven due to legacy defaults or lack of awareness.

- Update Lambda function configurations to use ARM/Graviton2 where compatible
- Benchmark function performance and duration to validate equal or improved performance
- For stable, high-throughput functions, consider pairing architecture changes with Compute Savings Plans

**Suboptimal Architecture Selection In Aws Lambda**
Service: AWS Lambda | Type: Suboptimal Configuration

Lambda functions default to the x86\_64 architecture, which is more expensive than Arm64. For many workloads, especially those written in interpreted languages (e.g., Python, Node.js) or compiled to architecture-neutral bytecode (e.g., Java), there is no dependency on x86-specific binaries.

- Benchmark representative functions on both architectures to validate performance and compatibility
- For functions using architecture-neutral runtimes or dependencies, migrate to Arm64 via configuration update
- Ensure CI/CD pipelines and IaC templates default to Arm64 for new functions

**Inefficient File Format And Layout For Athena Queries**
Service: AWS Athena | Type: Suboptimal Data Layout or Format

Storing raw JSON or CSV files in S3 -especially when written frequently in small batches -leads to excessive scan costs in Athena. These formats are row-based and verbose, requiring Athena to scan and parse the full content even when only a few fields are queried.

- Convert raw data to columnar formats such as Parquet or ORC to reduce scan size
- Partition data based on common query dimensions (e.g., date, tenant ID)
- Consolidate small files into larger batches to improve scan efficiency

**Inefficient Processor Selection In Ec2 Instances**
Service: AWS EC2 | Type: Suboptimal Instance Family Selection

Many organizations default to Intel-based EC2 instances due to familiarity or assumptions about workload compatibility. However, AWS offers AMD and Graviton-based alternatives that often deliver significantly better price-performance for general-purpose and compute-optimized workloads.

- Check for architecture-specific performance issues or compatibility blockers before switching
- Benchmark representative workloads on Intel, AMD, and Graviton instance types
- Migrate to the instance family that offers the best price-performance for the workload

**Overreliance On Lambda At Sustained Scale**
Service: AWS Lambda | Type: Suboptimal Pricing Model

Lambda is designed for simplicity and elasticity, but its pricing model becomes expensive at scale. When a function runs frequently (e.g., millions of invocations per day) or for extended durations, the cumulative cost may exceed that of continuously running infrastructure.

- Establish thresholds for Lambda usage that trigger cost-efficiency reviews
- Evaluate total Lambda cost versus equivalent EC2/ECS/EKS workloads
- Consider replatforming long-running or consistently triggered workloads to containerized or instance-based compute

**Suboptimal Use Of Compute Savings Plans For Specialized Instances**
Service: AWS EC2 | Type: Suboptimal Pricing Model

Accelerated EC2 instance types such as `p5.48xlarge` and `p5en.48xlarge (often used for ML/AI workloads)` are eligible for Compute Savings Plans, but the discount rates offered are modest compared to more common instance families. When organizations rely solely on CSPs, these lower priority instances are typically the last to benefit from the plan, especially if other instance types consume most of the discounted hours.

- Consider using dedicated EC2 Instance Savings Plans instead of CSPs for predictable, high-utilization p5 workloads
- Model CSP allocation on actual discount percentages in order to determine whether p-type instances are likely to be left uncovered
- Compare total cost of ownership between CSPs and dedicated instance savings plans for your specific usage patterns

**Suboptimal Use Of On Demand Instances In Fault Tolerant Ec2 Workloads**
Service: AWS EC2 | Type: Suboptimal Pricing Model

Many EC2 workloads -such as development environments, test jobs, stateless services, and data processing pipelines -can tolerate interruptions and do not require the reliability of On-Demand pricing. Using On-Demand instances in these scenarios drives up cost without adding value.

- Reconfigure eligible workloads to use Spot Instances via launch templates or Auto Scaling policies
- Use mixed-instance and capacity-optimized allocation strategies for better availability
- Apply On-Demand only where availability, SLA, or licensing requirements demand it

**Underutilized Kubernetes Workload**
Service: AWS EKS | Type: Underutilization

When Kubernetes workloads request more CPU and memory than they actually consume, nodes must reserve capacity that remains unused. This leads to lower node density, forcing the cluster to maintain more instances than necessary.

- Identify workloads where average CPU and memory usage are consistently much lower than requested values
- Analyze container-level metrics to assess request-to-usage ratios over time
- Leverage Vertical Pod Autoscaler recommendations, if available, to identify right-sizing opportunities

**Underutilized Or Overprovisioned Appstream Instances**
Service: AWS AppStream 2.0 | Type: Underutilization

AppStream fleets often default to instance types designed for worst-case or peak usage scenarios, even when average workloads are significantly lighter. This leads to consistently low utilization of CPU, memory, or GPU resources and inflated infrastructure costs.

- Right-size AppStream fleets by selecting smaller or less specialized instance types that meet current workload demands
- Conduct performance testing after downgrading to ensure that application responsiveness and user experience are preserved
- Update provisioning templates or fleet configurations to reflect optimized instance types going forward

**Underutilized Instances In Ec2 Auto Scaling Group**
Service: AWS EC2 | Type: Underutilized Resource

Oversized instances within Auto Scaling Groups lead to inflated baseline costs, even when scaling adjusts the number of instances dynamically. When workloads consistently use only a fraction of the available CPU, memory, or network capacity, there is an opportunity to downsize to smaller, less expensive instance types without sacrificing performance.

- Evaluate smaller instance types that better match the workload’s actual resource requirements.
- Update the launch template or configuration for the Auto Scaling Group to use the selected instance type, and deploy changes during a low-traffic window if needed.
- After downsizing, monitor performance metrics to ensure the workload continues to meet application and SLA expectations.

**Inactive Appstream Image Builder Or App Block Builder Instances**
Service: AWS AppStream 2.0 | Type: Unused Resource

When AppStream builder instances are left running but unused, they continue to generate compute charges without delivering any value. These instances are commonly left active after configuration or image creation is completed but can be safely stopped or terminated when not in use.

- Stop or decommission builder instances that are no longer required.
- Implement an automated workflow -such as a scheduled Lambda function -that stops builder instances after a defined period of inactivity.
- Establish operational guidelines to ensure builder instances are shut down after image creation or testing tasks are completed.

**Inactive Ec2 Instance**
Service: AWS EC2 | Type: Unused Resource

This inefficiency occurs when an EC2 instance remains in a running state but is not actively utilized. These instances may be remnants of past projects, forgotten development environments, or temporarily created for testing and never decommissioned.

- Identify EC2 instances that have been running throughout the lookback period
- Review CPU utilization, network throughput, and disk activity for sustained inactivity
- Check for the absence of inbound or outbound connections over the same period

**Inactive Eks Cluster**
Service: AWS EKS | Type: Unused Resource

Clusters that no longer run active workloads but remain provisioned continue incurring hourly control plane costs and may also maintain associated infrastructure like node groups or VPC components. Inactive clusters often persist after environment decommissioning, project shutdowns, or migrations.

- Identify EKS clusters with no active Deployments, StatefulSets, DaemonSets, CronJobs, or running pods over a representative time window
- Review node group activity and verify whether any EC2 instances or Fargate tasks are currently attached to the cluster
- Analyze cluster API server logs or CloudWatch metrics to confirm minimal API usage and cluster activity

**Inactive Kubernetes Workload**
Service: AWS EKS | Type: Unused Resource

Workloads with consistently low CPU and memory usage may no longer serve active traffic or scheduled tasks, but continue reserving resources within the cluster. These idle deployments often remain after project migrations, feature deprecations, or experimentation.

- Identify Kubernetes workloads (Deployments, StatefulSets, DaemonSets, or CronJobs) with minimal CPU and memory usage over a representative time window
- Review service exposure, pod restart patterns, and ingress configurations to validate inactivity
- Assess workload labels, annotations, and namespaces to determine original ownership and purpose

**Unnecessary Costs From Unused Lambda Versions With Snapstart**
Service: AWS Lambda | Type: Version Sprawl

Many teams publish new Lambda versions frequently (e.g., through CI/CD pipelines) but do not clean up old ones. When SnapStart is enabled, each of these versions retains an active snapshot in the cache, generating ongoing charges.

- Delete unused Lambda function versions with SnapStart enabled to eliminate unnecessary cache charges
- Implement version lifecycle management practices in CI/CD pipelines to automatically clean up old versions
- Retain only the most recent versions required for rollback or audit purposes

---

### Storage Optimization Patterns (28)

**Overprovisioned Throughput In Efs**
Service: AWS EFS | Type: Explanation

When file systems are launched with Provisioned Throughput, teams often overestimate future demand  - especially in environments cloned from production or sized “just to be safe.” Over time, many workloads consume far less throughput than allocated, especially in dev/test environments or during periods of reduced usage. These overprovisioned settings can silently accrue substantial monthly charges that go unnoticed without intentional review.

- Reconfigure overprovisioned file systems with a reduced Provisioned Throughput value
- For workloads with low and predictable throughput, consider switching to Elastic Throughput
- For dev/test systems cloned from production, adjust throughput settings independently

**Excessive Listbucket Api Calls To An S3 Bucket**
Service: AWS S3 | Type: Inefficient Architecture

ListBucket requests are commonly used to enumerate objects in a bucket, such as by backup systems, scheduled sync jobs, data catalogs, or monitoring tools. When these operations are frequent or target buckets with large object counts, they can generate disproportionately high request charges.

- Identify buckets with a high volume of ListObjects or ListObjectsV2 API requests during the lookback period
- Review whether these requests are part of scheduled automation, backup jobs, or inventory scans
- Check if the frequency of list operations aligns with actual business or operational requirements

**Delayed Transition Of Objects To Intelligent Tiering In An S3 Bucket**
Service: AWS S3 | Type: Inefficient Configuration

Some S3 lifecycle policies are configured to transition objects from Standard storage to Intelligent-Tiering after a fixed number of days (e.g., 30 days). This creates a delay where objects reside in S3 Standard, incurring higher storage costs without benefit.

- Identify buckets where Intelligent-Tiering is the intended or primary storage class
- Review how new objects are placed into those buckets -determine whether they are uploaded directly into Intelligent-Tiering or initially stored in S3 Standard and later moved to Intelligent-Tiering via a Lifecycle Policy
- Evaluate whether the delay provides any functional or operational benefit, or if it is a legacy configuration

**Infrequently Accessed Objects Stored In S3 Standard Tier**
Service: AWS S3 | Type: Inefficient Configuration

S3 Standard is the default storage class and is often used by default even for data that is rarely accessed. Keeping large volumes of infrequently accessed data in S3 Standard leads to unnecessary costs.

- Identify buckets or prefixes where large volumes of data are stored in the S3 Standard tier
- Assess whether the data is actively accessed or retained for archival, compliance, or backup purposes
- Review historical trends to determine whether data access is infrequent, irregular, or absent

**Missing S3 Gateway Endpoint For Intra Region Ec2 Access**
Service: AWS S3 | Type: Inefficient Configuration

When EC2 instances within a VPC access Amazon S3 in the same region without a Gateway VPC Endpoint, traffic is routed through the public S3 endpoint and incurs standard internet egress charges  - even though it remains within the AWS network. This results in unnecessary egress charges, as AWS treats this traffic as data transfer out to the internet, billed under the S3 service.

- Deploy a Gateway VPC Endpoint for S3 in VPCs that generate large intra-region S3 traffic
- Update route tables and access policies to route S3 traffic through the endpoint
- Validate that EC2-to-S3 traffic is using the private path and no longer incurring egress charges

**Missing S3 Lifecycle Policy For Incomplete Multipart Uploads**
Service: AWS S3 | Type: Inefficient Configuration

Multipart upload allows large files to be uploaded in segments. Each part is stored individually until the upload is finalized by a “CompleteMultipartUpload” request.

- Identify S3 buckets that are used for large file uploads or automation-driven data ingestion
- Review whether an S3 Lifecycle rule exists to abort incomplete multipart uploads
- Consult with application owners or platform teams to confirm upload workflows and fault tolerance

**Overprovisioned Ebs Volume**
Service: AWS EBS | Type: Inefficient Configuration

EBS volumes often remain significantly overprovisioned compared to the actual data stored on them. Because billing is based on the total provisioned capacity -not actual usage -this creates ongoing waste when large volumes are only partially used.

- If the volume is attached to a running EC2 instance and can tolerate replacement, create a smaller volume of the same type and migrate the data
- For volumes that cannot be replaced easily, plan to adjust provisioning defaults in AMIs, launch templates, or infrastructure-as-code going forward
- Document sizing assumptions and consider automated checks to catch overprovisioning at creation time

**Suboptimal Lifecycle Policy For Small Files On An S3 Bucket**
Service: AWS S3 | Type: Inefficient Configuration

This inefficiency occurs when small files are stored in S3 storage classes that impose a minimum object size charge, resulting in unnecessary costs. Small files under 128 KB stored in Glacier Instant Retrieval, Standard-IA, or One Zone-IA are billed as if they were 128 KB.

- Review if the bucket contains a high proportion of small objects (e.g., under 128 KB)
- Evaluate whether these small objects are stored in Glacier Instant Retrieval, Standard-IA, or One Zone-IA storage classes
- Assess the access patterns of the small files to determine if frequent retrieval justifies Standard storage

**Suboptimal Use Of Efs Storage Classes**
Service: AWS EFS | Type: Misaligned Storage Tiering

Many organizations default to storing all EFS data in the Standard class, regardless of how frequently data is accessed. This results in inefficient spend for workloads with significant portions of data that are rarely read.

- Transition infrequently accessed data to EFS IA or Archive storage classes to reduce cost
- Enable Intelligent Tiering for workloads where access frequency is variable or difficult to predict
- Maintain Standard storage only for data that requires frequent or high-performance access

**Excessive Kms Charges From Missing S3 Bucket Key Configuration**
Service: AWS S3 | Type: Misconfiguration

S3 buckets configured with SSE-KMS but without Bucket Keys generate a separate KMS request for each object operation. This behavior results in disproportionately high KMS request costs for data-intensive workloads such as analytics, backups, or frequently accessed objects.

- https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingBucketKeys.html

**Missing Lifecycle Policy On Replicated Efs File System**
Service: AWS EFS | Type: Misconfiguration

When replicating an EFS file system across AWS regions (e.g., for disaster recovery), the destination file system does not automatically inherit the source’s lifecycle policy. As a result, files replicated to the destination will remain in the Standard storage class unless a new lifecycle policy is explicitly configured.

- Manually apply a lifecycle policy to the destination EFS file system after replication is configured
- Align the policy with the source file system or tune it based on expected access frequency in the DR region
- Periodically audit replicated EFS environments to ensure lifecycle policies remain in place as environments evolve

**Delete On Termination Disabled For Ebs Volume**
Service: AWS EBS | Type: Misconfiguration Leading to Future Orphaned Resource

When EC2 instances are provisioned, each attached EBS volume has a `DeleteOnTermination` flag that determines whether it will be deleted when the instance is terminated. If this flag is set to `false`  - often unintentionally in custom launch templates, AMIs, or older automation scripts  - volumes persist after termination, resulting in orphaned storage.

- Update the instance configuration to set `DeleteOnTermination=true` for non-persistent volumes
- Modify infrastructure-as-code templates and launch configurations to use the correct flag by default
- Establish policy controls or monitoring to flag instances with unnecessary persistent volume retention

**Excessive Cloudtrail Charges From Bulk S3 Deletes**
Service: AWS S3 | Type: Misconfigured Logging

When large numbers of objects are deleted from S3 -such as during cleanup or lifecycle transitions -CloudTrail can log every individual delete operation if data event logging is enabled. This is especially costly when deleting millions of objects from buckets configured with CloudTrail data event logging at the object level.

- Temporarily disable S3 data event logging before initiating bulk deletes where logging is unnecessary
- Scope CloudTrail data event logging to only include relevant prefixes or buckets requiring detailed auditability

**Misaligned S3 Storage Tier Selection Based On Access Patterns**
Service: AWS S3 | Type: Misconfigured Storage Tier

While moving objects to colder storage classes like Glacier or Infrequent Access (IA) can reduce storage costs, premature transitions without analyzing historical access patterns can lead to unintended expenses. Retrieval charges, restore time delays, and early delete penalties often go unaccounted for in simplistic tiering decisions.

- Use S3 Storage Lens or CUR data to analyze per-object or per-prefix access frequency before applying lifecycle transitions
- Apply intelligent-tiering selectively where access patterns are unpredictable
- Avoid bulk transitions to IA or Glacier for data with unclear or variable access characteristics

**Unexpired Non Current Object Versions In S3**
Service: AWS S3 | Type: Missing Lifecycle Policy

When S3 versioning is enabled but no lifecycle rules are defined for non-current objects, outdated versions accumulate indefinitely. These non-current versions are rarely accessed but continue to incur storage charges.

- Implement lifecycle policies to expire or transition non-current versions after an appropriate retention period
- Tailor policies by bucket or prefix to align with business, compliance, or recovery requirements
- Retain only the number of historical versions necessary for recovery or auditing; remove excess versions automatically

**Outdated And Expensive Ebs Volume Type**
Service: AWS EBS | Type: Modernization

This inefficiency occurs when legacy volume types such as gp2 or io1 remain in use, even though AWS has released newer types -like gp3 and io2 -that offer better performance at lower cost. Gp3 allows users to configure IOPS and throughput independently of volume size, while io2 provides higher durability and more predictable performance than io1.

- Identify volumes using gp2, io1, or other legacy types
- Compare current performance needs (IOPS, throughput) with the default capabilities of newer alternatives
- Evaluate whether the volume type was chosen intentionally or inherited from legacy infrastructure

**Outdated Provisioned Iops Volume Type For High I O Workloads**
Service: AWS EBS | Type: Outdated Resource Selection

Many environments continue using io1 volumes for high-performance workloads due to legacy provisioning or lack of awareness of io2 benefits. io2 volumes provide equivalent or better performance and durability with reduced cost at scale.

- Convert high-IOPS io1 volumes to io2 where supported
- Update provisioning templates to default to io2 for performance-critical workloads
- Validate application compatibility (typically no changes required)

**Underutilized Provisioned Iops On An Ebs Volume**
Service: AWS EBS | Type: Overprovisioned Resource

This inefficiency occurs when an EBS volume has provisioned IOPS levels that consistently exceed the actual I/O requirements of the workload it supports. This can happen when performance buffers are estimated too high, usage patterns change over time, or default settings are left unadjusted.

- Review actual IOPS usage over a representative time window (e.g., 14–30 days)
- Compare provisioned IOPS to peak and average demand to assess excess capacity
- Confirm whether performance requirements or bursty workloads justify the current configuration

**Excessive Retention Of Automated Rds Backups**
Service: AWS RDS | Type: Retention

If backup retention settings are too high or old automated backups are unnecessarily retained, costs can accumulate rapidly. RDS backup storage is significantly more expensive than equivalent storage in S3.

- Adjust backup retention periods to match business or compliance needs
- Delete outdated snapshots or unnecessary automated backups
- Export long-term backups to S3 using snapshot export features

**Missing Intelligent Tiering On Efs Lifecycle Policy**
Service: AWS EFS | Type: Suboptimal Lifecycle Configuration

EFS offers lifecycle policies that transition files from the Standard tier to Infrequent Access (IA) based on inactivity, significantly reducing storage costs for cold data. When this feature is not enabled, infrequently accessed files remain in the more expensive Standard tier indefinitely.

- Enable EFS lifecycle management with a transition period (e.g., 7, 14, 30 days) aligned to actual data access patterns
- Monitor and periodically review access logs or file activity metrics to refine lifecycle timing
- If access latency is not a concern, consider more aggressive transitions to IA for archival-type data

**Unarchived Long Term Ebs Snapshots**
Service: AWS EBS | Type: Suboptimal Storage Tier

EBS Snapshot Archive is a lower-cost storage tier for rarely accessed snapshots retained for compliance, regulatory, or long-term backup purposes. Archiving snapshots that do not require frequent or fast retrieval can reduce snapshot storage costs by up to 75%.

- Archive eligible snapshots using the `ModifySnapshotTier` API, AWS CLI, or console
- Confirm organizational retention policies before archiving
- Ensure teams understand how to restore archived snapshots and the longer retrieval times involved

**Lack Of Deduplication And Change Block Tracking In Aws Backup**
Service: AWS Backup | Type: Underutilization

AWS Backup does not natively support global deduplication or change block tracking across backups. As a result, even traditional incremental or differential backup strategies (e.g., daily incremental, weekly full) can accumulate redundant data.

- Where supported, leverage third-party backup tools with CBT and deduplication (e.g., Commvault, Veeam, Druva)
- Reevaluate backup frequency and retention periods based on RPO/RTO requirements
- Consolidate redundant backup plans across environments and services

**Inactive And Detached Ebs Volume**
Service: AWS EBS | Type: Unused Resource

EBS volumes frequently remain detached after EC2 instances are terminated, replaced, or reconfigured. Some may be intentionally retained for reattachment or backup purposes, but many persist unintentionally due to the lack of automated cleanup.

- Identify EBS volumes that are not attached to any EC2 instance (“available”)
- Review usage data to confirm that no read or write activity has occurred over a defined lookback period
- Check whether the volume is intentionally retained for manual recovery, reattachment, or snapshot purposes, especially if it's part of a known backup or disaster recovery process managed outside of AWS

**Inactive And Unmounted Efs File System**
Service: AWS EFS | Type: Unused Resource

EFS file systems that are no longer attached to any running services  - such as EC2 instances or Lambda functions  - continue to incur storage charges. This often occurs after workloads are decommissioned but the file system is left behind.

- Delete EFS file systems that are no longer in use and have no attached mount targets
- If data must be retained, consider exporting it to a lower-cost storage service (e.g., S3 Glacier) before deletion
- Establish periodic audits to identify and clean up orphaned file systems

**Inactive S3 Bucket**
Service: AWS S3 | Type: Unused Resource

S3 buckets often persist after projects complete or when the associated workloads have been retired. If a bucket is no longer being read from or written to -and its contents are not required for compliance, backup, or retention purposes -it represents ongoing cost without delivering value.

- Identify S3 buckets with no read or write activity during the defined lookback period
- Review object access patterns to confirm that stored data is not being queried or updated
- Check whether the bucket was associated with a decommissioned workload, environment, or application

**Unaccessed Ebs Snapshot**
Service: AWS EBS | Type: Unused Resource

This inefficiency arises when snapshots are retained long after they’ve served their purpose. Snapshots may have been created for backups, migrations, or disaster recovery plans but were never deleted -even after the related workload or volume was decommissioned.

- EBS Snapshot Pricing
- Working with Snapshots

**Unused Ebs Volume Attached To A Stopped Ec2 Instance**
Service: AWS EBS | Type: Unused Resource

This inefficiency occurs when an EC2 instance is stopped but still has one or more attached EBS volumes. Although the compute resource is not generating charges while stopped, the attached volumes continue to incur full storage and performance-related costs.

- Identify EC2 instances in a stopped state during the defined lookback period
- Check whether attached EBS volumes remain actively provisioned
- Validate whether the instance or its volumes are needed for recovery, migration, or scheduled activation

**Unused S3 Storage Lens Advanced**
Service: AWS S3 | Type: Unused Resource

S3 Storage Lens Advanced provides valuable insights into storage usage and trends, but it incurs a recurring cost. Organisations often enable it during an optimization initiative but fail to turn it off afterwards.

- Disable S3 Storage Lens Advanced when not actively needed
- Use the free tier for basic visibility and re-enable Advanced only during optimization cycles
- Set a periodic review of observability tools to ensure paid features still deliver value

---

### RDS cost management strategy
<!-- src:optimnow-rds-handbook -->

Amazon RDS is a fully managed database service but its pricing model is complex enough
to generate unexpected cost surges. RDS instances are a subset of EC2 instance types
but carry a 40-70% premium over equivalent EC2 instances. Understanding the cost
structure and applying a structured optimisation approach prevents RDS from becoming
an outsized line item.

**Why RDS costs surge:**
- On-Demand instances combined with auto-scaling can rapidly inflate costs when
  demand spikes are not scaled back down
- Instance family mismatches mean you pay for resources you do not use
- Provisioned IOPS (io1/io2) storage is expensive and often deployed when gp3 would
  suffice
- Non-production environments (dev, test, QA) inherit production-grade configurations
  (Multi-AZ, oversized instances) without justification

**RDS optimisation framework (source: OptimNow):**

The optimisation sequence matters. Follow this order:

1. **Visibility first** - tag all RDS instances, databases, snapshots, and parameter
   groups. Start with engineering tags (service, environment, owner) for immediate
   waste detection, then add finance tags (cost centre, business unit) for allocation.
   Set up a Cost and Usage Report filtered for RDS to enable Athena-based analysis

2. **Eliminate waste** - identify and remove idle databases (no connections for 7+
   days), orphaned snapshots, and stopped instances approaching the 7-day auto-restart
   limit. Use Trusted Advisor or third-party tools to surface idle resources. Require
   application owner approval before deletion. Take a final snapshot before deleting
   any instance

3. **Implement scheduling** - stop non-production RDS instances outside business
   hours using AWS Instance Scheduler or Systems Manager. This alone can save 60-70%
   on dev/test database costs. Note: start/stop is only possible for single-AZ
   configurations without read replicas - which is the standard setup for non-production
   environments

4. **Right-size instances** - monitor CPUUtilization, FreeableMemory, and ReadIOPS
   in CloudWatch over a 4-week window. If memory consumption is high but CPU stays
   below 40%, transition from general-purpose (m-family) to memory-optimised
   (r-family) instances. Also evaluate Graviton-based instances (e.g. db.r6g, db.r7g)
   which offer up to 35% better performance and up to 52% better cost-effectiveness
   for open-source database engines

5. **Right-size storage** - before committing to Provisioned IOPS (io1/io2), test
   General Purpose gp3. For the majority of workloads, gp3 delivers satisfactory
   latency and throughput at a significantly lower cost. Only workloads with strict
   low-latency, high-throughput SLA requirements justify the io1/io2 premium. Review
   provisioned storage volumes - instances with 2TB provisioned but only 150GB used
   represent direct waste

6. **Review Multi-AZ deployments** - Multi-AZ doubles the cost of database instances
   and storage. Challenge the need by asking: what are the actual RTO and RPO
   requirements? Multi-AZ is essential for production; it is rarely justified for dev,
   test, or QA environments

7. **Improve database performance** - better performance can reduce the required
   instance size:
   - Implement caching with ElastiCache (Redis) to reduce direct database reads
   - Use read replicas to offload heavy read workloads and reduce primary instance
     strain
   - Review indexing and query patterns for I/O efficiency
   - For Aurora, evaluate Aurora Auto Scaling for read replicas to handle unpredictable
     workloads

8. **Review backup and snapshot costs** - manual snapshots persist indefinitely and
   continue incurring charges even after the source database is deleted. Review and
   remove outdated snapshots periodically. Consider relying more on automated backups,
   which self-manage retention. Also review backup retention settings - excessive
   retention on automated backups accumulates cost quickly

9. **Apply Reserved Instances** - commit only after completing steps 1-8 (do not
   commit to waste). Avoid "RDS Paralysis" - waiting for perfect right-sizing before
   purchasing RIs. Open-source database engines (MySQL, MariaDB, PostgreSQL) and
   Aurora support RI size flexibility within an instance family, so the initial RI
   investment remains valid as you continue right-sizing. Start with current
   recommendations and expand coverage as right-sizing progresses

**RDS RI payback guidelines (indicative, verify current pricing):**
- 1-year No Upfront: ~34% discount, no capital outlay
- 1-year Partial Upfront: ~37% discount, payback ~6.5 months
- 3-year Partial Upfront: ~57% discount, payback ~10 months
- For most organisations, 1-year No Upfront is the lowest-risk starting point

**Aurora-specific considerations:**
- Aurora clusters default to Standard I/O configuration, which charges separately for
  I/O operations. For read/write-intensive workloads, evaluate Aurora I/O-Optimized
  which eliminates I/O charges at a higher storage rate
- Aurora clusters running MySQL 5.7 or PostgreSQL 11 that have not been upgraded
  will incur Extended Support surcharges automatically
- Aurora Auto Scaling manages read replica count dynamically - use it to avoid
  over-provisioning read capacity

**Stakeholder alignment for RDS optimisation:**
Effective implementation requires collaboration across roles:
- FinOps practitioners bridge business, IT, and finance; drive evidence-based decisions
- Engineering executes right-sizing, scheduling, and architecture changes
- Finance provides budget constraints and forecasting; helps build the cost-per-unit
  model
- Product/business teams confirm which databases support which products and approve
  changes
- Procurement manages Reserved Instance purchasing strategy

### Database commitment discount decision tree

AWS now offers a **Database Savings Plan** alongside service-specific Reserved
Instances for managed databases. Database Savings Plans provide up to 35% discount
on serverless databases (Aurora Serverless v2, DynamoDB On-Demand, Neptune Serverless)
and up to 20% on provisioned database instances (RDS, Aurora, ElastiCache, MemoryDB,
OpenSearch). Compute Savings Plans still do not cover managed databases - those
workloads need either RIs or the Database Savings Plan, depending on the service.
Choosing the wrong instrument - or committing too early - is the most common database
FinOps mistake.

Source: https://docs.aws.amazon.com/savingsplans/latest/userguide/plan-types.html

**Instrument availability by service:**

| Service | Reserved Instances | Database Savings Plan | Compute Savings Plans | Notes |
|---|---|---|---|---|
| RDS (MySQL, PostgreSQL, MariaDB) | Yes - size-flexible within family | Yes - up to 20% discount | No | RI size flexibility means right-sizing does not invalidate the commitment. Database SP adds spend-based flexibility across engines. |
| RDS (Oracle, SQL Server) | Yes - locked to instance type | Eligibility varies - verify per engine | No | No size flexibility for commercial engines; must match instance exactly |
| Aurora (MySQL, PostgreSQL) | Yes - size-flexible within family | Yes - up to 20% discount (provisioned), up to 35% (Serverless v2) | No | Same RI pool as RDS open-source engines |
| DynamoDB | Yes - Reserved Capacity | Yes - up to 35% discount (On-Demand mode) | No | Commit to read/write capacity units for Provisioned mode; Database SP covers On-Demand |
| ElastiCache (Redis, Memcached) | Yes - node-type specific | Yes - up to 20% discount | No | Locked to node type, no size flexibility |
| MemoryDB | Yes - node-type specific | Yes - up to 20% discount | No | Same mechanics as ElastiCache RIs |
| Neptune | Yes - instance-type specific | Yes - up to 35% discount (Serverless) | No | Low discount depth compared to RDS RIs |
| OpenSearch | Yes - instance-type specific | Yes - up to 20% discount | No | Also covers legacy Elasticsearch domains |
| Redshift | Yes - node-type specific | No | No | Consider Redshift Serverless for variable workloads (no RI available) |
| DocumentDB | Yes - instance-type specific | No | No | Same RI mechanics as RDS commercial engines |

**Verify Database Savings Plan eligibility per engine and instance class** at the
plan-types reference above before sizing - the Database SP scope is narrower than
"all managed databases" and the eligible-engine list evolves.

**Key insight:** Compute Savings Plans do NOT cover any managed database service.
Compute SPs apply to EC2, Fargate, and Lambda. SageMaker AI uses its own Savings Plan.
Managed databases use either RIs (per service) or the Database Savings Plan (where
eligible). If a database runs on EC2 (self-managed), Compute Savings Plans apply to
the EC2 instance - but the database layer itself has no Compute SP coverage.

**Decision tree:**

```
Is the database workload stable and predictable (90+ days of consistent usage)?
├── NO → Stay on On-Demand. Re-evaluate quarterly.
│         For DynamoDB: use On-Demand capacity mode.
│         For Redshift: evaluate Serverless for variable workloads.
│
└── YES → Has the workload been right-sized? (steps 1-8 of RDS framework above)
    ├── NO → Right-size first, commit second. Do not lock in waste.
    │
    └── YES → What database service?
        │
        ├── RDS or Aurora (open-source engine: MySQL, PostgreSQL, MariaDB)
        │   → RDS Reserved Instances with size flexibility
        │     - Start with 1-year No Upfront (~34% discount, zero risk)
        │     - Upgrade to 1-year Partial Upfront (~37%) once confident
        │     - Consider 3-year Partial Upfront (~57%) only for workloads
        │       with 3+ year horizon AND no planned migration
        │     - Size flexibility means you can right-size within the
        │       instance family without losing the RI benefit
        │
        ├── RDS (commercial engine: Oracle, SQL Server)
        │   → RDS Reserved Instances (instance-type locked)
        │     - No size flexibility - must match exact instance type
        │     - Higher risk: right-size thoroughly before committing
        │     - Evaluate BYOL vs License Included cost difference
        │     - Consider migration to open-source engine to unlock
        │       size flexibility and reduce licensing costs
        │
        ├── DynamoDB
        │   → First: switch from On-Demand to Provisioned + Auto Scaling
        │     if usage is predictable (this alone saves 50-80%)
        │   → Then: Reserved Capacity for baseline read/write units
        │     - 1-year or 3-year terms available
        │     - Only commit the steady-state baseline; let Auto Scaling
        │       handle peaks above the reserved floor
        │
        ├── ElastiCache / MemoryDB
        │   → Reserved Nodes (node-type specific)
        │     - No size flexibility - must match exact node type
        │     - For MemoryDB: migrate to Valkey engine first (lower
        │       base cost), then evaluate RI on the new node type
        │
        ├── Redshift
        │   → Reserved Nodes for stable provisioned clusters
        │   → For variable workloads: Redshift Serverless (no RI, pay
        │     per RPU-hour) may be cheaper than committed idle capacity
        │
        └── Neptune / OpenSearch / DocumentDB
            → Reserved Instances (instance-type specific)
              - Evaluate usage carefully; these services often have
                bursty patterns that make commitment risky
              - Start with 1-year No Upfront if committing
```

**Self-managed databases on EC2 vs managed (RDS/Aurora):**

Running databases on EC2 instead of RDS trades management overhead for pricing
flexibility. The decision is rarely purely financial.

| Factor | Self-managed on EC2 | RDS / Aurora |
|---|---|---|
| Instance cost | EC2 On-Demand (cheaper base) | 40-70% premium over equivalent EC2 |
| Commitment options | Compute Savings Plans + EC2 RIs | RDS RIs + Database Savings Plan (eligible engines) |
| Maximum discount | Up to 72% (Standard RI) + EDP | Up to 57% (3yr Partial Upfront RI) + EDP |
| Operational cost | DBA time, patching, backups, HA setup | Managed by AWS |
| BYOL | Full control over licensing | Limited BYOL options (Oracle, SQL Server) |
| Flexibility | Any database engine, any version | AWS-supported engines and versions only |

**When self-managed makes financial sense:**
- Large-scale deployments where the 40-70% RDS premium exceeds the cost of a DBA team
- Commercial engines (Oracle, SQL Server) where BYOL on EC2 is significantly cheaper
  than RDS License Included pricing
- Workloads requiring database versions or configurations not supported by RDS
- Organisations with existing DBA capacity and mature operational practices

**When managed (RDS/Aurora) wins:**
- Teams without dedicated DBA capacity
- Workloads where high availability, automated backups, and patching are critical
- Aurora Serverless v2 for highly variable workloads (no EC2 equivalent)
- When the total cost of ownership (including operational burden) favours managed

**Layering strategy for database commitments:**

1. **EDP as base** - if eligible, the portfolio-wide EDP discount applies to both
   EC2 and RDS, reducing the effective rate before any RI is applied
2. **Right-size and optimise** - complete the 9-step RDS framework before committing
3. **Database Savings Plan for serverless** - if using Aurora Serverless v2, DynamoDB
   On-Demand, or Neptune Serverless, Database SP provides up to 35% discount with
   spend-based flexibility
4. **Reserve the steady-state floor** - commit RIs for provisioned baseline that will
   not change during the term. Leave headroom for scaling
5. **On-Demand for the variable layer** - peaks, new workloads, and workloads under
   evaluation stay on On-Demand until they stabilise
6. **Review quarterly** - commitment coverage should increase as workloads mature,
   not as a one-time purchasing event

**Diagnostic questions:**
- What percentage of your database spend is covered by Reserved Instances today?
- Are any RDS RIs sitting below 80% utilisation? (indicates over-commitment or
  workload changes)
- Do you have commercial-engine RDS instances that could migrate to open-source
  (unlocking size flexibility and reducing licence costs)?
- Are DynamoDB tables on On-Demand mode despite having predictable, steady throughput?
- Is anyone running self-managed databases on EC2 without Compute Savings Plans
  covering those instances?
- Have you evaluated Aurora Serverless v2 for workloads with unpredictable traffic
  before committing to provisioned Aurora RIs?

---

### Databases Optimization Patterns (31)

**Inefficient Use Of On Demand Capacity In Dynamodb**
Service: AWS DynamoDB | Type: Inefficient Configuration

While On-Demand mode is well-suited for unpredictable or bursty workloads, it is often cost-inefficient for applications with consistent throughput. In these cases, shifting to Provisioned mode with Auto Scaling allows teams to set a baseline level of capacity and scale incrementally as needed -often yielding substantial cost savings without compromising performance.

- Identify DynamoDB tables configured to use On-Demand capacity mode
- Review historical read/write activity for patterns of consistent or gradually increasing traffic
- Evaluate whether the workload exhibits steady throughput, such as regular API usage, background jobs, or scheduled data processing

**Outdated Elasticsearch Version Triggering Extended Support Charges**
Service: AWS ElasticSearch | Type: Inefficient Configuration

Many legacy workloads still run on older Elasticsearch versions  - particularly 5.x, 6.x, or 7.x  - due to inertia, compatibility constraints, or lack of ownership. Once these versions exceed their standard support window, AWS begins charging an hourly Extended Support fee for each domain.

- Upgrade to a supported version of OpenSearch
- Be aware that upgrading from Elasticsearch 7.x may require reindexing or application compatibility changes
- Where possible, consolidate or delete unused domains to eliminate unnecessary charges

**Outdated Opensearch Version Triggering Extended Support Charges**
Service: AWS OpenSearch | Type: Inefficient Configuration

Domains running outdated OpenSearch versions  - particularly OpenSearch 1.x  - begin to incur AWS Extended Support charges once they fall outside of the standard support period. These charges are persistent and apply even if the domain is inactive or lightly used.

- Upgrade OpenSearch domains to a supported version
- Test upgrade compatibility in lower environments before applying in production
- Decommission inactive domains to eliminate unnecessary support and compute charges

**Suboptimal Engine Selection In Memorydb**
Service: AWS MemoryDB | Type: Inefficient Configuration

MemoryDB now supports Valkey, a drop-in replacement for Redis OSS offering significant cost and performance advantages. However, many deployments still default to Redis OSS, incurring higher hourly costs and unnecessary data write charges.

- Migrate eligible MemoryDB clusters to use the Valkey engine
- Validate API compatibility and performance requirements prior to migration
- Use zero-downtime upgrade capabilities where possible for seamless transition

**Suboptimal Rds Instance Storage Type**
Service: AWS RDS | Type: Inefficient Configuration

This inefficiency occurs when an RDS instance uses a high-cost storage type such as io1 or io2 but does not require the performance benefits it provides. In many cases, provisioned IOPS are set at or below the free baseline included with gp3 (3,000 IOPS and 125 MB/s).

- Identify RDS instances using high-cost storage types (e.g., io1, io2)
- Review IOPS and throughput metrics to assess whether provisioned performance is being fully utilized
- Evaluate whether current workloads would meet SLAs with a general-purpose alternative like gp3

**Suboptimal Storage Type For Dynamodb Table**
Service: AWS DynamoDB | Type: Inefficient Configuration

This inefficiency occurs when a table remains in the default Standard storage class despite having minimal or infrequent access. In these cases, switching to Standard-IA can significantly reduce monthly storage costs, especially for archival tables, compliance data, or legacy systems that are still retained but rarely queried.

- Identify tables currently set to the Standard storage class
- Review read access patterns over the past 30+ days to confirm low usage
- Determine whether the table is used for active workloads or primarily exists for reference, compliance, or long-term retention

**Suboptimal Storage Configuration For Aurora Cluster**
Service: AWS Aurora | Type: Misconfiguration

Many Aurora clusters default to using the Standard configuration, which charges separately for I/O operations. For workloads with frequent read and write activity, this can lead to unnecessarily high costs.

- Identify Aurora clusters currently using the Standard storage configuration
- Review historical cost breakdowns to evaluate the portion of spend attributed to I/O charges
- Determine whether the workload exhibits high read/write activity or transactional behavior

**Unnecessary Multi Az Configuration For Non Production Rds Instances**
Service: AWS RDS | Type: Misconfigured Redundancy

RDS Multi-AZ deployments are designed for production-grade fault tolerance. In non-production environments, this configuration doubles the cost of database instances and storage with little added value.

**Unnecessary Multi Az Deployment For Elasticache In Non Production Environments**
Service: AWS ElastiCache | Type: Misconfigured Redundancy

In non-production environments, enabling Multi-AZ Redis clusters introduces redundant replicas that may not deliver meaningful business value. These replicas are often kept in sync across Availability Zones, incurring both compute and inter-AZ data transfer costs.

- Reconfigure ElastiCache Redis clusters in non-production environments to use single-node, single-AZ deployments
- If persistence is not needed, consider using Memcached instead of Redis to further reduce costs
- Tag clusters appropriately to distinguish between environments and enforce automated guardrails

**Unnecessary Multi Az Deployment For Opensearch In Non Production Environments**
Service: AWS OpenSearch | Type: Misconfigured Redundancy

Non-production OpenSearch domains often inherit Multi-AZ configurations from production setups without clear justification. This leads to redundant replica shards across AZs, inflating both compute and storage costs.

- Reconfigure OpenSearch domains in non-production environments to use single-AZ deployments
- Reduce the number of replica shards where appropriate
- Implement automated tagging or policy enforcement to prevent accidental Multi-AZ usage in non-prod

**Outdated Rds Cluster Incurring Extended Support Charges**
Service: AWS RDS | Type: Modernization

When an RDS cluster is not upgraded in time, it can fall out of standard support and incur Extended Support charges. This often happens when upgrade cycles are delayed, blocked by compatibility issues, or deprioritized due to competing initiatives.

- Identify RDS clusters running database engine versions past their standard support window
- Confirm whether the cluster is currently accruing Extended Support charges
- Check whether a newer, recommended version is available and compatible with the application

**Inactive Dms Replication Instance**
Service: AWS DMS | Type: Orphaned Resource

Replication instances are commonly left running after migration tasks are completed, especially when DMS is used for one-time or project-based migrations. Without active replication tasks, these instances no longer serve any purpose but continue to incur hourly compute costs.

- Stop and delete DMS replication instances that are no longer associated with active or planned tasks
- Tag replication instances by project or migration wave to enable future clean-up
- Incorporate DMS instance lifecycle checks into post-migration workflows

**Outdated Aurora Versions Triggering Extended Support Charges**
Service: AWS Aurora | Type: Outdated Engine Version

Customers often delay upgrading Aurora clusters due to compatibility concerns or operational overhead. However, when older versions such as MySQL 5.7 or PostgreSQL 11 move into Extended Support, AWS applies automatic surcharges to ensure continued patching.

- Upgrade Aurora clusters to currently supported major versions to avoid Extended Support charges
- Test upgrades in lower environments to validate application compatibility before production cutovers
- Decommission unused or non-critical Aurora clusters rather than paying ongoing surcharges

**Outdated Rds Versions Triggering Extended Support Charges**
Service: AWS RDS | Type: Outdated Engine Version

Many organizations continue to run outdated database engines, such as MySQL 5.7 or PostgreSQL 11, beyond their support windows. Beginning in 2024, AWS automatically enrolls these into Extended Support to maintain security updates, adding incremental charges that scale with vCPU count.

- Upgrade RDS instances to currently supported major versions to avoid Extended Support fees
- Plan upgrades in non-production first to validate compatibility before applying in production
- Decommission unused or development databases that no longer provide value

**Underutilized Rds Commitment Due To Workload Drift**
Service: AWS RDS | Type: Overcommitted Reservation

RDS workloads often evolve  - changing engine types, rightsizing instances, or shifting to Aurora or serverless models. When these changes occur after Reserved Instances have been purchased, the existing commitments may no longer match active usage.

- Evaluate whether current or new workloads can run on the reserved instance types
- Prioritize launching new RDS instances that align with the unused commitment
- Where feasible, upgrade or shift workloads to covered instance classes while monitoring performance and future fit

**Outdated Elasticache Node Type**
Service: AWS ElastiCache | Type: Overprovisioned Resource

Some ElastiCache clusters continue to run on older-generation node types that have since been replaced by newer, more cost-effective options. This can happen due to legacy templates, lack of version validation, or infrastructure that has not been reviewed in years.

- Identify ElastiCache nodes running on older-generation instance types (e.g., T2, M3, R3)
- Compare current node types to newer generation equivalents that offer the same size and better price/performance (e.g., M6g, R6g, T4g)
- Evaluate whether there are operational or application constraints that prevent an upgrade

**Oversized Rds Instance Storage**
Service: AWS RDS | Type: Overprovisioned Resource

This inefficiency occurs when an RDS instance is allocated significantly more storage than it consumes. For example, a 2TB volume might contain only 150GB of actual data.

- Identify RDS instances where provisioned storage significantly exceeds actual usage
- Review storage metrics to validate consistent underutilization (e.g., <25% usage over time)
- Evaluate whether storage needs have declined due to archival, data aging, or workload changes

**Underutilized Elasticache Node**
Service: AWS ElastiCache | Type: Overprovisioned Resource

ElastiCache clusters are often sized for peak performance or reliability assumptions that no longer reflect current workload needs. When memory and CPU usage remain consistently low, the node is likely overprovisioned.

- Rightsize nodes to smaller instance types that align with observed usage
- Modernize to newer instance families when possible to improve price-performance
- Remove idle or redundant nodes in dev, staging, or non-HA environments

**Underutilized Rds Instance**
Service: AWS RDS | Type: Overprovisioned Resource

This inefficiency occurs when an RDS instance is consistently operating below its provisioned capacity -for example, showing low CPU, or memory utilization over an extended period. This often results from conservative initial sizing, decreased workload demand, or failure to review and adjust after deployment.

- Identify RDS instances with consistently low CPU and memory usage over a representative time window
- Compare observed performance to the instance class’s capabilities to assess overprovisioning
- Evaluate whether Auto Scaling is disabled or not configured for compute resizing

**Suboptimal Elasticache Engine Selection**
Service: AWS ElastiCache | Type: Suboptimal Configuration

Many workloads default to using Redis or Memcached without evaluating whether a lighter or more efficient engine would provide equivalent functionality at lower cost. Valkey is a Redis-compatible, open-source engine supported by ElastiCache that may offer improved price-performance and licensing benefits.

- For Redis-compatible but non-persistent workloads, consider migrating to Valkey
- If using Memcached, reevaluate whether Redis or Valkey offers better price-performance
- Note that engine migration typically requires cluster recreation and data migration  - plan accordingly

**Non Graviton Elasticache Node On Eligible Workload**
Service: AWS ElastiCache | Type: Suboptimal Instance Family Selection

Many Redis and Memcached clusters still use legacy x86-based node types (e.g., cache.r5, cache.m5) even though Graviton-based alternatives are available. In-memory workloads tend to be highly compatible with Graviton due to their simplicity and reliance on standard CPU and memory usage patterns. Unless constrained by architecture-specific extensions or strict compliance requirements, most ElastiCache clusters can be transitioned with no application-level changes.

- Switch node types to cache.r6g, cache.m6g, or cache.t4g equivalents
- Update provisioning logic to default to Graviton families for new clusters
- Pilot in non-prod or lower-tier environments to validate behavior and latency

**Non Graviton Rds Instance On Eligible Workload**
Service: AWS RDS | Type: Suboptimal Instance Family Selection

Many RDS workloads continue to run on older x86 instance types (e.g., db.m5, db.r5) even though compatible Graviton-based options (e.g., db.m6g, db.r6g) are widely available. These newer families deliver improved performance per vCPU and lower hourly costs, yet are often not adopted due to legacy defaults, inertia, or lack of awareness. When workloads are not tightly bound to architecture-specific extensions (e.g., x86-specific binaries or drivers), switching to Graviton typically requires no application changes and results in immediate savings.

- Evaluate performance requirements and test Graviton-backed RDS instances in staging
- Modify instance class to a db.*g Graviton-based equivalent (e.g., db.r6g.large)
- Update infrastructure templates (e.g., Terraform, CloudFormation) to default to Graviton where applicable

**Inefficient Use Of Rds Reader Nodes**
Service: AWS RDS | Type: Suboptimal Workload Distribution

RDS reader nodes are intended to handle read-only workloads, allowing for traffic offloading from the primary (writer) node. However, in many environments, services are misconfigured or hardcoded to send all traffic -including reads -to the writer node.

- Refactor application logic or database client configurations to route read traffic to reader endpoints
- Introduce or enhance query routing layers (e.g., using database drivers with read/write splitting support)
- Remove reader nodes if there is no realistic path to utilizing them efficiently

**Underutilized Read Capacity On A Dynamodb Table**
Service: AWS DynamoDB | Type: Underutilization

Provisioned capacity mode is appropriate for workloads with consistent or predictable throughput. However, when read capacity is significantly over-provisioned relative to actual usage, it results in wasted spend.

- Identify DynamoDB tables using Provisioned capacity mode
- Review utilization history to assess average read throughput
- Determine whether actual read usage is consistently below the provisioned capacity

**Underutilized Write Capacity On A Dynamodb Table**
Service: AWS DynamoDB | Type: Underutilization

Provisioned capacity mode is appropriate for workloads with consistent or predictable throughput. However, when write capacity is significantly over-provisioned relative to actual usage, it results in wasted spend.

- Identify DynamoDB tables using Provisioned capacity mode
- Review utilization history over a 14-day or longer period to assess average write throughput
- Determine whether actual write usage is consistently below the provisioned capacity

**Inactive Dynamodb Table**
Service: AWS DynamoDB | Type: Unused Resource

This inefficiency occurs when a DynamoDB table is no longer accessed by any active workload but continues to accumulate storage charges. These tables often remain after a project ends, a feature is retired, or data is migrated elsewhere.

- Identify tables with zero read or write activity over a defined lookback period (e.g. 7, 14, 30+ days)
- Confirm no dependencies exist from applications, analytics jobs, backup processes, or event streams
- Check metadata (tags, naming, creation date) to determine purpose and ownership

**Inactive Rds Cluster**
Service: AWS RDS | Type: Unused Resource

This inefficiency occurs when an RDS cluster remains provisioned but is no longer serving any workloads and has no active database connections. Unlike underutilized resources, these clusters are completely idle -showing no query activity, background processing, or usage over time.

- Identify RDS clusters with no active connections or query activity during the lookback period
- Confirm whether the cluster is receiving any traffic from applications or internal services
- Check for sustained low or zero CPU utilization, network throughput, and read/write IOPS

**Inactive Rds Instance**
Service: AWS RDS | Type: Unused Resource

This inefficiency occurs when an RDS instance remains in the running state but is no longer actively serving application traffic. These instances may be remnants of retired applications, paused development environments, or workloads that were migrated elsewhere.

- Identify RDS instances that have been running continuously during the lookback period
- Review performance metrics to confirm low or zero CPU and memory usage
- Check connection logs and query metrics to validate the absence of active database traffic

**Inactive Rds Read Replica**
Service: AWS RDS | Type: Unused Resource

Read replicas are intended to improve performance for read-heavy workloads or support cross-region redundancy. However, it's common for replicas to remain in place even after their intended purpose has passed.

- Identify all existing RDS read replicas and their associated primary instances
- Assess whether read traffic is being actively routed to each replica
- Review recent query activity to determine if the replica is used for reporting, analytics, or scaling

**Long Retained Rds Manual Snapshot**
Service: AWS RDS | Type: Unused Resource

Manual snapshots are often created for operational tasks like upgrades, migrations, or point-in-time backups. Unlike automated backups, which are automatically deleted after a set retention period, manual snapshots remain in place until explicitly deleted.

- List all manual RDS snapshots across regions and accounts
- Identify snapshots that exceed a predefined age threshold (e.g., 30, 60, or 90 days)
- Check whether snapshots are tied to deleted or decommissioned database instances

**No Lifecycle Management For Temporarily Stopped Rds Instances**
Service: AWS RDS | Type: Unused Resource

While stopping an RDS instance reduces runtime cost, AWS enforces a 7-day limit on stopped state. After this period, the instance is automatically restarted and resumes incurring compute charges  - even if the database is still not needed.

- Take a snapshot and delete the RDS instance to avoid all runtime charges
- Restore from snapshot only when the environment is needed again

---

### Networking Optimization Patterns (14)

**Elastic Load Balancer With Only One Ec2 Instance**
Service: AWS ELB | Type: Inefficient Architecture

An ELB with only one registered EC2 instance does not achieve its core purpose -distributing traffic across multiple backends. In this configuration, the ELB adds complexity and cost without improving availability, scalability, or fault tolerance.

- If no scaling is planned or needed, remove the ELB and route traffic directly to the EC2 instance using a static IP or DNS entry
- If future scaling is expected, consider retaining the ELB but update documentation and monitoring to ensure it doesn't remain in this state long-term
- Document architectural decisions around ELB usage to prevent future misconfigurations

**Imbalanced Data Transfer Between Availability Zones**
Service: AWS Data Transfer | Type: Inefficient Architecture

Some architectures unintentionally route large volumes of traffic between resources that reside in different Availability Zones -such as database queries, service calls, replication, or logging. While these patterns may be functionally correct, they can lead to unnecessary data transfer charges when the traffic could be contained within a single AZ.

- Identify resources that receive or send high volumes of traffic to other Availability Zones within the same region
- Review VPC flow logs, CloudWatch metrics, or billing data to assess regional data transfer patterns
- Determine whether the resource acts as a centralized destination for data aggregation, storage, or processing

**Managed Nat Gateway With Excessive Data Transfer**
Service: AWS NAT Gateway | Type: Inefficient Architecture

NAT Gateways are convenient for enabling outbound access from private subnets, but in data-intensive environments, they can quietly become a major cost driver. When large volumes of traffic flow through the gateway -particularly during batch processing, frequent software updates, or hybrid cloud integrations -the per-GB charges accumulate rapidly.

- Identify NAT Gateways with consistently high data processing volumes over the lookback period
- Review per-GB transfer charges to assess whether NAT Gateway usage represents a significant portion of total networking costs
- Determine whether traffic patterns are driven by expected workload behavior or architectural inefficiencies

**Suboptimal Configuration Of A Cloudfront Distribution**
Service: AWS CloudFront | Type: Inefficient Configuration

This inefficiency occurs when compression is either disabled or not functioning effectively on a CloudFront distribution. Static assets such as text, JSON, JavaScript, and CSS files are compressible and benefit significantly from compression.

- Enable compression for all applicable content types in CloudFront settings
- Review and adjust cache behaviors to ensure compression is applied at the edge
- Coordinate with origin services to ensure headers support compression (e.g., avoid disabling with restrictive cache-control headers)

**Suboptimal Cross Az Routing To Nat Gateway**
Service: AWS NAT Gateway | Type: Inefficient Configuration

NAT Gateways are designed to serve private subnets within the same Availability Zone. When subnets in one AZ are configured to route traffic through a NAT Gateway in a different AZ, the traffic crosses AZ boundaries and incurs inter-AZ data transfer charges in addition to the standard NAT processing fees.

- Update route tables to ensure that each subnet routes outbound traffic through the NAT Gateway in the same AZ
- Ensure one NAT Gateway is deployed per Availability Zone for fault tolerance and cost efficiency
- Review and revise any infrastructure templates or automation that create non-AZ-aware routing

**Suboptimal Routing Through Nat Gateway Instead Of Vpc Endpoint**
Service: AWS NAT Gateway | Type: Inefficient Configuration

Workloads in private subnets often access AWS services like S3 or DynamoDB. If this traffic is routed through a NAT Gateway, it incurs both hourly and data processing charges.

- Create VPC Gateway Endpoints for services like S3 and DynamoDB in applicable regions
- Use Interface Endpoints for other AWS services frequently accessed by private subnet workloads
- Update route tables to redirect traffic through the appropriate VPC endpoint instead of NAT Gateway

**Missing Vpc Endpoints For High Volume Aws Service Access**
Service: AWS VPC | Type: Inefficient Network Configuration

When EC2 instances, Lambda functions, or containerized workloads access AWS-managed services without VPC Endpoints, that traffic exits the VPC through a NAT Gateway or Internet Gateway. This introduces unnecessary egress charges and NAT processing costs, especially for data-intensive or high-frequency workloads.

- Provision Gateway Endpoints for S3 and DynamoDB in each VPC that accesses those services
- Create Interface Endpoints (via AWS PrivateLink) for services with frequent or latency-sensitive access (e.g., Secrets Manager, CloudWatch Logs)
- Ensure routing tables and DNS settings support private resolution to AWS services

**Inactive Application Load Balancer Alb**
Service: AWS ELB | Type: Unused Resource

Application Load Balancers that no longer serve active workloads may persist after application migrations, architecture changes, or testing activities. When no incoming requests are processed through the ALB, it continues to generate baseline hourly and LCU charges.

- Identify Application Load Balancers with no active HTTP/HTTPS requests or minimal LCU consumption over a representative time period
- Confirm there are no listener rules, target groups, or backend services depending on the load balancer
- Review application dependencies, DNS records, and security group configurations to validate safe removal

**Inactive Classic Load Balancer Clb**
Service: AWS ELB | Type: Unused Resource

Classic Load Balancers that no longer serve active workloads will persist if they are not properly decommissioned. This often happens after application migrations, architecture changes, or testing activities.

- Identify Classic Load Balancers with no active connections or data transfer over a representative time period
- Confirm there are no health checks, listener rules, or target instances relying on the load balancer
- Review application and infrastructure dependencies to ensure decommissioning will not disrupt services

**Inactive Gateway Load Balancer Glb**
Service: AWS ELB | Type: Unused Resource

Gateway Load Balancers that no longer have active traffic flows can continue to exist indefinitely unless proactively decommissioned. This often happens after network topology changes, security architecture updates, or environment deprecations.

- Identify Gateway Load Balancers with no active traffic or minimal packet forwarding over a representative time window
- Confirm there are no attached target appliances or ongoing inspection flows depending on the load balancer
- Review networking configurations, route tables, and security group dependencies to validate safe removal

**Inactive Nat Gateway**
Service: AWS NAT Gateway | Type: Unused Resource

NAT Gateways are frequently left running after environments are re-architected, workloads are shut down, or connectivity patterns change. In many cases, they continue to incur hourly charges despite no active traffic flowing through them.

- List all NAT Gateways currently provisioned in each region
- Review flow logs, CloudWatch metrics, or billing data to confirm whether any data has been processed through the gateway during the lookback period
- Validate that no private subnet or route table is actively routing traffic through the NAT Gateway

**Inactive Network Load Balancer Nlb**
Service: AWS ELB | Type: Unused Resource

Network Load Balancers that are no longer needed often persist after architecture changes, service decommissioning, or migration projects. When no active TCP connections or traffic flow through the NLB, it still generates hourly operational costs.

- Identify Network Load Balancers with no active connections or minimal data processing over a defined monitoring window
- Confirm there are no registered targets, listener rules, or backend services depending on the NLB
- Review networking and security configurations to ensure the load balancer is not being used for future failover or redundancy scenarios

**Inactive Vpc Interface Endpoint**
Service: AWS VPC | Type: Unused Resource

VPC Interface Endpoints are commonly deployed to meet network security or compliance requirements by enabling private access to AWS services. However, these endpoints often remain provisioned even after the original use case is deprecated.

- Identify all VPC Interface Endpoints currently provisioned in your account
- Review data transfer activity to determine whether any data has flowed through the endpoint over a representative time period
- Confirm whether the associated AWS service or endpoint service is still used by any workloads in the environment

**Unassociated Elastic Ip Address**
Service: AWS EIP | Type: Unused Resource

Elastic IPs are often provisioned but forgotten  - left unassociated, or still attached to EC2 instances that have been stopped. In either case, AWS treats the EIP as idle and applies an hourly charge.

- Release any EIPs that are no longer required
- Automate audits to identify unassociated or inactive EIPs on a recurring basis
- Update IaC templates or provisioning workflows to clean up networking assets during teardown

---

### Other Optimization Patterns (13)

**Double Counting On Edp Commitments**
Service: AWS Marketplace | Type: Commitment Misalignment

Many organizations mistakenly believe that all AWS Marketplace spend automatically contributes to their EDP commitment. In reality, only certain Marketplace transactions, those involving EDP-eligible vendors and transactable SKUs, will count towards a portion of their EDP commitment.

- Request explicit confirmation of EDP eligibility for key Marketplace vendors and SKUs before purchase
- Negotiate drawdown terms into enterprise contracts when possible
- Maintain a list of verified EDP-eligible SKUs used in cost modeling

**Hidden Marketplace Spend Preventing Commitment Optimization**
Service: AWS Marketplace | Type: Commitment Misalignment

In many organizations, AWS Marketplace purchases are lumped into a single consolidated billing line without visibility into individual vendors. This lack of transparency makes it difficult to identify which Marketplace spend is eligible to count toward the EDP cap.

- Enable detailed cost allocation and tagging to isolate Marketplace spend by vendor
- Cross-reference vendor eligibility with AWS to determine which purchases count toward the 25% Marketplace cap
- Update forecasting and commitment planning to include both direct AWS and eligible Marketplace purchases

**Continuous Aws Config Recording In Non Production Environments**
Service: AWS Config | Type: Excessive Recording Frequency

By default, AWS Config is enabled in continuous recording mode. While this may be justified for production workloads where detailed auditability is critical, it is rarely necessary in non-production environments.

- Update AWS Config settings in non-production accounts to daily recording frequency instead of continuous
- Apply environment-specific configuration baselines to enforce lower granularity tracking outside of production
- Validate that compliance and auditing needs remain satisfied after reducing recording frequency

**Overly Permissive Vpc Flow Log Filters Sent To Cloudwatch Logs**
Service: AWS CloudWatch | Type: Explanation

VPC Flow Logs configured with the ALL filter and delivered to CloudWatch Logs often result in unnecessarily high log ingestion volumes  - especially in high-traffic environments. This setup is rarely required for day-to-day monitoring or security use cases but is commonly enabled by default or for temporary debugging and then left in place.

- Update the VPC Flow Log filter to ACCEPT or REJECT where appropriate
- Consider redirecting logs to S3 for lower-cost storage if detailed analysis is not required in CloudWatch
- Implement periodic audits of logging configurations to catch overly verbose setups

**Unfiltered Recording Of High Churn Resource Types In Aws Config**
Service: AWS Config | Type: Inefficient Configuration

By default, AWS Config can be set to record changes across all supported resource types, including those that change frequently, such as security group rules, IAM role policies, route tables, or network interfaces - frequent ephemeral resources in containerized or auto-scaling setups. These high-churn resources can generate an outsized number of configuration items and inflate costs - especially in dynamic or large-scale environments. This inefficiency arises when recording is enabled indiscriminately across all resources without evaluating whether the data is necessary.

- Limit AWS Config recording to only essential resource types using resource recording groups
- Exclude high-churn resource types that provide minimal compliance or operational value
- Disable Config entirely in sandbox, test, or dev accounts if configuration history is not needed

**Excessive Cloudwatch Log Volume From Persistently Enabled Debugging**
Service: AWS CloudWatch | Type: Inefficient Configuration

Engineers often enable verbose logging (e.g., debug or trace-level) during development or troubleshooting, then forget to disable it after deployment. This results in elevated log ingestion rates  - and therefore costs  - even when the detailed logs are no longer needed.

- Reduce log verbosity from debug/trace to info or warn levels where appropriate
- Implement logging configuration standards across environments, with production defaults
- Use dynamic log level toggling (e.g., via environment variables or feature flags) to avoid persistent debug logging

**Disabled Retry Policies In Eventbridge**
Service: AWS EventBridge | Type: Misconfiguration

By default, EventBridge includes retry mechanisms for delivery failures, particularly when targets like Lambda functions or Step Functions fail to process an event. However, if these retry policies are disabled or misconfigured, EventBridge may treat failed deliveries as successful, prompting upstream services to republish the same event multiple times in response to undelivered outcomes.

- Enable built-in retry policies on EventBridge rules to reduce reliance on external retry logic
- Confirm downstream targets are configured with error handling (e.g., DLQs, retry settings)
- Audit event patterns for high duplication rates and correlate with retry settings

**Suboptimal Log Class Configuration In Cloudwatch**
Service: AWS CloudWatch | Type: Misconfiguration

By default, CloudWatch Log Groups use the Standard log class, which applies higher rates for both ingestion and storage. AWS also offers an Infrequent Access (IA) log class designed for logs that are rarely queried  - such as audit trails, debugging output, or compliance records.

- Create new log groups using the Infrequent Access class for applicable use cases
- Update application and service configurations to route logs to the new log groups
- Use subscription filters or log routing to separate high-access logs (Standard) from infrequent logs (IA)

**Excessive Aws Config Costs From Spot Instances**
Service: AWS Config | Type: Over-Recording of Ephemeral Resources

Spot Instances are designed to be short-lived, with frequent interruptions and replacements. When AWS Config continuously records every lifecycle change for these instances, it produces a large number of CIRs.

- Use tag-based exclusions to prevent AWS Config from recording ephemeral Spot Instances and other transient resources
- Apply standardized tagging (e.g., `finops:config-exclude:true`) and configure AWS Config to filter them out
- If some visibility is required, switch Config from continuous to periodic recording to reduce event volume

**Duplicate Or Overlapping Aws Cloudtrail Trails**
Service: AWS CloudTrail | Type: Redundant Configuration

AWS CloudTrail enables event logging across AWS services, but when multiple trails are configured to log overlapping events - especially data events - it can result in redundant charges and unnecessary storage or ingestion costs. This commonly occurs in decentralised environments where teams create trails independently, unaware of existing coverage or shared logging destinations. Each trail that records data events contributes to billing on a per-event basis, even if the same activity is logged by multiple trails.

- Delete or disable redundant trails that provide no unique audit or compliance value
- Consolidate overlapping trails into a single unified configuration where feasible
- Use centralized log destinations (e.g., one S3 bucket) to reduce storage and ingestion cost

**Suboptimal Use Of Intel Based Instances In Opensearch**
Service: AWS OpenSearch | Type: Suboptimal Instance Selection

AWS Graviton processors are designed to deliver better price-performance than comparable Intel-based instances, often reducing cost by 20–30% at equivalent workload performance. OpenSearch domains running on older Intel-based families consume more spend without providing additional capability.

- Migrate OpenSearch domains from Intel-based instances (e.g., `m5`, `r5`, `i4i`) to equivalent Graviton families (`m6g`, `c6g`, `r6g`, `i4g`)
- Leverage in-place instance type updates for clusters where supported to minimize downtime
- Benchmark performance after migration to validate expected cost-performance improvements

**Unnecessarily High Recording Granularity In Aws Config**
Service: AWS Config | Type: Suboptimal Recording Configuration

Organizations frequently inherit continuous recording by default (e.g., through landing zones) without validating the business need for per-change granularity across all resource types and environments. In change-heavy accounts (ephemeral resources, CI/CD churn, autoscaling), continuous mode drives very high CIR volumes with limited additional operational value.

- Shift suitable resource types and/or non-production environments from continuous to periodic recording where real-time change tracking isn’t required.
- Scope recording frequency by environment: continuous for production or high-risk resources; periodic for development/test or low-risk resources.
- Document the rationale and ownership (e.g., security vs. platform) to ensure shared expectations on visibility vs. cost.

**Inactive Cloudwatch Log Group**
Service: AWS CloudWatch | Type: Unused Resource

CloudWatch log groups often persist long after their usefulness has expired. In some cases, they are associated with applications or resources that are no longer active.

- Identify log groups with significant stored log volume but no recent ingestion activity
- Review historical usage to determine if log data is still being used for operational, security, or compliance purposes
- Evaluate whether the log group is associated with an active application or AWS resource

---

## AWS Multi-Organisation Billing Features

*Added: March 2026. Source: AWS Keys to AWS Optimization podcast, S16E5.*

Two features released at re:Invent 2024 allow FinOps teams to centralise cost visibility and billing operations across multiple AWS organisations. They are related but solve different problems and should not be conflated.

---

### Custom billing views (cross-organisation)

A billing view is an AWS resource that controls which accounts' cost and usage data a given account can access in Cost Explorer, budgets, and dashboards.

**What changed at re:Invent 2024:**

- A payer account can now share a billing view with a payer account in a *different* AWS organisation (previously limited to member accounts within the same org).
- A recipient account can combine multiple billing views -- including views received from other organisations -- into a single aggregated view, giving a unified Cost Explorer experience across several payer accounts.
- Budgets can now be scoped to a billing view, including cross-organisation views.

**Key behaviours:**

- The owner of a billing view retains full control and can modify or revoke it at any time. Changes are reflected in the recipient account and in any combined view that uses it as a source.
- Sharing outside an org requires the `billing-view:full-access` permission level for the recipient to use a view as a source in a combined view.
- Supported tools: Cost Explorer, dashboards, reports, budgets, and forecasts. Amazon Q integration is not yet supported (as of early 2026).
- Creating, sharing, and combining billing views is free. Cost Explorer API calls against a multi-organisation billing view are charged at $0.01 per organisation queried per API call (vs. the standard $0.01 per call for a single org).

**Typical use cases:** enterprises managing multiple AWS organisations after M&A; FinOps teams giving an external consultant read access to cost data without console access; business unit owners needing a budget that spans accounts across multiple payers.

---

### Billing transfer

Billing transfer is a delegation mechanism that allows one payer account (the "bill transfer account") to take over payment responsibility for another AWS organisation's charges (the "bill source account").

**What this enables:**

- Decouples billing from governance. The bill source organisation retains full control of its AWS environment, IAM, governance, and security. It simply delegates invoice responsibility to the bill transfer account.
- The bill transfer account receives the invoice and can view cost and usage data for the bill source organisation centrally, without logging into the source account.
- Integrates with AWS Billing Conductor so the bill transfer account can control what pricing data the bill source account sees (e.g. to protect negotiated rates or to model a reseller margin).

**Key behaviours:**

- The invite process is unidirectional: only the account *taking over* the bill can initiate the transfer. The bill source cannot push its bill to another account.
- Savings plans and credits remain bounded at the organisation level. They do not share across the transfer relationship.
- The bill transfer account sees two distinct views: (1) what it pays AWS for the source org's consumption (net of its own discounts); (2) what the source org sees in its own account -- the "showback view", gross of discounts. These amounts will differ if the bill transfer account has negotiated rates.
- Tax settings and contractual obligations require careful review before enabling billing transfer.
- A basic (public pricing) showback plan is free. A customised pricing plan (e.g. to apply a managed service fee) is charged at $50 per bill source organisation per month, effective June 2025.

**Typical use cases:** AWS channel partners managing resale relationships; enterprises consolidating invoicing after acquisitions; large organisations that want subsidiaries to retain governance autonomy while centralising finance operations.

---

### Feature comparison

| | Custom billing views | Billing transfer |
|---|---|---|
| What it centralises | Cost visibility / data access | Invoice payment |
| Changes billing responsibility | No | Yes |
| Governance boundary | Unchanged | Unchanged |
| Savings plans shared | No | No |
| Credits shared | No | No |
| Supported tools | Cost Explorer, budgets, dashboards, reports | Cost Explorer, budgets, bills page |
| Pricing | Free (API surcharge for multi-org) | Free (basic) / $50/org/month (custom pricing plan) |

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
