# FinOps on Azure

> Azure-specific guidance covering cost management tools, commitment discounts, compute
> rightsizing, database and storage optimization, cost allocation, and governance.
> Covers Cost Management exports, FOCUS exports, Azure Advisor, Reservations, Savings
> Plans, Azure Hybrid Benefit, Azure Policy and tagging governance, AKS optimization,
> database optimisation (Azure SQL, Postgres/MySQL Flexible, Cosmos DB), Log Analytics
> cost control, backup and snapshot management, storage tiering and lifecycle, and
> networking cost.
>
> Distilled from the [Azure FinOps Master](https://github.com/yourorg/azure-finops-master)
> course (7 sessions + case studies).

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
Recommended for organizations that want production-grade reporting without building custom
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
| Azure Reservation | Up to 72% | Lowest - locked to VM family, region, size | Capacity-based (specific SKU) | 1yr or 3yr | VMs, Dedicated Hosts, App Service (Isolated), specific services |
| Azure Savings Plan for Compute | Up to 65% | High - any VM family, region, size | Spend-based ($/hr) | 1yr or 3yr | VMs, Dedicated Hosts, Container Instances, App Service (Premium v3 / Isolated v2) |
| Azure Hybrid Benefit (AHB) | Up to 40% (Windows), 55% (SQL) | Highest - no commitment, no lock-in | Licensing overlay | None | VMs, SQL Database, SQL MI, Red Hat/SUSE Linux |
| Spot Virtual Machines | Up to 90% | Variable - can be evicted with 30s notice | None (market-priced) | None | VMs, VMSS, AKS node pools |

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

**Reservation and Savings Plan liquidity mechanics (current as of April 2026):**

| Mechanic | Fee | Annual cap | Notes |
|---|---|---|---|
| **Reservation exchange** | None | None | Same product family only. Does not count against the refund cap. |
| **Reservation refund (cancellation)** | None today | $50,000 per 12-month rolling window per Billing Profile (MCA) or enrollment (EA) | "Refund" and "cancellation" are the same operation in current docs. Microsoft reserves the right to introduce a 12% early-termination fee in future - verify before relying on liquidity. |
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
│   │               ├── YES → Azure Reservation (up to 72%)
│   │               │         Deepest discount. Can be exchanged for a
│   │               │         different SKU if workload changes (subject
│   │               │         to exchange policy limits).
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
- High baseline + low variability + Linux or non-AHB -> 1-year RI (3-year if conviction
  is high)
- Variable workload, stable $ floor -> Savings Plan, 1-year, sized at 70-80% of floor
- Bursty / unpredictable -> PAYG with Spot for the spike layer

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

**Source:** https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices