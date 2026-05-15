---
name: finops-fabric
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Usage Optimization"]
fcp_phases: ["Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Product", "Finance"]
fcp_maturity_entry: "Walk"
---

# FinOps on Microsoft Fabric

> Microsoft Fabric capacity FinOps: F-SKU model, Capacity Units (CU) and the 24-hour
> smoothing window, pause / resume, Reserved Capacity, the Power BI Pro to Fabric
> migration governance trap, allocation models for shared capacity, and monitoring
> via the Fabric Capacity Metrics app.

---

## What Fabric is, in FinOps terms

Microsoft Fabric is the unified analytics platform Microsoft positions as the
successor to Power BI Premium and as a peer to Databricks / Snowflake for
non-engineer-led analytics. It bundles Power BI, Data Factory, Synapse-style data
engineering, real-time analytics, and Copilot under one **capacity-based** licence,
billed in **Capacity Units (CU)** delivered through **F-SKUs**.

The FinOps consequence: spend moves from per-user Power BI Pro / PPU licences to
shared compute capacity. The economic unit changes - and so does the governance
problem.

For the shared-data-platform allocation framing (cost object reported by the
platform vs business object Finance wants to allocate against), see the "data-
platform FinOps problem" callout in `finops-databricks.md`. The mechanics differ
between Databricks and Fabric; the allocation problem is the same.

---

## The capacity model - F-SKUs, Capacity Units, and the 24-hour smoothing window

### F-SKU range and the CU mapping

Fabric capacity is sold as F-SKUs in 11 sizes:

```
F2 / F4 / F8 / F16 / F32 / F64 / F128 / F256 / F512 / F1024 / F2048
```

The number after `F` is the **Capacity Unit (CU)** count. F2 = 2 CU, F64 = 64 CU,
F2048 = 2048 CU. CUs are the unit of compute throughput Fabric measures and bills
against.

**Verify current pricing against the Microsoft Fabric pricing page** -
https://azure.microsoft.com/en-us/pricing/details/microsoft-fabric/ - before
quoting dollar amounts. Fabric pricing has shipped multiple changes since GA;
hard-coded numbers age out fast.

### CU smoothing - the most counterintuitive Fabric mechanic

Fabric **smooths CU usage over a 24-hour rolling window** before applying
throttling decisions. Short spikes are absorbed by the smoothing; sustained
over-consumption triggers throttling. This is the single most counterintuitive
behaviour in Fabric capacity sizing and customers regularly mis-size F-SKUs
because they reason about peak instead of smoothed load.

**Practical implication:** a 5-minute spike at 200% of capacity does not throttle
anything if the rest of the 24-hour window runs below capacity. Capacity sizing
should target the **smoothed** P95-P99 load, not raw peak load. This is closer
to AWS's Lambda burst-capacity behaviour than to per-second autoscaling.

**Throttling behaviour when smoothed CU usage exceeds capacity:**
- **Interactive operations** (Power BI queries, Direct Lake reads, ad-hoc Spark
  notebooks) are delayed - users see slower response, not failures.
- **Background operations** (scheduled refreshes, pipelines, data warehouse
  loads) are queued and may eventually be rejected if the queue depth exceeds
  service limits.

Source: https://learn.microsoft.com/en-us/fabric/enterprise/throttling

### Autoscale - limited, not general-purpose

Fabric does not have a general-purpose autoscale across all workload types.
**Fabric Autoscale Billing for Spark** exists for Spark-specific overage - Spark
jobs that would otherwise throttle can be billed as autoscale CU consumption above
the F-SKU's base capacity. This is opt-in per workspace and bills separately on
the Azure invoice. Outside Spark, the capacity ceiling is the F-SKU; over-runs
throttle, they do not auto-scale.

Source: https://learn.microsoft.com/en-us/fabric/data-engineering/autoscale-billing-for-spark-overview

---

## Pause / Resume - the most underused cost lever

Fabric capacities support **manual pause and resume**. While paused, **compute
charges stop**; storage and metadata continue to accrue. Resume takes a few
minutes. This is functionally equivalent to Azure SQL Serverless auto-pause but
**not automatic** - you have to schedule it.

**Use cases:**
- Non-production / dev / departmental capacities only needed during business
  hours.
- Capacity used for monthly or quarterly reporting workloads with long idle
  windows between cycles.

**Saving math:** an F-SKU running 168 hours/week (24x7) vs 50 hours/week
(business hours) is a ~70% saving on capacity compute, with no functional change
beyond accepting the resume delay at the start of each working day.

