---
name: finops-sam
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Licensing & SaaS"
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Procurement"]
fcp_personas_collaborating: ["Engineering", "Finance", "Leadership"]
fcp_maturity_entry: "Walk"
---

# FinOps for SaaS Asset Management (SAM)

> SaaS management as a FinOps capability: discovery, license optimisation, renewal governance,
> SaaS Management Platforms (SMPs), shadow IT detection, and the connection to AI transition
> readiness. 6 sprawl patterns for diagnosing waste and building optimisation roadmaps.

---

## Why SAM matters for FinOps
<!-- ref:37b46c22605776cb -->

SaaS has become one of the largest and least visible cost categories in most organisations. Unlike IaaS, where billing data flows through cloud provider consoles, SaaS spend is decentralised: purchased on corporate credit cards, expensed by individual teams, auto-renewed without review, and rarely consolidated into a single view.

The State of FinOps 2026 survey (6th edition, 1,192 respondents, $83+ billion in cloud spend, published February 2026) confirms that SaaS is now firmly within the FinOps scope: 90% of respondents manage SaaS or plan to (up from 65% in 2025). Licensing management has also grown to 64% (up from 49%). This expansion reflects a practical reality: SaaS and IaaS are often interchangeable (a managed database versus an RDS instance, a SaaS observability tool versus self-hosted Prometheus), so managing one without the other creates blind spots in cost allocation and optimisation.

Gartner predicts that by 2028, over 70% of organisations will centralize SaaS management using a SaaS Management Platform (SMP), up from less than 30% in 2025. Organizations that fail to centralize SaaS lifecycle management will overspend on SaaS by at least 25% due to unused entitlements and unnecessary overlapping tools, and remain five times more susceptible to cyberincidents or data loss.

The structural problem - sometimes called the "SaaSocalypse" - is not access to tools. It is loss of control. A mid-sized organisation may run 120+ SaaS applications. License renewals go unreviewed. Tools described as mission-critical are used by three people. Finance discovers overlapping tools doing the same job only during emergency audits. Procurement becomes the bottleneck instead of the enabler.

**Connection to the FinOps Inform phase:** You cannot optimise what you cannot see. SaaS visibility is the prerequisite for license optimisation, renewal negotiation, and any serious application rationalisation effort.

---

## SaaS Sprawl Patterns (6)

These patterns describe the most common forms of SaaS waste. Use them to diagnose an organisation's SaaS estate and prioritize remediation.

**Unused or Underutilised Licenses (Shelfware)**
Type: License Waste

Licenses allocated to users who have not logged in within 30, 60, or 90 days. Common with enterprise agreements where seats are purchased in bulk and assigned broadly. Often the single largest source of SaaS waste.

- Implement automated license reharvesting after a defined inactivity threshold
- Notify users before revocation to avoid disrupting active but infrequent users
- Track reharvested licenses as a KPI: number of seats reclaimed per quarter
- Distinguish between inactivity (no login) and low usage (login but minimal feature use)

**Overlapping and Redundant Applications**
Type: Portfolio Waste

Multiple tools serving the same function across different teams. Marketing uses Tool A for project management, Engineering uses Tool B, Operations uses Tool C. Each was chosen locally for valid reasons, but the aggregate cost and data fragmentation is significant.

- Conduct application rationalisation: map tools to business functions, identify overlaps
- Consolidate to a single tool per function where possible, or establish a maximum of two
- Use feature-level usage data (not just login frequency) to determine which tool best serves the organisation's needs
- Involve end users in consolidation decisions to reduce resistance

**Per-Query Agent Billing**
Type: Emerging Cost Model

SaaS vendors are introducing per-query pricing specifically for AI agent interactions, moving beyond traditional seat-based models. As of March 2026, this represents a fundamental shift: agents do not need seats, but they generate thousands of API calls. A single agent workflow might query multiple SaaS systems, each charging per interaction.

- Monitor agent-to-SaaS API call volumes as a new cost driver
- Implement rate limiting and caching strategies to control per-query costs
- Negotiate bulk query packages or agent-specific pricing tiers during renewals
- Track cost-per-outcome metrics: what business value did those queries generate?
- Consider hybrid models: human seats plus agent query allowances

**Shadow SaaS**
Type: Governance Gap

