---
name: finops-practice-operations
fcp_domain: "Manage the FinOps Practice"
fcp_capability: "Intersecting Disciplines"
fcp_capabilities_secondary: ["FinOps Practice Operations", "Governance, Policy & Risk", "Invoicing & Chargeback", "Budgeting"]
fcp_phases: ["Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Leadership", "Finance"]
fcp_personas_collaborating: ["Engineering", "Product", "Procurement", "ITAM"]
fcp_maturity_entry: "Crawl"
---

# FinOps Practice Operations

> How a FinOps practice is run: the operating model and where the team sits, a
> responsibility matrix across Engineering, Product, Finance, ITFM, Procurement and
> Leadership, the governance forums and their cadence, decision rights and escalation,
> and how FinOps works with each of those functions, with the ITFM interface as the
> most detailed case.

---

## Scope of this file

This file is about running the practice, not about any single capability it runs. It
answers who owns what, which meetings exist, what each one decides, and how FinOps
works with the functions around it. Two Framework capabilities meet here: **FinOps
Practice Operations** (building and running the team, the decision model) and
**Intersecting Disciplines** (working with ITFM, ITAM, SAM and the others), plus the
governance part of **Governance, Policy & Risk**.

The Framework's own background is in `finops-framework.md` (phases, maturity, the
State of FinOps placement data); the consultancy lens is in `optimnow-methodology.md`.
A per-capability scorecard is not covered yet.

| If the question is about | Go to |
|---|---|
| Chargeback design, ERP readiness, transfer pricing, dispute process | `finops-chargeback.md` |
| Showback cadence and allocation keys | `finops-allocation-showback.md` |
| Forecast method and re-forecast cadence | `finops-forecasting.md` |
| Commitment purchasing cadence and portfolio review | `finops-aws-commitments.md`, `finops-azure-commitments.md` |
| The AI Investment Council | `finops-ai-value-management.md` |
| Licences and BYOL (ITAM), SaaS estate and its RACI (SAM) | `finops-itam.md`, `finops-sam.md` |
| Tag policy and enforcement | `finops-tagging.md` |
| KPIs and the executive readout | `finops-kpis-benchmarking.md` |

---

## The operating model

### Centralise the rate, distribute the usage

The Framework's principles set the split that every operating model below implements.
"FinOps should be enabled centrally", and "rate, commitment, and discount optimization
are best centralized to take advantage of economies of scale". At the same time
"everyone takes ownership for their technology usage": accountability is "pushed to the
edge, with engineers taking ownership of costs from architecture design to ongoing
operations". (The older wording, "a centralized team drives FinOps", was replaced in
the 2025 Framework update; a central team enables, it does not drive every decision.)

In practice: the central function owns commitments, negotiated rates, the data, the
allocation model and the policies; workload owners own usage, rightsizing and
architecture choices. Google's FinOps guidance names the failure on the other side:
the central team becoming "the Cost Optimization Team", when optimisation is "always best
performed by the workload owners".

### Team models

The Framework recognises that the "FinOps team" takes several shapes, and the
Foundation's working-group paper on building FinOps teams (last updated December 2025)
sets out when each fits:

| Model | What it is | Fits | Watch for |
|---|---|---|---|
| **Central** | One team in one functional area | Any size; early adoption, or where control and alignment are needed | Becoming a bottleneck or the team that does everyone's optimisation |
| **Virtual** | A committee of members from the core personas, "often Finance and Engineering" | Start-up phase, before a funded team exists | No one has FinOps as their day job; actions stall between meetings |
| **Hub and spoke** | A central team plus members embedded in engineering or business units, often with a dotted line back to the hub | Medium to large organisations at medium to high maturity | "Confusion and duplication if boundaries are not well defined" |
| **Distributed** | Practitioners report into the business units | Large, complex estates | It "makes it harder to maintain central and consolidated visibility" |

A central team can get much of the reach of hub and spoke through **champions**: a
named person in each engineering team, overseen by the central team, acting "as a
liaison between distributed teams and the central FinOps hub". A monthly champions
forum (see below) is the cheapest way to keep them aligned.

The practice may not be called FinOps at all: a Technology Business Office, a Cloud
Business Office, a Cloud Centre of Excellence or a platform engineering team can host
it. AWS's Well-Architected guidance (COST01-BP01) lists the same homes and describes the
same three ownership models (centralised, decentralised, hybrid).

