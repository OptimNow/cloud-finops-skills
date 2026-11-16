---
name: azure-ddos-plan-unassociated
scope: azure
service: Azure DDoS Protection
waste_category: orphaned
confidence: obvious
questions:
  - "We pay for an Azure DDoS Protection plan. Does it protect anything?"
  - "How do we find DDoS protection plans with no virtual network attached?"
  - "Do we need one DDoS protection plan per subscription?"
  - "DDoS Network Protection or IP Protection: which tier fits a handful of public IPs?"
  - "Nous payons un plan Azure DDoS Protection : protège-t-il encore un réseau virtuel ?"
---

# Azure DDoS Protection Plan With No Virtual Network

## Problem

A DDoS Network Protection plan carries a fixed monthly charge, which covers up to 100
public IP addresses, from the day it exists. It protects only the virtual networks
associated with it, so a plan with none protects nothing and still bills in full.
Plans end up empty when a landing-zone template creates one per subscription, when a
pilot ends, when the protected VNets are rebuilt elsewhere, or when someone disables
protection on the VNets: that leaves the plan in place, still billing. One plan can serve every
subscription of a tenant, so a second plan is usually a duplicate as well. Microsoft's
FinOps best practices name the unassociated plan as waste to remove
([Networking best practices](https://learn.microsoft.com/en-us/cloud-computing/finops/best-practices/networking),
[DDoS Protection FAQ](https://learn.microsoft.com/en-us/azure/ddos-protection/ddos-faq),
[Configure DDoS Network Protection](https://learn.microsoft.com/en-us/azure/ddos-protection/manage-ddos-protection),
read 16 November 2026).

## Symptoms

- A DDoS Protection line on the bill, and no VNet whose "DDoS protection" setting
  shows the plan
- More than one DDoS protection plan in the tenant
- Plans named after a landing zone, a subscription or a project that has ended
- A security baseline that requires DDoS protection, with VNets that are not attached
  to the plan it paid for

## Detection

Single signal: a plan whose list of virtual networks is empty is pure spend. Run it
over every subscription of the tenant, so duplicates show up side by side:

```kusto
// Azure Resource Graph - DDoS protection plans and how many VNets each protects
resources
| where type =~ "microsoft.network/ddosprotectionplans"
| extend vnetCount = coalesce(array_length(properties.virtualNetworks), 0)
| project subscriptionId, resourceGroup, name, location, vnetCount
| order by vnetCount asc, name asc
```

Resource Graph returns only the subscriptions the reader can see: a plan in any other
subscription is missed, not cleared, so run it with Reader on the whole tenant. More
than one row with `vnetCount > 0` is the duplicate case: the VNets can move to one
plan.

## Fix

1. Take the list to the security owner first. DDoS protection is often a compliance
   control, and the right answer can be to attach the VNets the baseline requires
   rather than delete the plan.
2. Consolidate duplicates: associate every protected VNet with one plan, then delete
   the others. The plan works across subscriptions in the tenant.
3. Delete plans with no VNet (`az network ddos-protection delete --name <plan>
   --resource-group <rg>`). Disabling protection on the VNets is not enough: the plan
   bills until the plan resource itself is deleted.
4. Where only a few public IPs need protection, compare with the IP Protection tier,
   priced per protected IP rather than per plan, on the
   [pricing page](https://azure.microsoft.com/pricing/details/ddos-protection/) with
   its read date.
5. Stop the template that creates one plan per subscription: the landing zone should
   reference the tenant's single plan.

## Anti-pattern

- Deleting a plan the security team relies on because its VNets were never attached.
  The waste is real, but the fix may be the attachment, and the decision is theirs.
- Keeping one plan per subscription "for isolation". Protection and billing follow the
  plan, not the subscription, so the extra plans add cost and no protection.
- Treating the per-plan charge as covering every public IP in the tenant. It covers the
  public IPs in the protected VNets, up to 100, and more are billed on top.

## See also

- `playbooks/azure-orphaned-public-ips-and-nics.md` - the IPs a plan would protect,
  often orphaned by the same project ending
- `playbooks/azure-idle-vnet-gateway.md` - another fixed-fee network resource that
  outlives its project
- `references/finops-azure.md` - Azure networking cost mechanics
- `references/finops-waste-detection-playbooks.md` - "orphaned" category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
