---
name: finops-forecasting
fcp_domain: "Quantify Business Value"
fcp_capability: "Forecasting"
fcp_capabilities_secondary: ["Budgeting", "Planning & Estimating"]
fcp_phases: ["Inform", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Finance"]
fcp_personas_collaborating: ["Engineering", "Product", "Leadership", "Procurement"]
fcp_maturity_entry: "Crawl"
---

# FinOps Forecasting

> How to build, measure and run a technology spend forecast that holds: the
> difference between an estimate, a forecast and a budget, the cost basis to
> forecast on, the FinOps Foundation's three forecast measures and the variance
> bands by maturity, the trend-to-driver method ladder, a re-forecast cadence
> driven by business changes rather than the calendar, and scenario forecasting
> for AI and other volatile workloads. Entry maturity is Crawl: a manual forecast
> is a legitimate start, provided it is measured.

---

## Scope and routing

This file owns the forecasting method, how a forecast is measured, and how often
it is re-cut. Neighbouring files own the decisions a forecast feeds:

| Question | Where it lives |
|---|---|
| Forecasting a new workload before it exists (intake estimate, 12-month forecast document, the 60-90 day forecast-then-commit rule) | `finops-onboarding-workloads.md` |
| How much to commit, and the keel below which no forecast is needed | `finops-aws-commitments.md`, `finops-azure-commitments.md` |
| Budget alerts and forecast-based alerts in each provider's tooling | `finops-anomaly-management.md`, `finops-aws.md` (AWS Budgets and early controls), `finops-azure.md` |
| Forecast variance as a KPI, and carrying it into the executive conversation | `finops-kpis-benchmarking.md` |
| AI business cases, incremental funding and stage gates | `finops-ai-value-management.md` |
| Current prices behind a forecast's unit costs | the AI Pricing Hub (<https://optimtoken.optimnow.io>); never a figure copied into a reference |

---

## Estimate, forecast and budget are three different numbers

The FinOps Framework keeps them in three capabilities, and a practice that blurs
them loses the signal each one carries.

- **Estimate** (Planning & Estimating): "estimation and exploration of potential
  cost and value", made before the change exists. The Foundation calls it
  "exploratory ideation" and states that estimates "will be an input to
  Forecasting".
- **Forecast** (Forecasting): "a model of the anticipated future cost and value of
  IT systems", built with statistical methods from "historical spend patterns,
  planned changes, and related metrics".
- **Budget** (Budgeting): the "process for setting limits, monitoring, and
  managing technology spending". The budget is the limit; the forecast is the
  best current view of where spend will land against it.

Two consequences. A budget re-cut to match actuals is a forecast with a
governance label, and the variance it reports is zero by construction. And at
Crawl the Foundation describes a budget "set at approval and reconciled against
actuals after the fact": there is no forecast in that loop at all, which is why
the first Crawl step is to produce one, however rough, and start measuring it.

---

## Forecast on amortised, discount-adjusted cost

The Foundation's first measure of success for Forecasting is that forecast models
use "discount-adjusted, amortized usage data". Billed cost carries the
timing of upfront commitment purchases, credits and refunds: forecast it and the
model predicts purchase dates, not consumption. In a FOCUS dataset the column is
`EffectiveCost`; the difference from `BilledCost` is covered in
`finops-allocation-showback.md`.

Three rules follow:

- **One cost basis and one currency** across every team's forecast, fixed before
  forecasts are delegated (the "normalise before you delegate" step in the
  five-minute budget example in `finops-kpis-benchmarking.md`).
- **Forecast the committed floor separately.** Spend covered by existing
  commitments is known for the rest of their term; forecast error lives in the
  uncovered part above it. The keel concept in the commitments files is the same
  split seen from the purchasing side.
- **Forecast usage as well as spend.** A spend forecast that lands on target while
  usage overshoots means a price or discount moved underneath it, and the next
  rate change exposes the gap. The Foundation measures both for this reason (next
  section).

---

## Measuring a forecast

The Forecasting capability names three KPIs, each computed per period (day, month
or quarter):

| Measure | Formula (as published by the Foundation) | What it tells you |
|---|---|---|
| Forecast Accuracy Rate (Spend) | (forecasted spend - actual spend) / forecasted spend | How close the forecast landed on cost |
| Forecast Accuracy Rate (Usage) | (forecasted usage - actual usage) / forecasted usage, on resource units such as vCPUs or memory | Whether the consumption model holds independently of price |
| Forecast Drift Rate | (new forecast - previous forecast) / previous forecast | How much the forecast moved before the period closed |

The page adds a fourth for emissions, built the same way (see
`greenops-cloud-carbon.md` for the carbon data it needs).

**Read accuracy and drift together.** A forecast re-cut the week before month end
will score well on accuracy and badly on drift: report only accuracy and the
practice rewards late re-forecasting. Drift is also the honest name for the most
common failure, which is not a single large miss but small changes (a vendor
price, a volume shift, a new feature) that are each immaterial and together move
the landing point.

**The formulas are signed.** Positive means actual landed below the forecast,
negative means it landed above. Report the signed figure per owner, and the
absolute value against the band.

**Measure at the level owners act on.** Errors of opposite sign cancel in a sum,
so an estate total can land inside the band while most teams miss theirs. Compute
accuracy per team or product first, and treat the estate figure as a summary, not
the measure.

**Variance bands by maturity.** The Forecasting page sets no number; it asks for
cost "within established percentage threshold of variance", set by the
organisation. The Budgeting capability does set ceilings for budget against
actual spend: a maximum of 20% at Crawl, 15% at Walk and 12% at Run. Use those as
the maturity gate. `finops-kpis-benchmarking.md` holds forecast variance to a
mid-single-digit band once a practice reports to an executive room, which is
stricter than the Foundation's Run ceiling and is this library's working bar for
executive trust, not a Foundation figure.

---

## Methods by maturity: trend first, drivers next

| Stage | Foundation description | What it takes in practice |
|---|---|---|
| Crawl | Forecast models "created manually and/or ad-hoc"; variance analysis "done manually". Budgeting cycle "annual to match other IT budget cycles" | A run-rate forecast per top-level owner from recent amortised cost, plus a written list of known changes. Measured monthly, by hand |
| Walk | Forecast models "rolling and trend-based"; updates "on a regular cadence but not automated". Budgeting cycle a hybrid of annual and shorter cycles for dynamic systems | A rolling trend forecast by service and owner, with the commitment portfolio overlaid and a monthly re-forecast |
| Run | Forecast models "a combination of rolling, trend-based, and driver-based". Budgeting cycle "short (rolling quarterly) with a consistent and automated approach to collecting forecasts" | Driver-based models for the products that carry most of the spend, trend for the long tail, forecasts collected automatically from owners |

**Trend against driver.** A trend model extrapolates the estate's own history. It
is right while nothing changes and wrong at every launch, migration, price change
or commitment purchase. A driver model writes cost as a business volume times a
unit cost (orders x cost per order, active users x cost per user, tasks x tokens
per task x price per token), so when spend moves, the forecast says whether volume
or unit cost moved it. That is also why driver-based forecasting needs the unit
metrics in `finops-kpis-benchmarking.md` before it can start, and why
`finops-allocation-showback.md` puts allocation first: cost that cannot be tied to
an owner or a unit has no driver.

Run both once a driver model exists. The gap between the trend forecast and the
driver forecast is the list of planned changes, and a gap nobody can explain is a
question for the product owner before it becomes a variance.

**Provider forecasts are a baseline, not a model.** AWS Cost Explorer, Azure Cost
Management and Google Cloud budgets all produce a forecast and can alert on it.
They project from the account's own history, so they cannot see a planned launch,
a migration or a price change. Use them as the Crawl and Walk baseline and as an
early warning (the forecast-triggered controls are in `finops-aws.md` and
`finops-anomaly-management.md`), and keep the drivers in the practice's own model.

---

## Cadence: re-forecast from drivers, not from the calendar

The Foundation's measures of success include a "forecast frequency that includes
intermediate forecasts to update budgets based on business drivers", and the
Budgeting page asks for a "budget cadence that includes rolling forecasts". The
calendar is not the trigger; a change in a driver is.

One operator's version of this, presented at FinOps X 2026 by Aishwarya Korde
(FastBridge Fiber), calls it a living forecast: driver changes (a vendor price, a
production or build rate, a volume shift) are folded in at least weekly, so the
forecast answers "where will we land on what we know today?" rather than "did we
meet the budget?". The questions carried upward change with it:

- Is forecast drift shrinking from cycle to cycle?
- Is unit cost stable, and if not, which driver moved it?
- Is variance against the band shrinking?
- Are decisions being taken earlier than they were a quarter ago?

This describes one organisation's practice; no comparative data was presented,
and the published recording carries machine-translated captions only, so this
summary paraphrases the talk rather than quoting it.

A weekly re-cut is not a weekly re-plan. Keep the budget fixed for its cycle, move
the forecast, and report the gap between the two; that gap is the signal.

**Re-forecasting through a structural change.** A divestiture, a migration programme
or an acquisition changes the assumptions under the forecast faster than any cadence.
In one corporate split, the cloud forecast was rebuilt about 10 times in 12 months and
the separation timeline moved from roughly 18-20 months to 9, because the answers to
"which company gets this application, is it cloned or moved, does it stay on-premises,
when does it move" kept changing (Ashley Hromatko, Medium, 20 October 2026; full citation in
`finops-onboarding-workloads.md`, "Divestiture and separation"; the figures are that
company's). Two practices follow. Model the change as scenarios keyed to those
assumptions, so a changed answer re-runs a scenario instead of rebuilding the forecast;
this works only when the application inventory behind the assumptions is reliable. And
present the output as a range with its driving assumptions, so leaders see the cost of
each decision rather than a single number that will move again.

Where an ITFM or TBM function owns period close, the forecast also has a fixed
delivery date: projected period-end actuals, variance drivers and the planned actions
behind them reach ITFM before close, not after it, so it can present Finance with a
defensible range (`finops-practice-operations.md`, "The five intersection points").

---

## Volatile and AI workloads: forecast scenarios, not a number

AI spend breaks the assumptions a trend model rests on. Volume grows in steps
with adoption, not along a line. Unit cost moves with model choice, prompt and
context length, retries and agent loop depth even at constant traffic (the
mechanics are in `finops-for-ai.md` and `finops-agentic.md`). And list prices
change between budget cycles. A single-number AI forecast will be wrong; the
useful question is in which direction and by how much.

The Planning & Estimating capability at Run asks for estimates "with an explicit
range and confidence level", and for "estimating scenarios" that support rolling,
trend-based and driver-based models. A practical shape for an AI line, presented
at FinOps X 2026 by Janine Pickard-Green (MagicOrange):

| Scenario | Assumptions to write down beside it |
|---|---|
| Base | Current token volume, stable demand, current model mix |
| Expected | Planned adoption: users or use cases added this period, at the current cost per task |
| Aggressive | Agentic workloads: concurrency, retries, longer contexts and deeper loops on top of expected adoption |

Run a rolling 90-day forecast across the three as the management instrument, and
keep the annual budget as the guardrail. When the 90-day lands outside its band,
re-forecast with the guardrails tightened rather than cutting the line: a cut
taken before anyone knows which driver moved tends to remove the use case that was
working. The scenario names and the 90-day cadence are that speaker's practice;
the range-and-confidence requirement is the Foundation's.

The scenarios need a driver underneath them, and the right driver differs by use
case. Palo Alto Networks forecasts each class of AI spend from a different one
(Abhinav Lad and Kuntal Patel, FinOps X 2026):

| AI use case | Forecast driver | What breaks a trend model |
|---|---|---|
| AI embedded in a revenue-generating product | AI cost as a share of that product's revenue | Nothing new: capacity behaves like other compute and takes commitments |
| AI coding and productivity tools | Adoption rate per business unit x a cost-per-user target, with a separate power-user tier | Pilot cost is near zero and sandbox cost is noise, then spend steps up on the day security, legal and governance clear general access; forecast that date as a step, not a trend |
| Internal enterprise assistants | Volume: users first, then tickets or requests handled | Usage follows the process the assistant serves, not the headcount |

Adoption differs widely between business units (in their case, about 90% in one
engineering team and 22% in another function; the speakers' figures), so a single
company-wide adoption rate misforecasts both ends. The drivers are that company's
practice, not a Foundation standard.

Two links into the rest of the library. A provisioned or reserved AI capacity
commitment should be sized on the post-spike baseline, never during a surge (the
rule is in `finops-genai-capacity.md`). And the people who build, evaluate and run
the AI line belong in its forecast: the total-cost checklist in `finops-for-ai.md`
lists them, and `finops-ai-value-management.md` funds AI work incrementally for
the same reason a single number fails here.

---

## When a forecast misses

Classify the miss before acting on it, because each class has a different owner:

| Miss | Signature | Owner and next step |
|---|---|---|
| Volume | Unit cost on plan, volume off | Product owner: update the driver and the scenarios |
| Unit cost | Volume on plan, cost per unit off | Engineering and FinOps: rate change, efficiency regression, model or architecture change |
| Event | A spike or step on specific days | Anomaly management (`finops-anomaly-management.md`); keep it out of the trend baseline, keep it in the variance record |
| Plan | A launch or migration nobody forecast | The intake gate (`finops-onboarding-workloads.md`): the change reached production without an estimate |

The classification is a working method, not a Foundation standard. Its use is
that a variance report which names the class tells the room who acts, where a
report that names only the amount starts a search for someone to blame.

---

## Anti-patterns

- **Forecasting billed cost.** The model forecasts commitment purchase dates and
  credits, not consumption.
- **Reporting accuracy at the estate total only.** Team errors cancel in the sum
  and the practice looks better than any single forecast in it.
- **Accuracy without drift.** A forecast re-cut just before month end scores well
  on accuracy and hides how late the practice learned where it would land.
- **The budget as the forecast.** Re-cutting the budget to actuals reports zero
  variance and removes the signal.
- **A single-number AI forecast.** Use the three scenarios with their written
  assumptions.
- **Forecasting before allocation.** Without an owner and a unit, a forecast has
  no driver and no one to explain the variance.
- **Annual-only cycles for dynamic spend.** The Foundation's own Walk stage
  already moves dynamic systems to shorter cycles.

---

## See also

- `finops-kpis-benchmarking.md` - forecast variance as a KPI, unit metrics, the
  five-minute budget and the executive conversation
- `finops-onboarding-workloads.md` - forecasting at intake and the 60-90 day
  forecast-then-commit rule
- `finops-aws-commitments.md`, `finops-azure-commitments.md` - the keel and
  commitment sizing on top of a forecast
- `finops-anomaly-management.md` - forecast-triggered alerts and the event class
  of forecast miss
- `finops-ai-value-management.md` - AI business cases, incremental funding and
  budgets per AI project
- `finops-allocation-showback.md` - `EffectiveCost` against `BilledCost`, and why
  allocation comes first

Sources: FinOps Foundation capability pages for Forecasting
(<https://www.finops.org/framework/capabilities/forecasting/>), Budgeting
(<https://www.finops.org/framework/capabilities/budgeting/>) and Planning &
Estimating (<https://www.finops.org/framework/capabilities/planning-estimating/>),
all read 16 October 2026. Practitioner accounts: Aishwarya Korde (FastBridge
Fiber), "Why FinOps Needs Forecasts That Actually Hold"
(<https://www.youtube.com/watch?v=870i5zAbFv4>), and Janine Pickard-Green
(MagicOrange), "Your AI Forecast Is Lying: ITFM Lessons"
(<https://www.youtube.com/watch?v=_vce-4Gisxg>), FinOps X 2026, both viewed 16
October 2026.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
