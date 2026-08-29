---
name: azure-idle-vm
scope: azure
service: Azure Virtual Machines
waste_category: idle
confidence: obvious
---

# Azure Idle VM (Stopped but Not Deallocated)

## Problem

Azure bills VM compute by allocation, not by activity, and it
distinguishes two "off" states that look identical from inside the OS.
A VM shut down **from within the guest OS** (or via a bare `az vm stop`)
lands in the **stopped** state: the hardware stays reserved and **compute
billing continues at the full rate**. Only the **deallocated** state
(portal Stop button, `az vm deallocate`) releases the hardware and stops
compute charges. Teams that "switched the server off" from inside Windows
or Linux routinely pay months of full compute for machines doing nothing.
Managed disks and static public IPs keep billing in both states - that is
expected and separate.

## Symptoms

- VMs whose power state reads `PowerState/stopped` rather than
  `PowerState/deallocated` for days or weeks
- A cost report showing full compute spend on machines the owning team
  believes are "turned off"
- Shutdown schedules implemented as in-guest cron/Task Scheduler jobs
  (they can only reach the stopped state, never deallocated)
- RDP/SSH unreachable but the VM still accrues compute cost

## Detection

Single signal, straight from Azure Resource Graph - a VM sitting in
`stopped` is billing for nothing, full stop:

```kusto
// Azure Resource Graph - VMs stopped but NOT deallocated (still billed)
resources
| where type =~ "microsoft.compute/virtualmachines"
| extend powerState = tostring(properties.extended.instanceView.powerState.code)
| where powerState == "PowerState/stopped"
| extend vmSize = tostring(properties.hardwareProfile.vmSize)
| project subscriptionId, resourceGroup, name, vmSize, powerState, location
| order by vmSize desc
```

`properties.extended` is populated by Resource Graph for VMs; if the
column comes back empty across the board, the tenant may not yet surface
extended properties in ARG - fall back to
`az vm list -d --query "[?powerState=='VM stopped']"` which reads the
same instance view per VM.

Resource Graph carries inventory, not cost: to price the finding, join
the VM list to the Cost Management / FOCUS export on the lowercased
resource ID, or simply read the `vmSize` column - the on-demand rate of
the size is what each machine burns per hour while stopped.

The neighbouring pattern - a **running** VM with near-zero CPU and
network - is a real but separate finding: it needs Azure Monitor metrics
(two signals, `likely` tier) and rightsizing judgement. See
`references/finops-azure.md` for that methodology; do not classify
running VMs from this playbook.

## Fix

1. Deallocate every VM the query returns:
   `az vm deallocate -g <rg> -n <name>`. Data on managed disks is
   preserved; only the ephemeral temp disk is lost, plus dynamic public
   IPs and the hardware placement.
2. Replace in-guest shutdown jobs with mechanisms that deallocate:
   the DevTest Labs **auto-shutdown** setting on the VM, an Automation
   runbook, or Azure Functions on a schedule.
3. For dev/test estates, pair deallocation with a start schedule -
   the full pattern is in `cross-cloud-schedule-blindness.md`.
4. Re-run the Detection query weekly; a machine that keeps reappearing
   has an owner who needs the stopped-vs-deallocated explanation, not
   another deallocation.

## Anti-pattern

- Deallocating a VM that holds a **dynamic** public IP or relies on its
  placement: the IP is released and a different one is assigned on
  restart, breaking DNS records and firewall allowlists. Check the IP
  allocation method first; convert to static if the address matters.
- Treating deallocation as free: managed disks, static public IPs, and
  any reservation covering the size keep billing. A deallocated VM
  covered by a reservation wastes the reservation instead - if the
  machine stays down, the reservation needs re-scoping
  (`azure-unused-reservation`).
- Deleting stopped VMs outright on the theory they are abandoned. The
  stopped state is often a mistaken shutdown of something that matters;
  deallocate first, delete only after an ownership check.

## See also

- `playbooks/cross-cloud-schedule-blindness.md` - the scheduling
  discipline that prevents the pattern recurring
- `playbooks/azure-unused-reservation.md` - where the waste moves if a
  reserved VM stays deallocated
- `references/finops-azure.md` - Azure compute billing mechanics and
  rightsizing methodology (the metrics-based idle-VM variant)
- `references/finops-waste-detection-playbooks.md` - "idle" category
  rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
