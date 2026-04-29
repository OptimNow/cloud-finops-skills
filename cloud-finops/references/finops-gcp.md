# FinOps on GCP

> GCP-specific optimization patterns covering compute, storage, databases, and networking. 26 inefficiency patterns for diagnosing waste and building optimization roadmaps.
> Source: PointFive Cloud Efficiency Hub.

---

## Compute Optimization Patterns (10)

**Idle Gke Autopilot Clusters With Always On System Overhead**
Service: GCP GKE | Type: Inactive Resource Consuming Baseline Costs

Even when no user workloads are active, GKE Autopilot clusters continue running system-managed pods that accrue compute and storage charges. These include control plane components and built-in agents for observability and networking.

- Delete unused Autopilot clusters in dev, test, or sandbox environments
- Replace infrequently used workloads with serverless alternatives like Cloud Run or Cloud Functions
- Implement automation to tear down unused clusters after inactivity thresholds

**Excessive Cold Starts In Gcp Cloud Functions**
Service: GCP Cloud Functions | Type: Inefficient Configuration

Cloud Functions scale to zero when idle. When invoked after inactivity, they undergo a "cold start," initializing runtime, loading dependencies, and establishing any required network connections (e.g., VPC connectors).

- Reduce function size by minimizing dependencies and optimizing startup code
- Use minimum instance settings to keep warm instances running during active periods
- Avoid using VPC connectors unless absolutely necessary  - consider Private Google Access instead

**Missing Scheduled Shutdown For Non Production Compute Engine Instances**
Service: GCP Compute Engine | Type: Inefficient Configuration

Development and test environments on Compute Engine are commonly provisioned and left running around the clock, even if only used during business hours. This results in wasteful spend on compute time that could be eliminated by scheduling shutdowns during idle periods.

- Use Cloud Scheduler and Cloud Functions to automate VM stop/start workflows
- Preserve instance configuration and state using persistent disks or custom images
- Align schedules to working hours and review regularly with workload owners

**Orphaned And Overprovisioned Resources In Gke Clusters**
Service: GCP GKE | Type: Inefficient Configuration

As environments scale, GKE clusters tend to accumulate artifacts from ephemeral workloads, dev environments, or incomplete job execution. PVCs can continue to retain Persistent Disks, Services may continue to expose public IPs and provision load balancers, and node pools are often oversized for steady-state demand.

- Delete PVCs with unmounted Persistent Disks
- Clean up Services with no backend to release IPs and load balancers
- Scale down overprovisioned node pools

**Orphaned Kubernetes Resources**
Service: GCP GKE | Type: Orphaned Resource

In GKE environments, it is common for unused Kubernetes resources to accumulate over time. Examples include Persistent Volume Claims (PVCs) that retain provisioned Persistent Disks, or Services of type LoadBalancer that continue to front GCP external load balancers even after the backing pods are gone.

- Remove PVCs to deprovision underlying Persistent Disks
- Delete unused Services to avoid charges for external Load Balancers and reserved IPs
- Clean up ConfigMaps and Secrets not in use

**Overprovisioned Memory In Cloud Run Services**
Service: GCP Cloud Run | Type: Overprovisioned Resource

Cloud Run allows users to allocate up to 8 GB of memory per container instance. If memory is overestimated  - often as a buffer or based on unvalidated assumptions  - customers pay for more than what the workload consumes during execution.

- Reduce memory allocation to match observed memory usage with a buffer for spikes
- Continuously monitor function-level memory metrics to right-size allocations over time
- Set up proactive alerts for services with memory allocation far exceeding usage

**Overprovisioned Node Pool In Gke Cluster**
Service: GCP GKE | Type: Overprovisioned Resource

Node pools provisioned with large or specialized VMs (e.g., high-memory, GPU-enabled, or compute-optimized) can be significantly overprovisioned relative to the actual pod requirements. If workloads consistently leave a large portion of resources unused (e.g., low CPU/memory request-to-capacity ratio), the organization incurs unnecessary compute spend.

- Resize nodes to align with observed workload requirements
- Enable or tune cluster autoscaler to manage node pool size dynamically
- Split heterogeneous workloads into separate node pools for right-sized resources

**Underutilized Gcp Vm Instance**
Service: GCP Compute Engine | Type: Overprovisioned Resource

GCP VM instances are often provisioned with more CPU or memory than needed, especially when using custom machine types or legacy templates. If an instance consistently consumes only a small portion of its allocated resources, it likely represents an opportunity to reduce costs through rightsizing.

- Analyze average CPU and memory utilization of running Compute Engine instance
- Determine whether actual usage justifies the current machine type or custom configuration
- Review whether the workload could be met using a smaller predefined or custom machine type

**Overprovisioned Memory Allocation In Cloud Run Services**
Service: GCP Cloud Run | Type: Overprovisioned Resource Allocation

In Cloud Run, each revision is deployed with a fixed memory allocation (e.g., 512MiB, 1GiB, 2GiB, etc.). These settings are often overestimated during initial development or copied from templates.

