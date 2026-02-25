# FinOps on Snowflake

> Snowflake-specific optimization patterns covering warehouse sizing, query efficiency, storage, and governance. 13 inefficiency patterns for diagnosing waste and building optimization roadmaps.
> Source: PointFive Cloud Efficiency Hub.

---

## Compute Optimization Patterns (5)

**Inefficient Execution Of Repeated Queries**
Service: Snowflake Query Processing | Type: Inefficient Query Pattern

Inefficient execution of repeated queries occurs when common query patterns are frequently executed without optimization. Even if individual executions are successful, repeated inefficiencies compound overall compute consumption and credit costs.

- Prioritize optimization efforts on the highest-cost or highest-frequency repeated queries
- Refactor query structures to minimize unnecessary complexity, joins, or large data scans
- Tune data models, clustering keys, or materialized views to support more efficient repeated query execution

**Suboptimal Query Timeout Configuration**
Service: Snowflake Virtual Warehouse | Type: Suboptimal Configuration

If no appropriate query timeout is configured, inefficient or runaway queries can execute for extended periods (up to the default 2-day system limit). For as long as the query is running, the warehouse will remain active and accrue costs.

- Configure a conservative account-level query timeout policy to limit maximum query execution times (e.g., 4–12 hours based on environment needs).
- Apply customized warehouse-level or user-level timeout policies for workloads that genuinely require longer execution windows.
- Regularly review and adjust query timeout settings as workload patterns evolve.

**Suboptimal Warehouse Auto Suspend Configuration**
Service: Snowflake Virtual Warehouse | Type: Suboptimal Configuration

If auto-suspend settings are too high, warehouses can sit idle and continue accruing unnecessary charges. Tightening the auto-suspend window ensures that the warehouse shuts down quickly once queries complete, minimizing credit waste while maintaining acceptable user experience (e.g., caching needs, interactive performance).

- Adjust warehouse auto-suspend settings to minimize idle billing while balancing performance needs.
- For batch and non-interactive workloads, consider shorter suspend intervals (e.g., around 60 seconds), recognizing that minimum billing granularity is already 60 seconds.
- For interactive workloads where query caching significantly improves performance, moderate suspend timers (e.g., up to 5 minutes) may be justified.

**Inefficient Workload Distribution Across Warehouses**
Service: Snowflake Virtual Warehouse | Type: Underutilized Resource

Many organizations assign separate Snowflake warehouses to individual business units or teams to simplify chargebacks and operational ownership. This often results in redundant and underutilized warehouses, as workloads frequently do not require the full capacity of even the smallest warehouse size.

- Consolidate compatible workloads onto shared warehouses to improve overall utilization without sacrificing performance.
- Adjust warehouse sizing or enable multi-cluster scaling if necessary to accommodate increased concurrency after consolidation.
- Validate SLA and performance expectations with all impacted business units or workload owners prior to consolidation.

**Underutilized Snowflake Warehouse**
Service: Snowflake Virtual Warehouse | Type: Underutilized Resource

Underutilized Snowflake warehouses occur when a workload is assigned a larger warehouse size than necessary. For example, a workload that could efficiently execute on a Medium (M) warehouse may be running on a Large (L) or Extra Large (XL) warehouse.This leads to unnecessary credit consumption without a proportional benefit to performance.

- Right-size the Snowflake warehouse by selecting a smaller size (e.g., from L to M, or M to S) that adequately supports workload performance and concurrency needs.
- Implement a periodic review process to reassess warehouse sizing based on observed usage patterns and changes in workload requirements
- Coordinate with business and engineering teams to validate any SLA requirements before resizing

---

## Storage Optimization Patterns (2)

**Retention Of Unused Data In Snowflake Table**
Service: Snowflake Tables | Type: Excessive Data Retention

Retention of stale data occurs when old, no longer needed records are preserved within active Snowflake tables. Without lifecycle policies or regular purging, tables accumulate outdated data.

- Implement data retention policies to regularly archive or delete records older than the required retention period (e.g., retain only 90 days of data if historical lookbacks are not needed beyond that)
- Collaborate with business, analytics, and compliance teams to validate acceptable data retention thresholds
- Purge old records to reduce table storage size and improve query performance by minimizing unnecessary data scans

**Excessive Snapshot Storage From High Churn Snowflake Tables**
Service: Snowflake Snapshots | Type: Inefficient Storage Usage

Snowflake automatically maintains previous versions of data when tables are modified or deleted. For tables with high churn—meaning frequent INSERT, UPDATE, DELETE, or MERGE operations—this can cause a significant buildup of historical snapshot data, even if the active data size remains small.

