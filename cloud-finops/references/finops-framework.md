---
name: finops-framework
fcp_domain: "Manage the FinOps Practice"
fcp_capability: "FinOps Practice Operations"
fcp_capabilities_secondary: ["FinOps Assessment"]
fcp_phases: ["Inform", "Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner"]
fcp_personas_collaborating: ["Engineering", "Finance", "Product", "Procurement", "Leadership"]
fcp_maturity_entry: "Crawl"
---

# FinOps Framework Reference

> Source: FinOps Foundation (finops.org/framework), 2024 version.
> This file covers the complete FinOps Framework: principles, phases, maturity model,
> domains, capabilities, and personas.

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
- Teams optimising in isolation without cross-functional alignment (violates #1)
- Cost cutting that degrades revenue-generating systems (violates #2)
- All FinOps work done by one team with no engineering engagement (violates #3)
- Monthly reporting with no anomaly detection (violates #4)
- Decentralized, inconsistent tooling and processes (violates #5)
- Treating cloud like on-premises - fixed capacity, no elasticity (violates #6)

---

## The 3 Phases

FinOps phases are iterative, not sequential. Organisations cycle through them continuously
as their cloud usage evolves. Being in "Operate" for one capability does not mean an
organisation has left "Inform" for another.

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
**Walk targets:** 70% commitment discount coverage, documented optimisation process
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
- Cost optimisation suggestions in code reviews

---

## The 4 Domains and 22 Capabilities (2026 update)

The FinOps Foundation refreshed the framework in 2026. Six capabilities were
renamed to be more inclusive of non-public-cloud technology spend (SaaS,
licensing, AI), one new capability was added (`Executive Strategy Alignment`),
and the previous `Onboarding Workloads` capability was absorbed into
`Architecting & Workload Placement` (intake-time decisions) and
`FinOps Practice Operations` (the intake-gate process discipline).

Mapping vs the 2024 framework:

| 2024 name | 2026 name | Domain |
|---|---|---|
| Architecting for Cloud | Architecting & Workload Placement | Optimize Usage & Cost |
| Workload Optimization | Usage Optimization | Optimize Usage & Cost |
| Cloud Sustainability | Sustainability | Optimize Usage & Cost |
| Benchmarking | KPIs & Benchmarking | Quantify Business Value |
| Policy & Governance | Governance, Policy & Risk | Manage the FinOps Practice |
| FinOps Tools & Services | Automation, Tools & Services | Manage the FinOps Practice |
| (none) | Executive Strategy Alignment | Manage the FinOps Practice (NEW) |
| Onboarding Workloads | (folded - see above) | (removed) |

### Domain 1: Understand Usage & Cost

| Capability | Description |
|---|---|
| Data Ingestion | Collecting billing and usage data from cloud, SaaS, AI, and licensing providers into a central platform. FOCUS conformance (v1.2 for AWS and Azure, v1.0-1.2 for other providers) is the recommended cross-source schema. |
| Allocation | Distributing shared costs to cost centres, teams, or products |
| Reporting & Analytics | Providing actionable cost and usage reports across audiences (Finance, Engineering, Leadership) |
| Anomaly Management | Detecting and responding to unexpected cost changes |

### Domain 2: Quantify Business Value

| Capability | Description |
|---|---|
| Planning & Estimating | Forecasting cost for new projects, features, and architectural changes before deployment |
| Forecasting | Predicting future spend based on current trends and committed business plans |
| Budgeting | Setting and managing cost budgets across the organisation |
| KPIs & Benchmarking | Establishing measurable cost-and-value indicators and comparing against internal trend or external benchmarks |
| Unit Economics | Connecting cost to business output metrics (cost per tenant, per request, per business outcome) |

### Domain 3: Optimize Usage & Cost

| Capability | Description |
|---|---|
| Architecting & Workload Placement | Designing workloads and choosing where they run so cost is appropriate to value at deployment time. Covers migration-time placement decisions, intake-gate sizing, and architecture review. |
| Usage Optimization | Architectural and operational changes that reduce cost at the workload level (rightsizing, scheduling, scale-to-zero, modernisation, idle elimination) |
| Rate Optimization | Managing commitment discounts (RIs, Savings Plans, CUDs, Reservations) and negotiated agreements (EDP, MACC, GCP commits) |
| Licensing & SaaS | Managing software entitlements - BYOL, marketplace, SaaS subscriptions, AI tool seats, AI inference contracts |
| Sustainability | Measuring and reducing the energy / carbon impact of technology workloads, and connecting sustainability to cost-and-value decisions |

### Domain 4: Manage the FinOps Practice

| Capability | Description |
|---|---|
| Executive Strategy Alignment | Connecting FinOps to executive decision-making across executive priority alignment, multi-year investment strategy, product prioritisation, and strategic decision support (NEW in 2026) |
| FinOps Practice Operations | Running the FinOps team and driving organisational adoption. Covers both reactive team formation (responding to unexplained bills, unattributed spend) and intentional team formation (cloud adoption strategy, platform teams, cloud centres of excellence) |
| Governance, Policy & Risk | Establishing controls that align technology use with business objectives and managing financial / operational / compliance risk |
| FinOps Education & Enablement | Training teams - Engineering, Finance, Product, Procurement - to incorporate FinOps into daily work |
| Invoicing & Chargeback | Reconciling invoices and implementing financial accountability (showback, soft chargeback, hard chargeback) |
| FinOps Assessment | Measuring maturity across all capabilities and producing per-capability scorecards |
| Automation, Tools & Services | Evaluating and integrating tools and automation that support FinOps capabilities. FOCUS-conformant exports are available from AWS, Azure, GCP, Oracle, Tencent, Huawei, OVHCloud, Alibaba, and Nebius. |
| Intersecting Disciplines | Integration with adjacent operating disciplines (ITAM, ITSM, ITFM, Security, Sustainability, Procurement) |

### Building FinOps teams: Reactive vs intentional approaches

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

## Personas

### Core Personas

**FinOps Practitioner**
Central coordinator of the FinOps practice. Owns the process, tooling, and cross-functional
relationships. Bridges engineering and finance. Does not own all decisions - enables others
to make good ones.

**Engineering**
Implements optimisation recommendations. Owns rightsizing, architecture decisions, and
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
optimisation and cloud license portability (BYOL, AHUB).

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

---

## Maturity Model - Detailed

### Crawl
- Processes are manual, reactive, and inconsistent
- Basic cost visibility exists but allocation is incomplete (<50%)
- Optimisation is ad hoc - one-off projects rather than continuous practice
- FinOps is driven by one person or team with limited organisational reach
- Commitment discount coverage is low and unmanaged

**Priority at Crawl:** Establish visibility and allocation before anything else.
Do not attempt chargeback. Do not purchase large commitment discounts without allocation.

### Walk
- Processes are documented and repeatable
- Cost allocation >80%, showback reports delivered to teams
- Optimisation is proactive - rightsizing and waste elimination run continuously
- FinOps is cross-functional - engineering and finance participate regularly
- Commitment discount coverage ~70%, managed with utilization monitoring

**Priority at Walk:** Establish unit economics, expand optimisation scope, begin
governance automation. Evaluate readiness for chargeback.

### Run
- Processes are automated and self-improving
- Cost allocation >90%, real-time visibility, anomalies auto-detected
- Optimisation is embedded in engineering workflows - not a separate activity
- FinOps culture is distributed - teams own their costs without central policing
- Commitment discount coverage 80%+, managed by automation with human oversight
- Chargeback implemented where organisationally appropriate

**Priority at Run:** Continuous improvement, automation of governance, agentic FinOps
patterns where they add value without introducing risk.

---

## Common FinOps implementation mistakes

**Starting with optimisation before visibility**
Rightsizing without allocation produces savings no one can claim or repeat. Establish
who owns what before optimising what.

**Purchasing commitment discounts on unallocated spend**
Committing to reserved capacity before understanding usage patterns creates stranded
reservations. Analyze 90+ days of usage before purchasing commitments.

**Implementing chargeback before showback**
Organisations that jump to financial accountability before teams understand their costs
create resistance, not ownership. Show first, charge second.

**Building dashboards instead of processes**
A new dashboard without a defined review cadence and decision-making process is
documentation, not FinOps. The meeting matters as much as the data.

**Treating tagging as a one-time project**
Tagging compliance degrades over time without enforcement. Treat it as an ongoing
operational process with automated compliance checking.

**Centralizing all FinOps decisions**
A FinOps team that owns all decisions creates a bottleneck and removes team ownership.
The FinOps function should enable distributed decision-making, not replace it.

**Building practices without community support**
Developing FinOps practices in isolation without engaging the broader FinOps community
misses valuable lessons learned. Leverage community resources, attend meetups, and
participate in forums to avoid reinventing solutions.

**Allowing inaccurate data to erode engineering trust**
Engineers quickly lose faith in FinOps initiatives when cost data is wrong, incomplete,
or misattributed. Prioritise data accuracy and validation before pushing adoption -
one bad report can undermine months of relationship building.

**Managing commitments manually**
Spreadsheet-based commitment management becomes unmanageable at scale and leads to
underutilisation or overcommitment. Automate commitment tracking, recommendations,
and purchasing workflows early.

**Running unproductive cost review meetings**
Meetings that review costs without clear actions, ownership, or follow-up waste time
and create FinOps fatigue. Structure meetings with specific agendas, action items,
and accountability mechanisms.

---

> Sources: FinOps Foundation (finops.org/framework, 2024 version; State of FinOps 2026);
> FinOps Weekly podcast on common implementation mistakes; FinOps Weekly blog on shift-left practices.

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*