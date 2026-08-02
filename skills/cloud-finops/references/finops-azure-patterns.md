---
name: finops-azure-patterns
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Anomaly Management"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["SRE", "Platform Engineering"]
fcp_maturity_entry: "Crawl"
---

# Azure Optimization Pattern Catalogue

> The enumerated Azure inefficiency catalogue - per-service waste patterns with the
> signal to look for and the remediation. A lookup surface: retrieve it when hunting a
> specific pattern, not to answer a billing-mechanics question. For named waste
> patterns with runnable detection queries prefer `playbooks/azure-*.md`; for billing
> mechanics see `finops-azure.md`; for commitments see `finops-azure-commitments.md`.

---

## Azure Optimization Patterns

> 48 cloud inefficiency patterns covering compute, storage, databases, networking,
> and other Azure services. Use to diagnose waste, validate architecture, or build
> optimisation roadmaps. Source: PointFive Cloud Efficiency Hub.

### Compute Optimization Patterns (13)

**Underutilized Azure Reserved Instance Due To Workload Drift**
Service: Azure Reservations | Type: Commitment Misalignment

As workloads evolve, Azure Reserved Instances (RIs) may no longer align with actual usage - due to refactoring, region changes, autoscaling, or instance-type drift. When this happens, the committed usage goes unused, while new workloads run on non-covered SKUs, resulting in both underutilized reservations and full-price on-demand charges elsewhere.

- Evaluate whether any existing workloads could be migrated to match the reservation scope
- For new workloads, consider provisioning on RI-covered instance types when technically viable
- Where appropriate, exchange the reservation for a more relevant SKU (non-covered
  services); for savings-plan-covered services after 1 Feb 2027, trade in to a savings
  plan or refund within the cap instead

**Oversized Hosting Plan For Azure Functions**
Service: Azure Functions | Type: Inefficient Configuration

Teams often choose the Premium or App Service Plan for Azure Functions to avoid cold start delays or enable VNET connectivity, especially early in a project when performance concerns dominate. However, these decisions are rarely revisited even as usage patterns change.

- Move low-usage or non-critical Function Apps to the Consumption Plan
- Pilot plan downgrades in non-production or latency-tolerant environments
- Use cost modeling tools to estimate savings from switching to Consumption Plan

**Missing Scheduled Shutdown For Non Production Azure Virtual Machines**
Service: Azure Virtual Machines | Type: Inefficient Configuration

Non-production Azure VMs are frequently left running during off-hours despite being used only during business hours. When these instances remain active overnight or on weekends, they generate unnecessary compute spend.

- Enable Azure's built-in auto-shutdown setting for applicable non-prod VMs
- Alternatively, configure shutdown/start schedules using Azure Automation or Logic Apps
- Preserve state using managed disks, snapshots, or generalized images

**Orphaned And Overprovisioned Resources In AKS Clusters**
Service: Azure AKS | Type: Inefficient Configuration

Clusters often accumulate unused components when applications are terminated or environments are cloned. These include PVCs backed by Managed Disks, Services that still front Azure Load Balancers, and test namespaces that are no longer maintained.

- Delete unused PVCs to release backing Managed Disks
- Clean up Services that are no longer in use to avoid unnecessary load balancer charges
- Scale down underutilized node pools

**Orphaned Kubernetes Resources**
Service: Azure AKS | Type: Orphaned Resource

Kubernetes environments often accumulate unused resources over time as applications evolve. Common examples include Persistent Volume Claims (PVCs) backed by Azure Disks, Services that trigger load balancer provisioning, or stale ConfigMaps and Secrets.

- Before deletion, verify resources are truly orphaned
- Delete orphaned PVCs to release Azure Managed Disks
- Remove Services that no longer front active workloads to deallocate Load Balancers and public IPs

**Outdated Azure App Service Plan**
Service: Azure App Service | Type: Outdated Resource

Applications running on App Service V2 plans may incur higher operational costs and degraded performance compared to V3 plans. V2 uses older hardware generations that lack access to platform-level enhancements introduced in V3, including improved cold start times, faster scaling, and enhanced networking options.

