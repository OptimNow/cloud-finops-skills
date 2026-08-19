---
name: finops-azure-commitments
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Forecasting"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Finance"]
fcp_personas_collaborating: ["Engineering", "Procurement", "Leadership"]
fcp_maturity_entry: "Walk"
---

# Azure Commitment Discounts

> Azure rate-optimisation instruments and the decisions around them: Reservations,
> Savings Plans, Azure Hybrid Benefit, Spot, the compute and database commitment
> decision trees, portfolio liquidity under the 1 February 2027 exchange retirement,
> phased purchasing, and MACC alignment. Split out of `finops-azure.md`, which carried
> this material in three sections ~2,000 lines apart. For Azure billing data,
> rightsizing, service optimisation and governance, see `finops-azure.md`.

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

**Note on one-year Reserved VM Instances:** As of July 1, 2026, Azure is retiring one-year Reserved VM Instances for select older VM series. This affects new purchases and renewals for these specific series. Three-year reservations remain available for all VM series. When planning reservation strategies, verify current eligibility for one-year terms on your target VM series. Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/manage-legacy-vm-reservations-after-july-1-2026

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

4. **Reservation liquidity is shrinking; Savings Plans have none.** See the liquidity
   mechanics table below for fees, caps, and operational rules. Hold two things together.
   First, from 1 February 2027 reservation exchange retires for any service a savings plan
   also covers (VMs, Dedicated Host, App Service, and the covered databases); refund and
   trade-in to a savings plan survive. Second, for services a savings plan does not cover
   (such as Azure VMware Solution) exchange continues. Microsoft's refund terms remain more
   generous than AWS Standard RI marketplace selling, but read the fine print on the future
   12% fee clause, and treat exchange as unavailable for covered services when planning.

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

**Reservation and Savings Plan liquidity mechanics (verified against Microsoft Learn, July 2026):**

| Mechanic | Fee | Annual cap | Notes |
|---|---|---|---|
| **Reservation exchange** | None | None | Same product family only. Does not count against the refund cap. **Retiring 1 February 2027 for services also covered by a savings plan** (VMs, Dedicated Host, App Service, and the covered databases). Reservations purchased before that date keep the right to one final exchange, granted per quantity. Because an exchange is processed as a cancel, refund, and repurchase, an exchange done after that date yields a non-exchangeable reservation. Reservations for services with no savings plan (such as Azure VMware Solution) keep exchange. |
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
│   │               │         │         Deepest discount. From 1 Feb 2027 covered
│   │               │         │         services can't be exchanged, so reserve only
│   │               │         │         at high conviction on family, region, and term.
│   │               │         │         Size stays flexible within the family via ISF.
│   │               │         │
│   │               │         └── NO → Consider 3yr reservation or migration to
│   │               │                  newer VM series that supports 1yr terms
│   │               │
│   │               └── NO / UNSURE → Savings Plan for Compute (up to 65%)
│   │                     Covers any VM family and region. ~7% shallower
│   │                     than Reservations but protects against family
│   │                     or region changes. Any doubt on the lock
│   │                     dimensions defaults here. Cannot be exchanged
│   │                     or refunded once purchased.
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
| Exchangeable | Until 1 Feb 2027 for covered services (then one final exchange for reservations bought earlier); unaffected for non-covered services such as VMware. Same product family, no fee, no cap | No |
| Refundable | Pro-rated, up to $50K per 12 months - no fee today; Microsoft reserves right to add 12% future fee | No |
| Cancellable | Yes - refund and cancellation are the same operation today, no fee currently charged | No |
| Payment options | Monthly or Upfront | Monthly or Upfront |
| Scoping | Subscription, resource group, management group, shared | Subscription, resource group, management group, shared |

**Key takeaway (updated for the 1 February 2027 exchange change):** Reservations still
offer the deeper discount, but their flexibility edge narrows sharply. For services a
savings plan also covers, reservation exchange retires on 1 February 2027, leaving only a
capped refund and a one-way trade-in to a savings plan. Until that date the old logic held:
reserve moderately stable workloads, exchange if things change. From that date, reserve a
covered service only at high conviction across family, region, term, and workload
continuation; instance size flexibility still handles size within the family. Default
anything short of that to a savings plan. See "Commitment liquidity after February 2027"
below for the operational rule.

### Commitment liquidity after February 2027

Context: this rule assumes the 1 February 2027 retirement of reservation exchange for
services also covered by a savings plan, and it applies to those covered services only.

The escape hatch that made reservations safe at moderate confidence, free and uncapped
exchange, is being removed for covered services. The remaining corrections are a refund
capped at $50,000 per 12-month rolling window and a one-way trade-in to a savings plan.
Build the strategy around that.

