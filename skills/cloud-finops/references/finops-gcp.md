---
name: finops-gcp
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Usage Optimization", "Data Ingestion", "Reporting & Analytics"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "Procurement"]
fcp_maturity_entry: "Walk"
---

# FinOps on GCP

> GCP-specific guidance covering cost data foundations, commitment discounts, carbon
> footprint, and 26 inefficiency patterns for diagnosing waste. Covers BigQuery billing
> export, FOCUS, Committed Use Discounts (CUDs), Sustained Use Discounts (SUDs), Spot
> VMs, Cloud Carbon Footprint, and pattern-level guidance for Compute Engine, GKE,
> Cloud Run, Cloud Functions, GCS, BigQuery, Cloud SQL, Bigtable, Memorystore, Pub/Sub,
> Cloud Logging, Cloud NAT, and Cloud Load Balancing.

---

## GCP cost data foundation

### Cloud Billing reports and Cost Management console

GCP's native cost surface is the Cloud Billing console - reports, cost breakdowns,
budgets, and pricing tables - scoped to a Billing Account. For organisations with
multiple Billing Accounts, the Cloud Console aggregates across them but the data
contract sits at the Billing Account level.

**Set up before anything else:**
- [ ] Billing administrator IAM grants for the FinOps team
- [ ] Budgets with email + Pub/Sub alerts at 50% / 80% / 100% thresholds, per project
- [ ] BigQuery billing export enabled (see below) - this is the canonical analytics path
- [ ] Pricing data export to BigQuery for SKU price reconciliation
- [ ] AI Cost Summary Agent widget in Billing Overview (preview) for AI workload visibility

The Cloud Billing console is sufficient for ad-hoc visualisation and budget alerting.
For any serious FinOps analytics, the BigQuery billing export is the right primitive,
not the console.

### AI Cost Summary Agent - native AI spend visibility

As of May 2026, GCP launched the **AI Cost Summary Agent** in preview, providing
dedicated AI spend analysis across Gemini API and Vertex AI services through a
Billing Overview widget. This addresses the AI cost visibility gap that FinOps teams
face when managing AI workloads on GCP.

**Key capabilities:**
- Aggregated AI spend across Gemini API and Vertex AI services
- Native tooling for AI spend attribution without third-party tools
- Integrated into the Cloud Billing console for unified cost management

For detailed AI cost optimisation strategies, see `finops-vertexai.md` and
`finops-for-ai.md`.

### BigQuery billing export - the canonical GCP cost data path

GCP exposes three distinct exports to BigQuery, and they are not interchangeable:

| Export | What it contains | Use for |
|---|---|---|
| **Standard usage cost data** | Daily aggregated cost by service / SKU / project / label | Showback, budget tracking, executive reporting |
| **Detailed usage cost data** | Resource-level line items (per-resource cost), backfilled from when enabled | Allocation, attribution, anomaly investigation, FinOps deep dives |
| **Pricing data** | SKU price catalogue (list and discounted) | Validating CUD discounts, pricing-aware what-if analysis |

**Important nuances:**
- **Resource-level data is opt-in** and backfills only from the moment you enable it -
  not historically. Enable it on Day 1 of any new GCP engagement.
- **Detailed export schema differs from standard.** Queries built against `gcp_billing_export_v1_*` (standard)
  do not run unchanged against `gcp_billing_export_resource_v1_*` (detailed); both schemas
  evolve over time.
- **Credits appear as separate line items**, not as discounts on the parent line. CUD
  application, SUD application, and promotional credits each get their own rows -
  filter or aggregate carefully.

Source: https://cloud.google.com/billing/docs/how-to/export-data-bigquery

### FOCUS billing export

GCP supports a **FOCUS-conformant BigQuery export** for cross-cloud normalisation.
Configure it alongside (not instead of) the standard/detailed exports - the FOCUS
schema is optimised for multi-cloud joins, while the native exports retain GCP-
specific columns the FOCUS spec does not surface.

