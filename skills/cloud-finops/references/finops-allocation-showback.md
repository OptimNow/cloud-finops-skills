---
name: finops-allocation-showback
fcp_domain: "Understand Usage & Cost"
fcp_capability: "Allocation"
fcp_capabilities_secondary: ["Reporting & Analytics", "Budgeting"]
fcp_phases: ["Inform"]
fcp_personas_primary: ["FinOps Practitioner"]
fcp_personas_collaborating: ["Engineering", "Finance"]
fcp_maturity_entry: "Crawl"
---

# FinOps Allocation and Showback

> Allocation is the FCP capability that turns billing data into team-level
> cost visibility. Showback is the first delivery vehicle on top of allocation:
> teams see their costs, build awareness, and start to act on them - without
> any financial accountability flowing yet. Both are prerequisites for
> chargeback (`finops-chargeback.md`).
>
> This file covers the allocation methodology that has to be in place before
> any chargeback discussion is meaningful, and the showback delivery model
> that earns the upgrade to chargeback.

---

## Why allocation comes before everything else in FinOps

A workload you cannot attribute to a team is a workload you cannot optimise,
forecast, govern, or charge for. Every other FinOps capability assumes
allocation is in place:

- Rightsizing recommendations have no owner without allocation
- Commitment discount coverage targets are meaningless without consumption
  attribution
- Forecasting has no driver if cost cannot be tied to a unit (team, product,
  feature)
- Anomaly investigation stalls at "whose workload is this?"
- Chargeback is impossible by definition

Allocation is the upstream dependency. `finops-tagging.md` covers the
prerequisite for allocation (the tags themselves). This file covers what to do
with the tags once they exist - turning per-resource tagging into per-team
cost views that survive Finance scrutiny.

---

## Cost-column methodology

The single most common allocation error in the field is using the wrong cost
column. FOCUS makes the choices explicit; AWS-native exports require some
translation.

### FOCUS cost columns

| Column | What it includes | Use for |
|---|---|---|
| **`BilledCost`** | Cash-basis: what the provider invoices for that period. Reservation purchases land as a Purchase row in their billing month, not amortised across the term. | Invoice reconciliation against `InvoiceId` |
| **`EffectiveCost`** | All discounts applied, prepaid commitments amortised across the consumption period (accrual basis). | Showback, chargeback, trend analysis, team attribution |
| **`ListCost`** | List rate × Pricing Quantity, no discounts. | Measuring rate-optimisation savings |
| **`ContractedCost`** | Negotiated rate × Pricing Quantity, before commitment discounts. | Measuring commitment-specific savings |

> **Note on FOCUS adoption**: As of March 2026, FOCUS v1.2 is available for AWS and Azure, v1.0 for GCP and Oracle, with newer providers like Vercel, Grafana Cloud, Redis, and Databricks also supporting various FOCUS versions. This expanded ecosystem significantly simplifies multi-cloud allocation by providing consistent cost columns across providers.

**Use `EffectiveCost` for allocation.** Allocation is an accrual concept: a
workload that consumes 10% of cluster capacity in March should be allocated
10% of the cluster's cost for March, even if the cluster runs on a Reservation
that was paid in full in January. `BilledCost` would attribute a $1M annual
prepay entirely to whoever consumed the first kilowatt-hour after the
purchase.

### Mapping to AWS legacy cost columns

The most common point of confusion is the AWS-native vocabulary, which
predates FOCUS and uses different terms.

| FOCUS column | AWS legacy column | Cost Explorer view |
|---|---|---|
| `EffectiveCost` | `line_item_amortized_cost` | "Amortized" |
| `BilledCost` | `line_item_unblended_cost` | "Unblended" |
| `ListCost` | (no direct column - compute as `pricing_public_on_demand_cost`) | n/a |
| `ContractedCost` | (no direct column - compute from EDP / private pricing rate sheet) | n/a |

**Avoid `blended_cost` (AWS) for allocation entirely.** Blended cost is a
payer-account averaging artefact: it averages Reservation-discounted rates
across all linked accounts that consumed the same instance type, regardless
of which account actually owns the Reservation. FOCUS deliberately has no
equivalent column because the concept is misleading - it does not reflect
either invoice reality (use `BilledCost`) or true accrual attribution
(use `EffectiveCost`). Teams that allocate on `blended_cost` discover the
error the first time a controller asks "why does our Reservation appear to
discount another team's spend?"

