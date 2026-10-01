---
name: azure-blob-version-and-soft-delete-sprawl
scope: azure
service: Azure Blob Storage
waste_category: orphaned
confidence: likely
---

# Azure Blob Version and Soft-Delete Sprawl

## Problem

Two safety features keep bytes alive after the application has
overwritten or deleted them. **Blob soft delete** (on by default, with
7-day retention, for accounts created in the Azure portal; off for
accounts created with the CLI, PowerShell or a template unless set;
configurable from 1 to 365 days) holds deleted blobs at the full rate of
their tier until the retention window expires. Without versioning, it
also turns every overwrite into a soft-deleted snapshot of the previous
content, so a high-churn container pays for its history even when nobody
switched versioning on. **Blob versioning**, once enabled, turns every overwrite into a
retained previous version with no expiry at all unless a lifecycle rule
deletes it. On a high-churn container (Terraform state, nightly exports,
ML checkpoints, log shippers that rewrite whole files) the retained history
can exceed the live data within months. The reason it hides: Azure Monitor
`BlobCapacity` and the Cost Management meters bill versions and soft-deleted
data under the same `Data Stored` meter as live data, so the account looks
"the right size" while the container listing, which shows current blobs
only, looks small. The billing subtlety that makes it worse than it sounds:
versions are charged on *unique blocks*, but most SDK uploads rewrite the
whole blob with new block IDs, so a version is in practice a full copy.

## Symptoms

- `isVersioningEnabled: true` on the blob service with no lifecycle rule
  carrying a `version.delete` action
- Soft-delete retention set to 90, 180 or 365 days "to be safe" on
  containers nobody has ever restored from
- `BlobCapacity` grows while `BlobCount` (current blobs) is flat
- The account hosts Terraform state, CI artefacts, exports, model
  checkpoints or anything rewritten on a schedule
- Point-in-time restore or object replication was enabled during a project
  and never reviewed afterwards (both require versioning and keep it on)

## Detection

Resource Graph carries the storage account but not its blob-service
properties, so the first pass is a CLI loop over accounts. Read-only.

```bash
# Stage 1: which accounts retain history with no pruning rule.
# Prerequisite: Reader on the subscriptions. Check the property names
# against one account first (az storage account blob-service-properties
# show); they are stable but the CLI output shape has changed before.
for acct in $(az storage account list --query "[?kind!='FileStorage'].name" -o tsv); do
  rg=$(az storage account show -n "$acct" --query resourceGroup -o tsv)
  props=$(az storage account blob-service-properties show -n "$acct" -g "$rg" -o json 2>/dev/null) || continue
  ver=$(echo "$props" | jq -r '.isVersioningEnabled // false')
  sd=$(echo "$props" | jq -r '.deleteRetentionPolicy.enabled // false')
  sd_days=$(echo "$props" | jq -r '.deleteRetentionPolicy.days // 0')
  rules=$(az storage account management-policy show -n "$acct" -g "$rg" -o json 2>/dev/null \
          | jq '[.policy.rules[]? | select(.enabled==true) | select(.definition.actions.version.delete!=null)] | length')
  if [ "$ver" = "true" ] && [ "${rules:-0}" = "0" ]; then
    echo "VERSIONED, NO VERSION-DELETE RULE: $acct"
  fi
  if [ "$sd" = "true" ] && [ "$sd_days" -gt 30 ]; then
    echo "SOFT DELETE RETENTION ${sd_days}d: $acct"
  fi
done
```

Stage 2 sizes the flagged accounts, and this is where "no result" and "no
data" must be told apart. `BlobCapacity` cannot split live from retained
bytes. The ground truth is a **Blob Inventory** rule on the account (a
configuration change: if it is not enabled, enabling it on the top-spend
accounts and re-running in a week is the finding). Include the
`IsCurrentVersion`, `VersionId`, `Deleted` and `Content-Length` fields,
output Parquet, and sum bytes by container where `IsCurrentVersion = false`
or `Deleted = true`. A quick sample without Inventory, per container:

```bash
# Sample only: counts current, version and soft-deleted blobs in one
# container. --include v,d lists versions and deleted blobs. Slow on large
# containers; use it to confirm the pattern, not to size it.
az storage blob list --account-name "$acct" -c "$container" --auth-mode login \
  --include v,d --query "[].{cur:isCurrentVersion, del:deleted, size:properties.contentLength}" -o json \
  | jq '{current_gib: ([.[] | select(.cur==true and (.del|not)) | .size] | add // 0) / 1073741824,
         versions_gib: ([.[] | select(.cur!=true and (.del|not)) | .size] | add // 0) / 1073741824,
         deleted_gib:  ([.[] | select(.del==true) | .size] | add // 0) / 1073741824}'
```

Classification is `likely`: act on the missing rule AND retained bytes
above roughly 20% of current bytes. The blocker check keeps it from being
`obvious`: an immutability policy or legal hold, **point-in-time restore**
(needs versioning, soft delete and change feed for its restore window),
and **object replication** (needs versioning on source and destination)
all legitimately retain versions, and the retention they need sets the
floor for any rule you add.

## Fix

1. Run the blocker check per account: immutability policies, legal holds,
   point-in-time restore window, object replication policies, and the
   owning team's real restore requirement (how many versions, how long).
2. Right-size soft-delete retention to the incident window the team has
   actually used, typically 7 to 14 days. Soft-deleted data is purged by
   the retention setting itself, not by lifecycle rules, so the number of
   days is the whole lever. Do the same for container soft delete.
3. Add a lifecycle rule with `version.delete.daysAfterCreationGreaterThan`
   at 30 to 90 days. Where the team needs rollback depth rather than a time
   window, add `version.tierToCool` or `tierToCold` first and delete later;
   the version tier-down pays the early-deletion window of the target tier,
   so keep the delete day beyond it.
4. Bake the rule and the retention values into the storage-account Bicep
   module, and add an Azure Policy audit effect on
   `Microsoft.Storage/storageAccounts/blobServices` for versioning enabled
   without a management policy.

Sources: <https://learn.microsoft.com/en-us/azure/storage/blobs/soft-delete-blob-overview>
(billing at the active-data rate, overwrite behaviour, purge at retention
expiry) and
<https://learn.microsoft.com/en-us/azure/storage/blobs/soft-delete-blob-enable>
(portal default versus CLI and PowerShell), both read 1 October 2026.

## Anti-pattern

- Disabling versioning to stop the growth. Existing versions stay and keep
  billing until something deletes them, point-in-time restore stops
  working, and the protection versioning gave is gone while the cost is
  not.
- Pruning versions on the *destination* account of an object replication
  policy, or on an account inside a point-in-time restore window shorter
  than the rule.
- One subscription-wide retention number. A Terraform state container needs
  deep history on a few small blobs; an export container needs almost none
  on many large ones.
- Confusing the `snapshot` and `version` actions in the lifecycle rule.
  Legacy snapshots and versions are separate objects with separate rule
  actions; a rule that only deletes snapshots leaves every version in
  place.

## See also

- `playbooks/azure-blob-cold-data-in-hot.md` - the tiering decision on the
  bytes that survive the pruning rule
- `playbooks/aws-s3-noncurrent-version-sprawl.md` - the AWS twin, same
  detection style and the same blocker list shape
- `playbooks/azure-snapshot-sprawl.md` - the managed-disk side of
  retention sprawl
- `references/finops-azure.md` - "Soft delete and versioning - default-on
  cost traps" and the lifecycle rule examples
- `references/finops-waste-detection-playbooks.md` - the eight-category
  taxonomy this pattern fits ("orphaned")

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
