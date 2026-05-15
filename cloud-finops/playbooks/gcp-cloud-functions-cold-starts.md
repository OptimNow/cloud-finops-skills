---
name: gcp-cloud-functions-cold-starts
scope: gcp
service: GCP Cloud Functions
waste_category: overprovisioned
confidence: possible
---

# GCP Cloud Functions Cold Starts

## Problem

Cloud Functions scale to zero when idle. When invoked after inactivity,
the function undergoes a "cold start" - initialising the runtime,
loading dependencies, and establishing network connections (e.g. VPC
connectors). Cold-start latency surfaces as user-facing slowness AND as
cost: longer cold-start time means longer billed execution time per
invocation. For high-fan-out, low-volume functions, the cold-start
cost can dominate the active execution cost.

This pattern is "possible" tier (not obvious or likely) because cold
starts are a legitimate trade-off for scale-to-zero economics. The
question is whether the trade is worth it for a specific function.

## Symptoms

- Cloud Functions execution metric shows P95 latency much greater than
  P50 latency (cold-start tail) for invocation patterns with low
  concurrency
- Function uses **VPC connector** to reach internal services - VPC
  connector setup adds 1-3 s to cold starts
- Function has heavy initialisation logic (loading large ML models,
  warming caches) that runs on every cold start
- Function is invoked sporadically (every few minutes / hours) rather
  than continuously

## Detection

```sql
-- BigQuery billing export: Cloud Functions cost by function
SELECT
  resource.name                   AS function_name,
  SUM(cost)                       AS cost_30d,
  SUM(usage.amount)               AS gb_seconds
FROM `<project>.<dataset>.gcp_billing_export_resource_v1_<account>`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND service.description = 'Cloud Functions'
GROUP BY 1
ORDER BY cost_30d DESC
LIMIT 30;
```

```bash
# P50 vs P99 latency for a candidate function (Cloud Monitoring)
gcloud monitoring metrics list --filter="metric.type:cloudfunctions.googleapis.com/function/execution_times"
# Then query in Metrics Explorer with grouping by execution_status
```

## Fix

1. **Set minimum instances** for functions where cold-start latency is
   user-visible. `min-instances=1` keeps one instance warm at the cost
   of one always-on billed execution. Trade-off: ~$5-15/month per warm
   instance, depending on memory tier.
2. **Reduce function size** by minimising dependencies and optimising
   startup code. Each MB of cold-start initialisation translates to
   billed time AND user-visible latency.
3. **Right-size your private-egress strategy**. VPC connector cold-start
   overhead is real, but the alternatives differ in scope:
   - **Private Google Access** covers only Google APIs and managed
     services reachable through `*.googleapis.com` / `*.pkg.dev`
     endpoints. It does NOT reach internal RFC1918 resources (Memorystore,
     internal VMs, Cloud SQL via private IP, internal load balancers).
     Use it when the function only needs to talk to BigQuery, GCS, Pub/Sub,
     Secret Manager, or other Google-API-fronted services.
   - **Direct VPC egress** (Cloud Run / Cloud Run Functions 2nd gen) and
     **Serverless VPC Access connectors** (1st gen) ARE required for
     RFC1918 resources. Direct VPC egress avoids the connector hourly and
     is the modern path on 2nd gen runtimes.
   - VPC connectors are still the right answer for 1st gen functions that
     need internal-IP reachability; what to optimise then is connector
     instance count and size, not removing the connector.
4. **Migrate to Cloud Run for sustained workloads**. Cloud Run has
   better cold-start economics for workloads invoked more than ~10
   times/min, and offers `min-instances` with finer control.
5. **Migrate to Cloud Run Functions (2nd gen)** which has much faster
   cold starts than 1st-gen Cloud Functions for the same code.

## Anti-pattern

- Setting `min-instances` blindly on all functions. The whole point of
  Cloud Functions is scale-to-zero economics; if you keep instances
  warm everywhere, Cloud Run is a better runtime for that workload.
- Adding VPC connectors as a default for Google-API-only access. If the
  function only talks to BigQuery, GCS, Pub/Sub, Secret Manager and other
  Google-API endpoints, Private Google Access reaches them without the
  per-connector hourly charge.
- Replacing a VPC connector with Private Google Access when the function
  actually talks to internal RFC1918 resources (Memorystore, internal
  VMs, Cloud SQL via private IP). The function will start failing
  silently because Private Google Access does not reach those.

## See also

- `references/finops-gcp.md` - Cloud Functions pricing model, VPC
  connector costs
- `references/finops-vertexai.md` - similar cold-start economics for
  Vertex AI batch prediction

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
