---
name: aws-orphaned-ebs-volumes
scope: aws
service: AWS EBS
waste_category: orphaned
confidence: obvious
---

# AWS Orphaned EBS Volumes

## Problem

EBS volumes in the `available` state (detached from any EC2 instance) are
billed at the same per-GB rate as attached volumes (~$0.08-0.12/GB-month
for gp3, more for io2). They accumulate after EC2 instance termination
when the volume's `DeleteOnTermination` flag is `false`, after migrations
that left source disks behind, and after manual snapshot-and-detach
workflows. Unlike snapshots, there is no recovery utility for orphaned
volumes - they just bleed money.

## Symptoms

- Volumes in `available` state for > 30 days
- Volumes with no `aws:tag:owner`, no `aws:tag:project`, and no parent
  EC2 instance still in the account
- Account holds many small `gp2` / `gp3` volumes (~8 GB or 30 GB) - the
  default sizes from auto-scaling group templates and EKS PVCs that
  outlived their pods
- The volume's `Description` references a project name that has since
  been decommissioned

## Detection

```bash
# All volumes detached, sorted by size (largest first)
aws ec2 describe-volumes \
  --filters Name=status,Values=available \
  --query 'Volumes[].{Id:VolumeId,Size:Size,Created:CreateTime,Type:VolumeType,Tags:Tags}' \
  --output json | jq 'sort_by(-.Size)'
```

```sql
-- Athena over CUR 2.0: detached EBS spend by account
-- (CUR exposes "Storage" usage type for detached volumes the same as attached;
--  cross-reference with the API above)
SELECT
  line_item_resource_id           AS volume_id,
  line_item_usage_account_id      AS account,
  product_volume_type             AS volume_type,
  SUM(line_item_usage_amount)     AS gb_month,
  SUM(line_item_unblended_cost)   AS cost_30d
FROM cur2
WHERE line_item_usage_start_date >= current_date - interval '30' day
  AND product_servicecode = 'AmazonEC2'
  AND line_item_usage_type LIKE '%EBS:VolumeUsage%'
GROUP BY 1, 2, 3
ORDER BY cost_30d DESC;
```

## Fix

1. Snapshot before delete (cheap insurance: snapshot is ~50% the cost of
   the live volume per GB-month, and you can keep the snapshot for 30
   days as a safety net before final deletion).
2. Delete volumes in the `available` state with confirmed:
   - No parent EC2 instance in the account
   - No matching live AMI or launch template
   - Detached for > 30 days
   - No restore activity in the last 90 days
3. Set `DeleteOnTermination=true` in launch templates and Auto Scaling
   Group launch configurations going forward to prevent the pattern at
   source.
4. For EKS, configure the CSI driver's `reclaimPolicy: Delete` on
   StorageClasses so PVC deletion releases the underlying EBS volume
   automatically.

## Anti-pattern

- Mass-deleting all `available` volumes in a sweep without the
  snapshot-first step. One forgotten compliance archive volume gets
  deleted and the recovery window is gone.
- Treating "no tags" as the trigger to delete. Some legitimate orphans
  carry a manual tag added during a migration; some still-needed
  volumes are untagged. Use the API age + state combination, not tag
  state alone.

## See also

- `references/finops-aws.md` - EBS volume types and pricing
- `playbooks/aws-snapshot-sprawl.md` - related snapshot accumulation
- `references/finops-waste-detection-playbooks.md` - "orphaned" category
  rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
