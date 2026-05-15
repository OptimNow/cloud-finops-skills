---
name: aws-oversized-rds
scope: aws
service: AWS RDS
waste_category: overprovisioned
confidence: likely
---

# AWS Oversized RDS Instance

## Problem

RDS instances are billed by instance class regardless of actual CPU /
memory utilisation, plus storage and IOPS. Production teams routinely
provision the next-larger instance class as a hedge ("we might need it"),
and the headroom never gets revisited. The waste is invisible because the
database is healthy - low CPU and low memory pressure look like good
operations, not over-provisioning.

## Symptoms

- CloudWatch `CPUUtilization` < 30% p95 over a 14-day window
- CloudWatch `FreeableMemory` consistently > 50% of instance memory
- `DatabaseConnections` peak well below the instance's
  `max_connections` setting
- The instance class was set during initial migration and has never been
  reviewed
- The team uses `db.r5.4xlarge` "because that's what we use everywhere"

## Detection

```sql
-- Athena over CUR 2.0: top RDS instances by 30-day cost
SELECT
  line_item_resource_id           AS db_arn,
  product_instance_type           AS instance_class,
  SUM(line_item_usage_amount)     AS hours,
  SUM(line_item_unblended_cost)   AS cost_30d
FROM cur2
WHERE line_item_usage_start_date >= current_date - interval '30' day
  AND product_servicecode = 'AmazonRDS'
  AND line_item_usage_type LIKE '%InstanceUsage%'
GROUP BY 1, 2
ORDER BY cost_30d DESC
LIMIT 30;
```

Then for each candidate, check Performance Insights or CloudWatch:

```bash
# 14-day p95 CPU on a candidate instance
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=my-db \
  --start-time $(date -u -d '14 days ago' +%FT%TZ) \
  --end-time $(date -u +%FT%TZ) \
  --period 3600 \
  --statistics p95
```

## Fix

1. **Right-size in the same family first** (e.g. `db.r5.4xlarge` ->
   `db.r5.2xlarge`). Same family preserves engine compatibility and
   minimises blast radius.
2. **Schedule the resize during a planned window** with replication lag
   monitored - the failover during `ApplyImmediately` causes ~30-90 s
   downtime for Multi-AZ; longer for Single-AZ.
3. **For sustained over-provisioning, consider Aurora Serverless v2** -
   pays per ACU consumed rather than per instance class. Caveat: Aurora
   Serverless v2 has its own pricing model; not always cheaper than a
   right-sized provisioned instance for steady workloads.
4. **Modernise instance family** if the database has been on `r5` for
   years - `r6i`, `r7g` (Graviton), or `r8g` typically deliver better
   $/perf for the same workload. Validate with a dev-environment load
   test before production cutover.

## Anti-pattern

- Resizing during the busy quarter-end / holiday window. Resize
  operations during peak load have caused replica lag spikes that
  cascaded into application timeouts.
- Going below `db.t4g.large` for production workloads relying on
  burstable credits - the credit-exhaustion failure mode is silent
  until queries start timing out.

## See also

- `references/finops-aws.md` - RDS commitment strategy, Database Savings
  Plans, Aurora vs RDS economics
- `playbooks/aws-snapshot-sprawl.md` - related RDS snapshot sprawl

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