- Evaluate workload compatibility with V3-based plans (e.g., Premium v3 or Isolated v2)
- Plan a phased migration of applications from V2 to V3 to improve performance and reduce cost per resource unit
- Update infrastructure-as-code templates and provisioning defaults to prefer V3-based plans

**Outdated Virtual Machine Version In Azure**
Service: Azure Virtual Machines | Type: Outdated Resource

Many organizations choose a VM SKU and version (e.g., `D4s_v3`) during the initial planning phase of a project, often based on availability, compatibility, or early cost estimates. Over time, Microsoft releases newer hardware generations (e.g., `D4s_v4`, `D4s_v5`) that offer equivalent or better performance at the same or reduced cost.

- Evaluate alternative VM versions (e.g., v4 or v5) within the same family to identify better cost/performance options
- Plan and schedule VM resizing during maintenance windows to avoid unplanned downtime
- Coordinate with application owners to validate compatibility and risk tolerance

**Underutilized Azure Virtual Machine**
Service: Azure Virtual Machines | Type: Overprovisioned Resource

Azure VMs are frequently provisioned with more vCPU and memory than needed, often based on template defaults or peak demand assumptions. When a VM operates well below its capacity for an extended period, it presents an opportunity to reduce costs through rightsizing.

- Analyze average CPU and memory utilization of running VMs to determine if they are underutilized
- Review whether application requirements justify the current VM size
- Evaluate if the workload would perform similarly on a lower SKU within the same VM series

**Inefficient Use Of Photon Engine In Azure Databricks**
Service: Databricks | Type: Suboptimal Configuration

Photon is optimized for SQL workloads, delivering significant speedups through vectorized execution and native C++ performance. However, Photon only accelerates workloads that use compatible operations and data patterns.

- Ensure that Photon is only enabled for workloads structured to benefit from vectorized execution
- Refactor SQL logic and data models to align with Photon-optimized patterns (e.g., filter pushdowns, supported UDFs)
- Use built-in tools such as query plans and job profiles to verify Photon execution

**Missing Shared Scope Configuration For Azure Reservations**
Service: Azure Reservations | Type: Suboptimal Configuration

When reservations are scoped only to a single subscription, any unused capacity cannot be applied to matching resources in other subscriptions within the same tenant. This leads to underutilization of the committed reservation and continued on-demand charges in other parts of the organization.

- Change reservation scope from *Single* to *Shared* in the Azure Portal or via API
- Reevaluate periodically to ensure the scope aligns with current organizational structure and usage distribution

**Suboptimal Architecture Selection For Azure Virtual Machines**
Service: Azure Virtual Machines | Type: Suboptimal Pricing Model

Azure provides VM families across three major CPU architectures, but default provisioning often leans toward Intel-based SKUs due to inertia or pre-configured templates. AMD and ARM alternatives offer substantial cost savings; ARM in particular can be 30-50% cheaper for general-purpose workloads.

- Assess workload compatibility with ARM or AMD architectures
- Propose migration to ARM-based SKUs for supported workloads to reduce compute costs
- Use AMD-based instances as an intermediate option when ARM compatibility is not feasible

**Idle Azure App Service Plan Without Deployed Applications**
Service: Azure App Service | Type: Unused Resource

App Service Plans continue to incur charges even when no applications are deployed. This can occur when applications are deleted, migrated, or retired, but the associated App Service Plan remains active.

- Decommission App Service Plans with no active applications unless a future use case is explicitly confirmed
- In cases with low utilization, consider consolidating multiple lightly used plans into a single plan to reduce spend
- Establish governance practices to routinely identify and remove orphaned plans after application lifecycle events

**Inactive And Stopped VM**
Service: Azure Virtual Machines | Type: Unused Resource

This inefficiency arises when a virtual machine is left in a stopped (deallocated) state for an extended period but continues to incur costs through attached storage and associated resources. These idle VMs are often remnants of retired workloads, temporary environments, or paused projects that were never fully cleaned up.

- Identify virtual machines that have remained in a stopped (deallocated) state for the entire lookback period
- Review whether any activity has occurred from the associated managed disks, network interfaces, or backup processes
- Evaluate whether the VM is part of a dev/test or legacy environment with no recent usage

### Storage Optimization Patterns (16)

**Archival Blob Container Storing Objects In Non Archival Tiers**
Service: Azure Blob Storage | Type: Inefficient Configuration

