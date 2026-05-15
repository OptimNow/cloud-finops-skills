---
name: greenops-cloud-carbon
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Sustainability"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Usage Optimization"]
fcp_phases: ["Inform", "Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Sustainability", "Leadership", "Finance"]
fcp_maturity_entry: "Walk"
---

# GreenOps & Cloud Carbon Optimisation

> Practical guidance for measuring, reducing, and governing cloud carbon emissions.
> Covers carbon measurement tooling (native and open source), FinOps-to-GreenOps
> integration, workload shifting strategies (temporal and spatial), region selection,
> and reporting alignment with GHG Protocol and EU/SEC regulations.
>
> Distilled from: Forrester, Thoughtworks, Green Software Foundation, AWS Sustainability Console docs,
> CloudCarbonFootprint.org, North.Cloud, Climatiq, and Microsoft/UBS Carbon Aware SDK
> case study (2023–2025).

---

## Context and scale

Data centers consumed approximately 415 TWh globally in 2024 - roughly 1.5% of world
electricity. The IEA projects this could reach 945 TWh by 2030, driven primarily by AI
workloads and cloud scale. Tech sector emissions already rival the aviation industry.

**GreenOps is not a separate discipline.** It is FinOps with a carbon column added.
Every tagging, rightsizing, or idle resource cleanup action that reduces cost also
reduces emissions. The marginal effort to add carbon tracking to an existing FinOps
program is low.

---

## Measurement foundation

### Native cloud carbon tools

Each major provider offers a carbon footprint dashboard. Capabilities differ
significantly.

| Tool | Scope coverage | Granularity | Limitations |
|---|---|---|---|
| **AWS Sustainability Console** (renamed from CCFT, broken out of Billing 31 March 2026; Methodology v3 Oct 2025) | Scope 1, 2, 3 | Monthly, by service and region | Monthly only; "Others" service bucket; unused-capacity ventilation creates 5-15% month-to-month variance |
| **GCP Carbon Footprint** | Scope 1, 2, 3 | Region + service, location-based and market-based | Most granular of the three |
| **Azure Emissions Impact Dashboard** | Scope 1, 2, 3 | Service-level | Relies on market-based method (RECs); less granular than GCP |

**Important distinction:** Market-based measurement uses Renewable Energy Certificates
(RECs) and can mask actual grid carbon intensity. Location-based measurement uses the
real carbon intensity of the local grid. For optimisation decisions, prefer location-based
data. For ESG reporting, understand which method your auditors require.

**AWS Sustainability Console setup checklist:**
- [ ] Open the standalone Sustainability Console (broken out of Billing & Cost Management on 31 March 2026)
- [ ] Configure Data Exports to S3 (CSV or Parquet, automated monthly delivery) - same mechanism as Cost and Usage Reports
- [ ] Scope the export to the management (payer) account to cover all member accounts
- [ ] Use Methodology v3 (October 2025) - aligned to GHG Protocol, ISO 14064, ISO 14040/14044, ICT sector guide; externally verified
- [ ] Pair with Cost Explorer tags to correlate emissions to teams or products

### AWS Sustainability Console - what changed in 2026 and what to watch

The tool was renamed from "Customer Carbon Footprint Tool" (CCFT) to **AWS Sustainability Console**
on **31 March 2026** and broken out of the Billing & Cost Management console as a standalone
service.

**Console v2 features (March 2026):**
- Standalone console (no longer nested under Billing).
- Location-based and market-based emissions displayed side-by-side rather than toggled.
- Scope 1, 2, and 3 visible directly on the main view.
- Granularity: monthly. No daily or hourly breakdown.
- Filtering by service (EC2, S3, CloudFront - others bucketed as "Others") and by region.
- Multi-account support via the payer account; can select specific accounts.
- Time-period selection (rolling months or full year).

