# FinOps Framework Reference

> Source: FinOps Foundation (finops.org/framework). The structure documented below is the
> 2024 framework (4 domains, 22 capabilities). The Foundation published a **2026 framework
> update** that adds an **Executive Strategy Alignment** dimension and renames several
> capabilities (notably **Workload Optimization → Usage Optimization**). See "2026 framework
> update" section below for the changes; verify the authoritative current capability list
> at https://www.finops.org/insights/2026-finops-framework/ before quoting in customer
> engagements.

---

## The 6 FinOps Principles
<!-- idx:37b46c22605776cb -->

1. **Teams need to collaborate** - FinOps requires cooperation across engineering, finance,
   product, and leadership. No single team can practice FinOps alone.

2. **Business value drives technology decisions** - the goal is not cost minimization but
   value maximization. Decisions should connect spend to outcomes.

3. **Everyone takes ownership for their cloud usage** - distributed accountability is more
   effective than centralized policing. Engineers who see their costs act on them.

4. **FinOps data should be accessible, timely, and accurate** - delayed, incomplete, or
   unattributed data cannot support good decisions. Visibility is the foundation.

5. **FinOps should be enabled centrally** - a central FinOps function sets standards,
   builds tooling, and enables teams. It does not own all decisions.

6. **Take advantage of the variable cost model of the cloud** - the cloud's elasticity
   is an asset. Commit to baseline, keep growth variable, avoid over-provisioning.

