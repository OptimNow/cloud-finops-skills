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
| Reservations, Savings Plans, AHB, Spot, commitment decision trees, portfolio liquidity, MACC | `finops-azure-commitments.md` |
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
- Azure DevTest Labs auto-shutdown (simplest, shutdown only)
- **Start/Stop VMs v2** (Microsoft recommended, supports both start and stop)
- Azure Automation Runbooks (most customisable)
- Infrastructure as Code (Terraform `azurerm_dev_test_schedule`, Bicep)

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

The notice excludes the v1 and v2 VM series and the newest v7 series (Dsv7, Ddsv7,
Dlsv7, Dldsv7, Esv7, Edsv7), and a list of storage services that includes General Block
Blob, Standard Page Blob, Tables, Queues and Storage Bandwidth. Excluded from this notice
does not mean spared: a separate rise is reported for the v1 and v2 series, and Microsoft
has not confirmed it (see "Treat a rise on v1 and v2 as reported, not confirmed" below).
The notice does not name the affected subscriptions or resources, so exposure has to be
worked out from the estate.

What to do before the date:

- **Size the exposure.** Group the last three months of cost by region and meter
  category in Cost Management, keep the seven regions and the non-excluded VM series
  and storage meters, and apply the percentages. That gives the 2027 budget delta and
  shows whether it is material.
- **Decide on placement for movable workloads.** For dev/test and batch work, compare
  the post-increase price in these regions against a neighbouring region (Sweden
  Central against North Europe, for example) with the Retail Prices API, and count the
  egress and latency cost of moving. Data residency usually rules out a move for
  production data; it rarely rules it out for build agents and test environments.
- **Treat commitment protection as unconfirmed.** Several partners report that a
  reservation bought before 1 February 2027 keeps its price for the term, and that
  savings plans are not protected. Microsoft has not stated either in a public page;
  confirm with the account team before buying reservations early to beat the increase,
  and remember that reservation exchange rules change on the same date
  (`finops-azure-commitments.md`).
- **Treat a rise on v1 and v2 as reported, not confirmed.** Partner and vendor blogs
  report that the v1 and v2 series take a separate global rise of about 25% in place of
  the regional one; no Microsoft page states it, and the copies of the notice read for
  this file do not carry it (checked 11 November 2026). Give that figure only with this
  status, never as a rise Microsoft is applying, and keep it out of a budget until the
  customer has read the advisories in their own Service Health blade or has the account
  team's answer in writing. What Microsoft has published is narrower: its
  [VM lifecycle post](https://azure.microsoft.com/en-us/blog/enhancing-microsoft-azure-virtual-machine-lifecycle/)
  of 28 September 2026 says that series entering the End of Life stage "should expect
  changes to pricing and availability", with no figure, no date and no series named.

Sourcing note: the Service Health notice is visible only in customers' portals and has
no public Microsoft page. The region list, percentages and exclusions above are as quoted
from the notice in a [Microsoft Q&A thread](https://learn.microsoft.com/en-in/answers/questions/6026564/clarification-required-azure-vm-and-storage-pricin)
and reported consistently by partners ([Cloudy with a Chance of Licensing](https://cloudywithachanceoflicensing.com/2026/10/13/microsoft-increase-azure-prices-from-february-2027/),
[FinOps Weekly](https://finopsweekly.com/news/azure-updates-2026-10-08/)), all read 16
October 2026. Check the notice in the Service Health blade for the exact scope. The rise
reported for the v1 and v2 series is a separate matter with no such source behind it: its
status is in the last bullet above.

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
is reversed by an outage. This is a common cause of rightsizing rollbacks.

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

Log Analytics offers tiered commitment pricing for daily ingestion. Choosing a tier
above the steady ingestion floor is usually the largest saving with zero
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

**Source:** https://learn.microsoft.com/en-us/azure/aks/cluster-autoscaler-overview

### Node pool segregation

A single node pool serving everything is the most expensive layout. Segregate by
workload class:

- **System pool** - hosts kube-system pods (CoreDNS, metrics-server, konnectivity).
  Stable, non-evictable SKUs. Minimum D2s_v5 or B2ms, 2-3 nodes for HA. Keep it
  off Spot: its addons do not tolerate eviction.
- **General user pool** - Standard Linux nodes, on-demand or with conservative
  autoscaler. Default destination for pods without specific tolerations.
- **Spot user pool** - taint with `kubernetes.azure.com/scalesetpriority=spot:NoSchedule`,
  workloads must tolerate it explicitly. 60-90% saving on stateless or batch pods.
- **GPU pool** - separate pool for NC/ND-series with `nvidia.com/gpu` resource
  requests. Often Spot for training, on-demand for serving.

**Anti-pattern:** running the system pool on Spot. CoreDNS and metrics-server cannot
gracefully tolerate eviction, and a Spot reclaim event can destabilise the entire
cluster's control-plane addons. Keep the system pool on dedicated, non-evictable
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
