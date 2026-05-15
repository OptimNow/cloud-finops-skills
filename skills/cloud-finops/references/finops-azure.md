---
name: finops-azure
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Usage Optimization", "Data Ingestion", "Reporting & Analytics"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "Procurement"]
fcp_maturity_entry: "Walk"
---

# FinOps on Azure

> Azure-specific guidance covering cost management tools, commitment discounts, compute
> rightsizing, database and storage optimisation, cost allocation, and governance.
> Covers Cost Management exports, FOCUS exports, Azure Advisor, Reservations, Savings
> Plans, Azure Hybrid Benefit, Azure Policy and tagging governance, AKS optimisation,
> database optimisation (Azure SQL, Postgres/MySQL Flexible, Cosmos DB), Log Analytics
> cost control, backup and snapshot management, storage tiering and lifecycle, and
> networking cost.
>
> Distilled from OptimNow Azure FinOps engagement experience and primary Microsoft
> sources (Azure Pricing pages, Cost Management documentation, FinOps Toolkit).

---

## Azure cost data foundation

### Azure Cost Management exports

Azure Cost Management is the native cost visibility tool. For serious FinOps
implementations, configure scheduled exports to Azure Storage for downstream processing.

**Export types:**
- **Actual cost** - charges as they appear on the invoice (use for billing reconciliation)
- **Amortized cost** - reservation and savings plan charges spread across the usage period
  (use for team-level showback and allocation)

**Export setup checklist:**
- [ ] Configure FOCUS exports at **Billing Account** or **Billing Profile** scope (Management Group is not supported for FOCUS exports)
- [ ] For legacy actual/amortized exports, MG scope is supported but with limitations - keep them on subscription or billing-profile scope for cleanest behaviour
- [ ] Select both actual and amortized cost exports
- [ ] Set daily granularity
- [ ] Export to Azure Data Lake Storage Gen2 for Power BI integration
- [ ] Consider FinOps Hubs (Microsoft FinOps Toolkit) for automated ingestion and normalization

Source for scope rules: https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-improved-exports

**FOCUS export support (April 2026):**
- **Cost Management exports** support a **FOCUS 1.2 preview** dataset, with documented conformance gaps against the published 1.2 spec.
- **FinOps Toolkit v12 / FinOps Hubs** ingest the preview and provide FOCUS 1.2-aligned analytics on top.
- FOCUS 1.0 went GA in Cost Management in June 2024 - that remains the historical baseline; FOCUS 1.2 is the current direction. Configure for multi-cloud normalisation alongside traditional actual/amortized exports.
- **FOCUS 1.3** implementations are emerging across the ecosystem (AWS, Vercel, Grafana Cloud, Redis, Databricks) - Azure's roadmap for 1.3 support has not been announced as of April 2026.

Sources: https://learn.microsoft.com/en-us/cloud-computing/finops/focus/conformance-summary, https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/changelog

**Five first-class export feeds (FinOps Hubs model):** beyond actual/amortized and FOCUS, Cost Management produces three more feeds the FinOps Hubs model treats as first-class:
- **Price sheet** - negotiated price per meter, per Billing Profile
- **Reservation details** - purchases, terms, scope, utilisation
- **Reservation recommendations** - Microsoft's purchase suggestions
- **Reservation transactions** - purchase, exchange, refund history

All five feed the same Hub for unified reservation portfolio analytics. Source: https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/hubs/finops-hubs-overview

### Retail Prices API for validation

Use the Azure Retail Prices API to verify EA discounts against public pricing. Useful for:
- Comparing PAYG vs Reserved Instance pricing with ROI calculation
- Evaluating Spot VM savings potential (60-90% off PAYG)
- Estimating database and storage tier costs across regions
- Validating that EA discount percentages match contracts

### FinOps Toolkit and FinOps Hubs

Microsoft's open-source FinOps Toolkit provides pre-built solutions including Power BI
report templates, Azure Workbooks, and FinOps Hubs for automated cost data ingestion.

**FinOps Hubs** normalize cost exports into a consistent schema and feed Power BI reports.
Recommended for organisations that want production-grade reporting without building custom
data pipelines. FinOps Hubs (Toolkit v12) ingest the **FOCUS 1.2 preview** from Cost
Management and provide 1.2-aligned analytics on top, enabling standardised multi-cloud
cost reporting (see "FOCUS export support" above for the layered preview vs GA picture).

Repository: https://github.com/microsoft/finops-toolkit

### Azure Resource Graph for cost analysis

Azure Resource Graph (ARG) enables large-scale resource inventory and compliance analysis
with KQL queries. Use it for:
- VM analysis by family, OS disk type, hybrid benefit status
- Storage disk type summary (Premium, Standard SSD, Standard HDD, Ultra)
- Tagging compliance analysis with percentages
- Resource distribution by business unit/owner

---

## Commitment discounts

### Compute commitment instruments

Azure provides four distinct instruments for reducing compute costs, plus Azure Hybrid
Benefit which acts as a licensing overlay. As with AWS, these instruments are designed
to be layered, not chosen in isolation.

**Instrument comparison:**

| Instrument | Discount depth | Flexibility | Commitment type | Term | Covers |
|---|---|---|---|---|---|
| Azure Reservation | Up to 72% | Lowest - locked to VM family, region, size | Capacity-based (specific SKU) | 1yr or 3yr (see note) | VMs, Dedicated Hosts, App Service (Isolated), specific services |
| Azure Savings Plan for Compute | Up to 65% | High - any VM family, region, size | Spend-based ($/hr) | 1yr or 3yr | VMs, Dedicated Hosts, Container Instances, App Service (Premium v3 / Isolated v2) |
| Azure Hybrid Benefit (AHB) | Up to 40% (Windows), 55% (SQL) | Highest - no commitment, no lock-in | Licensing overlay | None | VMs, SQL Database, SQL MI, Red Hat/SUSE Linux |
| Spot Virtual Machines | Up to 90% | Variable - can be evicted with 30s notice | None (market-priced) | None | VMs, VMSS, AKS node pools |

**Note on one-year Reserved VM Instances:** As of July 1, 2026, Azure is retiring one-year Reserved VM Instances for select older VM series. This affects new purchases and renewals for these specific series. Three-year reservations remain available for all VM series. When planning reservation strategies, verify current eligibility for one-year terms on your target VM series.

**Critical distinctions:**

1. **Azure Hybrid Benefit is not a commitment - it is free money.** If you have Windows
   Server or SQL Server licenses with Software Assurance, AHB eliminates the license
   component from VM pricing. No contract, no lock-in, no restart needed. This should
   be enabled on all eligible VMs before any other commitment decision. Windows licence
   costs can account for 44% of a Windows VM price (e.g. D4_v5 Windows at ~0.35/hr =
   ~0.19 compute + ~0.15 licence). Use the AHB Workbook from FinOps Toolkit for
   compliance tracking across the fleet.

2. **Savings Plans for Compute cover more than VMs.** Unlike Reservations (which are
   resource-specific), Compute Savings Plans also cover Container Instances and App
   Service Premium v3 / Isolated v2. If you run a mix of VMs, containers, and App
   Service, a Compute Savings Plan is the only instrument that covers all three.

3. **Reservations offer deeper discounts but less flexibility.** A Reservation locks to
   a specific VM family and region. If you change instance family or region mid-term, the
   Reservation does not follow. A Savings Plan is spend-based and applies wherever it
   finds eligible usage - but the discount is ~7% shallower than a Reservation.

4. **Reservations have meaningful liquidity; Savings Plans have none.** See the liquidity
   mechanics table below for fees, caps, and operational rules. The takeaway: Microsoft's
   current reservation-liquidity terms are significantly more generous than AWS Standard
   RI marketplace selling, but read the fine print on the future 12% fee clause.

5. **Savings Plans cannot be exchanged, cancelled, or refunded** once purchased. The
   commitment runs for the full term. This makes phased purchasing and portfolio
   diversification critical for Savings Plans (see "Commitment portfolio liquidity" below).

6. **Spot is not a commitment** - it is a market mechanism with a 30-second eviction
   notice and no SLA. It belongs in the compute cost strategy but should not be compared
   directly against commitment instruments.

7. **VM series lifecycle impacts reservation strategy.** With the July 1, 2026 retirement
   of one-year Reserved VM Instances for select older VM series, factor VM generation
   lifecycle into commitment decisions. For older VM series approaching retirement,
   either plan migration to newer generations or use three-year reservations if the
   workload will remain on the legacy series.

**Reservation and Savings Plan liquidity mechanics (current as of April 2026):**

| Mechanic | Fee | Annual cap | Notes |
|---|---|---|---|
| **Reservation exchange** | None | None | Same product family only. Does not count against the refund cap. The 1 January 2024 sunset of free exchanges was extended indefinitely; reservations purchased during the grace period (which is the current state as of April 2026) retain the right to one more exchange after the grace period eventually ends. |
| **Reservation refund (cancellation)** | None today | $50,000 per 12-month rolling window per Billing Profile (MCA) or enrollment (EA). **The cap restores day-by-day** - 365 days after a refund, the original $50K is fully reinstated. | "Refund" and "cancellation" are the same operation in current docs. Microsoft reserves the right to introduce a 12% early-termination fee in future - verify before relying on liquidity. |
| **Reservation trade-in to Savings Plan** | None | None | Convert RI to Savings Plan credit. No time limit. |
| **Savings Plan cancel / exchange / refund** | N/A | N/A | Not allowed. SPs are non-refundable, non-exchangeable, non-cancellable. |

Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/exchange-and-refund-azure-reservations

### Compute commitment decision tree

```
START: What Azure compute service runs the workload?
│
├── Virtual Machines (including VMSS)
│   │
│   ├── Does the VM run Windows Server or SQL Server with SA licenses?
│   │   └── YES → Enable Azure Hybrid Benefit immediately (up to 40-55%
│   │             savings, no commitment, no restart). Then continue below
│   │             for additional commitment discounts on top of AHB.
│   │
│   ├── Is the workload fault-tolerant and interruptible?
│   │   ├── YES → Use Spot VMs (up to 90% discount)
│   │   │         - Start with 20-30% Spot allocation in non-production
│   │   │         - Use VMSS with Spot priority for auto-scaling pools
│   │   │         - Implement eviction handling (30-second notice)
│   │   │         - Good for: batch, dev/test, CI/CD, stateless tiers
│   │   │
│   │   └── NO → Is the workload stable and predictable (90+ days)?
│   │       ├── NO → Stay on PAYG. Re-evaluate quarterly.
│   │       │
│   │       └── YES → Has it been right-sized? (see Compute rightsizing below)
│   │           ├── NO → Right-size first. Do not commit to waste.
│   │           │
│   │           └── YES → Will it stay on the same VM family + region?
│   │               ├── YES → Is the VM series eligible for 1yr reservations?
│   │               │         (Check: older series may only support 3yr after
│   │               │         July 1, 2026)
│   │               │         ├── YES → Azure Reservation (up to 72%)
│   │               │         │         Deepest discount. Can be exchanged for a
│   │               │         │         different SKU if workload changes (subject
│   │               │         │         to exchange policy limits).
│   │               │         │
│   │               │         └── NO → Consider 3yr reservation or migration to
│   │               │                  newer VM series that supports 1yr terms
│   │               │
│   │               └── NO / UNSURE → Savings Plan for Compute (up to 65%)
│   │                     Covers any VM family and region. ~7% shallower
│   │                     than Reservations but protects against family
│   │                     or region changes. Cannot be exchanged or
│   │                     refunded once purchased.
│   │
│   └── Special case: GPU / N-series VMs
│       - Capacity scarcity is a primary concern (NC, ND, NV families)
│       - Reservations may be necessary to secure capacity in constrained regions
│       - Savings Plans do not reserve capacity - only provide pricing benefit
│       - For ML training: consider Spot VMs with checkpointing
│       - For containerised GPU workloads: see AKS GPU optimisation below
│
├── Azure Kubernetes Service (AKS)
│   │
│   ├── AKS node pools run on VMs → commitment applies to underlying VMs
│   │   (use VM decision tree above for node pool instances)
│   │
│   ├── Spot node pools → use Spot priority for fault-tolerant pods
│   │   - Configure pod disruption budgets for graceful eviction
│   │   - Use taints/tolerations to isolate Spot-eligible workloads
│   │   - Can save 60-90% on non-critical node pools
│   │
│   ├── GPU node pools → special optimisation considerations
│   │   - Enable Dynamic Resource Allocation (DRA) for GPU-aware scheduling
│   │   - Use MPS (Multi-Process Service) for GPU sharing on NVIDIA GPUs
│   │   - Consider MIG (Multi-Instance GPU) for A100/H100 partitioning
│   │   - See "AKS GPU optimisation" section below for detailed guidance
│   │
│   └── Consider: cluster autoscaler + right-sized node pools before committing
│       Pod rightsizing (VPA) saves 20-40%; node pool rightsizing saves 15-30%.
│       Commit after these optimisations are stable, not before.
│
├── App Service
│   │
│   ├── Consumption Plan → no commitment needed (pay per execution)
│   │
│   ├── Premium v3 / Isolated v2 → Savings Plan for Compute applies
│   │   - Only relevant if App Service spend is significant (>$2K/month)
│   │   - Reservations also available for Isolated tier
│   │
│   └── Legacy plans (V2) → migrate to V3 first for better price-performance,
│       then evaluate commitment on the new tier
│
├── Azure Functions
│   │
│   ├── Consumption Plan → pay per execution, no commitment available
│   │   - Focus on optimising execution duration and memory allocation
│   │
│   ├── Premium Plan → runs on App Service infrastructure
│   │   Savings Plan for Compute applies. But first: does the workload
│   │   actually need Premium? Move non-critical functions to Consumption
│   │   Plan before committing to Premium.
│   │
│   └── Dedicated (App Service Plan) → same as App Service above
│
├── Container Instances
│   │
│   └── Savings Plan for Compute covers Container Instances
│       - Only worth committing if usage is sustained and predictable
│       - For short-lived or burst containers, PAYG is usually cheaper
│
└── Azure Databricks
    │
    └── Databricks has its own commitment model (DBCU pre-purchase)
        - Separate from Azure Reservations and Savings Plans
        - See finops-databricks.md for Databricks-specific guidance
```

### Savings Plan vs Reservation - detailed comparison

| Dimension | Azure Reservation | Azure Savings Plan for Compute |
|---|---|---|
| Commitment | Specific SKU for 1yr or 3yr | $/hr spend for 1yr or 3yr |
| Discount depth | Up to 72% | Up to 65% |
| VM family | Locked to one family | Any family |
| Region | Locked to one region | Any region |
| Size | Flexible within family (instance size flexibility) | Any size |
| Covers App Service | Premium v3 + Isolated v2 | App Service & Functions Premium plans (broader SKU set) |
| Covers Container Instances | No | Yes |
| Exchangeable | Yes - same product family, no fee, no cap (does not count against the refund cap) | No |
| Refundable | Pro-rated, up to $50K per 12 months - no fee today; Microsoft reserves right to add 12% future fee | No |
| Cancellable | Yes - refund and cancellation are the same operation today, no fee currently charged | No |
| Payment options | Monthly or Upfront | Monthly or Upfront |
| Scoping | Subscription, resource group, management group, shared | Subscription, resource group, management group, shared |

**Key takeaway:** Reservations offer deeper discounts AND more liquidity (exchanges,
refunds). Savings Plans offer broader coverage but zero liquidity once purchased. This
inverts the common assumption that "flexibility = Savings Plans." For Azure specifically,
Reservations are often the better choice when workloads are moderately stable, because
you retain the ability to exchange if things change.

### Spot Virtual Machines

For fault-tolerant, interruptible workloads, Spot offers up to 90% discount over PAYG.

**Appropriate for Spot:** Batch processing, dev/test, CI/CD, stateless pods in AKS,
ML training with checkpointing, scale-out processing with VMSS.

**Not appropriate:** Stateful databases, workloads with strict SLA requirements,
single-instance workloads with no failover.

**Key constraint:** 30-second eviction notice (vs 2 minutes on AWS), no SLA guarantees.

**Spot best practices:**
- Start with 20-30% Spot allocation in non-production, increase based on stability
- Use VMSS with Spot priority for auto-scaling pools with automatic fallback
- Configure eviction policy: Deallocate (preserves disk) or Delete (lowest cost)
- Set max price at PAYG rate - never bid above PAYG
- For AKS: use Spot node pools with taints/tolerations for workload isolation
- Monitor eviction rates by VM family and region - some combinations are more stable

### Current operational risk: ISF ratio CSV deprecation (9 May 2026)

**Action item with a clock on it.** From **9 May 2026**, Microsoft stops updating
the public CSV file that publishes Instance Size Flexibility (ISF) ratios. Ratio
data moves to **API and PowerShell only** after that date. The CSV will keep being
served but will silently go stale.

**Day 1 audit on any Azure-heavy engagement.** Ask whether any internal tool,
spreadsheet, or automation parses the legacy ISF CSV. If yes, it needs migration
to the Ratios API or PowerShell before the cutover - otherwise reservation-
utilisation reporting drifts as new VM SKUs ship and stale ratios persist in
downstream calculations. The drift is silent (no error) and only surfaces at the
next reservation review when the numbers stop matching Azure Advisor.

Source: [Instance size flexibility for Azure Reservations](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/instance-size-flexibility)

### Azure Hybrid Benefit (AHB)

Organisations with existing Windows Server or SQL Server licenses (with Software
Assurance) can apply them to Azure resources, eliminating the licence premium.

**Why AHB is the #1 quick win:**
- Up to 40% savings on Windows VMs, up to 55% on SQL Database
- No architectural change, no restart needed - single CLI command per VM
- Also applies to SQL Managed Instance and Red Hat/SUSE Linux
- Zero commitment, zero risk, immediate effect
- Use the AHB Workbook from FinOps Toolkit for compliance tracking across the fleet
- **Enable on all eligible VMs before evaluating any other commitment**

### Compute commitment layering strategy

Azure applies discounts in a specific order. The layering sequence matters.

**Discount application order (Azure-defined):**
1. Azure Hybrid Benefit (licence overlay, applied first to eligible VMs)
2. Spot pricing (market rate, for Spot-eligible workloads)
3. Reservations (capacity-based, applied to matching PAYG usage)
4. Savings Plans (spend-based, applied to remaining eligible PAYG usage)

