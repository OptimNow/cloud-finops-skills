---
name: azure-blob-cold-data-in-hot
scope: azure
service: Azure Blob Storage
waste_category: overprovisioned
confidence: possible
---

# Azure Blob Cold Data Sitting in Hot

## Problem

Block blobs written once and rarely read keep paying the Hot capacity rate
when Cool, Cold or Archive would cost a fraction of it. It is the
highest-value blob pattern in a typical estate and the easiest to get
wrong, because a defensible tier-down needs *access* evidence, and Azure
does not record last-access time unless **last access time tracking** is
switched on at the account. Age alone cannot separate "old but read every
month by a report" from "old and cold", and the colder tiers punish the
wrong guess twice: a per-GB retrieval charge on every read, and an
early-deletion charge if the blob is deleted or re-tiered before the tier's
minimum retention (30 days Cool, 90 Cold, 180 Archive). That evidence gap
is structural: a read-only review cannot raise this finding above
`possible` on its own, so the honest first deliverable is often a
prerequisite finding ("enable last-access tracking and Blob Inventory on
the accounts carrying the spend") rather than a savings number.

## Symptoms

- Cost Management or the FOCUS export shows large `Hot` capacity meters on
  accounts whose names or containers say logs, export, backup, archive or
  raw
- Azure Monitor `BlobCapacity` split by the `Tier` dimension is almost all
  Hot, with `Transactions` for `GetBlob` near zero against it
- No lifecycle management policy on the account, or rules scoped to
  prefixes that no longer match the data layout
- Last access time tracking is off, so nobody can say who reads the data
- The account default access tier is Hot and no blob carries an explicit
  tier

## Detection

Two stages. Stage 1 ranks where the Hot spend sits from data every tenant
already has. Stage 2 turns a candidate into a defensible recommendation and
needs two account-level settings most accounts have never enabled.

```kusto
// Stage 1: rank accounts by Hot capacity cost. Resource Graph has no
// billing table, so this runs over the FOCUS / Cost Management export
// wherever it is ingested. Illustrative KQL over an export loaded into a
// Log Analytics custom table named CostExport_CL - the column names
// follow the FOCUS export (ServiceCategory, ResourceId, EffectiveCost,
// ChargeDescription). Adapt to your table.
CostExport_CL
| where ServiceCategory == "Storage"
| where ChargeDescription has "Hot" and ChargeDescription has "Data Stored"
| where ChargePeriodStart >= startofmonth(ago(30d))
| summarize hot_capacity_cost = sum(EffectiveCost) by ResourceId
| top 25 by hot_capacity_cost desc
```

Where the export is not in a queryable store, the Cost Management console
grouped by resource with a meter filter on `Hot` capacity gives the same
ranking. The per-account tier split is also one metric call:

```bash
# Capacity by tier for one account. Read-only. Capacity metrics have a
# one-hour grain but refresh about once a day, so most hourly points are
# empty: look back 48 hours and keep the last non-empty value per tier.
az monitor metrics list --resource "$ACCOUNT_ID/blobServices/default" \
  --metric BlobCapacity --interval PT1H --offset 48h --aggregation Average \
  --filter "Tier eq '*'" -o json \
  | jq -r '.value[0].timeseries[]
           | [.metadatavalues[0].value,
              ([.data[] | select(.average != null) | .average] | last)] | @tsv'
```

Stage 2 prerequisites, both account settings and both a finding in their
own right if absent: **last access time tracking**
(`lastAccessTimeTrackingPolicy.enable`) and a **Blob Inventory** rule that
includes `LastAccessTime`, `Content-Length`, `AccessTier` and `Name`,
written as Parquet. Thirty days after enabling tracking, the inventory
gives the age-versus-size profile per container or prefix. Weight by
**bytes, not blob count**: a prefix where most blobs are old but most bytes
are recent must not be tiered down, and object-count weighting says the
opposite. A Synapse serverless or Databricks query over the inventory
Parquet with `sum(Content-Length)` grouped by container and
`LastAccessTime < now - 90d` is the whole analysis.

The gates that make a tier-down defensible (all three, hence `possible`
until they are met):

- **Access floor**: monthly read-bytes divided by stored-bytes below the
  break-even ratio `(rate_hot - rate_target) / retrieval_rate_target`,
  using the current regional list rates. Retrieval cost is rarely why Cool
  fails; the minimum-retention charge and the higher per-operation read
  prices on small blobs are.
- **Read-operation floor**: colder tiers price read operations several
  times higher than Hot, so a container of many small blobs read by a
  listing-heavy job can cost more in Cool than in Hot. Check operation
  counts, not just bytes.
- **Stability**: the data must have stopped changing for longer than the
  target tier's minimum retention, or the early-deletion charge fires on
  rewrites.

## Fix

1. If tracking or Inventory is missing: ship the prerequisite finding
   (enable both on the top-spend accounts), not a savings estimate.
2. For containers passing all three gates: a lifecycle rule with
   `tierToCool` at 30+ days and `tierToCold` at 90+ days keyed on
   `daysAfterLastAccessTimeGreaterThan`, not on modification time.
   Cold keeps millisecond reads; Archive changes the access model
   (rehydration takes hours and is charged) and needs the owning team's
   sign-off, not just a cost case.
3. For log-shaped containers (small blobs, monotonic growth, never read
   after N days): the lever is **delete**, not tier-down. Set
   `baseBlob.delete` at the retention requirement.
4. Check rule interactions before saving: a delete day earlier than
   `tier day + minimum retention` triggers the early-deletion charge on
   data being deleted anyway.
5. Where a whole account is cold and nothing carries an explicit tier,
   changing the **account default access tier** to Cool moves every
   untiered blob at once. It bills a tier-change charge across the account,
   so run the arithmetic against the saving first.

## Anti-pattern

- Recommending tier-downs from age data alone, at scale, without access
  evidence: a long `possible`-confidence list nobody can action.
- Tiering containers that Synapse, Databricks, Fabric OneLake shortcuts or
  Log Analytics search jobs read into Archive. Queries break or wait hours.
  Cool and Cold are the safe tiers under query engines.
- Tiering to Archive and then deleting or rehydrating inside 180 days; the
  prorated early-deletion charge erases the saving.
- Applying a tier-down rule to an account with versioning on without a
  matching `version` action; the versions stay in Hot.
- Treating premium block blob accounts as candidates. They have no access
  tiers; the lever there is moving the data to a standard account.

## See also

- `playbooks/azure-blob-version-and-soft-delete-sprawl.md` - run the
  pruning rule first; it is realised saving with no access study
- `playbooks/aws-s3-cold-data-in-standard.md` - the AWS twin, same
  two-stage detection and the same three gates
- `playbooks/azure-log-analytics-sprawl.md` - the Log Analytics side of
  retention and archive tiering
- `references/finops-azure.md` - "Storage tiering and lifecycle (beyond
  backup)", the tier decision table and the Bicep rule examples
- `references/finops-waste-detection-playbooks.md` - the taxonomy and the
  realised-versus-potential savings distinction this playbook leans on

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
