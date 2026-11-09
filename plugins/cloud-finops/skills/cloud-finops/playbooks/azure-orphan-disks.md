---
name: azure-orphan-disks
scope: azure
service: Azure Managed Disks
waste_category: orphaned
confidence: obvious
questions:
  - "Which Azure managed disks are attached to nothing?"
  - "Is it safe to delete disks left behind by deleted VMs?"
  - "Why do Azure disks survive when we delete the VM?"
  - "How much do orphan managed disks cost us per month?"
  - "Quels disques managés Azure ne sont rattachés à aucune VM, et peut-on les supprimer ?"
---

# Azure Orphan Managed Disks

## Problem

Azure Managed Disks are billed by tier and capacity regardless of whether
they are attached to a VM: at East US list rates read in November 2026, a
1 TiB Standard SSD (E30) is ~$77/month, about $0.075/GB-month, and a 1 TiB
Premium SSD (P30) is ~$135/month, about $0.13/GB-month, with Ultra Disk
well above both. Disks routinely become orphans when a VM is deleted with
the disk's deletion option set to "detach", when an AKS cluster is
recreated, or after a migration that left source disks in place. A 1 TiB
Premium SSD orphan accrues that ~$135/month for as long as it exists. The
rates are illustrative and vary by region; verify against the Azure
pricing page before sizing a business case.

## Symptoms

- The disk's `ManagedBy` property is null (no parent VM / VMSS)
- Created during a project that has since been decommissioned
- Owned by a resource group whose other resources are all gone
- The disk's name pattern matches a stopped-deallocated VM that no
  longer exists

## Detection

```kusto
// Azure Resource Graph - find all unattached managed disks
resources
| where type =~ "microsoft.compute/disks"
| where isempty(managedBy)   // catches both null and empty-string
| extend size_gb     = toint(properties.diskSizeGB)
| extend tier        = tostring(sku.name)
| extend created     = todatetime(properties.timeCreated)
| extend ageInDays   = datetime_diff('day', now(), created)
| where ageInDays > 30
| project subscriptionId, resourceGroup, name, tier, size_gb, ageInDays, created
| order by size_gb desc
```

Resource Graph carries inventory, not cost - there is no billing table to
join against inside ARG. To get cost per orphan disk, export the orphan list
above and join it to billing data outside Resource Graph, keying on the
resource ID (lowercased on both sides; ARG returns mixed case and the cost
exports do not):

- **FOCUS export / Cost Management export** (recommended): join on
  `ResourceId` from the export to `id` from the query above, filtering
  `ServiceCategory == "Storage"`.
- **Cost Management Query API**: `POST` to
  `/providers/Microsoft.CostManagement/query` scoped to the subscription,
  grouped by `ResourceId`, with a filter on
  `ResourceType = "microsoft.compute/disks"`.

If you only need a ranking rather than exact cost, the `size_gb` and `tier`
columns from the inventory query are enough to sort by rough monthly spend -
Premium SSD (`Premium_LRS`) costs several times Standard HDD (`Standard_LRS`)
per GB, so tier dominates the ordering.

## Fix

1. Snapshot the disk before deletion (Azure Disk Snapshot is cheap and
   the snapshot retains all data; deletion of a Premium SSD without a
   snapshot is irreversible).
2. Delete disks where:
   - `isempty(managedBy)` for > 30 days
   - No matching VM in the snapshot history
   - No matching backup vault recovery point
3. Set the **VM disk deletion option to "Delete"** at VM creation time
   so detached disks don't accumulate on VM deletion.
4. For AKS, configure the CSI driver's `reclaimPolicy: Delete` on
   StorageClasses so PVC deletion releases the underlying Managed Disk.

## Anti-pattern

- Deleting orphans by name pattern without confirming `managedBy` is
  empty. A disk attached to a stopped-deallocated VM is NOT orphan -
  the VM is still billed for any reservation, and the disk is
  intentional.
- Deleting all "Standard HDD" orphans assuming they are obsolete tiers.
  Some compliance archives are intentionally on Standard HDD for cost.

## See also

- `references/finops-azure.md` - Azure storage billing mechanics, Disk
  tiers, MCA contractual mechanics
- `references/finops-waste-detection-playbooks.md` - "orphaned" category
  rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