**Three data-extraction options:**
- Manual CSV export from the console.
- **Data Exports** - same mechanism as Cost and Usage Reports, automates delivery to an S3
  bucket. Use this for any production carbon dashboard.
- API and CLI access for programmatic integration.

**Methodology v3 (October 2025), ~43 pages, public, peer-reviewed.** Aligned to:
- **GHG Protocol Corporate Standard** for scope 1/2/3 framing.
- **ISO 14064** for organisational GHG accounting.
- **ISO 14040 / ISO 14044** for life-cycle assessment (used for scope 3 hardware embodied
  emissions).
- **Sector-specific GHG Protocol guide for ICT.**
- Third-party validated by an external assurance provider (verify the current verifier on the
  methodology document before quoting in client work).

This methodology alignment matters specifically for **CSRD reporting** in the EU - clients facing
CSRD audit requirements need the methodology to be ISO-aligned and externally verified, which v3
achieves.

**Common trap - the unused-capacity ventilation mechanic.** AWS does not measure individual
instance-level emissions precisely. The calculation works as follows:

1. Total data center emissions are measured (scope 1+2 for the facility, scope 3 for embodied
   hardware).
2. Customer allocations are computed from per-customer usage of metered services.
3. **Unused or unallocated capacity is ventilated proportionally across all customers based on
   usage share** - the unused racks were still built, powered, and cooled.

Consequence: **the same workload reports different carbon month-to-month even with no architectural
change**, because the unused-capacity ratio in the data center varies. Expect 5-15% month-to-month
variance and do not interpret it as workload drift. Flag this explicitly to clients before they
start chasing phantom anomalies.

### Critical reading of AWS sustainability claims

**The "100% renewable energy matched" claim is market-based, not physical.** AWS purchases enough
renewable energy globally - via PPAs, RECs in the US, Guarantees of Origin in Europe - to match
aggregate consumption. This does not mean any specific data center pulls renewable electrons from
its local grid. AWS regions in Ireland (~350 g CO2/kWh grid intensity) and Germany
(~300 g CO2/kWh) draw from gas-heavy grids regardless of the global renewable-matching claim. Use
**location-based** numbers for workload-placement decisions, not market-based.

**The Climate Pledge "net zero by 2040" headline covers scope 1+2 in most communications.**
Scope 3 emissions (supply chain, hardware manufacturing, customer use of products) are larger and
reduce more slowly. When a client's CSRD scope includes scope 3 disclosure, the AWS marketing
headline is not enough - request scope 3 detail explicitly.

**The "moving to AWS reduces emissions by 80%+" framing is vendor-funded analysis.** Studies cited
by AWS (451 Research, S&P Global) use methodology AWS commissions. Independent academic work
(Masanet et al., Berkeley) supports the directional claim - hyperscale is more efficient than
on-prem - but with smaller deltas, especially when on-prem is a modern facility. Treat the 80%
figure as a marketing ceiling, not a planning baseline.

### AWS-specific hardware and storage anchors

- **Graviton processors.** AWS publishes ~60% lower carbon at equivalent performance vs comparable
  x86 instances. Verify the current published figure on the AWS Graviton sustainability page
  before quoting (numbers change with new generations). Cheaper *and* meaningfully lower carbon -
  one of the rare unambiguous wins.
- **Parquet vs CSV storage.** ~90% size reduction with column compression. Generic to any
  column-oriented format, not AWS-specific, but worth flagging because it is one of the largest
  single-action data optimisations.
- **Spot instances as a scope 3 lever.** Cost benefit is well-known. The carbon benefit lands less
  often: Spot extends useful hardware life, amortising embodied emissions across more
  workload-hours. Make this explicit when presenting Spot to a sustainability-driven client.

### Open source: Cloud Carbon Footprint (CCF)

CCF is the most operationally useful multi-cloud carbon tool available today. It
estimates energy and carbon emissions at the service level using actual CPU utilization
rather than averages.

