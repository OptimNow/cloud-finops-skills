---
name: finops-databricks
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Rate Optimization", "Allocation"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Product", "Finance"]
fcp_maturity_entry: "Walk"
business_coverage: ["data-platforms:data:deep", "data-platforms:bill:deep", "data-platforms:commitments:deep", "data-platforms:waste:deep", "data-platforms:budget:partial", "data-platforms:ai:partial", "data-platforms:contracts:partial", "aws:data:partial", "azure:data:partial"]
---

# FinOps on Databricks

> Databricks-specific FinOps guidance covering cost data foundations (system tables,
> serverless usage policies, serverless and model-serving attribution), allocation and
> governance, commitment instruments, and 18 inefficiency patterns for diagnosing
> waste and building optimisation roadmaps.

---

## The data-platform FinOps problem

For Databricks (and Microsoft Fabric, see `finops-fabric.md` for the parallel
treatment), the cost object the platform reports - workspace, capacity, DBU hours,
query execution, capacity unit consumption - is rarely the same as the business
object Finance wants to allocate against (application, product, team, business unit,
data domain, use case). A shared workspace or shared Fabric capacity does not
naturally tell Finance who consumed what. The FinOps model needs a translation
layer between platform telemetry and business ownership. **Build the model around
the consumption driver, then reconcile it back to the invoice - not the other way
around.**

This framing is shared with `finops-fabric.md`. The mechanics differ between the two
platforms; the allocation problem is the same.

---

## Cost data foundations on Databricks

Databricks cost data lives primarily in **system tables** in Unity Catalog. Account-
admin queries against these tables are the canonical FinOps source of truth - cluster
UI snapshots, dashboards, and per-workspace reports all derive from the same data.
For attribution and custom tooling, query the system tables directly; the UI is for
ad-hoc views.

**FOCUS support:** As of December 2024, Databricks supports FOCUS v1.0 for
standardised cost data export, enabling cross-cloud normalisation with other
FOCUS-compliant providers (AWS v1.2, Azure v1.2, GCP v1.0). This simplifies
multi-cloud FinOps implementations by providing a common schema for cost allocation
and analysis across platforms.

### `system.billing.usage` - the canonical billing table

The core table for Databricks FinOps. One row per usage record
(typically 1-hour granularity), with fields covering account, workspace, SKU, DBUs
consumed, list-price USD, and identifiers for the workload that consumed the DBUs
(`usage_metadata` includes job_id, cluster_id, warehouse_id, endpoint_id depending
on workload type).

**Practical usage patterns:**
- Daily allocation by team / tag / project: join `usage_metadata.tags` to a team
  mapping; aggregate `usage_quantity` (DBUs) and `usage_quantity * list_price` (USD).
- Job-level cost trending: filter by `billing_origin_product = 'JOBS'` and join to
  `system.lakeflow.jobs` for job names.
- Pipeline-level cost: join `usage_metadata.dlt_pipeline_id` to
  `system.lakeflow.pipelines` (generally available since 21 October 2026). The table is
  a slowly changing dimension: take the latest row per `workspace_id` and `pipeline_id`
  by `change_time`, then drop rows that carry a `delete_time`. Materialized views,
  online tables, AI Search indexing and Lakeflow Connect ingestion bill under a pipeline
  ID, so this join is where their cost appears. Sources:
  https://docs.databricks.com/aws/en/admin/system-tables/billing,
  https://docs.databricks.com/aws/en/admin/system-tables/jobs
- Anomaly detection: month-over-month delta per workspace per SKU, flagged at >20%.

**Important nuances:**
- Data is account-level (not workspace-level) - all workspaces under one account
  show up in the same table, controlled by `account_id`.
- List-price USD is the published price, not the customer's negotiated rate. For
  effective cost, multiply by your contract discount or join to `system.billing.list_prices`
  for historical price rate-card.
- Usage records appear with a typical 24-48 hour lag; do not use this for real-time
  alerting (use cluster-level metrics for that).

Source: https://docs.databricks.com/aws/en/admin/system-tables/billing

### Serverless usage policies and budgets - attribution and alerting are separate

Databricks now calls budget policies **serverless usage policies**, and the
documentation describes them as an attribution object, not a spend control. A
policy carries a set of tags; serverless work that runs under it (notebooks,
jobs, Lakeflow pipelines, apps, model serving endpoints, Lakebase projects)
lands in `system.billing.usage` with those tags in the `custom_tags` column.
The policy does not tag classic compute, the documentation does not list SQL
warehouses, and nothing in it caps or stops spend.

**What a usage policy does:**
- **Serverless cost attribution before the fact.** Serverless compute exposes no
  node-level tags, so the policy is the documented way to make a serverless DBU
  arrive in the billing table already labelled with team and cost centre.
