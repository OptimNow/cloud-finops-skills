# GreenOps & Cloud Carbon Optimization

> Practical guidance for measuring, reducing, and governing cloud carbon emissions.
> Covers carbon measurement tooling (native and open source), FinOps-to-GreenOps
> integration, workload shifting strategies (temporal and spatial), region selection,
> and reporting alignment with GHG Protocol and EU/SEC regulations.
>
> Distilled from: Forrester, Thoughtworks, Green Software Foundation, AWS CCFT docs,
> CloudCarbonFootprint.org, North.Cloud, Climatiq, and Microsoft/UBS Carbon Aware SDK
> case study (2023–2025).

---

## Context and scale

Data centers consumed approximately 415 TWh globally in 2024  - roughly 1.5% of world
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
| **AWS CCFT** (updated Jan 2025) | Scope 1, 2, 3 | Regional, by service | Lagged data; limited for workload-level optimization |
| **GCP Carbon Footprint** | Scope 1, 2, 3 | Region + service, location-based and market-based | Most granular of the three |
| **Azure Emissions Impact Dashboard** | Scope 1, 2, 3 | Service-level | Relies on market-based method (RECs); less granular than GCP |

**Important distinction:** Market-based measurement uses Renewable Energy Certificates
(RECs) and can mask actual grid carbon intensity. Location-based measurement uses the
real carbon intensity of the local grid. For optimization decisions, prefer location-based
data. For ESG reporting, understand which method your auditors require.

**AWS CCFT setup checklist (2025 methodology):**
- [ ] Enable CCFT in the Billing & Cost Management console
- [ ] Configure Data Exports to S3 (CSV or Parquet, automated monthly delivery)
- [ ] Scope the export to the management account to cover all member accounts
- [ ] Use January 2025 forward data for the updated Scope 3 methodology
- [ ] Pair with Cost Explorer tags to correlate emissions to teams or products

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
- You need workload-level granularity for optimization (not just reporting)
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
layer carbon metrics onto a mature FinOps practice is surprisingly small  - the
hardest infrastructure work has already been done. The practical starting point is
adding one column  - gCO₂e  - to existing cost reports.

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

Region selection is the single highest-impact optimization available. Research from
Microsoft's Carbon Aware SDK project shows that location-shifting can reduce carbon
emissions by up to 75% for a given workload.

### Low-carbon regions by provider (indicative)

| Provider | Lower carbon regions | Higher carbon regions |
|---|---|---|
| **AWS** | us-east-1 (Virginia), us-east-2 (Ohio), eu-west-1 (Ireland)  - 100% renewable matched | Regions with coal-heavy grids vary; check CCFT regional data |
| **GCP** | Montreal, Toronto, Santiago (90%+ carbon-free energy) | Varies by grid mix |
| **Azure** | Nordics, Ireland, parts of Canada | Regions dependent on coal or gas grids |

**Recommendation:** Before selecting a region for a new workload, check the carbon
intensity in CCF's regional breakdown or the Climatiq region comparison chart. Do not
rely solely on provider sustainability claims  - use location-based data.

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
- ML model training (highest impact  - long-running, compute-intensive, not time-critical)
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

**Expected impact:** Optimizations typically reduce cloud carbon footprint by 20–40%
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

- **EU Energy Efficiency Directive (Data Centers in Europe):** European organizations
  must report on data center energy use, PUE, renewable energy share, water usage,
  and waste heat reuse. Reporting obligations apply from 2024 onward.
- **EU CSRD:** Large companies must report Scope 1, 2, and 3 emissions with third-party
  verification. Cloud emissions are material Scope 3 items.
- **SEC Climate-Related Disclosures (US):** Requires disclosure of material climate risks
  and GHG emissions for public companies.

### Reporting checklist

- [ ] Determine which reporting standard applies (GHG Protocol, CSRD, SEC, or internal)
- [ ] Decide on location-based vs. market-based methodology  - document the choice
- [ ] Enable Scope 3 data in AWS CCFT (available from Jan 2025 methodology)
- [ ] Use GCP's location-based and market-based views to understand the gap
- [ ] Export monthly carbon data to a central data store alongside cost data
- [ ] Assign a carbon data owner (typically the FinOps lead or sustainability team)
- [ ] Do not rely solely on provider-supplied carbon data for external reporting without
  independent verification  - provider tools use different methodologies

---

## Key tools reference

| Tool | Type | Use case | Link |
|---|---|---|---|
| AWS Customer Carbon Footprint Tool | Native | AWS Scope 1/2/3 reporting | aws.amazon.com/sustainability/tools |
| GCP Carbon Footprint | Native | GCP emissions, most granular | console.cloud.google.com |
| Azure Emissions Impact Dashboard | Native | Azure Scope 1/2/3 reporting | portal.azure.com |
| Cloud Carbon Footprint (CCF) | Open source | Multi-cloud, workload optimization | cloudcarbonfootprint.org |
| Carbon Aware SDK (GSF) | Open source | Workload shifting, carbon-aware scheduling | github.com/Green-Software-Foundation/carbon-aware-sdk |
| Kepler (CNCF) | Open source | Per-pod power and carbon metrics in Kubernetes | github.com/sustainable-computing-io/kepler |
| Electricity Maps | Data provider | Real-time and forecast grid carbon intensity | electricitymaps.com |
| WattTime | Data provider | Marginal carbon intensity data for the Carbon Aware SDK | watttime.org |
| Climatiq API | Commercial API | Embed carbon estimates in custom tooling | climatiq.io |

---

## Common mistakes

**Relying on market-based provider data for optimization decisions.**
RECs and renewable energy purchases reduce reported emissions on paper but do not
reflect the actual carbon intensity of the electricity running your workloads. Use
location-based data when making workload placement or shifting decisions.

**Committing to waste.**
The same rule applies as in FinOps: rightsize and shut down idle resources before
making any commitment. A Reserved Instance on an overprovisioned VM is still waste  -
now locked in for 1–3 years.

**Treating GreenOps as a separate program.**
Organizations that create a separate sustainability team disconnected from FinOps
typically fail to operationalize carbon reduction. Carbon data needs to be in the same
dashboards, the same team reviews, and the same governance processes as cost data.

**Measuring without acting.**
Carbon dashboards have low value if they are not connected to an optimization workflow.
Establish a feedback loop: measure → identify top emitters → assign owners → reduce →
re-measure.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io)  - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