For multi-cloud customers normalising AWS / Azure / GCP cost in one warehouse, the
FOCUS export is the path that aligns with AWS Data Exports for FOCUS 1.2 and
Azure Cost Management's FOCUS 1.2 support. Note that GCP currently supports FOCUS 1.0
while AWS and Azure have moved to v1.2, with additional providers like Databricks,
Vercel, and Grafana Cloud also joining the FOCUS ecosystem.

Source: https://cloud.google.com/billing/docs/how-to/export-data-bigquery-focus

### Cloud Billing Pricing API

For pricing-aware analytics, use the **Cloud Billing Pricing API** to validate that
CUD-discounted rates match expectation, model what-if scenarios for re-architecture
proposals, and reconcile invoice line items. Pricing changes propagate to the API
within hours of the public price change.

Source: https://cloud.google.com/billing/docs/reference/pricing-api

---

## Commitment discounts on GCP

GCP offers a different commitment model from AWS or Azure. There are no Reserved
Instances. The four levers are **Committed Use Discounts (CUDs)**, **Sustained Use
Discounts (SUDs)**, **Spot VMs**, and **Flex CUDs** (a recent spend-based addition).
SUDs are automatic; CUDs and Flex CUDs are explicit commitments; Spot is a market
mechanism.

### Sustained Use Discounts (SUDs) - free, automatic, often missed

SUDs apply automatically to Compute Engine VMs that run a significant portion of
the month. **No commitment, no purchase, no enrolment.** GCP discounts the on-demand
rate retroactively based on monthly run-time per VM family per region.

- Up to ~20% discount for a VM running 100% of a calendar month (general-purpose
  families)
- Discount is calculated per-resource and applied automatically on the next invoice
- Visible in BigQuery billing export as a separate line item with credit type
  `SUSTAINED_USAGE_DISCOUNT`

**Practical implication:** SUDs reduce the apparent saving from a 1-year CUD purchase
because the SUD discount is already baked into the on-demand rate the CUD compares
against. When sizing a CUD, model against the SUD-effective rate, not the headline
on-demand rate, to avoid overstating CUD savings.

Source: https://cloud.google.com/compute/docs/sustained-use-discounts

### Committed Use Discounts (CUDs) - resource-based vs spend-based

GCP CUDs come in two distinct flavours that are easy to conflate:

| CUD type | Commits to | Discount depth | Flexibility | Term |
|---|---|---|---|---|
| **Resource-based CUD** | Specific vCPU + memory in a region | Up to 57% (3yr) | Low - locked to machine series and region | 1yr or 3yr |
| **Spend-based / Flexible CUD** | $/hr spend on Compute Engine | **Up to 28% (1yr) or 46% (3yr)** | High - any machine series in any region | 1yr or 3yr |

**Resource-based CUDs** are the deeper-discount path for predictable, stable
workloads on a known machine series (N2, E2, etc.). The trade-off is rigidity -
they do not transfer if you migrate to a different series or to GKE / Cloud Run.

**Spend-based CUDs (Flexible CUDs)** are the spend-based equivalent of AWS Compute
Savings Plans or Azure Compute Savings Plans. Shallower discount than resource-
based CUDs at the same term, but they apply across machine series and regions and
survive architectural changes.

The **architectural drift trap** (already in the patterns section below) is the
most common GCP commitment failure: organisations buy resource-based CUDs early,
then migrate workloads to GKE Autopilot or Cloud Run, leaving the CUDs underused.
Spend-based CUDs avoid this category of failure at the cost of ~11 percentage
points of discount depth on 3-year terms (46% vs 57%).

**Layering recommendation (analogous to AWS / Azure layering):**

```
Layer 1: Spot VMs (interruptible workloads)
  ↓ removes 60-91% of compute cost on the spike layer
Layer 2: Spend-based CUDs (broad baseline across machine series)
  ↓ covers the predictable floor; survives migration
Layer 3: Resource-based CUDs (only for high-conviction stable workloads)
  ↓ adds the extra ~30% discount delta but locks you in
Layer 4: SUDs (automatic - no action)
  ↓ baseline retroactive discount on remaining on-demand
Layer 5: On-Demand (variable / new workloads)
```

