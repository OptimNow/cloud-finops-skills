---
name: finops-azure-commitments-sizing
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Forecasting"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Finance"]
fcp_personas_collaborating: ["Engineering", "Procurement", "Leadership"]
fcp_maturity_entry: "Walk"
business_coverage: ["azure:commitments:deep"]
questions:
  - q: "How much should we reserve in Azure, and what does Advisor get wrong?"
    section: "Commitment sizing methodology"
  - q: "Azure cost data is daily. How do we find the hourly floor before buying a savings plan?"
    section: "The cost-plus-utilisation join pattern"
  - q: "Can we trust the reservation and savings plan quantities that Azure Advisor recommends?"
    section: "Calibrating Advisor"
  - q: "Our Azure savings plan utilisation dropped a few months after we bought it. Did we size it on the wrong data?"
    section: "Why daily data hurts Savings Plan sizing more than RI sizing"
  - q: "How much of our Azure compute spend is it safe to commit to a savings plan?"
    section: "Mapping the floor to instruments"
  - "Combien réserver sur Azure, et comment calculer le socle horaire avant d'acheter un Savings Plan ?"
---

# Azure Commitment Sizing

> How much to commit on Azure compute: why daily cost data over-commits savings plans,
> the cost-plus-utilisation join that recovers the hourly floor, how to calibrate
> Advisor's reservation and savings plan recommendations, and how to map the floor to
> instruments. The instruments, the liquidity rules, MACC and phased purchasing are in
> `finops-azure-commitments.md`; database and storage commitments, with their own
> sizing notes, in `finops-azure-commitments-data.md`.

---

## Commitment sizing methodology - granularity, Advisor calibration, tooling

### Data granularity - the AWS-vs-Azure difference that bites in commitment sizing

Azure cost data is **daily**. AWS CUR is **hourly**. This is the structural difference
that changes how you size commitments.

- **Hourly in Azure:** Azure Monitor platform metrics (VM CPU, network, IOPS) -
  utilisation telemetry.
- **Daily in Azure:** Cost Management exports (actual, amortised, FOCUS) and the
  standard Consumption REST endpoints - all billing data.

Consequence: in AWS you read $/hour spend per SKU directly from CUR. In Azure you read
daily spend, but to derive the hourly equivalent you must join cost data with utilisation
data on `ResourceId`.

### Why daily data hurts Savings Plan sizing more than RI sizing

**RI sizing** is mostly OK with daily data. An RI commits to a SKU+region count for a
fixed term ("at least 5 D4s_v5 running 24/7"). Daily data answers count questions
reasonably well - if a SKU+region had at least 5 instances every day for 90 days, you
can size the RI confidently.

**SP sizing** is where daily granularity hurts. A Savings Plan commits to a $/hour
amount. The lowest-risk commitment is roughly the **5th percentile of hourly compute spend** -
the floor below which spend rarely drops. With daily data you cannot see the
hour-by-hour floor; you only see the daily average.

A workload that runs at $100/hour for 8 hours and $30/hour for 16 hours has a daily
average of ~$53/hour but an SP-safe commitment closer to $30.

**Common trap:** **daily-data sizing systematically over-commits Savings Plans on
workloads with within-day cyclicality** - business-hours patterns, batch jobs,
month-end spikes. The over-commitment hides as "low SP utilisation" months later.

### The cost-plus-utilisation join pattern

The workaround that closes the granularity gap:

1. Pull 90 days of daily compute spend from the FOCUS export, grouped by SKU family
   and region.
2. Pull hourly running vCPUs (or running instance count) per VM from Azure Monitor
   over the same period - via `Percentage CPU` joined with VM size, or VM-running-state
   telemetry from `Heartbeat`.
3. Join cost and utilisation on `ResourceId`.
4. From the hourly view, compute the **5th-10th percentile of running vCPUs** across
   the period - the steady-state floor.
5. Multiply by the SKU's hourly $ rate (from a price sheet export, FOCUS `ListUnitPrice`,
   or the Retail Prices API) to get the SP-safe commitment level.

FinOps Hubs and most third-party FinOps platforms do this join for you; without one,
you build it yourself.

```kql
// Cost-plus-utilisation join for Savings Plan sizing
// Assumes: FOCUS export ingested as a custom table (e.g. AzureCost_CL) and
// Azure Monitor InsightsMetrics from the same VMs in the same workspace.
// Adjust column names to match your FOCUS ingestion schema.

let lookback = 90d;
let cost =
    AzureCost_CL
    | where TimeGenerated > ago(lookback)
    | where ServiceCategory_s == "Compute"
    | summarize daily_cost_usd = sum(EffectiveCost_d)
                by ResourceId = tolower(ResourceId_s),
                   day = startofday(TimeGenerated);
let util =
    InsightsMetrics
    | where TimeGenerated > ago(lookback)
    | where Namespace == "Processor" and Name == "UtilizationPercentage"
    | summarize hourly_cpu_pct = avg(Val)
                by ResourceId = tolower(_ResourceId),
                   hour = bin(TimeGenerated, 1h);
cost
| join kind=inner util on ResourceId
| summarize p10_cpu_pct      = percentile(hourly_cpu_pct, 10),
            avg_daily_cost   = avg(daily_cost_usd)
            by ResourceId
| extend implied_hourly_floor_usd = (avg_daily_cost / 24.0) * (p10_cpu_pct / 100.0)
| order by implied_hourly_floor_usd desc
```

The query is illustrative: map the column names and the `_ResourceId` normalisation to
the customer's ingestion.