This inefficiency occurs when a blob container intended for long-term or infrequently accessed data continues to store objects in higher-cost tiers like Hot or Cool, instead of using the Archive tier. This often happens when containers are created without lifecycle policies or default tier settings.

- Identify blob containers with large volumes of data stored in the Hot or Cool tier
- Evaluate access patterns to confirm whether the data is rarely or never read
- Review whether the container's data retention requirements align with archival use cases

**High Transaction Cost Due To Misaligned Tier In Azure Blob Storage**
Service: Azure Blob Storage | Type: Inefficient Configuration

Azure Blob Storage tiers are designed to optimize cost based on access frequency. However, when frequently accessed data is stored in the Cool or Archive tiers - either due to misconfiguration, default settings, or cost-only optimization - transaction costs can spike.

- Move frequently accessed data to the Hot tier, either manually or via lifecycle management policies
- Evaluate default tiering settings on upload processes to prevent misplacement of active data
- Incorporate access pattern analysis into storage tier selection decisions

**High Transaction Cost Due To Misaligned Tier In Azure Files**
Service: Azure Files | Type: Inefficient Configuration

Azure Files Standard tier is cost-effective for low-traffic scenarios but imposes per-operation charges that grow rapidly with frequent access. In contrast, Premium tier provides consistent IOPS and throughput without additional transaction charges.

- Evaluate cost-performance tradeoffs between Standard and Premium tiers
- If justified, migrate data to a new Azure Files Premium account (required for tier change)
- Use performance metrics and transaction volume to guide future provisioning decisions

**Inactive Blobs In Storage Account**
Service: Azure Blob Storage | Type: Inefficient Configuration

Storage accounts can accumulate blob data that is no longer actively accessed - such as legacy logs, expired backups, outdated exports, or orphaned files. When these blobs remain in the Hot tier, they continue to incur the highest storage cost, even if they have not been read or modified for an extended period.

- Identify storage accounts with large amounts of data in the Hot tier
- Analyze blob-level access patterns using logs or metrics to confirm that data has not been read or written over a defined lookback period
- Determine whether the data is still relevant to any active workload, process, or compliance requirement

**SFTP Feature Enabled On Azure Storage Account Without Usage**
Service: Azure Storage Account | Type: Inefficient Configuration

Azure users may enable the SFTP feature on Storage Accounts during migration tests, integration scenarios, or experimentation. However, if left enabled after initial use, the feature continues to generate flat hourly charges - even when no SFTP traffic occurs.

- Disable the SFTP feature on any Storage Account where it is no longer needed
- Coordinate with owners to confirm that alternate access methods (e.g., HTTPS, SDK) are sufficient
- Consider including SFTP enablement in governance reviews to catch idle services before they accumulate charges

**Missing Performance Plus On Eligible Managed Disks**
Service: Azure Managed Disks | Type: Misconfiguration

For Premium SSD and Standard SSD disks 513 GiB or larger, Azure now offers the option to enable Performance Plus - unlocking higher IOPS and MBps at no extra cost. Many environments that previously required custom performance settings continue to pay for additional throughput unnecessarily.

- Enable Performance Plus on all eligible disks using Azure CLI, API, or portal
- Decommission paid performance tiers or custom throughput settings where Performance Plus provides equivalent capability
- Incorporate Performance Plus enablement into provisioning templates for large disks going forward

**Outdated And Expensive Premium SSD Disk**
Service: Azure Managed Disks | Type: Modernization

Workloads using legacy Premium SSD managed disks may be eligible for migration to Premium SSD v2, which delivers equivalent or improved performance characteristics at a lower cost. Premium SSD v2 decouples disk size from performance metrics like IOPS and throughput, enabling more granular cost optimization.

- Identify Premium SSD managed disks provisioned using the original Premium SSD offering (not v2)
- Review disk IOPS, throughput, and sizing requirements to ensure compatibility with Premium SSD v2 capabilities
- Analyze whether the current SKU size (e.g., P30, P40) exceeds actual capacity and performance needs

**Outdated And Expensive Standard SSD Disk**
Service: Azure Managed Disks | Type: Modernization

