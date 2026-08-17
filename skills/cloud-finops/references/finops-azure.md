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

## Commitments and the pattern catalogue live in their own files

| You want | Read |
|---|---|
| Reservations, Savings Plans, AHB, Spot, commitment decision trees, portfolio liquidity, MACC | `finops-azure-commitments.md` |
| The enumerated per-service inefficiency catalogue | `finops-azure-patterns.md` |
| A specific named waste pattern with a runnable detection query | `playbooks/azure-*.md` |


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

## Compute rightsizing

Start here: the VM cost model, SKU naming, family selection, automated start/stop,
generation upgrades and region placement. The Advisor mechanics below assume all of
this. (These two bodies of material previously sat ~1,200 lines apart in this file,
fundamentals *after* the advanced treatment - they are merged and reordered here.)

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


### Advisor mechanics and the band Advisor misses

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
instance size flexibility already covers smaller sizes within the same family, so a
downsize inside the family needs no action. Moving outside the family previously meant
exchanging the Reservation; for covered services that path closes on 1 February 2027, so
rightsize before committing rather than relying on a later exchange (non-covered services
such as VMware keep exchange). For Savings Plans (no exchange), rightsizing within covered
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

> *Every rate in this section is an approximate list rate for a common region, as of
> August 2026, and varies by region. They are here to show the relative weight of each
> charge - the per-GB peering charge landing on both sides, the NAT Gateway hourly floor -
> which is the part that stays true. Pull current rates from the Azure Retail Prices API
> before putting a number in a client model.*

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

## Agentic FinOps on Azure - Copilot agents and MCP servers

Microsoft is extending cost and usage intelligence beyond the portal into agent
workflows. As of July 2026, four surfaces matter for FinOps practitioners. They are
frequently conflated in coverage, so exact names matter. This is the Azure-native
counterpart to the MCP-based automation pattern documented in `finops-tagging.md`.

### Azure Copilot observability agent (GA June 2026)

Generally available since June 2026, with autonomous operations in public preview.
The agent continuously analyses telemetry (application topology, dependencies,
baseline behaviour), groups related alerts, begins investigations automatically, and
recommends next steps. It is an operations surface, not a billing surface - its
FinOps value is correlating "what changed" with deployment and configuration events.
It does not restart resources or change configuration on its own, and prompts and
responses are not used to train foundation models.

### Azure Resource Manager MCP Server (public preview)

A remote MCP server (hosted at `mcp.management.azure.com` - nothing to deploy) that
gives AI agents access to Azure estate data and ARM deployments. Microsoft marketing
also calls this the "Azure FinOps MCP Server" when framing cost scenarios - same
product, two names in the same announcement. Six tools in the preview, cleanly split:

| Half | Tools | FinOps relevance |
|---|---|---|
| Read (Azure Resource Graph) | `generate_query`, `validate_query`, `execute_query` | Tenant-wide estate queries in one call: cost-driver discovery by region/owner/workload, tag hygiene sweeps, orphaned-resource detection, rightsizing candidates |
| Write (ARM deployments) | `create_template_deployment`, `get_arm_template_deployment_status`, `cancel_arm_template_deployment` | Governed remediation: tag patches, cleanup templates - every deploy is an auditable ARM operation with a correlation ID |

**Permission model:** every operation runs in the context of the signed-in user -
no service principal, no separate agent credential. The agent's effective permissions
are exactly the human's, and Azure Policy assignments apply identically. Read-only
agents need Reader plus Resource Graph Reader on the target scope; deploy-capable
agents additionally need Contributor on the target resource groups.

**Determinism caveat for recurring agents:** `generate_query` is non-deterministic -
the same prompt can produce different KQL, different result sets, and therefore
different remediation actions on different runs. Microsoft's own PoC catalogue for
this server (24 agents, including a Cost Driver Finder, FinOps Rightsizer, Tag
Hygiene Czar, and Weekly Cleanup PRs) pins literal KQL in reviewed rules files and
uses the LLM only at dev time to draft queries. Adopt the same contract before
putting a recurring FinOps agent on these tools. Microsoft's observed pattern is
worth repeating verbatim: read-only agents are ~80% of the value at ~5% of the risk -
start there, and gate any write behind an explicit user verb, a confirm step showing
the resolved template and scope, and a freeze flag. This matches the
policy-generation-over-direct-mutation doctrine in `finops-agentic.md`.

### Azure MCP Server pricing tools

Distinct from the ARM MCP Server above: the **Azure MCP Server** (the `@azure/mcp`
developer server) includes a read-only pricing tool that queries Azure retail rates
by SKU, service, and region, with `Consumption`, `Reservation`, and
`DevTestConsumption` price types and optional savings-plan pricing. Its FinOps use is
**pre-deployment cost estimation inside the IDE**: extract resource types and SKUs
from a Bicep/ARM template, query per resource, and sum monthly cost (hourly rate x
730). This moves cost estimation from a post-deploy surprise to a design-time
constraint.

### FinOps hubs AI agents (FinOps Toolkit 14+)

FinOps hubs (see "FinOps Toolkit and FinOps Hubs" above) connect AI agents to the
hub's Data Explorer databases via the Azure MCP Server. Supported paths:

- **GitHub Copilot Agent mode** with Microsoft's downloadable FinOps hub instruction
  pack - engineers query FOCUS-normalised cost data in natural language (allocation,
  anomaly detection, forecasting, Effective Savings Rate quantification), with the
  KQL shown and approvable before execution
- **Copilot Studio agent template** (added in Toolkit 14, April 2026) - publishes a
  FinOps hub agent into Microsoft Teams or Microsoft 365 Copilot, aimed at finance,
  product, and leadership audiences rather than engineers
- **Any MCP client** (Claude, Continue, and others) - the hub connection is plain
  MCP; Microsoft's instruction pack is written for Copilot but reusable

Permission requirement: Database Viewer or greater on the hub's Data Explorer
databases. The usual freshness caveat applies - answers are only as current as the
last Cost Management export (typically every 24 hours), so ask the agent for the
last refresh time before trusting its numbers.

Sources (all Microsoft, as of July 2026):
https://azure.microsoft.com/en-us/blog/from-insight-to-action-the-next-phase-of-agentic-cloud-operations/,
https://techcommunity.microsoft.com/blog/azuregovernanceandmanagementblog/introducing-the-azure-resource-manager-mcp-server/4517521,
https://techcommunity.microsoft.com/blog/azuregovernanceandmanagementblog/arm-mcp-server-a-catalog-of-24-pocs/4519069,
https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/azure-pricing,
https://techcommunity.microsoft.com/blog/finopsblog/whats-new-in-finops-toolkit-14-%E2%80%93-april-2026/4519497,
https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/hubs/configure-ai

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

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
