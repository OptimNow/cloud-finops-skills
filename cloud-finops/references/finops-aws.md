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
- Supports FOCUS (FinOps Open Cost and Usage Specification) format export (AWS v1.2 as of March 2026)

**CUR setup checklist:**
- [ ] Enable CUR in the management (payer) account
- [ ] Configure S3 bucket with appropriate retention and access policies
- [ ] Enable resource IDs (required for tag-level allocation)
- [ ] Select hourly granularity (daily is insufficient for anomaly detection)
- [ ] Enable Athena integration for SQL-based analysis
- [ ] Consider enabling FOCUS format (v1.2) for tool-agnostic downstream use and cross-cloud normalisation

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

**Cost Explorer limitations to know:**
- 24–48 hour data lag (unacceptable for real-time AI cost management)
- Cannot filter by resource-level tags without enabling resource-level data (additional cost)
- API queries are charged ($0.01 per request)
- Granularity limited to daily in the UI (hourly requires API)

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

AWS provides five distinct instruments for reducing compute costs. Each has different
flexibility, discount depth, and risk profile. The most common mistake is treating
them as alternatives when they are designed to be layered.

**Instrument comparison:**

| Instrument | Discount depth | Flexibility | Commitment type | Term | Covers |
|---|---|---|---|---|---|
| EC2 Standard RI | Up to 72% | Lowest - locked to instance type, region, OS, tenancy | Capacity reservation + rate | 1yr or 3yr | EC2 only |
| EC2 Convertible RI | Up to 66% | Medium - can change instance family, OS, tenancy | Rate only (no capacity) | 3yr only | EC2 only |
| EC2 Instance Savings Plan | Up to 72% | Medium - locked to instance family and region | Spend-based ($/hr) | 1yr or 3yr | EC2 only |
| Compute Savings Plan | Up to 66% | Highest - any instance family, region, OS | Spend-based ($/hr) | 1yr or 3yr | EC2, Fargate, Lambda, SageMaker |
| Spot Instances | Up to 90% | Variable - can be interrupted with 2 min notice | None (market-priced) | None | EC2, EKS nodes, EMR, SageMaker Training |

**Critical distinctions most teams miss:**

1. **EC2 Instance Savings Plans match Standard RI discount depth** (up to 72%) but
   are spend-based, not capacity-based. They offer the same discount with more
   flexibility (any size within the instance family). For most teams, EC2 Instance
   SPs have replaced Standard RIs as the default choice.

2. **Compute Savings Plans are shallower** (up to 66%) but cover EC2, Fargate,
   Lambda, and SageMaker. The flexibility premium costs ~6% discount depth vs
   EC2 Instance SPs.

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
│       - For containerised GPU workloads: see GPU optimisation section
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
├── SageMaker (ML inference and training)
│   │
│   ├── Training jobs → Spot via SageMaker Managed Spot Training
│   │   (up to 90% discount; requires checkpoint support)
│   │   - As of April 2026, use gang scheduling for distributed training
│   │     to prevent resource waste from partial job execution
│   │
│   └── Inference endpoints
│       ├── Stable, predictable → SageMaker Savings Plan (dedicated)
│       │   OR Compute Savings Plan (if mixed with EC2/Fargate/Lambda)
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
    │   - As of April 2026, consider warm pools for faster scale-out:
    │     • Stopped warm pools: lower cost, ~2-3 min boot time
    │     • Running warm pools: higher cost, <30 sec join time
    │     • Cost trade-off: warm pool instances incur charges even
    │       when not actively serving pods
    │     • Best for: workloads with predictable scale patterns or
    │       strict latency requirements on scale-out
    │   - For GPU workloads: see GPU optimisation section below
    │
    └── EKS on Fargate → use Fargate decision tree above
```

### Savings Plan types - detailed comparison

| Dimension | Compute Savings Plan | EC2 Instance Savings Plan |
|---|---|---|
| Commitment | $/hr spend for 1yr or 3yr | $/hr spend for 1yr or 3yr |
| Discount depth | Up to 66% | Up to 72% |
| Instance family | Any | Locked to one family (e.g. m6i) |
| Region | Any | Locked to one region |
| OS | Any | Any |
| Tenancy | Any | Any |
| Size | Any | Any (flexible within family) |
| Covers Fargate | Yes | No |
| Covers Lambda | Yes | No |
| Covers SageMaker | Yes | No |
| Payment options | No Upfront, Partial Upfront, All Upfront | No Upfront, Partial Upfront, All Upfront |
| Discount by payment | All Upfront > Partial > No Upfront | All Upfront > Partial > No Upfront |

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
- For containers: use Karpenter (EKS) or Fargate Spot (ECS)