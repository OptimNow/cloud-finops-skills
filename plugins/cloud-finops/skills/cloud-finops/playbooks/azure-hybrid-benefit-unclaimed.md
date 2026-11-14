---
name: azure-hybrid-benefit-unclaimed
scope: azure
service: Azure Virtual Machines / SQL Server on Azure VMs
waste_category: commitment-mismatch
confidence: likely
questions:
  - q: "Which of our Azure Windows and SQL Server VMs pay for a licence we already own?"
    persona: "FinOps lead"
    also: ["finops-itam"]
  - "We have Software Assurance. How do we find the VMs where Azure Hybrid Benefit was never switched on?"
  - "Our SQL Server VMs claim the Windows benefit but we still pay for the SQL Server licence. Why?"
  - "Can we bring our Red Hat or SUSE subscriptions to Azure VMs that run pay-as-you-go images?"
  - "Quelles VM Windows et SQL Server paient sur Azure une licence que nous possédons déjà ?"
---

# Unclaimed Azure Hybrid Benefit

## Problem

A Windows Server or SQL Server VM deployed from a marketplace image bills the
licence inside its hourly rate unless a property on the resource says the
organisation brings its own. An organisation that owns licences with Software
Assurance, or subscription licences, pays twice on every VM where that
property was never set: once to Microsoft Licensing, once on the Azure bill.
The setting is per resource. A subscription does not pass it down, and a VM
rebuilt from a template that does not carry it loses it. SQL Server on a VM
has a second, separate switch, and RHEL and SLES use their own values of the
VM property, so a fleet can look covered on one check and still pay on the
other two.

## Symptoms

- The licence inventory shows Windows Server or SQL Server core licences
  under active Software Assurance, and the Azure estate was built by teams
  that never saw that inventory
- Cost Management shows SQL Server licence meters on virtual machines (the
  SQL licence is its own meter; the Windows share is folded into the VM rate)
- VMs created or rebuilt through infrastructure as code whose templates
  carry no `licenseType`
- A migration from on-premises that ended months ago, with the licences it
  freed never assigned in Azure
- Red Hat or SUSE subscriptions bought centrally while the VMs run
  pay-as-you-go marketplace images

## Detection

Three read-only Azure Resource Graph queries, one per switch. They are written
from the property names in Microsoft's API references and were not run
against a live estate: check one VM whose status you know before trusting the
counts.

```kusto
// 1. Windows VMs paying the licence inside the VM rate
resources
| where type =~ "microsoft.compute/virtualmachines"
| where tostring(properties.storageProfile.osDisk.osType) =~ "Windows"
| extend licenseType = tostring(properties.licenseType),
         vmSize = tostring(properties.hardwareProfile.vmSize),
         powerState = tostring(properties.extended.instanceView.powerState.code)
| where licenseType !in~ ("Windows_Server", "Windows_Client")
| project subscriptionId, resourceGroup, name, vmSize, powerState, licenseType
```

`Windows_Server` is the benefit for Windows Server and `Windows_Client` the
licensed state of a Windows desktop VM; an empty value or `None` means the
licence is billed in the VM price.

```kusto
// 2. SQL Server VMs still paying the SQL licence meter
resources
| where type =~ "microsoft.sqlvirtualmachine/sqlvirtualmachines"
| extend sqlLicense = tostring(properties.sqlServerLicenseType),
         edition = tostring(properties.sqlImageSku),
         vmId = tostring(properties.virtualMachineResourceId)
| where sqlLicense =~ "PAYG" and edition in~ ("Standard", "Enterprise")
| project subscriptionId, resourceGroup, name, edition, sqlLicense, vmId
```

Only VMs registered with the SQL IaaS Agent extension exist as this resource
type. A SQL Server VM absent from the result is unregistered, not proven
covered: compare the row count with the SQL Server VMs you know of.

```kusto
// 3. RHEL and SLES VMs on the pay-as-you-go software meter
resources
| where type =~ "microsoft.compute/virtualmachines"
| extend publisher = tostring(properties.storageProfile.imageReference.publisher),
         offer = tostring(properties.storageProfile.imageReference.offer),
         licenseType = tostring(properties.licenseType)
| where publisher in~ ("RedHat", "SUSE")
| where licenseType !in~ ("RHEL_BYOS", "SLES_BYOS")
| project subscriptionId, resourceGroup, name, publisher, offer, licenseType
```