**Implementation:**
- Fabric REST API: `POST /capacities/{capacityId}/suspend` and `/resume`. Source:
  https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities
- Azure Logic Apps or Function on a schedule, calling the REST endpoints with a
  service principal that has Fabric admin rights.
- Avoid: manual portal-driven pause / resume - it does not survive operator
  attrition.

**Common trap.** Pause / resume is **incompatible with capacities currently
serving Power BI Premium workloads with active datasets** - active datasets
prevent suspend. Plan a workspace migration off the capacity (or schedule the
pause for windows where datasets are not in use) before scheduling pause cycles.
Customers regularly hit this on day 1 of a pause-schedule rollout because they
did not audit the active-dataset list first.

---

## Fabric Reserved Capacity

- 1-year commitment, applied at the F-SKU level (e.g. one reservation per F64).
- **Saving: roughly 40-50% vs PAYG capacity** - verify current rate against the
  Microsoft Fabric reserved capacity page before quoting.
- Scope and exchange rules: similar to Azure VM Reservations but capacity-
  specific. Exchanges allowed within the F-SKU family with the standard Azure
  reservation mechanics (see `finops-azure.md` for exchange / refund / cap
  details, which apply identically here).
- **No 3-year option as of April 2026.** Fabric Reserved Capacity is 1-year only.
- **Sequencing:** only commit after cleanup and capacity sizing have stabilised.
  Reserving before cleanup locks the wrong F-SKU into a 1-year contract - the
  same mistake as committing to over-provisioned Databricks compute, with the
  same recovery cost.

Source: https://azure.microsoft.com/en-us/pricing/details/microsoft-fabric/

---

## The Power BI Pro to Fabric capacity migration - the governance failure pattern

The single most common Fabric FinOps failure pattern is the **post-migration
governance gap** in customers transitioning from per-user Power BI Pro licensing
to shared Fabric capacities. Document this as a specific repeatable engagement
scenario.

When an organisation moves from Pro / PPU to Fabric:

- The economic unit changes from **per-user licence** to **shared capacity
  consumption**.
- User behaviour does not adjust automatically. Users keep creating workspaces
  and treating them as effectively free, because under Pro they were - the
  marginal cost of a new workspace was zero.
- Costs spike weeks after migration because the operating model lagged the
  licensing model.

**Specific failures to watch for:**
- Users do not understand that workspace activity consumes shared capacity. A
  poorly-written Direct Query can consume meaningful CU on every page render.
- Workspace creation is not controlled - anyone can create one with default
  governance.
- Idle workspaces accumulate; nothing flags them because no per-user licence is
  expiring.
- Capacity sizing is not reviewed early enough. The F-SKU bought at migration is
  often wrong by month 2 - either over-sized (waste) or under-sized (throttling
  events the business owner blames on platform engineering).
- Business demand grows faster than cost governance maturity.

**Day 1 question on any post-migration engagement:** "When did you migrate from
Pro / PPU to Fabric, and what governance did you put in place at the same time?"
If the answer to "what governance" is vague, governance is the engagement -
capacity sizing and reservations are downstream.

---

## Capacity governance controls

| Control area | Practical control |
|---|---|
| Workspace creation | Approval workflow or Azure-Policy-based creation control; do not leave open to all users post-migration |
| Workspace ownership | Mandatory owner, cost centre, business purpose tags at creation |
| Idle cleanup | Recurring (monthly) review of inactive workspaces - delete or archive |
| Capacity sizing | Utilisation review and right-sizing every quarter for the first year, then annually |
| Reservation decision | Only after usage baseline is stable for 60-90 days post-cleanup |
| Monitoring | Capacity utilisation, spikes, throttling events, trend - all surfaced via the Fabric Capacity Metrics app |
| Escalation | Finance + platform owner + workspace owner in the same review cadence; do not silo by function |

---

## Allocation models for shared capacity

When several workspaces share a Fabric capacity, who pays? There is no canonical
right answer; the allocation model has to match the customer's maturity and
political reality.

| Model | When it works | Weakness |
|---|---|---|
| Equal split by workspace | Early-stage, low maturity, "we just need to start somewhere" | Unfair if usage differs materially - high consumers pay the same as light ones |
| Split by department / business-unit ownership | Broad showback, easy to administer | Weak for shared analytics teams that serve multiple BUs |
| Split by capacity consumption (CU-weighted) | Better accuracy, defensible | Requires reliable capacity-metrics telemetry; harder to explain to non-technical stakeholders |
| Centrally funded platform | Strategic platform-adoption phase, executive-sponsored | Weak accountability; users have no incentive to optimise |
| Hybrid (central platform + heavy-user chargeback) | Most realistic for mid-maturity orgs | More complex to explain and reconcile |

