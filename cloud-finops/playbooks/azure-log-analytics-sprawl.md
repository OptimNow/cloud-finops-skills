---
name: azure-log-analytics-sprawl
scope: azure
service: Azure Monitor / Log Analytics
waste_category: overprovisioned
confidence: likely
---

# Azure Log Analytics Ingestion Sprawl

## Problem

Log Analytics charges by **GB ingested** (~$2.30/GB Pay-As-You-Go,
discounted with Commitment Tiers) plus retention beyond the included
period. The default for many resource types is to send **everything** -
diagnostic settings on App Service, AKS audit logs, Azure Activity
Logs, NSG flow logs. Within months, 80% of ingestion volume is from
high-churn telemetry that nobody queries, and the bill is dominated by
table types like `AzureDiagnostics`, `ContainerLog`, `AppPlatformLogs`.

## Symptoms

- Top 5 ingestion tables represent > 80% of monthly GB
- Workspace has retention configured beyond compliance requirement
- Diagnostic settings configured organisation-wide via Policy without
  table-level filtering
- Ingestion grows month-over-month with no matching workload growth
- The cost-management chart for "Log Analytics ingestion" is on a
  steeper slope than overall cloud spend

## Detection

```kusto
// Top tables by ingestion volume, last 30 days (run inside the workspace)
Usage
| where TimeGenerated > ago(30d)
  and IsBillable == true
| summarize gb_ingested = sum(Quantity) / 1000 by DataType
| order by gb_ingested desc
| take 20
```

```kusto
// Per-resource ingestion drill-down for the worst offender
let topTable = "AzureDiagnostics";
table(topTable)
| where TimeGenerated > ago(30d)
| summarize records = count(), gb = sum(_BilledSize) / (1024*1024*1024) by ResourceId
| order by gb desc
| take 50
```

## Fix

1. **Lever 1 - Tier**: split tables between **Analytics** (queryable,
   expensive) and **Basic Logs** (cheaper, limited query). Move tables
   that are kept for forensic-only access (NSG flow logs, AKS verbose
   container logs) to Basic.
2. **Lever 2 - Filter at source**: configure diagnostic settings to
   send only the relevant log categories (e.g. AKS audit + control-plane
   ONLY, not container logs which can go to a separate, cheaper
   destination).
3. **Lever 3 - Sampling / aggregation**: for high-volume telemetry,
   aggregate at the source (Application Insights sampling) instead of
   sending raw events.
4. **Lever 4 - Retention right-sizing**: the included retention is 31
   days. Audit which tables actually need 365+ days; archive the rest
   to Storage Account Archive tier (~$0.002/GB-month) via export.
5. **Lever 5 - Commitment tier**: if the steady-state volume is > 100
   GB/day, switch from Pay-As-You-Go to a Commitment Tier - up to ~30%
   discount.

## Anti-pattern

- Disabling diagnostic settings entirely to "stop the bleeding". The
  audit gap surfaces during the next compliance review or incident
  investigation.
- Moving everything to Basic Logs. Some tables are queried by Sentinel
  detection rules; demoting them to Basic breaks security monitoring
  silently.

## See also

- `references/finops-azure.md` - Log Analytics 5-lever cost control,
  Sentinel cost mechanics, Commitment Tier pricing
- `references/finops-waste-detection-playbooks.md` - "overprovisioned"
  category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