- **Account-level assignment** to users, groups or service principals, scoped
  to every workspace or to a chosen list. A user with one policy gets it
  applied automatically; a user with several must pick one, and the default is
  the first alphabetically, which is worth knowing when a team's usage shows
  up under the wrong label.

**What alerts, and what blocks.** Alerting is the separate **budgets** feature:
an account-level budget with up to four monthly thresholds and email
notifications, filterable by workspace and by tag, which is where the usage
policy's tags earn their keep. The documentation says not to use budgets as an
absolute spend cap, because usage data can arrive up to 24 hours late. The one
blocking control it documents is **Block usage** on a Unity Gateway threshold,
and it describes that enforcement as approximate. The runtime caps a FinOps
team expects (idle timeout, hourly burn, allowed instance types) live in
compute policies, covered under "Allocation and Governance" below.

**FinOps integration pattern:** one usage policy per team or cost centre,
assigned to the groups that submit serverless work; one budget per cost
centre, filtered on the policy's tags, with thresholds at 50%, 80% and 100% of
plan; a monthly reconciliation of `custom_tags` in `system.billing.usage`
against the policy list, with serverless usage that carries no policy tag
routed to a visible "unattributed" line. This turns serverless from an
attribution-blind cost into a per-team line item. It does not make it a capped
one.

Sources: <https://docs.databricks.com/aws/en/admin/usage/budget-policies> and
<https://docs.databricks.com/aws/en/admin/account-settings/budgets> (both read
14 October 2026). An earlier version of this section described budget policies
as a spend cap with hard-stop enforcement; the documentation does not support
that, and the text was corrected in October 2026.

### Serverless attribution - what changes vs classic compute

Serverless compute (SQL Warehouses serverless, Jobs serverless, Model Serving)
differs from classic compute in two FinOps-relevant ways:

1. **No node-level visibility.** You don't see the underlying VMs - Databricks
   manages capacity and charges per DBU consumed. Cluster-level monitoring
   patterns (autoscaler tuning, node pool selection) don't apply.
2. **Attribution flows through workload IDs and usage policies, not cluster tags.**
   Tag the *workload* (job, warehouse, endpoint) or run it under a serverless
   usage policy; the tags propagate to `system.billing.usage` (`usage_metadata`
   for workload tags, `custom_tags` for policy tags).

The serverless billing system table - `system.billing.usage` filtered to serverless
SKUs, plus the more detailed serverless-specific tables - is the right starting
point for serverless cost analysis. Don't try to back-derive cost from query
duration; let the billing system tell you what it cost.

Source: https://docs.databricks.com/aws/en/admin/system-tables/serverless-billing

### Model serving attribution

Databricks Model Serving (foundation model APIs and custom-deployed models) bills
through dedicated meters that show up in `system.billing.usage` with
`billing_origin_product = 'MODEL_SERVING'` and per-endpoint identifiers in
`usage_metadata`.

**Two distinct cost categories within model serving:**
- **Provisioned throughput** - dedicated capacity for production endpoints, billed
  per DBU-hour regardless of request volume. Right-size against P95 throughput.
- **Pay-per-token** - token-based billing for foundation model APIs (Llama, Mixtral,
  etc. served by Databricks). Billed per 1k input/output tokens.

**Per-endpoint attribution pattern:** require all model-serving endpoints to carry
a `cost_centre` and `application` tag at deployment. Aggregate from
`system.billing.usage` weekly to surface high-cost endpoints and re-evaluate
provisioned-throughput sizing for ones consistently below 50% utilisation.

**External models and negotiated rates.** For external model provider services, the
spend estimates Databricks shows are computed at list rates. Since September 2026 a
**price multiplier** can be set on the model provider service so those estimates
match a negotiated discount. Set it before the estimates feed
showback; otherwise external-model spend is overstated by exactly the discount.
The multiplier is the contracted fraction of list price (0.8 for a 20% discount) and
flows into `system.ai_gateway.external_model_spend`. It applies only to requests made
after it is set, and not to Databricks-hosted partner models. Source:
<https://docs.databricks.com/aws/en/ai-gateway/create-model-provider-services>.

---

## Compute Optimization Patterns (15)

**Inefficient Query Design In Databricks Sql And Spark Jobs**
Service: Databricks SQL | Type: Inefficient Configuration

Many Spark and SQL workloads in Databricks suffer from micro-optimization issues - such as unfiltered joins, unnecessary shuffles, missing broadcast joins, and repeated scans of uncached data. These problems increase compute time and resource utilization, especially in exploratory or development environments.