**What it does:**
- Covers AWS, Azure, and GCP in a single dashboard
- Estimates emissions by cloud provider, account, service, and time period
- Includes embodied emissions (hardware manufacturing)
- Generates rightsizing and idle resource recommendations with projected carbon savings
- Exports metrics as CSV for stakeholder reporting

**When to use CCF over native tools:**
- You need cross-cloud visibility in one place
- You need workload-level granularity for optimisation (not just reporting)
- You want location-based emission factors rather than market-based

Repository: https://www.cloudcarbonfootprint.org/

### Kepler (Kubernetes-level)

Kepler (Kubernetes-based Efficient Power Level Exporter) is a CNCF sandbox project
that measures per-container power consumption and exposes it as Prometheus metrics.
Combined with the Carbon Aware SDK (v1.4+), it enables per-pod carbon emission tracking
in Grafana dashboards.

**Use case:** Teams running containerized workloads who want carbon as a real-time
engineering metric, not a monthly report.

### Climatiq API

REST API that converts cloud resource usage (CPU hours, memory, storage, network) to
CO2e estimates across AWS, GCP, and Azure. Useful for embedding carbon metrics directly
into internal tooling, showback reports, or FinOps platforms.

→ https://www.climatiq.io/cloud-computing-carbon-emissions

---

## FinOps-to-GreenOps integration

### The core principle

GreenOps reuses FinOps infrastructure. The same tagging, showback, and governance
patterns that surface cost waste also surface carbon waste. The marginal effort to
layer carbon metrics onto a mature FinOps practice is surprisingly small - the
hardest infrastructure work has already been done. The practical starting point is
adding one column - gCO₂e - to existing cost reports.

**GreenOps maturity phases (mapped from FinOps):**

| FinOps phase | GreenOps equivalent | What it means operationally |
|---|---|---|
| Inform | Learn & Measure | Enable carbon dashboards; establish baseline per account, service, region |
| Optimize | Reduce | Rightsize, shut down idle resources, shift workloads to cleaner regions |
| Operate | Govern & Report | Set carbon KPIs per team; add gCO₂e to weekly engineering reviews |

### Practical integration checklist

- [ ] Add carbon data source (CCF or native tool) alongside cost data in your reporting stack
- [ ] Report gCO₂e per team/product unit alongside $ spend in weekly FinOps reviews
- [ ] Tag the top 20 resources by spend with carbon efficiency metadata
- [ ] Set carbon reduction targets alongside cost targets in team OKRs
- [ ] Include carbon impact in rightsizing and idle resource recommendations

### Key difference from pure FinOps

In FinOps, the lowest-cost option is always preferred. In GreenOps, a slightly higher-cost
option may be justified if it runs in a region with significantly lower carbon intensity
(e.g., a renewable-heavy region vs. a coal-heavy region at marginally higher compute cost).
This trade-off should be explicit, documented, and time-bounded.

---

## Region selection for carbon reduction

Region selection is the single highest-impact optimisation available. Research from
Microsoft's Carbon Aware SDK project shows that location-shifting can reduce carbon
emissions by up to 75% for a given workload.

### Low-carbon regions by provider (indicative)

| Provider | Lower-carbon regions | Higher-carbon regions |
|---|---|---|
| **AWS** | Paris (eu-west-3), Stockholm (eu-north-1) | Virginia (us-east-1), Dublin (eu-west-1), Frankfurt (eu-central-1) |
| **GCP** | Montreal, Toronto, Santiago (90%+ carbon-free energy) | Varies by grid mix |
| **Azure** | Nordics, Ireland, parts of Canada | Regions dependent on coal or gas grids |

**AWS region intensities - quantitative anchors (location-based):**

