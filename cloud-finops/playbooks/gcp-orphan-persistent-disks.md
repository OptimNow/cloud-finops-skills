---
name: gcp-orphan-persistent-disks
scope: gcp
service: GCP Compute Engine / GKE Persistent Disks
waste_category: orphaned
confidence: obvious
---

# GCP Orphan Persistent Disks

## Problem

GCP Persistent Disks (Standard / Balanced / SSD / Extreme) bill by
provisioned capacity regardless of attachment. A 1 TB SSD persistent
disk accrues ~$170/month whether or not a VM mounts it. Orphans
accumulate from: deleted VMs whose disks were not in `auto-delete` mode,
GKE PVCs with `reclaimPolicy: Retain` after pod / namespace deletion,
and one-off snapshot-and-detach workflows during migrations.

## Symptoms

- Disk's `users` field is empty (no attached instance)
- Disk created during a project / cluster that has been decommissioned
- Disk lives in a zone with no remaining VMs
- Owning labels / annotations point to a Kubernetes namespace or
  workload that no longer exists

## Detection

```bash
# All unattached persistent disks across a project, sorted by size
gcloud compute disks list --filter="-users:*" --format="value(name,zone,sizeGb,type,creationTimestamp)" \
  | sort -k3 -n -r | head -50
```

```sql
-- BigQuery billing export: PD spend, joined to gcloud orphan list
-- (run gcloud command above first, save orphan disk names to a temp BQ table)
WITH orphans AS (
  SELECT name FROM `<project>.tmp.orphan_disks`
)
SELECT
  resource.name           AS disk,
  SUM(cost)               AS cost_30d,
  SUM(usage.amount)       AS gb_month
FROM `<project>.<dataset>.gcp_billing_export_resource_v1_<account>`
JOIN orphans USING (name)
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND service.description = 'Compute Engine'
  AND sku.description LIKE '%Storage%'
GROUP BY 1
ORDER BY cost_30d DESC;
```

## Fix

1. **Snapshot before delete** (GCP Persistent Disk Snapshot is cheap and
   restorable - typically ~50% the cost of a live disk per GB-month).
2. **Delete disks where**:
   - `users` is empty for > 30 days
   - No matching live VM in any zone in the project
   - No GKE PVC in any cluster references the underlying PD
3. **Configure VM creation with `auto-delete: true`** for the boot disk
   and any data disks that should not outlive the VM. This prevents the
   pattern at source.
4. **For GKE, set StorageClass `reclaimPolicy: Delete`** on classes used
   by ephemeral workloads (CI runners, cache layers). Keep `Retain`
   only for explicitly stateful workloads where data loss is the
   primary concern.

## Anti-pattern

- Deleting orphans without checking for snapshot schedules. A disk that
  is the daily backup target for another disk shows as `users: empty`
  but is doing real work.
- Treating "orphan" as "no labels" - some legitimately-needed disks are
  unlabelled (legacy migrations). Use the API attachment status, not
  label state, as the trigger.

## See also

- `references/finops-gcp.md` - PD pricing tiers (Standard / Balanced /
  SSD / Extreme), snapshot pricing
- `references/finops-kubernetes.md` - GKE volume management, CSI
  reclaim policies
- `playbooks/gcp-idle-gke-autopilot.md` - related GKE waste pattern

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