Standard SSD disks can often be replaced with Premium SSD v2 disks, offering enhanced IOPS, throughput, and durability at competitive or lower pricing. For workloads that require moderate to high performance but are currently constrained by Standard SSD capabilities, migrating to Premium SSD v2 improves both performance and cost efficiency without significant operational overhead.

- Identify Managed Disks using the Standard SSD offering that are eligible for migration to Premium SSD v2
- Review workload performance requirements to confirm suitability for Premium SSD v2 characteristics
- Verify regional availability of Premium SSD v2 before planning migration

**Excessive Retention Of Audit Logs**
Service: Azure Blob Storage | Type: Over-Retention of Data

Audit logs are often retained longer than necessary, especially in environments where the logging destination is not carefully selected. Projects that initially route SQL Audit Logs or other high-volume sources to LAW or Azure Storage may forget to revisit their retention strategy.

- Review retention policies for audit logs and align them with regulatory requirements
- Use Azure Storage lifecycle management to transition older logs to lower-cost tiers or delete them automatically
- Reference: Azure Storage Lifecycle Management documentation

**Overprovisioned Managed Disk For VM Limits**
Service: Azure Managed Disks | Type: Overprovisioned Resource

Each Azure VM size has a defined limit for total disk IOPS and throughput. When high-performance disks (e.g., Premium SSDs with high IOPS capacity) are attached to low-tier VMs, the disk's performance capabilities may exceed what the VM can consume.

- Resize disks to match the performance envelope of the associated VM
- Downgrade to lower disk tiers (e.g., Premium SSD -> Standard SSD) when full performance is not needed
- Establish guardrails to ensure disk and VM configurations are aligned during provisioning and resizing events

**Long Retained Azure Snapshot**
Service: Azure Snapshots | Type: Retained Unused Resource

Snapshots are often created for short-term protection before changes to a VM or disk, but many remain in the environment far beyond their intended lifespan. Over time, this leads to an accumulation of snapshots that are no longer associated with any active resource or retained for operational need. Since Azure does not enforce automatic expiration or lifecycle policies for snapshots, they can persist indefinitely and continue to incur monthly storage charges.

- Manually review long-retained snapshots with application or infrastructure owners
- Delete snapshots no longer needed for recovery, rollback, or compliance retention
- Adopt tagging standards to track purpose, owner, and expected retention period at time of snapshot creation

**Inactive And Detached Managed Disk**
Service: Azure Managed Disks | Type: Unused Resource

Managed Disks frequently remain detached after Azure virtual machines are deleted, reimaged, or reconfigured. Some may be intentionally retained for reattachment, backup, or migration purposes, but many persist unintentionally due to the lack of automated cleanup processes.

- Identify Managed Disks that are in an unattached state (not linked to any VM)
- Review metrics or activity logs to determine whether the disk has seen any read or write operations during the lookback period
- Check whether the disk is intentionally retained for recovery, migration, or reattachment

**Inactive Files In Storage Account**
Service: Azure Blob Storage | Type: Unused Resource

Files that show no read or write activity over an extended period often indicate redundant or abandoned data. Keeping inactive files in higher-cost storage classes unnecessarily increases monthly spend.

- Identify storage accounts or containers containing blobs with no reads or modifications over a defined lookback period
- Analyze blob access logs and object metadata to validate inactivity
- Review creation timestamps, tags, and business ownership metadata to assess ongoing relevance

**Inactive Tables In Storage Account**
Service: Azure Table Storage | Type: Unused Resource

Tables with no read or write activity often represent deprecated applications, obsolete telemetry, or abandoned development artifacts. Retaining inactive tables increases storage costs and operational complexity.

- Identify Azure Table Storage tables with no read or write operations over a defined lookback period
- Review table creation dates, metadata, and ownership tags to assess relevance and intended retention
- Check for compliance, legal hold, or audit requirements before initiating deletions or exports

**Managed Disk Attached To A Deallocated VM**
Service: Azure Managed Disks | Type: Unused Resource

This inefficiency occurs when a VM is deallocated but its attached managed disks are still active and incurring storage charges. While compute billing stops for deallocated VMs, the disks remain provisioned and billable.

