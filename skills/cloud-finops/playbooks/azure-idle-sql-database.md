---
name: azure-idle-sql-database
scope: azure
service: Azure SQL Database / Managed Instance
waste_category: idle
confidence: likely
---

# Azure Idle SQL Database

## Problem

Azure SQL Database is billed by service tier (Basic / Standard / Premium
DTU model OR vCore-based Business Critical / General Purpose / Hyperscale)
and reserved compute. An idle SQL Database in production tier accrues the
full hourly even when no application connects to it. Common origins:
abandoned dev databases never deleted, decommissioned applications whose
DB lingered, "we'll use it eventually" databases provisioned years ago.

## Symptoms

- `connection_successful` count < 10 / day over 14 days
- CPU < 5% p95 over 30 days
- DTU / vCore consumption < 5% sustained
- The database name encodes a project / app that no longer exists in
  the catalogue
- The owning resource group is named `*-decommissioned-*` or
  `*-old-*` but the SQL DB is still running

## Detection

```kusto
// Azure Resource Graph - all Azure SQL Databases by tier
resources
| where type =~ "microsoft.sql/servers/databases"
  and name != "master"
| extend tier = tostring(sku.tier)
| extend size = tostring(sku.name)
| project subscriptionId, resourceGroup, server = strcat(split(id, "/")[8]), name, tier, size
| order by tier desc
```

```kusto
// Connection activity from Azure Monitor over 14 days
AzureMetrics
| where ResourceProvider == "MICROSOFT.SQL"
  and ResourceType == "SERVERS/DATABASES"
  and MetricName == "connection_successful"
  and TimeGenerated > ago(14d)
| summarize total_connections = sum(Total) by Resource
| where total_connections < 100
| order by total_connections asc
```

## Fix

1. **Confirm the DB is genuinely idle** - some monthly batch jobs have
   long inter-run gaps. Cross-check with `dm_db_resource_stats` and the
   application's job scheduler.
2. **Backup before delete** (Azure SQL automatic backup retention is 7-
   35 days; a long-term backup snapshot is cheap insurance).
3. **Move long-tail dev databases to Basic tier or Serverless** - Basic
   is ~$5/month per DB, Serverless auto-pauses after inactivity (Gen5
   1-vCore can drop to ~$15/month for idle workloads).
4. **For permanent decommissions, drop the database AND the parent SQL
   Server** if no other DB lives on it - the server itself has no charge
   but littered server objects multiply your management overhead.

## Anti-pattern

- Deleting a SQL DB without checking firewall rule references and
  application connection strings. Some applications fail open ("connect
  to DB B if DB A is unreachable") and the failure mode is silent
  until quarterly reporting breaks.
- Migrating idle production DBs to Serverless without testing the
  cold-start latency. The first connection after auto-pause can take
  30-60 s, which times out short-window batch jobs.

## See also

- `references/finops-azure.md` - Azure SQL Database tier economics,
  Serverless vs Provisioned, Hyperscale architecture
- `references/finops-waste-detection-playbooks.md` - "idle" category
  rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
