---
name: aws-gp2-to-gp3
scope: aws
service: Amazon EBS
waste_category: modernization
confidence: obvious
---

# AWS gp2-to-gp3 Volume Migration

## Problem

gp3 is the successor to gp2 at a ~20% lower per-GB rate ($0.08 vs
$0.10/GB-month in us-east-1; illustrative list rates, written August
2026), and it decouples performance from size: every gp3 volume gets
3,000 IOPS and 125 MB/s baseline regardless of capacity, where gp2 ties
IOPS to size (3 IOPS per GB) and relies on burst credits below 1,000 GB.
For the bulk of the fleet - volumes at or under 1,000 GB - gp3 is equal
or better on every performance dimension at a lower price, and the
conversion is a **live, in-place modification with no downtime**. gp2
volumes persist purely because nothing forces the migration: new volumes
default to whatever the IaC template says, and templates written before
gp3 existed (December 2020) still say gp2.

## Symptoms

- CUR shows material spend on usage type `EBS:VolumeUsage.gp2`
- IaC modules and launch templates with `volume_type = "gp2"` hardcoded
  or defaulted
- Small gp2 volumes (< 334 GB) suffering burst-credit exhaustion under
  sustained IO - on gp3 the same workload would sit under the 3,000
  IOPS baseline
- AMI-launched instances inheriting gp2 root volumes from old images

## Detection

Single signal - a gp2 volume at or under 1,000 GB converts to gp3 at
equal-or-better performance for less money, no further analysis needed:

```sql
-- Athena over CUR 2.0: gp2 spend by account, last full month
SELECT
  line_item_usage_account_id    AS account_id,
  SUM(line_item_usage_amount)   AS gb_months,
  SUM(line_item_unblended_cost) AS gp2_cost
FROM cur2
WHERE line_item_usage_start_date >= date_trunc('month', current_date - interval '1' month)
  AND line_item_usage_start_date <  date_trunc('month', current_date)
  AND line_item_usage_type LIKE '%EBS:VolumeUsage.gp2'
GROUP BY 1
ORDER BY gp2_cost DESC;
```

Volume-level inventory with the size split that decides the treatment:

```bash
# gp2 volumes; those <= 1000 GiB are the no-analysis-needed cohort
aws ec2 describe-volumes \
  --filters "Name=volume-type,Values=gp2" \
  --query "Volumes[].{id:VolumeId,size:Size,az:AvailabilityZone,state:State}" \
  --output table
```

## Fix

1. Convert every gp2 volume at or under 1,000 GB:
   `aws ec2 modify-volume --volume-id vol-XXXX --volume-type gp3`.
   The volume stays attached and serving IO throughout; the state is
   visible in `describe-volumes-modifications`. One modification per
   volume per 6 hours, so batch scripts should tolerate the cooldown.
2. For gp2 volumes **over 1,000 GB**, match performance before
   converting: their gp2 baseline exceeds 3,000 IOPS (3 IOPS/GB), so
   set `--iops` to the current baseline and `--throughput` if the
   workload is sequential (gp2 reaches 250 MB/s on large volumes; gp3
   defaults to 125). Provisioned extra IOPS and throughput carry their
   own small per-unit rates - the conversion usually still wins, but
   compute it rather than assume it.
3. Fix the source: change `gp2` to `gp3` in launch templates,
   CloudFormation/Terraform defaults, and AMI build pipelines, or the
   fleet regrows.
4. Track the residual with the CUR query monthly until
   `EBS:VolumeUsage.gp2` reads zero.

## Anti-pattern

- Blind-converting > 1,000 GB volumes without setting IOPS and
  throughput. The volume lands on gp3 baseline (3,000 / 125) and a
  database that was quietly using its 9,000-IOPS gp2 baseline slows
  down - the saving gets blamed for an incident it did not need to
  cause.
- Converting io1/io2 volumes with the same script "while at it".
  Provisioned-IOPS volumes exist for latency-sensitive workloads;
  their migration is a rightsizing decision, not a default.
- Waiting to bundle the conversion into a maintenance window. The
  modification is online by design; treating it as risky delays a pure
  saving for months.

## See also

- `playbooks/aws-graviton-candidate.md` - the compute-side
  modernization pattern, same "newer generation, lower rate" shape
- `playbooks/aws-orphaned-ebs-volumes.md` - run the orphan sweep first
  so you do not migrate volumes that should simply be deleted
- `references/finops-aws-patterns.md` - the enumerated EBS pattern
  catalogue
- `references/finops-waste-detection-playbooks.md` - "modernization"
  category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