- Identify managed disks attached to deallocated VMs during the defined lookback period
- Review disk activity to confirm no read/write operations occurred while the VM was deallocated
- Evaluate whether the disk is still needed for backup, migration, or future reactivation

**Managed Disk Attached To A Stopped VM**
Service: Azure Managed Disks | Type: Unused Resource

Disks attached to VMs that have been stopped for an extended period, particularly when showing no read or write activity, may indicate abandoned infrastructure or obsolete resources. Retaining these disks without validation leads to unnecessary monthly storage costs.

- Identify Managed Disks attached to virtual machines that have remained in a stopped state over a representative time window
- Analyze disk activity metrics to detect absence of read/write operations during the lookback period
- Review VM metadata, ownership tags, and decommissioning records to assess whether the disk is still required

### Databases Optimization Patterns (8)

**Business Critical Tier On Non Production SQL Instance**
Service: Azure SQL | Type: Inefficient Configuration

Non-production environments such as development, testing, or staging often do not require the high availability, failover capabilities, and premium storage performance offered by the Business Critical tier. Running these workloads on Business Critical unnecessarily inflates costs.

- Migrate non-production SQL instances from the Business Critical tier to a lower-cost alternative, such as General Purpose
- Use downtime windows or database copy strategies to minimize risk during tier transitions, depending on instance size and availability requirements
- Monitor performance after migration to ensure the workload remains stable and meets operational needs

**Unnecessary Use Of RA-GRS For Azure SQL Backup Storage**
Service: Azure SQL | Type: Inefficient Configuration

Azure SQL databases often use the default backup configuration, which stores backups in RA-GRS storage to ensure geo-redundancy. While suitable for high-availability production systems, this level of resilience may be unnecessary for development, testing, or lower-impact workloads.

- For non-critical or non-regulated workloads, change the backup redundancy setting to LRS (or ZRS where supported)
- Document any exceptions where RA-GRS must be retained for compliance
- Incorporate backup configuration reviews into provisioning and governance processes

**Infrequently Accessed Data Stored In Azure Cosmos DB**
Service: Azure Cosmos DB | Type: Inefficient Storage Tiering

Azure Cosmos DB is optimized for low-latency, globally distributed workloads - not long-term storage of infrequently accessed data. Yet in many environments, cold data such as logs, telemetry, or historical records is retained in Cosmos DB due to a lack of lifecycle management.

- Export infrequently accessed data to lower-cost storage services
- Use Blob Storage Cool for rarely accessed but readily retrievable data
- Use Blob Storage Archive for long-term retention with delayed retrieval

**Overprovisioned Azure Database For PostgreSQL Flexible Server**
Service: Azure Database for PostgreSQL Flexible Server | Type: Overprovisioned Resource

Azure Database for PostgreSQL Flexible Server often defaults to general-purpose D-series VMs, which may be oversized for many production or development workloads. PostgreSQL typically does not require sustained high CPU, making it well-suited to memory-optimized (E-series) or burstable (B-series) instances.

- Resize the PostgreSQL Flexible Server to a smaller or more suitable VM family based on actual workload behavior
- For low-CPU workloads, consider B-series (burstable) or E-series (memory-optimized) configurations
- Review usage patterns quarterly to ensure the selected SKU remains aligned with performance needs

**Overprovisioned Compute Tier In Azure SQL Database**
Service: Azure SQL | Type: Overprovisioned Resource

Azure SQL Database resources are frequently overprovisioned due to default configurations, conservative sizing, or legacy requirements that no longer apply. This inefficiency appears across all deployment models: Single Databases may be assigned more DTUs or vCores than the workload requires; Elastic Pools may be oversized for the actual demand of pooled databases; Managed Instances are often deployed with excess compute capacity that remains underutilized. Because billing is based on provisioned capacity, not actual consumption, organizations incur unnecessary costs when sizing is not aligned with workload behavior.

- Downsize the compute tier (DTUs or vCores) to better match observed usage
- For Elastic Pools, reduce the total eDTUs/vCores and consider consolidating lightly used databases
- For Managed Instances, assess whether the vCore allocation can be reduced or workloads refactored

**Overprovisioned Storage In Azure SQL Elastic Pools Or Managed Instances**
Service: Azure SQL | Type: Overprovisioned Resource