Applications purchased or adopted without IT or procurement approval. Includes free-tier signups, credit-card purchases expensed individually, and trial accounts that convert to paid without review. Shadow SaaS introduces security risk (unvetted data handling), compliance risk (no DPA or SOC2 review), and cost risk (untracked spend).

- Deploy continuous discovery using multiple methods (see Discovery Methods section)
- Distinguish between shadow SaaS that signals unmet needs (positive signal) and careless purchasing (governance failure)
- Create an approved app catalog with a fast-track procurement process for low-cost tools, so employees do not feel the need to bypass IT
- Shadow IT is often a signal of innovation - govern it, do not crush it

**Auto-Renewal Without Review**
Type: Contract Waste

SaaS contracts that renew automatically without a usage review, pricing renegotiation, or competitive assessment. Often discovered only after the renewal window has closed. Particularly costly with multi-year enterprise agreements where termination notice periods are 60-90 days before renewal.

- Maintain a centralised renewal calendar with alerts at 90, 60, and 30 days before renewal
- Require a usage review and business justification before every renewal above a defined spend threshold
- Use actual usage data as negotiation leverage during renewal conversations
- Track auto-renewal clauses, price-lock guarantees, and true-up requirements as contract metadata

**Tier Mismatch**
Type: Licensing Waste

Users assigned premium or enterprise-tier licenses when their actual usage only requires a standard or basic tier. Common with productivity suites (e.g., Microsoft 365 E5 assigned to users who only need E3 features) and collaboration tools with tiered pricing.

- Analyse feature-level usage to identify users who can be downgraded
- Implement a default-to-lowest-tier policy for new user provisioning, with upgrade requests requiring justification
- Review tier assignments quarterly, particularly after organisational changes
- Calculate the cost delta between current and optimal tier assignments to quantify savings

**Missing Contract Metadata**
Type: Governance Gap

SaaS contracts managed without structured tracking of critical terms: renewal dates, termination notice periods, price escalation clauses, data portability provisions, and exit strategies. This makes the organisation reactive rather than proactive, and creates lock-in by default rather than by choice.

- Store all contract metadata in a centralised system (SMP, ITAM tool, or at minimum a structured spreadsheet)
- Track: renewal date, notice period, price-lock expiry, data export provisions, SLA terms, and named owner
- Flag contracts without exit clauses or data portability provisions as high-risk
- Treat exit strategy as a first-class requirement during procurement, not an afterthought

---

## Discovery Methods

No single discovery method provides complete visibility into an organisation's SaaS estate. Effective SaaS discovery requires layering multiple methods to eliminate blind spots.

**SSO / Identity Provider Logs**
Source: Okta, Azure AD, Google Workspace
Strengths: Reliable view of sanctioned apps accessed via corporate credentials. Easy to implement. Shows login frequency and user-level access.
Limitations: Only covers apps integrated with SSO. Misses shadow SaaS, free-tier tools, and apps where users authenticate with username/password or personal email. SSO licenses can also be significantly more expensive, creating a cost barrier to onboarding all apps.

**Financial and Expense Records**
Source: Coupa, SAP Ariba, Concur, corporate credit card statements, AP systems
Strengths: Reveals what the organisation is paying for, including shadow SaaS that appears on expense reports. Can uncover contracts and subscriptions that IT does not know about.
Limitations: Only shows what is paid for - misses free-tier and trial usage. Delay between purchase and data availability (monthly reconciliation cycles). Line items are often vague, requiring AI-powered categorisation. No user-level attribution.

**API Connectors (Direct Integrations)**
Source: Vendor-specific APIs for major SaaS applications
Strengths: Deep usage and entitlement data directly from the vendor. Can show feature-level usage, not just login counts. High data quality.
Limitations: Only available for apps the organisation already knows about. Limited to the connectors the SMP provider supports (typically hundreds, not thousands). Cannot discover shadow SaaS.

**Cloud Access Security Broker (CASB)**
Source: Network-level traffic analysis (Netskope, Zscaler, Microsoft Defender for Cloud Apps)
Strengths: Can detect SaaS usage across the corporate network, including shadow SaaS. Designed for security, so it captures risk-relevant data. Good for tightly controlled environments.
Limitations: Only sees traffic on managed networks. Misses remote workers not on VPN, personal devices, and BYOD. Designed for security rather than financial optimisation - may flag apps but cannot provide cost or license data. Legacy perimeter-based approach that struggles in decentralised organisations.