Note: MACC is **not** in this list. It is a commercial commitment / burn-down construct,
not a metered discount applied per usage record. See "MACC - commercial commitment
alignment" below.

**Recommended layering approach:**

```
Layer 0: Azure Hybrid Benefit (free - no commitment, immediate)
  ↓ eliminates licence cost on all eligible Windows/SQL VMs
Layer 1: Spot (for interruptible workloads)
  ↓ removes 15-40% of compute from the commitment equation
Layer 2: Savings Plans for Compute (broad baseline)
  ↓ covers predictable floor across VMs/App Service/Container Instances
Layer 3: Reservations (high-stability VM workloads)
  ↓ captures the extra ~7% discount for workloads locked to a family+region
  ↓ retains exchange/refund liquidity if workload changes
Layer 4: PAYG (variable / new workloads)
```

### MACC - commercial commitment alignment

MACC (Microsoft Azure Consumption Commitment) is **not a metered discount** - it is a
negotiated multi-year spend commitment that runs orthogonally to Reservations and
Savings Plans:

- Eligible Azure consumption (most services) **burns down** the commitment.
- The commercial discount on a MACC, if any, is negotiated up front - it is not applied
  per meter at billing time.
- The FinOps responsibility under MACC is **commitment alignment** - making sure Azure
  spend on the right Billing Profile burns down the right MACC, neither under-utilising
  the commitment (forfeit risk) nor over-utilising it (no further benefit beyond the
  commitment value).
- Reservation and Savings Plan purchases **count toward** MACC burndown - purchasing
  them does not "double-discount" but does pull commitment forward.

**Critical distinction:** A MACC is a binding obligation, not a forecast. If actual
consumption falls short of the committed amount by the end of the term, Microsoft
issues a shortfall invoice. The discount negotiated becomes an additional cost if the
target is missed.

**The optimisation paradox.** The MACC is typically sized based on current architecture
and projected growth. When a FinOps team then rightsizes VMs, decommissions idle
resources, and applies Reservations or Savings Plans, every dollar saved through
optimisation is a dollar that does not draw down against the MACC. The burndown rate -
how fast actual spend reduces the remaining commitment balance - starts to lag. If the
gap is significant, the final quarter becomes a scramble to close it.

This is the core tension: the MACC and the FinOps programme can quietly stop working
in the same direction unless burndown tracking is integrated into optimisation
reporting.

**What counts toward MACC drawdown:**
- Core Azure services consumed under the enrollment
- Azure Reservations for compute
- Azure Marketplace purchases carrying the "Azure benefit eligible" badge, transacted
  through the Azure portal under a subscription tied to the enrollment

**What does not count:**
- Marketplace purchases made by credit card directly on the Marketplace website (the
  purchase path matters even for eligible products)
- Hybrid licensing applied to on-premises workloads
- Azure Prepayment credits used to fund Marketplace purchases (billing mechanics
  separate these from MACC consumption, even though it feels like they should count)

**Reporting pitfall:** Azure Cost Management surfaces both actual cost and amortised
cost views. They produce different burndown numbers. Actual cost reflects when charges
are billed. Amortised cost spreads upfront Reservation purchases across the coverage
term. Without a fixed internal standard for which view to use - applied consistently
in what gets shared with Microsoft - the commitment can appear ahead or behind
depending on who pulls the number.

**Operational guidance:**
- Include MACC burndown rate in FinOps reporting alongside ESR (Effective Savings Rate)
  and commitment coverage. When burndown slows while ESR improves, that is the signal
  to act
- Review required monthly burn rate alongside optimisation metrics in the same session
- Keep procurement and FinOps in the same cadence review at least quarterly
- Maintain a forward-looking list of planned software purchases with MACC eligibility
  confirmed in advance, and pace them to support the burndown trajectory
- Confirm Marketplace eligibility at planning time, not at purchase time
- Do not treat Marketplace as a mechanism for spending toward a target - purchases
  made primarily because they count create vendor relationships, licensing costs, and
  integration work that were never in the original business case

Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/track-consumption-commitment

### Commitment sizing methodology - granularity, Advisor calibration, tooling

The earlier sections cover **what** to commit to (RI vs SP, scope, term, family). This
section covers **how to size** the commitment - the harder problem, with a structural
difficulty in Azure that AWS practitioners do not encounter until they hit it.

#### Data granularity - the AWS-vs-Azure difference that bites in commitment sizing

Azure cost data is **daily**. AWS CUR is **hourly**. This is the structural difference
that changes how you size commitments.

- **Hourly in Azure:** Azure Monitor platform metrics (VM CPU, network, IOPS) -
  utilisation telemetry.
- **Daily in Azure:** Cost Management exports (actual, amortised, FOCUS) and the
  standard Consumption REST endpoints - all billing data.

Consequence: in AWS you read $/hour spend per SKU directly from CUR. In Azure you read
daily spend, but to derive the hourly equivalent you must join cost data with utilisation
data on `ResourceId`.

**Common trap:** consultants moving from AWS to Azure assume hourly cost data is one
query away. It is not. Build the join into your sizing process before you hit the
problem on a live engagement.

#### Why daily data hurts Savings Plan sizing more than RI sizing

**RI sizing** is mostly OK with daily data. An RI commits to a SKU+region count for a
fixed term ("at least 5 D4s_v5 running 24/7"). Daily data answers count questions
reasonably well - if a SKU+region had at least 5 instances every day for 90 days, you
can size the RI confidently.

**SP sizing** is where daily granularity hurts. A Savings Plan commits to a $/hour
amount. The right commitment is roughly the **5th percentile of hourly compute spend** -
the floor below which spend rarely drops. With daily data you cannot see the
hour-by-hour floor; you only see the daily average.

A workload that runs at $100/hour for 8 hours and $30/hour for 16 hours has a daily
average of ~$53/hour but an SP-safe commitment closer to $30.

**Common trap:** **daily-data sizing systematically over-commits Savings Plans on
workloads with within-day cyclicality** - business-hours patterns, batch jobs,
month-end spikes. The over-commitment hides as "low SP utilisation" months later.

#### The cost-plus-utilisation join pattern

The workaround that closes the granularity gap:

1. Pull 90 days of daily compute spend from the FOCUS export, grouped by SKU family
   and region.
2. Pull hourly running vCPUs (or running instance count) per VM from Azure Monitor
   over the same period - via `Percentage CPU` joined with VM size, or VM-running-state
   telemetry from `Heartbeat`.
3. Join cost and utilisation on `ResourceId`.
4. From the hourly view, compute the **5th-10th percentile of running vCPUs** across
   the period - the steady-state floor.
5. Multiply by the SKU's hourly $ rate (from a price sheet export, FOCUS `ListUnitPrice`,
   or the Retail Prices API) to get the SP-safe commitment level.

This is the step the granularity gap forces. FinOps Hubs and most third-party FinOps
platforms do this for you behind the scenes; if you are not using one of those, you
build it yourself.

```kql
// Cost-plus-utilisation join for Savings Plan sizing
// Assumes: FOCUS export ingested as a custom table (e.g. AzureCost_CL) and
// Azure Monitor InsightsMetrics from the same VMs in the same workspace.
// Adjust column names to match your FOCUS ingestion schema.

let lookback = 90d;
let cost =
    AzureCost_CL
    | where TimeGenerated > ago(lookback)
    | where ServiceCategory_s == "Compute"
    | summarize daily_cost_usd = sum(EffectiveCost_d)
                by ResourceId = tolower(ResourceId_s),
                   day = startofday(TimeGenerated);
let util =
    InsightsMetrics
    | where TimeGenerated > ago(lookback)
    | where Namespace == "Processor" and Name == "UtilizationPercentage"
    | summarize hourly_cpu_pct = avg(Val)
                by ResourceId = tolower(_ResourceId),
                   hour = bin(TimeGenerated, 1h);
cost
| join kind=inner util on ResourceId
| summarize p10_cpu_pct      = percentile(hourly_cpu_pct, 10),
            avg_daily_cost   = avg(daily_cost_usd)
            by ResourceId
| extend implied_hourly_floor_usd = (avg_daily_cost / 24.0) * (p10_cpu_pct / 100.0)
| order by implied_hourly_floor_usd desc
```

The query is illustrative - real environments will need the cost-table column names
mapped to whatever FOCUS schema the ingestion produces, and the `_ResourceId`
normalisation tweaked for the customer's resource ID conventions.

#### Calibrating Advisor's reservation and Savings Plan recommendations

Advisor's commitment recommendations are **a sanity check, not a source of truth**.

What Advisor does well: surfaces obvious commitment opportunities at scale (hundreds of
subscriptions, manual analysis impractical). The "you would have saved $X if you had
purchased this RI three months ago" framing is operationally useful for stakeholder
conversations.

**Calibration points** - what Advisor does poorly:

- **Backward-looking by design.** Analyses 7, 30, or 60 days of past usage (default 60
  days). Does not know about a planned decommission, migration, or architecture change.
  If the customer is about to retire a workload, Advisor will recommend committing to it.
- **Does not account for Azure Hybrid Benefit.** Quoted savings are gross of AHB. For
  Windows workloads with AHB applied, the real saving from a recommended RI is
  meaningfully smaller than Advisor states.
- **Does not compare RI vs SP side by side.** RI recommendations and SP recommendations
  live on separate Advisor pages. The actual decision question - "for this workload,
  do I commit via RI or SP?" - Advisor cannot answer for you.
- **Defaults to Shared scope and 1-year term.** Both are usually right, but for
  multi-Billing-Profile MCAs the Shared scope is bounded by the Billing Profile that
  owns the recommendation, not the whole company. Advisor does not warn about this
  scope boundary.
- **Conservative coverage targeting.** Recommendations target ~80-90% of observed usage.
  If the customer wants lower coverage for liquidity reasons (more PAYG buffer for
  workload changes), Advisor does not propose that profile.

**Operating pattern:** take Advisor's output as one input, validate against your own
calculation from the cost-plus-utilisation join, reconcile differences. Differences are
diagnostic - they usually reveal AHB not factored, scope mismatches, or workload context
Advisor cannot know.

Source: https://learn.microsoft.com/en-us/azure/advisor/advisor-reference-cost-recommendations

#### Tooling decision - Power BI / FinOps Hubs / third-party

All three options consume the same underlying Azure data sources, so all three face the
same daily-granularity constraint. The difference is **where the work happens and what
it costs**.

**Custom Power BI on the FOCUS export.** Full control of the logic. Use the FinOps
Toolkit Power BI templates as a starting point - they ship with commitment coverage,
utilisation, and what-if commitment models. Cost: developer time to maintain. Best for
customer-specific reports, when the customer wants to own the analytics layer, or when
integration with non-Azure data is needed.

**FinOps Hubs (Azure-native, open source).** Microsoft's reference implementation.
Deploys an Azure Data Explorer or Fabric backend that ingests FOCUS exports, plus
pre-built Power BI reports. Open source as software - but the ADX or Fabric capacity is
real money. Small ADX cluster ~$300/month; Fabric capacity unit $2,500+/month depending
on size. **The cost of running FinOps Hubs is itself a FinOps line item that should
appear in the customer's cost model.** Best for customers committed to Azure-native,
with engineering capacity to maintain it.

**Third-party (Apptio Cloudability, Vantage, Cast.ai for AKS, Anodot, Spot.io, etc.).**
Pre-built logic, multi-cloud, vendor managed. Cost: typically fixed $X/month or 1-3% of
cloud spend. Best for customers with multi-cloud estates, no in-house FinOps engineering,
or who want a managed view without maintaining infrastructure. Trade-off: dependency on
the vendor data model, and vendor data typically lags Microsoft by 24-72 hours.

**Decision tree:**

```
START: What does the customer need?
|
+-- Single-cloud Azure, small FinOps team, native preference
|   \-- FinOps Hubs
|
+-- Multi-cloud, single pane of glass
|   \-- Third-party (Apptio Cloudability, Vantage, etc.)
|
+-- Specific reports off-the-shelf cannot handle,
|   OR existing Power BI / Fabric / Databricks practice
|   \-- Custom Power BI on FOCUS exports + FinOps Toolkit templates
|
\-- Short engagement (< 2 weeks)
    \-- Cost Management portal + manual Excel export
        Tooling decisions belong in Phase 2 roadmap, not Phase 1
```

#### Six-step commitment strategy framework

The canonical sequence to run on any Azure commitment engagement:

**Step 1 - Data foundation.** Daily FOCUS export to Storage Account, 90 days minimum
of history (trigger backfill if the export is new). Azure Monitor diagnostic settings
emitting VM metrics to a Log Analytics workspace.

**Step 2 - Identify the always-on baseline.** For each SKU family + region, compute
hourly running vCPUs from Azure Monitor over 90 days. The 5th-10th percentile is the
steady-state floor. **This is the step you cannot do from cost data alone - it is
forced by the granularity gap.**

**Step 3 - Coverage planning.** Map the floor to instruments:
- High baseline + low variability + AHB-eligible Windows -> 3-year RI with AHB
- High baseline + low variability + Linux or non-AHB -> 1-year RI if VM series supports
  it (verify post-July 2026 eligibility), otherwise 3-year RI if conviction is high
- Variable workload, stable $ floor -> Savings Plan, 1-year, sized at 70-80% of floor
- Bursty / unpredictable -> PAYG with Spot for the spike layer
- Older VM series approaching retirement -> Plan migration to newer generation or commit
  via 3-year reservation if workload must remain on legacy series

**Step 4 - Validate against Advisor.** Pull Advisor's reservation and SP recommendations.
Reconcile against your own calculation from Step 2. Differences usually reveal AHB not
factored, scope mismatches, or workload changes Advisor cannot know.

**Step 5 - Stagger purchases.** Do not buy the full recommendation at once. Stagger
over 60-90 days so utilisation patterns confirm or surprise before each next tranche.
Reservation exchange liquidity (see "Reservation and Savings Plan liquidity mechanics"
above) gives you a recovery path if Step 4 missed something; SP commitments do not.

**Step 6 - Quarterly re-evaluation.** Exchange RIs that no longer fit the workload.
Track SP utilisation against committed $/hour. Adjust the next quarter's commitments
based on prior actuals, not on Advisor's rolling backward-looking recommendation.

---

## Compute rightsizing

Rightsizing precedes any commitment decision. Committing to an oversized fleet locks
in waste for one to three years. The Azure Advisor recommendation is the obvious
starting point - and also the most misleading default in the entire Cost Management
surface.

### The Advisor threshold trap

Azure Advisor evaluates VMs through two distinct paths with different threshold logic.
Both paths are conservative by design - the result is that Advisor surfaces a thin slice
of the actual rightsizing opportunity, and customers who stop at the Advisor list miss
the bulk of it.

**Shutdown recommendation logic:**
- **P95 CPU < 3%** AND
- **P100 average CPU over the last 3 days <= 2%** AND
- **Outbound network < 2%**

**Resize recommendation logic:** uses CPU, **memory**, and outbound network - with
**different thresholds for user-facing vs non-user-facing workloads** (Microsoft's
internal classification). Memory is part of the resize evaluation, not just CPU.

Source: https://learn.microsoft.com/en-us/azure/advisor/advisor-cost-recommendations

**Common trap:** Advisor's logic is conservative on shutdown and skips many moderate-
rightsizing opportunities. A new Azure customer following Advisor at default settings
will typically see only 5-15% of their actual rightsizing surface; the remainder needs
custom queries (see KQL pattern below) to surface.

### The configurable rule is a display filter, not a tuning knob

Microsoft introduced configurable rules in late 2023 at:

```
Azure portal → Advisor → Configuration → Rules → Right-sizing rules
```

