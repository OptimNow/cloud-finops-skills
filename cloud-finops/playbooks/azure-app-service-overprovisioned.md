---
name: azure-app-service-overprovisioned
scope: azure
service: Azure App Service
waste_category: overprovisioned
confidence: likely
---

# Azure App Service Plan Overprovisioned

## Problem

Azure App Service plans are billed by SKU (P1v3, P2v3, etc.) and instance
count, regardless of how many web apps actually run on them. Teams
default to **Premium v3** plans for production apps and never revisit -
even when the app handles low traffic that **Standard** or **Basic**
would serve fine. As an anchor (verify against the current Azure
pricing page in your region before sizing): in US East, a P1v3
instance is roughly $130-160/month (2 vCPUs, 8 GB RAM) versus roughly
$70/month for S1 (1 vCPU, 1.75 GB RAM). The two are not feature-
equivalent, but for many low-traffic workloads S1 fits, so the per-
instance gap of $60-90/month compounds across the auto-scale fleet.

## Symptoms

- App Service plan CPU < 25% p95 over 30 days
- Memory utilisation < 50% sustained
- Plan is on Premium v3 SKU but the apps deployed have no requirement
  for Premium-only features (deployment slots, VNet integration with
  private endpoints, autoscale on schedule)
- Plan instance count was set during a one-time event (Black Friday,
  product launch) and never scaled back down

## Detection

```kusto
// Azure Resource Graph - App Service plans by SKU and capacity
resources
| where type =~ "microsoft.web/serverfarms"
| extend sku_tier  = tostring(sku.tier)
| extend sku_size  = tostring(sku.size)
| extend capacity  = toint(sku.capacity)
| project subscriptionId, resourceGroup, name, sku_tier, sku_size, capacity, kind
| order by sku_tier desc
```

For utilisation:

```kusto
// CPU + Memory p95 from Azure Monitor over 30 days
AzureMetrics
| where ResourceProvider == "MICROSOFT.WEB"
  and ResourceType == "SERVERFARMS"
  and TimeGenerated > ago(30d)
  and MetricName in ("CpuPercentage", "MemoryPercentage")
| summarize p95 = percentile(Average, 95) by Resource, MetricName
| evaluate pivot(MetricName, max(p95))
| where CpuPercentage < 25 or MemoryPercentage < 50
| order by CpuPercentage asc
```

## Fix

1. **Right-size SKU first.** Compare the workload's actual feature use
   against the SKU's feature set. The big tier-jump trade-offs are:
   - P1v3 -> S1 typically saves $60-90/month per instance. Standard
     keeps deployment slots (5 vs Premium v3's 20), keeps regional VNet
     integration, keeps custom domains and SSL, keeps daily backups.
     What it loses: the larger autoscale ceiling (Standard caps at 10
     instances vs Premium v3 at 30), private endpoint support on the
     plan itself, the v3 generation's per-vCPU performance gain,
     zone-redundant deployments, and the higher memory ratio. Validate
     against the app's real ceiling needs and security posture, not
     against an assumed Premium-only feature list.
   - P1v3 -> P0v3 stays in Premium v3 tier (preserves all Premium v3
     features including the higher autoscale ceiling and zone redundancy)
     and saves roughly $70/month per instance via halving the vCPU /
     memory footprint - the right move when the app needs Premium v3
     features but not the headroom.
   - P1v3 -> P1v2 (older Premium generation) is rarely the right move
     because v3 is faster per-vCPU and the per-month delta is small.
2. **Reduce instance count to match observed p95 + safety margin**. Use
   **scheduled autoscale** to keep production at 2 instances during
   peak hours and 1 off-hours rather than a flat 4.
3. **Consolidate low-traffic apps** onto a single shared plan. Each App
   Service plan you eliminate saves a flat hourly. Test isolation
   carefully if apps have different security boundaries.
4. **Move dev / test environments to Basic or Free tier**. The cost
   delta vs production is meaningful and dev/test rarely need
   Premium-only features.

## Anti-pattern

- Resizing a Premium v3 plan to Basic on the same instances - some
  Premium-only features (Always On default, deployment slots, custom
  domains with SSL on every slot) silently disable. Verify the app's
  actual feature usage first.
- Aggressive consolidation onto a shared plan in production. Plan-level
  scaling boundaries are real - one badly-behaving app can starve the
  others. Reserve consolidation for dev / test / low-stakes prod.

## See also

- `references/finops-azure.md` - Azure compute rightsizing methodology,
  App Service vs AKS vs Container Apps trade-offs
- `references/finops-waste-detection-playbooks.md` - "overprovisioned"
  category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
