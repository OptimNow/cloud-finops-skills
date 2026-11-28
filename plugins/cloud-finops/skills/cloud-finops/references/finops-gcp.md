---
name: finops-gcp
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Usage Optimization", "Data Ingestion", "Reporting & Analytics"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "Procurement"]
fcp_maturity_entry: "Walk"
business_coverage: ["gcp:bill:deep", "gcp:budget:deep", "gcp:commitments:deep", "gcp:carbon:partial", "gcp:data:partial"]
questions:
  - q: "How do we get our GCP billing data into BigQuery, and why is that the starting point?"
    section: "BigQuery billing export - the canonical GCP cost data path"
  - q: "Committed use discounts on GCP: resource-based or spend-based, and how much should we commit?"
    section: "Committed Use Discounts (CUDs) - resource-based vs spend-based"
  - q: "Are we getting the sustained use discount automatically, or are we missing it?"
    section: "Sustained Use Discounts (SUDs) - free, automatic, often missed"
  - q: "How do we split GKE cluster costs between teams?"
    section: "Kubernetes cost attribution on GKE"
  - q: "Where do we see our GCP carbon footprint?"
    section: "Cloud Carbon Footprint"
  - "How do we let project teams see their own GCP costs without access to the whole billing account?"
  - "Notre facture GCP est trop élevée : par où commencer, et quels engagements prendre ?"
---

# FinOps on GCP

> GCP-specific guidance covering cost data foundations, commitment discounts and carbon
> footprint: BigQuery billing export, FOCUS, Committed Use Discounts (CUDs), Sustained
> Use Discounts (SUDs), Spot VMs, BigQuery commitments, Cloud Carbon Footprint and GKE
> cost attribution. The per-service inefficiency patterns (Compute Engine, GKE, Cloud
> Run, Cloud Functions, GCS, BigQuery, Cloud SQL and others) are in
> `finops-gcp-patterns.md`.

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
- [ ] A spend cap budget on each project that runs Gemini API, Agent Platform or Cloud
      Run, as the hard stop beside the alert budgets (GA since 13 October 2026; it reads
      gross list price and pauses committed capacity too - see `finops-vertexai.md`,
      "Project-level spend caps for agent workloads")
- [ ] BigQuery billing export enabled (see below) - this is the canonical analytics path
- [ ] Pricing data export to BigQuery for SKU price reconciliation
- [ ] AI Cost Summary Agent widget in Billing Overview (preview) for AI workload visibility