- Enable Adaptive Query Execution to improve join strategies and reduce shuffle
- Use broadcast joins for small lookup tables where applicable
- Apply filtering and predicate pushdown early in the query

**Inefficient Use Of Photon Engine In Databricks Compute**
Service: Databricks Clusters | Type: Inefficient Configuration

Photon is enabled by default on many Databricks compute configurations. While it can accelerate certain SQL and DataFrame operations, its performance benefits are workload-specific and may not justify the increased DBU cost.

- Update default compute configurations to disable Photon for general-purpose or low-complexity workloads
- Restrict users from enabling Photon unless justified by benchmarked performance gains
- Establish cluster policies or templates that exclude Photon by default and allow opt-in only under specific conditions

**Lack Of Workload Specific Cluster Segmentation**
Service: Databricks Compute | Type: Inefficient Configuration

Running varied workload types (e.g., ETL pipelines, ML training, SQL dashboards) on the same cluster introduces inefficiencies. Each workload has different runtime characteristics, scaling needs, and performance sensitivities.

- Define and enforce separate cluster types for distinct workload categories (e.g., SQL, ML, ETL)
- Encourage the use of job clusters for short-lived, batch-oriented workloads to ensure clean isolation and efficient resource use
- Use job clusters for single-purpose, short-lived jobs to ensure isolation and efficient spin-up

**Overuse Of Photon In Non Production Workloads**
Service: Databricks Compute | Type: Inefficient Configuration

Photon is frequently enabled by default across Databricks workspaces, including for development, testing, and low-concurrency workloads. In these non-production contexts, job runtimes are typically shorter, SLAs are relaxed or nonexistent, and performance gains offer little business value.

- Disable Photon by default in dev/test environments using workspace settings or cluster policies
- Create separate cluster templates or policies for production and non-production workloads
- Use tagging or automation to flag or block Photon usage in low-priority environments

**Poorly Configured Autoscaling On Databricks Clusters**
Service: Databricks Compute | Type: Inefficient Configuration

Autoscaling is a core mechanism for aligning compute supply with workload demand, yet it's often underutilized or misconfigured. In older clusters or ad-hoc environments, autoscaling may be disabled by default or set with tight min/max worker limits that prevent scaling.

- Use autoscaling for variable workloads, but avoid overly wide min/max ranges that allow clusters to over-expand. Databricks may aggressively scale up if limits are too high, leading to cost spikes and instability.
- For predictable, recurring jobs with stable compute requirements, consider using fixed-size clusters to avoid the cost and time of scaling transitions.
- Tune autoscaling thresholds based on real workload behavior. Start narrow and adjust iteratively, based on runtime performance and cluster utilization.

**Underuse Of Serverless For Short Or Interactive Workloads**
Service: Databricks SQL | Type: Inefficient Configuration

Many organizations continue running short-lived or low-intensity SQL workloads - such as dashboards, exploratory queries, and BI tool integrations - on traditional clusters. This leads to idle compute, overprovisioning, and high baseline costs, especially when the clusters are always-on.

- Migrate lightweight SQL workloads and dashboards to Databricks SQL Serverless
- Enable serverless for high-concurrency, low-compute scenarios where persistent compute isn't needed
- Set policies or guidelines to default to serverless for interactive workloads unless specific performance reasons require otherwise

**Inefficient Bi Queries Driving Excessive Compute Usage**
Service: Interactive Clusters | Type: Inefficient Query Patterns

Business Intelligence dashboards and ad-hoc analyst queries frequently drive Databricks compute usage - especially when:

- Dashboards are auto-refreshed too frequently
- Queries scan full datasets instead of using filtered views or materialized tables
- Inefficient joins or large broadcast operations are used
- Redundant or exploratory queries are triggered during interactive exploration

This often results in clusters staying active for longer than necessary, or being autoscaled up to handle inefficient workloads, leading to unnecessary DBU consumption.

- Refactor BI queries to limit scan scope and reduce complexity
- Materialize frequently used intermediate results into temp or Delta tables
- Reduce auto-refresh frequency of dashboards unless real-time data is essential

**Inefficient Autotermination Configuration For Interactive Clusters**
Service: Databricks Clusters | Type: Misconfiguration

Interactive clusters are often left running between periods of active use. To mitigate idle charges, Databricks provides an “autotermination” setting that shuts down clusters after a period of inactivity.

- Lower the autotermination threshold for interactive clusters
- Apply workspace compute policies to cap the maximum idle time for clusters
- Grant exceptions only when use cases are documented and cost impact is understood

**Inefficient Use Of Interactive Clusters**
Service: Databricks Clusters | Type: Misconfiguration

