---
name: finops-aws-patterns-databases
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Rate Optimization", "Architecting & Workload Placement", "Anomaly Management"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["SRE", "Platform Engineering"]
fcp_maturity_entry: "Crawl"
---

# AWS Optimization Patterns: Databases

> The AWS pattern catalogue for RDS, Aurora, DynamoDB, ElastiCache, MemoryDB,
> OpenSearch and DMS, with the RDS cost management strategy and the database
> commitment discount decision tree (which also covers Redshift): the signal to
> look for and the remediation for each. A lookup surface, retrieved when hunting
> a specific pattern. For named patterns with runnable detection queries, prefer
> `playbooks/`. The other families are listed in `finops-aws-patterns.md`; billing
> mechanics are in `finops-aws-billing.md`, commitments in `finops-aws-commitments.md`.

> Source: the [Cloud Efficiency Hub](https://www.pointfive.co/efficiency-hub),
> an open, practitioner-governed library powered by PointFive, credited here as
> the Hub asks of anyone who reuses its content.

---

## RDS cost management strategy

Amazon RDS is a fully managed database service but its pricing model is complex enough
to generate unexpected cost surges. RDS instances are a subset of EC2 instance types
but carry a premium over equivalent EC2 instances, in the 40-70% range (indicative,
not a benchmark; verify against current pricing for the engine and size).
Understanding the cost structure and applying a structured optimisation approach
prevents RDS from becoming an outsized line item.

**Why RDS costs surge:**
- On-Demand instances combined with auto-scaling can rapidly inflate costs when
  demand spikes are not scaled back down
- Instance family mismatches mean you pay for resources you do not use
- Provisioned IOPS (io1/io2) storage is expensive and often deployed when gp3 would
  suffice
- Non-production environments (dev, test, QA) inherit production-grade configurations
  (Multi-AZ, oversized instances) without justification

**RDS optimisation framework (OptimNow engagement template, not an AWS document):**

The optimisation sequence matters. Follow this order:

1. **Visibility first** - tag all RDS instances, databases, snapshots, and parameter
   groups. Start with engineering tags (service, environment, owner) for immediate
   waste detection, then add finance tags (cost centre, business unit) for allocation.
   Set up a Cost and Usage Report filtered for RDS to enable Athena-based analysis

2. **Eliminate waste** - identify and remove idle databases (no connections for 7+
   days), orphaned snapshots, and stopped instances approaching the 7-day auto-restart
   limit. Use Trusted Advisor or third-party tools to surface idle resources. Require
   application owner approval before deletion. Take a final snapshot before deleting
   any instance

3. **Implement scheduling** - stop non-production RDS instances outside business
   hours using AWS Instance Scheduler or Systems Manager. This alone can save 60-70%
   on dev/test database costs. Note: start/stop is only possible for single-AZ
   configurations without read replicas - which is the standard setup for non-production
   environments

4. **Right-size instances** - monitor CPUUtilization, FreeableMemory, and ReadIOPS
   in CloudWatch over a 4-week window. If memory consumption is high but CPU stays
   below 40%, transition from general-purpose (m-family) to memory-optimised
   (r-family) instances. Also evaluate Graviton-based instances (e.g. db.r6g, db.r7g)
   which offer up to 35% better performance and up to 52% better cost-effectiveness
   for open-source database engines

5. **Right-size storage** - before committing to Provisioned IOPS (io1/io2), test
   General Purpose gp3. For the majority of workloads, gp3 delivers satisfactory
   latency and throughput at a significantly lower cost. Only workloads with strict
   low-latency, high-throughput SLA requirements justify the io1/io2 premium. Review
   provisioned storage volumes - instances with 2TB provisioned but only 150GB used
   represent direct waste

6. **Review Multi-AZ deployments** - Multi-AZ doubles the cost of database instances
   and storage. Challenge the need by asking: what are the actual RTO and RPO
   requirements? Multi-AZ is essential for production; it is rarely justified for dev,
   test, or QA environments

7. **Improve database performance** - better performance can reduce the required
   instance size:
   - Implement caching with ElastiCache (Redis) to reduce direct database reads
   - Use read replicas to offload heavy read workloads and reduce primary instance
     strain
   - Review indexing and query patterns for I/O efficiency
   - For Aurora, evaluate Aurora Auto Scaling for read replicas to handle unpredictable
     workloads

8. **Review backup and snapshot costs** - manual snapshots persist indefinitely and
   continue incurring charges even after the source database is deleted. Review and
   remove outdated snapshots periodically. Consider relying more on automated backups,
   which self-manage retention. Also review backup retention settings - excessive
   retention on automated backups accumulates cost quickly

9. **Apply Reserved Instances** - commit only after completing steps 1-8 (do not
   commit to waste). Avoid "RDS Paralysis" - waiting for perfect right-sizing before
   purchasing RIs. Open-source database engines (MySQL, MariaDB, PostgreSQL) and
   Aurora support RI size flexibility within an instance family, so the initial RI
   investment remains valid as you continue right-sizing. Start with current
   recommendations and expand coverage as right-sizing progresses

**RDS RI payback guidelines (indicative, verify current pricing):**
- 1-year No Upfront: ~34% discount, no capital outlay
- 1-year Partial Upfront: ~37% discount, payback ~6.5 months
- 3-year Partial Upfront: ~57% discount, payback ~10 months
- For most organisations, 1-year No Upfront is the lowest-risk starting point

**Aurora-specific considerations:**
- Aurora clusters default to Standard I/O configuration, which charges separately for
  I/O operations. For read/write-intensive workloads, evaluate Aurora I/O-Optimized
  which eliminates I/O charges at a higher storage rate
- Aurora clusters running MySQL 5.7 or PostgreSQL 11 that have not been upgraded
  will incur Extended Support surcharges automatically; the opt-out at creation
  (`EngineLifecycleSupport`) is in `finops-aws-billing.md`, "Extended Support version
  audits"
- Aurora Auto Scaling manages read replica count dynamically - use it to avoid
  over-provisioning read capacity

**Stakeholder alignment for RDS optimisation:**
Effective implementation requires collaboration across roles:
- FinOps practitioners bridge business, IT, and finance; drive evidence-based decisions
- Engineering executes right-sizing, scheduling, and architecture changes
- Finance provides budget constraints and forecasting; helps build the cost-per-unit
  model
- Product/business teams confirm which databases support which products and approve
  changes
- Procurement manages Reserved Instance purchasing strategy

---

## Database commitment discount decision tree

AWS now offers a **Database Savings Plan** alongside service-specific Reserved
Instances for managed databases. Database Savings Plans provide up to 35% discount
on serverless databases (Aurora Serverless v2, DynamoDB On-Demand, Neptune Serverless)
and up to 20% on provisioned database instances (RDS, Aurora, ElastiCache, MemoryDB,
OpenSearch). Compute Savings Plans still do not cover managed databases - those
workloads need either RIs or the Database Savings Plan, depending on the service.
Choosing the wrong instrument - or committing too early - is a common database
FinOps mistake.

Source: https://docs.aws.amazon.com/savingsplans/latest/userguide/plan-types.html

**Instrument availability by service:**

| Service | Reserved Instances | Database Savings Plan | Compute Savings Plans | Notes |
|---|---|---|---|---|
| RDS (MySQL, PostgreSQL, MariaDB) | Yes - size-flexible within family | Yes - up to 20% discount | No | RI size flexibility means right-sizing does not invalidate the commitment. Database SP adds spend-based flexibility across engines. |
| RDS (Oracle, SQL Server) | Yes - locked to instance type | Eligibility varies - verify per engine | No | No size flexibility for commercial engines; must match instance exactly |
| Aurora (MySQL, PostgreSQL) | Yes - size-flexible within family | Yes - up to 20% discount (provisioned), up to 35% (Serverless v2) | No | Same RI pool as RDS open-source engines |
| DynamoDB | Yes - Reserved Capacity | Yes - up to 35% discount (On-Demand mode) | No | Commit to read/write capacity units for Provisioned mode; Database SP covers On-Demand |
| ElastiCache (Redis, Memcached) | Yes - node-type specific | Yes - up to 20% discount | No | Locked to node type, no size flexibility |
| MemoryDB | Yes - node-type specific | Yes - up to 20% discount | No | Same mechanics as ElastiCache RIs |
| Neptune | Yes - instance-type specific | Yes - up to 35% discount (Serverless) | No | Low discount depth compared to RDS RIs |
| OpenSearch | Yes - instance-type specific | Yes - up to 20% discount | No | Also covers legacy Elasticsearch domains |
| Redshift | Yes - node-type specific (All Upfront / Partial Upfront / No Upfront for 1yr) | No | No | Redshift Serverless has its own Serverless Reservations: a committed RPU level for 1 or 3 years (up to 24% and 45% off), managed at payer-account level and shareable across accounts, with usage above the committed level at on-demand rates ([Redshift pricing](https://aws.amazon.com/redshift/pricing/), read 22 October 2026). As of July 2026, 1-year Redshift RIs support All Upfront and Partial Upfront payment options alongside No Upfront. |
| DocumentDB | Yes - instance-type specific | No | No | Same RI mechanics as RDS commercial engines |

**Verify Database Savings Plan eligibility per engine and instance class** at the
plan-types reference above before sizing - the Database SP scope is narrower than
"all managed databases" and the eligible-engine list evolves.

**Key insight:** Compute Savings Plans do NOT cover any managed database service.
Compute SPs apply to EC2, Fargate, and Lambda. SageMaker AI uses its own Savings Plan.
Managed databases use either RIs (per service) or the Database Savings Plan (where
eligible). If a database runs on EC2 (self-managed), Compute Savings Plans apply to
the EC2 instance - but the database layer itself has no Compute SP coverage.

**Decision tree:**

```
Is the database workload stable and predictable (90+ days of consistent usage)?
├── NO → Stay on On-Demand. Re-evaluate quarterly.
│         For DynamoDB: use On-Demand capacity mode.
│         For Redshift: evaluate Serverless for variable workloads.
│
└── YES → Has the workload been right-sized? (steps 1-8 of RDS framework above)
    ├── NO → Right-size first, commit second. Do not lock in waste.
    │         (A keel sized to the post-rightsizing floor can be bought now:
    │         see finops-aws-commitments.md, keel commitment.)
    │
    └── YES → What database service?
        │
        ├── RDS or Aurora (open-source engine: MySQL, PostgreSQL, MariaDB)
        │   → RDS Reserved Instances with size flexibility
        │     - Start with 1-year No Upfront (~34% discount, lowest commitment risk)
        │     - Upgrade to 1-year Partial Upfront (~37%) once confident
        │     - Consider 3-year Partial Upfront (~57%) only for workloads
        │       with 3+ year horizon AND no planned migration
        │     - Size flexibility means you can right-size within the
        │       instance family without losing the RI benefit
        │
        ├── RDS (commercial engine: Oracle, SQL Server)
        │   → RDS Reserved Instances (instance-type locked)
        │     - No size flexibility - must match exact instance type
        │     - Higher risk: right-size thoroughly before committing
        │     - Evaluate BYOL vs License Included cost difference
        │     - Consider migration to open-source engine to gain
        │       size flexibility and reduce licensing costs
        │
        ├── DynamoDB
        │   → First: switch from On-Demand to Provisioned + Auto Scaling
        │     if usage is predictable (indicative saving of 50-80%)
        │   → Then: Reserved Capacity for baseline read/write units
        │     - 1-year or 3-year terms available
        │     - Only commit the steady-state baseline; let Auto Scaling
        │       handle peaks above the reserved floor
        │
        ├── ElastiCache / MemoryDB
        │   → Reserved Nodes (node-type specific)
        │     - No size flexibility - must match exact node type
        │     - For MemoryDB: migrate to Valkey engine first (lower
        │       base cost), then evaluate RI on the new node type
        │
        ├── Redshift
        │   → Reserved Nodes for stable provisioned clusters
        │     - All three payment options (No Upfront, Partial Upfront,
        │       All Upfront) have long been available on RA3 and earlier
        │       node types. The June 2026 change added Partial and All
        │       Upfront to **RG instance** reservations specifically - it
        │       is not a general expansion of 1-year Redshift RI terms.
        │       All Upfront yields the deepest discount (~42% on 1-year),
        │       Partial ~41%, No Upfront ~20%.
        │       Source: https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-redshift-ri-upfront-pricing-rg-instances/
        │   → For variable workloads: Redshift Serverless (pay per
        │     RPU-hour) may be cheaper than committed idle capacity. Once
        │     its base RPU usage is steady, a Serverless Reservation
        │     (1 or 3 years, payer level) covers that floor; usage above
        │     it stays on-demand
        │
        └── Neptune / OpenSearch / DocumentDB
            → Reserved Instances (instance-type specific)
              - Evaluate usage carefully; these services often have
                bursty patterns that make commitment risky
              - Start with 1-year No Upfront if committing
```

**Self-managed databases on EC2 vs managed (RDS/Aurora):**

Running databases on EC2 instead of RDS trades management overhead for pricing
flexibility. The decision is rarely purely financial.

| Factor | Self-managed on EC2 | RDS / Aurora |
|---|---|---|
| Instance cost | EC2 On-Demand (cheaper base) | 40-70% premium over equivalent EC2 |
| Commitment options | Compute Savings Plans + EC2 RIs | RDS RIs + Database Savings Plan (eligible engines) |
| Maximum discount | Up to 72% (Standard RI) + EDP | Up to 57% (3yr Partial Upfront RI) + EDP |
| Operational cost | DBA time, patching, backups, HA setup | Managed by AWS |
| BYOL | Full control over licensing | Limited BYOL options (Oracle, SQL Server) |
| Flexibility | Any database engine, any version | AWS-supported engines and versions only |

**When self-managed makes financial sense:**
- Large-scale deployments where the 40-70% RDS premium exceeds the cost of a DBA team
- Commercial engines (Oracle, SQL Server) where BYOL on EC2 is significantly cheaper
  than RDS License Included pricing
- Workloads requiring database versions or configurations not supported by RDS
- Organisations with existing DBA capacity and mature operational practices

**When managed (RDS/Aurora) wins:**
- Teams without dedicated DBA capacity
- Workloads where high availability, automated backups, and patching are critical
- Aurora Serverless v2 for highly variable workloads (no EC2 equivalent)
- When the total cost of ownership (including operational burden) favours managed

**Layering strategy for database commitments:**

1. **EDP as base** - if eligible, the portfolio-wide EDP discount applies to both
   EC2 and RDS, reducing the effective rate before any RI is applied
2. **Right-size and optimise** - complete the 9-step RDS framework before committing
3. **Database Savings Plan for serverless** - if using Aurora Serverless v2, DynamoDB
   On-Demand, or Neptune Serverless, Database SP provides up to 35% discount with
   spend-based flexibility
4. **Reserve the steady-state floor** - commit RIs for provisioned baseline that will
   not change during the term. Leave headroom for scaling
5. **On-Demand for the variable layer** - peaks, new workloads, and workloads under
   evaluation stay on On-Demand until they stabilise
6. **Review quarterly** - commitment coverage should increase as workloads mature,
   not as a one-time purchasing event

**Diagnostic questions:**
- What percentage of your database spend is covered by Reserved Instances today?
- Are any RDS RIs sitting below 80% utilisation? (indicates over-commitment or
  workload changes)
- Do you have commercial-engine RDS instances that could migrate to open-source
  (which gives size flexibility and reduces licence costs)?
- Are DynamoDB tables on On-Demand mode despite having predictable, steady throughput?
- Is anyone running self-managed databases on EC2 without Compute Savings Plans
  covering those instances?
- Have you evaluated Aurora Serverless v2 for workloads with unpredictable traffic
  before committing to provisioned Aurora RIs?

**Capacity Reservations hold capacity; they do not discount it (since 21 October
2026).** Aurora and RDS DB instances can reserve capacity per Availability Zone, as EC2
can. A reservation bills at the On-Demand rate while active, whether or not a DB
instance runs in it, and capacity with no instance shows as unused reservation on the
bill. Reserved DB Instances and Database Savings Plans discount a DB instance that runs
in the reservation; the documentation does not extend them to unused reserved capacity,
so do not assume the EC2 behaviour, where a regional RI also covers an unused ODCR.
Three mechanics shape the review:

- Immediate reservations carry no commitment and can be cancelled at any time.
  Reservations scheduled 5 to 120 days ahead carry a 14-day minimum (12 weeks for the X
  family) and cannot be cancelled once scheduled.
- Reservations are targeted and stay in one account: a DB instance draws from one only
  when it names it, and capacity is not shared across accounts. An instance launched
  without the reservation's identifier runs beside it, and both bill.
- Multi-AZ RDS needs capacity in at least two Availability Zones; on Aurora the
  reservation is per DB instance, not per cluster. Aurora Serverless v2 and RDS Custom
  are out of scope.

List active reservations in the commitment review next to RIs and Savings Plans, and
give unused reserved capacity an owner. Sources:
https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/capacity-reservations.getting-started.html,
https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/capacity-reservations.pricing-billing.html

---

## Databases Optimization Patterns (31)

**Inefficient Use Of On Demand Capacity In Dynamodb**
Service: AWS DynamoDB | Type: Inefficient Configuration

While On-Demand mode is well-suited for unpredictable or bursty workloads, it is often cost-inefficient for applications with consistent throughput. In these cases, shifting to Provisioned mode with Auto Scaling allows teams to set a baseline level of capacity and scale incrementally as needed - often yielding substantial cost savings without compromising performance.

- Identify DynamoDB tables configured to use On-Demand capacity mode
- Review historical read/write activity for patterns of consistent or gradually increasing traffic
- Evaluate whether the workload exhibits steady throughput, such as regular API usage, background jobs, or scheduled data processing

**Outdated Elasticsearch Version Triggering Extended Support Charges**
Service: AWS ElasticSearch | Type: Inefficient Configuration

Many legacy workloads still run on older Elasticsearch versions - particularly 5.x, 6.x, or 7.x - due to inertia, compatibility constraints, or lack of ownership. Once these versions exceed their standard support window, AWS begins charging an hourly Extended Support fee for each domain.

- Upgrade to a supported version of OpenSearch
- Be aware that upgrading from Elasticsearch 7.x may require reindexing or application compatibility changes
- Where possible, consolidate or delete unused domains to eliminate unnecessary charges

**Outdated OpenSearch Or Elasticsearch Domain Incurring Extended Support Charges**
Service: AWS OpenSearch | Type: Outdated Resource

When an OpenSearch or Elasticsearch domain remains on a version past its standard support window, AWS applies an Extended Support surcharge to continue supplying security patches. This is a direct, quantifiable cost-forecasting item analogous to the EKS Extended Support pattern, and the surcharge rate is scheduled to increase materially. As of August 2026, AWS is extending Extended Support patch coverage for legacy Elasticsearch (1.5-7.8) and OpenSearch (1.0-1.2, 2.3-2.9) versions by 12 months to November 2027 - but from November 2026 the Extended Support surcharge rises to equal 100% of instance pricing (an effective 2x compute cost) for domains still on those old versions. AWS has also published Standard/Extended Support timelines for additional versions (ES 6.8/7.9/7.10, OpenSearch 1.3, 2.11-2.19), with support windows ranging 1-3 years. AWS revises these windows periodically, so verify current support dates before budgeting.

- Identify OpenSearch/Elasticsearch domains running versions past their standard support window (legacy ES 1.5-7.8, OpenSearch 1.0-1.2 and 2.3-2.9)
- Prioritise upgrades ahead of the November 2026 surcharge doubling to 100% of instance price, and note the November 2027 cutoff for continued Extended Support coverage
- Test upgrade compatibility in lower environments before applying in production, and decommission unused domains to eliminate unnecessary charges
<<REPLACE>>

**Outdated Opensearch Version Triggering Extended Support Charges**
Service: AWS OpenSearch | Type: Inefficient Configuration

Domains running outdated OpenSearch versions - particularly OpenSearch 1.x - begin to incur AWS Extended Support charges once they fall outside of the standard support period. These charges are persistent and apply even if the domain is inactive or lightly used.

- Upgrade OpenSearch domains to a supported version
- Test upgrade compatibility in lower environments before applying in production
- Decommission inactive domains to eliminate unnecessary support and compute charges

**Suboptimal Engine Selection In Memorydb**
Service: AWS MemoryDB | Type: Inefficient Configuration

MemoryDB now supports Valkey, a drop-in replacement for Redis OSS offering significant cost and performance advantages. However, many deployments still default to Redis OSS, incurring higher hourly costs and unnecessary data write charges.

- Migrate eligible MemoryDB clusters to use the Valkey engine
- Validate API compatibility and performance requirements prior to migration
- Use zero-downtime upgrade capabilities where possible for a transition without downtime

**Suboptimal Rds Instance Storage Type**
Service: AWS RDS | Type: Inefficient Configuration

This inefficiency occurs when an RDS instance uses a high-cost storage type such as io1 or io2 but does not require the performance benefits it provides. In many cases, provisioned IOPS are set at or below the free baseline included with gp3 (3,000 IOPS and 125 MB/s).

- Identify RDS instances using high-cost storage types (e.g., io1, io2)
- Review IOPS and throughput metrics to assess whether provisioned performance is being fully utilised
- Evaluate whether current workloads would meet SLAs with a general-purpose alternative like gp3

**Suboptimal Storage Type For Dynamodb Table**
Service: AWS DynamoDB | Type: Inefficient Configuration

This inefficiency occurs when a table remains in the default Standard storage class despite having minimal or infrequent access. In these cases, switching to Standard-IA can significantly reduce monthly storage costs, especially for archival tables, compliance data, or legacy systems that are still retained but rarely queried.

- Identify tables currently set to the Standard storage class
- Review read access patterns over the past 30+ days to confirm low usage
- Determine whether the table is used for active workloads or primarily exists for reference, compliance, or long-term retention

**Suboptimal Storage Configuration For Aurora Cluster**
Service: AWS Aurora | Type: Misconfiguration

Many Aurora clusters default to using the Standard configuration, which charges separately for I/O operations. For workloads with frequent read and write activity, this can lead to unnecessarily high costs.

- Identify Aurora clusters currently using the Standard storage configuration
- Review historical cost breakdowns to evaluate the portion of spend attributed to I/O charges
- Determine whether the workload exhibits high read/write activity or transactional behaviour

**Unnecessary Multi Az Configuration For Non Production Rds Instances**
Service: AWS RDS | Type: Misconfigured Redundancy

RDS Multi-AZ deployments are designed for production-grade fault tolerance. In non-production environments, this configuration doubles the cost of database instances and storage with little added value.

**Unnecessary Multi Az Deployment For Elasticache In Non Production Environments**
Service: AWS ElastiCache | Type: Misconfigured Redundancy

In non-production environments, enabling Multi-AZ Redis clusters introduces redundant replicas that may not deliver meaningful business value. These replicas are often kept in sync across Availability Zones, incurring both compute and inter-AZ data transfer costs.

- Reconfigure ElastiCache Redis clusters in non-production environments to use single-node, single-AZ deployments
- If persistence is not needed, consider using Memcached instead of Redis to further reduce costs
- Tag clusters appropriately to distinguish between environments and enforce automated guardrails

**Unnecessary Multi Az Deployment For Opensearch In Non Production Environments**
Service: AWS OpenSearch | Type: Misconfigured Redundancy

Non-production OpenSearch domains often inherit Multi-AZ configurations from production setups without clear justification. This leads to redundant replica shards across AZs, inflating both compute and storage costs.

- Reconfigure OpenSearch domains in non-production environments to use single-AZ deployments
- Reduce the number of replica shards where appropriate
- Implement automated tagging or policy enforcement to prevent accidental Multi-AZ usage in non-prod

**Outdated Rds Cluster Incurring Extended Support Charges**
Service: AWS RDS | Type: Modernization

When an RDS cluster is not upgraded in time, it can fall out of standard support and incur Extended Support charges. This often happens when upgrade cycles are delayed, blocked by compatibility issues, or deprioritised due to competing initiatives.

- Identify RDS clusters running database engine versions past their standard support window
- Confirm whether the cluster is currently accruing Extended Support charges
- Check whether a newer, recommended version is available and compatible with the application

**Inactive Dms Replication Instance**
Service: AWS DMS | Type: Orphaned Resource

Replication instances are commonly left running after migration tasks are completed, especially when DMS is used for one-time or project-based migrations. Without active replication tasks, these instances no longer serve any purpose but continue to incur hourly compute costs.

- Stop and delete DMS replication instances that are no longer associated with active or planned tasks
- Tag replication instances by project or migration wave to enable future clean-up
- Incorporate DMS instance lifecycle checks into post-migration workflows

**Outdated Aurora Versions Triggering Extended Support Charges**
Service: AWS Aurora | Type: Outdated Engine Version

Customers often delay upgrading Aurora clusters due to compatibility concerns or operational overhead. However, when older versions such as MySQL 5.7 or PostgreSQL 11 move into Extended Support, AWS applies automatic surcharges to ensure continued patching.

- Upgrade Aurora clusters to currently supported major versions to avoid Extended Support charges
- Test upgrades in lower environments to validate application compatibility before production cutovers
- Decommission unused or non-critical Aurora clusters rather than paying ongoing surcharges

**Outdated Rds Versions Triggering Extended Support Charges**
Service: AWS RDS | Type: Outdated Engine Version

Many organisations continue to run outdated database engines, such as MySQL 5.7 or PostgreSQL 11, beyond their support windows. Beginning in 2024, AWS automatically enrolls these into Extended Support to maintain security updates, adding incremental charges that scale with vCPU count.

- Upgrade RDS instances to currently supported major versions to avoid Extended Support fees
- Plan upgrades in non-production first to validate compatibility before applying in production
- Decommission unused or development databases that no longer provide value

**Underutilized Rds Commitment Due To Workload Drift**
Service: AWS RDS | Type: Overcommitted Reservation

RDS workloads often evolve - changing engine types, rightsizing instances, or shifting to Aurora or serverless models. When these changes occur after Reserved Instances have been purchased, the existing commitments may no longer match active usage.

- Evaluate whether current or new workloads can run on the reserved instance types
- Prioritise launching new RDS instances that align with the unused commitment
- Where feasible, upgrade or shift workloads to covered instance classes while monitoring performance and future fit

**Outdated Elasticache Node Type**
Service: AWS ElastiCache | Type: Overprovisioned Resource

Some ElastiCache clusters continue to run on older-generation node types that have since been replaced by newer, more cost-effective options. This can happen due to legacy templates, lack of version validation, or infrastructure that has not been reviewed in years.

- Identify ElastiCache nodes running on older-generation instance types (e.g., T2, M3, R3)
- Compare current node types to newer generation equivalents that offer the same size and better price/performance (e.g., M6g, R6g, T4g)
- Evaluate whether there are operational or application constraints that prevent an upgrade

**Oversized Rds Instance Storage**
Service: AWS RDS | Type: Overprovisioned Resource

This inefficiency occurs when an RDS instance is allocated significantly more storage than it consumes. For example, a 2TB volume might contain only 150GB of actual data.

- Identify RDS instances where provisioned storage significantly exceeds actual usage
- Review storage metrics to validate consistent underutilisation (e.g., <25% usage over time)
- Evaluate whether storage needs have declined due to archival, data aging, or workload changes

**Underutilized Elasticache Node**
Service: AWS ElastiCache | Type: Overprovisioned Resource

ElastiCache clusters are often sized for peak performance or reliability assumptions that no longer reflect current workload needs. When memory and CPU usage remain consistently low, the node is likely overprovisioned.

- Rightsize nodes to smaller instance types that align with observed usage
- Modernise to newer instance families when possible to improve price-performance
- Remove idle or redundant nodes in dev, staging, or non-HA environments

**Underutilized Rds Instance**
Service: AWS RDS | Type: Overprovisioned Resource

This inefficiency occurs when an RDS instance is consistently operating below its provisioned capacity - for example, showing low CPU, or memory utilisation over an extended period. This often results from conservative initial sizing, decreased workload demand, or failure to review and adjust after deployment.

- Identify RDS instances with consistently low CPU and memory usage over a representative time window
- Compare observed performance to the instance class's capabilities to assess overprovisioning
- Evaluate whether Auto Scaling is disabled or not configured for compute resizing

**Suboptimal Elasticache Engine Selection**
Service: AWS ElastiCache | Type: Suboptimal Configuration

Many workloads default to using Redis or Memcached without evaluating whether a lighter or more efficient engine would provide equivalent functionality at lower cost. Valkey is a Redis-compatible, open-source engine supported by ElastiCache that may offer improved price-performance and licensing benefits.

- For Redis-compatible but non-persistent workloads, consider migrating to Valkey
- If using Memcached, reevaluate whether Redis or Valkey offers better price-performance
- Note that engine migration typically requires cluster recreation and data migration - plan accordingly

**Non Graviton Elasticache Node On Eligible Workload**
Service: AWS ElastiCache | Type: Suboptimal Instance Family Selection

Many Redis and Memcached clusters still use legacy x86-based node types (e.g., cache.r5, cache.m5) even though Graviton-based alternatives are available. In-memory workloads are usually compatible with Graviton because they rely on standard CPU and memory operations. Unless constrained by architecture-specific extensions or strict compliance requirements, most ElastiCache clusters can be transitioned with no application-level changes.

- Switch node types to cache.r6g, cache.m6g, or cache.t4g equivalents
- Update provisioning logic to default to Graviton families for new clusters
- Pilot in non-prod or lower-tier environments to validate behaviour and latency

**Non Graviton Rds Instance On Eligible Workload**
Service: AWS RDS | Type: Suboptimal Instance Family Selection

Many RDS workloads continue to run on older x86 instance types (e.g., db.m5, db.r5) even though compatible Graviton-based options (e.g., db.m6g, db.r6g) are widely available. These newer families deliver improved performance per vCPU and lower hourly costs, yet are often not adopted due to legacy defaults, inertia, or lack of awareness. When workloads are not tightly bound to architecture-specific extensions (e.g., x86-specific binaries or drivers), switching to Graviton typically requires no application changes and results in immediate savings.

- Evaluate performance requirements and test Graviton-backed RDS instances in staging
- Modify instance class to a db.*g Graviton-based equivalent (e.g., db.r6g.large)
- Update infrastructure templates (e.g., Terraform, CloudFormation) to default to Graviton where applicable

**Inefficient Use Of Rds Reader Nodes**
Service: AWS RDS | Type: Suboptimal Workload Distribution

RDS reader nodes are intended to handle read-only workloads, allowing for traffic offloading from the primary (writer) node. However, in many environments, services are misconfigured or hardcoded to send all traffic - including reads - to the writer node.

- Refactor application logic or database client configurations to route read traffic to reader endpoints
- Introduce or enhance query routing layers (e.g., using database drivers with read/write splitting support)
- Remove reader nodes if there is no realistic path to utilising them efficiently

**Underutilized Read Capacity On A Dynamodb Table**
Service: AWS DynamoDB | Type: Underutilization

Provisioned capacity mode is appropriate for workloads with consistent or predictable throughput. However, when read capacity is significantly over-provisioned relative to actual usage, it results in wasted spend.

- Identify DynamoDB tables using Provisioned capacity mode
- Review utilisation history to assess average read throughput
- Determine whether actual read usage is consistently below the provisioned capacity

**Underutilized Write Capacity On A Dynamodb Table**
Service: AWS DynamoDB | Type: Underutilization

Provisioned capacity mode is appropriate for workloads with consistent or predictable throughput. However, when write capacity is significantly over-provisioned relative to actual usage, it results in wasted spend.

- Identify DynamoDB tables using Provisioned capacity mode
- Review utilisation history over a 14-day or longer period to assess average write throughput
- Determine whether actual write usage is consistently below the provisioned capacity

**Inactive Dynamodb Table**
Service: AWS DynamoDB | Type: Unused Resource

This inefficiency occurs when a DynamoDB table is no longer accessed by any active workload but continues to accumulate storage charges. These tables often remain after a project ends, a feature is retired, or data is migrated elsewhere.

- Identify tables with zero read or write activity over a defined lookback period (e.g. 7, 14, 30+ days)
- Confirm no dependencies exist from applications, analytics jobs, backup processes, or event streams
- Check metadata (tags, naming, creation date) to determine purpose and ownership

**Inactive Rds Cluster**
Service: AWS RDS | Type: Unused Resource

This inefficiency occurs when an RDS cluster remains provisioned but is no longer serving any workloads and has no active database connections. Unlike underutilised resources, these clusters are completely idle - showing no query activity, background processing, or usage over time.

- Identify RDS clusters with no active connections or query activity during the lookback period
- Confirm whether the cluster is receiving any traffic from applications or internal services
- Check for sustained low or zero CPU utilisation, network throughput, and read/write IOPS

**Inactive Rds Instance**
Service: AWS RDS | Type: Unused Resource

This inefficiency occurs when an RDS instance remains in the running state but is no longer actively serving application traffic. These instances may be remnants of retired applications, paused development environments, or workloads that were migrated elsewhere.

- Identify RDS instances that have been running continuously during the lookback period
- Review performance metrics to confirm low or zero CPU and memory usage
- Check connection logs and query metrics to validate the absence of active database traffic

**Inactive Rds Read Replica**
Service: AWS RDS | Type: Unused Resource

Read replicas are intended to improve performance for read-heavy workloads or support cross-region redundancy. However, it's common for replicas to remain in place even after their intended purpose has passed.

- Identify all existing RDS read replicas and their associated primary instances
- Assess whether read traffic is being actively routed to each replica
- Review recent query activity to determine if the replica is used for reporting, analytics, or scaling

**Long Retained Rds Manual Snapshot**
Service: AWS RDS | Type: Unused Resource

Manual snapshots are often created for operational tasks like upgrades, migrations, or point-in-time backups. Unlike automated backups, which are automatically deleted after a set retention period, manual snapshots remain in place until explicitly deleted.

- List all manual RDS snapshots across regions and accounts
- Identify snapshots that exceed a predefined age threshold (e.g., 30, 60, or 90 days)
- Check whether snapshots are tied to deleted or decommissioned database instances

Manual snapshots are not subject to the backup retention period and do not
expire (source: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_CreateSnapshot.html);
the detection query for untagged manual snapshots is in
[aws-snapshot-sprawl](../playbooks/aws-snapshot-sprawl.md).

**No Lifecycle Management For Temporarily Stopped Rds Instances**
Service: AWS RDS | Type: Unused Resource

While stopping an RDS instance reduces runtime cost, AWS enforces a 7-day limit on stopped state. After this period, the instance is automatically restarted and resumes incurring compute charges - even if the database is still not needed.

- Take a snapshot and delete the RDS instance to avoid all runtime charges
- Restore from snapshot only when the environment is needed again

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
