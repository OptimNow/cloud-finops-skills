---
name: azure-orphan-disks
scope: azure
service: Azure Managed Disks
waste_category: orphaned
confidence: obvious
---

# Azure Orphan Managed Disks

## Problem

Azure Managed Disks are billed by tier and capacity (Standard SSD ~
$0.075/GB-month, Premium SSD ~$0.12/GB-month, Ultra Disk significantly
more) regardless of whether they are attached to a VM. Disks routinely
become orphans when a VM is deleted with the disk's deletion option set
to "detach", when an AKS cluster is recreated, or after a migration
that left source disks in place. A 1 TB Premium SSD orphan accrues
~$120/month for as long as it exists.

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
| where managedBy == ""
| extend size_gb     = toint(properties.diskSizeGB)
| extend tier        = tostring(sku.name)
| extend created     = todatetime(properties.timeCreated)
| extend ageInDays   = datetime_diff('day', now(), created)
| where ageInDays > 30
| project subscriptionId, resourceGroup, name, tier, size_gb, ageInDays, created
| order by size_gb desc
```

For attribution-grade cost per orphan disk, join to the FOCUS export or
Cost Management billing data:

```kusto
// Azure Cost Management export joined to Resource Graph orphan list
costManagementBillingData
| where ResourceType == "microsoft.compute/disks"
  and CostInBillingCurrency > 0
| summarize cost30d = sum(CostInBillingCurrency) by ResourceId
| join kind=inner (
    resources
    | where type =~ "microsoft.compute/disks" and managedBy == ""
    | project ResourceId = id, name
  ) on ResourceId
| order by cost30d desc
```

## Fix

1. Snapshot the disk before deletion (Azure Disk Snapshot is cheap and
   the snapshot retains all data; deletion of a Premium SSD without a
   snapshot is irreversible).
2. Delete disks where:
   - `managedBy == ""` for > 30 days
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