**Browser Extensions**
Source: Lightweight agents deployed to corporate browsers
Strengths: Granular, real-time visibility into SaaS usage regardless of network. Can capture the long tail of smaller apps, free-tier tools, and shadow SaaS. Works for remote workers.
Limitations: Privacy concerns from employees. Difficult to scale across large enterprises. Requires managed browser deployment. Does not capture mobile-only SaaS usage.

**Email-Based Discovery**
Source: Corporate email metadata (signup confirmations, password resets, billing notifications)
Strengths: Works retroactively - can discover SaaS usage from before the tool was deployed. Covers apps authenticated via any method (SSO, username/password, OAuth, social sign-on). High coverage across the long tail of shadow SaaS.
Limitations: Cannot detect SaaS tied to personal email accounts. Privacy considerations around email scanning. Requires careful scoping to balance discovery with employee trust.

**Recommended approach:** Layer SSO + financial records as the foundation. Add browser extensions or CASB for shadow SaaS detection. Use API connectors for deep usage data on high-spend apps. Consider email-based discovery for retroactive inventory building.

---

## Core SAM Capabilities Within FinOps

The FinOps Foundation's Licensing & SaaS capability (added to the Framework in 2024) and the FinOps for SaaS scope define how SAM integrates with FinOps practice. The key capabilities, mapped to FinOps phases:

### Inform

**Inventory and Discovery**
Continuous (not one-off) identification of all SaaS applications in use. The goal is a single source of truth: every app, its owner, its cost, its usage level, its contract terms, and its security status.

**Cost Allocation and Chargeback**
Map 100% of SaaS spend to cost centres, products, or application owners. SaaS billing data may come through CSP Marketplace, direct vendor invoices, or expense reports - all need to be normalised and allocated. The FinOps Foundation recommends providing SaaS billing data in FOCUS format where possible.

**SaaS Taxonomy**
Segment applications by function (horizontal vs. vertical) and criticality (core vs. long-tail). Apply tiered governance: high-touch management for top-spend applications, lighter oversight for low-cost tools. This prevents governance overhead from exceeding the cost of the tools being governed.

### Optimise

**License Optimisation**
Rightsize license tiers, reharvest unused seats, and eliminate shelfware. This is the SaaS equivalent of IaaS rightsizing. Requires feature-level usage data, not just login frequency. With per-query agent billing emerging, optimisation now includes both human seat allocation and agent API consumption patterns.

**Renewal Management**
Centralised tracking of all renewal dates, notice periods, and contract terms. Usage data from the Inform phase becomes negotiation leverage. The goal: no renewal happens without a data-backed review of whether the tool is still needed, at the right tier, at a competitive price. Include agent usage projections in renewal negotiations - vendors are increasingly open to hybrid pricing models that account for both human and agent interactions.

**Build vs. Buy Decisions**
Data-driven comparison between purchasing SaaS versus building internal solutions. Factor in Total Cost of Ownership (TCO) including maintenance, integration, and opportunity cost - not just license price versus development cost.

### Operate

**Contract Lifecycle Management**
Track the full lifecycle from procurement through renewal or exit. Include: vendor management, termination clauses, price escalation terms, data portability, and true-up/down pricing. Unlike IaaS, most SaaS agreements cannot be changed quickly - some take years to exit. Planning must happen well in advance with procurement and ITAM personas.

**Unit Economics**
Link SaaS costs to business metrics: cost per transaction, cost per customer, cost per employee. This connects SaaS spend to business value, which is the core FinOps principle. Unit economics also help justify SaaS investments and identify when a tool's cost exceeds its contribution.

**Governance and Policy**
Approved app catalog, procurement policies, security review requirements, and shadow IT response procedures. The goal is to make the compliant path the easiest path - fast-track procurement for low-cost tools, automated provisioning for approved apps, clear escalation for exceptions.

---

## SaaS Management Platform (SMP) Landscape

SMPs are purpose-built tools that consolidate discovery, optimisation, and governance into a single platform. They address the transition period where SaaS sprawl is real but full automation (e.g., AI agents replacing SaaS backends) has not yet arrived.

### What an SMP provides