| AWS region | Approximate grid intensity | Grid mix |
|---|---|---|
| Paris (eu-west-3) | ~20-25 g CO2/kWh | Nuclear-heavy |
| Stockholm (eu-north-1) | ~20-25 g CO2/kWh | Hydro and nuclear |
| Frankfurt (eu-central-1) | ~300-350 g CO2/kWh | In transition, improving |
| Dublin (eu-west-1) | ~300-350 g CO2/kWh | Gas-heavy |
| Virginia (us-east-1) | ~350-400 g CO2/kWh | Gas + coal mix |

The intensity gap between Paris/Stockholm and US-East-1 is roughly **15x**. Use this number in
client conversations to make region selection concrete. Source via [Electricity
Maps](https://electricitymaps.com), not via vendor claims - vendor numbers reflect market-based
methodology, while Electricity Maps reflects physical grid reality.

**Recommendation:** Before selecting a region for a new workload, check the carbon intensity in
Electricity Maps, CCF's regional breakdown, or the Climatiq region comparison chart. Do not rely
solely on provider sustainability claims - use location-based data.

**Practical constraint:** Latency, data residency, and compliance requirements limit
region flexibility. Carbon region selection applies primarily to:
- Batch and asynchronous workloads with no user-facing latency requirement
- Dev/test and CI/CD environments
- Data processing pipelines and ML training jobs

---

## Workload shifting (carbon-aware computing)

### Two shifting strategies

**Temporal shifting (time-shifting):** Delay execution of flexible workloads to a time
window when the grid is running on cleaner energy (e.g., when solar generation is high).
Carbon reduction potential: ~15% for time-shifting alone.

**Spatial shifting (location-shifting):** Route workloads to a data center region where
current grid carbon intensity is lower. Carbon reduction potential: up to 50%+ when
combined with temporal shifting.

Most research before 2023 focused on one or the other. Current best practice combines
both.

### Green Software Foundation: Carbon Aware SDK

The Carbon Aware SDK is the primary open source implementation for carbon-aware workload
scheduling. It provides a standardized API and CLI for integrating grid carbon intensity
data into scheduling decisions.

**What it does:**
- Queries real-time and forecast carbon intensity from data providers (Electricity Maps,
  WattTime, UK National Grid ESO)
- Returns optimal execution windows for a given location and duration
- Integrates with Kubernetes, batch schedulers, cron jobs, and CI/CD pipelines
- Available as a Web API, CLI, and client libraries in 40+ languages
- Kepler integration enables per-application carbon tracking in Kubernetes (v1.4+)

**Workload types suitable for shifting:**
- ML model training (highest impact - long-running, compute-intensive, not time-critical)
- Batch data processing jobs
- CI/CD pipeline builds
- Database backups and maintenance windows
- Report generation

**Workloads not suitable for shifting:**
- User-facing, latency-sensitive applications
- Real-time data streaming
- Stateful workloads with strict SLA requirements

Repository: https://github.com/Green-Software-Foundation/carbon-aware-sdk

### Microsoft + UBS case study

Microsoft and UBS implemented time-shifting for Azure Batch jobs using the Carbon Aware
SDK. The 4-step methodology:

1. Measure carbon intensity of a past workload (historical baseline via SDK API)
2. Query the SDK for the optimal future execution window within an acceptable time range
3. Schedule the job at the optimal window
4. Measure actual carbon savings against the baseline

Initial implementation: observation only (logging optimal windows without acting on them),
followed by integration into the risk platform scheduler for non-time-sensitive jobs.

→ https://msftstories.thesourcemediaassets.com/sites/418/2023/01/carbon_aware_computing_whitepaper.pdf

### Carbon Aware SDK implementation checklist

- [ ] Identify batch or asynchronous workloads that have a flexible execution window
- [ ] Define the acceptable execution window (e.g., "run within the next 8 hours")
- [ ] Deploy the Carbon Aware SDK as a container or use the hosted API endpoint
- [ ] Query the `/emissions/forecasts/current` endpoint for optimal execution time
- [ ] Log actual vs. optimal carbon intensity to measure impact before automating
- [ ] Integrate with your scheduler (Kubernetes KEDA operator, cron, CI/CD trigger)
- [ ] Add Prometheus metrics export for carbon visibility in Grafana

---

## AWS Well-Architected Sustainability Pillar - the six areas

The pillar predates 2025 and its structure has been stable. Six best-practice areas (SUS01
through SUS06). Treat each concisely, with a critical-read note where the AWS framing is
overstated or under-operationalised.

### SUS01 - Region selection

AWS recommends choosing regions based on customer distance, business need, and grid carbon
intensity. The pillar treats region selection as a sustainability action.

**Critical read.** Region intensity matters for **location-based** reporting; for **market-based**
reporting AWS markets all regions as 100% renewable matched. The pillar does not call this
distinction out clearly - the consultant needs to know which reporting mode the client uses
before recommending a region migration as a sustainability action.

### SUS02 - Alignment to demand

Match infrastructure capacity to actual demand. Right-size, scale dynamically, decommission idle
resources.

**Critical read.** This is the FinOps right-sizing playbook reframed in carbon language. The
audit, the queries, the recommendations are the same. Do not run two separate workstreams; run
one and present results in both lenses.

### SUS03 - Software architecture patterns

Optimise software for hardware (use efficient libraries, avoid bloat), remove unused features,
refactor for parallelism, choose efficient programming languages.

**Critical read.** Most aspirational area. Hardest to operationalise on a 6-week or 6-month
engagement. "Switch programming language" is not an engagement deliverable. Treat as a long-cycle
architectural recommendation surfaced for the client's roadmap, not a quick win. The library-size
and unused-feature-removal advice is more actionable but rarely material at scale.

### SUS04 - Data patterns

Storage tier selection, lifecycle automation, deduplication, compression, format choice (Parquet
over CSV), retention pruning aligned to actual need.

**Critical read.** Almost complete overlap with FinOps storage optimisation. Same actions, same
audit. The carbon-specific framing is "embodied emissions of the underlying disk," but the
practical actions match cost optimisation precisely.

### SUS05 - Hardware patterns

Use efficient processor families (Graviton on AWS, equivalents elsewhere), upgrade to current
generations, use Spot to extend hardware lifetime, choose specialised accelerators only when
needed.

**Critical read.** This is the area where the carbon argument is strongest and sometimes lands
harder than the cost argument alone. Graviton is cheaper *and* meaningfully lower carbon. Spot
extends hardware lifetime - a real scope 3 lever, not just a cost lever. Recommend Hardware
Patterns first when a client is genuinely sustainability-driven.

### SUS06 - Development and deployment process

CI/CD efficiency, build cadence, sustainability metrics in dashboards, culture and people.

**Critical read.** Real but lightweight. Nightly-build emissions are rarely material at customer
scale. The cultural and metrics points are sound but generic - they apply to any optimisation
discipline, not specifically sustainability.

### The pillar overall - summary critical read

The Sustainability Pillar is **mostly the cost-optimisation pillar reframed in a carbon lens**,
with three sustainability-specific levers worth treating separately: (a) region selection for
location-based reporting, (b) hardware modernisation to lower-carbon processor families, (c) Spot
for hardware lifetime extension. Everything else overlaps with existing FinOps practice.

This means the engagement structure for a "GreenOps audit" should typically be:
- One unified audit looking through both lenses.
- One report presenting findings in both cost and carbon terms.
- Three sustainability-specific recommendation tracks layered on top.

Do not sell GreenOps as a separate engagement when the bulk of the work is already in scope under
FinOps.

---

## GreenOps engagement framing - vendor-agnostic

### Sizing the GreenOps opportunity

For most cloud customers, the achievable scope 1+2+3 reduction in cloud workloads sits in the
**5-15% range** over a 12-18 month engagement, expressed in tonnes CO2e. The headline reduction
in carbon footprint is rarely transformational on its own.

Decompose the typical opportunity:
- **70-80% of the carbon reduction comes from FinOps actions you would already take** -
  right-sizing, scheduling, decommissioning, lifecycle tiering.
- **20-30% is sustainability-specific** - region migration, hardware modernisation, Spot adoption
  for embodied-emissions amortisation, retention policy reductions specifically for
  embodied-storage reasons.

Set this expectation upfront with clients. A "GreenOps engagement" that promises 30%+ reductions
in 6 months is overpromising unless the customer's baseline is unusually wasteful.

### Where FinOps and GreenOps converge (the bulk of the work)

| Action | FinOps benefit | GreenOps benefit |
|---|---|---|
| Right-sizing oversized VMs | Compute cost down | Lower direct emissions, lower embodied amortisation |
| Auto-shutdown / scheduling | Compute cost down | Lower direct emissions during off-hours |
| Decommissioning idle / orphan resources | Direct cost reduction | Eliminates unused embodied carbon allocation |
| Storage lifecycle (hot to cool to archive) | Storage cost down | Lower embodied + powered storage |
| Snapshot and backup hygiene | Storage cost down | Same |
| Retention policy alignment to business need | Storage cost down | Same |

Frame to clients: **every cost optimisation is also a carbon optimisation, with rare exceptions.**

### Where they diverge (the cases that need explicit decisioning)

Four scenarios where cost and carbon point in different directions and the decision is strategic,
not technical.

**Region migration for carbon.** Moving from US-East-1 (~375 g CO2/kWh) to Sweden (~25 g) reduces
location-based emissions by ~15x. Trade-offs: higher latency to US users, potentially different
SKU pricing, egress charges to legacy systems, data-residency implications. Net cost may rise
even though carbon falls dramatically.

**Premium hardware for efficiency.** Latest-generation processors typically cost more per hour
but deliver more work per watt. Net cost per workload-output may be lower even at higher hourly
rate, but only if the workload actually utilises the new hardware features. For static workloads,
the migration cost may exceed savings. For carbon, latest-generation almost always wins.

**Hardware lifetime extension via Spot.** Spot reduces effective embodied-emissions amortisation
per workload-hour because the instances would otherwise sit idle. Trade-off: evictability,
complexity in workload design. Cost benefit is established; carbon benefit lands less often.

**Carbon reporting overhead.** Setting up CSRD-grade carbon reporting has its own infrastructure
cost (FinOps Hubs / Power BI / third-party platform). The reporting itself is overhead - the
value is in the optimisation it enables. Be explicit with the client about what they are paying
for and what they get.

### The cost-vs-carbon trade-off - four-quadrant framework

When cost and carbon diverge, the decision is strategic. Use this framing in client
conversations:

| Quadrant | Action |
|---|---|
| Lower cost + lower carbon | Pure win. No decision required. The bulk of optimisation. |
| Lower cost + higher carbon (rare) | Document the trade-off explicitly. Decide based on client's stated priority hierarchy. |
| Higher cost + lower carbon | Frame as a strategic sustainability investment. Compute a carbon-per-euro ROI. Escalate to the sustainability committee, not the CFO alone. |
| Higher cost + higher carbon | Never recommend. |

The "higher cost + lower carbon" quadrant is where consulting judgment matters most. A region
migration that costs €500k extra per year and reduces 200 tCO2e is €2.5k/tCO2e - useful to
compare against the customer's carbon-pricing assumption (internal carbon price, expected carbon
tax, voluntary offset rate). Many enterprise customers use €50-150/tCO2e as an internal price;
the region migration above is far more expensive than that and probably not justified on carbon
alone, but might be justified strategically.