**Project teams can see their own costs without a billing-account role (preview since
10 June 2026, read 26 November 2026).** Project Viewer, Editor and Owner include `billing.resourceCosts.get`,
so a team opens Reports and Anomalies for its own project, one project at a time
(budgets need Editor or Owner). Adding **Project Billing Costs Manager**
(`roles/billing.projectCostsManager`) on the billing account gives Reports and the FinOps
hub aggregated over the projects that person can already view, and nothing else in the
account; above 300 projects the aggregated view falls back to one project at a time. Use
it for engineering showback instead of Billing Account Viewer, which shows every project
([cost management for project owners](https://docs.cloud.google.com/billing/docs/how-to/project-owners/overview)).

### AI Cost Summary Agent - native AI spend visibility

The **AI Cost Summary Agent** has been in preview since 27 April 2026 (still preview
on 15 November 2026, per the
[Cloud Billing release notes](https://docs.cloud.google.com/billing/docs/release-notes)),
providing dedicated AI spend analysis across Gemini API and Vertex AI services through a
Billing Overview widget.

**Gemini Enterprise Pay-as-you-go edition - consumption alongside subscription.**
On 26 August 2026 Google announced a **Gemini Enterprise Pay-as-you-go** edition
alongside the per-seat editions (Business, Standard, Plus, Frontline). There is no
base subscription fee: you pay for the compute and tokens your teams consume at
standard model API rates, with no feature quota limits. At announcement it was
available to select customers on invoiced Cloud Billing accounts and "rolling out
broadly soon", so check eligibility before planning around it.

Seats waste money when they sit idle and consumption does when it is unbounded: start
new or variable agent workloads on pay-as-you-go behind a budget and a spend cap, and
move to seats once per-seat cost is consistently below the observed run-rate.

The same announcement brought *Gemini Enterprise Flexible Savings Plans* (10% for
1 year, 20% for 3 years on generative AI consumption; seat subscriptions draw one down
without earning the discount) and project-level monthly spend limits. Both are covered
in `finops-vertexai.md`. Sources:
https://cloud.google.com/blog/products/ai-machine-learning/flexible-billing-and-cost-controls-for-agents-on-google-cloud
(primary, 26 August 2026), https://docs.cloud.google.com/gemini/enterprise/docs/editions.

**Originating products filter and Gemini Enterprise preset report.** On 7 August 2026
Cloud Billing added an **"Originating products"** filter/group-by dimension in Billing
Reports, plus a preset report, **"Gemini Enterprise costs by SKU"** (release notes,
confirmed 15 November 2026). Use the group-by to segment AI-related consumption across
services; it is console-only (see `finops-vertexai.md`).

### BigQuery billing export - the canonical GCP cost data path

GCP exposes three distinct exports to BigQuery, and they are not interchangeable:

| Export | What it contains | Use for |
|---|---|---|
| **Standard usage cost data** | Daily aggregated cost by service / SKU / project / label | Showback, budget tracking, executive reporting |
| **Detailed usage cost data** | Resource-level line items (per-resource cost); history depends on dataset location (below) | Allocation, attribution, anomaly investigation, FinOps deep dives |
| **Pricing data** | SKU price catalogue (list and discounted) | Validating CUD discounts, pricing-aware what-if analysis |

**Important nuances:**
- **Resource-level data is opt-in, and history depends on the dataset location.** In a
  multi-region dataset (US or EU) the standard, detailed and FOCUS exports add data
  retroactively from the start of the previous month when first enabled (the initial
  backfill can take up to five days); in a single-region dataset nothing is backfilled.
  The pricing export is never backfilled, re-enabling an export does not repeat the
  backfill, a period with the FOCUS export switched off is never filled, and a
  dataset's location cannot be changed after creation. Enable every export on Day 1 of
  a new GCP engagement, in a multi-region dataset unless residency rules require a
  region ([set up Cloud Billing export](https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery-setup),
  read 11 November 2026).
- **Detailed export schema differs from standard.** Queries built against `gcp_billing_export_v1_*` (standard)
  do not run unchanged against `gcp_billing_export_resource_v1_*` (detailed); both schemas
  evolve over time.
- **Credits are not separate rows.** Each usage row carries a repeated `credits` field
  (`id`, `full_name`, `type`, `name`, `amount`), and Google's example queries treat the
  amounts as negative and add them to cost: net cost is
  `SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0))`. A query
  that reads only `cost` reports cost before CUDs, SUDs and promotions, and one that
  subtracts credits flips their sign. The exception is usage moved to the consumption
  model of spend-based CUDs (below): its `cost` is already at the discounted rate, with
  no CUD credit beside it. The credit types are `COMMITTED_USAGE_DISCOUNT`,
  `COMMITTED_USAGE_DISCOUNT_DOLLAR_BASE`, `SUSTAINED_USAGE_DISCOUNT`, `FREE_TIER`,
  `PROMOTION`, `DISCOUNT`, `RESELLER_MARGIN`, `SUBSCRIPTION_BENEFIT` and
  `FEE_UTILIZATION_OFFSET`. To reproduce a console view, the Billing Reports "Generate
  query" feature writes the equivalent BigQuery SQL.

Sources: https://cloud.google.com/billing/docs/how-to/export-data-bigquery,
https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery-tables/standard-usage,
https://docs.cloud.google.com/billing/docs/how-to/bq-examples

### Incentives page - tracking conditional contract credits

Custom Google Cloud contracts often carry **conditional incentives**: credits that are
only earned if a spend or usage milestone is hit inside a set window. The Cloud Billing
console has an **Incentives** page (Billing navigation menu; it replaced the Spend-based
Milestones tab of the Credits page on 4 September 2026, mechanics below confirmed
15 November 2026) that tracks them in one place: spend-based milestone credits, Incremental Workload
Credits (multi-milestone programmes tracking incremental spend), and Rapid Migration and
Modernization Program (RaMP) incentives. Each milestone shows its end date, spend target,
progress, reward, and a status of Active, Achieved, Upcoming or **Missed**.

What matters for FinOps:

- **A missed milestone is forfeited money, and often nobody owns watching it.**
  These terms are negotiated by procurement and then sit in a contract PDF. Put the
  milestone end dates in the same calendar as commitment expiries, and review the page
  monthly. It only appears for billing accounts whose contract includes such programmes.
- **The tracker lags by up to three days** and is not real time. Do not steer
  end-of-window spend decisions off it without allowing for the delay.
- **Credits arrive late.** They are typically applied within 45 days of achieving the
  milestone (for monthly milestones, within about 45 days of month-end), so the benefit
  lands in a later period than the spend that earned it. Forecasts and accruals should
  reflect that timing rather than netting the credit against the earning month.
- **In reports and the BigQuery export they appear as `PROMOTION` type credits**, the
  same type as other promotional credits. They act as a payment method applied to
  eligible costs, not as a rate discount, so unit-cost analysis on list or CUD-effective
  rates is unaffected by them.
- **RaMP incentives depend on workload tagging.** Outcome-based RaMP rewards are
  calculated from consumption mapped to the programme, so an untagged migrated workload
  earns nothing. This is a tagging-governance dependency with a direct cash value.
- **Do not pull spend forward just to hit a milestone** without comparing the credit
  against the cost of the extra consumption - the same discipline as not over-buying to
  reach an EDP or MACC tier.
- Access needs the `billing.credits.list` permission (Billing Account Viewer, User or
  Administrator).

Source: https://docs.cloud.google.com/billing/docs/how-to/incentives-program-tracker

### FOCUS billing export

GCP supports a **FOCUS-conformant BigQuery export** for cross-cloud normalisation.
Configure it alongside (not instead of) the standard/detailed exports - the FOCUS
schema is optimised for multi-cloud joins, while the native exports retain GCP-
specific columns the FOCUS spec does not surface.

GCP offers a dedicated FOCUS export to a
Google-provided immutable BigQuery dataset
(`gcp_billing_immutable_<BILLING_ACCOUNT_ID>_<Location>`), still in preview on
15 November 2026, with a conformance report covering FOCUS 1.0, 1.1 and 1.2; the earlier
SQL view over the standard export mapped to 1.0 only. Read the gaps table before
building on it: Tags is not provided as a standard column (labels arrive in the
provider columns `x_Labels`, `x_SystemLabels`, `x_ProjectLabels` and `x_Tags`), Charge
Category carries no "Purchase" or "Credit" value (credits are in `x_Credits`), and
Service Category, Resource Type, Charge Frequency and Invoice ID are among the columns
not provided. A cross-cloud query that groups on `Tags` or `ServiceCategory` returns
nothing for the GCP rows. Cross-provider normalisation (Tags shape, precision, column
drift, invoice timing) is covered in `finops-focus.md`.

Sources: https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery-focus-setup,
https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery-tables/focus-export
(both read 15 November 2026)

### Cloud Billing Pricing API

For pricing-aware analytics, use the **Cloud Billing Pricing API** to validate that
CUD-discounted rates match expectation, model what-if scenarios for re-architecture
proposals, and reconcile invoice line items.

Source: https://cloud.google.com/billing/docs/reference/pricing-api

---

## Commitment discounts on GCP

GCP offers a different commitment model from AWS or Azure. There are no Reserved
Instances. The four levers are **Committed Use Discounts (CUDs)**, **Sustained Use
Discounts (SUDs)**, **Spot VMs**, and **Flex CUDs** (a recent spend-based addition).
SUDs are automatic; CUDs and Flex CUDs are explicit commitments; Spot is a market
mechanism.

### Sustained Use Discounts (SUDs) - free, automatic, often missed

SUDs apply automatically to Compute Engine usage that runs more than a quarter of the
month. **No commitment, no purchase, no enrolment.** Usage is aggregated per resource,
machine family and region across the Cloud Billing account, not per VM.

- **Only some machine series earn one.** The maximum is 30% for N1 (predefined and
  custom), M1, M2, the f1-micro and g1-small shared-core types and GPUs attached to N1
  VMs, and 20% for N2, N2D and C2. A series not on Google's list earns nothing: E2 and
  the newer general-purpose and compute series (N4, C3, C4 and their variants) are not
  on it, and GPUs on accelerator-optimised machines are excluded by name. An estate
  that has moved from N1 to E2 or N4 has no SUD left to count on.
- **The discount is incremental, by quarter of the month.** Each further 25% of the
  month is billed at a lower rate, so the full 30% or 20% is reached only at 100% of
  the month, and a resource that runs half the month gets about a third of the maximum.
- **In the BigQuery export it is a credit, not a row:** an entry of type
  `SUSTAINED_USAGE_DISCOUNT` in the `credits` field of the usage row (see "Credits are
  not separate rows" above).
- **A resource takes one kind of discount at a time.** Usage covered by a commitment
  earns no SUD; only the overage above it can. The one exception is the sole-tenant
  node premium, which still earns a SUD when the node's vCPUs and memory are under a
  commitment.

**Practical implication:** on an eligible series, SUDs reduce the apparent saving from a
1-year CUD, because the usage the CUD would cover already earns the SUD. When sizing a
CUD, compare against the SUD-effective rate, not the headline on-demand rate; on an
ineligible series the on-demand rate is the right baseline.

Source: https://docs.cloud.google.com/compute/docs/sustained-use-discounts (read
15 November 2026)

### Committed Use Discounts (CUDs) - resource-based vs spend-based

GCP CUDs come in two distinct flavours that are easy to conflate:

| CUD type | Commits to | Discount depth | Flexibility | Term |
|---|---|---|---|---|
| **Resource-based CUD** | Specific vCPU + memory in a region | Up to 55% (3yr); up to 70% for memory-optimised series | Low - locked to machine series and region | 1yr or 3yr |
| **Spend-based / Compute flexible CUD** | $/hr spend across Compute Engine, GKE and Cloud Run, bought on the Cloud Billing account | **28% (1yr) and 46% (3yr)** on most general-purpose and compute series; 28% and 54% on C4N and M4N; M1 to M4 get **no 1-year discount** and 63% (3yr); 17% and 38% on H3 and H4D; GPUs 21% and 43% on G2, 16% and 42% on G4 | High - eligible machine series in any region | 1yr or 3yr |

Flexible rates vary by machine series (Google's table, read 15 November 2026): a 1-year
flexible commitment sized on an M1 to M4 fleet discounts nothing, and one sized on HPC
(H3, H4D) or G2 and G4 GPU usage at the general 28% or 46% overstates the saving.

**Block storage commitments** (GA 22 October 2026) are a resource-based category for
Hyperdisk Balanced and Hyperdisk Throughput **Exapool** capacity only: Persistent Disk,
Hyperdisk Storage Pools and standalone Hyperdisk are not eligible. They are bought for 1
or 3 years per project and region through the account team only (no console, gcloud or
REST, rates on request, no CUD recommendations), start the day after purchase, bill for
the full term whether or not the Exapool capacity is provisioned, and cannot be cancelled.
Sources: <https://docs.cloud.google.com/compute/docs/instances/signing-up-committed-use-discounts>
and, for the resource-based discount ceilings in the table,
<https://docs.cloud.google.com/compute/docs/instances/committed-use-discounts-overview>
(both updated 26 October 2026; the ceilings and the flexible rates were read again on
15 November 2026).

**Spend-based CUDs now bill as a discounted rate, not a credit.** Google is moving
spend-based CUDs (compute flexible, Cloud SQL, BigQuery, Spanner, Bigtable, AlloyDB,
Memorystore, Dataflow, Firestore and others) to a consumption model on a date shown per
account as a notification on the Billing Overview page. Three things change for
whoever reads the bill. The commitment is expressed in **discounted spend** (what you
pay), where the legacy model committed an on-demand amount, so the same hourly figure
covers more usage than before. Covered usage is billed at the discounted rate under a
`Consumption Model` such as "Compute Flexible CUD - 1 Year" and no longer at list price
with a CUD credit, so a query that measures CUD savings by summing
`COMMITTED_USAGE_DISCOUNT_DOLLAR_BASE` credits no longer finds them on migrated usage. And the
commitment fee appears as its own SKU, offset by a `FEE_UTILIZATION_OFFSET` credit to
the extent the commitment is used: what remains on the fee SKU is the cost of the
unused commitment. VMware Engine and NetApp Volumes CUDs stay on the credit model, and
resource-based CUDs are not concerned
([spend-based CUDs](https://docs.cloud.google.com/docs/cuds-multiprice), read
15 November 2026).

The live row-by-row commitment comparison
(<https://optimtoken.optimnow.io/guides/savings-plans-vs-reserved-instances> for the page,
<https://optimtoken.optimnow.io/guides/savings-plans-vs-reserved-instances/figures.json> for the data)
covers AWS and Azure only: its GCP committed-use figures are typed estimates, not read
from Google's price list, so check CUD rates on Google's own pricing pages. On the
cloud-finops MCP, `get_live_figures("savings-plans-vs-reserved-instances")` returns the same file, whose
`leftOut` field records the exclusion.

**Divestiture risk.** Resource-based CUDs move with their project to a new billing
account and stop applying in the old one; spend-based CUDs stay with the billing
account unless Cloud Billing Support moves them. See "Commitments in a separation" in
`finops-onboarding-workloads.md`.

**Sizing while optimisation is under way.** A CUD's monthly fee applies for the whole
term, so size the first commitment to a conservative estimate of the usage that will
remain after rightsizing, buy it without waiting for the optimisation to finish, and
commit the rest later (the keel rule in `finops-aws-commitments.md` applies unchanged).

**Resource-based CUDs** are the deeper-discount path for predictable, stable
workloads on a known machine series (N2, E2, etc.). The trade-off is rigidity -
they do not transfer if you migrate to a different series or to GKE / Cloud Run.

**Spend-based CUDs (Flexible CUDs)** are the spend-based equivalent of AWS Compute
Savings Plans or Azure Compute Savings Plans. Shallower discount than resource-
based CUDs at the same term, but they apply across machine series and regions and
survive architectural changes.

**Not the same instrument as a Flexible Savings Plan.** Spend-based CUDs cover Compute
Engine and the services listed below; **Gemini Enterprise Flexible Savings Plans (FSPs)**
are a separate spend-based commitment covering generative AI model consumption
(10% for 1 year, 20% for 3 years, announced 26 August 2026). The names are close enough
to be confused in a commitment review, and they do not cover each other's spend - token
consumption is not eligible for a Compute Engine CUD, and compute is not eligible for an
FSP. Mechanics and the eligibility boundary are in `finops-vertexai.md`.

The **architectural drift trap** (also a pattern in `finops-gcp-patterns.md`) is the
GCP commitment failure OptimNow sees most often: organisations buy resource-based
CUDs early, then migrate workloads to GKE Autopilot or Cloud Run, leaving the CUDs
underused. Spend-based CUDs avoid this category of failure at the cost of about 9
percentage points of discount depth on 3-year terms for most machine series (46% vs 55%).
On the memory-optimised M1 to M4 series the 3-year gap is 7 points (63% vs 70%), but a
1-year flexible commitment earns nothing there, so 1-year coverage of those series has
to be resource-based. M4N is not in that group: its flexible rates are those of C4N
(28% and 54%).

**Layering recommendation (analogous to AWS / Azure layering):**

```
Layer 1: Spot VMs (interruptible workloads)
  ↓ removes up to 91% of compute cost on the spike layer
Layer 2: Spend-based CUDs (broad baseline across machine series)
  ↓ covers the predictable floor; survives migration
Layer 3: Resource-based CUDs (only for high-conviction stable workloads)
  ↓ adds the extra ~30% discount delta but locks you in
Layer 4: SUDs (automatic - no action)
  ↓ baseline retroactive discount on remaining on-demand
Layer 5: On-Demand (variable / new workloads)
```

Resource-based CUDs exist for **Compute Engine only** (GKE Standard nodes are Compute
Engine VMs, so they are covered). One compute flexible CUD covers eligible spend on
**Compute Engine, GKE and Cloud Run**; the separate Cloud Run and GKE Autopilot
spend-based CUDs can no longer be purchased. Other services have their own spend-based
CUD, bought per service: Cloud SQL, Memorystore, Spanner, Bigtable, AlloyDB, BigQuery,
Dataflow and Firestore among them. Cloud Storage and Pub/Sub have none
([committed use discounts](https://docs.cloud.google.com/docs/cuds), read
15 November 2026).

**CUD Sharing - check it on every older billing account.** A resource-based CUD
applies either to the project that purchased it or, with **CUD Sharing** enabled on
the Cloud Billing account, to every project the account pays for. Billing accounts
created on or after 16 June 2026 have sharing enabled by default; an account created
before that date keeps whatever was configured, so check it; do not assume. Without
it, one project leaves part of its commitment unused while sibling projects pay
on-demand, and coverage looks healthy in aggregate while project-level utilisation is
poor. Day-1 audit on any GCP commitment engagement: verify whether CUD Sharing is
enabled, and which attribution applies (resource-based CUDs support proportional and
prioritised attribution; spend-based CUDs, which are bought at the billing account,
proportional only). Sources:
https://docs.cloud.google.com/compute/docs/instances/committed-use-discounts-overview,
https://docs.cloud.google.com/docs/cuds (read 15 November 2026)

**GPUs under a compute flexible CUD: G2 and G4 only.** A compute flexible commitment
covers GPUs only when they are used with the G2 and G4 machine series; GPUs on other
series need a resource-based hardware commitment. Flexible commitments neither require
nor support attached reservations, so they carry no capacity assurance: pair them with
a standalone reservation where G2 or G4 capacity must be guaranteed (read
15 November 2026).

Source: https://docs.cloud.google.com/compute/docs/instances/committed-use-discounts-overview

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

Spot VMs (which superseded Preemptible VMs) are priced at **up to 91% off** the
on-demand price (Google states the ceiling only; the discount varies by machine type
and region and moves over time) in exchange for:
- Preemption at any time. The shutdown period is best effort and up to 30 seconds. By
  default there is no notice before it; a **120-second preemption notice** can be set
  when the VM is created, which Google recommends for any workload that needs more than
  30 seconds to checkpoint or drain
- No SLA, no live migration

**No 24-hour maximum runtime.** Spot VMs can run indefinitely until preempted - the
24-hour cap was a property of the older Preemptible VM offering, not Spot. Long-
running batch jobs and training workloads with checkpointing are valid Spot
workloads.

Source: https://docs.cloud.google.com/compute/docs/instances/spot (read
15 November 2026)

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
Slots scale in multiples of 50, billed per second with that one-minute minimum.
**Fluid scaling**, an opt-in set per reservation, removes the minimum: scaled slots
are billed per second, still in 50-slot steps. It suits reservations that serve many
short, spiky queries, where the minimum is a large share of the autoscaling bill
([slots autoscaling](https://docs.cloud.google.com/bigquery/docs/slots-autoscaling-intro),
read 15 November 2026).

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
problem" engagements are waste-factor problems hidden behind a
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
4. **Slot commitments**: only when there is a stable, binpackable
   baseline AND the team has re-architected concurrency to fit it. Start
   small (50-100 slots) and expand based on observed waste factor.

Jumping straight to step 4 - the "I'll just commit to my observed average
usage" reflex - is a common BigQuery commitment failure.

#### Principal-based reservation assignments - native slot attribution

BigQuery reservation assignments support an optional **`principal` property**,
generally available since 11 November 2026 on the Enterprise and Enterprise Plus
editions, allowing queries to be routed to specific reservations
based on the calling user, service account, or third-party identity. This gives
FinOps teams a native mechanism to attribute BigQuery slot consumption to specific
principals/teams, directly addressing the shared-reservation attribution problem
raised in the slot-commitment section above.

Historically, slot consumption within a shared reservation could only be attributed
through labels or project separation - both imperfect. Labels depend on consistent
query-time tagging, and project separation forces organisational structure onto the
billing model. Principal-based assignments add a third, cleaner attribution mechanism:

- Route a given user, service account, or third-party identity to a specific
  reservation, so their slot consumption is isolated and measurable
- Enables **per-principal budget enforcement** within shared reservations, rather
  than only at the reservation or project boundary
- Improves allocation accuracy without relying solely on labels or project splits

**Practical FinOps use:** where a shared reservation previously masked which team
was driving the waste factor, principal-based assignments let you segment the
baseline per team/service account. Combine with the waste-factor lens above to
identify which principal is over-consuming committed slots, and to enforce
per-principal budget guardrails inside a single shared reservation. Two companions
since November 2026: **project caps** (GA, same editions) limit slots and concurrency
per project inside a reservation, the ceiling the shared pool lacked; and opt-in
**compute cost attribution** (Preview) charges billed editions compute directly to the
query projects that consume the administration project's reservation, which replaces
a label-based split of the reservation bill for chargeback. It does not empty the
administration project: unused baseline, unassigned commitments and unused autoscaler
slots stay there, as a residual to allocate by rule, and a query project on another
billing account is not attributed at all. It is set per administration project and
location and applies from the next billing day.

**Keeping the commitment as the ceiling (GA 23 November 2026).** Two options, set per
region with `ALTER PROJECT SET OPTIONS` or `ALTER ORGANIZATION SET OPTIONS`, decide
whether a query can leave its reservation for on-demand billing.
`reservation_override_mode` governs overrides of an assigned reservation: the default,
`DENY_OVERRIDE_TO_NONE`, lets a query move to another reservation but refuses an
explicit override to on-demand; `ALLOW_ANY_OVERRIDE` reopens that path; and
`DENY_ANY_OVERRIDE` holds every query on its assignment, which also protects the
attribution above. `disable_on_demand_billing`, set to true, makes any query without an
assigned reservation fail instead of billing per TiB: it closes the case of an
unassigned project running on-demand beside the commitment. It trades a surprise
charge for a failed query, so check that every project that runs queries in the region
has an assignment before setting it, and set it where the commitment is meant to be the
ceiling.

Sources: https://docs.cloud.google.com/bigquery/docs/reservations-assignments,
https://docs.cloud.google.com/bigquery/docs/reservations-monitoring and the
[BigQuery release notes](https://docs.cloud.google.com/bigquery/docs/release-notes)
(9 and 11 November 2026 entries, read 14 November 2026); for the two options, the
23 November 2026 entry, [default configuration](https://docs.cloud.google.com/bigquery/docs/default-configuration)
and the [options list](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language),
read 28 November 2026.

#### Cross-cloud queries - cache the remote reads

A BigQuery query over data left in Amazon S3 or Azure storage pays the other cloud's
egress on every read. Lakehouse **cross-cloud caching**, GA since 2 November 2026,
keeps the file blocks it fetched in the Google Cloud region where the query runs, so
repeat reads, by any query, are served locally. It is off by default: enable it on the
Lakehouse federated catalog or the BigQuery cross-cloud connection. Google adds no
charge for it and manages retention and eviction, so the saving depends on how often
the same blocks are re-read and how often the source files change. Two limits: the
cache is a copy at rest in the query region (check residency before enabling), and it
does not support customer-managed keys. Measure it per job in `objectStorageStats`
(`cacheBytesRead` against `objectStorageBytesRead`)
([cross-cloud data access](https://docs.cloud.google.com/lakehouse/docs/about-cross-cloud-data-access),
read 14 November 2026).

#### Daily token quotas for generative AI SQL functions - native spend guardrail

On 31 August 2026 BigQuery restored **daily token quotas** for its generative AI
functions (`AI.GENERATE_TEXT`, `AI.CLASSIFY` and the other Gemini-based inference
functions; embedding functions such as `AI.EMBED` are excluded). The quotas went GA
on 8 June 2026, were disabled a week later, and came back at the end of August.
They are the platform-level cap on GenAI spend from BigQuery workloads,
complementing budget alerts and anomaly detection.

- Four quota metrics, tracked globally across regions: input and output tokens per
  day, each at project level and per user. Cached tokens do not count.
- The defaults are very high, so the quota does nothing until you lower it: set a
  stricter override on the IAM & Admin > Quotas & System Limits page. That override
  is the actual cost control.
- Complements (does not replace) budget alerts and anomaly detection - it is the
  hard ceiling while budget alerts remain the softer, notification-based signal.

Sources: https://docs.cloud.google.com/bigquery/docs/control-genai-costs (primary),
https://docs.cloud.google.com/bigquery/docs/release-notes#August_31_2026 (release
note). See `finops-for-ai.md` for the broader proactive guardrail and token-budget
enforcement guidance; this is the GCP-native example of platform-level token
budget enforcement.

The discounts in this section were recomputed as ratios from the
[BigQuery pricing page](https://cloud.google.com/bigquery/pricing) on 15 November 2026
and are unchanged. When a slot commitment expires with no renewal plan, its
reservations remain and their baseline slots go on being billed until someone deletes
them ([commitments](https://docs.cloud.google.com/bigquery/docs/reservations-commitments)).

**Frame for clients**: BigQuery commitments trade flexibility for
predictability, and often performance for predictability. The right
question is not "what discount can we get" but "what is the SLA the
business needs, and what is the cheapest pricing mix that meets
it without breaking that SLA".

Sources:
- https://cloud.google.com/bigquery/docs/reservations-intro
- https://cloud.google.com/bigquery/pricing#commitments

### Negotiated commitments

A negotiated commitment (a Minimum Commitment under a Google Cloud Addendum, shown in
billing as the Negotiated savings credit), its Marketplace drawdown cap and the RaMP
migration credits are covered in `finops-cloud-contracts.md`.

---

## Cloud Carbon Footprint

GCP publishes per-project, per-region, per-service carbon emissions data through the
**Cloud Carbon Footprint** product. Both **location-based** and **market-based**
emissions methodologies are supported.

| Methodology | What it measures | When to use |
|---|---|---|
| **Location-based** | Average emissions intensity of the regional grid where compute runs | Comparing physical regions; reporting under GHG Protocol Scope 2 location-based |
| **Market-based** | Emissions accounting for Google's renewable energy purchases (PPAs, RECs) | Reporting under GHG Protocol Scope 2 market-based; Google's net-zero claims |

**Both views are exposed in the console and via BigQuery export.** Choose the one that
matches your Scope 2 accounting framework: the numbers differ materially where Google
has heavy renewable PPAs.

**Practical FinOps integration:**
- Region selection has a carbon-cost trade-off: cheaper regions are sometimes higher-
  carbon (Asian regions vs European).
- The BigQuery carbon export joins to billing data on `project_id` + `service` +
  `region`, enabling carbon-per-dollar analytics for greenops dashboards.

See `greenops-cloud-carbon.md` for cross-provider GreenOps guidance.

Sources: https://cloud.google.com/carbon-footprint, https://docs.cloud.google.com/carbon-footprint/docs/methodology

---

### Kubernetes cost attribution on GKE

GKE workloads need container-level cost attribution that native GCP billing data does
not provide (it stops at node-level). For the cross-cluster discipline, see
`finops-kubernetes.md`. GKE-specific anchors:

- Label consistency between Kubernetes resources and GCP resources is the prerequisite
  for unified reporting through BigQuery billing export
- GKE Cost Allocation (native) emits per-namespace, per-pod, per-label costs to BigQuery
  when enabled - prefer this over third-party tools where the use case is GKE-only

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
