---
name: finops-azure-commitments
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Forecasting"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Finance"]
fcp_personas_collaborating: ["Engineering", "Procurement", "Leadership"]
fcp_maturity_entry: "Walk"
business_coverage: ["azure:commitments:deep", "azure:contracts:partial", "azure:saas:partial"]
---

# Azure Commitment Discounts

> Azure rate-optimisation instruments and the decisions around them: Reservations,
> Savings Plans, Azure Hybrid Benefit, Spot, the compute and database commitment
> decision trees, portfolio liquidity under the 1 February 2027 exchange retirement,
> phased purchasing, and MACC alignment (MACC negotiation is in
> `finops-cloud-contracts.md`). For Azure billing data, allocation and governance, see
> `finops-azure-billing.md`; for rightsizing and service optimisation, `finops-azure.md`.

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

**Note on one-year Reserved VM Instances:** As of 1 July 2026, Azure is retiring one-year Reserved VM Instances for select older VM series. This affects new purchases and renewals for these specific series. Three-year reservations remain available for all VM series. When planning reservation strategies, verify current eligibility for one-year terms on your target VM series. Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/manage-legacy-vm-reservations-after-july-1-2026

**Critical distinctions:**

1. **Azure Hybrid Benefit is not a commitment - it is a licensing overlay.** If you have
   Windows Server or SQL Server licenses with Software Assurance, AHB eliminates the
   license component from VM pricing. No contract, no lock-in, no restart needed. The
   one exposure is licence compliance: each VM claiming AHB needs an eligible licence
   with active Software Assurance assigned to it, and the assignment must hold up in
   a licence audit. Enable it on all eligible VMs before any other commitment
   decision. Windows licence costs can be a large share of a Windows VM's
   pay-as-you-go rate; read the exact split for your SKU from the pricing
   calculator. Use the AHB Workbook from
   FinOps Toolkit for
   compliance tracking across the fleet.

2. **Savings Plans for Compute cover more than VMs.** Unlike Reservations (which are
   resource-specific), Compute Savings Plans also cover Container Instances and App
   Service Premium v3 / Isolated v2. If you run a mix of VMs, containers, and App
   Service, a Compute Savings Plan is the only instrument that covers all three.

3. **Reservations offer deeper discounts but less flexibility.** A Reservation locks to
   a specific VM family and region. If you change instance family or region mid-term, the
   Reservation does not follow. A Savings Plan is spend-based and applies wherever it
   finds eligible usage - but the discount is ~7% shallower than a Reservation.
   Measured on the 2026-10-25 OptimToken catalogue (Linux, eastus, no upfront), the
   median per-row gap is 8.7 points at 1 year (median discounts 32.0% and 41.0%) and
   7.9 at 3 years (53.4% and 60.5%). The reservation discount splits by family: 41.0%
   to 41.1% at 1 year on Esv5, Easv5, Dpsv5 and Epsv5, 38.3% on Dsv5 and Dasv5, while
   the savings plan runs 31.3% to 32.7% across all of them. Current values:
   <https://optimtoken.optimnow.io/guides/savings-plans-vs-reserved-instances> (page) and
   <https://optimtoken.optimnow.io/guides/savings-plans-vs-reserved-instances/figures.json> (data).

4. **Reservations keep a capped refund and trade-in; savings plans keep nothing.**
   From 1 February 2027 reservation exchange retires for services a savings plan also
   covers; the mechanics are in the liquidity table below and the operating rule in
   "Commitment liquidity after February 2027". Savings plans cannot be exchanged,
   cancelled or refunded, which is why phased purchasing matters most for them.

5. **Spot is not a commitment** - it is a market mechanism with a 30-second eviction
   notice and no SLA. It belongs in the compute cost strategy but should not be compared
   directly against commitment instruments.