- Reconfigure services with right-sized memory allocations aligned to observed usage patterns
- Test progressively smaller memory configurations to find a stable baseline without introducing latency or OOM errors
- Implement monitoring for memory pressure or failures to validate new settings

**Underutilized Vm Commitments Due To Architectural Drift**
Service: GCP Compute Engine | Type: Underutilized Commitment

VM-based Committed Use Discounts in GCP offer cost savings for predictable workloads, but they are rigid: they apply only to specified VM types, quantities, and regions. When organizations evolve their architecture  - such as moving to GKE (Kubernetes), Cloud Run, or autoscaling  - usage patterns often shift away from the original commitments.

- Consolidate workloads onto committed VM types where feasible
- Avoid renewing commitments for workloads that are scaling down or migrating
- Use Resource-based CUDs when architectural flexibility is needed

---

## Storage Optimization Patterns (3)

**Missing Autoclass On Gcs Bucket**
Service: GCP GCS | Type: Inefficient Configuration

Buckets without Autoclass enabled can accumulate infrequently accessed data in more expensive storage classes, inflating monthly costs. Enabling Autoclass allows GCS to automatically move objects to lower-cost tiers based on observed access behavior, optimizing storage costs without manual lifecycle policy management.

- Identify GCS buckets where Autoclass is not enabled
- Review object access patterns to confirm a mix of frequently and infrequently accessed data
- Assess current storage class distribution to identify potential inefficiencies

**Over Retained Exported Object Versions In Gcs Versioning Buckets**
Service: GCP GCS | Type: Over-Retention of Data

When GCS object versioning is enabled, every overwrite or delete operation creates a new noncurrent version. Without a lifecycle rule to manage old versions, they persist indefinitely.

- Implement lifecycle policies to delete noncurrent versions after a defined period
- Transition noncurrent versions to colder storage classes (e.g., Archive) if needed for compliance
- Audit versioned buckets periodically to ensure alignment with data governance and cost goals

**Inactive Gcs Bucket**
Service: GCP GCS | Type: Unused Resource

GCS buckets often persist after applications are retired or data is no longer in active use. Without access activity, these buckets generate storage charges without providing ongoing value.

- Identify GCS buckets that have had no read or write activity over a representative lookback period
- Review object access logs and storage metrics to confirm inactivity
- Assess whether the bucket is tied to any active workload, automated workflow, or scheduled task

---

## Databases Optimization Patterns (8)

**Unnecessary Reset Of Long Term Storage Pricing In Bigquery**
Service: GCP BigQuery | Type: Behavioral Inefficiency

BigQuery incentivizes efficient data retention by cutting storage costs in half for tables or partitions that go 90 days without modification. However, many teams unintentionally forfeit this discount by performing broad or unnecessary updates to long-lived datasets  - for example, touching an entire table when only a few rows need to change.

- Limit write operations to the exact data that requires change  - avoid broad table rewrites
- Partition large datasets so updates are scoped to specific partitions, minimizing disruption to cold data
- For static reference tables, use append-only patterns or restructure workflows to avoid unnecessary modification

**Idle Cloud Memorystore Redis Instance**
Service: GCP Cloud Memorystore | Type: Inactive Resource

Cloud Memorystore instances that remain idle -i.e., not receiving read or write requests -continue to incur full costs based on provisioned size. In test environments, migration scenarios, or deprecated application components, Redis instances are often left running unintentionally.

- Decommission idle Redis instances no longer in use
- Consider scaling down instance size if usage is expected to remain minimal
- Use labels to track instance ownership and business purpose for easier future audits

**Inactive Memorystore Instance**
Service: Inefficiency Type | Type: Inactive Resource

Memorystore instances that are provisioned but unused  - whether due to deprecated services, orphaned environments, or development/testing phases ending  - continue to incur memory and infrastructure charges. Because usage-based metrics like client connections or cache hit ratios are not tied to billing, an idle instance costs the same as a heavily used one.

- Decommission inactive or obsolete Memorystore instances
- Consolidate fragmented caching layers across services or environments
- Use automated tagging and monitoring to flag long-idle instances

**Excessive Shard Count In Gcp Bigtable**
Service: GCP BigTable | Type: Inefficient Configuration

Bigtable automatically splits data into tablets (shards), which are distributed across provisioned nodes. However, poorly designed row key schemas or excessive shard counts (caused by high cardinality, hash-based keys, or timestamp-first designs) can result in performance bottlenecks or hot spotting.

- Redesign row keys to promote even tablet distribution (e.g., avoid monotonically increasing keys)
- Consolidate shards where appropriate to reduce overhead
- Use Bigtable’s Key Visualizer tool to identify and resolve hot spotting

**Unoptimized Billing Model For Bigquery Dataset Storage**
Service: GCP BigQuery | Type: Inefficient Configuration

Highly compressible datasets, such as those with repeated string fields, nested structures, or uniform rows, can benefit significantly from physical storage billing. Yet most datasets remain on logical storage by default, even when physical storage would reduce costs.

