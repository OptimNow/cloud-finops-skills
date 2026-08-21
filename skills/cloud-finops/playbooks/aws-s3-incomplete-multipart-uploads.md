---
name: aws-s3-incomplete-multipart-uploads
scope: aws
service: Amazon S3
waste_category: orphaned
confidence: obvious
---

# S3 Incomplete Multipart Uploads Never Aborted

## Problem

A multipart upload that fails or is abandoned mid-transfer leaves its
already-uploaded parts in the bucket, billed at the bucket's storage rate,
forever - unless a lifecycle rule aborts them. The parts are invisible in
the console object listing and excluded from the CloudWatch
`BucketSizeBytes` metric, which is exactly why they accumulate for years:
nothing a team normally looks at shows them. Any bucket that receives
large objects over unreliable links (log shippers, backup agents, CI
artefact pushes) grows this waste continuously. The fix is a one-line
lifecycle rule with essentially no risk.

## Symptoms

- Buckets receiving large uploads (backups, media, ML artefacts) with no
  lifecycle rule containing `AbortIncompleteMultipartUpload`
- S3 Storage Lens shows non-zero **incomplete multipart upload bytes**
  (in the free tier of Lens metrics) on buckets nobody can explain
- Billed storage for a bucket exceeds what the console object listing and
  `BucketSizeBytes` suggest

## Detection

Beware the existence trap: "the bucket has a lifecycle policy" is not the
check. A `Disabled` rule, or a rule filtered to a prefix that matches
nothing, passes an existence check and still covers 0% of the bucket.
Parse rule coverage, not rule presence.

```bash
# Read-only. Flags every bucket with no ENABLED whole-bucket
# AbortIncompleteMultipartUpload rule. A bucket with no lifecycle
# configuration at all returns an error, which the loop treats as "no rule".
for b in $(aws s3api list-buckets --query 'Buckets[].Name' --output text); do
  rule=$(aws s3api get-bucket-lifecycle-configuration --bucket "$b" \
    --query "Rules[?Status=='Enabled' && AbortIncompleteMultipartUpload && (Filter.Prefix=='' || Filter==null)] | length(@)" \
    --output text 2>/dev/null)
  [ "$rule" = "0" ] || [ -z "$rule" ] && echo "NO ABORT RULE: $b"
done

# Sizing the waste on a flagged bucket (LIST-request charges apply; on
# very large buckets sample first). Ongoing in-progress uploads younger
# than a few days are legitimate - look at Initiated dates.
aws s3api list-multipart-uploads --bucket BUCKET \
  --query 'Uploads[].{key:Key,initiated:Initiated}' --output table
```

If S3 Storage Lens is already enabled, its `IncompleteMPUStorageBytes`
metric gives the org-wide sizing without any per-bucket LIST cost - use it
to rank before looping. Classification is `obvious`: stale incomplete-MPU
bytes plus a missing abort rule is one compound signal, and the fix cannot
break anything that a 7-day threshold does not explicitly allow for. The
entire detection runs on read-only APIs - no configuration change is
needed to reach a decision.

## Fix

1. Add a whole-bucket lifecycle rule with
   `AbortIncompleteMultipartUpload: { DaysAfterInitiation: 7 }`. The only
   workload this can break is an upload legitimately running longer than
   7 days - raise the threshold for those rare buckets rather than
   skipping the rule.
2. Apply it as a default in the IaC module or template that creates
   buckets, so every future bucket is covered at creation.
3. Existing stale parts are removed by the rule itself once it takes
   effect - no manual cleanup pass is needed.

## Anti-pattern

- Scoping the abort rule to a prefix "to be careful". Incomplete parts
  land wherever uploads fail; a prefix-scoped abort rule leaves the rest
  of the bucket accumulating.
- Treating this as part of a storage-tiering decision. Aborting dead parts
  is garbage collection with realised savings; do not gate it behind the
  slower cold-data-transition analysis
  (`playbooks/aws-s3-cold-data-in-standard.md`).

## See also

- `playbooks/aws-s3-noncurrent-version-sprawl.md` - the versioning-side
  garbage-collection twin
- `playbooks/aws-s3-cold-data-in-standard.md` - the transition (tiering)
  decision, which needs far more evidence than this one
- `references/finops-aws.md` - S3 billing mechanics, Storage Lens setup
- `references/finops-waste-detection-playbooks.md` - the eight-category
  taxonomy this pattern fits ("orphaned")

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