6. **Legacy VM series can no longer be reserved at all.** As of the Learn retirement page
   (updated 25 September 2026), new and renewed one-year **and** three-year Reserved VM
   Instances are unavailable for the affected A, B, D, E, F and L variants of the v1 to
   v3 series. Existing reservations run to term and cannot be renewed; when they expire,
   coverage falls to pay-as-you-go unless a Compute Savings Plan absorbs it. The series also retire outright: Dv3, Dsv3, Ev3 and
   Esv3 (32 sizes) cannot be created, resized into, run or purchased after 15 November
   2029 (this retirement does not apply to Azure Government, 21Vianet or sovereign cloud
   regions). The other affected v1 and v2 series retire earlier: D, Ds, Dv2, Dsv2 and Ls
   on 1 May 2028, and Av2/Amv2, B (v1), F, Fs, Fsv2, G, Gs and Lsv2 on 15 November 2028,
   per the Learn retirement page.
   Capacity growth restrictions apply in the meantime (no new subscriptions, no quota
   increases), and a reservation gives no capacity assurance, so use an on-demand capacity
   reservation where capacity matters. The practical move is to migrate to v5 or later and
   exchange the reservation to the new series on the way (exchanges are unrestricted until
   1 February 2027; after that date each eligible reservation bought before it keeps one
   final exchange), or trade it in for a savings plan, rather than letting the reservation
   run out on a series that cannot be re-reserved. Source:
   https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/lifecycle/retirements-and-capacity-restrictions
   (read 2 October 2026). On the 2026-10-25 OptimToken catalogue, Azure's retail price
   API returns no reservation in eastus for B1s, B2s, F2s_v2 and F4s_v2, series this
   page names, so on those sizes the savings plan is the only commitment left. NC6s_v3
   has no reservation either, and the savings plan takes 26.7% off it at 1 year against
   32.2% on the CPU families. Current values:
   <https://optimtoken.optimnow.io/guides/savings-plans-vs-reserved-instances> (page) and
   <https://optimtoken.optimnow.io/guides/savings-plans-vs-reserved-instances/figures.json> (data).

**Reservation and Savings Plan liquidity mechanics (verified against Microsoft Learn, July 2026; exchange and trade-in rows re-checked 2 October 2026):**

| Mechanic | Fee | Annual cap | Notes |
|---|---|---|---|
| **Reservation exchange** | None | None | Same product family only. Does not count against the refund cap. **Retiring 1 February 2027 for services also covered by a savings plan** (VMs, Dedicated Host, App Service, and the covered databases). Reservations purchased before that date keep the right to one final exchange each. Because an exchange is processed as a cancel, refund, and repurchase, an exchange done after that date yields a non-exchangeable reservation. Reservations for services with no savings plan (such as Azure VMware Solution), for products that are deprecated and approaching end-of-life, and in clouds that do not support savings plans keep exchange. The end-of-life exclusion and the legacy VM retirement page (point 6) describe the v1 to v3 series differently; treat their exchange status as unsettled until Microsoft aligns the two pages. |
| **Reservation refund (cancellation)** | None today | $50,000 per 12-month rolling window per Billing Profile (MCA) or enrollment (EA). **The cap restores day-by-day** - 365 days after a refund, the original $50K is fully reinstated. | "Refund" and "cancellation" are the same operation in current docs. Microsoft reserves the right to introduce a 12% early-termination fee in future - verify before relying on liquidity. |
| **Reservation trade-in to Savings Plan** | None today | None | Convert RI to Savings Plan credit. No time limit, and the trade-in policy is unchanged by the 2027 exchange retirement. Up to 100 reservations per trade-in; the new savings plan's lifetime commitment must be at least the remaining commitment of the reservations returned. Microsoft does not charge an early-termination fee on trade-ins today but reserves the right to add one. Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/savings-plan/reservation-trade-in |
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
│   │       └── YES → Has it been right-sized? (finops-azure.md, rightsizing)
│   │           ├── NO → Right-size first. Do not commit to waste.
│   │           │
│   │           └── YES → Will it stay on the same VM family + region?
│   │               ├── YES → Is the VM series eligible for 1yr reservations?
│   │               │         (Check: older series may only support 3yr after
│   │               │         1 July 2026)
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
│
├── Azure Kubernetes Service (AKS)
│   │
│   ├── AKS node pools run on VMs → commitment applies to underlying VMs
│   │   (use VM decision tree above for node pool instances)
│   │
│   └── Spot and GPU node pools, autoscaler and pod rightsizing: see
│       finops-azure.md, "AKS optimisation in depth". Commit after those
│       are stable, not before.
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

