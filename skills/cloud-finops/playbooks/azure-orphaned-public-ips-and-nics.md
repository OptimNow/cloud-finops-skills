---
name: azure-orphaned-public-ips-and-nics
scope: azure
service: Azure Public IP / Network Interface
waste_category: orphaned
confidence: obvious
---

# Azure Orphaned Public IPs and NICs

## Problem

A Standard SKU public IP address bills every hour it exists (~$0.005/hr,
roughly $3.65/month; illustrative list rate, written August 2026) whether
or not it is attached to anything. Deleting a VM does not delete its
public IP or its network interface - both survive as free-floating
resources, and every deleted VM, torn-down load balancer, or abandoned
migration leaves a few behind. The NIC itself is not billed, but orphaned
NICs matter twice over: they frequently hold the orphaned public IP (so
the IP cannot be released until the NIC goes), and they block subnet and
VNet deletion during cleanup. Since the Basic SKU retirement (September
2025), every remaining public IP is a billed Standard SKU one.

## Symptoms

- Public IPs whose `ipConfiguration` is empty in the portal's
  "Associated to" column
- NICs left behind by deleted VMs, recognisable by the dead VM's name
  in their own
- Subnet or VNet deletions failing with "in use" errors caused by
  resources nobody can name
- Public IP count in a subscription far exceeding the running VM +
  load balancer + firewall count

## Detection

Single signal - an unassociated public IP is pure spend:

```kusto
// Azure Resource Graph - public IPs attached to nothing
resources
| where type =~ "microsoft.network/publicipaddresses"
| where isempty(properties.ipConfiguration) and isempty(properties.natGateway)
| extend allocation = tostring(properties.publicIPAllocationMethod)
| extend skuName    = tostring(sku.name)
| project subscriptionId, resourceGroup, name, skuName, allocation, location
| order by name asc
```

Both emptiness checks matter: a load balancer, firewall, or VM NIC
association fills `ipConfiguration`, while a NAT Gateway association
fills `natGateway` - an IP is only orphaned when both are empty.

The companion query for orphaned NICs:

```kusto
// Azure Resource Graph - NICs attached to no VM and owned by no
// platform service (private endpoints and Private Link services
// create NICs that legitimately have no VM - exclude them)
resources
| where type =~ "microsoft.network/networkinterfaces"
| where isempty(properties.virtualMachine)
| where isempty(properties.privateEndpoint)
| where isempty(properties.privateLinkService)
| extend hasPublicIp = tostring(properties.ipConfigurations[0].properties.publicIPAddress.id)
| project subscriptionId, resourceGroup, name, hasPublicIp, location
```

## Fix

Ordered safest-first, because a released public IP address returns to
the Azure pool and **cannot be recovered**:

1. For each orphaned IP, search DNS zones, firewall rules, and partner
   allowlists for the literal address before touching it. An address
   that external parties have pinned is a coordination task, not a
   cleanup task.
2. Delete orphaned NICs first (`az network nic delete`) - this detaches
   any public IP they hold and unblocks subnet cleanup. NICs bill
   nothing, so this step is pure hygiene with no rollback concern
   beyond step 1's check.
3. Delete the now-unassociated public IPs
   (`az network public-ip delete`).
4. Prevent recurrence: create VMs with the NIC and public IP deletion
   options set to delete-with-VM (`--nic-delete-option Delete` and the
   public IP equivalent on the ipconfig), and put an Azure Policy audit
   on unassociated public IPs so the estate stays clean.

## Anti-pattern

- Releasing a static public IP that a partner firewall or an external
  DNS record still points at. The address is gone for good; the
  breakage surfaces days later as a third party's connectivity ticket.
- Deleting NICs by name pattern without the private-endpoint exclusion
  above. A private endpoint's NIC has no VM by design; deleting it
  severs the private endpoint.
- Skipping the orphan sweep during VM deletion "to save time" and
  planning a quarterly cleanup instead. The IPs bill daily; the
  delete-with-VM options in Fix step 4 cost nothing to set.

## See also

- `playbooks/azure-orphan-disks.md` - the same abandonment pattern one
  resource type over; run the two sweeps together
- `playbooks/azure-idle-vm.md` - the deallocation state where public
  IP allocation methods start to matter
- `references/finops-azure.md` - Azure networking cost mechanics
- `references/finops-waste-detection-playbooks.md` - "orphaned"
  category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
