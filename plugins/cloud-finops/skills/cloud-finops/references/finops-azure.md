---
name: finops-azure
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Rate Optimization", "Architecting & Workload Placement"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "Procurement"]
fcp_maturity_entry: "Walk"
business_coverage: ["azure:waste:deep"]
questions:
  - q: "Azure Advisor says our VMs are fine, but they look oversized. What does Advisor miss?"
    section: "Advisor mechanics and the band Advisor misses"
  - q: "Which Azure VMs can we stop at night and at weekends, and how do we automate it?"
    section: "Automated start/stop"
  - q: "How do we cut Azure Log Analytics cost without losing the logs we need?"
    section: "Log Analytics cost control"
  - q: "How do we reduce AKS cost without hurting the apps running on it?"
    section: "AKS optimisation in depth"
  - "Nos VM Azure sont surdimensionnées mais Advisor ne dit rien : que vérifier ?"
  - q: "Azure prices rise on 1 February 2027: which VM series, disks and storage take the rise, and how do we size it?"
    section: "Region placement for cost"
  - q: "Hausse des prix Azure au 1er février 2027 : nos réservations, savings plans et Managed Disks sont-ils concernés ?"
    section: "Region placement for cost"
---

# FinOps on Azure

> Azure usage optimisation: compute rightsizing and Azure Advisor calibration, Log
> Analytics cost control, AKS optimisation and networking cost.
>
> Backup and snapshots, storage tiering and database optimisation, billing data,
> exports, allocation, governance and the EA-to-MCA transition, commitments
> (Reservations, Savings Plans, AHB, Spot, MACC) and the enumerated per-service pattern
> catalogue live in their own files - see the routing table below.
>
> Distilled from OptimNow Azure FinOps engagement experience and primary Microsoft
> sources (Azure Pricing pages, Cost Management documentation, FinOps Toolkit).

---

## Billing, commitments and the pattern catalogue live in their own files

| You want | Read |
|---|---|
| Backup and snapshot management, blob and disk storage tiering and lifecycle, database optimisation (Azure SQL, Postgres / MySQL Flexible Server, Cosmos DB) | `finops-azure-data.md` |
| Cost Management and FOCUS exports, Retail Prices API, FinOps Toolkit and hubs, billing scopes and allocation, tagging and Azure Policy, budgets, EA-to-MCA, agent access to cost data | `finops-azure-billing.md` |
| Reservations, Savings Plans, AHB, Spot, the compute commitment decision tree, portfolio liquidity, MACC | `finops-azure-commitments.md` |
| How much to commit, Advisor's commitment recommendations | `finops-azure-commitments-sizing.md` |
| Database and storage commitments | `finops-azure-commitments-data.md` |
| MACC and ACD negotiation, EA or MCA-E renewal, term sheet review | `finops-cloud-contracts.md` |
| The enumerated per-service inefficiency catalogue | `finops-azure-patterns.md` |
| A specific named waste pattern with a runnable detection query | `playbooks/azure-*.md` |


## Compute rightsizing

Start here: the VM cost model, SKU naming, family selection, automated start/stop,
generation upgrades and region placement. The Advisor mechanics below assume all of
this.

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
- VM auto-shutdown, a DevTest Labs schedule resource (simplest, a daily shutdown time,
  no start)
- **Start/Stop VMs v2** (supports both start and stop; still deployable, but Microsoft
  has frozen it: no further development beyond keeping its components on supported
  versions. The Automation-based v1 is deprecated)
- Azure Automation Runbooks (most customisable)
- Scheduled Actions API (`Microsoft.ComputeSchedule`): one-off Start, Deallocate or
  Hibernate on a batch of VMs, with nothing to deploy. It runs one operation, so
  something still has to call it each day
- Infrastructure as Code (Terraform `azurerm_dev_test_global_vm_shutdown_schedule` for a
  standalone VM; `azurerm_dev_test_schedule` only manages schedules inside a DevTest
  Lab. In Bicep, the `Microsoft.DevTestLab/schedules` resource)