For the operating rule after the exchange retirement, see "Commitment liquidity after
February 2027".

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
4. Term length is one you can hold (1yr vs 3yr).
5. No migration or decommission is planned in the window.

If any single dimension is uncertain, default to a savings plan. Family and region are the
hard new locks; size within the family stays flexible through ISF.

**Two refinements so the rule does not backfire:**

- **The default has a price, so size it.** A savings plan discounts roughly 7 points less
  than a reservation on compute (up to 65% vs up to 72%), and more on databases (up to 35%
  vs the reservation rate); on compute with no upfront, the median gap measured on the
  2026-10-25 OptimToken catalogue is 8.7 points at 1 year (point 3). That gap is the premium for the flexibility exchange used to
  provide for free. On a large, stable baseline it can reach six figures a year.
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

Spot offers up to 90% off pay-as-you-go for fault-tolerant, interruptible workloads:
batch, dev/test, CI/CD, stateless AKS pods, ML training with checkpointing. The
constraint is a 30-second eviction notice (2 minutes on AWS) and no SLA. Choose the
eviction policy (Deallocate keeps the disk, Delete is cheapest), cap the maximum price
at the pay-as-you-go rate, and track eviction rates by family and region. Spot is not a
commitment: it takes interruptible capacity out of the commitment equation (Layer 1 of
the layering strategy below).

### Instance size flexibility ratios come from the API, not the CSV

Since 9 May 2026 Microsoft no longer updates the public CSV of instance size
flexibility ratios; the ratios are published through the API and PowerShell only. A
tool that still parses the CSV reports reservation utilisation against stale ratios,
silently, as new SKUs ship, so check for one at the start of an Azure engagement.
Source: [Instance size flexibility for Azure Reservations](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/instance-size-flexibility)

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
  ↓ takes interruptible capacity out of the commitment equation
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

**Critical distinction:** A MACC is a binding obligation, not a forecast: a shortfall at
the end date or at a missed milestone is charged as an Azure prepayment credit. What
counts toward it, Marketplace eligibility and the shortfall cases are in
`finops-cloud-contracts.md` ("Azure: MACC and the Azure Commitment Discount").

**The optimisation paradox.** The MACC is typically sized based on current architecture
and projected growth. When a FinOps team then rightsizes VMs, decommissions idle
resources, and applies Reservations or Savings Plans, every dollar saved through
optimisation is a dollar that does not draw down against the MACC. The burndown rate -
how fast actual spend reduces the remaining commitment balance - starts to lag. If the
gap is significant, the final quarter becomes a scramble to close it.

This is the core tension: the MACC and the FinOps programme can quietly stop working
in the same direction unless burndown tracking is integrated into optimisation
reporting.

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

### Net discount under a MACC with an Azure Commitment Discount

Many MACC customers also hold an Azure Commitment Discount (ACD) on pay-as-you-go
consumption. The ACD does not apply to reservations or savings plans: they decrement the
MACC at their own price unless separate discount amendments on savings plan rates and on
named reservation families were asked for and written in. The ACD's reach is set by the
amendment's scope clause, and contracts differ: read it, then verify on the price sheet
(`unitPrice` against `marketPrice` on a reservation or savings plan purchase line).

The rule, with reservation discount `d` and ACD `a` on pay-as-you-go:

```
net discount           = 1 - (1 - d) / (1 - a)
break-even utilisation = (1 - d) / (1 - a)
```

Below the break-even utilisation the reservation loses money against discounted
pay-as-you-go. Worked at an illustrative `a = 10%` with West Europe list discounts
(Retail Prices API, 15 October 2026):