CUDs cover **Compute Engine, GKE (via the underlying nodes), Cloud SQL, Cloud Run
(spend-based only), and Memorystore** depending on the CUD type. They do **not**
cover Cloud Functions, BigQuery, GCS, or Pub/Sub - those services have their own
commitment models (BigQuery slot reservations, etc.).

**CUD Sharing - the single most-missed CUD setting.** By default, CUD discounts
apply only **within the project that purchased them**. To pool CUDs across an
organisation - the typical multi-team / multi-project scenario - you must
explicitly enable **CUD Sharing** at the **billing-account level**. Without it,
one project burns its CUDs to zero while sibling projects pay PAYG, and the
billing-account-level coverage looks healthy in aggregate while individual
project-level utilisation is poor. Day-1 audit on any GCP commitment engagement:
verify whether CUD Sharing is enabled. Source:
https://cloud.google.com/billing/docs/how-to/cud-analysis

Sources: https://cloud.google.com/compute/docs/instances/committed-use-discounts-overview, https://cloud.google.com/compute/docs/instances/signing-up-flexible-committed-use-discounts

### Compute SKU billing - vCPU and memory bill separately

GCP bills Compute Engine resources with the **vCPU and memory components on
separate SKUs**, unlike AWS where the EC2 instance is a single billable unit.
This is invisible in the console summary but explicit in BigQuery billing export -
a single VM produces multiple cost rows per day (one for vCPU, one for memory,
plus disk, network, licensing, sustained-use credits, etc.).

**Practical implications for cost analytics:**
- Aggregating "cost per VM" requires summing across SKUs, not reading a single
  line. Custom Power BI / BigQuery dashboards that treat one row = one resource
  will under-report.
- Right-sizing analysis must consider vCPU and memory independently - GCP's
  custom machine types let you tune the ratio, which AWS cannot match at the
  same granularity.
- CUDs apply to the vCPU and memory components separately; mixed coverage is
  possible (e.g. 100% vCPU CUD, 60% memory CUD) and shows as such in CUD
  utilisation reports.

Source: https://cloud.google.com/compute/all-pricing

### Spot VMs

Spot VMs (which superseded Preemptible VMs) offer **60-91% discount** off on-demand
pricing in exchange for:
- 30-second termination notice on preemption
- No SLA, no live migration

**No 24-hour maximum runtime.** Spot VMs can run indefinitely until preempted - the
24-hour cap was a property of the older Preemptible VM offering, not Spot. Long-
running batch jobs and training workloads with checkpointing are valid Spot
workloads.

Use for: batch jobs, ML training with checkpointing, CI/CD, fault-tolerant tiers.
Avoid for: stateful workloads, latency-sensitive APIs, anything that cannot tolerate
abrupt termination.

Source: https://cloud.google.com/compute/docs/instances/spot

### BigQuery commitments (separate from Compute CUDs)

BigQuery has its own pricing layers and **two distinct commitment levers**. Treat
them as independent from Compute CUDs - the resource-based vs spend-based CUD
framing from Compute does not map directly here.

#### PAYG pricing layers

| Layer | Pricing model | When it is the right default |
|---|---|---|
| **On-demand** | $/TiB scanned | Unpredictable or low-volume usage; compute-heavy queries that scan little data; no slot-waste penalty (you always pay list for what you scan) |
| **Standard edition** | $/slot-hour PAYG, ~33% cheaper than Enterprise, 1600-slot cap | Scan-heavy workloads that do not need Enterprise features; often the cheapest tier overall for queries that process a lot of data |
| **Enterprise edition** | $/slot-hour PAYG | Enterprise features required, or individual queries demand high slot counts beyond the 1600-slot Standard cap |
| **Enterprise Plus edition** | $/slot-hour PAYG, highest rate | Multi-region requirements, advanced governance, CMEK at scale |