**Important framing:** this rule **filters which existing recommendations get displayed**.
It does not retune the underlying CPU / memory / network logic Advisor uses to generate
those recommendations. If Advisor's evaluation never produced a recommendation for a
given VM (e.g. a 12% steady-state CPU VM that Advisor's logic skipped), no rule change
makes it appear.

**The right pattern to extend coverage** is a custom Azure Monitor or Resource Graph
query that surfaces the band Advisor's logic skips. The KQL example below complements
Advisor - it does not replace or "tune" it.

Scope the display filter rule at **subscription**, **resource group**, or **management
group** as appropriate. Document the scope in the FinOps runbook so the next engineer
understands what is being filtered out of the visible Advisor list.

Source: https://learn.microsoft.com/en-us/azure/advisor/advisor-cost-recommendations

### KQL: catch the band Advisor misses

The band between 5% and 15% steady-state CPU is where most of the structural over-
provisioning sits, and Advisor's shutdown logic (P95 CPU < 3%) does not surface it.
This Azure Monitor query against VM guest metrics fills the gap:

```kql
// VMs with steady-state CPU between 5% and 15% over 30 days
// (the band default Advisor filters out)
InsightsMetrics
| where TimeGenerated > ago(30d)
| where Namespace == "Computer" and Name == "UtilizationPercentage"
| summarize p95_cpu = percentile(Val, 95),
            p50_cpu = percentile(Val, 50)
            by Computer
| where p95_cpu between (5.0 .. 15.0)
| order by p95_cpu asc
```

Cross-reference against the VM SKU catalogue (via Resource Graph) to estimate the
saving from a one-size step-down within the same family.

### The four-dimension check

CPU alone is insufficient. Before recommending a downsize, validate all four
dimensions over the same window:

| Dimension | Source metric | Red flag |
|---|---|---|
| CPU | `Percentage CPU` (host) or guest `% Processor Time` | P95 > 70% (do not downsize) |
| Memory | Guest `\Memory\Available MBytes` or `Committed Bytes In Use` | P95 > 85% utilisation (do not downsize) |
| Disk IOPS | `Data Disk IOPS Consumed Percentage` | P95 > 80% (consider disk SKU change, not VM) |
| Network | `Network In/Out Total` | Sustained at SKU bandwidth ceiling (do not downsize) |

A VM with 8% CPU but 95% memory pressure will OOM on a downsize - the cost saving
is reversed by an outage. This is the most common rightsizing rollback cause.

### B-series caveat - the credit bank trap

Burstable VMs (B-series) accumulate CPU credits during low-use periods and spend them
during bursts. Advisor's default percentile views do not always interpret credit-bank
logic correctly. A B-series VM showing low average CPU may still be drawing down its
credit balance every business hour and would throttle on a downsize.

Before recommending a downsize on any B-series VM, query `CPU Credits Remaining` and
`CPU Credits Consumed`:

```kql
AzureMetrics
| where TimeGenerated > ago(30d)
| where MetricName in ("CPU Credits Remaining", "CPU Credits Consumed")
| where ResourceProvider == "MICROSOFT.COMPUTE"
| summarize p05_remaining = percentile(Total, 5),
            p95_consumed = percentile(Total, 95)
            by Resource, MetricName
```

If P05 of credits remaining trends toward zero, the VM is credit-constrained and the
nominal CPU% understates the demand. Either move off B-series or hold size.

### When rightsizing competes with commitment renewal

If a Reservation is locked to a specific SKU and the workload is genuinely oversized,
rightsize first then exchange the Reservation to the smaller SKU (Azure allows
exchange to equal-or-greater value, but smaller SKUs are accommodated by exchanging
to a different family). For Savings Plans (no exchange), rightsizing within covered
spend is free - the Savings Plan still applies to the smaller VM at the same hourly
commitment.

---

## Log Analytics cost control

On mature Azure customers, Log Analytics is frequently the second-largest cost line
after compute and almost always the most overspent. Default ingestion settings, agent
sprawl, and Sentinel layering compound quickly. The levers below are listed in
order of impact - work top-down.

### Lever 1: Commitment tiers (the quickest win)

Log Analytics offers tiered commitment pricing for daily ingestion. Choosing a tier
above the steady ingestion floor is usually the single largest saving with zero
architectural change:

| Tier | Daily commitment (GB) | Discount vs PAYG ingestion |
|---|---|---|
| Pay-as-you-go | None | 0% (baseline) |
| 100 GB/day | 100 | ~15% |
| 200 GB/day | 200 | ~20% |
| 300, 400, 500 GB/day | as named | ~25% |
| 1000 GB/day | 1000 | ~28% |
| 2000 GB/day | 2000 | ~30% |
| 5000 GB/day | 5000 | ~30% |

Match the tier to the steady-state floor (P10 of daily ingestion over 30-90 days),
not the average. Overshooting the tier means paying for unused capacity; undershooting
means paying PAYG rates above the commitment.

**Source:** https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs

### Lever 2: Table-level tier choice

Each table in a workspace can be set to one of three plans, with order-of-magnitude
cost differences:

| Plan | Query capability | Retention | Cost vs Analytics |
|---|---|---|---|
| **Analytics** | Full KQL, alerts, dashboards | 30 days default; extendable to 2 years interactive (12 years with archive) | Baseline (highest) |
| **Basic** | Limited KQL (no joins, no aggregations across tables) | **30-day query period** (data accessible by KQL for 30 days); total retention up to 12 years | Cheaper ingestion than Analytics |
| **Auxiliary** | KQL with reduced features | **Query for the full retention period** (not search-job only) | Lowest per-GB cost; search and query costs differ by plan |

**Important:** built-in Azure tables (`AzureDiagnostics`, `Heartbeat`, AKS container
logs, `AppTraces`, `W3CIISLog`, etc.) **do not currently support the Auxiliary plan**.
Auxiliary is restricted to specific custom tables on a documented allow-list. Verify
per-table eligibility before assuming Auxiliary is available.

**Realistic candidates for Basic** (where Auxiliary is not yet available for built-in
tables):
- `AzureDiagnostics` (high volume, rarely queried interactively)
- `ContainerLogV2` on AKS (high volume)
- `Heartbeat` (every-minute pings; availability not investigation)
- `AppTraces` at debug level
- `W3CIISLog` for high-traffic web tiers

Move these to Basic where you keep them for short-window troubleshooting. Use
Auxiliary for compliance retention only on tables that explicitly support it.

Sources: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-table-plans, https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs

### Lever 3: Data Collection Rules (DCR) - filter at source

The cheapest log is the one you do not ingest. DCRs apply KQL-based transformations
before ingestion, dropping or sampling rows that hit the workspace. Patterns:

- **Severity filter** - drop `Information`-level entries from `SecurityEvent` if you
  only investigate `Warning` and above
- **Per-host sampling** - retain 1 in 10 verbose rows from chatty agents
- **Column projection** - drop large-payload columns you never query (e.g.,
  `RawEventData` on Windows event logs)

Example DCR transformation that drops Information-level Windows events:

```kql
source
| where EventLevelName != "Information"
```

Apply at the DCR level - changes propagate within minutes and reduce ingestion
volume immediately. Save 30-60% on chatty workspaces with no observability loss
when scoped well.

### Lever 4: Daily ingestion cap as circuit-breaker, not strategy

The workspace daily cap drops data above the threshold and fires an alert. It is
useful only for runaway protection - a misconfigured agent or attack pattern flooding
the workspace. It is **not** a cost optimisation lever. Hitting the cap means
observability gaps for the rest of the day.

Configure the cap at ~150% of the steady ingestion peak. Wire the cap-breach alert
to the FinOps and SRE on-call channels.

### Lever 5: Archive tier and search jobs

Data older than the table's retention period can move to Archive for ~85% lower cost
than Analytics retention. Querying archived data requires a **search job** charged
per GB scanned, so the savings only hold if archive data is rarely queried.

Decision rule: if a table is queried less than once per quarter beyond its first
30 days, archive it. If it is queried weekly, keep it in Analytics retention - the
search-job cost will exceed the retention saving.

### Sentinel-on-LA layering

Microsoft Sentinel charges a **Sentinel premium** on top of the Log Analytics
ingestion cost. The two are entangled - cutting LA ingestion cuts the Sentinel bill
proportionally. Never optimise one without the other:

- Tables in Basic plan are not eligible for most Sentinel analytics rules - confirm
  before moving security-relevant tables to Basic
- Sentinel commitment tiers exist separately from LA commitment tiers - both must
  be sized
- The DCR-level filtering applies before Sentinel sees the data, so source-side
  filtering is the most effective Sentinel cost lever

### KQL: top tables by ingestion

The first query on any LA cost engagement:

```kql
Usage
| where TimeGenerated > ago(30d)
| where IsBillable == true
| summarize GBIngested = round(sum(Quantity) / 1024, 2) by DataType
| order by GBIngested desc
```

The 80/20 distribution is consistent across customers - typically 3-5 tables drive
70-80% of the bill. Address those first.

### KQL: ingestion trend by solution

```kql
Usage
| where TimeGenerated > ago(90d)
| where IsBillable == true
| summarize GBIngested = round(sum(Quantity) / 1024, 2)
            by Solution, bin(TimeGenerated, 1d)
| render timechart
```

Step-changes in the trend usually correlate with a deployment - new agent rollout,
new diagnostic setting, or a debug-level setting left enabled in production.

---

## Snapshot and backup management

Backup and snapshot is its own discipline, not a footnote in storage. Different
decision-makers (security and compliance often own retention, not infrastructure),
different tools (Recovery Services Vault, managed disk snapshots, database PITR/LTR,
blob soft delete), and different waste patterns from generic blob storage.

### Sizing question first

Before any deep-dive, group cost by `MeterCategory` for `Storage`, `Backup`, and
`Azure Backup` over the last 90 days:

```kql
// Cost Management export - share of backup/snapshot in total spend
costmanagement
| where TimeGenerated > ago(90d)
| where MeterCategory in ("Storage", "Backup", "Azure Backup")
| summarize Cost = sum(CostInBillingCurrency) by MeterCategory
```

Or via Resource Graph + Cost Management API. Decision rule:

- **Below 3% of total spend** - hygiene only. Apply the four waste patterns below
  and move on.
- **3-6% of total spend** - mid-priority. Worth a half-day rationalisation.
- **Above 6% of total spend** - deep-dive topic. Schedule a dedicated retention
  review with security and compliance stakeholders.

### The four concentrated waste patterns

Most backup waste sits in four categories. Find these first.

**1. Unattached managed disks.** A VM is deleted, the OS or data disk is left behind,
billing continues at the disk SKU's per-GB monthly rate. On any non-trivial fleet,
expect 5-15% of total disk spend to be unattached.

```kusto
// Resource Graph - unattached managed disks
resources
| where type == "microsoft.compute/disks"
| where properties.diskState == "Unattached"
| extend sizeGB = toint(properties.diskSizeGB),
         sku = sku.name,
         createdDays = datetime_diff('day', now(), todatetime(properties.timeCreated))
| project name, resourceGroup, sku, sizeGB, createdDays, location
| order by sizeGB desc
```

**2. Orphan snapshots older than 90 days.** Manual snapshots taken for a one-off
restore that nobody cleaned up. Often charged at full-source-disk rate even when
incremental.

```kusto
// Resource Graph - snapshots > 90 days, sized
resources
| where type == "microsoft.compute/snapshots"
| extend sizeGB = toint(properties.diskSizeGB),
         createdDays = datetime_diff('day', now(), todatetime(properties.timeCreated))
| where createdDays > 90
| project name, resourceGroup, sizeGB, createdDays, location
| order by createdDays desc
```

**3. Recovery Services Vault on GRS where LRS would do.** Default vault redundancy
is GRS (geo-redundant), which costs roughly 2x LRS. For non-production workloads,
or workloads where the source data is already geo-redundant, LRS is sufficient.

**Common trap:** vault redundancy is set **at creation time** and cannot be changed
in place. Switching from GRS to LRS requires recreating the vault and re-protecting
all items - a multi-day project, not a one-click change. Plan accordingly.

```kusto
// Resource Graph - vaults grouped by redundancy
resources
| where type == "microsoft.recoveryservices/vaults"
| extend redundancy = tostring(properties.redundancySettings.standardTierStorageRedundancy)
| summarize VaultCount = count() by redundancy, location
```

**4. Long-term retention on Standard tier instead of Archive.** Recovery Services
Vault and blob backup support an Archive tier for items older than ~3 months. Cost
saving on the affected volume is roughly 98%. Restore latency from Archive is
hours, not minutes - suitable for compliance copies, not active recovery.

**Source:** https://learn.microsoft.com/en-us/azure/backup/archive-tier-support

### Database backups - sized separately

Database backup costs are accounted under different meters and have their own
retention configuration. Walk each engine:

**Azure SQL Database / Managed Instance:**
- **Point-in-time restore (PITR)** - included up to 7-35 days at no extra cost (set
  via `pitr_retention` or `--backup-retention` on `az sql db`)
- **Long-term retention (LTR)** - paid per GB, billed separately. The typical
  over-retention culprit. Default policies often set monthly/yearly backups for
  10 years across the whole fleet - charge audit retention requirements per
  workload class instead of blanket-applying.

**Cosmos DB:**
- **Periodic backup** - free, two copies retained
- **Continuous backup (7-day or 30-day)** - paid feature, often left on after a
  one-time PITR test. Audit which accounts have it enabled and whether the workload
  actually needs continuous PITR.

**Postgres / MySQL Flexible Server:**
- `backup_retention_days` is per-server, default 7 days, max 35 days. Servers
  inadvertently configured at 35 days without business need are common.

```kusto
// Resource Graph - Postgres Flexible Server backup retention
resources
| where type == "microsoft.dbforpostgresql/flexibleservers"
| extend retentionDays = toint(properties.backup.backupRetentionDays),
         geoRedundant = tostring(properties.backup.geoRedundantBackup)
| project name, resourceGroup, retentionDays, geoRedundant, location
| order by retentionDays desc
```

### Vault Archive tier mechanics

Items in Recovery Services Vault can move to Archive after roughly 3 months of
retention. Constraints to know:

- **Restore latency** - hours, sometimes a full business day. Not for active
  incident recovery; appropriate for audit and compliance copies.
- **Minimum retention in Archive** - 180 days. Early deletion incurs charges for
  the unmet portion.
- **Not all backup types support Archive** - confirm per workload type (Azure VM
  backup, SQL in VM, file share, etc.) before assuming the saving applies.

### Retention-tuning conversation framework

Backup retention is not a FinOps decision in isolation - it is a joint decision
with security, compliance, and the workload owner. Frame the conversation per
workload class:

| Workload class | RPO target | RTO target | Compliance retention floor | Backup policy outcome |
|---|---|---|---|---|
| Compliance-critical (regulated, audit) | <1h | <4h | Per regulation (often 7-10y) | Monthly + yearly LTR to Archive after 90d |
| Production | <4h | <8h | None typically | Daily PITR 30d, weekly 12w, no LTR |
| Non-production | <24h | <24h | None | Daily PITR 7d, no LTR |
| Dev / sandbox | None or self-recreate | N/A | None | Disable backup or weekly snapshot only |

Translate the per-class outcome into an Azure Backup policy and apply via Azure
Policy with `DeployIfNotExists`. This makes retention enforcement structural rather
than per-resource discretionary.

**Sources:**
- https://learn.microsoft.com/en-us/azure/backup/
- https://learn.microsoft.com/en-us/azure/virtual-machines/disks-incremental-snapshots

---

## AKS optimisation in depth

The commitment decision tree above covers AKS at the layer of "node pools run on
VMs - apply VM commitments." That is necessary but not sufficient. AKS-specific
levers - autoscaler tuning, node pool segregation, pod rightsizing - typically
deliver more saving than the commitment layer because they shrink the workload
before commitments are sized.

**Sequence:** pod rightsizing → node pool rightsizing → cluster autoscaler tuning →
commitment purchase. Committing before the cluster is right-sized locks in waste.

### Cluster Autoscaler tuning

The Cluster Autoscaler scales node pools based on pending pods. Default settings
trade saving for stability, often too conservatively:

| Parameter | Default | Aggressive | Trade-off |
|---|---|---|---|
| `scale-down-delay-after-add` | 10 min | 5 min | Aggressive scales down faster after a scale-up event - saves money but can cause pod evictions if traffic is bursty |
| `scale-down-utilization-threshold` | 0.5 | 0.65 | Higher threshold removes nodes when they drop below 65% utilisation rather than 50% - better bin-packing, more eviction pressure |
| `scale-down-unneeded-time` | 10 min | 5 min | How long a node must look unneeded before removal |
| `max-empty-bulk-delete` | 10 | 20 | How many empty nodes can be removed in one cycle |
| `skip-nodes-with-system-pods` | true | true | Keep at default - system pods (CoreDNS, metrics-server) cannot be evicted gracefully |

For non-production, the aggressive column is usually safe. For production with
strict SLOs, stay closer to defaults and lean on pod rightsizing for savings.

**Source:** https://learn.microsoft.com/en-us/azure/aks/cluster-autoscaler-overview

### Node pool segregation

A single node pool serving everything is the most expensive layout. Segregate by
workload class:

- **System pool** - hosts kube-system pods (CoreDNS, metrics-server, konnectivity).
  Stable, non-evictable SKUs. Minimum D2s_v5 or B2ms, 2-3 nodes for HA. Never on
  Spot.
- **General user pool** - Standard Linux nodes, on-demand or with conservative
  autoscaler. Default destination for pods without specific tolerations.
- **Spot user pool** - taint with `kubernetes.azure.com/scalesetpriority=spot:NoSchedule`,
  workloads must tolerate it explicitly. 60-90% saving on stateless or batch pods.
- **GPU pool** - separate pool for NC/ND-series with `nvidia.com/gpu` resource
  requests. Often Spot for training, on-demand for serving.

**Anti-pattern:** running the system pool on Spot. CoreDNS and metrics-server cannot
gracefully tolerate eviction, and a Spot reclaim event can destabilise the entire
cluster's control-plane addons. Always system-pool on dedicated, non-evictable
capacity.

Use **taints and tolerations** to steer pods. The Spot taint above forces explicit
opt-in. Without it, kube-scheduler will pile general workloads onto cheap Spot
nodes that evict during traffic peaks.

**Source:** https://learn.microsoft.com/en-us/azure/aks/use-multiple-node-pools

### Pod-level rightsizing

Node pool rightsizing only goes as deep as the pods running on it. Pod requests and
limits drive the bin-packing:

- **VPA (Vertical Pod Autoscaler)** - recommends or sets `requests` and `limits`
  based on observed usage. Run in `recommendation` mode first to gather data, then
  switch select workloads to `auto` mode. VPA cannot run alongside HPA on the same
  metric (CPU) - this is a common collision.
- **HPA (Horizontal Pod Autoscaler)** - scales replica count based on CPU, memory,
  or custom metrics. Default targets 80% CPU which is usually right.
- **KEDA (Kubernetes Event-Driven Autoscaling)** - scales on external metrics:
  queue depth, event-hub backlog, scheduled cron, Prometheus metric. Critical for
  workloads that should scale to zero outside business hours.

**Typical impact:** pod-level rightsizing yields 20-40% reduction in node pool
capacity demand. Node pool rightsizing on top of that yields another 15-30%.
Layer both before sizing the Reservation or Savings Plan commitment.

### Node SKU sizing trade-off

Many small nodes vs few big nodes - both are wrong defaults. The trade-off:

- **Larger SKUs** (16-32 vCPU) - better bin-packing efficiency (system pod overhead
  amortised), larger blast radius on a node failure, longer drain time.
- **Smaller SKUs** (2-4 vCPU) - faster scale operations, more system pod overhead
  per node (each node carries ~250-500m CPU and ~600-700 MiB memory of system
  daemons), worse bin-packing.

Rule of thumb: aim for **80%+ node utilisation** at steady state. Prefer mid-size
SKUs (8-16 vCPU) for general workloads. Move to larger SKUs only when individual
pods are large enough to benefit from the headroom.

### Azure Linux 3 vs Ubuntu

Azure Linux 3 (AKS-tuned) has a smaller memory footprint, slightly faster startup,
and Microsoft-supported lifecycle. Ubuntu has a broader ecosystem and tooling.
**Cost difference is negligible** - choose for operational reasons (security
hardening, supportability, debug familiarity), not cost.

### Current platform risk: Azure Linux 2 retirement

**Action item for any AKS-heavy engagement.** Azure Linux 2 reached end of support on
**30 November 2025**, and node images were removed on **31 March 2026**. As of
April 2026, customers still on Azure Linux 2:

- Cannot scale node pools (no new images available)
- Face emergency migration cost if a node fails or a scale-out is needed
- Are running unsupported infrastructure with no security patching

**Day 1 audit:** list AKS node pools by OS image (Resource Graph or
`az aks nodepool list`) and flag Azure Linux 2 pools immediately. Migration target is
Azure Linux 3 or Ubuntu 22.04+.

Source: https://learn.microsoft.com/en-us/azure/aks/use-azure-linux

### AKS Node Auto Provisioning (NAP)

Node Auto Provisioning (NAP) is Microsoft's branded, Karpenter-based node provisioning
engine for AKS. It consolidates workloads more aggressively than the Cluster Autoscaler:

- Right-sizes node SKU at runtime based on pending pod requirements (rather than
  scaling a fixed SKU pool)
- Consolidates underutilised nodes by re-scheduling pods onto fewer larger nodes
- Faster bin-packing convergence on heterogeneous workloads

**Limitations to flag before recommending:**
- **Incompatible with Cluster Autoscaler on the same cluster** - choose one or the
  other.
- **No Windows node pool support.**
- Documented egress and networking constraints - verify against the current
  limitations list before adoption.

For AKS-heavy customers with diverse pod sizes, NAP typically delivers an additional
10-20% on top of a tuned Cluster Autoscaler - but only on Linux clusters that can
accept the autoscaler trade-off.

Source: https://learn.microsoft.com/en-us/azure/aks/node-autoprovision

### AKS-specific commitment applicability

- **Reservations and Savings Plans** apply to AKS-managed VMs the same way they
  apply to standalone VMs - the commitment is on the underlying Virtual Machine
  Scale Set instance, not the AKS service.
- **Azure Hybrid Benefit on Windows node pools** - applies, but is **not
  auto-enabled**. The `licenseType` must be set explicitly when creating or
  updating the Windows node pool:

```bash
az aks nodepool add \
  --resource-group rg-aks \
  --cluster-name aks-cluster \
  --name winpool \
  --os-type Windows \
  --enable-ahub
```

Audit existing Windows node pools for missing AHB - this is a common quick win on
mixed Windows/Linux AKS estates.

### KQL: AKS optimisation triage queries

```kusto
// AKS clusters with autoscaler disabled
resources
| where type == "microsoft.containerservice/managedclusters"
| mv-expand pool = properties.agentPoolProfiles
| extend autoscale = tobool(pool.enableAutoScaling),
         poolName = tostring(pool.name)
| where autoscale == false
| project cluster = name, resourceGroup, poolName, location
```

```kusto
// AKS Windows node pools without Hybrid Benefit
resources
| where type == "microsoft.containerservice/managedclusters"
| mv-expand pool = properties.agentPoolProfiles
| extend osType = tostring(pool.osType),
         licenseType = tostring(pool.licenseType),
         poolName = tostring(pool.name)
| where osType == "Windows" and licenseType != "Windows_Server"
| project cluster = name, resourceGroup, poolName
```

```kusto
// Spot node pools without taints (anti-pattern)
resources
| where type == "microsoft.containerservice/managedclusters"
| mv-expand pool = properties.agentPoolProfiles
| extend priority = tostring(pool.scaleSetPriority),
         taints = pool.nodeTaints,
         poolName = tostring(pool.name)
| where priority == "Spot" and (isnull(taints) or array_length(taints) == 0)
| project cluster = name, resourceGroup, poolName
```

---

## Database optimisation patterns

Azure SQL, Postgres / MySQL Flexible Server, and Cosmos DB each have their own
sizing levers. The commitment-side guidance is in the decision-tree section above;
the levers below are the architectural and configuration changes that should
happen **before** any Database Reserved Capacity purchase.

### Azure SQL Serverless auto-pause

Azure SQL Database Serverless tier scales compute automatically and **pauses to
zero compute charge** after an idle period:

- Min vCore configurable from 0.5
- Auto-pause delay - default 60 min, range 1 hour to 7 days, or disabled
- Storage continues to bill while paused; compute charges drop to zero

**Best fit:** dev/test databases, intermittent internal tools, departmental apps,
QA environments.

**Common trap:** cold-start adds 30-60 seconds. Not appropriate for latency-sensitive
production workloads or any workload behind a user-facing transaction.

```bash
# Convert a Provisioned database to Serverless with 1h auto-pause
az sql db update \
  --resource-group rg-data \
  --server sql-server-name \
  --name dbname \
  --edition GeneralPurpose \
  --compute-model Serverless \
  --family Gen5 \
  --min-capacity 0.5 \
  --capacity 4 \
  --auto-pause-delay 60
```

**Source:** https://learn.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-overview

### Elastic Pool sizing

When multiple Azure SQL databases have non-overlapping peaks, an Elastic Pool
shares compute across the set. Rather than paying for each database's peak, you pay
for the **aggregate peak** of the pool.

- Configure pool max DTU/vCore at the **aggregate P95** of pooled workloads, not
  the sum
- Typical saving: 30-50% versus single-database pricing for fleets of 5+ databases
  with mixed traffic patterns
- Per-database min/max DTU/vCore lets you guarantee floor and cap for noisy
  neighbours within the pool

Pooling is most effective when database peaks are uncorrelated (different time
zones, different business functions, dev mixed with batch). When all databases
peak together, the pool size collapses to the sum and savings disappear.

### Hyperscale tier

For Azure SQL databases above ~1 TB or with read-heavy workloads, the Hyperscale
service tier decouples storage from compute:

- Storage scales independently up to 100 TB
- **Named replicas** for read scale-out without provisioning a full secondary
- Per-vCore compute cost similar to Business Critical, but storage is materially
  cheaper at scale
- Backup is snapshot-based (faster, cheaper than General Purpose for large DBs)

**Threshold rule:** consider Hyperscale once a database is >4 TB or when read
replica scale-out is genuinely needed. Below that, General Purpose or Business
Critical is usually the right call.

### Postgres / MySQL Flexible Server start/stop

Flexible Server supports manual start/stop, useful for dev/test and overnight
shutdown. The constraint is auto-restart:

- **Postgres Flexible** - server **auto-restarts after 7 days** stopped. This is a
  Microsoft platform constraint and is **not configurable**.
- **MySQL Flexible** - server **auto-restarts after 30 days** stopped.

**Source:** https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-server-stop-start

This caps how aggressively start/stop can be used as a cost lever for non-prod.
For Postgres, the practical pattern is **stop on Friday evening, restart Monday
morning via automation** - within the 7-day window. For longer dormancy
(seasonal, infrequent dev), the stop is wasted - either keep running with smaller
SKU, or destroy and recreate from backup.

### Cosmos DB - autoscale vs manual throughput

Cosmos DB throughput is provisioned in Request Units per second (RU/s):

- **Manual throughput** - flat hourly cost at the configured RU/s. Cheaper if load
  is predictable and steady.
- **Autoscale throughput** - scales between 10% and 100% of the configured maximum
  RU/s. Costs **1.5x manual at peak**, but only when at peak. For workloads with
  10x peak-to-trough ratios, autoscale is cheaper despite the 1.5x multiplier.

Decision rule: if the steady-state-to-peak ratio is below 1:3, manual is cheaper.
Above 1:3, autoscale wins. Sample 30 days of `Total Request Units` to establish
the ratio before deciding.

Beyond throughput sizing, Cosmos cost optimisation is dominated by **RU efficiency**
per query:

- **Indexing policy** - Cosmos indexes every property by default. On large
  documents this consumes both storage and write RUs. Tune the indexing policy to
  index only queried fields.
- **Partition key** - a hot partition forces over-provisioning to handle the
  bottleneck. Re-partition if a single key receives >10% of traffic.
- **Point reads** (1 RU each) vs **queries** (often 5-50 RU). Where the access
  pattern is by `id`, use point reads.

### Reserved Capacity for databases

Database Reserved Capacity is purchased separately from compute Reservations and
covers different services:

| Service | Reservation type | Term | Saving |
|---|---|---|---|
| Azure SQL Database | vCore reservation | 1y / 3y | up to 33% / 55% |
| Azure SQL Managed Instance | vCore reservation | 1y / 3y | up to 33% / 55% |
| Cosmos DB | RU/s reservation | 1y / 3y | up to 20% / 65% |
| Azure Database for PostgreSQL Flexible | vCore reservation | 1y / 3y | up to 30% / 55% |
| Azure Database for MySQL Flexible | vCore reservation | 1y / 3y | up to 30% / 55% |

Database Reserved Capacity does not auto-apply Hybrid Benefit - SQL Server with
Software Assurance must still be enabled separately on Azure SQL DB / MI.

### KQL: database optimisation triage

```kusto
// Azure SQL DBs not on Serverless that could be (low utilisation)
resources
| where type == "microsoft.sql/servers/databases"
| extend tier = tostring(properties.currentServiceObjectiveName),
         skuName = tostring(sku.name)
| where skuName !contains "GP_S"  // not already Serverless
| where tier startswith "GP_"     // General Purpose only
| project name, resourceGroup, tier, skuName
```

```kusto
// Postgres Flexible servers with backup_retention > 14 days
resources
| where type == "microsoft.dbforpostgresql/flexibleservers"
| extend retentionDays = toint(properties.backup.backupRetentionDays)
| where retentionDays > 14
| project name, resourceGroup, retentionDays, location
```

```kusto
// Cosmos DB accounts on autoscale - candidates for manual switch on steady load
resources
| where type == "microsoft.documentdb/databaseaccounts"
| extend capabilities = properties.capabilities
| project name, resourceGroup, location, capabilities
```

---

## Governance - tagging and Azure Policy as a FinOps lever

Tagging governance and Azure Policy belong together. Policy is the mechanism that
enforces tags; tag compliance is checked via Policy. Treating them as separate
topics is how organisations end up with policies that audit but never enforce, or
tagging schemes that exist on paper but not in production.

### Tagging policy design

Mandatory tag set - the OptimNow default for FinOps allocation:

| Tag | Purpose | Allowed values |
|---|---|---|
| `CostCenter` | Allocation to finance ledger | Controlled enum from finance |
| `Environment` | Lifecycle separation | `Production`, `Staging`, `Development`, `Sandbox` |
| `Owner` | Accountability for spend | Email or distribution list |
| `Application` | Workload grouping | Controlled enum from CMDB or ServiceNow |
| `DataClassification` | Compliance and retention | `Public`, `Internal`, `Confidential`, `Restricted` |

**Critical mechanic:** tags **are not** automatically inherited from a Resource
Group to its resources. A tag on the RG does not propagate to VMs, disks, or NICs
inside it. This is the most common source of "we tag everything" claims that
collapse on audit. Inheritance must be enforced via Policy with `Modify` or
`Inherit a tag from the resource group` built-in.

Tag values should be drawn from a **controlled enum**, not free text. `CostCenter`
values that drift across `12345`, `CC-12345`, `CC12345` make allocation impossible.
Validate at policy deploy time with `allowedValues`.

**Source:** https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/tag-resources

### Azure Policy effects to know

| Effect | Behaviour | Use for |
|---|---|---|
| `Audit` | Logs non-compliance, no action | Starting mode for any new policy |
| `Deny` | Blocks deployment if non-compliant | Hard rules - "no resource creation without `CostCenter`" |
| `Modify` | Adds or changes tags during deployment / via remediation | Tag inheritance from RG |
| `Append` | Adds properties during deployment | Default values for missing fields |
| `DeployIfNotExists` | Deploys a remediation resource if missing | Auto-shutdown schedule, AHB enablement, monitoring agent install |

`AuditIfNotExists` is the read-only sibling to `DeployIfNotExists` - use to flag
where remediation is needed without auto-deploying.

**Source:** https://learn.microsoft.com/en-us/azure/governance/policy/concepts/effects

### Audit-mode rollout pattern

Going straight to `Deny` on day one breaks deployments and creates tickets. The
defensible rollout sequence:

1. **Deploy in `Audit` mode** - log non-compliance for 2-4 weeks
2. **Run remediation tasks** to fix the existing fleet (`Modify` and
   `DeployIfNotExists` policies have built-in remediation)
3. **Communicate the cutover date** to all teams that deploy resources
4. **Escalate to `Deny`** for new deployments
5. **Keep `Audit` mode** for tags that are nice-to-have but not blocking

This sequence converts policy from a deployment blocker into a governance lever
without breaking the engineering workflow.

### Cost allocation patterns

Three patterns, in order of allocation cleanliness vs flexibility:

1. **Subscription-per-business-unit** - the cleanest allocation model. Each
   business unit consumes its own subscription, billing rolls up by subscription
   ID, no tags needed for business-unit allocation. Trade-off: rigid - changes to
   the org structure require subscription migrations.
2. **Tag-based allocation** - flexible but depends on tag hygiene. `CostCenter`
   becomes the allocation key. Use Cost Management's allocation rules to split
   shared subscription costs (network, governance) across consumers based on tag
   values.
3. **Hybrid** - subscription per BU for direct costs, tag-based allocation for
   shared services. Most enterprise customers end here.

**Cost Management allocation rules** can split shared costs (a shared subscription,
RG, or service) across consumers based on tag values, fixed proportions, or
absolute amounts. Document the allocation rule logic in the FinOps runbook -
allocation-rule debugging is otherwise an audit nightmare.

### Chargeback vs showback decision

- **Showback** - costs are visible to consuming teams, no money moves. Appropriate
  for low-to-medium maturity, or organisations without internal billing plumbing.
  Most enterprise FinOps engagements end here.
- **Chargeback** - costs flow to consuming teams' budgets. Requires finance
  process and tooling to actually move money internally. Appropriate when the
  organisation has the financial plumbing and the cultural readiness to be
  confronted with its consumption.

Recommend showback first. Chargeback adds organisational complexity and only pays
off when the showback signal stops driving behaviour change on its own.

### OptimNow tooling for tag governance

Two OptimNow assets directly relevant to engagement delivery:

- **Tag compliance MCP (open source)** -
  https://github.com/OptimNow/finops-tag-compliance-mcp - agent-accessible tag
  compliance auditing across Azure (and AWS). Recommended pattern when an
  engagement needs ongoing tag compliance reporting integrated with an AI agent.
- **Tagging policy generator** -
  https://vercel.com/optim-now/tagging-policy-generator - generates Azure Policy /
  AWS SCP / GCP Org Policy from a tagging schema. Fastest way to bootstrap a
  tagging policy from a customer's tag taxonomy without hand-writing Bicep or ARM.

### KQL: tag governance triage

```kusto
// Untagged resources by RG
resources
| where isempty(tags) or tags == dynamic({})
| summarize Untagged = count() by resourceGroup, subscriptionId
| order by Untagged desc
```

```kusto
// Resources missing CostCenter
resources
| where isnull(tags.CostCenter) or tags.CostCenter == ""
| summarize MissingCostCenter = count() by type, subscriptionId
| order by MissingCostCenter desc
```

```kusto
// Tag value drift detection - CostCenter case-insensitive variants
resources
| where isnotempty(tags.CostCenter)
| extend ccLower = tolower(tostring(tags.CostCenter)),
         ccActual = tostring(tags.CostCenter)
| summarize variants = make_set(ccActual) by ccLower
| where array_length(variants) > 1
```

The third query catches `cc-12345` / `CC-12345` / `Cc-12345` style drift - the
silent allocation killer.

---

## Storage tiering and lifecycle (beyond backup)

Backup-side storage is in the snapshot/backup section above. This section covers
generic blob, disk, and lifecycle decisions that apply to all storage.

### Blob hot / cool / cold / archive decision criteria

| Tier | Read pattern | Min retention before tier-down | Early-deletion penalty |
|---|---|---|---|
| Hot | Frequent (multiple times/month) | None | None |
| Cool | Infrequent (~once/month) | 30 days | Yes - prorated to 30d |
| Cold | Rare (~once/quarter) | 90 days | Yes - prorated to 90d |
| Archive | Compliance / DR only | 180 days | Yes - prorated to 180d |

**Common trap:** moving data to Archive then re-tiering or deleting within 180
days incurs the prorated charge for the unmet window. On large-scale lifecycle
moves, validate that source data has been stable for at least the minimum
retention before scheduling the tier-down rule. Rehydration from Archive takes
hours (1-15h standard, ~1h high priority, charged separately) - factor this into
RPO/RTO.

**Source:** https://learn.microsoft.com/en-us/azure/storage/blobs/lifecycle-management-overview

### Redundancy choice per workload class

Storage redundancy SKU drives a 2-3x cost multiplier. Default `GRS` ("safe") on
everything is overspending:

| SKU | Replication | Cost multiplier | Use for |
|---|---|---|---|
| LRS | 3 copies, 1 datacentre | 1x (baseline) | Non-prod, ephemeral data, source data already replicated upstream |
| ZRS | 3 copies, 3 zones in 1 region | ~1.25x | Production within-region, active-active workloads |
| GRS | LRS + async copy to paired region | ~2x | Production where geo-redundancy is a hard requirement and source data is not already geo-redundant |
| GZRS | ZRS + async copy to paired region | ~2.5x | Compliance-driven highest tier |
| RA-GRS / RA-GZRS | GRS / GZRS with read access to secondary | ~2.5-3x | Active read failover |

Rule: do not pay for geo-redundancy on storage that mirrors a system already
geo-replicated upstream (database secondaries, replicated source-of-truth blob
stores).

### Soft delete and versioning - default-on cost traps

New storage accounts have **soft delete enabled by default** (containers, blobs,
file shares) with 7-day retention. Versioning, when enabled, retains every
overwrite as a separate billable version.

Both are valuable safety features and both **accumulate cost silently** if no
lifecycle rule prunes old versions and soft-deleted blobs. On busy workspaces, the
versioning charge can rival the live-data charge after 6-12 months.

Lifecycle rule pattern (Bicep) for version pruning:

```bicep
{
  name: 'pruneOldVersions'
  enabled: true
  type: 'Lifecycle'
  definition: {
    actions: {
      version: {
        delete: { daysAfterCreationGreaterThan: 90 }
      }
    }
    filters: { blobTypes: [ 'blockBlob' ] }
  }
}
```

For soft delete, a similar rule prunes deleted blobs after a fixed window. Match
the window to the actual incident-recovery use case, not a default 365 days.

### Ephemeral OS disks for stateless VMs

Ephemeral OS disks are stored on the VM's local cache or temp disk - **no managed
disk charge**. Trade-offs:

- Free (no managed disk billing for the OS disk)
- Lost on VM reallocation, deallocation, or stop-deallocate
- Available only on certain VM SKUs and only for OS disks (not data disks)

Appropriate for stateless VM scale sets, container hosts, and immutable-image
workloads. Not appropriate for VMs that need to survive deallocation, or workloads
that store anything on the OS disk.

### Premium SSD v2 vs Premium SSD v1 vs Standard SSD

Premium SSD v2 is per-IOPS billed (you provision capacity, IOPS, and throughput
independently) rather than fixed per-tier:

- For moderate-IOPS workloads (3,000-10,000 IOPS), Premium SSD v2 is often
  **cheaper** than Premium SSD v1 because you're not paying for the over-provisioned
  IOPS bundled into the v1 SKU.
- Standard SSD remains the default unless workload IOPS justifies the upgrade.
- Ultra Disk is a separate product for >80,000 IOPS or sub-ms latency requirements.

**Sizing default:** start on Standard SSD. Migrate to Premium SSD v2 only when
performance metrics demonstrate IOPS or throughput contention.

### Lifecycle rule examples (tier-down by age)

```bicep
{
  name: 'tierDownColdArchive'
  enabled: true
  type: 'Lifecycle'
  definition: {
    actions: {
      baseBlob: {
        tierToCool: { daysAfterModificationGreaterThan: 30 }
        tierToCold: { daysAfterModificationGreaterThan: 90 }
        tierToArchive: { daysAfterLastAccessTimeGreaterThan: 180 }
        delete: { daysAfterModificationGreaterThan: 2555 } // 7 years
      }
    }
    filters: {
      blobTypes: [ 'blockBlob' ]
      prefixMatch: [ 'logs/', 'archive/' ]
    }
  }
}
```

Tier-down rules use `daysAfterModificationGreaterThan` or, more accurately,
`daysAfterLastAccessTimeGreaterThan` (requires last-access tracking enabled on the
storage account).

---

## Networking cost

Networking is the most commonly underestimated cost line on multi-region or
hub-spoke architectures. The egress and peering charges are small per GB but
compound to material amounts on busy workloads.

### Egress pricing tiers

Outbound to internet, per-GB pricing decreases by volume:

| Volume per month | Approximate price per GB |
|---|---|
| First 100 GB | Free |
| 100 GB - 10 TB | ~$0.087 |
| 10 - 50 TB | ~$0.05 |
| 50 - 150 TB | ~$0.04 |
| Above 150 TB | Negotiated |

Egress *between* Azure regions is charged separately at ~$0.02/GB outbound from
the source region.

**Source:** https://azure.microsoft.com/en-us/pricing/details/bandwidth/

### VNet peering - the multi-region surprise

VNet peering charges **$0.01/GB on each side** - both ingress to peer and egress
to peer. For a multi-region architecture peered through a hub VNet, every cross-
region byte is billed twice (once on each peering edge). On busy hub-spoke
designs, peering can be a meaningful share of the network bill.

Reduce peering traffic by:
- Co-locating chatty workloads in the same VNet
- Using Private Link / Private Endpoint for cross-VNet PaaS access (peering
  charge replaced by Private Endpoint charge - see below for trade-off)
- Using Azure Virtual WAN where many spokes need to talk to many spokes (replaces
  full-mesh peering)

### VPN Gateway and ExpressRoute pricing

| Product | Pricing model |
|---|---|
| VPN Gateway Basic | Hourly, single-tunnel, deprecated for new deployments |
| VPN Gateway VpnGw1-5 | Hourly tier rate, throughput scales with tier |
| VPN Gateway VpnGw1-5AZ | Zone-redundant variants, ~25% premium over non-AZ |
| ExpressRoute Local | Per-hour, no egress charge for in-region peering location |
| ExpressRoute Standard | Per-hour + per-GB egress |
| ExpressRoute Premium | Per-hour + per-GB egress + global reach + larger circuit limits |

ExpressRoute Local is the cheapest model when the customer has a peering location
co-located with their Azure region. Standard and Premium are charged per-GB on
top of the hourly circuit cost - audit metered vs unlimited billing options for
high-throughput circuits.

### NAT Gateway as a hidden cost driver in AKS

NAT Gateway has two charges: **per-hour** (~$0.045/hr) and **per-GB processed**
(~$0.045/GB). On AKS clusters defaulted to NAT Gateway outbound:

- A 24/7 NAT Gateway costs ~$33/month idle, before any traffic
- 1 TB of outbound through NAT Gateway adds ~$45 on top
- For low-egress AKS clusters, removing the NAT Gateway and using **outbound rules
  on a Standard Load Balancer** can save 60-80% of the outbound networking line

Audit AKS clusters for NAT Gateway necessity:

```kusto
resources
| where type == "microsoft.containerservice/managedclusters"
| extend outboundType = tostring(properties.networkProfile.outboundType)
| project name, resourceGroup, outboundType, location
```

`outboundType` of `managedNATGateway` or `userAssignedNATGateway` is the trigger
for review. For clusters with low egress (most internal-facing), `loadBalancer`
outbound is materially cheaper.

### Private Endpoint vs Service Endpoint trade-off

| Feature | Private Endpoint | Service Endpoint |
|---|---|---|
| Cost | ~$0.01/hour per endpoint + per-GB processed | Free |
| Network model | Private IP in your VNet | VNet allows access to public endpoint via Microsoft backbone |
| Cross-region | Supported | Same region only |
| Cross-tenant | Supported | Not supported |
| Security posture | Stronger - resource is reachable only from VNet | Weaker - public endpoint still exposed |

Per-endpoint cost is small individually but compounds. On a fleet of 200 storage
accounts with Private Endpoint enabled, the monthly bill is non-trivial (~$1,400
plus per-GB processing). Use Private Endpoint where compliance requires it; use
Service Endpoint for internal storage accounts where same-region access is the
only requirement.

### Front Door vs Application Gateway vs Traffic Manager

| Product | Layer | Scope | Primary cost driver |
|---|---|---|---|
| Front Door | L7 (HTTP/HTTPS) | Global | Per request + per-GB egress + WAF rules if Premium |
| Application Gateway | L7 (HTTP/HTTPS) | Regional | Hourly tier + Capacity Units (CU) - autoscaling sizes drive cost |
| Traffic Manager | DNS-based | Global | Per million DNS queries + per endpoint monitor |

**Decision rule:**
- Need global anycast + caching + WAF → Front Door (Standard or Premium)
- Need regional L7 with WAF + path-based routing → Application Gateway
- Need DNS-level failover only, no traffic inspection → Traffic Manager (cheapest)

Replacing an Application Gateway with Front Door for a small workload usually
costs more, not less - Front Door's per-request pricing wins at scale, not at
small-footprint regional services.

---

## FOCUS exports and Retail Prices API - the data-side gaps

The Cost Management foundation section covers FOCUS exports as a setup step. This
section covers the practical patterns and known limitations when building custom
cost analytics on top.

### FOCUS export practical patterns (1.0 GA, 1.2 preview)

FOCUS 1.0 went GA in Azure Cost Management in June 2024. As of April 2026, Cost
Management additionally supports a **FOCUS 1.2 preview** export with documented
conformance gaps (see Cost Management foundation section above). FinOps Hubs /
Toolkit v12 ingest the 1.2 preview into 1.2-aligned analytics. The schema fields
below cover the 1.0 GA columns most useful for FinOps work - additional 1.2 columns
become available once the preview export is enabled.

**Multi-cloud normalisation context:** With FOCUS 1.2 implementations now available
across AWS, Azure, and emerging providers (Nebius, Vercel, Grafana Cloud, Redis,
Databricks), organisations can build unified cost reporting across their entire
cloud estate. Azure's 1.2 preview aligns with this broader ecosystem trend.

| Field | Use |
|---|---|
| `BilledCost` | What appears on the invoice - use for billing reconciliation |
| `EffectiveCost` | Amortised cost including commitment amortisation - use for showback |
| `ListCost` | Pre-discount list price - use for negotiated discount validation |
| `ContractedCost` | Cost at contracted rate before commitment discounts - use for portfolio analysis |
| `ResourceId` | Full Azure ARM resource ID - join key to Resource Graph |
| `Tags` | Resource and inherited tags - allocation key |
| `Region` | Azure region - drives carbon and latency analysis |
| `ServiceCategory` | FOCUS service taxonomy - normalises across clouds |
| `CommitmentDiscountId` | Reservation or Savings Plan ID - join to commitment portfolio |

**MCA join pattern:** under Microsoft Customer Agreement, each Billing Profile
produces its own FOCUS export. Central FinOps must **union the exports across
profiles** before analysis. For multi-profile customers (most large enterprises),
this is a daily ETL step, not a one-time configuration. Document the union logic
in the FinOps platform runbook.

**Source:** https://learn.microsoft.com/en-us/azure/cost-management-billing/dataset-schema/cost-usage-details-focus

### Retail Prices API - note for custom Power BI / third-party tooling only

**Native Azure Cost Management, Advisor, and FOCUS exports run on Microsoft's
internal pricing service** and are not affected by the public Retail Prices API
rate limit. This subsection is only relevant when a custom Power BI dashboard,
Python script, or third-party tool calls the public pricing endpoint directly.

**Endpoint:** `https://prices.azure.com/api/retail/prices`

- Pagination via `NextPageLink`, 100 items per page
- Practical rate limit: ~300 requests per minute per source IP (undocumented by
  Microsoft)
- Caching strongly recommended - prices change weekly at most for most SKUs

**Failure modes that look like success:**

- Empty pages mid-chain - the response returns 200 with an empty `Items` array
  but a populated `NextPageLink`. Naive scripts treat empty as end-of-data and
  stop.
- Truncated `NextPageLink` - silently dropped from the response on a transient
  error. The script reports "done" with incomplete data.
- Partial pagination terminating without error - the `NextPageLink` chain ends
  before all matching pages are returned.

A naive Power BI refresh or Python pull will report success while having pulled
40-60% of the actual price catalogue. The result is wrong unit-economics
calculations downstream.

**Defensive pattern:**

1. Use `$filter` to narrow the query (by `serviceFamily`, `armRegionName`,
   `priceType`) - smaller queries are more reliable.
2. Self-throttle to ~200 RPM (well below the practical ceiling).
3. Validate pagination chain completeness - track expected total via the
   `Count` field on the first page if available, or compare to the previous
   refresh's row count.
4. Cache for at least 24 hours.
5. For full-catalogue enumeration, use the **bulk Pricing CSV exports** from the
   Azure Pricing Calculator rather than the API.

Frame this as a known limitation of what can be built on the public API, not a
recurring engagement issue. Native Cost Management surfaces are unaffected.

---

## Compute rightsizing fundamentals

The earlier "Compute rightsizing" section focuses on Advisor mechanics and the band
Advisor's logic skips. This section covers the foundational topics needed before any
of that applies: VM cost model, SKU naming convention, family selection, automated
start/stop, generation upgrades, and region placement.

### VM cost model

**Cost drivers:** Compute (SKU, hours, licensing), storage (managed disks),
networking (egress), indirect costs (monitoring, backups).

**Critical insight:** When stopped (deallocated), you still pay for storage and
public IPs. You save compute and license costs only.

### VM SKU naming convention

Understanding Azure VM names is essential for rightsizing decisions:

```
D 4 a s _v5
| | | |   |
| | | |   +-- Generation (newer = better price/performance)
| | | +------ Premium storage support
| | +-------- AMD CPU (cheaper than Intel)
| +---------- vCPU count
+------------ Family (D=general, B=burstable, E=memory, F=compute, N=GPU)
```

**Other modifiers:** `p` = ARM CPU (cheapest, requires workload compatibility),
`m` = more memory, `d` = local temp SSD.

### VM family selection

| Family | Memory per vCPU | Best for | Cost position |
|---|---|---|---|
| **B-series** | Varies | Spiky, mostly-idle workloads (dev/test, small web) | 15-55% cheaper than D-series |
| **D-series** | 4 GB | General purpose | Baseline |
| **E-series** | 8 GB | Memory-optimized (databases, caches) | Premium over D |
| **F-series** | 2 GB | Compute-optimized (batch, gaming) | Cheaper per vCPU |

**AMD-based variants** (Das, Eas): Better price/performance vs Intel equivalents.
**ARM-based variants** (Dps, Eps): Cheapest option for compatible workloads (web,
containers).

### Automated start/stop schedules

The highest-impact quick win for non-production environments.

**Savings math:** Office hours (10h x 5 days/week = 217h/month vs 730h/month) =
up to 70% cost reduction on non-production compute.

**Implementation options:**
- Azure DevTest Labs auto-shutdown (simplest, shutdown only)
- **Start/Stop VMs v2** (Microsoft recommended, supports both start and stop)
- Azure Automation Runbooks (most customisable)
- Infrastructure as Code (Terraform `azurerm_dev_test_schedule`, Bicep)

**Tagging strategy for automation:** Use `startTime` and `stopTime` tags on VMs.
Automation reads tags to determine schedule. This allows per-VM scheduling without
modifying the automation logic.

### VM generation upgrades

Newer VM generations improve price/performance ratio. Examples:
- D2s_v3 -> D2s_v5: sometimes cheaper AND better performance
- E4_v3 -> E4as_v5: AMD variant gives further savings

Review VM generations quarterly and upgrade where possible.

### Region placement for cost

Azure pricing varies significantly by region. India is cheaper, Brazil is expensive.
Dev/test workloads can often use cheaper regions without user-facing impact.
Use the Retail Prices API to compare regions programmatically.

---

## Database commitment decision tree and fundamentals

### Database commitment decision tree

Azure offers two commitment instruments for database services, plus operational
optimisations that should be applied before any commitment purchase.

**Pre-commitment optimisation (do these first):**
1. Enable Azure Hybrid Benefit on all eligible SQL Database and SQL MI instances
2. Switch dev/test databases to SQL Serverless (auto-pause) - saves 70-90% on idle DBs
3. Stop PostgreSQL/MySQL Flexible Servers outside business hours
4. Consolidate small databases into Elastic Pools (20-40% savings)
5. Review DTU vs vCore: migrate to vCore if AHB-eligible for licence savings
6. Right-size overprovisioned compute and storage tiers

**Decision tree:**

```
Is the database workload stable and predictable (90+ days)?
+-- NO -> Stay on PAYG or use Serverless (auto-pause for intermittent use).
|         Re-evaluate quarterly.
|
\-- YES -> Has the database been right-sized and optimised? (steps 1-6 above)
    +-- NO -> Optimise first, commit second. Do not lock in waste.
    |
    \-- YES -> What is the database estate profile?
        |
        +-- Single service, single region, stable configuration
        |   -> Azure Reservation (deeper discount than Savings Plan)
        |     - Available for: SQL Database, Cosmos DB, PostgreSQL,
        |       MySQL, MariaDB, SQL MI
        |     - Exchangeable for different SKU if workload changes
        |     - Pro-rated refund available (up to $50K/12 months)
        |
        +-- Multiple database services or regions
        |   -> Savings Plan for Databases (up to 35%, March 2026)
        |     - Covers: SQL Database, PostgreSQL, MySQL, Cosmos DB,
        |       SQL MI, MariaDB
        |     - Applies savings across services and regions automatically
        |     - Cannot be exchanged or refunded once purchased
        |     - CAUTION: SQL Server on Azure VMs and Azure Arc consume
        |       the commitment at PAYG rates (no discount) - factor
        |       this into sizing the hourly commitment
        |
        +-- Mix of stable and evolving workloads
        |   -> Layer both: Savings Plan for Databases as broad baseline,
        |     then add Reservations for the most stable, high-spend
        |     database instances to capture deeper discounts
        |
        \-- Cosmos DB (special case)
            -> Cosmos DB Reserved Capacity available separately
              - 1yr or 3yr terms, significant discounts on RU/s
              - Requires predictable throughput baseline
              - For variable throughput: use autoscale (no commitment)
              - Evaluate serverless for low/intermittent usage first
```

**Database commitment diagnostic questions:**
- What percentage of your database spend is PAYG vs committed?
- Are Azure Hybrid Benefit licences applied to all eligible SQL instances?
- Are dev/test databases on Serverless (auto-pause) or still running 24/7?
- Do you have SQL Server on Azure VMs that would consume a Database Savings Plan
  at PAYG rates? If so, how much of the plan's hourly commitment would they absorb?
- Are overprovisioned tiers (Business Critical on non-prod, RA-GRS backup storage
  on non-critical DBs) inflating the baseline you would commit to?

### Savings Plan for Databases (announced March 2026)

A spend-based commitment discount for eligible database services. Customers commit
to a fixed hourly spend (e.g. $5/hr) for one year and receive discounted prices -
up to 35% vs PAYG on select services. The plan applies savings automatically each
hour, prioritising the usage that delivers the greatest discount first, across
services and regions.

**Eligible services:** Azure SQL Database, Azure Database for PostgreSQL, Azure
Database for MySQL, Azure Cosmos DB, Azure SQL Managed Instance, Azure Database
for MariaDB.

**Important caveat:** SQL Server on Azure VMs and SQL Server enabled by Azure Arc
also consume the plan's hourly commitment, but at normal PAYG rates (no discount).
If these workloads are in the mix, they reduce the effective savings from the plan.
Factor this into sizing the hourly commitment.

**Scoping:** Subscription, resource group, management group, or entire billing
account.

**Purchase options:** Monthly or upfront payment, optional auto-renewal. Personalised
recommendations available in Azure Advisor and the Azure portal.

**When to use vs Reservations:**
- Choose Savings Plan for Databases when the database estate spans multiple services
  or regions, or when architecture changes (migrations, service swaps) are expected
  during the commitment period.
- Choose Reservations when a single database service runs stably in a fixed
  configuration and the deeper RI discount outweighs the flexibility benefit.
- Layer both: use the Savings Plan for broad baseline coverage, then add RIs for the
  most stable, high-spend database workloads.

**Pricing note (March 2026):** The "up to 35%" figure is based on Azure SQL Database
Serverless over a 1-year term. Actual discounts vary by service and usage pattern.
Azure Pricing Calculator and pricing pages had not yet been updated at time of
announcement - verify current rates before purchasing.

### DTU vs vCore pricing

- **DTU:** Predictable pricing, good for small/uncertain workloads
- **vCore:** Better for migrations (license reuse via AHB), more control over
  compute/storage
- **Serverless (vCore):** Higher hourly rate but auto-pause makes it cheaper for
  intermittent use

### Database architecture principles

- **Only keep active working set in relational DB.** Move cold data to Blob (Cool /
  Archive tier).
- **Avoid "one instance per application" by default.** Consolidate databases to
  increase utilization.
- **Active data in Premium, cold data in Blob.** Avoid storing backups on premium
  disks.
- **High availability has a cost.** Balance resilience requirements against budget
  per environment.

### PostgreSQL and MySQL Flexible Server optimisation

**Compute rightsizing patterns:**
- Use B-series (burstable) for dev/test with <30% average CPU
- Monitor `cpu_percent` and `memory_percent` metrics over 30 days
- Size for P75 utilisation, not peak - autoscaling handles spikes
- Enable read replicas only when query offload justifies the cost

**Storage optimisation:**
- **Auto-grow**: Enable with 20% increment to prevent manual interventions
- **IOPS scaling**: Use default provisioned IOPS unless workload requires more
- **Backup retention**: 7 days default; only extend for compliance requirements
- **Storage type**: Premium SSD only for production; Standard SSD for dev/test

**High availability considerations:**
- **Zone-redundant HA**: Doubles compute cost - use only for critical production
- **Same-zone HA**: Lower cost option when RPO/RTO allows
- **Read replicas**: More cost-effective than HA for read scaling
- **Geo-redundant backup**: Only enable where DR requirements mandate

### Cosmos DB cost optimisation patterns

**Throughput optimisation:**
- **Autoscale vs Manual**: Use autoscale for >3:1 peak-to-trough ratio
- **Shared throughput**: Pool RU/s across containers with similar access patterns
- **Serverless**: Consider for <1M requests/month or sporadic workloads
- **Time-based scaling**: Use Azure Functions to scale RU/s by schedule

**Data modelling for cost:**
- **Partition key design**: Poor partitioning forces over-provisioning
- **Document size**: Smaller documents = lower RU consumption
- **Indexing policy**: Exclude unused paths to reduce write RUs
- **TTL (Time-to-live)**: Auto-expire old data to control storage growth

**Multi-region considerations:**
- Each additional region multiplies RU/s cost
- Use regional failover (manual) instead of multi-master where possible
- Place read regions close to users, write region close to data sources
- Monitor cross-region replication lag to validate region necessity

---

## Commitment portfolio - phased purchasing

### Commitment portfolio liquidity

Commitment liquidity - the ability to reshape, rebalance, or exit your commitment
portfolio without wasting money - is as important as discount depth. Azure offers
more built-in liquidity mechanisms than AWS, but each has limits.

**Azure liquidity mechanisms:**

| Mechanism | How it works | Applies to | Limits |
|---|---|---|---|
| **Reservation exchange** | Swap a Reservation for a different SKU within the same product family | Reservations only | Same product family. **No fee, no annual cap. Exchanges do NOT count against the $50K refund cap.** |
| **Reservation refund (cancellation)** | Cancel a Reservation and receive a pro-rated refund | Reservations only | $50,000 rolling 12-month cap **per Billing Profile (MCA) or enrollment (EA)**. The cap restores day-by-day; 365 days after a refund, the original $50K is fully reinstated. |
| **Reservation instance size flexibility (ISF)** | A Reservation on one VM size covers other sizes in the same family at a normalised ratio | VM Reservations | Same VM family and region only |
| **Reservation trade-in to Savings Plan** | Convert RI to Savings Plan credit | Reservations only | No fee, no time limit |
| **Staggered expiry** | Purchase commitments in phased blocks so only a fraction expires each quarter | All instruments (Reservations, Savings Plans) | Requires purchasing discipline |

This table is the same set of mechanics as the "Reservation and Savings Plan
liquidity mechanics" table earlier in this file - kept here in the commitment-
portfolio context for engagement readers who land in this section first.

**Key insight:** Reservations are more liquid than Savings Plans on Azure. This is
the opposite of the common assumption. Savings Plans offer usage flexibility (any
family, any region) but zero financial liquidity (no exchange, no refund, no
cancellation). Reservations lock to a specific SKU but allow exchanges (no fee,
no cap), refunds (within the $50K cap), trade-in to Savings Plan (no fee, no
limit), and instance size flexibility within the family. When choosing between
the two, factor liquidity into the decision - not just discount depth and coverage
breadth.

**The $50,000 refund cap (applies to refunds only, not exchanges).** Microsoft
imposes a rolling 12-month cap of $50,000 on Reservation refunds per Billing
Profile (MCA) or enrollment (EA). **Exchanges within the same product family do
not count against this cap** - confirmed in current Microsoft docs. For
organisations with large Reservation portfolios, the refund cap can still be a
binding constraint if you need to cancel rather than exchange. The cap restores
day-by-day; spread cancellations across the 12-month window where possible.

Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/exchange-and-refund-azure-reservations

### Phased purchasing

Never buy the full commitment in a single transaction. Purchase in blocks to create
a portfolio with staggered expiry dates. The cadence and block size should match
your consumption profile - not a fixed rule.

**Why phased purchasing matters on Azure:**
- **Reduces lock-in risk:** if workloads migrate or are re-architected, only the
  current block is at risk
- **Creates natural re-evaluation points:** each purchase cycle forces a review of
  utilisation, Advisor recommendations, and architecture direction
- **Preserves refund/exchange headroom:** spreading purchases means smaller
  individual Reservations, making it easier to stay within the $50K refund cap if
  changes are needed
- **Aligns with MACC cadence:** phased purchasing can be timed to support MACC
  burndown trajectory, avoiding end-of-period scrambles
- **Captures pricing improvements:** newer VM generations (v5, v6) and architecture
  shifts (ARM-based Dps/Eps families) can be reflected in subsequent blocks

**Cadence and block size by consumption profile:**

The purchasing cadence should follow consumption volatility. The more variable the
workload, the shorter the purchase cycle and the smaller each block. Your commitment
refresh rate should be faster than your workload change rate.

| Consumption profile | Examples | Cadence | Block size | Rationale |
|---|---|---|---|---|
| Steady, predictable | Enterprise ERP, internal tools, back-office systems | Quarterly | 20-25% | Workloads barely move quarter to quarter. Larger blocks capture deeper coverage faster. |
| Moderate growth or gradual shifts | SaaS platforms, B2B applications, steady API services | Monthly to bi-monthly | 10-15% | Growth adds new capacity regularly. Smaller blocks incorporate new workloads without over-committing to the old baseline. |
| Seasonal or event-driven | Retail (holiday peaks), media (live events), gaming (launches) | Monthly to weekly | 5-10% | Demand swings mean the baseline shifts frequently. Small blocks commit only to the proven floor; peaks stay on PAYG/Spot. |
| Highly volatile or early-stage | Startups, experimental workloads, pre-product-market-fit | Weekly or do not commit | 5% or less | If you cannot predict next month, do not lock in for a year. Stay on PAYG with Spot until patterns stabilise. |

**The cadence can shift over time for the same company.** A retail company might
buy quarterly in Q1-Q3 (steady baseline) and switch to weekly in Q4 (holiday ramp)
to avoid committing to peak capacity that evaporates in January. A SaaS company
might start with monthly cadence during a growth phase and shift to quarterly once
the growth rate stabilises.

**Block size and cadence are inversely related:** higher frequency = smaller blocks.
This keeps the total portfolio size similar but distributes the risk across more,
smaller decisions.

**Azure-specific consideration:** on Azure, Reservations can be exchanged mid-term,
so organisations with moderate-frequency cadence (monthly/bi-monthly) can favour
Reservations over Savings Plans - the exchange mechanism provides an additional
liquidity layer on top of the staggered expiry approach. Organisations buying weekly
may prefer Savings Plans to avoid the administrative overhead of frequent
Reservation management.

**Phased purchasing framework (quarterly example for steady consumption):**

```
Quarter 1: Buy 20-25% of target commitment (the floor you are certain about)
  -> Monitor utilisation for 30 days via Azure Advisor and Cost Management
  -> If utilisation >80%: proceed to next block
  -> If utilisation <80%: investigate before buying more

Quarter 2: Buy next 15-20% block
  -> Reassess workload stability and architecture plans
  -> Review Reservation exchange opportunities on earlier blocks if workloads shifted

Quarter 3: Buy next 15-20% block
  -> By now 50-65% of target is covered
  -> Remaining gap is intentional PAYG buffer

Quarter 4: Evaluate whether to buy more or hold
  -> Factor MACC burndown position into the decision
  -> Early blocks from previous year start approaching renewal
```

**Portfolio view - staggered expiry example (1-year terms, quarterly cadence):**

| Block | Purchased | Expires | % of total | Instrument | Rationale |
|---|---|---|---|---|---|
| Block 1 | Jan 2026 | Jan 2027 | 25% | Compute Savings Plan | Broad baseline across VMs + App Service |
| Block 2 | Apr 2026 | Apr 2027 | 20% | VM Reservations (D-series) | Stable production VMs, deepest discount |
| Block 3 | Jul 2026 | Jul 2027 | 15% | VM Reservations (E-series) | Memory-optimised database VMs |
| Block 4 | Oct 2026 | Oct 2027 | 10% | DB Savings Plan | Database baseline across SQL + PostgreSQL |
| PAYG | - | - | 30% | None | Buffer for variable / new workloads |

**3-year term phasing:** For 3-year commitments (deeper discounts), purchase in
smaller blocks (10-15%) at 6-month intervals. The longer the term, the smaller
each block should be.

**Portfolio management cadence:**
- **At each purchase cycle** (weekly/monthly/quarterly depending on profile): review
  Reservation and Savings Plan utilisation in Azure Cost Management. Flag any
  commitment below 80%. Decide whether to buy the next block, adjust the mix, or
  pause. Review Reservation exchange opportunities on earlier blocks if workloads
  have shifted.
- **At each expiry:** do not auto-renew blindly. Re-evaluate the workload: has it
  grown, shrunk, migrated, or been decommissioned? Renew only what is still
  justified. Azure Advisor provides renewal recommendations - use them as input,
  not as the decision.
- **Quarterly (regardless of purchase cadence):** strategic review of commitment
  coverage ratio, instrument mix, MACC burndown trajectory, and upcoming expiries.
- **Annually:** review the overall commitment strategy against the organisation's
  Azure roadmap. Adjust coverage ratio, cadence, instrument mix, and MACC alignment.

**Commitment portfolio diagnostic questions:**
- What percentage of your commitment portfolio expires in any single quarter? If
  more than 30%, the portfolio is insufficiently diversified.
- Are you buying commitments in phased blocks with staggered expiry, or purchasing
  the full amount in a single transaction?
- How much of your $50,000 Reservation refund/exchange cap have you used in the
  last 12 months? If you are close to the cap, you have less room to reshape the
  portfolio.
- Are Savings Plans covering workloads that are stable enough for Reservations
  (leaving ~7% discount on the table)?
- Is MACC burndown tracking integrated into the same review cadence as commitment
  purchasing? If not, optimisation gains may create a MACC shortfall risk.
- Are engineering teams planning VM family migrations (e.g. to ARM-based Dps/Eps)
  that would strand existing Reservations? If so, favour Savings Plans for those
  workloads or plan Reservation exchanges in advance.

**Key metrics:**
- **Reservation/SP Utilisation:** Target >80%. Below this, the commitment is
  oversized.
- **Reservation/SP Coverage:** Target 70% (Walk maturity), 80%+ (Run maturity).
- **Effective Savings Rate:** actual savings / theoretical maximum. Measures how
  well commitments are matched to real usage.
- **Break-even period:** should be <9 months for 1-year terms, <15 months for 3-year.
- **Commitment waste:** hours where committed capacity had no matching usage.
- **Exchange headroom:** remaining $ available under the $50K/12-month refund cap.

**Pre-purchase checklist:**
- [ ] Azure Hybrid Benefit enabled on all eligible VMs and SQL instances
- [ ] Workload has run stably for 90+ days
- [ ] Workload has been right-sized (do not commit to waste)
- [ ] No planned architecture changes during the commitment term
- [ ] All resources are tagged and attributable to an owner
- [ ] Existing commitment utilisation is >80% before purchasing more
- [ ] MACC burndown trajectory reviewed - commitment purchase aligns with drawdown
- [ ] Finance has approved the capital outlay (for Upfront payments)

---

## Cost allocation on Azure

### Billing scope hierarchy

The hierarchy is different on EA vs MCA. Get this right at engagement kickoff -
the wrong mental model leads to wrong recommendations on chargeback and reservations.

**EA hierarchy:** Enrollment -> Department -> Account -> Subscription, with the
Management Group / Resource Group layers sitting underneath subscriptions for
governance.

**MCA hierarchy (four billing levels):**

| Level | What it is | What it aggregates | Key role |
|---|---|---|---|
| **Billing Account** | Root container, created at signup. One per MCA signature. | Everything below. | Billing Account Owner - full visibility and control. |
| **Billing Profile** | The unit that **generates a single monthly invoice**. One invoice per Billing Profile. Payment method attached here. Pricing is tied to the Billing Profile (not enrollment-wide as under EA - relevant for multi-entity groups where negotiated discounts may not propagate the way the client assumes). | All Invoice Sections below it. | Billing Profile Owner - manage invoices, create budgets, purchase reservations and savings plans. |
| **Invoice Section** | A grouping on the invoice (department, team, project). Shows as a line on the invoice, not a separate invoice. | Subscriptions assigned to it. | Invoice Section Owner - create subscriptions in the section, manage them. |
| **Subscription** | Where resources are deployed and billed. Resource Groups and Resources sit underneath. | Resources. | Subscription Owner / Contributor / Reader (standard Azure RBAC). |

**Three sentences that anchor the hierarchy:**
1. **Invoices happen at the Billing Profile level.** That is why multi-entity groups
   often have one Billing Profile per legal entity - because invoices have to match
   legal contracts.
2. **Invoice Sections are chargeback groupings inside one invoice.** They do not mean
   separate invoices.
3. **Reservations sit on the Billing Profile.** They do not belong to an Invoice
   Section - this has direct consequences for chargeback (see "MCA reservation
   ownership and the chargeback trap" below).

**MCA visibility gap to plan for at kickoff.** Under EA, a Subscription Owner with
enrollment access can create exports and budgets at higher scopes. **Under MCA, a
Subscription Owner cannot create exports or budgets at Billing Profile or Invoice
Section level** - the user needs at least **Billing Profile Reader** or **Billing
Profile Contributor**. Sort out these roles in the engagement kickoff before you
need them, otherwise the day-1 export setup will block on a permissions ticket.

Sources: [MCA setup](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/mca-setup-account), [Cost Management scopes](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/understand-work-scopes), [Billing roles for MCA](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/understand-mca-roles)

**Allocation strategy (applies to both EA and MCA):**
- Use Management Groups for policy inheritance and org-level cost views
- Use Subscriptions as the primary cost allocation boundary (equivalent to AWS
  accounts)
- Use Resource Groups to group resources by workload or team within a subscription
- Use Tags for cross-cutting dimensions (Environment, CostCenter, Project)

### MCA reservation ownership and the chargeback trap

Under MCA, an Azure Reservation is **owned at the Billing Profile level**. Default
discount scope is **Shared**, which means the reservation benefit flows to any
eligible resource across all subscriptions under that Billing Profile - regardless
of which Invoice Section the subscription sits in.

**Reservations cannot be moved between Invoice Sections.** This is a hard limit, not
a configuration flag.

**Consequence for multi-entity engagements.** If a customer has three business units
mapped to three Invoice Sections and asks "can we attribute each BU's reservation
cost to its own invoice section?" - the answer is **no, not natively**. You cannot
do it at the billing layer. You build an allocation layer on top of Cost Management
exports (allocation rules, or BI-side logic on the FOCUS export).

**Anti-pattern to avoid.** Do not promise "we will put BU-A's reservations on BU-A's
invoice line." That is not how MCA works. Promise: "we will show BU-A its share of
reservation cost in a Cost Management view and feed that to your chargeback system."

Source: [Organize your invoice based on your needs](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/mca-section-invoice)

### Azure-specific tagging considerations

**Key difference from AWS:** Azure supports tag inheritance policies through Azure
Policy. Resources can inherit tags from their resource group or subscription
automatically. This simplifies governance for teams that organise resources by
resource group.

**Tag enforcement policies (Azure Policy):**
- `deny` effect: Block resource creation without mandatory tags
- `audit` effect: Flag non-compliant resources without blocking
- `modify` effect: Auto-apply tags from resource group to child resources
- Tag inheritance from subscription level and resource group level

**Tags for automation:** Beyond cost allocation, use tags to drive automation:
- `startTime` / `stopTime` for VM scheduling
- `Environment` (dev/pre/pro) for policy differentiation
- `Owner` for accountability and notification routing

**Resource Group naming convention (recommended):**
Pattern: `rg-{bu3chars}-{name}-{env}` (e.g., `rg-fin-webapp-dev`)

---

## Azure governance tools - policy patterns and budgets

The earlier "Governance - tagging and Azure Policy as a FinOps lever" section
covers tag governance specifically. This section covers Azure Policy patterns for
FinOps more broadly, plus Azure Budgets and environment-tier definitions.

### Azure Policy for FinOps - common policy library

Azure Policy enforces organisational standards across subscriptions. Key FinOps
policies:

| Policy | Effect | Purpose |
|---|---|---|
| Require mandatory tags | `deny` | Block untagged resource creation |
| Audit tag compliance | `audit` | Visibility into tagging gaps |
| Inherit tags from resource group | `modify` | Automatic tag propagation |
| Allowed VM SKUs | `deny` | Prevent expensive GPU/M-series in dev |
| Allowed disk SKUs | `deny` | Block UltraSSD/PremiumV2 in non-prod |
| Allowed storage SKUs | `deny` | Restrict to Standard_LRS/ZRS |
| Deny expensive SQL tiers | `deny` | Only allow Basic/Standard/GeneralPurpose |
| Deny public IPs | `deny` | Use Bastion/VPN instead (cost + security) |
| Restrict regions | `deny` | Enforce approved regions |
| Enforce VM shutdown schedule | `audit` | Flag VMs without auto-shutdown tags |

**Assign policies at Management Group scope** for org-wide enforcement. Use
remediation tasks to apply `modify` policies to existing resources retroactively.

### Azure Budgets and Alerts

Configure at minimum:
- Subscription-level monthly budget with 80% and 100% actual cost alerts
- Forecasted cost alert at 100% (triggers before the budget is exceeded)
- Resource group level budgets for high-spend workloads

**Alert recipients:** Both the FinOps practitioner and the engineering team lead.
FinOps-only alerts create a bottleneck; engineering-only alerts lack financial
context.

Use Action Groups for automated responses (Logic Apps, Azure Functions, webhooks).

### Environment definitions

Formalise environment tiers with different governance levels:

| Environment | Allowed SKUs | Schedule | Commitment eligible | Backup |
|---|---|---|---|---|
| Sandbox | B-series only | Auto-delete after 7 days | No | No |
| Dev | B-series, small D/E | Business hours only | No | No |
| Pre-Production | Match prod families, smaller | Business hours only | No | Optional |
| Production | Any approved | 24/7 | Yes (after 90-day stability) | Yes |

**Principle: Shut down waste before committing to anything.** Reduce baseline cost
first, then layer commitments (RIs, Savings Plans) on top of the optimised baseline.

---

## Azure-specific quick wins

Ordered by priority: highest savings + lowest risk first.

| # | Action | Typical savings | Risk | Effort |
|---|---|---|---|---|
| 1 | Enable Azure Hybrid Benefit on eligible VMs | Up to 40-55% on license cost | None | Very Low |
| 2 | Schedule dev/test VM auto-shutdown (business hours) | 60-70% of VM cost | Low | Low |
| 3 | Delete unattached managed disks | 100% of disk cost | None | Low |
| 4 | Remove unassociated public IP addresses | 100% of IP cost | None | Low |
| 5 | Shut down idle VMs (CPU <5% for 14+ days) | 100% of VM compute cost | Low | Low |
| 6 | Move cold blob storage to Cool or Archive tier | 50-90% storage cost | Low | Low |
| 7 | Set Log Analytics daily cap + optimise retention | 30-60% monitoring cost | Low | Low |
| 8 | Use ephemeral OS disks for stateless workloads | 100% of OS disk cost | Low | Low |
| 9 | Auto-pause dev SQL databases (Serverless tier) | 70-90% during idle | Low | Low |
| 10 | Use B-series for dev/test web servers | 15-55% vs D-series | Low | Medium |
| 11 | Right-size over-provisioned VMs (Azure Advisor) | 20-50% VM cost | Medium | Medium |
| 12 | Convert to Reserved Instances for stable workloads | 30-72% compute cost | Medium | Medium |
| 13 | Archive backups >90 days in Recovery Services Vault | 95% on old backups | Low | Medium |
| 14 | Filter Container Insights to error/warning only | 40-60% Log Analytics | Low | Medium |

---

## Case study: 2-tier web app optimisation

**Baseline:** 12 VMs across prod/pre-prod/dev (D4_v5 Windows web + E8_v5 Linux DB),
all running 24/7. Monthly cost: ~5,071 EUR. Non-prod CPU utilization: 3-5%.

**Optimisation waterfall (compute only):**

```
Current compute       3,747 EUR/mo
 - AHB               -  675  -->  3,073  (enable today, no downtime)
 - Start/Stop        -1,440  -->  1,633  (non-prod business hours only)
 - Rightsize Web     -   97  -->  1,536  (D4_v5 -> B2ms for non-prod)
 - Rightsize DB      -  331  -->  1,205  (E8_v5 -> E2_v5 for non-prod)
                               ------
Optimised compute     1,205 EUR/mo  (-67.9% compute reduction)
Annual savings       30,515 EUR/year
```

**Implementation order matters:**
1. **Week 1:** AHB - zero risk, zero downtime, immediate savings
2. **Week 1-2:** Start/Stop automation - low risk, high impact
3. **Week 3:** Rightsize non-prod web tier (stateless, easy rollback)
4. **Week 4-6:** Rightsize non-prod DB tier (stateful, validate carefully per VM)

**Key lesson:** 44% of Windows VM cost was license premium the company was double-
paying. AHB alone saved 675 EUR/month with a single CLI command per VM.

---

## EA-to-MCA transition - FinOps impact

Microsoft is actively migrating Enterprise Agreement (EA) customers to the Microsoft
Customer Agreement (MCA). While the transition is primarily a commercial
restructuring, it has significant FinOps operational consequences that teams must
prepare for.

### The three MCA flavours - know which one before kickoff

MCA is one programme with three distinct purchase paths. They are easy to confuse
and the answer changes who owns the billing relationship.

| Flavour | Purchase path | Who signs what | Where the FinOps team gets data |
|---|---|---|---|
| **MCA Direct** | Customer signs digitally, buys Azure directly from Microsoft via the portal. | Customer signs MCA with Microsoft. | Direct Microsoft billing portal and Cost Management. |
| **MCA Partner** (formerly **CSP**) | Customer buys through a Microsoft partner. | Partner signs MCA with Microsoft; customer signs with the partner. | Partner's billing tools first, Cost Management for resource-level data. **CSP is no longer a separate programme** - it is the indirect channel under MCA. People still say "CSP" out of habit. |
| **MCA Enterprise (MCA-E)** | Enterprise sales motion, direct with Microsoft, negotiated terms. | Customer signs MCA-E directly with Microsoft. | Direct Microsoft billing, plus negotiated rate sheet visibility. This is the path most EAs migrate to. |

**Day 1 question to ask the customer:** "Did you sign the Azure agreement directly
with Microsoft, or through a partner?" If partner, chargeback questions route through
the partner's tooling first. If direct, the standard Cost Management surfaces apply.

### What changes under MCA

| Dimension | EA | MCA |
|---|---|---|
| Billing hierarchy | Single enrollment, departments, accounts | Billing account, billing profiles, invoice sections |
| Invoice structure | Single consolidated invoice | Multiple invoices (one per billing profile) |
| Commitment flexibility | Annual upfront or monthly payments | Pay-as-you-go default, optional commitments |
| Cost Management data | Full historical visibility | Pre-migration data may not carry over |
| Power BI connector | Legacy EA connector | Deprecated - must use FOCUS exports + ADLS |
| FinOps Toolkit support | Direct EA integration | Requires migration to storage-based exports or FinOps Hubs |

### FinOps risks during transition

**Historical data visibility loss.** Cost Management may not display pre-migration
spending after the switch. Export historical data before migration begins. Without
this, year-over-year comparisons and trend analysis break.

**Power BI reporting disruption.** The legacy EA Power BI connector is deprecated
under MCA. Teams must migrate to FOCUS-aligned exports to Azure Data Lake Storage
(ADLS) and rebuild Power BI reports against the new schema. Plan for 2-4 weeks of
reporting rework.

**Savings plan and reservation visibility gaps.** Commitment discount usage
reporting changes under MCA billing scopes. Verify that existing reservation and
savings plan utilisation dashboards still function after migration. Re-scope alerts
and reports to the new billing profile hierarchy.

**Invoice reconciliation complexity.** Multiple billing profiles generate separate
invoices. Teams accustomed to a single EA invoice need new reconciliation
processes. Map cost centres and departments to MCA invoice sections before
migration.

### Migration checklist for FinOps teams

- [ ] Export 12-24 months of historical cost data from Cost Management before
  migration
- [ ] Document current EA billing hierarchy and map to planned MCA structure
- [ ] Inventory all Power BI reports using the legacy EA connector
- [ ] Plan migration to FOCUS exports + ADLS (or FinOps Hubs) for reporting
- [ ] Verify reservation and savings plan visibility in the new billing scope
- [ ] Update cost allocation rules and management group assignments
- [ ] Test showback/chargeback reports against the new invoice structure
- [ ] Update Azure Policy assignments if scoped to EA enrollment or departments

### FinOps Toolkit migration paths

Microsoft's FinOps Toolkit supports two migration approaches:

1. **Storage-based exports** - configure Cost Management exports to ADLS Gen2 in
   FOCUS format, then connect Power BI directly. Simpler but requires manual
   schema management.

2. **FinOps Hubs** - deploy the FinOps Hubs solution for automated ingestion,
   normalisation, and multi-tenant support. Recommended for organisations with
   multiple billing profiles or complex allocation requirements.

Both approaches produce FOCUS-compliant data, which is the forward-looking standard
for Azure cost reporting.

---

## Key resources

- **Microsoft FinOps Toolkit:** https://github.com/microsoft/finops-toolkit
- **Azure FinOps Guide (community):** https://github.com/dolevshor/azure-finops-guide
- **Azure Cost Management docs:** https://docs.microsoft.com/azure/cost-management-billing/
- **FinOps Foundation Azure guidance:** https://www.finops.org/wg/azure/
- **Azure Retail Prices API:** https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices

---

## Azure Optimization Patterns

> 48 cloud inefficiency patterns covering compute, storage, databases, networking,
> and other Azure services. Use to diagnose waste, validate architecture, or build
> optimisation roadmaps. Source: PointFive Cloud Efficiency Hub.

### Compute Optimization Patterns (13)

**Underutilized Azure Reserved Instance Due To Workload Drift**
Service: Azure Reservations | Type: Commitment Misalignment

As workloads evolve, Azure Reserved Instances (RIs) may no longer align with actual usage - due to refactoring, region changes, autoscaling, or instance-type drift. When this happens, the committed usage goes unused, while new workloads run on non-covered SKUs, resulting in both underutilized reservations and full-price on-demand charges elsewhere.

- Evaluate whether any existing workloads could be migrated to match the reservation scope
- For new workloads, consider provisioning on RI-covered instance types when technically viable
- Where appropriate, exchange the reservation for a more relevant SKU

**Oversized Hosting Plan For Azure Functions**
Service: Azure Functions | Type: Inefficient Configuration

Teams often choose the Premium or App Service Plan for Azure Functions to avoid cold start delays or enable VNET connectivity, especially early in a project when performance concerns dominate. However, these decisions are rarely revisited even as usage patterns change.

- Move low-usage or non-critical Function Apps to the Consumption Plan
- Pilot plan downgrades in non-production or latency-tolerant environments
- Use cost modeling tools to estimate savings from switching to Consumption Plan

**Missing Scheduled Shutdown For Non Production Azure Virtual Machines**
Service: Azure Virtual Machines | Type: Inefficient Configuration

Non-production Azure VMs are frequently left running during off-hours despite being used only during business hours. When these instances remain active overnight or on weekends, they generate unnecessary compute spend.

- Enable Azure's built-in auto-shutdown setting for applicable non-prod VMs
- Alternatively, configure shutdown/start schedules using Azure Automation or Logic Apps
- Preserve state using managed disks, snapshots, or generalized images

**Orphaned And Overprovisioned Resources In AKS Clusters**
Service: Azure AKS | Type: Inefficient Configuration

Clusters often accumulate unused components when applications are terminated or environments are cloned. These include PVCs backed by Managed Disks, Services that still front Azure Load Balancers, and test namespaces that are no longer maintained.

- Delete unused PVCs to release backing Managed Disks
- Clean up Services that are no longer in use to avoid unnecessary load balancer charges
- Scale down underutilized node pools

**Orphaned Kubernetes Resources**
Service: Azure AKS | Type: Orphaned Resource

Kubernetes environments often accumulate unused resources over time as applications evolve. Common examples include Persistent Volume Claims (PVCs) backed by Azure Disks, Services that trigger load balancer provisioning, or stale ConfigMaps and Secrets.

- Before deletion, verify resources are truly orphaned
- Delete orphaned PVCs to release Azure Managed Disks
- Remove Services that no longer front active workloads to deallocate Load Balancers and public IPs

**Outdated Azure App Service Plan**
Service: Azure App Service | Type: Outdated Resource

Applications running on App Service V2 plans may incur higher operational costs and degraded performance compared to V3 plans. V2 uses older hardware generations that lack access to platform-level enhancements introduced in V3, including improved cold start times, faster scaling, and enhanced networking options.

- Evaluate workload compatibility with V3-based plans (e.g., Premium v3 or Isolated v2)
- Plan a phased migration of applications from V2 to V3 to improve performance and reduce cost per resource unit
- Update infrastructure-as-code templates and provisioning defaults to prefer V3-based plans

**Outdated Virtual Machine Version In Azure**
Service: Azure Virtual Machines | Type: Outdated Resource

Many organizations choose a VM SKU and version (e.g., `D4s_v3`) during the initial planning phase of a project, often based on availability, compatibility, or early cost estimates. Over time, Microsoft releases newer hardware generations (e.g., `D4s_v4`, `D4s_v5`) that offer equivalent or better performance at the same or reduced cost.

- Evaluate alternative VM versions (e.g., v4 or v5) within the same family to identify better cost/performance options
- Plan and schedule VM resizing during maintenance windows to avoid unplanned downtime
- Coordinate with application owners to validate compatibility and risk tolerance

**Underutilized Azure Virtual Machine**
Service: Azure Virtual Machines | Type: Overprovisioned Resource

Azure VMs are frequently provisioned with more vCPU and memory than needed, often based on template defaults or peak demand assumptions. When a VM operates well below its capacity for an extended period, it presents an opportunity to reduce costs through rightsizing.

- Analyze average CPU and memory utilization of running VMs to determine if they are underutilized
- Review whether application requirements justify the current VM size
- Evaluate if the workload would perform similarly on a lower SKU within the same VM series

**Inefficient Use Of Photon Engine In Azure Databricks**
Service: Databricks | Type: Suboptimal Configuration

Photon is optimized for SQL workloads, delivering significant speedups through vectorized execution and native C++ performance. However, Photon only accelerates workloads that use compatible operations and data patterns.

- Ensure that Photon is only enabled for workloads structured to benefit from vectorized execution
- Refactor SQL logic and data models to align with Photon-optimized patterns (e.g., filter pushdowns, supported UDFs)
- Use built-in tools such as query plans and job profiles to verify Photon execution

**Missing Shared Scope Configuration For Azure Reservations**
Service: Azure Reservations | Type: Suboptimal Configuration

When reservations are scoped only to a single subscription, any unused capacity cannot be applied to matching resources in other subscriptions within the same tenant. This leads to underutilization of the committed reservation and continued on-demand charges in other parts of the organization.

- Change reservation scope from *Single* to *Shared* in the Azure Portal or via API
- Reevaluate periodically to ensure the scope aligns with current organizational structure and usage distribution

**Suboptimal Architecture Selection For Azure Virtual Machines**
Service: Azure Virtual Machines | Type: Suboptimal Pricing Model

Azure provides VM families across three major CPU architectures, but default provisioning often leans toward Intel-based SKUs due to inertia or pre-configured templates. AMD and ARM alternatives offer substantial cost savings; ARM in particular can be 30-50% cheaper for general-purpose workloads.

- Assess workload compatibility with ARM or AMD architectures
- Propose migration to ARM-based SKUs for supported workloads to reduce compute costs
- Use AMD-based instances as an intermediate option when ARM compatibility is not feasible

**Idle Azure App Service Plan Without Deployed Applications**
Service: Azure App Service | Type: Unused Resource

App Service Plans continue to incur charges even when no applications are deployed. This can occur when applications are deleted, migrated, or retired, but the associated App Service Plan remains active.

- Decommission App Service Plans with no active applications unless a future use case is explicitly confirmed
- In cases with low utilization, consider consolidating multiple lightly used plans into a single plan to reduce spend
- Establish governance practices to routinely identify and remove orphaned plans after application lifecycle events

**Inactive And Stopped VM**
Service: Azure Virtual Machines | Type: Unused Resource

This inefficiency arises when a virtual machine is left in a stopped (deallocated) state for an extended period but continues to incur costs through attached storage and associated resources. These idle VMs are often remnants of retired workloads, temporary environments, or paused projects that were never fully cleaned up.

- Identify virtual machines that have remained in a stopped (deallocated) state for the entire lookback period
- Review whether any activity has occurred from the associated managed disks, network interfaces, or backup processes
- Evaluate whether the VM is part of a dev/test or legacy environment with no recent usage

### Storage Optimization Patterns (16)

**Archival Blob Container Storing Objects In Non Archival Tiers**
Service: Azure Blob Storage | Type: Inefficient Configuration

This inefficiency occurs when a blob container intended for long-term or infrequently accessed data continues to store objects in higher-cost tiers like Hot or Cool, instead of using the Archive tier. This often happens when containers are created without lifecycle policies or default tier settings.

- Identify blob containers with large volumes of data stored in the Hot or Cool tier
- Evaluate access patterns to confirm whether the data is rarely or never read
- Review whether the container's data retention requirements align with archival use cases

**High Transaction Cost Due To Misaligned Tier In Azure Blob Storage**
Service: Azure Blob Storage | Type: Inefficient Configuration

Azure Blob Storage tiers are designed to optimize cost based on access frequency. However, when frequently accessed data is stored in the Cool or Archive tiers - either due to misconfiguration, default settings, or cost-only optimization - transaction costs can spike.

- Move frequently accessed data to the Hot tier, either manually or via lifecycle management policies
- Evaluate default tiering settings on upload processes to prevent misplacement of active data
- Incorporate access pattern analysis into storage tier selection decisions

**High Transaction Cost Due To Misaligned Tier In Azure Files**
Service: Azure Files | Type: Inefficient Configuration

Azure Files Standard tier is cost-effective for low-traffic scenarios but imposes per-operation charges that grow rapidly with frequent access. In contrast, Premium tier provides consistent IOPS and throughput without additional transaction charges.

- Evaluate cost-performance tradeoffs between Standard and Premium tiers
- If justified, migrate data to a new Azure Files Premium account (required for tier change)
- Use performance metrics and transaction volume to guide future provisioning decisions

**Inactive Blobs In Storage Account**
Service: Azure Blob Storage | Type: Inefficient Configuration

Storage accounts can accumulate blob data that is no longer actively accessed - such as legacy logs, expired backups, outdated exports, or orphaned files. When these blobs remain in the Hot tier, they continue to incur the highest storage cost, even if they have not been read or modified for an extended period.

- Identify storage accounts with large amounts of data in the Hot tier
- Analyze blob-level access patterns using logs or metrics to confirm that data has not been read or written over a defined lookback period
- Determine whether the data is still relevant to any active workload, process, or compliance requirement

**SFTP Feature Enabled On Azure Storage Account Without Usage**
Service: Azure Storage Account | Type: Inefficient Configuration

Azure users may enable the SFTP feature on Storage Accounts during migration tests, integration scenarios, or experimentation. However, if left enabled after initial use, the feature continues to generate flat hourly charges - even when no SFTP traffic occurs.

- Disable the SFTP feature on any Storage Account where it is no longer needed
- Coordinate with owners to confirm that alternate access methods (e.g., HTTPS, SDK) are sufficient
- Consider including SFTP enablement in governance reviews to catch idle services before they accumulate charges

**Missing Performance Plus On Eligible Managed Disks**
Service: Azure Managed Disks | Type: Misconfiguration

For Premium SSD and Standard SSD disks 513 GiB or larger, Azure now offers the option to enable Performance Plus - unlocking higher IOPS and MBps at no extra cost. Many environments that previously required custom performance settings continue to pay for additional throughput unnecessarily.

- Enable Performance Plus on all eligible disks using Azure CLI, API, or portal
- Decommission paid performance tiers or custom throughput settings where Performance Plus provides equivalent capability
- Incorporate Performance Plus enablement into provisioning templates for large disks going forward

**Outdated And Expensive Premium SSD Disk**
Service: Azure Managed Disks | Type: Modernization

Workloads using legacy Premium SSD managed disks may be eligible for migration to Premium SSD v2, which delivers equivalent or improved performance characteristics at a lower cost. Premium SSD v2 decouples disk size from performance metrics like IOPS and throughput, enabling more granular cost optimization.

- Identify Premium SSD managed disks provisioned using the original Premium SSD offering (not v2)
- Review disk IOPS, throughput, and sizing requirements to ensure compatibility with Premium SSD v2 capabilities
- Analyze whether the current SKU size (e.g., P30, P40) exceeds actual capacity and performance needs

**Outdated And Expensive Standard SSD Disk**
Service: Azure Managed Disks | Type: Modernization

Standard SSD disks can often be replaced with Premium SSD v2 disks, offering enhanced IOPS, throughput, and durability at competitive or lower pricing. For workloads that require moderate to high performance but are currently constrained by Standard SSD capabilities, migrating to Premium SSD v2 improves both performance and cost efficiency without significant operational overhead.

- Identify Managed Disks using the Standard SSD offering that are eligible for migration to Premium SSD v2
- Review workload performance requirements to confirm suitability for Premium SSD v2 characteristics
- Verify regional availability of Premium SSD v2 before planning migration

**Excessive Retention Of Audit Logs**
Service: Azure Blob Storage | Type: Over-Retention of Data

Audit logs are often retained longer than necessary, especially in environments where the logging destination is not carefully selected. Projects that initially route SQL Audit Logs or other high-volume sources to LAW or Azure Storage may forget to revisit their retention strategy.

- Review retention policies for audit logs and align them with regulatory requirements
- Use Azure Storage lifecycle management to transition older logs to lower-cost tiers or delete them automatically
- Reference: Azure Storage Lifecycle Management documentation

**Overprovisioned Managed Disk For VM Limits**
Service: Azure Managed Disks | Type: Overprovisioned Resource

Each Azure VM size has a defined limit for total disk IOPS and throughput. When high-performance disks (e.g., Premium SSDs with high IOPS capacity) are attached to low-tier VMs, the disk's performance capabilities may exceed what the VM can consume.

- Resize disks to match the performance envelope of the associated VM
- Downgrade to lower disk tiers (e.g., Premium SSD -> Standard SSD) when full performance is not needed
- Establish guardrails to ensure disk and VM configurations are aligned during provisioning and resizing events

**Long Retained Azure Snapshot**
Service: Azure Snapshots | Type: Retained Unused Resource

Snapshots are often created for short-term protection before changes to a VM or disk, but many remain in the environment far beyond their intended lifespan. Over time, this leads to an accumulation of snapshots that are no longer associated with any active resource or retained for operational need. Since Azure does not enforce automatic expiration or lifecycle policies for snapshots, they can persist indefinitely and continue to incur monthly storage charges.

- Manually review long-retained snapshots with application or infrastructure owners
- Delete snapshots no longer needed for recovery, rollback, or compliance retention
- Adopt tagging standards to track purpose, owner, and expected retention period at time of snapshot creation

**Inactive And Detached Managed Disk**
Service: Azure Managed Disks | Type: Unused Resource

Managed Disks frequently remain detached after Azure virtual machines are deleted, reimaged, or reconfigured. Some may be intentionally retained for reattachment, backup, or migration purposes, but many persist unintentionally due to the lack of automated cleanup processes.

- Identify Managed Disks that are in an unattached state (not linked to any VM)
- Review metrics or activity logs to determine whether the disk has seen any read or write operations during the lookback period
- Check whether the disk is intentionally retained for recovery, migration, or reattachment

**Inactive Files In Storage Account**
Service: Azure Blob Storage | Type: Unused Resource

Files that show no read or write activity over an extended period often indicate redundant or abandoned data. Keeping inactive files in higher-cost storage classes unnecessarily increases monthly spend.

- Identify storage accounts or containers containing blobs with no reads or modifications over a defined lookback period
- Analyze blob access logs and object metadata to validate inactivity
- Review creation timestamps, tags, and business ownership metadata to assess ongoing relevance

**Inactive Tables In Storage Account**
Service: Azure Table Storage | Type: Unused Resource

Tables with no read or write activity often represent deprecated applications, obsolete telemetry, or abandoned development artifacts. Retaining inactive tables increases storage costs and operational complexity.

- Identify Azure Table Storage tables with no read or write operations over a defined lookback period
- Review table creation dates, metadata, and ownership tags to assess relevance and intended retention
- Check for compliance, legal hold, or audit requirements before initiating deletions or exports

**Managed Disk Attached To A Deallocated VM**
Service: Azure Managed Disks | Type: Unused Resource

This inefficiency occurs when a VM is deallocated but its attached managed disks are still active and incurring storage charges. While compute billing stops for deallocated VMs, the disks remain provisioned and billable.

- Identify managed disks attached to deallocated VMs during the defined lookback period
- Review disk activity to confirm no read/write operations occurred while the VM was deallocated
- Evaluate whether the disk is still needed for backup, migration, or future reactivation

**Managed Disk Attached To A Stopped VM**
Service: Azure Managed Disks | Type: Unused Resource

Disks attached to VMs that have been stopped for an extended period, particularly when showing no read or write activity, may indicate abandoned infrastructure or obsolete resources. Retaining these disks without validation leads to unnecessary monthly storage costs.

- Identify Managed Disks attached to virtual machines that have remained in a stopped state over a representative time window
- Analyze disk activity metrics to detect absence of read/write operations during the lookback period
- Review VM metadata, ownership tags, and decommissioning records to assess whether the disk is still required

### Databases Optimization Patterns (8)

**Business Critical Tier On Non Production SQL Instance**
Service: Azure SQL | Type: Inefficient Configuration

Non-production environments such as development, testing, or staging often do not require the high availability, failover capabilities, and premium storage performance offered by the Business Critical tier. Running these workloads on Business Critical unnecessarily inflates costs.

- Migrate non-production SQL instances from the Business Critical tier to a lower-cost alternative, such as General Purpose
- Use downtime windows or database copy strategies to minimize risk during tier transitions, depending on instance size and availability requirements
- Monitor performance after migration to ensure the workload remains stable and meets operational needs

**Unnecessary Use Of RA-GRS For Azure SQL Backup Storage**
Service: Azure SQL | Type: Inefficient Configuration

Azure SQL databases often use the default backup configuration, which stores backups in RA-GRS storage to ensure geo-redundancy. While suitable for high-availability production systems, this level of resilience may be unnecessary for development, testing, or lower-impact workloads.

- For non-critical or non-regulated workloads, change the backup redundancy setting to LRS (or ZRS where supported)
- Document any exceptions where RA-GRS must be retained for compliance
- Incorporate backup configuration reviews into provisioning and governance processes

**Infrequently Accessed Data Stored In Azure Cosmos DB**
Service: Azure Cosmos DB | Type: Inefficient Storage Tiering

Azure Cosmos DB is optimized for low-latency, globally distributed workloads - not long-term storage of infrequently accessed data. Yet in many environments, cold data such as logs, telemetry, or historical records is retained in Cosmos DB due to a lack of lifecycle management.

- Export infrequently accessed data to lower-cost storage services
- Use Blob Storage Cool for rarely accessed but readily retrievable data
- Use Blob Storage Archive for long-term retention with delayed retrieval

**Overprovisioned Azure Database For PostgreSQL Flexible Server**
Service: Azure Database for PostgreSQL Flexible Server | Type: Overprovisioned Resource

Azure Database for PostgreSQL Flexible Server often defaults to general-purpose D-series VMs, which may be oversized for many production or development workloads. PostgreSQL typically does not require sustained high CPU, making it well-suited to memory-optimized (E-series) or burstable (B-series) instances.

- Resize the PostgreSQL Flexible Server to a smaller or more suitable VM family based on actual workload behavior
- For low-CPU workloads, consider B-series (burstable) or E-series (memory-optimized) configurations
- Review usage patterns quarterly to ensure the selected SKU remains aligned with performance needs

**Overprovisioned Compute Tier In Azure SQL Database**
Service: Azure SQL | Type: Overprovisioned Resource

Azure SQL Database resources are frequently overprovisioned due to default configurations, conservative sizing, or legacy requirements that no longer apply. This inefficiency appears across all deployment models: Single Databases may be assigned more DTUs or vCores than the workload requires; Elastic Pools may be oversized for the actual demand of pooled databases; Managed Instances are often deployed with excess compute capacity that remains underutilized. Because billing is based on provisioned capacity, not actual consumption, organizations incur unnecessary costs when sizing is not aligned with workload behavior.

- Downsize the compute tier (DTUs or vCores) to better match observed usage
- For Elastic Pools, reduce the total eDTUs/vCores and consider consolidating lightly used databases
- For Managed Instances, assess whether the vCore allocation can be reduced or workloads refactored

**Overprovisioned Storage In Azure SQL Elastic Pools Or Managed Instances**
Service: Azure SQL | Type: Overprovisioned Resource

Azure SQL deployments often reserve more storage than needed, either due to default provisioning settings or anticipated future growth. Over time, if actual usage remains low, these oversized allocations generate unnecessary storage costs.

- Where supported, reduce provisioned storage to better align with actual usage
- For Managed Instances, safely execute `DBCC SHRINKFILE` or equivalent operations before resizing
- Incorporate storage reviews into regular database hygiene practices

**Overbilling Due To Tier Switches And Allocation Overlaps In DTU Model**
Service: Azure SQL | Type: Suboptimal Pricing Model

Workloads that frequently scale up and down within the same day - whether manually, via automation, or platform-managed - can encounter hidden cost amplification under the DTU model. When a database changes tiers (e.g., S7 -> S4), Azure treats each tiered segment as a separate allocation and applies full-hour rounding independently.

- Minimize same-day tier switches unless operationally justified
- Schedule up/down-scaling during off-peak windows to reduce risk of overlapping billing
- Move to the vCore or serverless pricing model for more transparent and granular cost control

**Idle Azure SQL Elastic Pool Without Databases**
Service: Azure SQL | Type: Unused Resource

An Azure SQL Elastic Pool continues to incur costs even if it contains no databases. This can occur when databases are deleted, migrated to single-instance configurations, or consolidated elsewhere - but the pool itself remains provisioned.

- Decommission any Elastic Pool with no active databases unless a valid business case exists for retaining it
- Review infrastructure-as-code templates and automation pipelines to ensure pool cleanup is included in deprovisioning workflows
- Establish periodic audits to catch and remove idle pools across subscriptions and teams

### Networking Optimization Patterns (5)

**Suboptimal Load Balancer Rule Configuration In Azure Standard Load Balancer**
Service: Azure Load Balancer | Type: Inefficient Configuration

As organizations migrate from the Basic to the Standard tier of Azure Load Balancer (driven by Microsoft's retirement of the Basic tier), they may unknowingly inherit cost structures they didn't previously face. Specifically, each load balancing rule - both inbound and outbound - can contribute to ongoing charges.

- Audit existing Standard Load Balancer rule sets to identify unused entries
- Remove unnecessary inbound and outbound rules, especially in non-production environments
- Avoid blanket rule creation in templated environments unless explicitly required

**Inactive Azure Load Balancer**
Service: Azure Load Balancer | Type: Unused Resource

In dynamic environments - especially during autoscaling, testing, or infrastructure changes - it's common for load balancers to remain provisioned after their backend resources have been decommissioned. When this happens, the load balancer continues to incur hourly charges despite serving no functional purpose.

- Delete Azure Load Balancers that have no backend pool members and no observed traffic
- Implement automation or tagging policies to detect and flag inactive networking resources
- Update infrastructure-as-code or deployment scripts to ensure load balancers are removed alongside their dependent compute resources

**Inactive Standard Load Balancer With Unused Frontend IPs**
Service: Azure Load Balancer | Type: Unused Resource

Standard Load Balancers are frequently provisioned for internal services, internet-facing applications, or testing environments. When a workload is decommissioned or moved, the load balancer may be left behind without any active backend pool or traffic - but continues to incur hourly charges for each frontend IP configuration. Because Azure does not automatically remove or alert on inactive load balancers, and because they may not show significant outbound traffic, these resources often persist unnoticed.

- Delete load balancers that have no active backend pool and are no longer needed
- Review associated resources (e.g., front-end IP configurations, probes, rules) to ensure they can be safely removed
- Establish tagging or documentation standards to track ownership and intended usage

**Inactive Web Application Firewall (WAF)**
Service: Azure WAF | Type: Unused Resource

Azure WAF configurations attached to Application Gateways can persist after their backend pool resources have been removed - often during environment reconfiguration or application decommissioning. In these cases, the WAF is no longer serving any functional purpose but continues to incur fixed hourly costs.

- Delete WAF configurations that are no longer routing traffic or protecting active applications
- Establish periodic audits to flag and review WAFs with empty backend pools
- Use automated checks to detect and alert on WAF deployments with no active use

**Unassigned Public IP Address**
Service: Azure Networking | Type: Unused Resource

In Azure, it's common for public IP addresses to be created as part of virtual machine or load balancer configurations. When those resources are deleted or reconfigured, the IP address may remain in the environment unassigned.

- Delete unassigned Standard SKU public IPs that are no longer needed
- If an unassigned IP is intended for future use, consider converting it to Basic (if compatible)
- Incorporate IP resource cleanup into deprovisioning workflows

### Other Optimization Patterns (6)

**Transactable vs Non-Transactable Confusion In Azure Marketplace**
Service: Azure Marketplace | Type: Commitment Misalignment

Azure Marketplace offers two types of listings: transactable and non-transactable. Only transactable purchases contribute toward a customer's MACC commitment. See the "MACC - commercial commitment alignment" section under Commitment discounts for full drawdown mechanics, including what counts and what does not.

- Prefer transactable listings in Azure Marketplace whenever MACC utilization is a priority
- Validate SKU eligibility against Microsoft's Procurement Playbook or MACC eligibility lists
- Standardize sourcing templates and procurement workflows to explicitly document whether the offer contributes to MACC
- Confirm that the purchase is transacted through the Azure portal under a subscription tied to the enrollment - credit card purchases on the Marketplace website do not count toward MACC even for eligible products

**Lifecycle Visibility Gaps Inflating Renewal Costs In Azure Marketplace**
Service: Azure Marketplace | Type: Contract Lifecycle Mismanagement

When Marketplace contracts or subscriptions expire or change without visibility, Azure may automatically continue billing at higher on-demand or list prices. These lapses often go unnoticed due to lack of proactive tracking, ownership, or renewal alerts, resulting in substantial cost increases.

- Assign clear ownership of Marketplace contracts across business, finance, or procurement teams
- Set calendar-based and system-based reminders for contract renewals and entitlement expiration
- Regularly reconcile Azure billing data with vendor-provided SLA or entitlement terms

**Inefficient Use Of Azure Pipelines**
Service: Azure DevOps | Type: Inefficient Configuration

Teams often overuse Microsoft-hosted agents by running redundant or low-value jobs, failing to configure pipelines efficiently, or neglecting to use self-hosted agents for steady workloads. These inefficiencies result in unnecessary cost and delivery friction, especially when pipelines create queues due to limited agent availability.

- Audit and streamline pipelines to remove redundant or unnecessary stages
- Use conditional logic to limit execution of non-critical pipelines
- Prioritize agent capacity for pipelines supporting core or production workloads

**Overly Frequent Querying In Azure Monitor Alerts**
Service: Azure Monitor | Type: Inefficient Configuration

While high-frequency alerting is sometimes justified for production SLAs, it's often overused across non-critical alerts or replicated blindly across environments. Projects with multiple environments (e.g., dev, QA, staging, prod) often duplicate alert rules without adjusting for business impact, which can lead to alert sprawl and inflated monitoring costs.

- Test changes gradually. Start with non-production environments and non-critical alerts
- Right-size alert frequency based on actual SLA requirements rather than worst-case assumptions
- Review and prune alert rules quarterly to keep monitoring overhead aligned with operational value

**Inefficient Private Link Routing To Azure Databricks**
Service: Azure Databricks | Type: Misconfiguration

In Azure Databricks environments that rely on Private Link for secure networking, it's common to route traffic through multi-tiered network architectures. This often includes multiple VNets, Private Link endpoints, or peered subscriptions between data sources (e.g., ADLS) and the Databricks compute plane.

- Simplify routing by colocating Databricks and storage in the same region and VNet when possible
- Eliminate redundant Private Link endpoints that add no security or compliance value
- Use direct peering or shared services models to reduce network traversal

**Suboptimal Table Plan Selection In Log Analytics**
Service: Azure Monitor | Type: Suboptimal Pricing Model

By default, all Log Analytics tables are created under the Analytics plan, which is optimized for high-performance querying and interactive analysis. However, not all telemetry requires real-time access or frequent querying. (Note: Auxiliary plan availability varies per table - see Log Analytics cost control section above for current eligibility.)

- Assign the Basic plan to tables that are retained for audit, archival, or compliance purposes
- Split high-volume ingestion sources into separate tables based on access needs
- Reconfigure ingestion routes to direct non-essential logs to lower-cost tables

**Source:** https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
