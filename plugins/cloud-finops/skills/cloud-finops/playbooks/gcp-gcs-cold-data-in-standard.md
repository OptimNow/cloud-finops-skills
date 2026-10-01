---
name: gcp-gcs-cold-data-in-standard
scope: gcp
service: Google Cloud Storage
waste_category: overprovisioned
confidence: possible
---

# GCS Cold Data Sitting in Standard

## Problem

Objects written once and rarely read keep paying the Standard rate when
Nearline, Coldline or Archive would cost a fraction of it. It is the
highest-value GCS pattern in a typical estate and the hardest of the three
clouds to evidence, because **GCS records no last-access time per
object**. Access evidence has to come from Data Access audit logs or usage
logs that most projects never enabled, or from Autoclass observing the
bucket for you. The colder classes punish a wrong guess twice: a per-GB
retrieval charge on every read, and a minimum storage duration (30 days
Nearline, 90 Coldline, 365 Archive) billed in full if the object is
deleted or re-classed earlier. That evidence gap is structural: a
read-only review cannot raise this finding above `possible` on its own, so
the honest first deliverable is often a prerequisite finding ("enable
Storage Insights and Data Access logging on the buckets carrying the
spend") rather than a savings number.

## Symptoms

- The billing export shows large Standard Storage SKU cost on buckets
  whose names say logs, export, backup, raw, archive or landing
- Cloud Monitoring `storage/v2/total_bytes` by `storage_class` is almost
  all Standard, with `api/request_count` for `ReadObject` near zero
- No lifecycle rule with `SetStorageClass`, and Autoclass is off
- Nobody can say who reads the bucket or how often
- BigQuery external tables, Dataproc or Dataflow jobs point at the bucket,
  which would make a cold class expensive rather than cheap

## Detection

Two stages. Stage 1 ranks where the Standard spend sits from the billing
export every project should already have. Stage 2 turns a candidate into
a defensible recommendation and needs telemetry that is usually missing.

```sql
-- Stage 1: BigQuery resource-level billing export. Standard-class storage
-- cost per bucket, last 30 days. Needs the *resource-level* export
-- (table name ends in _resource_v1_...); the standard export has no
-- resource.name for GCS. Check sku.description values on a sample row:
-- class names appear in the SKU text ("Standard Storage", "Nearline
-- Storage"), region-qualified.
SELECT
  resource.name                 AS bucket,
  SUM(cost)                     AS standard_storage_cost_30d,
  ANY_VALUE(usage.pricing_unit) AS unit
FROM `<project>.<dataset>.gcp_billing_export_resource_v1_<account>`
WHERE service.description = 'Cloud Storage'
  AND sku.description LIKE 'Standard Storage%'
  AND _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY 1
ORDER BY 2 DESC
LIMIT 25;
```

Stage 2 needs the age-versus-size profile and some access signal:

- **Storage Insights inventory reports** (a bucket-level configuration,
  exported to BigQuery or CSV) give `name`, `size`, `storageClass`,
  `timeCreated` and `updated` per object. Weight by **bytes, not object
  count**: a prefix where most objects are old but most bytes are recent
  must not be moved, and object-count weighting says the opposite.
- **Access**: either Data Access audit logs for `storage.objects.get`
  routed to BigQuery (costly on busy buckets; enable on the candidates
  only, for 30 days), or the `api/request_count` metric by `method`
  as a bucket-level proxy. If neither exists, that is the finding.

```sql
-- Stage 2 illustrative: Storage Insights inventory in BigQuery, bytes by
-- top-level prefix and age band. Column names follow the inventory
-- report schema; confirm against the table before running.
SELECT
  REGEXP_EXTRACT(name, r'^([^/]+)/')                      AS prefix,
  storageClass,
  COUNT(*)                                                AS objects,
  SUM(size) / 1073741824.0                                AS gib,
  SUM(size) / COUNT(*) / 1024.0                           AS avg_kib,
  SAFE_DIVIDE(SUM(IF(updated < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY), size, 0)),
              SUM(size))                                  AS byte_share_over_90d
FROM `<project>.<dataset>.<inventory_table>`
GROUP BY 1, 2
HAVING SUM(size) > 107374182400   -- prefixes over 100 GiB only
ORDER BY gib DESC;
```

The gates that make a class change defensible (all three, hence
`possible` until they are met):

- **Access floor**: monthly read-bytes divided by stored-bytes below the
  break-even ratio `(rate_standard - rate_target) / retrieval_rate_target`
  at current regional list rates. For Nearline that ratio has historically
  sat near 1, so a dataset re-read roughly monthly gains nothing; verify
  with the live rates before quoting it.
- **Object size floor**: average object size comfortably above 128 KiB.
  Autoclass does not transition smaller objects at all, and for explicit
  rules the per-operation and retrieval costs on small objects eat the
  saving.
- **Stability**: the data must have stopped changing for longer than the
  target class's minimum duration, or the early-deletion charge fires on
  rewrites.

## Fix

1. If inventory reports and an access signal are missing: ship the
   prerequisite finding, not a savings estimate.
2. Where access is genuinely unknown and objects are large: **Autoclass**
   with the terminal class set to Nearline (or Archive where the team
   accepts the access model). It moves objects on observed access, waives
   retrieval and early-deletion fees, and charges a per-object management
   fee instead, which is the trade for not doing the access study. The
   fee is per 1,000 objects, so a bucket of millions of small objects can
   pay more in fee than it saves.
3. Where the evidence is in hand: a lifecycle `SetStorageClass` rule on
   the evidenced prefixes (`matchesPrefix`) at 90+ days to Nearline or
   Coldline. Archive changes the access model for anything that still gets
   read and needs the owning team's sign-off. Autoclass and
   `SetStorageClass` rules do not combine on one bucket; pick one.
4. For log-shaped prefixes (small objects, monotonic growth, never read
   after N days): the lever is **Delete** at the retention requirement,
   not a class change that bills operations on every object.
5. Check rule interactions: a `Delete` day earlier than
   `class-change day + minimum duration` triggers the early-deletion charge
   on data being deleted anyway.

## Anti-pattern

- Recommending class changes from age alone, at scale, without access
  evidence: a long `possible`-confidence list nobody can action.
- Moving buckets that BigQuery external tables, Dataproc, Dataflow or
  Vertex pipelines read into Coldline or Archive; every query pays
  retrieval, and Archive reads are slow enough to break jobs.
- Enabling Autoclass on a bucket of millions of tiny objects, where the
  per-object fee exceeds the saving on bytes that never transition.
- Paying the dual-region or multi-region multiplier on cold data that a
  single region would serve; location is a bigger lever than class on
  some estates, and both can change at once in the rule.
- Reading the standard billing export and concluding GCS spend cannot be
  attributed; it is the resource-level export that carries the bucket.

## See also

- `playbooks/gcp-gcs-soft-delete-and-version-sprawl.md` - run the
  pruning rules first; they are realised saving with no access study
- `playbooks/aws-s3-cold-data-in-standard.md` and
  `playbooks/azure-blob-cold-data-in-hot.md` - the twins, same two-stage
  detection and the same three gates
- `references/finops-gcp.md` - Storage Optimization Patterns ("Missing
  Autoclass On GCS Bucket", "Inactive GCS Bucket") and the BigQuery
  billing export section
- `references/finops-waste-detection-playbooks.md` - the taxonomy and the
  realised-versus-potential savings distinction this playbook leans on

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
