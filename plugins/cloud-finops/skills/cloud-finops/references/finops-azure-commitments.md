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
questions:
  - q: "My Azure reservation exchanges stop working in 2027. What changes and what should I do before then?"
    section: "Commitment liquidity after February 2027"
  - q: "Azure Savings Plan or Reservation for our VMs: how do we choose?"
    section: "Savings Plan vs Reservation"
  - q: "How does a MACC change the real discount on our Azure reservations?"
    section: "Net discount under a MACC"
  - "Does Azure Hybrid Benefit stack with reservations, and who should track our licences?"
  - q: "Nos réservations Azure arrivent à échéance : on renouvelle, on bascule en Savings Plan ou on laisse courir ?"
    section: "Commitment liquidity after February 2027"
  - q: "Our Azure reservations are up for renewal. What changes if we renew before or after 1 February 2027?"
    section: "Commitment liquidity after February 2027"
  - q: "Does an Azure reservation guarantee us capacity, and what does a capacity reservation cost while it sits empty?"
    section: "On-demand capacity reservation"
  - q: "Should we pay for our Azure reservations and savings plans monthly or upfront, and does upfront buy a bigger discount?"
    section: "Savings Plan vs Reservation"
---

# Azure Commitment Discounts

> Azure rate-optimisation instruments and the decisions around them: Reservations,
> Savings Plans, Azure Hybrid Benefit, Spot, the compute commitment decision tree,
> portfolio liquidity under the 1 February 2027 exchange retirement, phased purchasing,
> and MACC alignment (MACC negotiation is in `finops-cloud-contracts.md`). How much to
> commit and how to calibrate Advisor: `finops-azure-commitments-sizing.md`. Database
> and storage commitments: `finops-azure-commitments-data.md`. For Azure billing data,
> allocation and governance, see `finops-azure-billing.md`; for rightsizing and service
> optimisation, `finops-azure.md` and `finops-azure-data.md` (backup, storage, databases).

---

## Commitment discounts

### Compute commitment instruments

Azure provides four distinct instruments for reducing compute costs, plus Azure Hybrid
Benefit which acts as a licensing overlay. As with AWS, these instruments are designed
to be layered, not chosen in isolation.

**Instrument comparison:**

| Instrument | Discount depth | Flexibility | Commitment type | Term | Covers |
|---|---|---|---|---|---|
| Azure Reservation | Up to 72% | Lowest - locked to VM family, region, size | Resource-based (specific SKU) | 1yr or 3yr (see note) | VMs, Dedicated Hosts, App Service (Premium v3 and later, Isolated v2), specific services |
| Azure Savings Plan for Compute | Up to 65% | High - any VM family, region, size | Spend-based ($/hr) | 1yr or 3yr | VMs, Dedicated Hosts, Container Instances, Container Apps, App Service (Premium v3 / Isolated v2), Functions Premium |
| Azure Hybrid Benefit (AHB) | Up to 40% (Windows), 55% (SQL) | Highest - no commitment, no lock-in | Licensing overlay | None | VMs, SQL Database, SQL MI, Red Hat/SUSE Linux |
| Spot Virtual Machines | Up to 90% | Variable - can be evicted with 30s notice | None (market-priced) | None | VMs, VMSS, AKS node pools |