**Common principle violations to identify:**
- Teams optimizing in isolation without cross-functional alignment (violates #1)
- Cost cutting that degrades revenue-generating systems (violates #2)
- All FinOps work done by one team with no engineering engagement (violates #3)
- Monthly reporting with no anomaly detection (violates #4)
- Decentralized, inconsistent tooling and processes (violates #5)
- Treating cloud like on-premises - fixed capacity, no elasticity (violates #6)

---

## The 3 Phases

FinOps phases are iterative, not sequential. Organizations cycle through them continuously
as their cloud usage evolves. Being in "Operate" for one capability does not mean an
organization has left "Inform" for another.

### Inform - Establish visibility and allocation

**Goal:** Make cost data accessible, attributed, and actionable.

**Key activities:**
- Set up data ingestion (AWS CUR / Azure Cost Export / GCP BigQuery billing export / FOCUS exports)
- Implement cost allocation - by account, subscription, project, or tag
- Build executive dashboards showing top cost drivers and trends
- Configure anomaly alerts (recommended threshold: >20% daily change)
- Establish a shared cost allocation methodology

**Crawl targets:** >50% of spend allocated, basic dashboards live, alerts configured
**Walk targets:** >80% allocated, hierarchical allocation, showback reports to teams
**Run targets:** >90% allocated, automated allocation, real-time visibility

### Optimize - Improve rates and usage efficiency

**Goal:** Reduce cost while maintaining or improving performance and reliability.

**Key activities:**
- Rightsize compute resources (EC2, VMs, containers, databases)
- Implement commitment discounts (Reserved Instances, Savings Plans, CUDs)
- Eliminate waste - unattached volumes, idle resources, zombie features
- Schedule non-production environments (60–70% savings on dev/test)
- Implement lifecycle policies for storage and data

**Crawl targets:** Obvious waste eliminated, basic rightsizing started
**Walk targets:** 70% commitment discount coverage, documented optimization process
**Run targets:** 80%+ commitment coverage, continuous rightsizing, automated policies

### Operate - Operationalize through governance and automation

**Goal:** Embed FinOps into engineering and finance workflows permanently.

**Key activities:**
- Establish weekly or biweekly cost review cadence with engineering teams
- Define and enforce mandatory tagging policies
- Implement budget alerts and approval workflows for new spend
- Automate governance through policy-as-code (Cloud Custodian, OpenOps, AWS Config)
- Build chargeback or showback reporting into finance workflows

**Crawl targets:** Weekly cost reviews established, mandatory tags defined
**Walk targets:** Automated alerts, showback reports delivered to teams
**Run targets:** Chargeback implemented, policies self-enforcing, anomalies auto-investigated

#### Shift Left FinOps Practices

**Goal:** Prevent cost issues during development rather than discovering them in production.

Cost errors typically appear weeks after architectural decisions are deployed, making
prevention far more valuable than remediation. Shifting FinOps left embeds cost
considerations into the development lifecycle before expensive architectural changes
become difficult to reverse.

**Key activities:**
- **Pre-deployment cost estimation** - require cost projections for new features and
  architectural changes during design reviews
- **Cost-aware CI/CD pipelines** - integrate cost validation into build processes,
  failing deployments that exceed cost thresholds
- **Development environment cost visibility** - provide real-time cost feedback in IDEs
  and development dashboards
- **Architectural cost reviews** - include FinOps practitioners in architecture review
  boards (ARBs) to assess cost implications before approval
- **Cost testing in lower environments** - validate cost models in dev/test before
  production deployment
- **Infrastructure-as-code cost scanning** - tools like Infracost analyse Terraform
  and CloudFormation templates for cost impact before deployment

**Implementation approach:**
1. Start with visibility - developers need to see the cost impact of their code
2. Add guardrails - implement soft limits that warn before hard limits that block
3. Provide alternatives - when blocking expensive patterns, suggest cost-effective options
4. Measure prevention value - track costs avoided through shift-left practices

**Common shift-left patterns:**
- Requiring cost estimates in pull requests for infrastructure changes
- Automated cost anomaly detection in staging environments
- Cost-based approval workflows for resource provisioning
- Developer cost budgets with real-time tracking
- Cost optimization suggestions in code reviews

---

## The 4 Domains and 22 Capabilities (2024 baseline)

> The structure documented in this section is the **2024 framework baseline**. The
> FinOps Foundation published a **2026 framework update** (Executive Strategy
> Alignment dimension; Workload Optimization renamed to Usage Optimization;
> capability list refreshed) - see "2026 framework update" further down for the
> changes. In customer engagements as of 2026, use the 2026 capability names; the
> 2024 baseline below remains useful for mapping legacy artefacts (older
> assessments, vendor proposals, procurement decks) to current terminology.

### Domain 1: Understand Usage and Cost

| Capability | Description |
|---|---|
| Data Ingestion | Collecting billing data from cloud providers into a central platform. FOCUS specification (v1.2 for AWS and Azure, v1.0-1.2 for other providers) enables normalised data ingestion across multiple clouds. |
| Allocation | Distributing shared costs to cost centers, teams, or products |
| Reporting and Analytics | Providing actionable cost and usage reports |
| Anomaly Management | Detecting and responding to unexpected cost changes |

### Domain 2: Quantify Business Value

| Capability | Description |
|---|---|
| Planning and Estimating | Forecasting cloud spend for new projects and features |
| Budgeting | Setting and managing cloud budgets across the organization |
| Forecasting | Predicting future cloud spend based on current trends |
| Unit Economics | Connecting cloud cost to business output metrics |
| Sustainability | Measuring and reducing the carbon impact of cloud usage |

### Domain 3: Optimize Usage and Cost

| Capability | Description |
|---|---|
| Rightsizing | Matching resource size to actual workload requirements |
| Commitment Discounts | Managing RIs, Savings Plans, and CUDs for sustained workloads |
| Workload Optimization | Architectural changes that reduce cost at the workload level |
| License Optimization | Managing software licenses (BYOL, AHUB, marketplace) |
| Cloud Sustainability | Reducing energy and carbon footprint of cloud workloads |

### Domain 4: Manage the FinOps Practice

| Capability | Description |
|---|---|
| FinOps Practice Operations | Running the FinOps team and driving organizational adoption. This includes both reactive and intentional team building patterns - organisations often start reactively (responding to unexplained bills or unattributed spend) before transitioning to proactive practice establishment. |
| FinOps Assessment | Measuring maturity across all capabilities |
| FinOps Education and Enablement | Training teams to incorporate FinOps into daily work |
| Onboarding Workflows | Managing cost implications of cloud migrations |
| Cloud Policy and Governance | Establishing controls that align cloud use with business objectives |
| FinOps Tools and Services | Evaluating and integrating tools to support FinOps capabilities. FOCUS exports are now offered by most major providers but **conformance levels vary** - AWS Data Exports for FOCUS 1.2 went GA on 19 November 2025; Azure Cost Management offers a FOCUS 1.2 preview with documented conformance gaps; GCP and others publish FOCUS exports at varying levels. Distinguish ratified FOCUS 1.2 conformance from preview / partial-conformance exports when planning multi-cloud normalisation. Source: https://focus.finops.org/focus-specification/ |
| Invoicing and Chargeback | Reconciling cloud invoices and implementing financial accountability |
| Cloud Vendor Management | Managing relationships, contracts, and commitments with cloud providers |

---

## 2026 framework update

The FinOps Foundation published a 2026 framework update that builds on the 2024
structure documented above. Verify exact capability names and the full delta against
the official page (https://www.finops.org/insights/2026-finops-framework/) before
quoting in a customer engagement - the Foundation continues to refine the framework
between major versions.

**Headline changes:**

- **Executive Strategy Alignment** is added as an explicit dimension. The 2024
  framework treated executive engagement as embedded across "Manage the FinOps
  Practice"; the 2026 version makes strategic alignment with C-suite priorities a
  named capability area in its own right. Practical implication: FinOps practitioners
  reporting to CTO/CIO (78% per State of FinOps 2026) need an explicit cadence for
  surfacing technology-spend trade-offs at the executive level.
- **Workload Optimization → Usage Optimization.** The capability previously named
  Workload Optimization has been renamed to **Usage Optimization**. The semantic
  shift reframes the work from architectural rewrites of workloads to the broader
  practice of matching consumption to demand (which includes, but is not limited
  to, architectural change). Rightsizing, autoscaling, scheduling, and demand
  shaping all live under Usage Optimization.
- **Capability list refreshed.** The capability count and grouping have been
  refined relative to the 2024 "4 domains, 22 capabilities" structure. Treat the
  numbers in the table above as the 2024 baseline; the authoritative 2026 list is
  on the Foundation page.

**What did not change:**

- The 6 principles. They remain the canonical statements of FinOps philosophy.
- The 3 phases (Inform / Optimize / Operate) and the Crawl / Walk / Run maturity
  model.
- The persona model and allied-persona framing.

**FinOps engagement implications:**

- When using framework capabilities as the spine of a maturity assessment, use the
  2026 capability names with customers - the 2024 names are now legacy.
- "Workload Optimization" still appears in older customer artefacts (procurement
  decks, vendor proposals, prior assessment reports). Treat it as equivalent to
  Usage Optimization rather than rewriting historical documents.
- The Executive Strategy Alignment addition is a useful prompt for engagements
  that have plateaued at "tactical optimisation" - it reframes the work as
  strategic, not just operational.

Source: https://www.finops.org/insights/2026-finops-framework/

---

## Personas

### Core Personas

**FinOps Practitioner**
Central coordinator of the FinOps practice. Owns the process, tooling, and cross-functional
relationships. Bridges engineering and finance. Does not own all decisions - enables others
to make good ones.

**Engineering**
Implements optimization recommendations. Owns rightsizing, architecture decisions, and
tagging at the resource level. Needs cost visibility in their existing workflows (not
separate dashboards).

**Finance**
Owns budgets, forecasting, and financial reporting. Needs cloud cost data mapped to
existing budget structures and accounting categories. Primary audience for chargeback.

**Product**
Connects cloud spend to product features and user outcomes. Key partner for unit economics.
Often the right owner for AI feature cost management.

**Procurement**
Manages cloud vendor contracts, enterprise discounts, and commitment purchases. Involved
in Reserved Instance and Savings Plan purchasing decisions.

**Leadership (C-suite, VP)**
Requires executive dashboards showing cloud spend vs. budget, trend, and business value.
Primary sponsor for FinOps culture change. Engaged for chargeback decisions and large
commitment purchases.

### Allied Personas

**ITAM (IT Asset Management)** - manages software licenses, intersects with license
optimization and cloud license portability (BYOL, AHUB).

**Sustainability** - connects cloud efficiency work to carbon metrics and ESG reporting.

**ITSM (IT Service Management)** - integrates FinOps into change management and
service catalog processes.

**Security** - intersects with governance, tagging policy enforcement, and access controls
for cost management tools.

---

## FinOps organisational placement

The State of FinOps 2026 survey (6th edition, 1,192 respondents representing $83+ billion
in cloud spend, published February 2026) provides current data on how FinOps practices
are structured and positioned within organisations.

**Reporting line:** 78% of FinOps practices now report into the CTO/CIO organisation
(up 18% vs 2023). Teams reporting to the CFO declined to 8%. Practitioners aligned with
CTOs and CIOs indicated two to four times more influence over technology selection -
reinforcing that FinOps is increasingly viewed as a technology capability tied to
architecture and platform decisions, not financial reporting alone.

**Team structure:** Centralized enablement remains the dominant model (60%), followed by
hub-and-spoke (21%) which is more common in large enterprises. Team sizes remain small:
organisations managing over $100M in cloud spend typically average 8-10 practitioners
and 3-10 contractors.

**Scope expansion:** FinOps has moved decisively beyond cloud-only cost management. 90%
of respondents now manage SaaS (up from 65% in 2025), 64% manage licensing (up from
49%), 57% manage private cloud, and 48% manage data centres. An emerging 28% are
beginning to include labour costs.

**Mission change:** These trends prompted the FinOps Foundation to update its mission
from "Advancing the People who manage the Value of Cloud" to "Advancing the People who
manage the Value of Technology."

### Building FinOps teams: Reactive vs. intentional approaches

Organisations typically form FinOps teams through one of two patterns:

**Reactive team formation** occurs when organisations respond to immediate pain points:
- Unexplained cloud bills that shock finance teams
- Unattributed spend that prevents accountability
- Budget overruns that trigger executive attention
- Failed cloud migrations due to unexpected costs

**Intentional team formation** happens when organisations proactively establish FinOps:
- As part of cloud adoption strategy
- Before major digital transformation initiatives
- When establishing platform teams or cloud centres of excellence
- During organisational restructuring that creates new accountability models

**Transitioning from reactive to proactive:**
1. **Stabilise the immediate crisis** - address the triggering issue first to build credibility
2. **Document lessons learned** - use the reactive trigger as a case study for broader adoption
3. **Establish forward-looking processes** - shift from firefighting to prevention
4. **Build cross-functional relationships** - expand beyond the initial crisis team
5. **Define long-term charter** - move from ad hoc responses to strategic practice

**Common triggers that drive FinOps team formation:**
- Cloud spend exceeding 10% of IT budget
- Failed audit findings on cloud cost controls
- M&A activity requiring cloud estate consolidation
- Board-level questions about cloud ROI
- Competitive pressure to improve unit economics

Source: Holori Blog on building FinOps teams (https://holori.com/how-to-build-a-finops-team/)

---

## Maturity Model - Detailed

### Crawl
- Processes are manual, reactive, and inconsistent
- Basic cost visibility exists but allocation is incomplete (<50%)