Read the `offer` column before counting a row. A VM deployed from a
bring-your-own-subscription image keeps an empty `licenseType` and already
pays no software fee, and VMs built from custom images do not appear at all.

Resource Graph carries inventory, not cost. To price the finding, filter Cost
Management on the SQL Server licence meters, and compare the Windows and Linux
rates of each VM size for the Windows share. Windows node pools in AKS have
their own query in `references/finops-azure.md`.

Classification is `likely`: the query is the first signal, and the second is
an eligible licence that is free to assign. A listed VM with no licence behind
it is not waste.

## Fix

Ordered safest-first.

1. **Count licences with their owner before touching a VM.** Windows Server
   needs core licences with Software Assurance or subscription licences, with
   a minimum of eight cores per VM. SQL Server needs Standard or Enterprise
   core licences with Software Assurance; Express, Web and Developer editions
   are outside the benefit. The counting rules are in
   `references/finops-itam.md`.
2. **Spend the licences where they return most.** Always-on production before
   scheduled VMs, since a licence assigned to a VM that runs office hours
   still costs its full fee. Large VMs before those under eight cores, where
   the minimum eats licences. SQL Server Enterprise before Standard.
3. **Set the property.** Windows: `licenseType` set to `Windows_Server`. SQL
   Server on a VM: `az sql vm update --license-type AHUB`, which Microsoft
   documents as immediate, with no downtime and no restart of the VM or of the
   SQL Server service. A passive high-availability or disaster-recovery
   replica takes `DR`, the free licence type. RHEL and SLES:
   `az vm update --license-type RHEL_BYOS` or `SLES_BYOS`; the Red Hat route
   needs the subscription enabled for Azure through Red Hat Cloud Access and
   Microsoft lists a VM extension for it, the SUSE route needs none.
4. **Make it survive the next rebuild.** Put the property in the templates and
   modules that create VMs, and audit or deploy it through Azure Policy. For
   SQL Server, centrally managed Azure Hybrid Benefit assigns licences at
   subscription or billing account scope on EA and MCA, in place of the per-VM
   setting.
5. **Size the saving in cascade.** The licence setting comes first because it
   needs no restart and reverses in one command; a schedule or a resize is
   then priced on what it leaves (`references/optimnow-methodology.md`).

Sources: [SQL Server licence model on Azure VMs](https://learn.microsoft.com/en-us/azure/azure-sql/virtual-machines/windows/licensing-model-azure-hybrid-benefit-ahb-change),
[Azure Hybrid Benefit for Windows Server](https://learn.microsoft.com/en-us/azure/virtual-machines/windows/hybrid-use-benefit-licensing)
and [Azure Hybrid Benefit for Linux](https://learn.microsoft.com/en-us/azure/virtual-machines/linux/azure-hybrid-benefit-linux),
read 14 November 2026.

## Anti-pattern

- Switching the property on every VM the query lists. The property is a
  declaration that a licence is assigned; without the licence it is a finding
  in the next licence audit, not a saving.
- Counting VMs in Dev/Test subscriptions. Windows already bills at Linux
  rates there, so the benefit adds nothing.
- Spending the eight-core minimum on a 2-vCPU VM that runs ten hours a day.
- Reading every non-empty `licenseType` on Linux as a benefit. `RHEL_BYOS`
  and `SLES_BYOS` bring a subscription; values such as `RHEL_BASE` mean the
  software fee is charged.
- Assuming the setting holds. Adding a SQL Server VM to an availability set
  recreates it and returns it to pay-as-you-go.

## See also

- `references/finops-itam.md` - the BYOL decision, core counting rules and
  the licence-included premium per provider
- `references/finops-azure-commitments.md` - where the benefit sits in the
  commitment layering, before any reservation or savings plan
- `references/finops-azure.md` - the Resource Graph query for Windows node
  pools in AKS
- `references/optimnow-methodology.md` - sizing stacked savings in cascade
- `playbooks/azure-unused-reservation.md` - the other member of the
  commitment-mismatch family on Azure
- `references/finops-waste-detection-playbooks.md` - the taxonomy and the
  confidence rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
