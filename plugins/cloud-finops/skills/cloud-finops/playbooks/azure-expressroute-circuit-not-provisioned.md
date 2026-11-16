---
name: azure-expressroute-circuit-not-provisioned
scope: azure
service: Azure ExpressRoute
waste_category: idle
confidence: likely
questions:
  - "Our ExpressRoute circuit shows Not provisioned. Are we still paying for it?"
  - "When does billing start and stop for an Azure ExpressRoute circuit?"
  - "How do we find ExpressRoute circuits that carry no traffic?"
  - "The carrier contract ended. What do we still have to delete in Azure?"
  - "Un circuit ExpressRoute affiche Not provisioned : est-il encore facturé, et comment l'arrêter ?"
---

# Azure ExpressRoute Circuit Not Provisioned

## Problem

An ExpressRoute circuit is billed from the moment its service key is issued, and
Microsoft keeps billing until the circuit is deleted in Azure. Two situations leave a
circuit billed while it carries nothing, and both show the same provider status,
`NotProvisioned`: the circuit was created before the connectivity provider was ready
and the order stalled, or the provider deprovisioned it at the end of a contract and
nobody deleted the Azure side. Deleting the circuit once the provider has
deprovisioned it is what stops the charge. A circuit cannot be deleted while it is
`Provisioning` or `Provisioned`: the provider has to deprovision it first
([Create and modify a circuit](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-howto-circuit-portal-resource-manager),
[Circuit workflows](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-workflows),
read 16 November 2026).

## Symptoms

- A circuit whose provider status reads "Not provisioned" in the portal
- An ExpressRoute line on the bill for a site that moved to another circuit, to
  Virtual WAN or to a VPN
- A carrier contract that ended while the Azure circuit stayed
- A circuit with no gateway connection and no Microsoft peering

## Detection

Two signals: the provider state, and whether anything uses the circuit. A gateway
connection to a circuit is a `connections` resource whose `peer` is the circuit:

```kusto
// Azure Resource Graph - ExpressRoute circuits, provider state, and what uses them
resources
| where type =~ "microsoft.network/expressroutecircuits"
| extend circuitId     = tolower(id)
| extend providerState = tostring(properties.serviceProviderProvisioningState)
| extend provider      = tostring(properties.serviceProviderProperties.serviceProviderName)
| extend peeringSite   = tostring(properties.serviceProviderProperties.peeringLocation)
| extend mbps          = toint(properties.serviceProviderProperties.bandwidthInMbps)
| extend skuTier       = tostring(sku.tier)
| extend skuFamily     = tostring(sku.family)
| extend peerings      = tostring(properties.peerings)
| extend msPeering     = peerings has "MicrosoftPeering"
| join kind=leftouter (
    resources
    | where type =~ "microsoft.network/connections"
    | where tostring(properties.connectionType) =~ "ExpressRoute"
    | extend circuitId = tolower(tostring(properties.peer.id))
    | summarize gatewayConnections = count() by circuitId
  ) on circuitId
| extend gatewayConnections = coalesce(gatewayConnections, 0)
| project subscriptionId, resourceGroup, name, providerState, provider, peeringSite,
          mbps, skuTier, skuFamily, gatewayConnections, msPeering
| order by providerState asc, mbps desc
```

Read the rows in this order:

- `providerState == "NotProvisioned"`: billed and carrying nothing. The one question
  left is whether a provider order is in flight for it.
- `Provisioned`, `gatewayConnections == 0` and `msPeering == false`: nothing in
  these subscriptions uses it. Before calling it idle, check two consumers this query
  cannot see: a Virtual WAN hub (its ExpressRoute connections are not `connections`
  resources) and a gateway connection in a subscription the reader cannot open.
- `msPeering == true` with no gateway connection is normal: Microsoft peering serves
  Microsoft 365 and public services without a VNet gateway.

ExpressRoute Direct port pairs follow their own rule (billed 45 days after creation
or when a link is enabled, whichever comes first) and are out of this query's scope.

## Fix

1. For a `NotProvisioned` circuit, ask the network team whether a provider order is
   open. If none is, delete the circuit (`az network express-route delete --name
   <circuit> --resource-group <rg>`): billing stops. Microsoft's clean-up order
   removes its VNet connections, authorisations, route filters and Global Reach links
   first.
2. For a provisioned circuit nobody uses, ask the provider to deprovision it, then
   delete it in Azure. Ending the carrier contract alone stops the carrier's bill, not
   Microsoft's.
3. For new circuits, request the service key only when the provider is ready to
   provision: the wait is billed.
4. On circuits that stay, check the SKU and billing model: a move from Unlimited back
   to Metered is not possible, and a downgrade to the Local SKU goes through
   PowerShell or the CLI, not the portal.

## Anti-pattern

- Deleting a circuit that serves Microsoft peering because it has no gateway
  connection. Microsoft 365 or public-service routing breaks on-premises.
- Removing the second circuit of a resilience pair because it carries little traffic.
  A standby circuit at another peering location is idle by design; price it as
  insurance, not waste.
- Cancelling the carrier contract and leaving the Azure circuit "for later". The
  provider deprovisions it, the status turns `NotProvisioned`, and Microsoft bills it
  until someone deletes it.

## See also

- `playbooks/azure-idle-vnet-gateway.md` - the ExpressRoute gateway on the Azure side,
  billed by the hour whether the circuit works or not
- `references/finops-azure.md` - "VPN Gateway and ExpressRoute pricing"
- `references/finops-waste-detection-playbooks.md` - "idle" category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