Core capabilities across all mature SMPs: continuous SaaS discovery (multi-method), license usage analytics, spend tracking and benchmarking, renewal management with calendar alerts, workflow automation (onboarding, offboarding, reharvesting), shadow IT detection, and reporting for IT, finance, and procurement stakeholders.

### 2025 Gartner Magic Quadrant

The Gartner Magic Quadrant for SaaS Management Platforms (published July 2025, analysts: Tom Cipolla, Dan Wilson, Lina Al Dana) evaluated 17 vendors. Notable vendors include:

**Zylo** - Enterprise-focused. Manages over $40B in SaaS spend across its customer base. Strong in continuous discovery, license optimisation, and renewal management. Positions itself as a platform for IT, procurement, finance, and SAM teams working together. Recognised as a Leader in both the 2024 and 2025 Gartner MQ editions. Customers include AbbVie, Adobe, Atlassian, Salesforce.

**Flexera** - The only vendor recognised in both the 2025 Gartner MQ for SaaS Management Platforms and the 2024 Gartner MQ for Cloud Financial Management Tools. SaaS management is embedded within the broader Flexera One platform, which also covers ITAM and FinOps. Strong multi-source discovery (browser extension, CASB, agent, financial data). Positioned as a Leader in 2025.

**BetterCloud** - Pioneer in SaaS management. Moved from Visionary to Leader between 2024 and 2025. Strong in SaaS lifecycle management (provisioning, deprovisioning, automation). Has $35B+ in SaaS vendor contracts on the platform, enabling pricing benchmarks for nearly 70 market-leading apps. Focus on operational efficiency and security.

**Torii** - Founded 2017. Discovery-first approach. Launched agentic SaaS management capabilities in 2025, including AI-powered insights and support for Model Context Protocol (MCP). Evaluated in the 2025 Gartner MQ. Particularly relevant for organisations exploring how SaaS management intersects with AI agent workflows.

**SAP LeanIX SaaS Management** - Successor to Cleanshelf (acquired by LeanIX in 2021, subsequently integrated into SAP ecosystem). Natural fit for organisations already operating within SAP infrastructure. Provides SaaS governance with enterprise architecture context.

**Productiv** - SaaS Intelligence platform, known for deep feature-level usage analytics. Useful for renewal negotiations and demonstrating actual ROI. Note: Productiv was not among the 17 vendors evaluated in the 2025 Gartner Magic Quadrant.

**Other evaluated vendors (2025 MQ):** 1Password, Auvik, Axonius, Calero, CloudEagle.ai, Corma, Josys, Lumos, MegazoneCloud, ServiceNow, USU, Viio, Zluri.

### SMP selection criteria

When evaluating SMPs, assess against these dimensions:

- Discovery depth: How many discovery methods are supported? Can it detect shadow SaaS?
- Usage analytics granularity: Login-level only, or feature-level usage data?
- Financial integration: Does it connect to your expense management and AP systems?
- Contract management: Can it track renewal dates, notice periods, and terms?
- Security and compliance: Does it assess app security posture and flag risks?
- ITAM/SAM integration: Does it complement or replace existing ITAM tooling?
- Ecosystem fit: Does it integrate with your identity provider, CASB, and ITSM tools?
- Pricing benchmarks: Does the vendor have enough contract data to benchmark your pricing?
- Scale: Is it designed for enterprise (10,000+ employees) or mid-market?

---

## SAM Governance Model

### RACI between teams

SaaS management is inherently cross-functional. The FinOps Foundation notes that the scope of the FinOps team's involvement depends on organisational setup and the maturity of existing ITAM/SAM teams. On one end, FinOps teams manage SaaS end-to-end. On the other, they collaborate with established ITAM/SAM, Procurement, and Finance teams.

A typical RACI for SaaS management:

| Activity | FinOps | IT/SAM | Procurement | Finance | Security |
|---|---|---|---|---|---|
| Discovery and inventory | R | A | C | I | C |
| Cost allocation | R | C | I | A | I |
| License optimisation | R | A | C | I | I |
| Renewal negotiation | C | C | A | R | I |
| Security review | I | C | I | I | A |
| Shadow IT response | C | A | I | I | R |
| Contract management | C | I | A | C | C |
| Budget and forecasting | R | C | C | A | I |

