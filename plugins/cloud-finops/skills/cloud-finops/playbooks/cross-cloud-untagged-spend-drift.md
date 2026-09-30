---
name: cross-cloud-untagged-spend-drift
scope: cross-cloud
service: All cost-bearing resources
waste_category: orphaned
confidence: likely
---

# Untagged Spend Drift

## Problem

Untagged or partially-tagged resources cannot be allocated to a team,
product, or cost-centre. They appear in the bill as a single
unattributable bucket - and that bucket grows month over month if no
intake gate stops new resources from landing without tags. Once
unallocated spend crosses ~10% of the bill, allocation reports become
unreliable, showback loses credibility with engineering teams, and
chargeback becomes politically impossible. This is not a "waste"
pattern in the per-resource sense - it is a **governance failure**
that destroys the financial visibility downstream.

## Symptoms

- The "Unallocated" or "Other" bucket in showback reports is > 10% of
  total spend
- Tag compliance scan shows < 80% of resources have all mandatory tags
  populated
- Unallocated bucket grows month-over-month at a rate similar to or
  faster than total spend growth
- Engineering teams routinely dispute their showback numbers because
  "the unallocated bucket should be charged to someone else"
- New resource provisioning happens via console / CLI rather than
  IaC + policy enforcement

## Detection

**AWS** - find resources with missing mandatory tags:

```sql
-- Athena over CUR 2.0: spend with missing 'cost-centre' tag, last 30 days
SELECT
  product_servicecode             AS service,
  line_item_resource_id           AS resource_id,
  SUM(line_item_unblended_cost)   AS cost_30d
FROM cur2
WHERE line_item_usage_start_date >= current_date - interval '30' day
  AND (resource_tags_user_cost_centre IS NULL
       OR resource_tags_user_cost_centre = '')
  AND line_item_unblended_cost > 0
GROUP BY 1, 2
ORDER BY cost_30d DESC
LIMIT 100;
```

**Azure** - tag compliance via Resource Graph:

```kusto
resources
| where type !startswith "microsoft.resources/"
| extend hasOwner    = isnotempty(tostring(tags.owner))
| extend hasCostCtr  = isnotempty(tostring(tags["cost-centre"]))
| extend hasEnv      = isnotempty(tostring(tags.environment))
| summarize
    total = count(),
    untagged_owner    = countif(not(hasOwner)),
    untagged_costctr  = countif(not(hasCostCtr)),
    untagged_env      = countif(not(hasEnv))
  by subscriptionId, type
| where untagged_costctr > 0
| order by untagged_costctr desc
```

**GCP** - resources with missing labels:

```sql
SELECT
  service.description     AS service,
  resource.name           AS resource,
  SUM(cost)               AS cost_30d
FROM `<project>.<dataset>.gcp_billing_export_v1_<account>`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND ARRAY_LENGTH(labels) = 0
  AND cost > 0
GROUP BY 1, 2
ORDER BY cost_30d DESC
LIMIT 100;
```

## Fix

1. **Define the mandatory tag set first** (typically: `owner`,
   `cost-centre`, `environment`, `product`, `data-classification`).
   Document in a tagging policy. See `references/finops-tagging.md`.
2. **Backfill the existing estate** - run the detection queries above,
   assign owners to every untagged resource via team workshops. Set a
   30 / 60 / 90 day deadline for tag compliance.
3. **Enforce at the intake gate**:
   - **AWS**: Service Control Policies (SCPs) that deny resource
     creation without mandatory tags; AWS Config rules to flag
     non-compliant resources.
   - **Azure**: Azure Policy with `[deny]` effect on missing tags;
     `[modify]` effect to inherit from resource group.
   - **GCP**: Organisation Policy + label inheritance from project
     metadata.
4. **Make untagged spend visible weekly** - publish a "tag debt"
   leaderboard by team. Social pressure works.
5. **Tie the tagging mandate to the onboarding gate**: a new workload
   does not enter the cloud estate until it passes the tag check. See
   `references/finops-onboarding-workloads.md`.

## Anti-pattern

- Backfilling tags via mass-update scripts that overwrite legitimate
  team-specific tags. Scripts should only ADD missing mandatory tags,
  never overwrite existing values.
- Implementing tag enforcement before defining the policy. Engineering
  teams that get blocked at provisioning without knowing what to put
  in the tag values lose trust in the FinOps function.
- Treating "Unallocated" as a cost-allocation bucket to charge a
  default team. That team will dispute it forever - the right answer is
  to fix the tags at source, not absorb the unallocated.

## See also

- `references/finops-tagging.md` - tag taxonomy, enforcement patterns,
  IaC conventions
- `references/finops-allocation-showback.md` - allocation methodology,
  unallocated > 10% as a tagging signal
- `references/finops-onboarding-workloads.md` - intake gate patterns
- `references/finops-waste-detection-playbooks.md` - "orphaned" category
  rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