If your billing pipeline only exposes one cost column, configure it to surface
the amortised view (Azure: amortized cost export; AWS: Cost Explorer amortised
view or CUR `line_item_amortized_cost`; GCP: BigQuery export's amortised cost
columns). FOCUS-conformant exports surface both `EffectiveCost` and
`BilledCost` natively. With the expanded FOCUS ecosystem (AWS v1.2, Azure v1.2,
GCP v1.0, and newer providers supporting various versions), organisations can
increasingly rely on FOCUS exports as their primary data source for multi-cloud
allocation, reducing the complexity of maintaining provider-specific mappings.

### Reconcile to invoice via `InvoiceId`

The sum of `BilledCost` for a given `InvoiceId` must match the corresponding
provider invoice to the penny. Use this as the integrity check on the
allocation pipeline:

- Run a monthly reconciliation: `SUM(BilledCost) GROUP BY InvoiceId` against
  the invoice line items
- Any drift > 0.5% is a data-quality issue worth investigating before it
  compounds
- Showback to teams uses allocated `EffectiveCost`; the invoice anchor is
  `BilledCost` × `InvoiceId`. Both views are correct, for different audiences

---

## Defensible allocation keys

Every allocation key will be questioned the moment a team sees their costs.
The test for a defensible key: can the team trace the dollar amount back to
a metric they can independently verify?

| Key class | Example | Defensibility | Notes |
|---|---|---|---|
| Direct attribution | Resource has the team's tag | Strong | The default whenever physical tagging supports it. |
| Operational metric | CPU-hours from Prometheus, request count from product telemetry | Strong | Right answer for shared services. The metric must come from a system the team trusts. |
| Header / authentication | API gateway request counts by client ID | Strong | Strong for multi-tenant platforms. |
| Budget / headcount weighting | Team A is 60% of engineering, gets 60% of shared cost | Defensible at Walk, fragile at Run | Works while the org structure is stable. Fails at reorganisations. |
| Even-split | Six teams use the platform, each gets 1/6 | Indefensible past showback | Triggers disputes immediately. Use only when no better key exists, and document the reason. |
| Manual override | "We agreed Team B gets allocated less because they're a strategic priority" | Indefensible | Encodes politics into the data. Surface the politics elsewhere; keep the methodology clean. |

**Rule of thumb:** build allocation keys from authoritative operational systems
(Prometheus, Thanos, product telemetry, API gateway logs) for shared platform
costs, not just from tags. Tags miss what teams actually consume; metrics
do not.

---

## Shared-services hard cases