State of FinOps 2026 shares, and team sizes by spend band, are in
`finops-framework.md`, "FinOps organisational placement": centralised enablement is the
majority model and teams stay small even at large spend.

### Where it reports

The Framework says FinOps teams "tend to report to the executive who is responsible for
making technology selections and use successful", and that in organisations focused on
financial controls the CFO may lead it. The Foundation's team paper puts the trade-off
in two sentences: placing FinOps "too close to finance can reinforce the image of a
reactive cost-control function", while aligning it "too closely with technology can
weaken financial rigor". Two rules hold whichever line is chosen:

- **Place it centrally, not inside one business unit.** A FinOps team owned by a
  business unit is judged as partial by the others; the Foundation's executive guidance
  is explicit that business-unit positioning "inevitably leads to conflicts of interest".
- **Name an executive sponsor who will take escalations.** AWS calls sponsorship "a key
  success factor" and describes the sponsor as the escalation route that keeps cost work
  at the priority the organisation set. Without one, every cross-team decision becomes a
  negotiation.

### When a dedicated team is worth it

There is no agreed threshold. Microsoft's FinOps guidance says most organisations find a
team important "as they near $1 million in cloud spend per year" and also that "a
dedicated team is not for everyone"; Google's guidance argues for sizing by the
capabilities on the roadmap rather than by spend; the Foundation's team paper says the
right size "is less about hitting a particular ratio". Start with a virtual team and a
named lead, and fund dedicated roles when the forums below cannot keep up with the
decisions they are asked to take.

---

## Who does what: a responsibility matrix

The FinOps Foundation published a RACI in its earlier Framework and retired it in 2024,
in favour of activities listed per persona, so that the Framework stays usable "for a
20 person start-up without the need for imposing process (like RACI)". A matrix is still
the fastest way to settle ownership in a mid-size or large organisation. The one below
is a working template assembled from the Framework's persona activities, the FinOps and
ITFM paper, AWS Well-Architected (COST01, COST02) and Microsoft's FinOps and governance
guidance; it is not a Foundation standard. Adapt the rows, and keep one A per row.

R = responsible, A = accountable, C = consulted, I = informed. "Product / BU" is the
budget-holding product or business-unit owner; "ITFM" is IT finance where it is separate
from corporate Finance (where it is not, Finance takes its cells).

| Activity | FinOps | Engineering | Product / BU | Finance | ITFM | Procurement | Leadership |
|---|---|---|---|---|---|---|---|
| Tagging standard and cost dictionary | A, R | R (apply) | C | C | C | I | I |
| Exception to a tagging or cost policy | A | R (request) | C | I | I | - | I |
| Allocation and showback model | A, R | I | C | C | C | - | I |
| Chargeback execution (journals) | C (data and logic) | I | I | C | A, R | - | I |
| Budget setting | C | C | R | A | R | I | I (approves the total) |
| Forecast | R | C (drivers) | C | A | C | I | I |
| Anomaly response | A (process) | R | I | I (if material) | - | - | I (if material) |
| Rightsizing and waste removal | R (find, prioritise) | A, R (implement) | C | I | - | - | - |
| Commitment purchase (RIs, Savings Plans, CUDs) | A, R | C (usage plans) | C | C | I | C | I (above threshold) |
| Enterprise agreement and renewal | C (usage model) | C | C | C | I | A, R | I (signs above threshold) |
| Savings recognition | R (quantify) | I | I | C (confirms budget) | A | - | I |
| Unit economics (cost per business unit of value) | R (cost side) | C | A (value side) | C | C | - | I |
| FinOps staffing, scope and funding | R | - | - | C | - | - | A |

Three rows are where organisations and sources disagree most:

- **Commitment purchases.** AWS, Microsoft and Google guidance all recommend centralised
  purchasing by the FinOps function, with Finance as adviser on the use of capital
  (AWS COST01-BP02 casts Finance as "strategic advisors"). Some organisations require a
  joint Engineering and Finance sign-off, or put Procurement in charge. Pick one, and set
  the value above which Leadership approves.
- **Budgets.** Finance (or FP&A) is accountable in most sources; FinOps supplies the
  consumption forecast. A FinOps team that "owns the budget" ends up defending numbers it
  cannot control.
- **Rightsizing.** The workload owner implements and is accountable; FinOps finds and
  prioritises. Reversing this is the "central team does the optimisation" failure above.

