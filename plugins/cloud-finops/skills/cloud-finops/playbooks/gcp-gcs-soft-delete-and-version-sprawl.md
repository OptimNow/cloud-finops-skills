---
name: gcp-gcs-soft-delete-and-version-sprawl
scope: gcp
service: Google Cloud Storage
waste_category: orphaned
confidence: likely
---

# GCS Soft-Delete and Noncurrent Version Sprawl

## Problem

Three mechanisms keep bytes billable after the application is done with
them. **Soft delete** is on by default on every bucket, with a 7-day
retention (configurable up to 90 days, or 0 to disable): every deleted or
overwritten object is retained and billed at the bucket's storage-class
rate for the whole window. **Object versioning**, once enabled, keeps every
overwritten object as a noncurrent version with no expiry unless a
lifecycle rule deletes it. **Abandoned XML API multipart uploads** keep
their parts billable until aborted. On a high-churn bucket (Dataflow
staging, Composer and Spark scratch, CI artefacts, model checkpoints,
Terraform state) the retained bytes can exceed the live bytes. The soft
delete case is the one that surprised most estates: it arrived enabled on
existing buckets, so a scratch bucket that deletes and rewrites its whole
contents daily now pays for roughly seven extra copies with no
configuration change anyone made.

## Symptoms

- A bucket's `storage/v2/total_bytes` metric split by `type` shows
  `soft-deleted-object`, `noncurrent-object` or `multipart-upload` bytes
  as a large share of `live-object` bytes
- Versioning enabled with no lifecycle rule carrying `isLive: false`
- Soft-delete retention left at 7 days on scratch and staging buckets, or
  raised to 90 days "to be safe" on buckets nobody has restored from
- Storage cost rose in the month soft delete was enabled by default while
  live object counts did not

## Detection

```bash
# Stage 1: configuration. Flags buckets that retain history with no
# pruning rule. Read-only. Prerequisite: storage.buckets.get on the
# project. Verify the JSON key names against one bucket first with
# `gcloud storage buckets describe gs://<bucket> --format=json`; the
# gcloud storage schema is flat snake_case and differs from gsutil.
for b in $(gcloud storage buckets list --project "$PROJECT" --format="value(name)"); do
  j=$(gcloud storage buckets describe "gs://$b" --format=json)
  ver=$(echo "$j" | jq -r '.versioning_enabled // false')
  sd=$(echo "$j" | jq -r '.soft_delete_policy.retentionDurationSeconds // 0')
  ncv_rule=$(echo "$j" | jq '[.lifecycle_config.rule[]? | select(.action.type=="Delete") | select(.condition.isLive==false)] | length')
  mpu_rule=$(echo "$j" | jq '[.lifecycle_config.rule[]? | select(.action.type=="AbortIncompleteMultipartUpload")] | length')
  [ "$ver" = "true" ] && [ "${ncv_rule:-0}" = "0" ] && echo "VERSIONED, NO NONCURRENT DELETE RULE: $b"
  [ "${mpu_rule:-0}" = "0" ] && echo "NO MULTIPART ABORT RULE: $b"
  [ "$sd" -gt 604800 ] && echo "SOFT DELETE RETENTION $((sd/86400))d: $b"
done
```

Stage 2 sizes the flagged buckets. Unlike the AWS and Azure twins, GCS
exposes the split directly: the Cloud Monitoring metric
`storage.googleapis.com/storage/v2/total_bytes` carries a `type` label
with the values `live-object`, `noncurrent-object`, `soft-deleted-object`
and `multipart-upload`. In Metrics Explorer, group by `bucket_name` and
`type`; as PromQL in the same console:

```promql
# Metrics Explorer, PromQL tab. Bytes retained but not live, per bucket.
# Verify the metric and label names in the metric picker first; the v2
# metric is the one with the type label, the older storage/total_bytes
# is not.
sum by (bucket_name, type) (storage_googleapis_com:storage_v2_total_bytes{type!="live-object"})
```

The metric is daily and lags about a day, so an empty series on a new
bucket is "no data", not "no waste". Classification is `likely`: act on
the missing rule or oversized retention AND retained bytes above roughly
20% of live bytes. The blocker check keeps it from `obvious`: a bucket
retention policy or lock, a `Bucket Lock` compliance hold, Turbo
replication or a dual-region bucket used as the surviving copy, and any
documented point-in-time recovery need all legitimately keep history.

## Fix

1. Run the blocker check per bucket: retention policy and lock state,
   event-based holds, replication role, and the owning team's real
   restore requirement.
2. Set soft-delete retention to the recovery need. For scratch, staging and
   rebuildable buckets that is 0 (disabled); for data of value keep 7
   days. The retention duration is the whole lever: soft-deleted objects
   are purged when it expires, lifecycle rules do not touch them. Set the
   organisation-level default for new buckets through the
   `storage.softDeletePolicySeconds` constraint so the next scratch bucket
   does not inherit 7 days (confirm the constraint name in the current
   organisation policy catalogue).
3. Add a lifecycle rule `Delete` with `isLive: false` and
   `daysSinceNoncurrentTime` at 30 to 90 days, plus `numNewerVersions` where
   the team needs rollback depth rather than a time window.
4. Add `AbortIncompleteMultipartUpload` with `age` of about 7 days to every
   bucket that receives XML API multipart uploads (most S3-compatible
   tooling does).
5. Put all three into the bucket Terraform module and a project-level
   policy check.

## Anti-pattern

- Turning versioning off to stop the growth. Existing noncurrent versions
  stay and keep billing until deleted, and the protection is gone.
- Disabling soft delete across the organisation in one sweep. It is the
  cheapest accidental-delete insurance on buckets whose data cannot be
  rebuilt; the saving is on the scratch tier, not everywhere.
- Deleting noncurrent versions on a bucket that is the replication
  destination of a compliance copy.
- Reading the older `storage/total_bytes` metric and concluding there is
  no retained data. It has no `type` label and folds everything together.

## See also

- `playbooks/gcp-gcs-cold-data-in-standard.md` - the tiering decision on
  the bytes that survive the pruning rules
- `playbooks/aws-s3-noncurrent-version-sprawl.md` and
  `playbooks/aws-s3-incomplete-multipart-uploads.md` - the AWS twins
- `playbooks/azure-blob-version-and-soft-delete-sprawl.md` - the Azure
  twin, same default-on soft delete trap
- `playbooks/gcp-orphan-persistent-disks.md` - the block-storage side of
  orphaned bytes
- `references/finops-gcp.md` - Storage Optimization Patterns ("Over
  Retained Exported Object Versions")
- `references/finops-waste-detection-playbooks.md` - the eight-category
  taxonomy this pattern fits ("orphaned")

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
