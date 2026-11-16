---
name: azure-idle-vnet-gateway
scope: azure
service: Azure VPN Gateway / ExpressRoute gateway
waste_category: idle
confidence: likely
questions:
  - "Do we pay for an Azure VPN gateway that has no connection?"
  - "How do we find virtual network gateways nobody uses any more?"
  - "Our site-to-site VPN moved to ExpressRoute. What is left to delete?"
  - "Can a VPN gateway with no connections still be in use?"
  - "Une passerelle VPN Azure n'a plus de connexion : est-elle encore facturée ?"
---

# Idle Azure Virtual Network Gateway

## Problem

A virtual network gateway, of VPN or ExpressRoute type, bills an hourly rate set by
its SKU for as long as it exists, plus egress, whether or not a tunnel or circuit
uses it. Its public IP bills on top. Gateways outlive the reason they were built: a
site-to-site VPN replaced by ExpressRoute, a hub moved to Virtual WAN, a proof of
concept VNet nobody removed. Two signals are needed, because a gateway with no
connection resource can still serve remote users over point-to-site
([About VPN Gateway](https://learn.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-about-vpngateways),
[Networking best practices](https://learn.microsoft.com/en-us/cloud-computing/finops/best-practices/networking),
read 16 November 2026).

## Symptoms

- A VPN or ExpressRoute gateway line on the bill for a VNet whose workloads moved
- Gateways whose "Connections" blade is empty in the portal
- An ExpressRoute gateway whose circuit is gone or `NotProvisioned`
- A hub VNet gateway left after the move to a Virtual WAN hub

## Detection

First signal, from inventory: connections that reference the gateway, on either side
(a VNet-to-VNet connection names the second gateway as `virtualNetworkGateway2`), and
whether point-to-site is configured:

```kusto
// Azure Resource Graph - virtual network gateways, the connections that use them,
// and whether a point-to-site address pool is configured
resources
| where type =~ "microsoft.network/virtualnetworkgateways"
| extend gatewayId   = tolower(id)
| extend gatewayType = tostring(properties.gatewayType)
| extend skuName     = tostring(properties.sku.name)
| extend hasP2S      = array_length(properties.vpnClientConfiguration.vpnClientAddressPool.addressPrefixes) > 0
| join kind=leftouter (
    resources
    | where type =~ "microsoft.network/connections"
    | project gatewayId = tolower(tostring(properties.virtualNetworkGateway1.id))
    | union (
        resources
        | where type =~ "microsoft.network/connections"
        | project gatewayId = tolower(tostring(properties.virtualNetworkGateway2.id)))
    | where isnotempty(gatewayId)
    | summarize connections = count() by gatewayId
  ) on gatewayId
| extend connections = coalesce(connections, 0), hasP2S = coalesce(hasP2S, false)
| project subscriptionId, resourceGroup, name, gatewayType, skuName, connections, hasP2S, location
| order by connections asc, hasP2S asc
```

`connections == 0` and `hasP2S == false` is a gateway nothing in these subscriptions
uses. A connection in a subscription the reader cannot open is invisible here, so run
it with Reader on the whole tenant.

Second signal, from platform metrics, which Azure collects without any diagnostic
setting. For a VPN gateway that has connections or a point-to-site pool, 30 days of
zero tunnel bandwidth and zero point-to-site sessions confirm it is idle:

```bash
# Azure Monitor - 30 days of tunnel bandwidth and point-to-site sessions (read only)
GATEWAY_ID="/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworkGateways/<gateway>"
az monitor metrics list --resource "$GATEWAY_ID" \
  --metric TunnelAverageBandwidth P2SConnectionCount \
  --interval P1D --offset 30d --aggregation Maximum -o table
```

Metric names are from the
[VPN Gateway monitoring reference](https://learn.microsoft.com/en-us/azure/vpn-gateway/monitor-vpn-gateway-reference).
For an ExpressRoute gateway, the state of its circuit is the second signal: see
`playbooks/azure-expressroute-circuit-not-provisioned.md`. Virtual WAN gateways are
other resource types (`vpngateways`, `p2svpngateways`, `expressroutegateways`) and are
not covered by these queries.

## Fix

1. Confirm with the network owner. A disaster-recovery gateway that waits for a
   failover is idle by design: keep it and price it as insurance.
2. Delete the remaining connections, then the gateway (`az network vnet-gateway
   delete --name <gateway> --resource-group <rg>`).
3. Delete the gateway's public IP, or keep it deliberately if the gateway may come
   back and on-premises devices point at that address
   (`playbooks/azure-orphaned-public-ips-and-nics.md`).
4. For a gateway that is used but lightly, check whether a smaller SKU of the same
   generation carries the measured tunnel bandwidth.

## Anti-pattern

- Deleting a gateway with no connection resource while it serves point-to-site users.
  Remote access stops for everyone at once; the `hasP2S` column and the
  `P2SConnectionCount` metric exist to prevent it.
- Taking an empty Connections blade at face value when the gateway is the second side
  of a VNet-to-VNet connection: that connection is listed on the other gateway.
- Deleting a gateway and its public IP when it may be rebuilt. A new public IP means
  every on-premises device and partner firewall needs reconfiguring.

## See also

- `playbooks/azure-expressroute-circuit-not-provisioned.md` - the circuit behind an
  ExpressRoute gateway
- `playbooks/azure-ddos-plan-unassociated.md` - another fixed-fee network resource
  that outlives its project
- `references/finops-azure.md` - "VPN Gateway and ExpressRoute pricing"
- `references/finops-waste-detection-playbooks.md` - "idle" category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