R = Responsible, A = Accountable, C = Consulted, I = Informed. This is illustrative, not prescriptive. Organizations will differ.

### Crawl / Walk / Run maturity for SAM

| Indicator | Crawl | Walk | Run |
|---|---|---|---|
| SaaS inventory | Spreadsheet, updated quarterly | SMP with multi-source discovery | Continuous, automated, real-time |
| Spend visibility | Partial, found during audits | 80%+ of spend tracked | 95%+ allocated to cost centres |
| Shadow IT detection | Reactive (discovered by accident) | Periodic scans via SSO + finance | Continuous multi-signal detection |
| License optimisation | Manual, annual | Quarterly reviews, some automation | Automated reharvesting, tier rightsizing |
| Renewal management | Ad hoc, often missed | Centralised calendar, 60-day alerts | Data-backed review for every renewal |
| Governance | No formal policy | Approved app catalog exists | Fast-track procurement, automated provisioning |
| ITAM/FinOps alignment | Separate teams, no coordination | Regular collaboration meetings | Integrated practice, shared KPIs |

Always assess maturity before recommending solutions. A Crawl organisation needs a basic inventory before it can meaningfully optimise licenses. Recommending an enterprise SMP to a team that has never audited its SaaS estate is premature.

---

## Connection to AI Transition

SaaS management governance is a prerequisite for any serious AI integration strategy. The argument: if an organisation cannot answer "what SaaS tools are we running, what do they cost, and what business logic do they contain?" then it has no foundation for deciding what to replace, integrate, or retire when AI agents mature.

**Why this matters now:**

SaaS applications are, at their core, CRUD databases with embedded business logic. As AI agents become capable of operating across multiple systems and data sources, some of that business logic may migrate out of SaaS tools and into agent workflows. This does not mean SaaS is dead. It means SaaS without structure will not survive the era of agents.

**Practical implications for the transition period:**

- Organizations need full visibility into their current SaaS estate before making informed decisions about what to replace, integrate, or retire
- SaaS inventory data becomes an input to AI strategy: which tools contain business logic that could be displaced by agents? Which are data stores that agents will need to access?
- Torii's 2025 launch of MCP-compatible agentic capabilities signals the direction: SMPs themselves are becoming platforms for AI agent orchestration
- Until AI agents actually displace SaaS at scale (which may take years), organisations need the ability to know their current stack, control it deliberately, and evolve it with confidence

**Digital sovereignty (European context):**

For European organisations, SaaS governance intersects with sovereignty concerns. Who controls the infrastructure? Where does the data live? What happens when vendor pricing, policies, or geopolitics change? These are governance questions, not technical questions, and they require the same structured approach as cost optimisation.

**Environmental dimension:**

Always-on SaaS services, duplicated infrastructure across overlapping tools, and unnecessary compute cycles all carry an environmental cost. SaaS rationalisation - reducing the number of tools, consolidating redundant services, eliminating shelfware - has direct sustainability benefits. Digital efficiency and sustainability are increasingly the same conversation.

---

## Key metrics

| Metric | Description | Target |
|---|---|---|
| % of SaaS spend under management | Spend tracked and allocated vs. total SaaS spend | >90% |
| Number of discovered apps | Total apps in inventory, including shadow SaaS | Baseline, then trend |
| License utilization rate | Active users / allocated licenses | >85% |
| Shelfware rate | Unused licenses / total licenses | <15% |
| Renewal review coverage | Renewals reviewed before auto-renewal / total renewals | 100% for top-spend apps |
| Shadow SaaS ratio | Unmanaged apps / total apps | Decreasing quarter over quarter |
| Cost per employee (SaaS) | Total SaaS spend / headcount | Benchmark against industry |
| Redundant app count | Apps with overlapping functionality | Decreasing |
| Time to deprovision | Days between employee departure and SaaS access revocation | <1 day |
| Agent query cost ratio | Per-query agent costs / total SaaS spend | Monitor trend |
| Cost per agent outcome | Total agent query costs / business outcomes delivered | Establish baseline |

---

> Sources: FinOps Foundation (Licensing & SaaS capability; FinOps for SaaS scope; State of FinOps 2026),
> Gartner MQ for SaaS Management Platforms (July 2025), Halit Oener "The SaaSocalypse"
> (March 2026), Flexera 2025 State of Cloud Report, vendor documentation.

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