**Autoscaler under the hood**: regardless of edition, the BigQuery Autoscaler is
implemented as a series of **60-second slot commitments stitched together**. This
is why the autoscaler bills a 60-second minimum per scale-up and why "scale to
zero" has a 1-minute floor. Useful mental model when an engineering team is
surprised that a sub-minute query left billed slots running for a full minute.

#### Two commitment levers

| Lever | Discount depth | How it applies | Trade-off |
|---|---|---|---|
| **Slot commitments** (capacity commits) | 20% (1yr) / 40% (3yr) on Enterprise | Always-on baseline; PAYG slots bill on top at the edition rate when usage exceeds the baseline | High lock-in; only pays off when workload can be binpacked into the baseline or the team accepts the performance penalty of stretching peak work across longer windows |
| **BigQuery spend-based CUDs** (introduced at Cloud Next 2025) | 10% (1yr) / 20% (3yr) | Applies **hourly** across all capacity SKUs (Standard, Enterprise, Enterprise Plus); no baseline-vs-overage split | Lower headline discount, but no architectural rework, no overage stack, and the discount survives an edition switch |

**The slot-commitment trap (the math that catches teams out).** A 500-slot
1-year commitment at 20% discount **can net out as a cost increase** when the
workload is spiky. If the workload averages 500 slots per hour but peaks at
1500 slots in short bursts, the committed 500 slots are paid in full whether
used or not, AND the peak overage is billed PAYG on top at the edition rate.
A 3-year commitment at 40% can net out as only ~5% savings, not the headline
40%. Commitments only pay off when the team can either flatten the workload
into the baseline or accept stretching peak work across longer windows. In
the example above, going all-in on the 500-slot baseline turns 1500-slot
6-minute bursts into 500-slot 18-minute runs - which may break a 9am
dashboard SLA.

**Slot waste factor**: define `waste_factor = billed_slots / utilised_slots`.
A reservation with a waste factor of 1.5 pays 50% more per useful slot than
its list rate. This is the right cost lens for capacity reservations, not
the slot-hour list price. A surprising number of "we have a BigQuery cost
problem" engagements are really waste-factor problems hidden behind a
reservation discount that looked fine on paper.

#### Progressive ladder for BigQuery commitments

The recommended order of operations, especially for clients earlier in
maturity (Crawl or early Walk):

1. **Query hygiene first**: partitioning, clustering, eliminate broad
   `SELECT *`, fix unpartitioned scans. Inefficient queries are a 10-100x
   cost amplifier; commitments lock in the inefficiency for 1-3 years.
2. **Right-size the edition**: many scan-heavy workloads belong on
   Standard, not Enterprise. The ~33% cost gap is structural, not a
   commitment discount, and is available without lock-in.
3. **Spend-based CUDs on top of PAYG**: cover the predictable baseline at
   10/20% without architectural rework or concurrency trade-offs. Applies
   across all capacity SKUs, so the discount does not strand if the team
   later switches editions.
4. **Slot commitments**: only when there is a genuinely stable, binpackable
   baseline AND the team has re-architected concurrency to fit it. Start
   small (50-100 slots) and expand based on observed waste factor.

Jumping straight to step 4 - the "I'll just commit to my observed average
usage" reflex - is the single most common BigQuery commitment failure.

**Frame for clients**: BigQuery commitments trade flexibility for
predictability, and often performance for predictability. The right
question is not "what discount can we get" but "what is the SLA the
business actually needs, and what is the cheapest pricing mix that meets
it without breaking that SLA".

Sources:
- https://cloud.google.com/bigquery/docs/reservations-intro
- https://cloud.google.com/bigquery/pricing#commitments

---

## Cloud Carbon Footprint

GCP publishes per-project, per-region, per-service carbon emissions data through the
**Cloud Carbon Footprint** product. Both **location-based** and **market-based**
emissions methodologies are supported.

| Methodology | What it measures | When to use |
|---|---|---|
| **Location-based** | Average emissions intensity of the regional grid where compute runs | Comparing physical regions; reporting under GHG Protocol Scope 2 location-based |
| **Market-based** | Emissions accounting for Google's renewable energy purchases (PPAs, RECs) | Reporting under GHG Protocol Scope 2 market-based; Google's net-zero claims |