### The CSRD / climate-disclosure conversation

For European clients (and increasingly global ones via SEC and similar regulators), carbon
reporting is no longer optional. The roles to know:

**Chief Sustainability Officer / Head of Sustainability.** Owns the disclosure narrative. Wants
methodology defensibility (ISO standards, third-party verification, scope completeness). Cares
less about absolute optimisation than about reportability and audit-readiness.

**CFO / Group Controller.** Owns the financial disclosure. Wants the carbon disclosure to align
with cost disclosure - consistent boundaries (which subsidiaries, which legal entities),
consistent allocation methodology (how shared services are split), consistent reporting cadence.

**Cloud platform owner / FinOps lead.** Owns the cloud data and the cost-allocation model. Needs
to operationalise emissions reporting on top of the existing cost reporting machinery - same
export pipelines, additional carbon dimensions.

**The deliverable for a CSRD-flavoured engagement is typically:**
- A documented carbon allocation methodology (which scopes, location-based vs market-based,
  calculation method, sources).
- A monthly or quarterly emissions report aligned to the financial reporting cadence.
- A reduction roadmap tied to the financial planning cycle (multi-year budget alignment).

The consulting work is as much about **reporting infrastructure** as about optimisation.
Sometimes more.

### The vendor-agnostic stance on carbon numbers

