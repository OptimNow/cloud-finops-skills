---
name: finops-practice-operations
fcp_domain: "Manage the FinOps Practice"
fcp_capability: "Intersecting Disciplines"
fcp_capabilities_secondary: ["FinOps Practice Operations", "Invoicing & Chargeback", "Budgeting"]
fcp_phases: ["Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Finance"]
fcp_personas_collaborating: ["Leadership", "ITAM", "Procurement", "Engineering"]
fcp_maturity_entry: "Walk"
---

# FinOps Practice Operations

> How a FinOps practice works alongside the functions that already own part of the
> technology cost picture, starting with IT Financial Management (ITFM) and TBM: the
> five handoffs where the two meet, who owns each side, the shared identifiers that let
> their numbers reconcile, the bridge that keeps them aligned, and the maturity markers
> for each stage.

---

## Scope of this file

This file starts with the part of practice operations that most often decides whether
FinOps numbers are trusted outside the FinOps team: the interface with the disciplines
next to it. It covers the FinOps Framework's **Intersecting Disciplines** capability,
with ITFM as the first and fullest case, and points to the files that already cover the
other allied disciplines.

What a FinOps team does internally (team models, staffing, the decision model,
stakeholder adoption) is the **FinOps Practice Operations** capability; its framing is
in `finops-framework.md` and the consultancy lens in `optimnow-methodology.md`. The
three-cadence operating model and the per-capability scorecard planned for this file
are recorded in `docs/ROADMAP.md` and will be added when an engagement needs them.

| If the question is about | Go to |
|---|---|
| Designing chargeback, ERP readiness, transfer pricing, audit trail | `finops-chargeback.md` |
| Forecast method, accuracy and drift, re-forecast cadence | `finops-forecasting.md` |
| Licences, BYOL and marketplace (ITAM), SaaS estate (SAM) | `finops-itam.md`, `finops-sam.md` |
| Carbon and sustainability reporting | `greenops-cloud-carbon.md` |
| Tag policy and enforcement | `finops-tagging.md` |
| The shared cost schema | `finops-focus.md` |

---

## Two functions, two speeds

The FinOps Foundation's paper on the FinOps and ITFM intersection (June 2026, built on
practitioner interviews from March and April 2026) frames the difference as one of
speed and audience, not of competence:

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

---

## The five intersection points

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

---

## The six shared identifiers

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

---

## The bridge between the two functions

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

## Maturity markers

The Framework's Intersecting Disciplines capability (page updated 15 September 2026)
describes the stages:

| Stage | Markers |
|---|---|
| **Crawl** | FinOps and the other teams report through separate structures; "coordination between disciplines takes place only when required"; renewal and exit ownership is undefined until a contract nears expiry |
| **Walk** | FinOps and the intersecting discipline share a reporting structure; allied personas are consulted regularly for decisions (for example SAM on BYOL); renewal, exit and consumption accountability are assigned at signature |
| **Run** | The teams are integrated or work in one organisation; "a common data repository / source for the management of cost, usage, and context" serves every discipline; accountability is monitored continuously, triggering renegotiation or exit before the contract anniversary |

For the ITFM interface specifically, a usable Walk test: the five intersection points
each have a named owner on both sides, the pre-close handoff date is in the close
calendar, and savings are reported only once ITFM has recognised them.

The capability lists "% of costs aligned with the other standards", tag compliance and
% unallocated among its measures. The last two are already tracked in
`finops-allocation-showback.md` and `finops-kpis-benchmarking.md`; the first is the one
to add once the shared identifiers are agreed.

---

## The other intersecting disciplines

The capability names ITFM, ITAM or SAM, ITSM, IT security, enterprise architecture,
platform engineering, DevOps or SRE, and portfolio management, and its statement adds
sustainability. It is explicit that the point is coordination, "not to define how FinOps
teams should perform these other disciplines". Where the library already covers the
interface:

| Discipline | Where the interface is covered |
|---|---|
| ITAM (licences, BYOL, marketplace) | `finops-itam.md` |
| SAM (SaaS estate, renewals) | `finops-sam.md` |
| Sustainability | `greenops-cloud-carbon.md` |
| Platform engineering, DevOps and SRE | `finops-kubernetes.md`, `finops-tagging.md` (shift-left enforcement in `finops-framework.md`) |
| Procurement (a core persona rather than an intersecting discipline) | `finops-chargeback.md`, `finops-sam.md` |

---

## Anti-patterns

| Anti-pattern | What happens | Instead |
|---|---|---|
| Two reports for the same period | Leadership stops trusting both | One set of identifiers, a pre-close handoff, one recognised figure |
| FinOps reports savings straight to leadership | The saving is disputed or counted twice | Savings recognition handoff through ITFM and Finance |
| One team designs and executes chargeback | Accountability gap; disputes have no owner | FinOps owns the attribution logic, ITFM the journal entries |
| Each function buckets costs its own way | Statements diverge for months | Shared service dictionary and cost hierarchy, agreed first |
| Tagging "encouraged" rather than enforced | The join keys are missing on the rows that matter | Enforcement at deployment |
| AI spend classified after it scales | Token cost buried in licences and general IT overhead | Classification at contract time |

---

## See also

- `finops-chargeback.md` - chargeback design, Finance roles, ERP readiness
- `finops-forecasting.md` - the forecast that feeds the pre-close handoff
- `finops-kpis-benchmarking.md` - realised versus potential savings
- `finops-framework.md` - the 22 capabilities, including Practice Operations
- `finops-focus.md` - the shared cost and usage schema

## Sources

- FinOps Foundation, "How FinOps & ITFM Are Intersecting" (last updated 4 June 2026,
  CC BY 4.0): <https://www.finops.org/wg/finops-itfm-intersection/>; key takeaways:
  <https://www.finops.org/wg/key-takeaways-finops-itfm-intersection/>
- FinOps Framework capability, Intersecting Disciplines (updated 15 September 2026):
  <https://www.finops.org/framework/capabilities/intersecting-disciplines/>
- FinOps Framework capability, FinOps Practice Operations:
  <https://www.finops.org/framework/capabilities/finops-practice-operations/>
- FinOps Foundation, "FinOps & TBM: Navigating Co-Existing Disciplines" (survey of
  2022): <https://www.finops.org/wg/finops-tbm-navigating-coexisting-disciplines/>
- Lead: Dean Oliver, FinOps Foundation, "FinOps + ITFM: One Version of the Truth, Two
  Speeds of Value", FinOps X 2026 (YouTube, uploaded 21 August 2026)

All read 19 October 2026.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