The SaaS estate has its own matrix (FinOps, IT/SAM, Procurement, Finance, Security) in
`finops-sam.md`, "RACI between teams".

---

## Governance forums and cadence

The Framework's advice is to "try to use existing decision making and governance
mechanisms" before creating new meetings, and its Governance, Policy & Risk capability
asks for "governance cadences and reporting structures" that are reviewed with
Leadership. A forum earns its place only if it takes a decision; a review with no
decision is a report, and a report can be an email. A typical set, from the most
frequent to the least:

| Forum | Cadence | Chair | Attendees | Decides | Detail |
|---|---|---|---|---|---|
| Anomaly triage | Daily, or on alert | FinOps | Resource owner | Cause, owner, fix or accept | `finops-anomaly-management.md` |
| Variance checkpoint | Weekly | FinOps (or Finance) | Owners of the accounts that moved | Which variances need an owner's explanation; what escalates | AWS "weekly FinOps checkpoint" |
| Cost item in engineering reviews | Weekly or per change | Engineering lead | Engineers, champion | Cost impact of planned changes | AWS COST01-BP08, COST02-BP01 |
| FinOps monthly review | Monthly | FinOps | Engineering and product leads, Finance | Priorities for the optimisation backlog; forecast changes; items for steering | `finops-kpis-benchmarking.md` |
| Pre-close handoff to ITFM | Monthly, fixed date before close | FinOps and ITFM | FP&A as needed | Projected actuals, variance drivers, savings to recognise | "The ITFM interface" below |
| Commitment and contract review | Monthly or quarterly | FinOps | Finance, Procurement, Engineering | Buy, hold or exchange; renewal positions | `finops-aws-commitments.md` |
| Allocation and chargeback methodology review | Quarterly | FinOps | Finance (Controller), receiving teams | Changes to allocation keys; dispute rulings | `finops-chargeback.md` |
| AI Investment Council | Monthly or as needed | Business or technology executive | Product, Finance, FinOps, Engineering | Fund the next stage of AI initiatives | `finops-ai-value-management.md` |
| Steering committee | Quarterly; monthly in the first year | Executive sponsor, or the FinOps lead | Finance, Engineering and business leaders, Procurement | Targets, policies, decision rights, escalations, team scope and funding | Below |
| Champions forum | Monthly | FinOps | One champion per team | Nothing; shares practice and gathers feedback | Above |

**The steering committee.** Microsoft's FinOps guidance recommends "a virtual steering
committee" of "finance, business, and engineering teams" early on, chaired by the central
cost team where one exists, meeting "weekly or monthly", with the roles of each member
documented. Once the practice runs, quarterly is enough if the monthly review carries the
operating detail. What it is for: approving the policies and the RACI, setting targets,
settling escalations the monthly review could not, and deciding the team's scope and
funding (the Framework puts the last one with Leadership). Each meeting ends with
recorded decisions; the Framework's Executive Strategy Alignment capability suggests "a
lightweight decision log" and an action register.

**The variance checkpoint.** AWS describes the weekly checkpoint as "a process, not a
tool": the central team looks at the accounts or cost centres that moved, asks the owner
whether the increase "was planned and incorporated into your latest forecast", tracks
the answers, and escalates material ones. Set the materiality threshold on both the
percentage change and the annualised amount, so that a small team's doubling and a large
platform's small drift are both caught.

---

## Decision rights and escalation

The Framework's Executive Strategy Alignment capability asks Leadership to "define who can
approve spend changes, commit capacity, and accept cost, risk, and performance
tradeoffs". Write those down as thresholds, not names:

- **Spend changes.** Who can approve a budget overrun, at what amount, and when it goes to
  the steering committee.
- **Commitments.** Who can buy, up to what value and term, and what needs Finance or
  Leadership sign-off.
- **Policy exceptions.** Who can grant an exception to a tagging, region or size policy,
  for how long, and where it is recorded.
- **Escalation path.** Owner, then FinOps, then the owner's leadership, then the steering
  committee or the executive sponsor. Unresolved material variances follow the same path.

Where the platform can enforce a decision right, use it rather than a meeting:

- **Azure:** the Reservation Purchaser role lets a central team buy reservations for
  subscriptions it does not own, which makes centralised purchasing a permission rather
  than a convention. Azure Policy exemptions record a waiver with an expiry
  (`expiresOn`) and metadata such as who requested and approved it, which turns a policy
  exception into an auditable, time-boxed record.