**Pragmatic adoption sequence:**

1. Start with workspace-ownership allocation.
2. Use capacity-utilisation metrics from the Fabric Capacity Metrics app to
   identify heavy consumers.
3. Apply exceptions for large workloads (e.g. data engineering pipelines that
   dominate CU).
4. Move to usage-weighted allocation once the capacity-metrics telemetry is
   trusted.

Going to usage-weighted before the telemetry is trusted produces arguments rather
than action. Trust the data first, then bill on it.

---

## Pricing comparison - Pro vs PPU vs Fabric F-SKU

Fabric capacities replace per-user Power BI Pro and PPU licensing at scale. The
breakeven is headcount-dependent.

- **Power BI Pro** - per-user, monthly. Suits low-headcount tenancies, read-only
  consumers, or organisations where a small fraction of users need analytics.
- **Power BI Premium per User (PPU)** - per-user, monthly, gives Premium feature
  set without shared capacity. Useful for power users who need Premium-only
  features (paginated reports, larger model sizes) but are too few to justify a
  capacity.
- **Fabric F-SKU** - capacity-based. Replaces both Pro and PPU at scale and adds
  data engineering / Spark / data-warehouse workloads to the same capacity.

**Rough breakeven:** above ~100-200 users with active Premium feature use, an
F-SKU starts to compete economically. Below that threshold, Pro or PPU is
usually cheaper. The exact crossover depends on F-SKU size selected, workspace
mix, and whether Spark / pipeline workloads are running on the capacity.

Provide a decision-tree-style guide to the customer rather than a single-number
breakeven - the answer depends on feature mix, not just headcount.

Source: https://azure.microsoft.com/en-us/pricing/details/power-bi/

---

## Monitoring - where to look

### Microsoft Fabric Capacity Metrics app

Built into the Fabric admin portal. The primary tool for FinOps and platform
engineering. The metrics that matter:

- **CU usage smoothed** - the 24-hour-smoothed view, which is what throttling
  decisions are based on. Use this for sizing, not the raw spike view.
- **Throttling events** - count and duration. Persistent throttling is the signal
  to upsize the F-SKU or migrate workloads.
- **Top items by CU consumption** - typically Power BI datasets, dataflows, or
  Spark notebooks. Surface the top 10 each week as a starting point for
  optimisation.
- **Background vs interactive split** - background operations (refreshes,
  pipelines) often dominate CU but are easier to schedule off-peak; interactive
  operations are user-perceived and cannot be scheduled.

Source: https://learn.microsoft.com/en-us/fabric/enterprise/metrics-app

### Azure Monitor / Log Analytics integration

Fabric capacity metrics can be sent to Log Analytics via diagnostic settings -
the right path for customers who already have a centralised observability and
cost-data pipeline. Once in Log Analytics, KQL is the query layer.

```kql
// Top 10 Fabric workspaces by CU consumption over the last 30 days
// Requires diagnostic settings exporting Fabric capacity metrics to Log Analytics.
// Adjust table name to match your diagnostic-setting target.
FabricCapacityMetrics_CL
| where TimeGenerated > ago(30d)
| where MetricName_s == "CU_Consumed"
| summarize total_cu = sum(MetricValue_d)
            by WorkspaceId_g, WorkspaceName_s
| order by total_cu desc
| take 10
```

The query is illustrative - the exact column names depend on the diagnostic-
setting export schema, which evolves. Verify the schema in your tenant before
using this in production reports.

### Cost Management

Azure Cost Management surfaces capacity-level cost only, **not workspace-level**.
Workspace-level allocation has to come from the Fabric Capacity Metrics app
combined with tag-based attribution. Do not expect Cost Management alone to
answer the "who consumed the capacity?" question.

---

## Monthly review cadence - Fabric side

| Review item | Source signal |
|---|---|
| Top cost drivers | Capacity utilisation by workspace (Fabric Capacity Metrics app) |
| Waste | Idle workspaces, oversized capacities, scheduled refreshes that no longer have business owners |
| Allocation gaps | Workspaces without owner, cost centre, or business purpose tags |
| Commitment status | Reserved Capacity utilisation, paused-capacity adherence to schedule |
| Anomalies | Capacity spikes, throttling events, overload windows |
| Actions | Delete idle workspaces, downsize over-provisioned capacities, reserve stable ones, govern creation |

This review is monthly during the first 6-12 months post-migration, then
quarterly once the operating model is mature.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