| Instrument | List discount `d` | Net discount at 10% ACD | Break-even utilisation |
|---|---|---|---|
| Blob Hot LRS 100 TiB, 1 year | 15-18% | 6-9% | 91-94% |
| Blob Hot LRS 100 TiB, 3 years | 31-34% | 23-27% | 73-77% |
| Premium SSD P30, 1 year | 5% | -6% | never |
| SQL Database GP Gen5 vCore, 1 year | 35% | 28% | 72% |
| SQL Database GP Gen5 vCore, 3 years | 55% | 50% | 50% |
| PostgreSQL Flexible GP Ddsv5 vCore, 1 year | 40% | 33% | 67% |
| PostgreSQL Flexible GP Ddsv5 vCore, 3 years | 60% | 56% | 44% |
| Fabric CU, 1 year | 40.5% | 34% (ACD alone); 27% with an illustrative 10% Fabric pay-as-you-go discount stacked | 66%; 73% stacked |

The sequencing consequence: shallow instruments (1-year storage, disk reservations,
the Savings Plan for Databases on provisioned SQL at 12-20%) drop to the bottom of the
list under a MACC, while deep instruments (3-year database and compute reservations)
keep most of their value. Advisor and the portal quote savings list against list and
do not apply this adjustment. One timing point: an upfront 3-year reservation bought in
the last MACC year decrements the commitment immediately for the whole term, a
legitimate lever against a forecast shortfall; a monthly-billed reservation only counts
the instalments that fall inside the MACC window.

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
- **Recommendation scope has caught up with purchase scope (29 September 2026).**
  Savings plan and reservation recommendations, including P3 reservations, are now
  produced at **management group** scope in the portal purchase flows and through
  the savings-plan and reservation recommendations REST endpoints. They aggregate the
  steady-state usage of every subscription under the group, which is the right input
  for a management-group-scoped purchase and removes the old workaround of summing
  per-subscription recommendations by hand (and over-committing, because each one
  targeted its own 80-90%). The calibration points above still apply: the figure is
  backward-looking, gross of AHB, and silent on planned decommissions. Source:
  https://techcommunity.microsoft.com/blog/finopsblog/now-available-management-group%E2%80%93scoped-savings-plan-and-reservation-recommendatio/4560869
  (Microsoft FinOps blog, 29 September 2026).
- **Conservative coverage targeting.** Recommendations target ~80-90% of observed usage.
  If the customer wants lower coverage for liquidity reasons (more PAYG buffer for
  workload changes), Advisor does not propose that profile.

**Operating pattern:** take Advisor's output as one input, validate against your own
calculation from the cost-plus-utilisation join, reconcile differences. Differences are
diagnostic - they usually reveal AHB not factored, scope mismatches, or workload context
Advisor cannot know.

**Agentic access.** Since August 2026 the Azure Resource Manager MCP server (preview)
exposes cost query and pricing tools, plus an optional Cost Management toolset with
reservation and savings plan insights. Agent-surfaced recommendations carry the same
calibration caveats; see "Agentic FinOps on Azure" in `finops-azure-billing.md`.
Sources: https://github.com/Azure/Azure-Resource-Manager-MCP (README),
https://techcommunity.microsoft.com/blog/finopsblog/cost-management-with-azure-resource-manager-mcp/4550182
(Microsoft FinOps blog, 25 August 2026).

Source: https://learn.microsoft.com/en-us/azure/advisor/advisor-reference-cost-recommendations

**Which products Advisor covers, and how to pull the feed.** Advisor emits reservation
recommendations for VMs, App Service, Dedicated Host, Azure VMware Solution, Azure Data
Explorer, Data Factory, Azure Files, managed disks, Blob storage (Blob v2 and ADLS
Gen2), Cosmos DB, Database for MySQL, Database for PostgreSQL, SQL PaaS databases,
Synapse (SQL DW), NetApp Files, Azure Cache for Redis, Red Hat and SUSE, Azure OpenAI
provisioned throughput and Microsoft Fabric, plus the compute and database savings
plans (Advisor cost recommendations reference, read 15 October 2026). Each
recommendation carries a term (P1Y or P3Y), a look-back period (7, 30 or 60 days), a
quantity and an annual saving quoted list against list per subscription. The REST
feed:

```
GET {scope}/providers/Microsoft.Consumption/reservationRecommendations?api-version=2026-06-01
    &$filter=properties/scope eq 'Shared' AND properties/resourceType eq '<type>'
             AND properties/lookBackPeriod eq 'Last60Days'
```

Scope is a subscription, resource group, billing account, billing profile or, through
the filter, a management group. Allowed `resourceType` values: VirtualMachines,
SQLDatabases, PostgreSQL, ManagedDisk, MySQL, RedHat, MariaDB, RedisCache, CosmosDB,
SqlDataWarehouse, SUSELinux, AppService, BlockBlob, AzureDataExplorer,
VMwareCloudSimple. Azure Files and Fabric are not in the API filter list: read those
from the portal purchase blade (Reservations > Add > product > Recommended tab). Two
more calibration points: every recommendation is gross of any MACC or EA discount (see
"Net discount under a MACC with an Azure Commitment Discount"), and a product's
recommendation appears only when the estimated saving clears Advisor's internal
threshold, so a missing 1-year blob recommendation next to a 3-year one says something
about the shallow 1-year discount, not about the data. Source:
https://learn.microsoft.com/en-us/rest/api/consumption/reservation-recommendations/list
(read 15 October 2026).

#### Mapping the floor to instruments

Once the always-on floor per SKU family and region is known (the join above), map it:

- High baseline + low variability + AHB-eligible Windows -> 3-year RI with AHB
- High baseline + low variability + Linux or non-AHB -> 1-year RI if the VM series
  supports it (verify post-July 2026 eligibility), otherwise 3-year RI if conviction
  is high
- Variable workload, stable $ floor -> 1-year Savings Plan sized below the floor (70-80%
  of it is a working estimate, not a published benchmark)
- Bursty / unpredictable -> PAYG with Spot for the spike layer
- Older VM series approaching retirement -> migrate to a newer generation, or commit
  via 3-year reservation if the workload must stay on the legacy series

Then validate against Advisor (above), buy in phased blocks ("Phased purchasing"
below), and re-evaluate quarterly against actuals rather than against Advisor's rolling
recommendation.

---

## Database commitment decision tree and fundamentals

### Database commitment decision tree

Azure offers two commitment instruments for database services, plus operational
optimisations that should be applied before any commitment purchase.

**Pre-commitment optimisation (do these first):**
1. Enable Azure Hybrid Benefit on all eligible SQL Database and SQL MI instances
2. Switch dev/test databases to SQL Serverless (auto-pause)
3. Stop PostgreSQL/MySQL Flexible Servers outside business hours
4. Consolidate small databases into Elastic Pools
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
    |         (A keel sized to the post-optimisation floor can be bought now:
    |         see finops-aws-commitments.md, keel commitment.)
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

**What cannot be reserved.** DTU-based SQL tiers (Basic, Standard, Premium); Azure
SQL Database serverless compute (Learn: "Reservation discounts don't apply to Azure
SQL Database serverless", read 15 October 2026); the PostgreSQL and MySQL Flexible
Server Burstable tier (only General Purpose and Memory Optimized have reservation SKUs
in the price list); Cosmos DB serverless; and the storage, backup, IOPS and licence
meters of every database service, since reservations cover compute vCores only. The
reservable base of a mid-size estate is therefore often a fraction of the "database"
line in Cost Management: size it from the vCore meters, not from the service total.

**Reservation units per service:**
- **SQL Database and SQL MI:** one vCore per region + service tier + hardware
  generation, with size flexibility within the tier and region, elastic pools
  included. Zone redundancy is a separate add-on reservation type ("vCore ZR"; read
  its rate from the Retail Prices API). Reservations cover the primary and the billable
  secondary replicas.
- **PostgreSQL Flexible:** one vCore per region + tier + compute series (Ddsv4,
  Ddsv5, Dsv6, Edsv5 and so on). Advisor includes zone-redundant HA standby vCores in
  its recommended quantity, which implies the standby compute is reservable
  (moderate confidence; Learn does not state it).
- **Cosmos DB:** fixed reservations in 100 RU/s units, 20% for 1 year and 30% for
  3 years below 1 M RU/s (larger quantities tier deeper; read the page), bought
  without a region but applied per region with ratios (most regions 1.0, France
  Central 1.25, France South 1.625); autoscale throughput consumes the reservation
  with a 1.5 multiplier; serverless and storage are excluded. Source:
  https://learn.microsoft.com/en-us/azure/cosmos-db/reserved-capacity (page dated
  27 April 2026).