**Reserve only at high conviction across five lock dimensions, for the full term:**

1. VM family stays put.
2. Region stays put.
3. Size stays inside the instance-size-flexibility band (ISF is unaffected by the change).
4. Term length is one you can genuinely hold (1yr vs 3yr).
5. No migration or decommission is planned in the window.

If any single dimension is uncertain, default to a savings plan. Family and region are the
hard new locks; size within the family stays flexible through ISF.

**Two refinements so the rule does not backfire:**

- **The default has a price, so size it.** A savings plan discounts roughly 7 points less
  than a reservation on compute (up to 65% vs up to 72%), and more on databases (up to 35%
  vs the reservation rate). That gap is the premium for the flexibility exchange used to
  provide for free. On a large, genuinely stable baseline it can reach six figures a year.
  Reserve the certain floor; do not surrender its depth out of caution.
- **At Crawl and Walk maturity, the fallback is often more PAYG buffer, not a bigger
  savings plan.** Azure bills daily while a savings plan is sized on an hourly floor (see
  "Why daily data hurts Savings Plan sizing more than RI sizing"), and a savings plan has
  zero liquidity to unwind an over-commitment. Teams that cannot yet build the
  cost-plus-utilisation join should hedge the uncertain slice with a wider PAYG buffer,
  plus AHB and Spot where they fit, until they can size the hourly floor with confidence.

Microsoft's own framing now matches this split: reservations for predictable, stable
workloads, savings plans for evolving or dynamic ones.

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
Layer 3: Reservations (high-conviction, locked-in VM workloads)
  ↓ captures the extra ~7% discount for workloads locked to a family+region
  ↓ liquidity for covered services is refund + trade-in only from 1 Feb 2027 (no exchange)
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
Staggering matters more now that exchange retires for covered services on 1 February 2027:
the recovery path for a wrong covered reservation is a capped refund or a one-way trade-in
to a savings plan, not a free exchange. Size each tranche so a mistake fits inside the
$50,000 refund window.

**Step 6 - Quarterly re-evaluation.** For non-covered services, exchange RIs that no
longer fit the workload; for covered services after 1 February 2027, use refund (within
the cap) or trade-in to a savings plan instead. Track SP utilisation against committed
$/hour. Adjust the next quarter's commitments based on prior actuals, not on Advisor's
rolling backward-looking recommendation.

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
        |       MySQL, SQL MI
        |     - Exchange retires 1 Feb 2027 for these services (one final
        |       exchange for reservations bought before that date)
        |     - Pro-rated refund (up to $50K/12 months) and trade-in to a
        |       savings plan remain
        |
        +-- Multiple database services or regions
        |   -> Savings Plan for Databases (up to 35%, March 2026)
        |     - Covers: SQL Database, PostgreSQL, MySQL, Cosmos DB,
        |       SQL MI
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
Database for MySQL, Azure Cosmos DB, Azure SQL Managed Instance.

Azure Database for MariaDB is **not** eligible - the service retired in September
2025. If you still carry MariaDB workloads, they are running somewhere other than
the managed service (VMs, containers, or a third-party host) and no database
commitment covers them.

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

The mechanics themselves - exchange, refund and its $50,000 rolling cap, instance
size flexibility, trade-in to a savings plan, staggered expiry - are tabulated once in
"Reservation and Savings Plan liquidity mechanics" near the top of this file. That
table used to be repeated here because the two sections lived ~2,000 lines apart in
`finops-azure.md` and a reader landing in the portfolio section would not have seen it.
Now that both sit in this file, the duplicate is gone; read the table above, then the
portfolio consequences below.

**Key insight (updated for 1 February 2027):** Reservations were more liquid than Savings
Plans on Azure, the opposite of the common assumption. That edge is narrowing. Savings
Plans still offer usage flexibility (any family, any region) but zero financial liquidity
(no exchange, no refund, no cancellation). Reservations still allow refunds (within the
$50K cap), trade-in to a Savings Plan (no fee, no limit), and instance size flexibility
within the family, but reservation exchange retires on 1 February 2027 for any service a
savings plan also covers. For those covered services the liquidity edge shrinks to the
refund cap; exchange survives only for non-covered services such as VMware. When choosing
between the two, factor this into the decision, not just discount depth and coverage
breadth.

