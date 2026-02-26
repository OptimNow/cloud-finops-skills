# FinOps on Databricks

> Databricks-specific optimization patterns covering compute clusters, jobs, storage, and configuration. 18 inefficiency patterns for diagnosing waste and building optimization roadmaps.
> Source: PointFive Cloud Efficiency Hub.

---

## Compute Optimization Patterns (15)

**Inefficient Query Design In Databricks Sql And Spark Jobs**
Service: Databricks SQL | Type: Inefficient Configuration

Many Spark and SQL workloads in Databricks suffer from micro-optimization issues  - such as unfiltered joins, unnecessary shuffles, missing broadcast joins, and repeated scans of uncached data. These problems increase compute time and resource utilization, especially in exploratory or development environments.

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

Many organizations continue running short-lived or low-intensity SQL workloads  - such as dashboards, exploratory queries, and BI tool integrations  - on traditional clusters. This leads to idle compute, overprovisioning, and high baseline costs, especially when the clusters are always-on.

- Migrate lightweight SQL workloads and dashboards to Databricks SQL Serverless
- Enable serverless for high-concurrency, low-compute scenarios where persistent compute isn’t needed
- Set policies or guidelines to default to serverless for interactive workloads unless specific performance reasons require otherwise

**Inefficient Bi Queries Driving Excessive Compute Usage**
Service: Interactive Clusters | Type: Inefficient Query Patterns

Business Intelligence dashboards and ad-hoc analyst queries frequently drive Databricks compute usage  - especially when: * Dashboards are auto-refreshed too frequently * Queries scan full datasets instead of leveraging filtered views or materialized tables * Inefficient joins or large broadcast operations are used * Redundant or exploratory queries are triggered during interactive exploration This often results in clusters staying active for longer than necessary, or being autoscaled up to handle inefficient workloads, leading to unnecessary DBU consumption.

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

Interactive clusters are intended for development and ad-hoc analysis, remaining active until manually terminated. When used to run scheduled jobs or production workflows, they often stay idle between executions -leading to unnecessary infrastructure and DBU costs.

- Reassign scheduled jobs to ephemeral job clusters
- Apply workspace policies to enforce job cluster usage for scheduled workflows
- Educate users on the differences between cluster modes and their appropriate use cases

**Missing Auto Termination Policy For Databricks Clusters**
Service: Databricks Clusters | Type: Missing Safeguard

In many environments, users launch Databricks clusters for development or analysis and forget to shut them down after use. When no auto-termination policy is configured, these clusters remain active indefinitely, incurring unnecessary charges for both Databricks and cloud infrastructure usage.

- Enable auto-termination for all clusters that do not require persistent runtime
- Set cluster policies to require auto-termination configuration for new clusters
- Establish reasonable inactivity thresholds based on workload type (e.g., 30–60 minutes for interactive)

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

In non-production environments -such as development, testing, and experimentation -many teams default to on-demand nodes out of habit or caution. However, Databricks offers built-in support for using spot instances safely.

- Enable spot instance usage for non-production clusters where workloads are resilient to interruption
- Leverage Databricks’ native fallback-to-on-demand capabilities to preserve job continuity
- Establish workspace-level defaults or templates that promote spot usage in dev/test clusters

**Suboptimal Use Of On Demand Instances In Non Production Clusters**
Service: Databricks Clusters | Type: Suboptimal Pricing Model

In Databricks, on-demand instances provide reliable performance but come at a premium cost. For non-production workloads -such as development, testing, or exploratory analysis -high availability is often unnecessary.

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

---

## Other Optimization Patterns (2)

**Inefficient Use Of Job Clusters In Databricks Workflows**
Service: Databricks Workflows | Type: Suboptimal Cluster Configuration

When multiple tasks within a workflow are executed on separate job clusters  - despite having similar compute requirements  - organizations incur unnecessary overhead. Each cluster must initialize independently, adding latency and cost.

- Configure a shared job cluster to run multiple tasks within the same workflow when compute requirements are similar
- Leverage cluster reuse settings to reduce start-up overhead and improve efficiency
- Validate that consolidation does not impact workload performance or isolation requirements before implementing

**Lack Of Functional Cost Attribution In Databricks Workloads**
Service: Databricks | Type: Visibility Gap

Databricks cost optimization begins with visibility. Unlike traditional IaaS services, Databricks operates as an orchestration layer spanning compute, storage, and execution  - but its billing data often lacks granularity by workload, job, or team.

- Orchestration (DBUs): Analyze query/job-level execution and optimize workload design
- Compute: Review underlying VM types and cost models (e.g., Spot, RI, Savings Plans)
- Storage: Align S3/ADLS/GCS usage with lifecycle policies and avoid excessive churn

---

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io)  - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
