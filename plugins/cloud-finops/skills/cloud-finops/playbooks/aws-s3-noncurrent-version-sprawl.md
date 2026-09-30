---
name: aws-s3-noncurrent-version-sprawl
scope: aws
service: Amazon S3
waste_category: orphaned
confidence: likely
---

# S3 Noncurrent Version Sprawl

## Problem

Versioning-enabled buckets keep every overwritten and deleted object as a
noncurrent version, billed at full storage rates, until a lifecycle rule
expires them. With no `NoncurrentVersionExpiration` rule, a bucket with
high overwrite churn (state files, exports, rebuilt artefacts) can carry
several times its current data volume in invisible history. The related
leak: delete markers whose versions have all expired still count as
objects and slow listings unless expired-delete-marker cleanup is on. A
subtlety that hides the problem: CloudWatch `BucketSizeBytes` *includes*
noncurrent versions, so the billed size looks "right" while the console
object listing - current versions only - looks small, and nobody
reconciles the two.

## Symptoms

- Versioning `Enabled` (or `Suspended`, which still retains existing
  versions) with no `NoncurrentVersionExpiration` lifecycle rule
- Storage Lens `NonCurrentVersionStorageBytes` is a large share of a
  bucket's total bytes
- `BucketSizeBytes` far exceeds what the console listing suggests
- High-churn workloads (Terraform state, nightly exports, CI artefacts)
  write to the bucket

## Detection

```bash
# Read-only. Flags versioned buckets with no enabled
# NoncurrentVersionExpiration rule. As with the multipart playbook,
# parse rule coverage, not rule presence - a Disabled or prefix-scoped
# rule is not coverage.
for b in $(aws s3api list-buckets --query 'Buckets[].Name' --output text); do
  v=$(aws s3api get-bucket-versioning --bucket "$b" --query 'Status' --output text 2>/dev/null)
  if [ "$v" = "Enabled" ] || [ "$v" = "Suspended" ]; then
    rule=$(aws s3api get-bucket-lifecycle-configuration --bucket "$b" \
      --query "Rules[?Status=='Enabled' && NoncurrentVersionExpiration] | length(@)" \
      --output text 2>/dev/null)
    [ "$rule" = "0" ] || [ -z "$rule" ] && echo "VERSIONED, NO EXPIRY RULE: $b ($v)"
  fi
done
```

Sizing the flagged buckets needs a metric that splits current from
noncurrent - `BucketSizeBytes` cannot (it lumps them together). Storage
Lens `NonCurrentVersionStorageBytes` (free tier) is the cheap answer; S3
Inventory with `IsLatest` gives object-level ground truth where a bucket
is worth the deeper look. Classification is `likely` - two signals before
acting: the missing rule AND noncurrent bytes above roughly 20% of
current bytes. The blocker check is what keeps this from being `obvious`:
Object Lock, legal holds, replication relationships where this bucket is
the surviving copy, or a genuine point-in-time recovery requirement all
legitimately retain versions.

## Fix

1. Run the blocker check per bucket: Object Lock / legal hold status,
   replication configuration, and the owning team's actual recovery
   requirement (how many versions, for how long).
2. Add `NoncurrentVersionExpiration` at 30-90 days, with
   `NewerNoncurrentVersions` set to keep the last N versions where the
   team needs rollback depth rather than a pure time window.
3. Set `ExpiredObjectDeleteMarker: true` in the same rule so
   fully-expired objects do not leave marker debris behind.
4. Bake both into the bucket-creation IaC module alongside the multipart
   abort rule.

## Anti-pattern

- Turning versioning off to stop the growth. Suspending versioning does
  not delete existing noncurrent versions (they keep billing) and it
  removes the protection versioning was providing - the expiry rule
  achieves the saving while keeping the safety.
- Expiring versions on a bucket that is the replication *destination* of
  a compliance copy - check replication topology before, not after.
- Applying one org-wide retention number to every bucket. A Terraform
  state bucket needs deep version history on a few small objects; a
  nightly-export bucket needs almost none on many large ones.

## See also

- `playbooks/aws-s3-incomplete-multipart-uploads.md` - the other S3
  garbage-collection rule, same detection style
- `playbooks/aws-s3-cold-data-in-standard.md` - the tiering decision on
  the bytes that survive expiry
- `playbooks/aws-snapshot-sprawl.md` - the EBS-side retention sprawl twin
- `references/finops-aws-patterns.md` - Storage Optimization Patterns, the
  S3 lifecycle and storage-class patterns plus Storage Lens usage
- `references/finops-waste-detection-playbooks.md` - the eight-category
  taxonomy this pattern fits ("orphaned")

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
