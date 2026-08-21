---
name: aws-s3-cold-data-in-standard
scope: aws
service: Amazon S3
waste_category: overprovisioned
confidence: possible
---

# S3 Cold Data Sitting in Standard

## Problem

Data that is written once and rarely read again keeps paying the Standard
storage rate when an infrequent-access or archive class would cost a
fraction of it. This is the highest-value S3 pattern in a typical estate -
and the easiest to get wrong, because a defensible transition
recommendation needs *access* evidence, and access evidence lives in
telemetry (S3 Inventory, Storage Lens Advanced, request metrics) that most
accounts have never enabled. Age alone cannot separate "old but still
read" from "old and cold". That evidence gap is structural, not a tooling
choice: a read-only review can never raise this finding above `possible`
on its own, which is why the honest first deliverable is often a
prerequisite finding - "enable the telemetry on the buckets that carry the
spend" - rather than a savings estimate.

## Symptoms

- CUR `TimedStorage-ByteHrs` shows large Standard-class spend on buckets
  with archive-shaped names or log/export write patterns
- CloudWatch request metrics (where enabled) show near-zero `GetRequests`
  against large stored volume
- Buckets have no transition rules at all, or transition rules scoped to
  prefixes that no longer match the data layout
- Nobody can say who reads a bucket's data or how often

## Detection

Two stages. Stage 1 ranks candidates from data every account already has;
stage 2 turns a candidate into a defensible recommendation and requires S3
Inventory on the bucket (a configuration change - if it is not enabled,
that *is* the finding: recommend enabling Inventory plus request metrics
on the buckets carrying, say, 80% of S3 spend, and re-run in 30 days).

```sql
-- Stage 1: Athena over CUR 2.0 - Standard-class storage cost per bucket,
-- last full month. Ranks where the money is; says nothing about access.
SELECT line_item_resource_id AS bucket,
       SUM(line_item_unblended_cost) AS standard_storage_cost
FROM cur2
WHERE product_servicecode = 'AmazonS3'
  AND line_item_usage_type LIKE '%TimedStorage-ByteHrs'
  AND line_item_usage_start_date >= date_trunc('month', current_date - interval '1' month)
  AND line_item_usage_start_date <  date_trunc('month', current_date)
GROUP BY 1 ORDER BY 2 DESC LIMIT 25;
```

```sql
-- Stage 2: Athena over S3 Inventory (Parquet, IsLatest included) - the
-- age-vs-size profile per prefix. Weight by BYTES, not object count: a
-- prefix where 95% of objects are old but 95% of bytes are recent must
-- not be transitioned, and object-count weighting says the opposite.
SELECT regexp_extract(key, '^([^/]+)/', 1) AS prefix,
       storage_class,
       count(*)                          AS objects,
       sum(size)/1073741824.0            AS gib,
       sum(size)/count(*)/1024.0         AS avg_kib,
       sum(CASE WHEN last_modified_date < current_date - interval '90' day
                THEN size ELSE 0 END) * 1.0 / sum(size) AS byte_share_over_90d
FROM s3_inventory
WHERE is_latest = true AND is_delete_marker = false
GROUP BY 1, 2
HAVING sum(size) > 107374182400   -- only prefixes over 100 GiB
ORDER BY gib DESC;
```

The gates that make a transition defensible (all three, hence `possible`
until they are met):

- **Access floor**: monthly GET-bytes / stored-bytes below the break-even
  ratio `(rate_standard - rate_target) / retrieval_rate_target`.
  Illustrative with us-east-1 list rates as of August 2026 (Standard
  $0.023, Standard-IA $0.0125, retrieval $0.01 per GB): break-even ≈ 1.05
  - you would need to re-read the whole dataset monthly before IA loses.
  Retrieval cost is almost never why IA fails; the 30-day minimum storage
  duration and the 128 KiB minimum billable object size are.
- **Object size floor**: average object size >= 128 KiB. Below it,
  IA-class minimums and transition request fees eat the saving.
- **Payback**: per-object transition request cost recovered in under ~3
  months at the class-rate delta.

Where access patterns are genuinely unknown and average object size is
comfortably large (roughly >= 1 MiB), **Intelligent-Tiering** is the
lower-evidence alternative: its monitoring fee is the trade for not
needing the access study. Between ~128 KiB and ~240 KiB average object
size the monitoring fee can exceed the IA-tier saving - check the
arithmetic with current rates before defaulting to it.

## Fix

1. If Inventory/request metrics are missing: ship the prerequisite
   finding (enable on the top-spend buckets), not a savings estimate.
2. For prefixes passing all three gates: transition to Standard-IA or
   Glacier Instant Retrieval at 90+ days. GIR keeps millisecond reads;
   Glacier Flexible / Deep Archive change the access model and need the
   owning team's sign-off, not just a cost case.
3. For log-shaped prefixes (small objects, monotonic growth, never read
   after N days): the right lever is **expiration**, not transition - set
   an expiry at the retention requirement and delete, because a
   transition rule on sub-128 KiB objects is a no-op that still bills
   transition requests.
4. Check rule interactions before saving: `transition_day + class minimum
   duration` must be earlier than any expiration day (30d for IA/GIR, 90d
   Glacier Flexible, 180d Deep Archive), or the minimum-duration charge
   fires on data being deleted anyway.

## Anti-pattern

- Recommending transitions from age data alone, at scale, without access
  evidence - a long `possible`-confidence list nobody can action, which
  burns the credibility that realised-savings findings build.
- Transitioning prefixes that Athena, Redshift Spectrum, or EMR tables
  point at into Glacier Flexible/Deep Archive - queries break silently.
  GIR is the safe archive class under query engines.
- Stacking a transition rule onto a bucket already in Intelligent-Tiering,
  or double-counting savings on replicated buckets (storage-class changes
  do not propagate to replicas unless configured).
- Per-object overhead blindness: Glacier classes add ~40 KiB of billable
  metadata per object, so archiving millions of tiny objects can cost
  more than it saves - another face of the 128 KiB floor.

## See also

- `playbooks/aws-s3-incomplete-multipart-uploads.md` and
  `playbooks/aws-s3-noncurrent-version-sprawl.md` - run the two
  garbage-collection rules first; they are realised savings with no
  access study
- `references/finops-aws.md` - S3 billing mechanics, storage-class table,
  Storage Lens and Inventory setup
- `references/finops-waste-detection-playbooks.md` - the taxonomy and the
  realised-vs-potential savings distinction this playbook leans on

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