Azure SQL deployments often reserve more storage than needed, either due to default provisioning settings or anticipated future growth. Over time, if actual usage remains low, these oversized allocations generate unnecessary storage costs.

- Where supported, reduce provisioned storage to better align with actual usage
- For Managed Instances, safely execute `DBCC SHRINKFILE` or equivalent operations before resizing
- Incorporate storage reviews into regular database hygiene practices

**Overbilling Due To Tier Switches And Allocation Overlaps In DTU Model**
Service: Azure SQL | Type: Suboptimal Pricing Model

Workloads that frequently scale up and down within the same day - whether manually, via automation, or platform-managed - can encounter hidden cost amplification under the DTU model. When a database changes tiers (e.g., S7 -> S4), Azure treats each tiered segment as a separate allocation and applies full-hour rounding independently.

- Minimize same-day tier switches unless operationally justified
- Schedule up/down-scaling during off-peak windows to reduce risk of overlapping billing
- Move to the vCore or serverless pricing model for more transparent and granular cost control

**Idle Azure SQL Elastic Pool Without Databases**
Service: Azure SQL | Type: Unused Resource

An Azure SQL Elastic Pool continues to incur costs even if it contains no databases. This can occur when databases are deleted, migrated to single-instance configurations, or consolidated elsewhere - but the pool itself remains provisioned.

- Decommission any Elastic Pool with no active databases unless a valid business case exists for retaining it
- Review infrastructure-as-code templates and automation pipelines to ensure pool cleanup is included in deprovisioning workflows
- Establish periodic audits to catch and remove idle pools across subscriptions and teams

### Networking Optimization Patterns (5)

**Suboptimal Load Balancer Rule Configuration In Azure Standard Load Balancer**
Service: Azure Load Balancer | Type: Inefficient Configuration