- **AWS:** Budget Actions can run automatically or "require workflow approval", which
  puts an approval gate on the response to an overrun.

A documented example of a decision right on capacity rather than spend: Meta's product
teams review each feature before launch (James Kneeland and Joshua Louie, FinOps X 2026).
Capacity budgets are set per product area in a planning cycle and released in tranches;
a launch review tool turns the feature's measured business impact and capacity cost
(the method is the "Pricing a feature that is code" paragraph of the "Unit economics"
section in `finops-kpis-benchmarking.md`) into a simple return figure, and a reviewer close to the product makes one of
three calls: approve, defer to the next capacity tranche, or send back to optimise.
Strategic exceptions are allowed and recorded. Leadership allocates the budgets between
areas and does not rank features across areas whose business metrics are not comparable.
The speakers reported that company-wide launch freezes for capacity stopped once the
review was in place. For AI features, the funding side of the same gate is in
`finops-ai-value-management.md`.

A decision right that exists only in a slide deck is negotiated again at every incident.

---

## Working with each function

The Framework treats personas as "broad stakeholder groups that must collaborate, not
individual people". What each one needs from FinOps, what FinOps needs from it, and
where the two meet:

| Function | What it owns (Framework persona goal) | What FinOps gives it | What FinOps needs from it | Where they meet |
|---|---|---|---|---|
| **Engineering** | Delivering solutions that "balance cost, speed, and quality" | Cost data in the tools engineers already use, prioritised recommendations, central purchasing of commitments | Ownership of usage, action on recommendations, tags applied at deployment, usage forecasts | Anomaly triage, engineering reviews, champions forum |
| **Product / business** | Bringing products to market "with a predictable price point" | Cost per feature or customer, early cost estimates for go/no-go decisions | The value side of unit economics, demand forecasts, budget ownership | Monthly review, AI council, steering |
| **Finance (FP&A, Controller)** | Budgets, forecasts and reporting of technology cost | Consumption forecast, variance drivers, allocation data | The budget process, chart of accounts and cost centres, accounting treatment, approval of commitments as capital decisions | Monthly review, commitment review, methodology review |
| **ITFM / TBM** | Period-accurate, ledger-aligned reporting and chargeback execution | Attribution logic and data, pre-close forecast, quantified savings | Chargeback execution, savings recognition, the cost model and taxonomy | Pre-close handoff, methodology review |
| **Procurement** | Contracts and the value of vendor relationships | Usage models and forecasts for negotiation, renewal positions, commitment coverage | Contract terms, renewal and exit dates, early involvement before deadlines | Commitment and contract review |
| **Leadership** | Aligning technology investment with business objectives | Two or three numbers attached to a decision | Sponsorship, decision rights, funding, a seat in investment decisions | Steering committee |

Three working rules apply across the table:

- **Engineering engagement is the hardest of these.** The Foundation's engineering paper
  found "encouraging engineers to take action" to be the top FinOps challenge for 40% of
  its survey respondents (survey year not stated on the page); its tactics include making
  cost impact a field on the user-story template and naming a business owner and a
  technical owner per team. Put recommendations where engineers work (`finops-allocation-showback.md`,
  "Delivery") and give credit for avoided cost, not only realised savings.
- **Procurement needs FinOps before the deadline, not after it.** The Framework's
  Procurement persona stresses that "proactive engagement is essential before contract
  deadlines become imminent"; the Foundation's ITAM and procurement scenarios recommend a
  "deal desk" engagement before agreement renewals and marketplace commitments.
- **Finance and ITFM need one number.** Where ITFM exists, the handoffs below decide
  whether Leadership sees one figure or two.

---

## The ITFM interface

ITFM is the function where the handoffs are most defined, and where a missing interface
is most visible: two reports for the same period. The FinOps Foundation's paper on the
FinOps and ITFM intersection (June 2026, built on practitioner interviews from March and
April 2026) is the basis of this section.

### Two functions, two speeds

The paper frames the difference as one of speed and audience, not of competence:

| | FinOps | ITFM |
|---|---|---|
| Typical origin | "driven from Engineering" | "often originates from Finance" |
| Data | Near real-time cost and usage, attributed down to a workload, query, pipeline or token | Monthly, "aligned to budget periods, ledger close" |
| Output | Intelligence that Engineering, Product and Leadership act on now | Period-accurate, GL-aligned reporting and the journal entries in the official record |
| Question it answers | What is happening now | What happened in this period |