- Optimize Time Travel retention settings: Reduce retention periods (e.g., from 90 days to 1 day) for high-churn tables where long recovery windows are not necessary.
- Periodically clone and recreate heavily churned tables to "reset" accumulated historical storage if appropriate.
- Regularly monitor table storage metrics to proactively manage and clean up storage waste in evolving datasets.

---

## Other Optimization Patterns (6)

**Excessive Auto Clustering Costs From High Churn Tables**
Service: Snowflake Automatic Clustering Service | Type: Inefficient Configuration

Excessive Auto-Clustering costs occur when tables experience frequent and large-scale modifications ("high churn"), causing Snowflake to constantly recluster data. This leads to significant and often hidden compute consumption for maintenance tasks, especially when table structures or loading patterns are not optimized.

- Optimize data loading practices by using incremental loads and pre-sorting data where possible to minimize disruption to partition structures
- Redesign cluster key selections to prioritize columns commonly used in query filters and joins, limit the number of keys, and order by cardinality
- Disable or adjust clustering maintenance for low-value or rarely queried tables to reduce unnecessary overhead

**Inefficient Snowpipe Usage Due To Small File Ingestion**
Service: Snowflake Snowpipe | Type: Inefficient Data Ingestion

Ingesting a large number of small files (e.g., files smaller than 10 MB) using Snowpipe can lead to disproportionately high costs due to the per-file overhead charges. Each file, regardless of its size, incurs the same overhead fee, making the ingestion of numerous small files less cost-effective.

- Implement batching mechanisms to aggregate small files into larger ones before ingestion, aiming for file sizes between 10 MB and 250 MB for optimal cost-performance balance.

**Missing Or Inefficient Use Of Materialized Views**
Service: Snowflake Materialized Views | Type: Inefficient Resource Usage

Inefficiency arises when MVs are either underused or misused. When high-cost, repetitive queries are not backed by MVs, workloads consume unnecessary compute resources.

- Create materialized views for high-cost, repetitive queries where refresh costs are low relative to compute savings.
- Decommission materialized views that incur maintenance and storage costs without sufficient query usage.
- Implement periodic reviews of MV usage and refresh behavior as data volumes and access patterns evolve.

**Inefficient Pipeline Refresh Scheduling**
Service: Snowflake Tasks and Pipelines | Type: Inefficient Scheduling

Inefficient pipeline refresh scheduling occurs when data refresh operations are executed more frequently, or with more compute resources, than the actual downstream business usage requires. Without aligning refresh frequency and resource allocation to true data consumption patterns (e.g., report access rates in Tableau or Sigma), organizations can waste substantial Snowflake credits maintaining underutilized or rarely accessed data assets.

- Adjust pipeline refresh frequencies to better align with actual data access patterns (e.g., move from hourly to daily refresh if applicable)
- Right-size the warehouse resources used for pipeline executions to minimize overprovisioning
- Implement usage monitoring frameworks that continuously correlate refresh costs with downstream consumption

**Suboptimal Use Of Search Optimization Service**
Service: Snowflake Search Optimization Service | Type: Suboptimal Configuration and Usage

Search Optimization can enable significant cost savings when selectively applied to workloads that heavily rely on point-lookup queries. By improving lookup efficiency, it allows smaller warehouses to satisfy performance SLAs, reducing credit consumption.

- Enable Search Optimization selectively on columns supporting frequent, high-value point-lookup queries
- After enabling Search Optimization, reassess and right-size warehouses where feasible.
- Remove Search Optimization from tables or columns with low query activity to eliminate unnecessary storage and maintenance costs.

**Suboptimal Query Routing**
Service: Snowflake Query Processing | Type: Suboptimal Query Routing and Warehouse Utilization

Organizations may experience unnecessary Snowflake spend due to inefficient query-to-warehouse routing, lack of dynamic warehouse scaling, or failure to consolidate workloads during low-usage periods. Third-party platforms offer solutions to address these inefficiencies: Sundeck enables highly customizable, SQL-based control over the query lifecycle through user-defined rules (Flows, Hooks, Conditions).

- Implement customizable query lifecycle management platforms (e.g., Sundeck) if granular control is required and in-house SQL/DevOps expertise is available
- Deploy AI-driven warehouse optimization platforms (e.g., Keebo) for organizations prioritizing ease of use and autonomous cost management
- Pilot third-party solutions in a limited environment to validate cost savings and performance impacts before full-scale adoption

---