**Sizing with daily data.** Unlike savings plans, database reservations are
count-based: Cost Management daily vCore-hours divided by 24 gives the vCores billed
per day, and the 90-day minimum (or P10) per key is the quantity to reserve. No hourly
join is needed (contrast "Why daily data hurts Savings Plan sizing more than RI
sizing" above). Under a MACC, apply the net-discount rule before ranking candidates.

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

**Scoping:** Subscription, resource group, management group, or entire billing
account.

**Purchase options:** Monthly or upfront payment, optional auto-renewal. Personalised
recommendations available in Azure Advisor and the Azure portal.

**Terms and coverage as published (Azure savings plans page and Redmondmag, 10 April
2026; both read 15 October 2026).** 1-year term only. Covered: Azure SQL Database
(provisioned, serverless and Hyperscale), SQL Managed Instance, Azure Database for
PostgreSQL, Azure Database for MySQL, Azure Cosmos DB, Azure DocumentDB and Database
Migration Service; SQL Server hourly licences on Azure VMs and Arc draw down the
commitment at 0% discount, as above. Indicative 1-year discounts: SQL Database
serverless 35%; SQL Database provisioned, PostgreSQL and MySQL about 20%; Cosmos DB
12% (Redmondmag table; the Azure page says "0% to 35%"). The plan cannot be modified
or cancelled. It combines with reservations, and the billing engine applies the
highest-percentage usage first; portal recommendations use the last 30 days of
pay-as-you-go usage. Position: this is the only commitment instrument that reaches
SQL serverless. On provisioned workloads a 3-year reservation beats it by a wide
margin, and under a MACC its 12-20% tiers lose most of their value (see "Net discount
under a MACC with an Azure Commitment Discount").

Database usage optimisation (serverless auto-pause, Flexible Server start/stop, elastic
pools, Cosmos DB autoscale) is in `finops-azure.md`, "Database optimisation patterns".

---

## Storage reserved capacity - Blob, ADLS Gen2, Files, managed disks

Storage is the commitment surface most Azure estates leave uncovered, and the one
where the discount shape differs most from compute: shallow 1-year terms, a strict
matching key, and an hourly use-it-or-lose-it model with no size flexibility. The
figures below are West Europe USD list prices from the Azure Retail Prices API
(queried 15 October 2026, `serviceName eq 'Storage' and armRegionName eq
'westeurope' and type eq 'Reservation'`), illustrative and dated; other regions and
redundancies follow similar ratios but must be read from the portal or the API.

| Instrument | Unit and term | Matching key | What is discounted | 1-year / 3-year discount (West Europe list, 15 October 2026) |
|---|---|---|---|---|
| Blob and ADLS Gen2 reserved capacity | 100 TiB or 1 PiB per month; 1 or 3 years; upfront or monthly | Region + access tier (Hot, Cool, Archive) + redundancy | "Data Stored" capacity meters only | Hot LRS 100 TiB 18% / 34%; Hot LRS 1 PiB 22% / 38%; Cool LRS 100 TiB 18% / 34%; Archive LRS 100 TiB 11% / 18% |
| Azure Files reserved capacity | 10 TiB or 100 TiB; 1 or 3 years | Region + tier (Premium, Hot, Cool) + redundancy | Provisioned (Premium) or stored capacity | Premium LRS 10 TiB 18% / 34%; Premium ZRS 10 TiB 18% / 34% |
| Premium SSD managed disk reservation | Per disk, P30 to P80 only; 1 year only | Region + disk SKU, no size flexibility | The disk's monthly rate | P30 to P80 LRS: 5% |

**Blob and ADLS Gen2.** Eligible: standard GPv2 and Blob storage accounts, block
blobs and ADLS Gen2. Not eligible: GPv1, premium block blob accounts, page blobs,
queues, tables (Azure Files has its own reservation, below). Cold does not appear in
the reservation documentation or the pricing grid; treat it as not reservable and
verify if a customer asks. The key is strict: a Hot LRS West Europe reservation covers
no Cool data, no ZRS data and no France Central data, so each key needs its own
reservation. Only the capacity meters are discounted; operations, bandwidth,
early-deletion and index charges stay pay-as-you-go. The reservation applies hourly:
hours above the reserved quantity bill at pay-as-you-go, unused reserved hours are
lost, and coverage resets every hour. Exchange is unlimited but storage-for-storage
only and goes through a support request; refunds sit inside the $50,000 rolling
12-month cap. No savings plan covers storage, so the 1 February 2027 exchange
retirement should not reach storage reservations (moderate confidence: the exchange
page does not name storage).

Sizing: take 90 days of daily stored capacity per key (Azure Monitor `BlobCapacity`
split by `BlobTier`, or the Cost Management "Data Stored" meter quantity), use the P10
as the floor, subtract any planned lifecycle tiering (Hot to Cool or Archive moves
shrink the Hot key), then count whole 100 TiB blocks. Tier first, reserve second: a
Hot reservation bought before a lifecycle policy lands locks a shrinking base for 1 or
3 years. Calibration: the 1-year blob discount is shallow (11 to 18%), and under a
MACC with an ACD on pay-as-you-go it collapses to single digits (see "Net discount
under a MACC with an Azure Commitment Discount"). The 3-year term is where blob
reservations carry value; the trade-off is a 3-year lock on the key that tiering
projects tend to shrink.

**Azure Files.** Units of 10 TiB and 100 TiB, 1 or 3 years, per region + tier
(Premium, Hot, Cool) + redundancy. Premium Files bill on provisioned GiB whether used
or not, so the base is very stable, which makes Premium Files a better reservation
candidate per TiB than blob. Sequence: shrink over-provisioned premium shares first
(provisioned v1 sizes shares for IOPS, so many are oversized), then reserve.
Whether the reservation applies to the provisioned v2 billing model
is not documented: verify before recommending it on v2 accounts.

**Premium SSD managed disks.** Premium SSD P30 to P80 only (P1 to P20 are listed as
"currently unavailable"), 1-year term only, LRS SKUs only in the price list (no ZRS
reservation SKU observed). Not eligible: Standard SSD and HDD, Premium SSD v2, Ultra,
unmanaged disks. The reservation is per disk SKU and region with no size flexibility
(a P40 reservation does not cover two P30 disks); quantity is the number of disks. It
applies hourly, and a disk in the "Reserved" state (attached to a deallocated VM)
still bills and still consumes the reservation. Calibration: any ACD above 5% erases the
5% list discount; under an illustrative 10% ACD the reservation costs about 6% more than
discounted pay-as-you-go. The disk
levers that pay are Premium to Standard SSD rightsizing where premium IOPS are not
needed, deleting unattached disks (`azure-orphan-disks` playbook) and reviewing disks
attached to long-deallocated VMs. A disk reservation only makes sense on a large,
stable P30+ fleet with no ACD or an ACD below 5%.

Sources: https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-reserved-capacity,
https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/understand-storage-charges
and https://learn.microsoft.com/en-us/azure/virtual-machines/disks-reserved-capacity
(all read 15 October 2026); https://azure.microsoft.com/en-us/pricing/details/storage/blobs/
and https://prices.azure.com/api/retail/prices (queried 15 October 2026).

---

## Commitment portfolio - phased purchasing

### Commitment portfolio liquidity

Commitment liquidity - the ability to reshape, rebalance, or exit your commitment
portfolio without wasting money - is as important as discount depth. Azure offers
more built-in liquidity mechanisms than AWS, but each has limits.

The mechanics themselves - exchange, refund and its $50,000 rolling cap, instance
size flexibility, trade-in to a savings plan, staggered expiry - are tabulated once in
"Reservation and Savings Plan liquidity mechanics" near the top of this file. Read
that table first, then the portfolio consequences below.

**The portfolio consequence.** Savings plans give usage flexibility (any family, any
region) and no financial liquidity. Reservations keep a refund within the $50,000
rolling cap and a trade-in to a savings plan, and for covered services that is all they
keep after 1 February 2027, so the refund cap becomes the main reshaping lever and binds
harder on large portfolios. It restores day by day: spread cancellations across the
window.

Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/exchange-and-refund-azure-reservations

**Size the first tranche at the keel commitment** - the usage level that has never
left the water across the trailing 12 months. Below the keel, committing needs no
forecast: that spend is already sunk. Every point of coverage above it is a bet on a
forecast, and belongs in the phased blocks below. Re-measure the keel quarterly; it
moves when workloads are decommissioned or migrated, not when traffic fluctuates,
and a falling keel is an early liquidity warning - on Azure doubly so after
1 February 2027, when the refund cap becomes the main reshaping lever.

**Divestiture risk.** If part of the estate could be sold or spun off within the term,
check what happens to each commitment when its subscription
leaves: see the "Commitments in a separation" table in
`finops-onboarding-workloads.md` ("Divestiture and separation").

### Phased purchasing

Avoid buying the full commitment in a single transaction. Purchase in blocks to create
a portfolio with staggered expiry dates. The cadence and block size should match
your consumption profile - not a fixed rule.

**Why phased purchasing matters on Azure:** smaller, staggered reservations keep each
change inside the $50,000 refund cap, and purchases can be timed to the MACC burndown
trajectory instead of an end-of-period scramble.

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

**3-year term phasing:** For 3-year commitments (deeper discounts), purchase in
smaller blocks (10-15%) at 6-month intervals. The longer the term, the smaller
each block should be.

**Portfolio management cadence:** at each purchase cycle, review utilisation and flag
any commitment below 80% before buying the next block; at each expiry, renew only what
the workload still justifies (Advisor's renewal recommendation is an input, not the
decision); quarterly, review coverage, instrument mix, MACC burndown and upcoming
expiries together.

**Commitment portfolio diagnostic questions:**
- What share of the portfolio expires in any single quarter? Above 30% (a working
  estimate), it is insufficiently diversified.
- How much of the $50,000 refund cap has been used in the last 12 months?
- Are savings plans covering workloads stable enough for reservations (about 7 points
  of discount left on the table)?
- Is MACC burndown reviewed in the same session as commitment purchasing?
- Are VM family migrations planned (for example to Dps/Eps) that would strand
  reservations? Favour savings plans there: after 1 February 2027 exchange can no
  longer rescue a stranded reservation on a covered service.

**Key metrics:**
- **Reservation/SP Utilisation:** Target >80% (a working estimate, not a published
  benchmark). Below this, the commitment is oversized.
- **Reservation/SP Coverage:** Target 70% (Walk maturity), 80%+ (Run maturity).
- **Effective Savings Rate (ESR):** savings generated / on-demand equivalent (ODE)
  spend, where ODE is what the covered usage would have cost with no discount
  applied: the FinOps Foundation definition, which decomposes as utilisation x
  coverage x discount. On FOCUS data, (sum of `ContractedCost` minus sum of
  `EffectiveCost`) / sum of `ContractedCost` per service. Name the denominator
  in use; the two give different numbers. An earlier version of this line
  defined ESR as actual savings over the theoretical maximum, which is a
  realisation ratio, not ESR. Sources: <https://www.finops.org/?p=16534> (FinOps Foundation playbook
  "How to Calculate Effective Savings Rate", updated 17 March 2026) and
  <https://focus.finops.org/docs/use-cases/v1-4/determine-effective-savings-rate-by-service/>
  (both read 15 October 2026).
- **Break-even period:** under 9 months for 1-year terms and 15 months for 3-year (a
  working estimate; compute it per instrument with the net-discount rule above).
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

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