### Calibrating Advisor's reservation and Savings Plan recommendations

Advisor's commitment recommendations are **a sanity check, not a source of truth**:
useful to surface opportunities across hundreds of subscriptions, weak on:

- **Backward-looking by design.** Analyses 7, 30, or 60 days of past usage (default 60
  days). Does not know about a planned decommission, migration, or architecture change.
  If the customer is about to retire a workload, Advisor will recommend committing to it.
- **Does not account for Azure Hybrid Benefit.** Quoted savings are gross of AHB. For
  Windows workloads with AHB applied, the real saving from a recommended RI is
  meaningfully smaller than Advisor states.
- **Does not compare RI vs SP side by side.** RI recommendations and SP recommendations
  live on separate Advisor pages. The actual decision question - "for this workload,
  do I commit via RI or SP?" - Advisor cannot answer for you.
- **Defaults to Shared scope and 1-year term.** Both are usually right, but for
  multi-Billing-Profile MCAs the Shared scope is bounded by the Billing Profile that
  owns the recommendation, not the whole company. Advisor does not warn about this
  scope boundary.
- **Recommendation scope has caught up with purchase scope (29 September 2026).**
  Savings plan and reservation recommendations, including P3 reservations, are now
  produced at **management group** scope in the portal and the REST endpoints,
  aggregating every subscription under the group. Do not sum per-subscription
  recommendations by hand any more: each targeted its own 80-90%, so the sum
  over-commits. The other calibration points still apply. Source:
  https://techcommunity.microsoft.com/blog/finopsblog/now-available-management-group%E2%80%93scoped-savings-plan-and-reservation-recommendatio/4560869
  (Microsoft FinOps blog, 29 September 2026).
- **Conservative coverage targeting.** Recommendations target ~80-90% of observed usage.
  If the customer wants lower coverage for liquidity reasons (more PAYG buffer for
  workload changes), Advisor does not propose that profile.

**Operating pattern:** take Advisor's output as one input, validate against your own
calculation from the cost-plus-utilisation join, reconcile differences. Differences are
diagnostic - they usually reveal AHB not factored, scope mismatches, or workload context
Advisor cannot know.

**Agentic access.** Reservation and savings plan insights surfaced through the Azure
Resource Manager MCP server (preview, August 2026) carry the same caveats; see "Agentic
FinOps on Azure" in `finops-azure-billing.md`.

Source: https://learn.microsoft.com/en-us/azure/advisor/advisor-reference-cost-recommendations

**Which products Advisor covers, and how to pull the feed.** Advisor emits reservation
recommendations for VMs, App Service, Dedicated Host, Azure VMware Solution, Azure Data
Explorer, Data Factory, Azure Files, managed disks, Blob storage (Blob v2 and ADLS
Gen2), Cosmos DB, Database for MySQL, Database for PostgreSQL, SQL PaaS databases,
Synapse (SQL DW), NetApp Files, Azure Cache for Redis, Red Hat and SUSE, Azure OpenAI
provisioned throughput and Microsoft Fabric, plus the compute and database savings
plans (Advisor cost recommendations reference, read 15 October 2026). Each
recommendation carries a term (P1Y or P3Y), a look-back period (7, 30 or 60 days), a
quantity and an annual saving quoted list against list per subscription. The REST
feed:

```
GET {scope}/providers/Microsoft.Consumption/reservationRecommendations?api-version=2026-06-01
    &$filter=properties/scope eq 'Shared' AND properties/resourceType eq '<type>'
             AND properties/lookBackPeriod eq 'Last60Days'
```

Scope is a subscription, resource group, billing account, billing profile or, through
the filter, a management group. Allowed `resourceType` values: VirtualMachines,
SQLDatabases, PostgreSQL, ManagedDisk, MySQL, RedHat, MariaDB, RedisCache, CosmosDB,
SqlDataWarehouse, SUSELinux, AppService, BlockBlob, AzureDataExplorer,
VMwareCloudSimple. Azure Files and Fabric are not in the API filter list: read those
from the portal purchase blade (Reservations > Add > product > Recommended tab). Two
more calibration points: every recommendation is gross of any MACC or EA discount (see
"Net discount under a MACC with an Azure Commitment Discount" in
`finops-azure-commitments.md`), and a product's
recommendation appears only when the estimated saving clears Advisor's internal
threshold, so a missing 1-year blob recommendation next to a 3-year one says something
about the shallow 1-year discount, not about the data. Source:
https://learn.microsoft.com/en-us/rest/api/consumption/reservation-recommendations/list
(read 15 October 2026).

### Mapping the floor to instruments

Once the always-on floor per SKU family and region is known (the join above), map it:

- High baseline + low variability + AHB-eligible Windows -> 3-year RI with AHB
- High baseline + low variability + Linux or non-AHB -> 1-year RI, or 3-year if
  conviction is high (affected v1 to v3 series take neither: "Compute commitment
  instruments", point 6, in `finops-azure-commitments.md`)
- Variable workload, stable $ floor -> 1-year Savings Plan sized below the floor (70-80%
  of it is a working estimate, not a published benchmark)
- Bursty / unpredictable -> PAYG with Spot for the spike layer
- Older VM series approaching retirement -> migrate to a newer generation, or cover
  it with a Savings Plan if the workload must stay on the legacy series

Then validate against Advisor (above), buy in phased blocks ("Phased purchasing"
in `finops-azure-commitments.md`), and re-evaluate quarterly against actuals.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