Vendor-reported carbon data should not be the only source of truth. Vendor methodology favours
vendor framing - not necessarily wrong, but worth triangulating. Build the cross-check into the
default workflow:

- **Cloud Carbon Footprint (open source).** Independent estimates across AWS, Azure, GCP. Useful
  sanity check on vendor-reported numbers.
- **Climatiq API.** Programmatic carbon estimates with documented emission factors. Useful for
  embedding in custom dashboards.
- **Electricity Maps.** Real-time grid intensity, location-based. Use to verify region-selection
  assumptions and to anchor the location-based vs market-based conversation in physical reality.
- **Academic sources.** Masanet et al. (Berkeley), the IEA, the European Environment Agency for
  context on how cloud emissions compare to other sectors.

State this stance explicitly in the engagement so the workflow always cross-checks vendor numbers
against an independent source.

### The three actions for any engagement (vendor-agnostic)

1. **Measure.** Establish the baseline using vendor-native tools (Sustainability Console for AWS,
   Emissions Impact Dashboard for Azure, Carbon Footprint for GCP) cross-checked against an
   independent source (CCF or Climatiq).
2. **Act.** Run the FinOps audit through both lenses - cost and carbon - and present findings in
   both. Layer the three sustainability-specific recommendations (region, hardware,
   Spot/equivalent).
