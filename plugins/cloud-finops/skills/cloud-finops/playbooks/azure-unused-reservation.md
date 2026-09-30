---
name: azure-unused-reservation
scope: azure
service: Azure Reservations
waste_category: commitment-mismatch
confidence: obvious
---

# Unused Azure Reservation

## Problem

An Azure reservation bills its full committed amount every hour whether or
not any resource consumes the benefit. A reservation showing 0% (or
near-zero) utilisation is paying list-committed money for nothing - most
often because the covered resource was deleted or resized, the reservation
scope no longer matches where the workload runs (wrong subscription or
resource group scope), or an instance-size-flexibility group stopped
matching after a SKU migration. Unlike a lapsed discount, this is spend
with literally no offsetting benefit, which is why a sustained 0% reading
is single-signal actionable.

## Symptoms

- Reservation utilisation shows 0% or single digits for 30+ consecutive
  days in the Reservations blade
- A VM family migration (e.g. Dv3 to Dv5, Intel to Ampere), region move,
  or AKS node pool change happened recently and nobody touched the
  reservation
- Reservation scope is set to a single subscription or resource group that
  has since been emptied or decommissioned
- Amortised cost reports show reservation charges with no matching
  `Reservation applied` usage lines

## Detection

Portal path (no setup needed): **Cost Management + Billing > Reservations**
- the list view shows a utilisation (%) column per reservation; sort
ascending. Requires Reservation Reader (or higher) on the reservation
order.

```bash
# CLI inventory of reservations with scope and state. Requires the
# `az account` extension access to reservation orders (Reservation
# Reader). Utilisation percentages come from Cost Management, not ARM,
# so pull them via the portal view above or the REST call below.
az reservations reservation-order list --output table

# Utilisation via REST (last 30 days, daily grain) - substitute the
# reservation order id. Prerequisite: Reservation Reader on the order.
az rest --method get \
  --url "https://management.azure.com/providers/Microsoft.Capacity/reservationorders/{orderId}/providers/Microsoft.Consumption/reservationSummaries?grain=daily&\$filter=properties/usageDate ge $(date -u -d '-30 days' +%Y-%m-%d) AND properties/usageDate le $(date -u +%Y-%m-%d)&api-version=2023-05-01" \
  --query "value[].{date:properties.usageDate,utilised:properties.avgUtilizationPercentage}"
```

An empty result from the REST call means no utilisation *records*, not
proven waste - check the portal view to distinguish "0% utilised" from
"no data for this order". Classification is `obvious` at sustained ~0%:
one signal, action always warranted. Partial underutilisation (say 40-70%)
is a different, weaker finding - it needs a second signal (no pending
migration, no seasonal trough) before acting, and sizing guidance for it
lives in `references/finops-azure-commitments.md`.

## Fix

Ordered safest-first; note the calendar, because the liquidity toolkit
shrinks on 1 February 2027 (reservation exchange retires for services a
savings plan also covers - see the commitments reference for the full
rules).

1. Check scope first: flipping a reservation from a dead subscription
   scope to **shared scope** is free, instant, reversible, and fixes the
   most common cause outright.
2. If the covered SKU is gone: while exchange remains available for the
   service, exchange into the family and region the estate actually runs.
   Reservations bought before 1 February 2027 keep one final exchange
   after that date - spend it deliberately, batched, not on a minor tweak.
3. If neither scope nor exchange can restore utilisation: refund
   (cancellation) within Microsoft's refund terms - plan against the
   documented cap and fee clause rather than assuming a free exit - or
   trade in against a compute savings plan where eligible.
4. Feed the root cause back into purchase practice: buy shared-scope by
   default unless there is a governance reason not to, and put reservation
   utilisation on the same monthly review as the commitment register.

## Anti-pattern

- Fixing utilisation by moving workloads back onto the reserved SKU purely
  to make the reservation look used - optimising the metric instead of the
  estate. If the migration away was right, fix the reservation, not the
  workload.
- Waiting for annual review to look at utilisation. A 0% reservation found
  eleven months late has already burnt eleven months of commitment.
- Assuming exchange will always be available. For savings-plan-covered
  services that door closes on 1 February 2027; post-purchase flexibility
  planning that relies on exchange is building on retired mechanics.

## See also

- `references/finops-azure-commitments.md` - reservation vs savings plan
  decision trees, portfolio liquidity, the 1 February 2027 exchange
  retirement rules
- `playbooks/aws-expiring-commitment-no-decision.md` - the AWS member of
  the commitment-mismatch family
- `playbooks/gcp-cud-mismatch.md` - the GCP member of the family
- `references/finops-waste-detection-playbooks.md` - the eight-category
  taxonomy this pattern fits ("commitment-mismatch")

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