**Note on legacy Reserved VM Instances:** from 1 July 2026 the affected v1 to v3 series lose some or all reservation terms, and Microsoft's two Learn pages disagree on which; see point 6.

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
   resource-specific), Compute Savings Plans also cover Container Instances, Container
   Apps, the Functions Premium plan and App Service Premium v3 / Isolated v2. If you
   run a mix of VMs, containers, and App Service, a Compute Savings Plan is the only
   instrument that covers all three. App Service reservations exist for Premium v3
   and later and for Isolated v2 only ([savings plans](https://learn.microsoft.com/en-us/azure/cost-management-billing/savings-plan/savings-plan-overview),
   [App Service reserved instances](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/prepay-app-service),
   read 14 November 2026).

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
   <https://optimtoken.optimnow.io/guides/savings-plans-vs-reserved-instances/figures.json> (data);
   with the cloud-finops MCP, `get_live_figures("savings-plans-vs-reserved-instances")`.

4. **Reservations keep a capped refund and trade-in; savings plans keep nothing.**
   From 1 February 2027 reservation exchange retires for services a savings plan also
   covers; the mechanics are in the liquidity table below and the operating rule in
   "Commitment liquidity after February 2027". Savings plans cannot be exchanged,
   cancelled or refunded, which is why phased purchasing matters most for them.

5. **Spot is not a commitment** - it is a market mechanism with a 30-second eviction
   notice and no SLA. It belongs in the compute cost strategy but should not be compared
   directly against commitment instruments.

6. **Legacy VM series can no longer be reserved at all.** Microsoft's two Learn pages
   disagree. The transition guide (dated 1 May 2026) ends one-year RIs from 1 July 2026
   for Av2, Amv2, Bv1, D, Ds, Dv2, Dsv2, F, Fs, Fsv2, G, Gs, Ls and Lsv2, and both terms
   for Dv3, Dsv3, Ev3 and Esv3:
   https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/manage-legacy-vm-reservations-after-july-1-2026.
   The later retirement page (dated 25 September 2026) makes new or renewed one-year and
   three-year RIs unavailable for all affected A, B, D, E, F and L variants of v1 to v3.
   Plan on the later page and confirm the term in the purchase blade before buying.
   Existing reservations run to term and cannot be renewed; when they expire,
   coverage falls to pay-as-you-go unless a Compute Savings Plan absorbs it. The series also retire outright: Dv3, Dsv3, Ev3 and
   Esv3 (32 sizes) cannot be created, resized into, run or purchased after 15 November
   2029 (this retirement does not apply to Azure Government, 21Vianet or sovereign cloud
   regions). The other affected v1 and v2 series retire earlier: NP and HC on 31 May 2027
   (NP reservations ended on 2 April 2026), D, Ds, Dv2, Dsv2 and Ls on 1 May 2028, and
   Av2/Amv2, B (v1), F, Fs, Fsv2, G, Gs and Lsv2 on 15 November 2028, per the Learn
   retirement page (read 20 November 2026).
   Capacity growth restrictions apply in the meantime (no new subscriptions, no quota
   increases); for capacity assurance see "On-demand capacity reservation" below. The practical move is to migrate to
   v5 or later and
   exchange the reservation to the new series on the way (exchanges are unrestricted until
   1 February 2027; after that date each eligible reservation bought before it keeps one
   final exchange), or trade it in for a savings plan, rather than letting the reservation
   run out on a series that cannot be re-reserved. Source:
   https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/lifecycle/retirements-and-capacity-restrictions
   (read 2 October 2026). On the 2026-10-25 OptimToken catalogue, Azure's retail price
   API returns no reservation in eastus for B1s, B2s, F2s_v2 and F4s_v2, series this
   page names, so on those sizes the savings plan is the only commitment left. NC6s_v3
   has no reservation either, and the savings plan takes 26.7% off it at 1 year against
   32.2% on the CPU families. Current values: same sources as point 3.

**Reservation and Savings Plan liquidity mechanics (verified against Microsoft Learn, July 2026; exchange and trade-in rows re-checked 2 October 2026):**

| Mechanic | Fee | Annual cap | Notes |
|---|---|---|---|
| **Reservation exchange** | None | None | Same product family only. Does not count against the refund cap. **Retiring 1 February 2027 for services also covered by a savings plan** (VMs, Dedicated Host, App Service, and the covered databases). Reservations purchased before that date keep the right to one final exchange each. Because an exchange is processed as a cancel, refund, and repurchase, an exchange done after that date yields a non-exchangeable reservation. Reservations for services with no savings plan (such as Azure VMware Solution), for products that are deprecated and approaching end-of-life, and in clouds that do not support savings plans keep exchange. The end-of-life exclusion and the legacy VM retirement page (point 6) describe the v1 to v3 series differently; treat their exchange status as unsettled until Microsoft aligns the two pages. |
| **Reservation refund (cancellation)** | None today | $50,000 per 12-month rolling window per Billing Profile (MCA) or enrollment (EA). **The cap restores day-by-day** - 365 days after a refund, the original $50K is fully reinstated. | "Refund" and "cancellation" are the same operation in current docs. Microsoft reserves the right to introduce a 12% early-termination fee in future - verify before relying on liquidity. |
| **Reservation trade-in to Savings Plan** | None today | None | Convert RI to Savings Plan credit. No time limit, and the trade-in policy is unchanged by the 2027 exchange retirement. Up to 100 reservations per trade-in; the new savings plan's lifetime commitment must be at least the remaining commitment of the reservations returned. Microsoft does not charge an early-termination fee on trade-ins today but reserves the right to add one. Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/savings-plan/reservation-trade-in |
| **Savings Plan cancel / exchange / refund** | N/A | N/A | Not allowed. SPs are non-refundable, non-exchangeable, non-cancellable. |

Source: https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/exchange-and-refund-azure-reservations

### On-demand capacity reservation - billed when unused

A reservation discounts; only an on-demand capacity reservation holds capacity. It
reserves a VM size in a region or zone under an SLA, with no term: create and delete it
at will. It bills at the VM's pay-as-you-go rate from creation, used or not; a VM running
in it is billed in its place, not on top. A VM uses it only if it names the capacity
reservation group: without that, you pay the empty reservation and the VM. Reservations
and savings plans discount its used and unused quantity alike. Not offered for Spot,
dedicated hosts or availability sets, nor for the ND, NCads H100 v5, HB and HC series
([capacity reservation](https://learn.microsoft.com/en-us/azure/virtual-machines/capacity-reservation-overview),
read 26 November 2026).

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
│   │               ├── YES → Is the VM series still reservable?
│   │               │         (affected v1 to v3 series are not; point 6)
│   │               │         ├── YES → Azure Reservation (up to 72%)
│   │               │         │         Deepest discount. From 1 Feb 2027 covered
│   │               │         │         services can't be exchanged, so reserve only
│   │               │         │         at high conviction on family, region, and term.
│   │               │         │         Size stays flexible within the family via ISF.
│   │               │         │
│   │               │         └── NO → Savings Plan, or migrate to a newer
│   │               │                  series and reserve there
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
│       - Reservations and Savings Plans discount; neither guarantees capacity
│       - To hold capacity: on-demand capacity reservation (above), where offered
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
│   │   - Reservations also available for both (Premium v3 and later, Isolated v2)
│   │
│   └── Legacy plans (V2) → migrate to V3 first for better price-performance,
│       then evaluate commitment on the new tier
│
├── Azure Functions
│   │
│   ├── Consumption Plan → pay per execution, no commitment available
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
│   └── Savings Plan for Compute covers Container Instances; commit only
│       on sustained usage, short-lived or burst containers stay on PAYG
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
Both take the same scopes (subscription, resource group, management group, shared) and
monthly or upfront payment. **The total is the same either way, with no fee for paying
monthly**: upfront buys no extra discount, unlike AWS, so pay monthly unless MACC timing
argues otherwise ("Net discount under a MACC", last paragraph). Under an MCA billed
outside USD each instalment moves with the month's exchange rate. Cancelling a
monthly-paid reservation counts its remaining payments towards the $50,000 refund cap;
SUSE, Red Hat and pre-purchase plans are upfront only
([buy a reservation](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/prepare-buy-reservation)
and, for savings plans, the overview cited in point 2; read 26 November 2026).
Exchange, refund and trade-in are in the liquidity table
above; the operating rule after the exchange retirement follows.

### Commitment liquidity after February 2027

This rule applies to services also covered by a savings plan. Free, uncapped exchange,
the escape hatch that made reservations safe at moderate confidence, retires for them on
1 February 2027. What remains is a refund capped at $50,000 per 12-month rolling window
and a one-way trade-in to a savings plan. Savings plans give usage flexibility (any
family, any region) and no financial liquidity.

<!-- Deliberate mirror of finops-azure.md, "Region placement for cost": a reservation
purchase or renewal question is routed to this file alone, so the rise is stated here and not
only pointed to. Change the figures in both files together. -->
**The same date brings a regional price rise.** From 1 February 2027 Virtual Machine and
Azure Storage prices rise in seven regions: North Europe (Dublin) 17%, France Central
and France South 11%, West Europe (Amsterdam), Norway East and Norway West 9%, Southeast
Asia 8% (Azure Service Health notice, October 2026). A reservation bought or renewed
before the date keeps today's price to term on the compute meter only (the VM's disks
take the rise), and a savings plan's hourly commitment covers less usage in these regions
from the date. Renewing early to keep today's price fits stable usage only: the five
locks below decide it. Which series take which rise, the storage meters in scope and how
to size the exposure: `finops-azure.md`, "Region placement for cost".

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
  than a reservation on compute (measured gap in point 3), and more on databases (up to
  35% vs the reservation rate). That gap is the premium for the flexibility exchange used
  to provide for free; on a large, stable baseline it can reach six figures a year.
  Reserve the certain floor; do not surrender its depth out of caution.
- **At Crawl and Walk maturity, the fallback is often more PAYG buffer, not a bigger
  savings plan.** Azure bills daily while a savings plan is sized on an hourly floor (see
  "Why daily data hurts Savings Plan sizing more than RI sizing" in
  `finops-azure-commitments-sizing.md`), and a savings plan has
  zero liquidity to unwind an over-commitment. Teams that cannot yet build the
  cost-plus-utilisation join should hedge the uncertain slice with a wider PAYG buffer,
  plus AHB and Spot where they fit, until they can size the hourly floor with confidence.

### Spot Virtual Machines

Beyond the table and the decision tree: the eviction notice is 30 seconds (2 minutes on
AWS). Choose the eviction policy (Deallocate keeps the disk, Delete is cheapest), cap
the maximum price at the pay-as-you-go rate, and track eviction rates by family and
region. B-series and promo sizes cannot run as Spot. Before choosing a size and a
region, read the Spot Placement Score (High, Medium or Low, for up to eight regions
and five sizes) and the price history and eviction rates Azure publishes per size and
region, in the portal and in the Resource Graph `SpotResources` table
([Spot VMs](https://learn.microsoft.com/en-us/azure/virtual-machines/spot-vms),
[Spot Placement Score](https://learn.microsoft.com/en-us/azure/virtual-machine-scale-sets/spot-placement-score),
read 14 November 2026).

**Spot plus (public preview, announced 17 November 2026)** is a tier between Spot and
pay-as-you-go. It targets at least 60 minutes of runtime on a best-effort basis while
remaining evictable, gives up to 2 minutes' eviction notice, sends rebalance
notifications when eviction risk rises (typically 30 seconds to 15 minutes ahead), and
is not charged for a VM that Azure evicts to reclaim capacity within its first 60
minutes. Microsoft says only that it costs more than standard Spot and stays well below
pay-as-you-go: no ratio is published. The premium buys the longer notice and the
no-charge rule, so it suits work that checkpoints within the hour or needs more than 30
seconds to drain. Compare its rate with the standard Spot rate plus the expected cost
of re-running evicted work, not with pay-as-you-go. The no-charge rule is stated for
capacity evictions only, so do not count on it for a VM you delete yourself. It runs on
single VMs and scale sets (Flexible or Uniform) with `SpotPlus` priority, on API version
2026-04-01 or later, once the subscription is registered for the preview; the
announcement does not mention AKS node pools
([Azure Updates](https://azure.microsoft.com/updates?id=581145), read 28 November 2026).

### Instance size flexibility ratios come from the API, not the CSV

Since 9 May 2026 Microsoft no longer updates the public CSV of instance size
flexibility ratios; the ratios are published through the API and PowerShell only. A
tool that still parses the CSV reports reservation utilisation against stale ratios,
silently, as new SKUs ship, so check for one at the start of an Azure engagement.
The FinOps toolkit's Power BI reports, workbooks and Azure Optimization Engine are such
tools before release 15 (October 2026), which replaced the file with an open data
file built from the Reservations catalogue API.
Sources: [Instance size flexibility for Azure Reservations](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/instance-size-flexibility),
[toolkit v15 release notes](https://github.com/microsoft/finops-toolkit/releases/tag/v15) (read 16 November 2026)

### Compute commitment layering strategy

**Discount application order (Azure-defined):** Azure Hybrid Benefit removes the licence
component first; Spot usage is market-priced; reservations apply to matching
pay-as-you-go usage; savings plans then apply to the remaining eligible usage. MACC is
not in this order: it is a burn-down construct, not a metered discount (next section).

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
  them does not "double-discount" but does pull commitment forward. A burndown
  computed from amortised cost with purchases removed (as the FinOps toolkit's
  catalogue query does in release 15) understates and delays it.

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
- Report MACC burndown rate beside ESR (Effective Savings Rate) and coverage, in the
  same session as the optimisation metrics. Burndown slowing while ESR improves is the
  signal to act
- Keep procurement and FinOps in the same cadence review at least quarterly
- Keep a forward list of planned software purchases with MACC and Marketplace
  eligibility confirmed at planning time, paced to the burndown trajectory
- Do not buy Marketplace products because they count: they bring vendor, licence and
  integration costs that were never in the business case

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

---

## Commitment portfolio - phased purchasing

### Commitment portfolio liquidity

Liquidity, the ability to reshape or exit the portfolio without wasting money, matters
as much as discount depth. The mechanics are in the liquidity table near the top. The
portfolio consequence: for covered services after 1 February 2027 the $50,000 refund
cap becomes the main reshaping lever and binds harder on large portfolios. It restores
day by day, so spread cancellations across the window.

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

**Azure-specific consideration:** mid-term exchange, an extra liquidity layer on top of
staggered expiry, disappears for covered services on 1 February 2027 (it stays for
non-covered services such as VMware). Weekly buyers may prefer savings plans to avoid
the overhead of frequent reservation management.

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
  `EffectiveCost`) / sum of `ContractedCost` per service, commitment purchase
  rows excluded from both sums (`finops-allocation-showback.md`, "Measuring savings
  from the cost columns"). Name the denominator in use; the two give different numbers. Actual savings over the theoretical
  maximum is a realisation ratio, not ESR. Sources: <https://www.finops.org/?p=16534> (FinOps Foundation playbook
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
- [ ] Bought through a partner (MCA Partner): who buys, exchanges and cancels is
      settled, see "Who can buy a commitment under MCA Partner" in `finops-azure-billing.md`

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