Two practical consequences:

- **ITFM is not Finance.** The paper places ITFM "between Finance and IT", and treats
  corporate Finance or FP&A as a separate function. A FinOps team that hands its
  numbers straight to FP&A has skipped the function that turns them into ledger entries.
- **ITFM has no single name.** The paper found it labelled IT Finance, Financial
  Operations, Business Finance Management, Technology Finance and Controlling, or
  Technology or IT Finance Partners, reporting to the CFO, the CIO, the CTO or a matrix. TBM
  is the more specific practice, used mainly "as a cost taxonomy and allocation
  methodology", most often through a vendor platform. Find out which of these the
  organisation has before designing a handoff.

When the two run in parallel without a defined interface, leadership sees two numbers
for the same period, savings that one side counts and the other does not, and
variance explanations that contradict each other. The paper's summary of the failure is
"parallel reports, disputed savings figures, and financial narratives that contradict
each other".

### The five intersection points

The paper names five points where the two functions meet, and says each "requires
defined ownership, a clear handoff process, and a minimum set of shared data":

| Intersection | FinOps | ITFM | Finance | Minimum shared data |
|---|---|---|---|---|
| **Savings recognition** | Quantifies and categorises the saving (cost avoidance or cost reduction) | Validates and formally recognises it in the cost model | Confirms it against the budget and removes it from the forward budget | Amount and type; affected cost category and period; the cost centre or service it is recognised against |
| **Chargeback and showback design** | Designs the attribution model and owns its data and logic | Executes the chargeback: journal entries to the GL and the financial consequences for each recipient | No role set in the paper | Cost centre or hierarchy code; service or product; application; period and amount; the allocation method, agreed before any chargeback is communicated |
| **Budget and forecast alignment** | Provides consumption trend, projected period-end actuals and variance drivers at a fixed point before close | Converts them into a budget range Finance can defend | Receives a range rather than a single figure | Projected consumption by category and period; assumptions; planned engineering actions that move the trend |
| **Variance decomposition** | Explains variance by workload, price movement and consumption pattern | Translates the explanation into budget and ledger terms | Acts on it | Price and volume components; whether each was planned; shared before close, not produced separately after it |
| **Terminology and tagging** | Agreed jointly; the paper sets no split for this point, but requires enforcement at deployment | Agreed jointly | Needs costs categorised for its own treatment (capitalisation eligibility, R&D) | The shared identifiers below and a shared service dictionary |

Three rules sit behind the table:

- **Attribution design and chargeback execution are different jobs.** FinOps
  provides "the data precision", ITFM "the financial authority". Organisations that
  merge the two roles, in the paper's words, "create an accountability gap".
- **A saving that never reaches the budget is not a saving.** "A saving that exists
  only in a FinOps report does not reduce a budget." Agree in advance how savings are
  categorised, who validates the arithmetic and who takes the amount out of the forward
  budget, or the same saving is claimed twice or lost.
- **Terminology comes first.** The paper calls it "the foundational intersection that
  makes all others possible". One case in the paper shows why: ITFM's and Finance's
  income statements diverged for months, and the cause was "different cost bucketing
  logic applied independently by each function to the same underlying costs", not bad
  data.

### The six shared identifiers

The paper found six identifiers in "every mature FinOps-ITFM operating model in this
research", and calls them the join keys that connect the two data sets without manual
reconciliation:

1. Cost centre or organisational hierarchy
2. Application or service identifier
3. Legal entity
4. Environment (production, development, test)
5. Project identifier
6. Owner

The Foundation's shorter key-takeaways page for the same paper lists seven, adding
service or product next to application; carry the six from the full paper as the
minimum and add product where the organisation's cost model has it.

In cloud billing data most of these arrive as tags, so they inherit every weakness of the
tagging programme. The paper's finding is blunt: "Where tagging is encouraged, coverage
remains inconsistent." Enforce the six at deployment, treating a missing identifier the
way an access-control failure is treated (`finops-tagging.md`). Standardising them against
FOCUS gives both functions one vocabulary for consumption data (`finops-focus.md`); the
paper reports lower reconciliation effort where organisations did so, without putting a
number on it.

### The bridge between the two functions

The paper's four practices, in the order an organisation tends to need them:

1. **Make the bridge permanent.** A role accountable to both domains, a joint
   operational review on a defined cadence, or a structured data handoff with a named
   owner on each side; "the form of the bridge matters less than its existence". One
   regional bank in the paper splits it by layer: FinOps owns the billing data at the
   back end, ITFM owns the executive chargeback presentation at the front.
