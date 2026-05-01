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

The Cloud Billing console is sufficient for ad-hoc visualisation and budget alerting.
For any serious FinOps analytics, the BigQuery billing export is the right primitive,
not the console.

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
FOCUS export is the path that aligns with AWS Data Exports for FOCUS 1.2 (GA Nov 2025)
and Azure Cost Management's FOCUS 1.2 preview.

Source: https://cloud.google.com/billing/docs/how-to/export-data-bigquery-focus

### Cloud Billing Pricing API

For pricing-aware analytics, use the **Cloud Billing Pricing API** to validate that
CUD-discounted rates match expectation, model what-if scenarios for re-architecture
proposals, and reconcile invoice line items. Pricing changes propagate to the API
within hours of the public price change.

Source: https://cloud.google.com/billing/docs/reference/pricing-api

### Kubernetes cost attribution and monitoring

For GKE workloads, native GCP billing data provides node-level costs but lacks
container-level granularity. Modern Kubernetes cost monitoring tools bridge this gap:

**Open-source options:**
- **OpenCost** - CNCF sandbox project providing real-time Kubernetes cost allocation,
  integrates with GCP billing APIs for accurate node pricing
- **Kubernetes Resource Report** - lightweight cost visibility without external dependencies

**Commercial solutions:**
- **Kubecost** - detailed namespace/deployment/pod cost allocation with efficiency
  recommendations
- **CloudZero** - unified Kubernetes and cloud cost platform with anomaly detection
- **Finout** - real-time cost attribution with custom business metrics mapping

**Key attribution patterns for GKE:**
- Label consistency between Kubernetes resources and GCP resources for unified reporting
- Namespace-based cost allocation aligned with team/project boundaries
- Pod resource requests/limits accuracy - overprovisioning at pod level compounds at
  cluster scale
- Shared resource allocation (system pods, ingress controllers) using weighted
  distribution models

**Industry benchmarks for rightsizing opportunities:**
As of March 2026, Cast AI's State of Kubernetes Resource Optimization report shows
typical Kubernetes clusters running at only 8% CPU utilisation and 20% memory
utilisation - down from 10% CPU and 23% memory in 2025. For GPU-enabled node pools,
utilisation tracking is now critical as GPU waste compounds the cost impact. These
benchmarks provide a baseline for identifying overprovisioned GKE workloads.

Source: https://www.finout.io/blog/kubernetes-cost-management-tools, https://cast.ai/blog/2026-state-of-kubernetes-resource-optimization-cpu-at-8-memory-at-20-and-getting-worse/

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

### BigQuery commitment model (separate from CUDs)

BigQuery has its own commitment model unrelated to Compute CUDs:

- **On-demand pricing:** $/TiB scanned
- **Capacity-based pricing:** slot reservations (Standard, Enterprise, Enterprise Plus
  editions). Reserve slots for predictable workload; Autoscaler scales up beyond the
  baseline at usage rates.
- **Slot commitments:** 1-year or 3-year for additional discount on top of the
  edition rate.

**The BigQuery cost trap** (in the patterns catalogue): teams adopt slot reservations
to stabilise costs, then query volumes drop and slots sit underused. The reservation
discount is wasted. Separately, **inefficient query design** (unpartitioned tables,
broad SELECT *, missing clustering) is often a 10-100x cost amplifier - fix the
queries before sizing the reservation.

Source: https://cloud.google.com/bigquery/docs/reservations-intro

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
- Use Kubernetes cost monitoring tools (OpenCost, Kubecost) to track system overhead vs workload costs
- Monitor cluster utilisation against industry benchmarks (as of March 2026: 8% CPU, 20% memory) to identify overprovisioned clusters

**Excessive Cold Starts In Gcp Cloud Functions**
Service: GCP Cloud Functions | Type: Inefficient Configuration

Cloud Functions scale to zero when idle. When invoked after inactivity, they undergo