Interactive clusters are intended for development and ad-hoc analysis, remaining active until manually terminated. When used to run scheduled jobs or production workflows, they often stay idle between executions - leading to unnecessary infrastructure and DBU costs.

- Reassign scheduled jobs to ephemeral job clusters
- Apply workspace policies to enforce job cluster usage for scheduled workflows
- Educate users on the differences between cluster modes and their appropriate use cases

**Missing Auto Termination Policy For Databricks Clusters**
Service: Databricks Clusters | Type: Missing Safeguard

In many environments, users launch Databricks clusters for development or analysis and forget to shut them down after use. When no auto-termination policy is configured, these clusters remain active indefinitely, incurring unnecessary charges for both Databricks and cloud infrastructure usage.

- Enable auto-termination for all clusters that do not require persistent runtime
- Set cluster policies to require auto-termination configuration for new clusters
- Establish reasonable inactivity thresholds based on workload type (e.g., 30-60 minutes for interactive)

**Oversized Worker Or Driver Nodes In Databricks Clusters**
Service: Databricks Clusters | Type: Overprovisioned Resource

Databricks users can select from a wide range of instance types for cluster driver and worker nodes. Without guardrails, teams may choose high-cost configurations (e.g., 16xlarge nodes) that exceed workload requirements.

- Define and enforce compute policies that restrict driver and worker node types to appropriate sizes
- Reconfigure existing clusters using oversized nodes to use smaller, cost-effective alternatives
- Allow exceptions only for workloads that demonstrably require high-performance nodes

**Underuse Of Serverless Compute For Jobs And Notebooks**
Service: Databricks Serverless Compute | Type: Suboptimal Execution Model

Databricks Serverless Compute is now available for jobs and notebooks, offering a simplified, autoscaled compute environment that eliminates cluster provisioning, reduces idle overhead, and improves Spot survivability. For short-running, bursty, or interactive workloads, Serverless can significantly reduce cost by billing only for execution time.

- Pilot Serverless for eligible workloads, such as short, periodic jobs or ad-hoc notebooks
- Use compute policies or templates to promote Serverless adoption where appropriate
- Retain traditional clusters for workloads with unsupported libraries or long-lived compute patterns

**Lack Of Graviton Usage In Databricks Clusters**
Service: Databricks Clusters | Type: Suboptimal Instance Selection

Databricks supports AWS Graviton-based instances for most workloads, including Spark jobs, data engineering pipelines, and interactive notebooks. These instances offer significant cost advantages over traditional x86-based VMs, with comparable or better performance in many cases.

- Monitor utilized instance types and recommend Graviton-based families
- Reconfigure default cluster templates to use Graviton by default
- Allow exceptions only for workloads with documented compatibility or performance issues

**On Demand Only Configuration For Non Production Databricks Clusters**
Service: Databricks Clusters | Type: Suboptimal Pricing Model

In non-production environments - such as development, testing, and experimentation - many teams default to on-demand nodes out of habit or caution. However, Databricks offers built-in support for using spot instances safely.

- Enable spot instance usage for non-production clusters where workloads are resilient to interruption
- Use Databricks' native fallback-to-on-demand capabilities to preserve job continuity
- Establish workspace-level defaults or templates that promote spot usage in dev/test clusters

**Suboptimal Use Of On Demand Instances In Non Production Clusters**
Service: Databricks Clusters | Type: Suboptimal Pricing Model

In Databricks, on-demand instances provide reliable performance but come at a premium cost. For non-production workloads - such as development, testing, or exploratory analysis - high availability is often unnecessary.

- Implement compute policies that cap the percentage of on-demand nodes in relevant workloads
- Update existing cluster configurations to prioritize Spot usage for dev/test workloads
- Allow exceptions only when reliability or performance constraints are well documented

---

## Storage Optimization Patterns (1)

**Missing Delta Optimization Features For High Volume Tables**
Service: Delta Lake | Type: Suboptimal Data Layout

In many Databricks environments, large Delta tables are created without enabling standard optimization features like partitioning and Z-Ordering. Without these, queries scanning large datasets may read far more data than necessary, increasing execution time and compute usage.

- Apply partitioning when writing Delta tables, using columns commonly filtered in queries
- Enable Z-Ordering on appropriate columns to improve data skipping efficiency
- Use `OPTIMIZE` and `VACUUM` to reduce file fragmentation and improve query performance