**The $50,000 refund cap.** Microsoft imposes a rolling 12-month cap of $50,000 on
Reservation refunds per Billing Profile (MCA) or enrollment (EA). Exchanges that still
apply (non-covered services, or a final exchange on a pre-2027 covered reservation) do
not count against this cap. Once exchange retires for covered services on 1 February 2027,
the refund cap becomes the main reshaping lever for those reservations, so it binds harder
on large portfolios. The cap restores day-by-day; spread cancellations across the 12-month
window where possible.

Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/exchange-and-refund-azure-reservations

**Size the first tranche at the keel commitment** - the usage level that has never
left the water across the trailing 12 months. Below the keel, committing needs no
forecast: that spend is already sunk. Every point of coverage above it is a bet on a
forecast, and belongs in the phased blocks below. Re-measure the keel quarterly; it
moves when workloads are decommissioned or migrated, not when traffic fluctuates,
and a falling keel is an early liquidity warning - on Azure doubly so after
1 February 2027, when the refund cap becomes the main reshaping lever.

### Phased purchasing

Never buy the full commitment in a single transaction. Purchase in blocks to create
a portfolio with staggered expiry dates. The cadence and block size should match
your consumption profile - not a fixed rule.

**Why phased purchasing matters on Azure:**
- **Reduces lock-in risk:** if workloads migrate or are re-architected, only the
  current block is at risk
- **Creates natural re-evaluation points:** each purchase cycle forces a review of
  utilisation, Advisor recommendations, and architecture direction
- **Preserves refund headroom:** spreading purchases means smaller individual
  Reservations, making it easier to stay within the $50K refund cap if changes are
  needed (exchange headroom applies only to non-covered services after 1 Feb 2027)
- **Aligns with MACC cadence:** phased purchasing can be timed to support MACC
  burndown trajectory, avoiding end-of-period scrambles
- **Captures pricing improvements:** newer VM generations (v5, v6) and architecture
  shifts (ARM-based Dps/Eps families) can be reflected in subsequent blocks

<!-- Deliberate mirror: this cadence/block-size table also appears in
finops-aws-commitments.md. Each commitments file is loaded standalone
(one provider per query), so the duplication is intentional - do not
deduplicate into a shared file. -->
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

**Azure-specific consideration:** until 1 February 2027, reservations for covered services
can be exchanged mid-term, giving moderate-frequency buyers (monthly/bi-monthly) an extra
liquidity layer on top of staggered expiry. From that date exchange retires for covered
services, so that layer disappears there and the choice rests on discount depth and
conviction; it persists for non-covered services such as VMware. Organisations buying
weekly may still prefer Savings Plans to avoid the administrative overhead of frequent
Reservation management.

**Phased purchasing framework (quarterly example for steady consumption):**

```
Quarter 1: Buy 20-25% of target commitment (the keel commitment - the floor you are certain about)
  -> Monitor utilisation for 30 days via Azure Advisor and Cost Management
  -> If utilisation >80%: proceed to next block
  -> If utilisation <80%: investigate before buying more

Quarter 2: Buy next 15-20% block
  -> Reassess workload stability and architecture plans
  -> Reshape earlier blocks if workloads shifted (exchange for non-covered services;
     refund or trade-in for covered services after 1 Feb 2027)

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
  pause. Reshape earlier blocks if workloads have shifted: exchange for non-covered
  services, refund or trade-in to a savings plan for covered services after 1 Feb 2027.
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
- How much of your $50,000 Reservation refund cap have you used in the last 12 months?
  With exchange retiring for covered services on 1 Feb 2027, this cap is the main
  reshaping lever for those reservations, so headroom matters more.
- Are Savings Plans covering workloads that are stable enough for Reservations
  (leaving ~7% discount on the table)?
- Is MACC burndown tracking integrated into the same review cadence as commitment
  purchasing? If not, optimisation gains may create a MACC shortfall risk.
- Are engineering teams planning VM family migrations (e.g. to ARM-based Dps/Eps)
  that would strand existing Reservations? If so, favour Savings Plans for those
  workloads, since exchange retires for covered services on 1 Feb 2027 and can no
  longer rescue a stranded reservation.

**Key metrics:**
- **Reservation/SP Utilisation:** Target >80%. Below this, the commitment is
  oversized.
- **Reservation/SP Coverage:** Target 70% (Walk maturity), 80%+ (Run maturity).
- **Effective Savings Rate:** actual savings / theoretical maximum. Measures how
  well commitments are matched to real usage.
- **Break-even period:** should be <9 months for 1-year terms, <15 months for 3-year.
- **Commitment waste:** hours where committed capacity had no matching usage.
- **Refund headroom:** remaining $ available under the $50K/12-month refund cap. This
  is the main reshaping lever for covered services once exchange retires on 1 Feb 2027.

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


---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