3. **Report.** Build the recurring reporting mechanism - monthly or quarterly, aligned to
   financial reporting cadence, methodology documented for audit.

---

## Immediate wins (quick actions)

These actions reduce both cost and carbon. Prioritize in this order:

**1. Shut down idle and unused resources**
Instances with no active workload continue drawing power. Shutting them down eliminates
both spend and emissions immediately. Focus on: stopped-but-not-terminated VMs, idle
load balancers, orphaned storage volumes, empty container clusters.

**2. Rightsize overprovisioned compute**
Many teams overprovision "just in case." Matching instance size to actual usage improves
efficiency without sacrificing performance. Use CCF recommendations or native advisor
tools. Target: CPU utilization consistently below 20% is a rightsizing candidate.

**3. Schedule non-production resources**
Dev, test, and staging environments do not need to run 24/7. Implement automatic
shutdown outside business hours. Typical saving: 65–70% of compute hours for non-prod.
Use AWS Instance Scheduler, Azure Automation, or GCP resource policies.

**4. Move cold data to lower-carbon storage tiers**
Data that is rarely accessed consumes energy in hot storage unnecessarily. Identify data
with low access frequency and move to cold/archive tiers. This reduces both storage cost
and the energy required to maintain it.

**5. Eliminate multi-cloud duplication**
Running identical workloads across multiple clouds for redundancy purposes often creates
carbon waste. Audit cross-cloud replication to confirm it is operationally justified.

**Expected impact:** Optimisations typically reduce cloud carbon footprint by 20–40%
and generate cost savings of 15–40% simultaneously.