As organizations migrate from the Basic to the Standard tier of Azure Load Balancer (driven by Microsoft's retirement of the Basic tier), they may unknowingly inherit cost structures they didn't previously face. Specifically, each load balancing rule - both inbound and outbound - can contribute to ongoing charges.

- Audit existing Standard Load Balancer rule sets to identify unused entries
- Remove unnecessary inbound and outbound rules, especially in non-production environments
- Avoid blanket rule creation in templated environments unless explicitly required

**Inactive Azure Load Balancer**
Service: Azure Load Balancer | Type: Unused Resource

In dynamic environments - especially during autoscaling, testing, or infrastructure changes - it's common for load balancers to remain provisioned after their backend resources have been decommissioned. When this happens, the load balancer continues to incur hourly charges despite serving no functional purpose.

- Delete Azure Load Balancers that have no backend pool members and no observed traffic
- Implement automation or tagging policies to detect and flag inactive networking resources
- Update infrastructure-as-code or deployment scripts to ensure load balancers are removed alongside their dependent compute resources

**Inactive Standard Load Balancer With Unused Frontend IPs**
Service: Azure Load Balancer | Type: Unused Resource

Standard Load Balancers are frequently provisioned for internal services, internet-facing applications, or testing environments. When a workload is decommissioned or moved, the load balancer may be left behind without any active backend pool or traffic - but continues to incur hourly charges for each frontend IP configuration. Because Azure does not automatically remove or alert on inactive load balancers, and because they may not show significant outbound traffic, these resources often persist unnoticed.

- Delete load balancers that have no active backend pool and are no longer needed
- Review associated resources (e.g., front-end IP configurations, probes, rules) to ensure they can be safely removed
- Establish tagging or documentation standards to track ownership and intended usage

**Inactive Web Application Firewall (WAF)**
Service: Azure WAF | Type: Unused Resource

Azure WAF configurations attached to Application Gateways can persist after their backend pool resources have been removed - often during environment reconfiguration or application decommissioning. In these cases, the WAF is no longer serving any functional purpose but continues to incur fixed hourly costs.

- Delete WAF configurations that are no longer routing traffic or protecting active applications
- Establish periodic audits to flag and review WAFs with empty backend pools
- Use automated checks to detect and alert on WAF deployments with no active use

**Unassigned Public IP Address**
Service: Azure Networking | Type: Unused Resource

In Azure, it's common for public IP addresses to be created as part of virtual machine or load balancer configurations. When those resources are deleted or reconfigured, the IP address may remain in the environment unassigned.

- Delete unassigned Standard SKU public IPs that are no longer needed
- If an unassigned IP is intended for future use, consider converting it to Basic (if compatible)
- Incorporate IP resource cleanup into deprovisioning workflows

### Other Optimization Patterns (6)

**Transactable vs Non-Transactable Confusion In Azure Marketplace**
Service: Azure Marketplace | Type: Commitment Misalignment

Azure Marketplace offers two types of listings: transactable and non-transactable. Only transactable purchases contribute toward a customer's MACC commitment. See the "MACC - commercial commitment alignment" section under Commitment discounts for full drawdown mechanics, including what counts and what does not.

- Prefer transactable listings in Azure Marketplace whenever MACC utilization is a priority
- Validate SKU eligibility against Microsoft's Procurement Playbook or MACC eligibility lists
- Standardize sourcing templates and procurement workflows to explicitly document whether the offer contributes to MACC
- Confirm that the purchase is transacted through the Azure portal under a subscription tied to the enrollment - credit card purchases on the Marketplace website do not count toward MACC even for eligible products

**Lifecycle Visibility Gaps Inflating Renewal Costs In Azure Marketplace**
Service: Azure Marketplace | Type: Contract Lifecycle Mismanagement

When Marketplace contracts or subscriptions expire or change without visibility, Azure may automatically continue billing at higher on-demand or list prices. These lapses often go unnoticed due to lack of proactive tracking, ownership, or renewal alerts, resulting in substantial cost increases.

- Assign clear ownership of Marketplace contracts across business, finance, or procurement teams
- Set calendar-based and system-based reminders for contract renewals and entitlement expiration
- Regularly reconcile Azure billing data with vendor-provided SLA or entitlement terms

**Inefficient Use Of Azure Pipelines**
Service: Azure DevOps | Type: Inefficient Configuration

Teams often overuse Microsoft-hosted agents by running redundant or low-value jobs, failing to configure pipelines efficiently, or neglecting to use self-hosted agents for steady workloads. These inefficiencies result in unnecessary cost and delivery friction, especially when pipelines create queues due to limited agent availability.

- Audit and streamline pipelines to remove redundant or unnecessary stages
- Use conditional logic to limit execution of non-critical pipelines
- Prioritize agent capacity for pipelines supporting core or production workloads

**Overly Frequent Querying In Azure Monitor Alerts**
Service: Azure Monitor | Type: Inefficient Configuration

While high-frequency alerting is sometimes justified for production SLAs, it's often overused across non-critical alerts or replicated blindly across environments. Projects with multiple environments (e.g., dev, QA, staging, prod) often duplicate alert rules without adjusting for business impact, which can lead to alert sprawl and inflated monitoring costs.

- Test changes gradually. Start with non-production environments and non-critical alerts
- Right-size alert frequency based on actual SLA requirements rather than worst-case assumptions
- Review and prune alert rules quarterly to keep monitoring overhead aligned with operational value

**Inefficient Private Link Routing To Azure Databricks**
Service: Azure Databricks | Type: Misconfiguration

In Azure Databricks environments that rely on Private Link for secure networking, it's common to route traffic through multi-tiered network architectures. This often includes multiple VNets, Private Link endpoints, or peered subscriptions between data sources (e.g., ADLS) and the Databricks compute plane.

- Simplify routing by colocating Databricks and storage in the same region and VNet when possible
- Eliminate redundant Private Link endpoints that add no security or compliance value
- Use direct peering or shared services models to reduce network traversal

**Suboptimal Table Plan Selection In Log Analytics**
Service: Azure Monitor | Type: Suboptimal Pricing Model

By default, all Log Analytics tables are created under the Analytics plan, which is optimized for high-performance querying and interactive analysis. However, not all telemetry requires real-time access or frequent querying. (Note: Auxiliary plan availability varies per table - see Log Analytics cost control section above for current eligibility.)

- Assign the Basic plan to tables that are retained for audit, archival, or compliance purposes
- Split high-volume ingestion sources into separate tables based on access needs
- Reconfigure ingestion routes to direct non-essential logs to lower-cost tables

**Source:** https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices



---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