Sources: [Start/Stop VMs v2 overview](https://learn.microsoft.com/en-us/azure/azure-functions/start-stop-v2/overview),
the [ComputeSchedule API](https://learn.microsoft.com/en-us/rest/api/computeschedule/)
and the [azurerm provider page](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/dev_test_global_vm_shutdown_schedule),
read 14 November 2026.

**Dev/Test pricing before scheduling.** Non-production subscriptions can sit on a
Dev/Test offer (Enterprise Dev/Test under an EA, Azure Plan for Dev/Test under an MCA,
Pay-As-You-Go Dev/Test for individuals): Windows VMs bill at Linux rates and SQL
Database, App Service and some other services get discounted rates. Every user needs an
active Visual Studio subscription (monthly cloud subscriptions do not qualify), the
resources may be used only for development and test, and there is no SLA. Moving dev
and test into such subscriptions is a rate lever that stacks with start/stop
([Azure Dev/Test pricing](https://azure.microsoft.com/en-us/pricing/offers/dev-test/),
read 9 November 2026).

**Tagging strategy for automation:** Use `startTime` and `stopTime` tags on VMs.
Automation reads tags to determine schedule. This allows per-VM scheduling without
modifying the automation logic.

**Measuring the hours a VM runs.** Resource Graph gives the power state now, not over a
month. For history, read the VM availability platform metric: 1 while the VM runs, 0
when it is unavailable, which includes a shutdown from inside the guest (the VM stays
allocated and billed), and no data once it is stopped from Azure. The hours at 1 over
30 days are the uptime a schedule tag should explain
([VM monitoring data reference](https://learn.microsoft.com/en-us/azure/virtual-machines/monitor-vm-reference#vm-availability-metric),
read 14 November 2026).

**Availability sets.** A deallocated VM gives up its capacity. Restarting part of an
availability set counts as adding VMs to it: the request has to be served by the
original cluster and can fail on capacity. Put the whole set on the same schedule
([allocation failures](https://learn.microsoft.com/en-us/troubleshoot/azure/virtual-machines/windows/allocation-failure),
read 14 November 2026).

### VM generation upgrades

Newer VM generations improve price/performance ratio. Examples:
- D2s_v3 -> D2s_v5: sometimes cheaper AND better performance
- E4_v3 -> E4as_v5: AMD variant gives further savings

Review VM generations quarterly and upgrade where possible.

### Region placement for cost

Azure pricing varies significantly by region. India is cheaper, Brazil is expensive.
Dev/test workloads can often use cheaper regions without user-facing impact.
Use the Retail Prices API to compare regions programmatically.

**Regional price increase from 1 February 2027 (announced October 2026).** Microsoft
notified customers through Azure Service Health that prices for Virtual Machines and
Azure Storage will rise in seven regions on 1 February 2027:

| Region | Increase |
|---|---|
| North Europe (Dublin) | 17% |
| France Central, France South | 11% |
| West Europe (Amsterdam), Norway East, Norway West | 9% |
| Southeast Asia (Singapore) | 8% |

**Which VM series take which rise.** The notice excludes from the regional rise the v1
series Bv1, D, Ds, F, Fs, G, Gs, L, NP and HCS, the v2 series Av2, Amv2, Dv2, Dsv2, Fsv2
and Lsv2, and six Intel v7 series (Dsv7, Ddsv7, Dlsv7, Dldsv7, Esv7, Edsv7). Every series
not on the list takes the regional rise, which is easy to misread in two places: the v3 to
v6 series, Dv3, Dsv3, Ev3 and Esv3 included (supported until 15 November 2029), and the
AMD v7 series (Dasv7, Easv7 and the rest). Excluded does not mean spared: the listed v1
and v2 series take a separate rise instead (status in the last bullet below).

| Series | Regional rise (seven regions) | Separate rise of about 25% (all regions) |
|---|---|---|
| Listed v1 and v2 series | No | Yes, as an account team states it |
| v3 to v6, and AMD v7 | Yes | No |
| The six listed Intel v7 series | No | No |

**Storage in scope.** The storage exclusions, as listed on the Microsoft Q&A thread below:
Azure Container Storage, Azure Managed Lustre, Azure NetApp Files Cross Region Replication
SKU, Blob Features, Change Feed, General Block Blob, Import/Export, Queues, Queues v2,
Standard Page Blob, Storage Actions, Storage Bandwidth, Storage Discovery, Tables and the
Transaction Optimized SKU. Two readings to get right:

- **Managed Disks take the rise.** They are not on the list, and the Standard Page Blob
  exclusion covers page blobs in storage accounts, not managed disks, which bill on their
  own meters.
- **Azure Files takes the rise except its Transaction Optimized tier**: Premium, Hot and
  Cool are in scope.

The thread leaves open whether general-purpose v2 (StorageV2) blob storage falls under
the General Block Blob exclusion: match the names on the list against the meter
subcategories in the price sheet, and ask the account team where they do not match. The
notice text names no subscription or resource, and an Impacted Resources tab, where the
advisory has one, is visible only in the customer's portal, so exposure is worked out
from the estate's cost data.

What to do before the date:

- **Size the exposure meter by meter.** Take three months of amortised cost, the price
  sheet (for the contract unit prices) and the reservation inventory with its expiry
  dates. Keep the seven regions and filter on meter subcategory or meter, not on meter
  category alone: managed disks, files and blob share the Storage category, and the
  exclusions are named at the finer level. Usage under a reservation takes the rise only
  from the reservation's expiry; pay-as-you-go usage and usage under a savings plan take
  it from 1 February. The result is the 2027 budget delta, phased by reservation expiry.
- **Apply the negotiated discounts to the new prices.** An ACD and service-specific
  discounts apply as a percentage of the list price in force, so to the new prices.
  Whether a contract caps the rise depends on its price-protection clause: the EA price
  guarantee and the Effective Price rule some ACD amendments carry are in
  `finops-cloud-contracts.md` ("Azure: MACC and the Azure Commitment Discount"), and
  MCA-E has no protection by default. No Microsoft statement on this rise addresses
  either, so read the clause and ask the account team.
- **Decide on placement for movable workloads.** For dev/test and batch work, compare
  the post-increase price in these regions against a neighbouring region (Sweden
  Central against North Europe, for example) with the Retail Prices API, and count the
  egress and latency cost of moving. Data residency usually rules out a move for
  production data; it rarely rules it out for build agents and test environments.
- **Know what a commitment protects.** A reservation bought before 1 February 2027 keeps
  its price to term, then its usage bills at the prices in force. It covers the compute
  meter only, so the VM's disks and software meters take whatever rise applies to their
  own meters. A savings plan keeps its hourly commitment in currency, but from 1 February
  that commitment covers less usage in these regions and the overflow bills at the new
  pay-as-you-go price: utilisation stays full while coverage falls. Buying reservations
  before the date to keep today's price fits stable usage only, weighed against the
  exchange retirement on the same date and the series that can no longer be reserved
  (`finops-azure-commitments.md`).
- **Migrate the listed v1 and v2 series rather than absorb their rise.** They retire
  anyway, NP and HC first on 31 May 2027, and they can no longer be reserved (dates and
  terms in `finops-azure-commitments.md`, "Compute commitment instruments", point 6). A move
  to v5 or later avoids both the rise and the retirement.
- **Know the status of what account teams state.** No Microsoft page states the rise on
  the listed v1 and v2 series. A written answer from a Microsoft account team to a
  customer in November 2026, consistent with what partners had reported, states that
  these series take about 25% from 1 February 2027 in every region, all sizes, in place
  of the regional rise and not on top of it; that reservations bought before the date
  keep their price to term; that a savings plan covers less usage from the date; and
  that the ACD applies to the new prices. Such messages state that they are for general
  information and do not bind Microsoft. Budget on the 25% once the customer has the same
  answer in writing from its own account team or reads it in its Service Health blade,
  and quote it as the account team's statement, not as a published price. What Microsoft
  has published is narrower: its
  [VM lifecycle post](https://azure.microsoft.com/en-us/blog/enhancing-microsoft-azure-virtual-machine-lifecycle/)
  of 28 September 2026 says that series entering the End of Life stage "should expect
  changes to pricing and availability", with no figure, no date and no series named.

Sourcing note: the Service Health notice is visible only in customers' portals and has
no public Microsoft page. The region list, percentages and VM exclusions above are as
quoted from the notice in a [Microsoft Q&A thread](https://learn.microsoft.com/en-in/answers/questions/6026564/clarification-required-azure-vm-and-storage-pricin),
the storage exclusions as listed in an answer on the same thread, and both were reported
consistently by partners ([Cloudy with a Chance of Licensing](https://cloudywithachanceoflicensing.com/2026/10/13/microsoft-increase-azure-prices-from-february-2027/),
[FinOps Weekly](https://finopsweekly.com/news/azure-updates-2026-10-08/)), all read 16
October 2026; the thread was read again on 20 November 2026. Check the notice in the
Service Health blade for the exact scope. What account teams state beyond the notice has
the status given in the last bullet above.

---


### Advisor mechanics and the band Advisor misses

Rightsizing precedes any commitment decision. Committing to an oversized fleet locks
in waste for one to three years. The Azure Advisor recommendation is the obvious
starting point - and, in the Azure estates OptimNow has reviewed, the most misleading
default in the Cost Management surface.

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
sees only a fraction of its rightsizing surface (5-15% is a working estimate; verify
in the estate); the remainder needs custom queries (see KQL pattern below) to surface.

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

**The lookback period is the setting that does change the analysis.** Advisor reads
the last 7 days by default; the configuration offers 14, 21, 30, 60 and 90 days, and
the list takes up to 48 hours to refresh after a change. Seven days misses a
month-end close or a weekly batch, so set 30 days or more before acting on a resize
list.

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
| Memory | `Available Memory Percentage` / `Available Memory Bytes` (platform metrics, no agent) or guest `\Memory\Available MBytes` | P95 > 85% utilisation (do not downsize) |
| Disk IOPS | `Data Disk IOPS Consumed Percentage` | P95 > 80% (consider disk SKU change, not VM) |
| Network | `Network In/Out Total` | Sustained at SKU bandwidth ceiling (do not downsize) |

A VM with 8% CPU but 95% memory pressure will OOM on a downsize - the cost saving
is reversed by an outage. This is a common cause of rightsizing rollbacks.

Two checks before applying a resize. Advisor verifies that its target SKU keeps the
Accelerated Networking and Premium Storage capabilities and exists in the region; it
documents no check on data disk or NIC counts, so compare those limits yourself. And
a resize restarts the VM, with a deallocation first when the target size is not
available on the hardware cluster hosting it: plan it as a disruptive change
([resize a VM](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/resize-vm),
read 14 November 2026).

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

If a Reservation is locked to a specific SKU and the workload is oversized,
instance size flexibility already covers smaller sizes within the same family, so a
downsize inside the family needs no action. Moving outside the family previously meant
exchanging the Reservation; for covered services that path closes on 1 February 2027, so
rightsize before committing rather than relying on a later exchange (non-covered services
such as VMware keep exchange). For Savings Plans (no exchange), rightsizing within covered
spend is free - the Savings Plan still applies to the smaller VM at the same hourly
commitment.

---

## Log Analytics cost control

In the mature Azure estates OptimNow has reviewed, Log Analytics is often the
second-largest cost line after compute and the most overspent. Default ingestion
settings, agent sprawl, and Sentinel layering compound quickly. The levers below
are listed in order of impact - work top-down.

### Lever 1: Commitment tiers (the quickest win)

Log Analytics offers tiered commitment pricing for daily ingestion. Moving a workspace
with steady ingestion onto the right tier is usually the largest saving with zero
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

Usage above the committed level is billed at the tier's own per-GB price, not at the
pay-as-you-go rate: a workspace on the 200 GB/day tier that ingests 300 GB pays 1.5
units of that tier. A day therefore costs more on a tier than on pay-as-you-go only
when it ingests less than the tier's break-even volume, the tier level times
(1 - discount): about 85 GB/day for the 100 GB/day tier at a 15% discount. Compare
the two bills day by day over the last 30-90 days (weekends and holidays are the low
days) instead of sizing on the floor; the workspace's Usage and estimated costs page
shows the estimate at each tier. A tier holds for 31 days from the day it is set or
raised: it can go up at any time, which restarts the 31 days, but not down, except
within 6 hours of the change. Tiers cover Analytics Logs ingestion only; Basic and
Auxiliary ingestion is billed at flat rates outside them.

Several workspaces that each sit under the break-even can share one tier through a
dedicated cluster: linked workspaces are billed on the cluster's commitment tier. A
cluster needs at least 100 GB/day, has no pay-as-you-go option and bills from the day
it is created, linked workspaces or not.

**Source:** https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs (read 14 November 2026)

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
- `ContainerLogV2` on AKS (high volume). Support for the v1 `ContainerLog` table
  retired on 30 September 2026, and v1 never accepted the Basic plan
  ([Container insights log schema](https://learn.microsoft.com/en-us/azure/azure-monitor/containers/container-insights-logs-schema))
- `AppTraces` at debug level
- Resource-specific tables such as `AKSAudit`, `AKSControlPlane`, `StorageBlobLogs`
  and `AZFWNetworkRule`

Three tables often put on this list do not qualify. `AzureDiagnostics` does not
support the Basic plan: the resource has to send its logs in resource-specific mode
(the destination-table choice of the diagnostic setting) to land in tables that do.
`W3CIISLog` does not support it either; filter it at source with a transformation
(Lever 3). `Heartbeat` carries no ingestion charge at all, like `AzureActivity`,
`Usage` and `Operation`, so there is nothing to save on it. Support is per table:
read the table's row in Microsoft's feature reference before planning a move.

Move the eligible tables to Basic where you keep them for short-window
troubleshooting. Use Auxiliary for compliance retention only on tables that
explicitly support it.

Sources: [table plans](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-table-plans),
[table feature support reference](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/basic-logs-azure-tables)
and [cost calculations, "Excluded tables"](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs#excluded-tables),
read 14 November 2026.

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

The same lever exists outside the workspace for network telemetry. Network Watcher VNet
flow logs filter at collection since October 2026 (general availability announced on
26 October): by direction, source and destination IP or CIDR, port, protocol, encryption
state and flow state, on a flow log targeting a VNet, subnet or NIC, changed in place
without recreating the log. The volume collected drives the per-GB Network Watcher
meter, the storage account and, with traffic analytics on, the per-GB processing charge,
so one filter cuts all three; a VNet-level log captures gateway traffic by default, which
is usually the first thing to exclude. Sources: [Azure Updates](https://azure.microsoft.com/en-us/updates?id=577782),
[VNet flow logs filtering](https://learn.microsoft.com/en-us/azure/network-watcher/vnet-flow-logs-filtering)
(read 9 November 2026; the Learn page still carried a preview banner on that date).

### Lever 4: Daily ingestion cap as circuit-breaker, not strategy

The workspace daily cap stops collection of billable data once the threshold is
reached, until a reset hour that differs per workspace and cannot be set. It is
useful only for runaway protection - a misconfigured agent or attack pattern flooding
the workspace. It is **not** a cost optimisation lever. Hitting the cap means
observability gaps for the rest of the day, and since 18 September 2023 those gaps
include security tables: the cap stops every billable data type, with no exemption
left for Defender for Servers data. Only Auxiliary-plan tables sit outside it. The
cap is not exact either: some data is collected past it and is still billed.

Nobody is notified by default. Reaching the cap writes an event (`_LogOperation`,
category `Ingestion`, detail containing `OverQuota`); the alert is a log search rule
to create on that event. Configure the cap at ~150% of the steady ingestion peak,
create the rule, and route it to the FinOps and SRE on-call channels.

**Source:** https://learn.microsoft.com/en-us/azure/azure-monitor/logs/daily-cap (read 14 November 2026)

### Lever 5: Archive tier and search jobs

Data older than the table's retention period can move to Archive for ~85% lower cost
than Analytics retention. Querying archived data requires a **search job** charged
per GB scanned, so the savings only hold if archive data is rarely queried.

Decision rule: if a table is queried less than once per quarter beyond its first
30 days, archive it. If it is queried weekly, keep it in Analytics retention - the
search-job cost will exceed the retention saving.

Retention is set per table, independently of the workspace default. 31 days of
analytics retention are included in the ingestion price, so setting a table below 31
days saves nothing; Application Insights tables keep 90 days at no charge. The paid
range runs to 730 days, and total retention with the long-term tier to 12 years. Keep
the workspace at the included period and extend only the tables that compliance names
([data retention](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure),
read 14 November 2026).

### Sentinel-on-LA layering

Microsoft Sentinel charges a **Sentinel premium** on top of the Log Analytics
ingestion cost. The two are entangled - cutting LA ingestion cuts the Sentinel bill
proportionally. Size the two together, because a change on one side moves the other:

- Tables in Basic plan are not eligible for most Sentinel analytics rules - confirm
  before moving security-relevant tables to Basic
- Sentinel commitment tiers exist separately from LA commitment tiers - both must
  be sized
- The DCR-level filtering applies before Sentinel sees the data, so source-side
  filtering is the most effective Sentinel cost lever

### KQL: top tables by ingestion

The first query on any LA cost engagement:

```kql
// Quantity is in MB; Microsoft's own usage queries divide by 1000 for GB
Usage
| where TimeGenerated > ago(30d)
| where IsBillable == true
| summarize GBIngested = round(sum(Quantity) / 1000, 2) by DataType
| order by GBIngested desc
```

Source for the conversion: [Analyze usage in a Log Analytics workspace](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/analyze-usage),
read 9 November 2026.

The distribution is skewed: a handful of tables, often 3-5, drive most of the
bill (70-80% is indicative, not a benchmark).
Address those first.

### KQL: ingestion trend by solution

```kql
Usage
| where TimeGenerated > ago(90d)
| where IsBillable == true
| summarize GBIngested = round(sum(Quantity) / 1000, 2)
            by Solution, bin(TimeGenerated, 1d)
| render timechart
```

Step-changes in the trend usually correlate with a deployment - new agent rollout,
new diagnostic setting, or a debug-level setting left enabled in production.

---

## AKS optimisation in depth

The compute commitment decision tree in `finops-azure-commitments.md` covers AKS at the layer of "node pools run on
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

The profile is cluster-wide: it applies to every autoscaled node pool and cannot be
set per pool. What is per pool is the minimum and maximum node count, the first thing
to read on a pool that never shrinks. A minimum left at the creation-time count is a
floor paid around the clock.

**Source:** https://learn.microsoft.com/en-us/azure/aks/cluster-autoscaler-overview

### Node pool segregation

A single node pool serving everything is the most expensive layout. Segregate by
workload class:

- **System pool** - hosts kube-system pods (CoreDNS, metrics-server, konnectivity).
  AKS sets the floor: a SKU of at least 4 vCPUs and 4 GB, no B-series, at least two
  nodes (three recommended). D4s_v5 is therefore the small end; a B2ms system pool
  is not a supported saving. Keep application pods off it with the
  `CriticalAddonsOnly=true:NoSchedule` taint, so they cannot inflate it.
- **General user pool** - Standard Linux nodes, on-demand or with conservative
  autoscaler. Default destination for pods without specific tolerations.
- **Spot user pool** - AKS adds the `kubernetes.azure.com/scalesetpriority=spot:NoSchedule`
  taint and the matching label itself; workloads must tolerate it explicitly. 60-90%
  saving on stateless or batch pods.
- **GPU pool** - separate pool for NC/ND-series with `nvidia.com/gpu` resource
  requests. Often Spot for training, on-demand for serving.

**The system pool cannot run on Spot.** AKS accepts Spot for user pools only, and a
Spot pool cannot be the cluster's default pool: CoreDNS and metrics-server do not
tolerate eviction. User pools, unlike the system pool, can scale to zero nodes.

Use **taints and tolerations** to steer pods. The Spot taint forces explicit opt-in,
so general workloads cannot pile onto cheap Spot nodes that evict during traffic
peaks.

**Tags for cost separation.** Tags set on a node pool reach its scale set and each
instance; tags set on the cluster do not reach the node pools. Disks and file shares
created through a StorageClass take their tags from its `tags` parameter, when the
volume is provisioned and not afterwards. Tag each pool, and set the StorageClass
tags, before relying on tags to split a cluster's bill.

**Sources:** [system node pools](https://learn.microsoft.com/en-us/azure/aks/use-system-pools),
[Spot node pools](https://learn.microsoft.com/en-us/azure/aks/spot-node-pool)
and [AKS tags](https://learn.microsoft.com/en-us/azure/aks/use-tags),
read 14 November 2026; https://learn.microsoft.com/en-us/azure/aks/use-multiple-node-pools

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

**The OS disk is a per-node line.** Where the node SKU supports it and no size is
set, AKS provisions an ephemeral OS disk, which carries no disk charge. Otherwise
each node gets a managed Premium disk whose default size follows the vCPU count:
128 GB up to 7 vCPUs, 256 GB from 8, 512 GB from 16 and 1,024 GB from 64. On an
autoscaled pool of large nodes that is one more line per node: choose a SKU whose
local storage holds an ephemeral disk, or set a smaller size explicitly
([AKS storage concepts](https://learn.microsoft.com/en-us/azure/aks/concepts-storage),
read 14 November 2026).

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

---

## Networking cost

Networking is a commonly underestimated cost line on multi-region or hub-spoke
architectures. The egress and peering charges are small per GB but
compound to material amounts on busy workloads.

> *Every rate in this section is an approximate list rate for a common region (eastus),
> read on the Azure Retail Prices API on 9 November 2026, and varies by region. They are here to show the relative weight of each
> charge - the per-GB peering charge landing on both sides, the NAT Gateway hourly floor -
> which is the part that stays true. Pull current rates from the Azure Retail Prices API
> before putting a number in a client model.*

### Egress pricing tiers

Outbound to internet, per-GB pricing decreases by volume (eastus list rates on the default
Microsoft-network routing, Retail Prices API read 9 November 2026; the Internet routing
preference is cheaper on every tier):

| Volume per month | Price per GB |
|---|---|
| First 100 GB | Free |
| 100 GB - 10 TB | $0.087 |
| 10 - 50 TB | $0.083 |
| 50 - 150 TB | $0.07 |
| Above 150 TB | $0.05 list; negotiated at volume |

Egress *between* Azure regions is charged separately at $0.02/GB outbound from the source
region (eastus, November 2026). **Source:** https://azure.microsoft.com/en-us/pricing/details/bandwidth/

### VNet peering - the multi-region surprise

VNet peering charges **on each side** - both ingress to peer and egress to peer: $0.01/GB
within a region, $0.035/GB for global peering between zone-1 regions (list rates read
9 November 2026). For a multi-region architecture peered through a hub VNet, every
cross-region byte is billed twice (once on each peering edge) at the global rate. On busy
hub-spoke designs, peering can be a meaningful share of the network bill.

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

NAT Gateway has two charges: **per-hour** ($0.045/hr) and **per-GB processed**
($0.045/GB), list rates read 9 November 2026. On AKS clusters defaulted to NAT Gateway
outbound:

- A 24/7 NAT Gateway costs ~$33/month idle at the November 2026 rate, before any traffic
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
| Cost | $0.01/hour per endpoint + $0.01/GB processed each way (list, November 2026) | Free |
| Network model | Private IP in your VNet | VNet allows access to public endpoint via Microsoft backbone |
| Cross-region | Supported | Same region only |
| Cross-tenant | Supported | Not supported |
| Security posture | Stronger - resource is reachable only from VNet | Weaker - public endpoint still exposed |

Per-endpoint cost is small individually but compounds. On a fleet of 200 storage
accounts with Private Endpoint enabled, the monthly bill is non-trivial (~$1,460 at the
November 2026 hourly rate, plus per-GB processing). Use Private Endpoint where compliance
requires it; use Service Endpoint for internal storage accounts where same-region access
is the only requirement.

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

## Key resources

- **Microsoft FinOps Toolkit:** https://github.com/microsoft/finops-toolkit
- **Azure FinOps Guide (community):** https://github.com/dolevshor/azure-finops-guide
- **Azure Cost Management docs:** https://docs.microsoft.com/azure/cost-management-billing/
- **FinOps Foundation Azure guidance:** https://www.finops.org/wg/azure/
- **Azure Retail Prices API:** https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
