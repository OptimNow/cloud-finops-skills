---
name: finops-azure-data
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Rate Optimization", "Architecting & Workload Placement"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "Procurement"]
fcp_maturity_entry: "Walk"
business_coverage: ["azure:waste:deep"]
questions:
  - q: "Our Azure backup and snapshot bill keeps growing. Where does the waste sit?"
    section: "Snapshot and backup management"
  - q: "Which blob data should move to the cool, cold or archive tier, and when does moving it cost more than it saves?"
    section: "Storage tiering and lifecycle"
  - q: "Soft delete and versioning are switched on for our storage accounts. What are they costing us?"
    section: "Soft delete and versioning"
  - q: "Our Azure SQL databases sit idle most of the day. Serverless, an elastic pool, or leave them as they are?"
    section: "Database optimisation patterns"
  - q: "Should our Cosmos DB containers run on autoscale or on manual throughput?"
    section: "Cosmos DB - autoscale vs manual throughput"
  - "Notre facture de stockage et de bases de données Azure augmente : par où commencer ?"
---

# FinOps on Azure: storage, backup and databases

> Azure usage optimisation for data at rest: backup and snapshot management, blob and
> disk storage tiering and lifecycle, and database optimisation (Azure SQL,
> Postgres/MySQL Flexible, Cosmos DB).
>
> Compute rightsizing, Log Analytics, AKS and networking are in `finops-azure.md`.
> Billing data, commitments and the enumerated per-service pattern catalogue live in
> their own files - see the routing table below.
>
> Distilled from OptimNow Azure FinOps engagement experience and primary Microsoft
> sources (Azure Pricing pages, Cost Management documentation, FinOps Toolkit).

---

## Compute, billing, commitments and the pattern catalogue live in their own files

| You want | Read |
|---|---|
| Compute rightsizing and Advisor calibration, Log Analytics cost control, AKS, networking cost | `finops-azure.md` |
| Cost Management and FOCUS exports, billing scopes and allocation, tagging and Azure Policy, budgets | `finops-azure-billing.md` |
| Database Reserved Capacity, storage reserved capacity and the database commitment decision tree | `finops-azure-commitments.md` |
| The enumerated per-service inefficiency catalogue | `finops-azure-patterns.md` |
| A specific named waste pattern with a runnable detection query | `playbooks/azure-*.md` |


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
- **Continuous backup** - the 7-day tier has no backup storage charge; the 30-day
  and 35-day tiers bill backup storage per GB of data per region. Every tier charges
  per GB restored, each time a restore runs. A 30-day or 35-day tier left on after a
  one-time PITR test is the cost to audit
  ([continuous backup](https://learn.microsoft.com/en-us/azure/cosmos-db/continuous-backup-restore-introduction),
  read 9 November 2026).

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

Storage accounts created in the Azure portal have **soft delete enabled by
default** (containers, blobs, file shares) with 7-day retention; accounts created
with the CLI, PowerShell or a template have it off unless the template sets it.
Without versioning, blob soft delete also keeps every overwrite as a soft-deleted
snapshot. Versioning, when enabled, retains every overwrite as a separate billable
version with no expiry of its own.

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

Soft-deleted blobs are not pruned by lifecycle rules: they are purged when the
retention window expires, so the retention setting itself is the lever. Match
the window to the actual incident-recovery use case, not a default 365 days.
Detection loop, sizing via Blob Inventory and the blocker list (point-in-time
restore, object replication, immutability) are in the playbook
[azure-blob-version-and-soft-delete-sprawl](../playbooks/azure-blob-version-and-soft-delete-sprawl.md);
the tier-down decision on the bytes that survive is in
[azure-blob-cold-data-in-hot](../playbooks/azure-blob-cold-data-in-hot.md).

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

## Database optimisation patterns

Azure SQL, Postgres / MySQL Flexible Server, and Cosmos DB each have their own
sizing levers. The commitment-side guidance is in the database commitment decision tree in
`finops-azure-commitments.md`;
the levers below are the architectural and configuration changes that should
happen **before** any Database Reserved Capacity purchase.

### Azure SQL Serverless auto-pause

Azure SQL Database Serverless tier scales compute automatically and **pauses to
zero compute charge** after an idle period:

- Min vCore configurable from 0.5
- Auto-pause delay - General Purpose: 15 minutes to 7 days (default 60); Hyperscale
  (auto-pause in preview as of 2 October 2026): 60 minutes to 7 days; `-1` disables
- Storage continues to bill while paused; compute charges drop to zero
- **Several features silently prevent auto-pause**: long-term backup retention (LTR),
  geo-replication, failover groups and a server DNS alias. Open sessions are the most
  common blocker in practice. A database that never pauses only saves the autoscale gap,
  so check these before counting the pause in a business case

**Best fit:** dev/test databases, intermittent internal tools, departmental apps,
QA environments.

**Common trap:** resume generally takes about a minute, and the first connection after a
pause fails with error 40613, so clients need retry logic. Not appropriate for
latency-sensitive production workloads or any workload behind a user-facing transaction.

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

**Sources:** https://learn.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-overview
and https://learn.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-auto-pause-resume
(both read 2 October 2026).

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
- **Serverless Hyperscale can pause** to storage-only billing (preview as of 2 October
  2026), with a 60-minute minimum delay, and named replicas are not supported with
  auto-pause. A General Purpose serverless database with a delay under 60 minutes comes
  out of an upgrade to Hyperscale with auto-pause disabled; reset the delay after the
  upgrade

**Threshold rule:** consider Hyperscale once a database is >4 TB or when read
replica scale-out is needed. Below that, General Purpose or Business
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
  RU/s and bills each hour for the highest RU/s it scaled to (never below 10% of the
  maximum), at **1.5x the manual rate per RU/s**.

Decision rule (Microsoft's): take the `Normalized RU Consumption` metric at 1-hour
grain with **Max** aggregation over 7 to 30 days, and average those hourly peaks. Below
66%, autoscale is cheaper; above 66%, stay on manual. On accounts with multi-region
writes and more than one region, the two rates per 100 RU/s are the same, so autoscale
costs nothing extra and is always the choice.

**The throughput floor rises on its own.** A manual container cannot go below the
largest of 400 RU/s, 1 RU/s per GB stored, and one hundredth of the highest RU/s ever
provisioned; for an autoscale maximum the terms are 1,000 RU/s, 10 RU/s per GB and one
tenth of the highest maximum ever set. A container scaled up for a one-off migration or
load test therefore keeps a higher minimum bill afterwards, and growing data raises it
too: check the minimum in the portal before promising a scale-down saving. Sources:
[choose between manual and autoscale](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-choose-offer)
and [service limits](https://learn.microsoft.com/en-us/azure/cosmos-db/concepts-limits),
read 9 November 2026.

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

SQL Database serverless, the DTU tiers and the Flexible Server Burstable tier are not
reservable, and the figures above are illustrative upper bounds. The sizing method, the
full exclusion list and the net-discount rule under a MACC live in
`finops-azure-commitments.md` ("Database commitment decision tree" and "Net discount
under a MACC with an Azure Commitment Discount").

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
// Cosmos DB accounts and their capabilities (inventory only). Autoscale is set per
// database or container, not at account level, so this cannot show it: read the
// throughput settings, then apply the 66% rule above.
resources
| where type == "microsoft.documentdb/databaseaccounts"
| extend capabilities = properties.capabilities
| project name, resourceGroup, location, capabilities
```

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