The simple cases (resource has the team's tag, allocate to that team) work for
roughly 70% of cloud spend. The remaining 30% is shared services, and that is
where allocation methodology earns its credibility.

### Network cost

Network cost is the single hardest shared-services allocation problem. Cost
hides across many `ServiceCategory` values:

- Cross-zone data transfer between EC2 instances of two different teams
  (shows up under `ServiceCategory='Compute'`, not `'Networking'`)
- Database replica replication traffic (shows up under `'Databases'`)
- Storage egress for a team's S3 reads from a service in another region
  (shows up under `'Storage'`)
- Managed-service traffic (CloudFront, API Gateway, Application Gateway,
  Cloud CDN) that serves multiple teams' workloads
- NAT Gateway and Transit Gateway processing fees

Recommended allocation pattern:
1. Tag the network appliances themselves (NAT, ALB, TGW, ExpressRoute) where
   tagging is supported
2. For untaggable inter-resource traffic, allocate by **traffic share**
   measured from VPC Flow Logs, Application Gateway logs, or equivalent
3. For genuinely shared infrastructure (CDN, edge), use a tiered approach:
   first attribute to product through the CDN's request logs; then fall back
   to revenue-weighted or even-split for the residual

Document the methodology before publishing. Network allocation disputes are
guaranteed; the documentation pre-empts the worst of them.

### Observability and platform tooling

Logging pipelines, metrics platforms, distributed tracing, and CI/CD systems
serve every team. Three patterns that work:

- **Volume-weighted**: ingestion bytes per team for log platforms, span counts
  for tracing, build minutes for CI/CD. The metric is the bill driver.
- **Capacity-share**: for tools billed by capacity (Splunk indexers, Datadog
  hosts), allocate by team consumption of that capacity measured at a fixed
  cadence
- **Tiered floor**: every team pays a minimum platform fee for participation
  (covers the fixed cost of running the platform), and the variable cost is
  allocated by usage

The tiered-floor pattern is what most mature organisations land on. It avoids
the failure mode where a small team using one log line per minute pays a
microscopic share of a $100K/month log platform.

### Security tooling

Security tools serve the organisation, not individual teams. Default to
allocating their cost to the central security cost centre, not to engineering
teams. Engineering teams cannot opt out of security tooling, so charging them
for it creates noise without improving accountability.

The exception: per-team security workloads (e.g. WAF rules specific to one
team's app, secrets-manager entries owned by one team) can and should be
attributed to that team.

### Ingress / API gateway

Allocate by request count if the gateway has per-route or per-client
attribution. If it does not, configure that attribution before showback
goes live. An ingress allocation that cannot survive a "where did this
number come from?" question will be the first dispute.

---

## Showback - the first delivery vehicle on top of allocation

Showback distributes cost visibility without financial consequence. Teams see
their costs, learn to read them, and start to act on them. It builds the
trust in the data that any subsequent chargeback discussion depends on.

### Showback report design

A working showback report has four properties:

1. **Per-team breakdown** at the granularity the team operates at (per
   environment, per service, per workload - whatever maps to how they think)
2. **Trend over time** (current month vs trailing 3-month average, with a
   directional indicator)
3. **Top movers** (the three line items that changed most week-over-week,
   month-over-month - this is where engineering attention lands)
4. **Allocation methodology one click away** - a link or footnote explaining
   how each shared-services number was computed. If the team cannot trace
   the number, they cannot trust the number.

What it should NOT include at showback maturity:
- Forecast accountability (that comes with chargeback)
- Cross-team comparisons that imply ranking (creates the wrong incentives;
  the question is "is Team A using cloud appropriately for what they do?",
  not "is Team A more efficient than Team B?")
- Budget variance unless an explicit per-team budget exists (most don't at
  this maturity)

### Where showback reports land

A report that lives in a FinOps dashboard nobody opens does nothing. Route
showback into the team's existing surfaces:

| Audience | Where they already look | How showback arrives |
|---|---|---|
| Engineering team owner | Slack, Grafana | Weekly digest in team Slack channel; cost panel in their existing dashboard |
| Engineering manager | Monthly business review, sprint review | One-page team summary in the existing review pack |
| Product manager | Product analytics tool | Cost-per-feature line item alongside usage metrics |
| Finance partner | Excel / Google Sheets, ERP | CSV export from FOCUS query, reconciled to `InvoiceId` |

A standalone FinOps dashboard with a separate URL that requires its own login
is the failure mode. Integration into the team's existing tools is the work.

### Showback cadence

| Frequency | Activity | Audience |
|---|---|---|
| Daily | Anomaly review (see `finops-anomaly-management.md`) | FinOps + Engineering owners |
| Weekly | Showback digest with top movers | Engineering team leads |
| Monthly | Showback close, including invoice reconciliation | FinOps + Finance |
| Quarterly | Methodology review: do the allocation keys still work? Has the org changed? | FinOps + Finance |

Daily anomaly review and monthly invoice reconciliation are not optional. The
weekly digest and quarterly methodology review are the minimum cadence for a
trustworthy showback.

---

## Unallocated spend is a tagging signal

If more than 10% of spend cannot be allocated to a team or product, the
problem is upstream of allocation. The pipeline is not broken; tagging is.

The temptation when unallocated spend is high is to redistribute it across
known teams (e.g. proportional to their allocated spend). Resist this. It
penalises teams that tag well and rewards teams that do not. It also hides
the tagging problem from leadership, which makes the underlying fix less
likely to happen.

Better: surface unallocated spend as a discrete line item. Make it visible to
leadership. Drive the tagging programme on the back of it. See `finops-tagging.md`
for the enforcement work that brings unallocated spend below the 10% threshold.

---

## Data-quality dispute process

At showback maturity, almost every dispute is a data-quality issue, not a
methodology disagreement (methodology disputes show up later, when chargeback
makes the numbers consequential). Treat data-quality disputes as
high-value feedback - they are the team telling you their tagging is wrong,
their service is misclassified, or their resource ID has drifted.

A working data-quality dispute process:

1. **Single intake channel** (Slack, ticket queue) with a templated form:
   which line item, what is wrong, what the team thinks the correct value is
2. **Triage SLA**: 5 business days to first response
3. **Fix at source**: data-quality issues fix in the tagging pipeline or the
   resource itself, not in the showback report. A patched report that
   contradicts the source of truth is a future audit problem.
4. **Quarterly retrospective**: dispute count, top dispute categories. A
   rising rate in one area is a signal to invest in tagging or attribution
   infrastructure for that area

---

## Anti-patterns

- **Allocating `BilledCost` to teams**. Causes spike-and-trough chargeback
  charges aligned to commitment purchase dates rather than consumption. Always
  use `EffectiveCost` for allocation.
- **Using AWS `blended_cost` for showback or chargeback**. Payer-account
  averaging artefact. Use amortised (`EffectiveCost` / `line_item_amortized_cost`)
  for allocation; use unblended (`BilledCost` / `line_item_unblended_cost`)
  for invoice reconciliation. Never blended.
- **Hiding unallocated spend**. Redistributing it across known teams penalises
  good tagging and removes the lever to fix the underlying problem.
- **Even-split allocation past showback**. "Six teams use the platform, each
  gets 1/6" works only when the platform's cost is small and the teams are
  similar in size. Past showback, this triggers disputes that consume more
  FinOps time than building a real key would have.
- **Manual overrides for political reasons**. Encoding "Team A pays less
  because they're strategic" into the data corrupts the methodology and
  destroys credibility. Surface the strategic subsidy elsewhere; keep the
  allocation clean.
- **Showback reports in a standalone FinOps dashboard**. If teams have to
  log into a separate tool to see their costs, they will not. Route into the
  surfaces they already watch.
- **Cross-team rankings in showback**. Creates the wrong incentives. The
  question is whether each team is using cloud appropriately for what they
  do, not whether one team is more efficient than another.
- **No invoice reconciliation**. If `SUM(BilledCost) GROUP BY InvoiceId` does
  not match the invoice, every other number is suspect. Run the reconciliation
  monthly without exception.

---

## Maturity progression

### Crawl

- Tagging at >50% allocation (the prerequisite - see `finops-tagging.md`)
- Allocation pipeline running monthly: cost data joined to tags, output to
  per-team views
- Manual showback reports per team, distributed monthly via email or shared
  dashboard
- Allocation keys are simple: direct attribution from tags, even-split or
  central-cost-centre for unattributed shared services
- Data-quality dispute channel established

### Walk

- Automated allocation pipeline running daily on FOCUS-conformant data
  (or amortised native exports)
- Showback reports at fixed cadence (monthly minimum, weekly digest preferred)
  routed into team-existing tools (Slack, Grafana, sprint review packs)
- Documented allocation methodology: which key applies to which cost class,
  why
- Defensible keys for the top three shared-services categories (network,
  observability, ingress)
- Unallocated spend tracked as a discrete metric, < 10% target
- Quarterly methodology review with stakeholder sign-off
- Data-quality dispute SLA being met consistently

### Run

- Allocation keys driven by authoritative operational metrics (Prometheus,
  product telemetry, API gateway logs), not just tags
- Showback views integrated into the team's existing tools (Slack channels,
  PR-review cost annotations, Grafana panels) with no separate dashboard
- Allocation methodology version-controlled and reviewed annually with
  explicit stakeholder sign-off
- Unallocated spend < 5%, with the residual driven by genuinely untaggable
  cost categories
- Data-quality dispute rate trending down year over year
- Allocation pipeline outputs are the input to forecasting, anomaly
  detection, and (if the org has progressed there) chargeback

---

## Cross-references

- `finops-tagging.md` - the upstream prerequisite. Allocation maturity
  cannot exceed tagging maturity.
- `finops-chargeback.md` - the downstream extension. Showback at Walk
  maturity is the prerequisite for soft chargeback; both are prerequisites
  for hard chargeback.
- `finops-anomaly-management.md` - daily anomaly review feeds the same
  allocation pipeline; shares the FOCUS dataset.
- `optimnow-methodology.md` - "Showback before chargeback" principle, and
  the broader maturity-aware framing.
- `finops-framework.md` - Allocation capability in the FinOps Framework, plus
  the Inform-phase context.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
