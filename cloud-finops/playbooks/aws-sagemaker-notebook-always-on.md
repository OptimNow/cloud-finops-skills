---
name: aws-sagemaker-notebook-always-on
scope: aws
service: AWS SageMaker
waste_category: idle
confidence: obvious
---

# AWS SageMaker Always-On Notebook Instance

## Problem

SageMaker notebook instances are billed per hour while they are in `InService`
state, whether a kernel is running or not. A modest `ml.t3.medium` notebook
costs ~$36/month if left on 24/7; an `ml.t3.xlarge` is ~$144/month; a GPU
notebook (`ml.g4dn.xlarge`) is ~$540/month. Data-science teams routinely
spin notebooks up for a half-day experiment, walk away, and the notebook
keeps billing for months. Multiply across a 10-person ML team and a Friday
deadline, and the always-on notebook bill becomes the second-largest line
in SageMaker spend after endpoints.

## Symptoms

- Notebook instance `Status` is `InService` for > 14 consecutive days
- `LastModifiedTime` from `describe-notebook-instance` has not advanced
  during the same window (the notebook configuration has not been touched)
- The instance has no Lifecycle Configuration (LCC) attached, or the LCC
  does not implement auto-shutdown
- CUR `line_item_usage_amount` for `*-SageMaker:Notebk-*` exceeds 600 hours
  in a single month for the same `line_item_resource_id`
- The owner / team tag is empty or points to someone who has moved on

## Detection

```sql
-- Athena over CUR 2.0: notebooks running > 600 hours/month
SELECT
  line_item_resource_id           AS notebook_arn,
  line_item_usage_type            AS usage_type,
  SUM(line_item_usage_amount)     AS instance_hours,
  SUM(line_item_unblended_cost)   AS cost_month
FROM cur2
WHERE line_item_usage_start_date >= date_trunc('month', current_date - interval '1' month)
  AND line_item_usage_start_date <  date_trunc('month', current_date)
  AND product_servicecode = 'AmazonSageMaker'
  AND line_item_usage_type LIKE '%SageMaker:Notebk-%'
GROUP BY 1, 2
HAVING SUM(line_item_usage_amount) > 600
ORDER BY cost_month DESC;
```

For each candidate, cross-check `LastModifiedTime` via the API:

```
aws sagemaker list-notebook-instances --status-equals InService \
  --query 'NotebookInstances[].[NotebookInstanceName,InstanceType,LastModifiedTime,NotebookInstanceLifecycleConfigName]' \
  --output table
```

A notebook in `InService` with stale `LastModifiedTime` and no LCC is a
near-certain idle. SageMaker does not expose kernel activity through
CloudWatch directly, so the LCC log file (written to CloudWatch Logs at
`/aws/sagemaker/NotebookInstances`) is the practical signal for "is anyone
actually running anything in there".

## Fix

1. **Stop** the notebook (do not delete) once confirmed idle:
   `aws sagemaker stop-notebook-instance --notebook-instance-name <name>`.
   Stopping releases the instance charge but preserves the attached EBS
   volume (~$0.10/GB/month) and the notebook contents.
2. **Attach an auto-shutdown LCC** so the instance never ends up always-on
   again. AWS publishes a reference script that runs every 5 minutes,
   detects kernel idle time, and stops the instance after N hours of
   inactivity (search "amazon-sagemaker-notebook-instance-lifecycle-config-samples
   auto-stop-idle"). Attach the LCC via
   `update-notebook-instance --lifecycle-config-name`.
3. **Schedule** stop/start via EventBridge for predictable office-hours
   patterns (e.g. start 09:00 weekday, stop 19:00 weekday, never on
   weekends). Cheaper than relying on the LCC for teams that never use
   notebooks off-hours.
4. **Migrate the team to SageMaker Studio** for new work. Studio bills the
   Studio app per-second, supports native idle shutdown via the Studio
   admin console, and avoids the per-notebook EBS footprint. Existing
   notebook instances do not need to be migrated in place - new users join
   Studio directly.

## Anti-pattern

- Deleting (rather than stopping) a notebook to clean up - this also
  deletes the EBS volume and loses any uncommitted work. Always confirm
  that the notebook code is checked into Git first, or take a manual EBS
  snapshot, before deletion.
- Setting the LCC idle threshold too aggressive (e.g. 30 min). Data
  scientists running long-running training cells get their kernel killed
  mid-epoch. A 2-hour idle threshold is the practical default; 4 hours for
  teams running model evaluations.
- Replacing notebook instances with always-on Studio user-default apps and
  not configuring Studio idle shutdown - the same waste pattern just moves
  to a different SKU.

## See also

- `references/finops-aws.md` - SageMaker billing model, notebook hygiene,
  Lifecycle Configurations and Studio migration
- `playbooks/aws-sagemaker-idle-endpoint.md` - the related "forgotten
  resource" pattern on the inference side
- `references/finops-waste-detection-playbooks.md` - Category 7 (AI/ML
  inefficiency) taxonomy