**Both views are exposed in the console and via BigQuery export.** For
sustainability reporting that needs to align with corporate Scope 2 disclosures,
choose the methodology that matches your accounting framework - they will produce
materially different numbers, especially in regions where Google has heavy renewable
PPAs.

**Practical FinOps integration:**
- Region selection has a carbon-cost trade-off: cheaper regions are sometimes higher-
  carbon (Asian regions vs European). Surface this in the architecture review, not
  just at procurement.
- The BigQuery carbon export joins to billing data on `project_id` + `service` +
  `region`, enabling carbon-per-dollar analytics for greenops dashboards.

See `greenops-cloud-carbon.md` for cross-provider GreenOps guidance.

Sources: https://cloud.google.com/carbon-footprint, https://docs.cloud.google.com/carbon-footprint/docs/methodology

---

### Kubernetes cost attribution on GKE

GKE workloads need container-level cost attribution that native GCP billing data does
not provide (it stops at node-level). For the cross-cluster discipline (OpenCost,
Kubecost, rightsizing methodology, node-level autoscaling, idle node cost),
see `finops-kubernetes.md`. GKE-specific anchors:

- Label consistency between Kubernetes resources and GCP resources is the prerequisite
  for unified reporting through BigQuery billing export
- GKE Cost Allocation (native) emits per-namespace, per-pod, per-label costs to BigQuery
  when enabled - prefer this over third-party tools where the use case is GKE-only
- Industry benchmarks: as of March 2026, Cast AI's State of Kubernetes Resource
  Optimization report shows typical clusters running at 8% CPU and 20% memory
  utilisation (down from 10% / 23% in 2025)

Source: https://cast.ai/blog/2026-state-of-kubernetes-resource-optimization-cpu-at-8-memory-at-20-and-getting-worse/

---

## Inefficiency patterns catalogue

The remainder of this reference is a curated catalogue of 26 GCP inefficiency
patterns covering compute, storage, databases, networking, and operational
mechanics. Use these as a diagnostic checklist when building optimisation roadmaps.
Source: PointFive Cloud Efficiency Hub.

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
- For workloads where architecture is still evolving, prefer Flexible / spend-based CUDs (Compute Engine Flex CUDs) over Resource-based CUDs - they trade a few percentage points of discount depth for the freedom to move across machine families and regions without stranding commitments. Resource-based CUDs are the right fit only when the workload, family, and region are genuinely stable for the full term.

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
Service: GCP Cloud Memorystore | Type: Inactive Resource

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
Service: GCP BigQuery | Type: Suboptimal Configuration

If a table is not partitioned by a relevant column (typically a timestamp), every query scans the entire dataset, even if filtering by date. This leads to:

- High costs per query
- Long execution times
- Inefficient use of resources when querying recent or small subsets of data

This inefficiency is especially common in:

- Event or log data stored in raw, unpartitioned form
- Historical data migrations without schema optimisation
- Workloads developed without awareness of BigQuery's scanning model

- Enable time-based partitioning on large fact or event tables
- Retrofit existing tables with ingestion- or column-based partitioning
- Cluster tables by frequently filtered fields (e.g., customer ID) to reduce scan volume

**Inefficient Use Of Reservations In Bigquery**
Service: GCP BigQuery | Type: Underutilized Commitment

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
Service: GCP Marketplace | Type: Subscription Disruption Due to Billing Migration

Changing a Google Cloud billing account can unintentionally break existing Marketplace subscriptions. If entitlements are tied to the original billing account, the subscription may fail or become invalid, prompting teams to make urgent, direct purchases of the same services, often at higher list or on-demand rates.

- Secure fallback agreements with vendors prior to billing account changes to ensure service continuity
- Establish "true-up" clauses that allow emergency direct purchases to be retroactively priced at Marketplace rates
- Document and communicate subscription dependencies before initiating billing account migrations

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