---

## Reporting and compliance

### Emission scopes (GHG Protocol)

| Scope | What it covers | Cloud relevance |
|---|---|---|
| Scope 1 | Direct emissions from owned sources | Not relevant for cloud customers |
| Scope 2 | Indirect emissions from purchased electricity | Your cloud workloads fall here |
| Scope 3 | All other indirect emissions (supply chain, hardware manufacturing) | Embodied emissions of cloud hardware; increasingly required |

Cloud customers report cloud emissions under **Scope 3** in their own GHG reporting.
Cloud providers report their data center emissions under Scope 1 and 2.

### Regulatory context

- **EU Energy Efficiency Directive (Data Centers in Europe):** European organisations
  must report on data center energy use, PUE, renewable energy share, water usage,
  and waste heat reuse. Reporting obligations apply from 2024 onward.
- **EU CSRD:** Large companies must report Scope 1, 2, and 3 emissions with third-party
  verification. Cloud emissions are material Scope 3 items.
- **SEC Climate-Related Disclosures (US):** Requires disclosure of material climate risks
  and GHG emissions for public companies.

### Reporting checklist

- [ ] Determine which reporting standard applies (GHG Protocol, CSRD, SEC, or internal)
- [ ] Decide on location-based vs. market-based methodology - document the choice
- [ ] Enable Scope 3 data in the AWS Sustainability Console (Methodology v3, October 2025, externally verified)
- [ ] Use GCP's location-based and market-based views to understand the gap
- [ ] Export monthly carbon data to a central data store alongside cost data
- [ ] Assign a carbon data owner (typically the FinOps lead or sustainability team)
- [ ] Do not rely solely on provider-supplied carbon data for external reporting without
  independent verification - provider tools use different methodologies

---

## Key tools reference

| Tool | Type | Use case | Link |
|---|---|---|---|
| AWS Sustainability Console | Native | AWS Scope 1/2/3 reporting (renamed from CCFT 31 March 2026; Methodology v3 Oct 2025) | aws.amazon.com/sustainability/tools |
| GCP Carbon Footprint | Native | GCP emissions, most granular | console.cloud.google.com |
| Azure Emissions Impact Dashboard | Native | Azure Scope 1/2/3 reporting | portal.azure.com |
| Cloud Carbon Footprint (CCF) | Open source | Multi-cloud, workload optimisation | cloudcarbonfootprint.org |
| Carbon Aware SDK (GSF) | Open source | Workload shifting, carbon-aware scheduling | github.com/Green-Software-Foundation/carbon-aware-sdk |
| Kepler (CNCF) | Open source | Per-pod power and carbon metrics in Kubernetes | github.com/sustainable-computing-io/kepler |
| Electricity Maps | Data provider | Real-time and forecast grid carbon intensity | electricitymaps.com |
| WattTime | Data provider | Marginal carbon intensity data for the Carbon Aware SDK | watttime.org |
| Climatiq API | Commercial API | Embed carbon estimates in custom tooling | climatiq.io |

---

## Common mistakes

**Relying on market-based provider data for optimisation decisions.**
RECs and renewable energy purchases reduce reported emissions on paper but do not
reflect the actual carbon intensity of the electricity running your workloads. Use
location-based data when making workload placement or shifting decisions.

**Committing to waste.**
The same rule applies as in FinOps: rightsize and shut down idle resources before
making any commitment. A Reserved Instance on an overprovisioned VM is still waste  -
now locked in for 1–3 years.

**Treating GreenOps as a separate program.**
Organisations that create a separate sustainability team disconnected from FinOps
typically fail to operationalize carbon reduction. Carbon data needs to be in the same
dashboards, the same team reviews, and the same governance processes as cost data.

**Measuring without acting.**
Carbon dashboards have low value if they are not connected to an optimisation workflow.
Establish a feedback loop: measure → identify top emitters → assign owners → reduce →
re-measure.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