2. **Agree the terminology and the identifiers first, then enforce them at deployment.**
   A shared service dictionary, a cost hierarchy and the minimum identifiers come before
   any shared report.
3. **Send FinOps forecast data to ITFM before period close, not after it.** The handoff
   date is fixed in the close calendar. The forecast is a range: the trajectory if
   current consumption continues, and what planned optimisation would achieve
   (`finops-forecasting.md`, "Cadence").
4. **Classify new consumption categories when the contract is signed.** Set the GL
   account type, cost category, service mapping and attribution fields in the purchasing
   process, not after spend has grown.

The fourth practice matters most for AI. The organisations the paper found best placed
had made AI "a distinguishable, attributable cost dimension at the point of contract or
procurement, before consumption scales", whatever the mechanism: a cost centre, an
internal order, a dimension in the ITFM tool or a contract clause. AI cost arrives in two
forms that need different handling: token cost inside a cloud or API bill, which can be
isolated, and token cost bundled into a software licence, which can only be separated if
the contract asks for separate line items (`finops-ai-value-management.md`,
`finops-sam.md`).

What not to do: draw a line that gives FinOps to operations and ITFM to Finance. A
practitioner quoted in the paper calls that "effectively a design for failure".

---

---

## Maturity markers

From the Framework capability pages for Practice Operations, Governance, Policy & Risk
and Intersecting Disciplines:

| Stage | Running the practice | Governance | Working with other disciplines |
|---|---|---|---|
| **Crawl** | A FinOps lead is named; virtual support rather than full-time hires; an initial staffing plan and budget; decision processes "immature" | "Governance is informal, with no regular cadence or structured communication" | Separate reporting structures; "coordination between disciplines takes place only when required" |
| **Walk** | The team "regularly reviews its needs, size, roles, and placement"; recurring decisions need "a more formal decision model" | "A regular review cadence exists" | A shared reporting structure; allied personas consulted regularly; renewal and exit accountability assigned at signature |
| **Run** | Champions extend the team; "a regular funding source"; a comprehensive, documented decision model | FinOps risk inputs are "incorporated into enterprise risk registers and management reporting" | Integrated teams; "a common data repository / source for the management of cost, usage, and context" |

A usable Walk test for the whole practice: every row of the responsibility matrix has a
named accountable person, the forums above each have a chair and a decision log, and
savings reach leadership only after ITFM or Finance has recognised them.