Predictive optimization runs `OPTIMIZE`, `VACUUM` and `ANALYZE` automatically on Unity
Catalog managed tables (not external tables), enabled at account, catalog, schema or
table level. It runs on serverless compute for jobs and is billed under a serverless jobs
SKU, so its cost appears as serverless jobs usage, not under the cluster or warehouse
that queries the table; `system.storage.predictive_optimization_operations_history`
records what ran on which table
([predictive optimization](https://docs.databricks.com/aws/en/optimizations/predictive-optimization),
read 22 October 2026).

---

## Other Optimization Patterns (2)

**Inefficient Use Of Job Clusters In Databricks Workflows**
Service: Databricks Workflows | Type: Suboptimal Cluster Configuration

When multiple tasks within a workflow are executed on separate job clusters - despite having similar compute requirements - organizations incur unnecessary overhead. Each cluster must initialize independently, adding latency and cost.

- Configure a shared job cluster to run multiple tasks within the same workflow when compute requirements are similar
- Use cluster reuse settings to reduce start-up overhead and improve efficiency
- Validate that consolidation does not impact workload performance or isolation requirements before implementing

**Lack Of Functional Cost Attribution In Databricks Workloads**
Service: Databricks | Type: Visibility Gap

Databricks cost optimization begins with visibility. Unlike traditional IaaS services, Databricks operates as an orchestration layer spanning compute, storage, and execution - but its billing data often lacks granularity by workload, job, or team.

- Orchestration (DBUs): Analyze query/job-level execution and optimize workload design
- Compute: Review underlying VM types and cost models (e.g., Spot, RI, Savings Plans)
- Storage: Align S3/ADLS/GCS usage with lifecycle policies and avoid excessive churn

---

## Allocation and Governance

The optimisation patterns above answer "where is the waste?" This section answers
"who pays?" - the harder problem on a shared data platform.

### Workspace-level reporting is necessary but not sufficient

Workspace cost alone is too coarse. A single workspace is shared across teams, jobs,
notebooks, pipelines, and experiments. Allocating only by workspace owner risks
charging the platform owner or default business unit, not the actual consumer.

A useful Databricks allocation model layers signals:

| Layer | Allocation signal | Why it matters |
|---|---|---|
| Workspace | name, owner, business mapping | First-level showback |
| Compute | cluster, job, pool usage | Identifies major technical cost drivers |
| Execution | query executor, job owner, notebook owner | Links cost to users or teams |
| Consumption | DBU hours | Core usage metric |
| Financial view | amortised vs PAYG cost | Shows savings from commitments |

The strongest single allocation pattern: **DBU hours by executor or workload,
translated into amortised cost.**

```sql
-- DBU hours by executor / job, joined to workspace metadata, last 30 days
-- Adjust to your account's system table location and tag conventions.
WITH usage_by_executor AS (
  SELECT
    workspace_id,
    coalesce(usage_metadata.job_id,
             usage_metadata.cluster_id,
             usage_metadata.warehouse_id,
             usage_metadata.endpoint_id) AS workload_id,
    coalesce(identity_metadata.run_as,
             usage_metadata.created_by) AS executor,
    sku_name,
    sum(usage_quantity) AS dbu_hours,
    sum(usage_quantity * list_price) AS list_usd
  FROM system.billing.usage
  LEFT JOIN system.billing.list_prices USING (sku_name, currency_code, usage_unit)
  WHERE usage_date >= current_date() - INTERVAL 30 DAY
  GROUP BY ALL
)
SELECT
  workspace_id,
  executor,
  workload_id,
  sku_name,
  round(sum(dbu_hours), 2) AS dbu_hours,
  round(sum(list_usd), 2) AS list_usd_30d
FROM usage_by_executor
GROUP BY ALL
ORDER BY list_usd_30d DESC
LIMIT 50;
```

The query is illustrative - your `system.billing.list_prices` schema and
identity-metadata fields may differ; adapt column names to your account.

### Classic compute total cost and instance pools

Classic compute has two bills: DBUs from Databricks, and VMs, disks and network from the
cloud provider. `system.billing.usage` carries only the first. Instance pools move the
second bill away from its consumer:

- Databricks charges no DBUs while instances sit idle in a pool, but the cloud provider
  bills them ([Azure Databricks pools](https://learn.microsoft.com/en-us/azure/databricks/compute/pool-index)).
- When clusters are created from pools, only workspace and pool tags propagate to the
  VMs; cluster tags do not, so the pool's VM cost carries the pool owner's tags, not the
  consuming team's ([usage detail tags](https://learn.microsoft.com/en-us/azure/databricks/admin/account-settings/usage-detail-tags)).
  On Azure the default `DatabricksInstancePoolId` tag on those VMs is the join key on the
  cloud side.

Re-allocate pool infrastructure from the compute system tables: `system.compute.node_timeline`
holds minute-by-minute records per instance (`cluster_id`, `instance_id`), and
`system.compute.clusters` records `driver_instance_pool_id` and `worker_instance_pool_id`
([compute system tables](https://docs.databricks.com/aws/en/admin/system-tables/compute);
all three pages read 21 October 2026). Split each pool's cloud cost by the node-minutes of
the clusters that used it. Pool VM cost not matched by any cluster's node-minutes is the
pool's idle cost: keep it as a visible line for the pool owner, who controls the pool's
minimum idle size. 84.51° re-allocates shared pool spend this way and reports DBU and
infrastructure cost together as Databricks total cost (Josh Anness, FinOps X 2026).

A community repository, `databricks-solutions/cloud-infra-costs`, combines classic DBU and
cloud infrastructure cost and emits FOCUS 1.4; its own page states that Databricks support
does not cover it, so treat it as a starting point to review, not a supported product.

### Compute policies - the runtime enforcement layer for classic compute

A usage policy labels serverless spend; it constrains nothing. On classic
compute (all-purpose and job clusters) the constraining object is the
**compute policy**: a JSON document that fixes, bounds or requires attributes
of any cluster created under it. Four attributes do most of the FinOps work:

| Attribute | What it controls | Policy shape |
|---|---|---|
| `custom_tags.<key>` | Presence and value of a tag on every cluster under the policy | `fixed` (one value), `allowlist` (a set) or `regex` (a shape); any limiting type makes the key required unless `isOptional` is true |
| `autotermination_minutes` | Idle time before the cluster shuts itself down; `0` means never | `fixed`, or `range` with a `maxValue` so nobody can raise it past the ceiling |
| `dbus_per_hour` | Hourly DBU burn, a calculated attribute covering driver and workers | `range` with a `maxValue`, which the documentation presents as the direct way to cap cost per cluster |
| `node_type_id` | Which instance types a user can pick | `allowlist`, or `regex` to admit a family range |

A policy that requires a `cost_centre` tag, caps `autotermination_minutes` at
60, caps `dbus_per_hour` at a value sized to the team's plan and restricts
`node_type_id` to a short list is the Databricks equivalent of the IaC and SCP
prevention layer in `finops-tagging.md`: the violation is rejected at creation,
not reported after the invoice.

```json
{
  "custom_tags.cost_centre": { "type": "allowlist", "values": ["CC-1200", "CC-1210", "CC-1340"] },
  "autotermination_minutes": { "type": "range", "maxValue": 60, "defaultValue": 30 },
  "dbus_per_hour": { "type": "range", "maxValue": 50 },
  "node_type_id": { "type": "allowlist", "values": ["m6id.xlarge", "m6id.2xlarge"], "defaultValue": "m6id.xlarge" }
}
```

Two operating notes. A policy binds only the users it is granted to, and a
user who holds the unrestricted cluster-creation entitlement is bound by
none, so the entitlement audit comes before the policy design. And a ceiling
that is too tight produces override requests within months: a Databricks
product manager, Sadhana Bala, described the "day-one caps, month-six
exceptions" cycle at FinOps X 2026 as the common shape across customers. Set
the ceilings from the team's own 90-day usage rather than a round number, and
review them each quarter.

Source: <https://docs.databricks.com/aws/en/admin/clusters/policy-definition>
(read 14 October 2026).

### Query-level attribution on SQL warehouses

A shared SQL warehouse bills DBUs per warehouse in `system.billing.usage`, so the
executor query above stops at "the warehouse" and cannot say which team's queries
drove the bill. Two features, both GA in September 2026, close that gap:

- **`system.query.history`** records every query run on a SQL warehouse or serverless
  compute, with its execution status, duration metrics and query source.
- **Query tags** attach key-value pairs to a query, set with `SET QUERY_TAGS` in SQL or
  the connector's `query_tags` session parameter. Limits: at most 20 tags per query,
  128 characters per key or value, 10 KB per session. Tags land in the `query_tags`
  column of `system.query.history`.

The allocation pattern: require every client of a shared warehouse (BI tool, dbt, the
application connector) to set a `team` and `application` tag, then split each
warehouse's daily DBUs across tags pro rata to query execution time from
`system.query.history`. This is an **apportionment, not a metered figure**: idle time,
warm-up and concurrency are spread by the rule, so publish the rule with the numbers
and route untagged queries to a visible "unattributed" line rather than to the
warehouse owner. Tags do not appear in `system.billing.usage`; the join is by warehouse
and time window.

Sources: <https://docs.databricks.com/aws/en/release-notes/product/2026/september>,
<https://docs.databricks.com/aws/en/sql/user/queries/query-tags> (read 2 October 2026).

### The Azure VM Reservation vs DBU clarification

**Common trap.** Databricks compute runs on Azure VMs, so **Azure VM Reservations
apply to the underlying VM compute layer**. But Databricks also charges a separate
**DBU meter** for the Databricks platform layer, billed independently. **Azure VM
RIs do not cover the DBU meter.**

- Azure VM RI -> covers the VM hourly charge.
- DBU meter -> covered by Databricks-specific commitments (DBCU, see below) or
  paid PAYG.

Customers coming from VM-only commitment thinking often assume an Azure RI on the
underlying VM family covers their Databricks bill. It covers half of it. Surface
both meters separately when modelling Databricks commitment economics.

### Databricks commitment instruments

- **Committed use (a Usage Commitment with Databricks, a DBCU plan on Azure)** - a
  prepaid dollar commitment to DBU usage for 1 to 3 years, priced on published
  bands (below). Separate from Azure RIs and Savings Plans, which cover the VM meter only.

**Published discount bands.** Databricks publishes its committed-use bands in its UK
G-Cloud 14 pricing document, by total commitment value after discount. The Azure
Databricks pre-purchase (DBCU) plans in the Azure Retail Prices API carry the same
values: each plan's price is the lower bound of the band at the same discount, for
example 12,500 DBCUs (worth $12,500 of pay-as-you-go DBUs) for $12,000 (both read
24 October 2026).

| 1-year commitment from | Discount | 3-year commitment from | Discount |
|---|---|---|---|
| $12,000 | 4% | $35,250 | 6% |
| $23,500 | 6% | $69,000 | 8% |
| $46,000 | 8% | $135,000 | 10% |
| $89,000 | 11% | $261,000 | 13% |
| $172,000 | 14% | $504,000 | 16% |
| $287,000 | 18% | $819,000 | 22% |
| $400,000 | 20% | $1,140,000 | 24% |
| $577,500 | 23% | $1,642,500 | 27% |
| $730,000 | 27% | $2,070,000 | 31% |
| $1,050,000 | 30% | $2,970,000 | 34% |
| $1,340,000 | 33% | $3,780,000 | 37% |

Values are the commitment over the whole term. A 24-month schedule exists on the
same pattern: the 12-month percentages at twice the threshold, from 4% at $24,000 to
33% at $2,680,000. The bands are the published floor; what a large account obtains
beyond them is negotiated and not public.

**What the paper says** (G-Cloud 14 Usage Commitment Pricing Annex):
- Each Contract Year is billed as an **Advance Payment**, non-refundable and not a
  credit for services after the term. Databricks may accelerate the schedule when
  usage runs ahead of it.
- A shortfall at the end of the term is billed as a **True-Up Payment**: the total
  commitment less the commitment fees paid. Unused commitment is paid for and lost
  unless the Order Form says otherwise.
- Usage above the commitment is billed monthly in arrears "subject to the Discount",
  at the contracted rate on this paper. Practitioner sources report list-rate overage
  on other contracts: read the overage clause in your Order Form before assuming either.
- The committed-use discount "may not be combined with any other discounts".

**Azure Databricks is a separate contract.** It is a Microsoft first-party service:
the customer contracts with Microsoft, which sets the price and bills it on the Azure
subscription. A DBCU plan covers the DBU meter only; VM, storage and network stay on
the Azure bill. DBCU plans cannot be cancelled, exchanged, split or merged. Databricks'
Cloud Provider Directory states that Powered Services usage "may not count toward your
Universal Commitment" with Databricks unless confirmed in writing, so a direct
commitment on AWS or Google Cloud does not cover an Azure Databricks estate by default.
Microsoft does not state whether a DBCU purchase decrements a MACC: check it in the
portal's MACC view before counting on it.

**Support is priced on the commitment.** On AWS and Google Cloud, support is the
greater of a floor or a share of the annual product commitment: Business $15,000 or
15%, Enhanced $30,000 or 20%, Production $60,000 or 25%, Mission Critical $120,000 or
35% (G-Cloud 14 support rate card, filed 17 November 2025). A larger commitment raises
the support bill with it; model the two together.

**Serverless moves spend between two commitments.** Serverless compute runs in
Databricks' compute plane and its infrastructure cost sits inside the DBU price, so a
serverless migration moves spend out of the cloud provider's commitment (EDP, MACC,
Google Cloud commitment) and into the Databricks one. Size them together: the
Databricks commitment on DBUs from `system.billing.usage`, the cloud commitment on the
VM hours the remaining classic DBUs imply.

**Fiscal calendar.** Databricks' fiscal year ends 31 January; quarters end 30 April,
31 July, 31 October and 31 January (Series J press release, 17 December 2024). Some
practitioner calendars place its quarter ends in March, June, September and December;
the official calendar overrides them.

Sources: <https://assets.applytosupply.digitalmarketplace.service.gov.uk/g-cloud-14/documents/720473/231837180032941-pricing-document-2024-04-30-1430.pdf>
(bands and annex, filed 30 April 2024),
<https://assets.applytosupply.digitalmarketplace.service.gov.uk/g-cloud-14/documents/720473/415786224708639-pricing-document-2025-11-17-1036.pdf>
(support),
<https://prices.azure.com/api/retail/prices> (service Azure Databricks, price type
Reservation, read 24 October 2026),
<https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/prepay-databricks-reserved-capacity>
(updated 17 July 2026), <https://databricks.com/legal/cloud-provider-directory>
(modified 27 August 2026),
<https://www.databricks.com/company/newsroom/press-releases/databricks-raising-10b-series-j-investment-62b-valuation>.

**Factors that move the DBU volume a commitment has to cover:**

- **Photon multiplier** - Photon-enabled clusters consume DBUs at roughly 2x the
  base rate but execute 2-3x faster on supported workloads (vectorised SQL,
  certain DataFrame ops). Net cost can go down despite the multiplier; depends on
  workload. Validate per workload before defaulting Photon on or off org-wide.
- **Serverless premium** - Serverless SQL Warehouses, jobs, and notebooks consume
  DBUs at a higher rate (roughly 1.5-2x) than classic compute. Trade-off: no
  cluster management overhead, near-instant start, no idle cost. Worth it for
  spiky interactive work; not always worth it for steady-state heavy jobs.
- **DBU rates differ by workload type** - Jobs Compute is the cheapest tier,
  All-Purpose is the most expensive, SQL Warehouse sits between with tier-
  dependent rates. Migrating a scheduled job from All-Purpose to Jobs Compute is
  often a 30-40% saving with zero functional change. **Verify current rates
  against the Databricks Azure pricing page; do not hard-code.**

### Amortised vs PAYG visibility - splitting the conversation

A useful Databricks cost report shows **both amortised cost and PAYG-equivalent
cost.** This separates two distinct conversations:

- **Consumption conversation** - "Who used the platform, and how much?" - driven
  by DBU hours and PAYG-equivalent cost. The right view for showback to teams,
  capacity planning, and unit-economics work.
- **Commercial effectiveness conversation** - "How much did reservations or DBCU
  commitments reduce the effective rate?" - driven by amortised vs PAYG delta.
  The right view for finance to assess commitment ROI and for FinOps to track ESR
  (Effective Savings Rate).

Without this split, teams may believe their behaviour generated savings when the
savings came from centralised commitment purchasing, or the reverse - a
team that reduced consumption sees no impact in their amortised number
because the contractual amortisation is fixed.

### Monthly review cadence - Databricks side

| Review item | Source signal |
|---|---|
| Top cost drivers | DBU hours by workspace, job, user (from `system.billing.usage` joined to `system.lakeflow.jobs`) |
| Waste | Idle clusters, unused jobs, oversized clusters (cluster events + utilisation metrics) |
| Allocation gaps | Unmapped workspaces, missing executor labels, untagged workloads |
| Commitment status | DBCU utilisation, RI utilisation on underlying VMs, PAYG-equivalent vs amortised delta |
| Anomalies | DBU hour spikes, query activity spikes (>20% week-over-week threshold) |
| Unit cost | Total cost per DBU: DBU cost plus allocated cloud infrastructure, divided by DBUs. Compare it within one SKU and discount level, because the DBU rate differs by SKU and commitment discount, so a change in workload mix moves the ratio too; within one SKU it isolates infrastructure efficiency, where spot adoption and VM rightsizing move it and DBU volume does not (84.51° used job cost per DBU to set targets, Josh Anness, FinOps X 2026) |
| Actions | Tune jobs, remove clusters, fix labels, scope new commitments |

This feeds Finance, platform engineering, and data owners simultaneously - the
review is not three separate meetings.

### Sequencing - clean up before committing

Standard FinOps sequencing applies to Databricks specifically. Each step is a
prerequisite for the next:

1. Remove idle clusters and abandoned workspaces.
2. Right-size clusters that survive cleanup.
3. Migrate jobs from All-Purpose to Jobs Compute where appropriate (cheapest tier).
4. Establish baseline consumption over 60-90 days post-cleanup.
5. **Then** commit via DBCU and / or Azure VM RIs on the underlying compute.

**Reserving before cleanup turns waste into a contractual baseline.** This is the
most expensive ordering mistake OptimNow has seen on Databricks engagements - DBCU
commitments are non-trivial and a year-long commitment to over-provisioned clusters
is hard to unwind.

Source for the data-platform allocation framing: a FinOps Foundation practitioner
webinar on data-platform allocation (Databricks + Fabric); title and date were not
recorded, so treat the framing as practitioner observation rather than a citable source.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
