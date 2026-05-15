---
name: aws-snapshot-sprawl
scope: aws
service: AWS EBS / RDS Snapshots
waste_category: orphaned
confidence: likely
---

# AWS Snapshot Sprawl

## Problem

EBS and RDS snapshots are billed at roughly $0.05/GB-month (Standard EBS
snapshots; Archive tier is cheaper at the cost of slower restore). Over
years of un-curated CI / CD pipelines, broken backup automation, and
forgotten one-off "before-the-upgrade" snapshots, accounts accumulate tens
of TB of snapshot storage with no owner and no recovery test in living
memory. Cost grows linearly forever; nothing prunes it.

## Symptoms

- Number of snapshots in the account grows month-over-month with no
  matching growth in workloads
- Many snapshots have no associated AMI, no `aws:tag:owner`, and no
  parent volume (the volume was deleted long ago)
- The oldest snapshot in the account is > 24 months old, no matching
  compliance retention requirement explains it
- Dev / test accounts hold larger snapshot inventory than production
  (a clear smell)

## Detection

```sql
-- Athena over CUR 2.0: top snapshot spend by account, last 30 days
SELECT
  line_item_usage_account_id      AS account,
  product_volume_type             AS volume_type,
  SUM(line_item_usage_amount)     AS gb_month,
  SUM(line_item_unblended_cost)   AS cost_30d
FROM cur2
WHERE line_item_usage_start_date >= current_date - interval '30' day
  AND product_servicecode IN ('AmazonEC2', 'AmazonRDS')
  AND line_item_usage_type LIKE '%Snapshot%'
GROUP BY 1, 2
ORDER BY cost_30d DESC;
```

Cross-reference with the EC2 API to find orphaned snapshots:

```bash
# Snapshots with no associated AMI AND no current volume
aws ec2 describe-snapshots --owner-ids self \
  --query 'Snapshots[?!not_null(Tags[?Key==`aws:ec2:image-id`])].{Id:SnapshotId,VolumeId:VolumeId,Created:StartTime,SizeGb:VolumeSize}' \
  --output table
```

## Fix

1. Tag every snapshot with `owner`, `purpose`, and `retention-until` as a
   one-time pass.
2. Delete snapshots that are: (a) older than the documented retention
   window, AND (b) have no parent AMI, AND (c) are in a non-prod account.
3. For remaining production snapshots, move pre-defined retention tiers
   to **EBS Snapshot Archive** (~75% cheaper, restore takes 24-72 h - fine
   for compliance retention, not for hot DR).
4. Establish ongoing curation via **Data Lifecycle Manager** policies tied
   to tag rules, NOT calendar-based mass delete.
5. Test restore on a sample once - if no one in the org has restored a
   snapshot from this set in 12 months, the recovery story is not
   credible and the snapshots are theatre, not insurance.

## Anti-pattern

- Mass-delete by age alone. A 5-year-old snapshot may be the only copy of
  the production database from before a destructive migration; deleting it
  costs nothing in $ but everything in trust.
- Moving snapshots to Archive tier without confirming RTO. If your DR plan
  needs a 4-hour recovery, Archive tier (24-72 h restore) silently
  invalidates it.

## See also

- `references/finops-aws.md` - EBS / RDS billing mechanics, snapshot
  pricing tiers
- `references/finops-waste-detection-playbooks.md` - "orphaned" category
  rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