- Switch eligible datasets to physical storage billing when compression advantages are material
- There is no performance impact between the two billing models.
- Changing the billing model takes 24 hours before it’s reflected in the GCP billing SKUs.

**Excessive Data Scanned Due To Unpartitioned Tables In Bigquery**
Service: Inefficiency Type | Type: Suboptimal Configuration

If a table is not partitioned by a relevant column (typically a timestamp), every query scans the entire dataset, even if filtering by date. This leads to: * High costs per query * Long execution times * Inefficient use of resources when querying recent or small subsets of data This inefficiency is especially common in: * Event or log data stored in raw, unpartitioned form Historical data migrations without schema optimization * Workloads developed without awareness of BigQuery’s scanning model.

- Enable time-based partitioning on large fact or event tables
- Retrofit existing tables with ingestion- or column-based partitioning
- Cluster tables by frequently filtered fields (e.g., customer ID) to reduce scan volume

**Inefficient Use Of Reservations In Bigquery**
Service: Inefficiency Type | Type: Underutilized Commitment

Teams often adopt flat-rate pricing (slot reservations) to stabilize costs or optimize for heavy, recurring workloads. However, if query volumes drop  - due to seasonal cycles, architectural shifts (e.g., workload migration), or inaccurate forecasting  - those reserved slots may sit underused.

- Reduce reservation size if sustained usage is consistently lower than commitment
- Consolidate slot reservations across projects to improve pool utilization
- Switch low-concurrency or unpredictable workloads back to on-demand or flex slots

**Underutilized Cloud Sql Instance**
Service: GCP Cloud SQL | Type: Underutilized Resource

Cloud SQL instances are often over-provisioned or left running despite low utilization. Since billing is based on allocated vCPUs, memory, and storage  - not usage  - any misalignment between actual workload needs and provisioned capacity leads to unnecessary spend.

- Right-size vCPU and memory allocations based on actual performance needs
- Schedule automatic shutdown for non-production instances during off-hours
- Use Cloud SQL’s stop/start capability for intermittent workloads

---

## Networking Optimization Patterns (2)

**Idle Load Balancer**
Service: GCP Load Balancers | Type: Idle Resource

Provisioned load balancers continue to generate costs even when they are no longer serving meaningful traffic. This often occurs when applications are decommissioned, testing infrastructure is left behind, or backend services are removed without deleting the associated frontend configurations.

- Decommission load balancers that no longer serve traffic or lack associated backend services
- Release reserved IP addresses tied to unused load balancers
- Incorporate lifecycle tagging and auditing practices to flag test or temporary load balancers for removal

**Idle Cloud Nat Gateway Without Active Traffic**
Service: GCP Cloud NAT | Type: Idle Resource with Baseline Cost

Each Cloud NAT gateway provisioned in GCP incurs hourly charges for each external IP address attached, regardless of whether traffic is flowing through the gateway. In many environments, NAT configurations are created for temporary access (e.g., one-off updates, patching windows, or ephemeral resources) and are never cleaned up.

- Decommission unused Cloud NAT gateways with no associated traffic
- Release reserved external IP addresses if no longer needed
- Consolidate NAT configurations where feasible across shared VPCs or regions

---

## Other Optimization Patterns (3)

**Excessive Retention Of Logs In Cloud Logging**
Service: GCP Cloud Logging | Type: Excessive Retention of Non-Critical Data

By default, Cloud Logging retains logs for 30 days. However, many organizations increase retention to 90 days, 365 days, or longer  - even for non-critical logs such as debug-level messages, transient system logs, or audit logs in dev environments.

- Set log-specific retention policies aligned with usage and compliance requirements
- Reduce retention on verbose log types such as DEBUG, INFO, or system health logs
- Route non-essential logs to a lower-cost or exclusionary sink (e.g., exclude from ingestion)

**Overprovisioned Throughput In Pub Sub Lite**
Service: GCP Pub/Sub Lite | Type: Overprovisioned Resource Allocation

Pub/Sub Lite is a cost-effective alternative to standard Pub/Sub, but it requires explicitly provisioning throughput capacity. When publish or subscribe throughput is overestimated, customers continue to pay for unused capacity  - similar to idle virtual machines or overprovisioned IOPS.

- Reduce provisioned throughput to better match actual traffic levels
- Consider right-sizing both publish and subscribe throughput independently
- Archive or delete unused topics with retained throughput settings

**Billing Account Migration Creating Emergency List Price Purchases In Google Cloud Marketplace**
Service: Inefficiency Type | Type: Subscription Disruption Due to Billing Migration

Changing a Google Cloud billing account can unintentionally break existing Marketplace subscriptions. If entitlements are tied to the original billing account, the subscription may fail or become invalid, prompting teams to make urgent, direct purchases of the same services, often at higher list or on-demand rates.

- Secure fallback agreements with vendors prior to billing account changes to ensure service continuity
- Establish "true-up" clauses that allow emergency direct purchases to be retroactively priced at Marketplace rates
- Document and communicate subscription dependencies before initiating billing account migrations

---

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io)  - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
