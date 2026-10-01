---
name: gcp-cud-mismatch
scope: gcp
service: GCP Committed Use Discounts
waste_category: commitment-mismatch
confidence: likely
---

# GCP Resource-Based CUD Mismatch

## Problem

A resource-based Committed Use Discount commits to specific vCPU and
memory in a specific region for 1 or 3 years, and GCP bills the
commitment whether matching resources run or not. When the estate drifts
away from the committed shape - a machine-series migration (N2 to C4, x86
to Arm), a region consolidation, or a workload move to GKE Autopilot or
serverless - the CUD keeps billing while the discount it was bought for
stops landing. This is the most common GCP commitment failure: the deep
discount of a resource-based CUD is exactly what makes it brittle, because
resource-based CUDs cannot be exchanged or cancelled mid-term. The paired
sizing trap: CUD savings modelled against headline on-demand rates
overstate the benefit, because Sustained Use Discounts already reduce the
effective rate the CUD competes against.

## Symptoms

- Billing export shows commitment charges with shrinking or zero matching
  CUD credit lines
- A machine-series or region migration shipped since the CUD was bought
- Committed vCPU/memory in a region exceeds what the project family
  actually runs there
- CUD analysis report (Billing console) shows utilisation trending down
  over consecutive weeks

## Detection

```sql
-- BigQuery over the standard billing export. Prerequisite: detailed
-- billing export enabled into `billing_dataset.gcp_billing_export_v1_*`.
-- Compares commitment fees against the CUD credits they generate, per
-- region, last 30 days. Credits appear as separate line items on usage
-- rows (credits.type = 'COMMITTED_USAGE_DISCOUNT'), not as discounts on
-- the commitment fee line itself.
WITH fees AS (
  SELECT location.region AS region,
         SUM(cost) AS commitment_fee
  FROM `billing_dataset.gcp_billing_export_v1_XXXXXX`
  WHERE sku.description LIKE 'Commitment%'
    AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  GROUP BY 1
),
credits AS (
  SELECT location.region AS region,
         SUM(c.amount) AS cud_credit   -- credits are negative amounts
  FROM `billing_dataset.gcp_billing_export_v1_XXXXXX`, UNNEST(credits) AS c
  WHERE c.type = 'COMMITTED_USAGE_DISCOUNT'
    AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  GROUP BY 1
)
SELECT f.region,
       ROUND(f.commitment_fee, 2)            AS commitment_fee_30d,
       ROUND(ABS(COALESCE(c.cud_credit, 0)), 2) AS cud_credit_30d,
       ROUND(ABS(COALESCE(c.cud_credit, 0)) / NULLIF(f.commitment_fee, 0), 2) AS credit_to_fee_ratio
FROM fees f
LEFT JOIN credits c USING (region)
ORDER BY credit_to_fee_ratio ASC;
-- COALESCE matters: a region whose committed shape no longer runs at all
-- produces commitment fees with NO credit lines, and a bare join would
-- drop exactly the worst mismatches.
```

A `credit_to_fee_ratio` well below 1.0 sustained over the window signals a
mismatch. Classification is `likely`, not `obvious`: two signals are
needed - the sustained ratio gap AND confirmation that no in-flight
migration or seasonal trough explains it - because a CUD mid-workload-move
can look mismatched for a few weeks and self-heal. The console equivalent
is Billing > Reports > **CUD analysis**.

## Fix

1. Confirm the second signal: check with the owning team whether a
   migration back onto the committed shape is in flight. If yes, date it
   and re-check after; if no, proceed.
2. Resource-based CUDs cannot be exchanged or cancelled - the levers are
   forward-looking. Stop the bleeding at the renewal boundary: mark the
   commitment do-not-renew in the register and decide the replacement
   shape now, not on expiry day.
3. Where residual matching capacity exists, steer schedulable workloads
   (batch, CI, dev) onto the committed series/region so the remaining
   term's credits land - a workload-placement fix, legitimate when the
   workload is genuinely shape-agnostic.
4. Re-buy flexibility-first: for estates still migrating, spend-based
   (Flex) CUDs trade discount depth for series/region freedom, and are
   usually the right instrument until the target architecture is stable.
   Size any replacement against the SUD-effective rate, not headline
   on-demand.

## Anti-pattern

- Buying 3-year resource-based CUDs during an active modernisation
  programme. The migration that saves 20% on compute can strand a 57%
  discount instrument worth more than the saving.
- Forcing workloads back onto old machine series *solely* to consume CUD
  credits when the migration was performance- or cost-justified -
  metric-fixing (distinct from step 3, which moves only shape-agnostic
  work).
- Modelling CUD savings against list on-demand rates. SUDs are automatic;
  the honest baseline is the SUD-effective rate.

## See also

- `references/finops-gcp.md` - CUD types (resource-based vs Flex), SUD
  interaction, billing export and credit line-item mechanics
- `playbooks/aws-expiring-commitment-no-decision.md` - the AWS member of
  the commitment-mismatch family
- `playbooks/azure-unused-reservation.md` - the Azure member of the family
- `references/finops-waste-detection-playbooks.md` - the eight-category
  taxonomy this pattern fits ("commitment-mismatch")

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