Measures worth tracking: the share of major technology decisions that went through the
agreed decision routine (the Executive Strategy Alignment capability calls this "decision
cadence coverage"), time to resolve anomalies, % unallocated, tag compliance, and "% of
costs aligned with the other standards" once the shared identifiers are agreed. Several
are already tracked in `finops-allocation-showback.md` and `finops-kpis-benchmarking.md`.

---

## The other intersecting disciplines

The Intersecting Disciplines capability names ITFM, ITAM or SAM, ITSM, IT security,
enterprise architecture, platform engineering, DevOps or SRE, and portfolio management,
and its statement adds sustainability. It is explicit that the point is coordination,
"not to define how FinOps teams should perform these other disciplines". Where the library
already covers the interface:

| Discipline | Where the interface is covered |
|---|---|
| ITAM (licences, BYOL, marketplace) | `finops-itam.md` |
| SAM (SaaS estate, renewals, its own RACI) | `finops-sam.md` |
| Sustainability | `greenops-cloud-carbon.md` |
| Platform engineering, DevOps and SRE | `finops-kubernetes.md`, `finops-tagging.md` (shift-left enforcement in `finops-framework.md`) |
| Procurement (a core persona rather than an intersecting discipline) | "Working with each function" above; `finops-sam.md` |

---

## Anti-patterns

| Anti-pattern | What happens | Instead |
|---|---|---|
| The central team does everyone's optimisation | A bottleneck, and engineers never own their usage | Central team finds and prioritises; workload owners implement |
| FinOps placed inside one business unit | Its numbers are read as partial by the other units | Central placement with an executive sponsor |
| A committee with no decision rights | Meetings that report but cannot decide; escalations go nowhere | Written decision rights and thresholds, a decision log |
| A dashboard with no forum behind it | Data nobody acts on | Every report tied to a forum that takes a decision |
| Each business unit buys its own commitments | Overlapping coverage, lost economies of scale | Centralised purchasing, enforced by permissions where possible |
| Procurement engaged at the renewal deadline | No leverage and no usage model | Commitment and contract review months ahead |
| Two reports for the same period (FinOps and ITFM) | Leadership stops trusting both | One set of identifiers, a pre-close handoff, one recognised figure |
| FinOps reports savings straight to leadership | The saving is disputed or counted twice | Savings recognition through ITFM and Finance |
| Tagging "encouraged" rather than enforced | The join keys are missing on the rows that matter | Enforcement at deployment |
| AI spend classified after it scales | Token cost buried in licences and general IT overhead | Classification at contract time |

---

## See also

- `finops-framework.md` - the 22 capabilities, maturity, State of FinOps placement data
- `finops-chargeback.md` - chargeback design, Finance roles, dispute process
- `finops-allocation-showback.md` - showback cadence and delivery into engineering tools
- `finops-forecasting.md` - the forecast behind the pre-close handoff
- `finops-kpis-benchmarking.md` - KPIs and the executive conversation
- `finops-ai-value-management.md` - the AI Investment Council
- `finops-sam.md` - the SaaS management RACI

## Sources

FinOps Foundation (Framework pages are licensed CC BY 4.0):

- Principles: <https://www.finops.org/framework/principles/>; 2025 Framework update:
  <https://www.finops.org/insights/2025-finops-framework/>
- Capabilities: FinOps Practice Operations
  (<https://www.finops.org/framework/capabilities/finops-practice-operations/>),
  Governance, Policy & Risk (<https://www.finops.org/framework/capabilities/governance-policy-risk/>),
  Executive Strategy Alignment (<https://www.finops.org/framework/capabilities/executive-strategy-alignment/>),
  Intersecting Disciplines (<https://www.finops.org/framework/capabilities/intersecting-disciplines/>);
  personas: <https://www.finops.org/framework/personas/>
- Retired Decision & Accountability page, with the former RACI:
  <https://www.finops.org/framework/previous-capabilities/decision-accountability-structure/>
- "Building FinOps Teams: Roles, Structures, Career Paths":
  <https://www.finops.org/wg/building-finops-teams-roles-structures-career-paths/>;
  "What is a FinOps Champions Program?": <https://www.finops.org/wg/what-is-a-finops-champions-program/>;
  "FinOps Enabled Executive": <https://www.finops.org/insights/finops-executive-technology-leader/>
- "Encouraging Engineers to Take Action": <https://www.finops.org/wg/encouraging-engineers-to-take-action/>;
  "FinOps & ITAM Practical Scenarios: Planning & Procurement":
  <https://www.finops.org/wg/finops-itam-practical-scenarios-planning-procurement/>
- "How FinOps & ITFM Are Intersecting" (4 June 2026, CC BY 4.0):
  <https://www.finops.org/wg/finops-itfm-intersection/>; key takeaways:
  <https://www.finops.org/wg/key-takeaways-finops-itfm-intersection/>;
  "FinOps & TBM: Navigating Co-Existing Disciplines" (survey of 2022):
  <https://www.finops.org/wg/finops-tbm-navigating-coexisting-disciplines/>

Cloud providers:

- AWS Well-Architected, Cost Optimization pillar, COST01 "Practice Cloud Financial
  Management" and COST02:
  <https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/practice-cloud-financial-management.html>;
  "Improve Your Monthly Cloud Variance Analysis with a Weekly FinOps Checkpoint" (30 July 2026):
  <https://aws.amazon.com/blogs/aws-cloud-financial-management/improve-your-monthly-cloud-variance-analysis-with-a-weekly-finops-checkpoint/>
- Microsoft FinOps, practice operations:
  <https://learn.microsoft.com/en-us/cloud-computing/finops/framework/manage/operations>;
  Reservation Purchaser role:
  <https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/view-reservations>;
  Azure Policy exemptions:
  <https://learn.microsoft.com/en-us/azure/governance/policy/concepts/exemption-structure>
- Google Cloud, "Getting started with FinOps on GCP" (2021):
  <https://services.google.com/fh/files/misc/cloud_finops_getting_started.pdf>

Lead: Dean Oliver, FinOps Foundation, "FinOps + ITFM: One Version of the Truth, Two
Speeds of Value", FinOps X 2026 (YouTube, uploaded 21 August 2026). All sources read
19 October 2026.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
