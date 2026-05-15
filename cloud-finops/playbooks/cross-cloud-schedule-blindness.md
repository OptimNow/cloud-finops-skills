---
name: cross-cloud-schedule-blindness
scope: cross-cloud
service: Compute (EC2 / Azure VM / Compute Engine)
waste_category: schedule-blindness
confidence: obvious
---

# Schedule Blindness (Non-Production 24/7)

## Problem

Non-production environments (dev, test, QA, staging, sandbox) are
typically used during business hours - say 12 hours/day, 5 days/week,
which is ~30% of a full week. Yet most non-prod compute runs 24/7
because nobody automated the off-hours shutdown. The 70% of unused time
is pure waste, and it scales linearly with the number of dev / test
environments. A team running 30 non-prod EC2 instances at $50/month
each pays $1,500/month for ~$450/month of actual use.

This is the highest-leverage, lowest-risk optimisation in cloud cost
work. It is the canonical "obvious" tier waste because the business
case is unambiguous: dev / test does not need to run while everyone is
asleep.

## Symptoms

- Non-prod compute (EC2 / VM / Compute Engine) shows ~constant
  utilisation across 24h windows in CloudWatch / Azure Monitor /
  Cloud Monitoring
- Tagged `env=dev` / `env=test` / `env=qa` instances have the same
  utilisation profile as production
- The non-prod / prod cost ratio is > 1:3 (mature orgs are typically
  1:5 to 1:10 because non-prod is auto-stopped)
- No team-owned automation visible in the IaC repo for stop / start

## Detection

**AWS** - CUR over 30 days, instance-hours by environment tag:

```sql
SELECT
  resource_tags_user_environment AS env,
  SUM(line_item_usage_amount) AS instance_hours,
  SUM(line_item_unblended_cost) AS cost_30d
FROM cur2
WHERE line_item_usage_start_date >= current_date - interval '30' day
  AND product_servicecode = 'AmazonEC2'
  AND line_item_usage_type LIKE '%BoxUsage%'
GROUP BY 1
ORDER BY cost_30d DESC;
```

**Azure** - Cost Management export, similar filter:

```kusto
costManagementBillingData
| where ServiceName == "Virtual Machines"
  and UsageDate >= now(-30d)
| summarize cost30d = sum(CostInBillingCurrency) by Tags["environment"]
| order by cost30d desc
```

**GCP** - BigQuery billing export with label-based filter:

```sql
SELECT
  labels.value AS environment,
  SUM(cost)     AS cost_30d
FROM `<project>.<dataset>.gcp_billing_export_v1_<account>`,
UNNEST(labels) AS labels
WHERE labels.key = 'environment'
  AND service.description = 'Compute Engine'
  AND _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY 1
ORDER BY cost_30d DESC;
```

## Fix

1. **AWS Instance Scheduler** (CloudFormation template provided by AWS)
   or **EventBridge + Lambda** for stop/start by tag. Common schedule:
   M-F 8am-7pm local time, weekends off. Saves ~70%.
2. **Azure Automation Start/Stop VMs during off-hours** (Microsoft-
   provided runbook). Same logic: tag + schedule.
3. **GCP Instance Schedules** (native feature) - attach a schedule to
   instances by label.
4. **For Kubernetes / managed services**: scale node pools to zero on
   schedule (Karpenter / Cluster Autoscaler with min=0). For Cloud Run
   / App Service / Lambda - the scale-to-zero is automatic, no scheduling
   needed.
5. **Communicate the schedule** to dev teams. The pattern fails if a
   developer needs to debug at 11pm and can't start the environment -
   provide a self-service "wake up my env" button (Slack command, web
   UI) so the schedule is a guideline, not a hard block.

## Anti-pattern

- Stopping production by accident due to a tag-misconfiguration
  ("env=production" vs "env=prod"). Audit tags BEFORE enabling
  automated stop. Some teams use `auto-stop=true` as the explicit opt-in
  rather than relying on env tags.
- Stopping databases with the same schedule as compute. RDS / SQL
  databases have separate billing (storage continues even when compute
  stops; some RDS instances cannot be stopped at all in Multi-AZ).
  Database schedules are a separate exercise, not bundled with compute.

## See also

- `references/finops-aws.md` - EC2 patterns including non-prod
  scheduling
- `references/finops-azure.md` - Azure VM rightsizing and scheduling
- `references/finops-gcp.md` - Compute Engine scheduling patterns
- `references/finops-waste-detection-playbooks.md` - "schedule-
  blindness" category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
