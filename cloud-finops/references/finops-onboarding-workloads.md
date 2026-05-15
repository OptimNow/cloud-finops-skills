---
name: finops-onboarding-workloads
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Architecting & Workload Placement"
fcp_capabilities_secondary: ["Allocation", "FinOps Practice Operations", "Budgeting", "Forecasting"]
fcp_phases: ["Inform", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "Procurement", "Leadership"]
fcp_maturity_entry: "Walk"
---

# FinOps Onboarding Workloads

> Onboarding is the FCP capability that governs how new workloads enter the
> cloud estate - whether from on-premises migration, cloud-to-cloud move,
> account consolidation, or M&A integration. It is the cheapest moment in
> the workload's lifetime to enforce tagging, allocation, forecasting, and
> commitment-strategy alignment. Miss the window and the same hygiene work
> costs 5-10x more to retrofit post-migration.
>
> This file covers the intake gate that prevents the miss, and the operating
> patterns for the migration-time activities that the gate enforces.

---

## Why migration is the cheapest FinOps window

A workload that lands in production untagged, unallocated, and unforecast
becomes part of the catalogue of things that need fixing later. Every
quarter that passes makes the fix harder:

- **Tagging retrofit.** The team that built the workload moves on; the team
  that inherits it does not have the context to assign tags accurately.
  Untagged spend grows; allocation accuracy degrades.
- **Allocation pipeline drift.** Each new untagged workload pushes the
  unallocated spend ratio higher, eventually past the 10% threshold that
  signals to leadership that allocation is broken (see
  `finops-allocation-showback.md`).
- **Premature commitment.** A workload that runs for 90 days on PAYG before
  anyone forecasts its profile gets a commitment purchase based on the
  90-day baseline, not the steady-state. Steady-state often differs by 30-50%.
- **Architectural debt.** A workload deployed without cost-aware architecture
  review locks in patterns (cross-AZ chatter, oversized databases, untiered
  storage) that get harder to change once they are load-bearing.

The migration window is when all of this is cheapest to address: the team
that built the workload is still engaged, the architecture is still
malleable, the budget is still defensible because the migration is the
named project that funds it.

---

## The intake gate

The intake gate is the checklist that every workload must pass before
go-live. The gate is the operational expression of "no workload lands
untagged, unallocated, or unforecast."

### Mandatory checklist (minimum viable)

| Item | Owner | Verification |
|---|---|---|
| Mandatory tags applied (Environment, Owner, CostCenter, Project, Application) | Engineering | Tag-compliance scan in CI/CD or pre-deploy |
| Cost centre exists in ERP and is open for posting | Controller | Pre-migration handshake |
| Allocation pipeline maps the workload to the receiving team | FinOps | Sample query against the FOCUS / billing dataset for the new ResourceId |
| Forecast for the next 12 months exists, even if rough | Engineering + FinOps | Document with assumptions; revisit at 60 and 90 days |
| Commitment plan deferred until 60-90 days post-migration | FinOps | Explicit "do not commit yet" note in the workload's FinOps record |
| SLO and observability baselines defined | Engineering | Dashboards live before go-live, not after |
| Architecture review covered cost trade-offs | Engineering + FinOps | ADR or equivalent documenting cost-aware decisions |

### What "intake gate" means in practice

The gate is a process, not a tool. Three implementation patterns:

- **Pull request gate** - the deployment IaC change that makes the workload
  go live cannot merge without checklist evidence linked in the PR
  description (tag-policy CI passing, FinOps approval, forecast document URL)
- **Cutover gate** - for migrations that don't go through CI/CD, the cutover
  runbook includes the checklist as a hard step; the cutover is paused
  until the items are checked off by their respective owners
- **Pre-production gate** - the workload runs in a non-prod environment
  with the checklist applied; only after the checklist is green does the
  workload promote to prod

The pull-request gate is the strongest pattern for cloud-native work; the
cutover gate is the realistic pattern for lift-and-shift migrations from
on-premises.

### What the gate is NOT

- **A blocker for the migration deadline.** If the gate is consistently
  bypassed because "we have to ship", the gate is broken - the checklist is
  too long, the owners are wrong, or the upstream tooling does not support
  enforcement. Fix the gate; do not normalise bypassing.
- **A FinOps-only checklist.** Most items have an Engineering or Controller
  owner. FinOps coordinates and verifies; Engineering and Finance do the work.
- **A one-time exercise.** The gate runs on every workload. Recurring
  bypasses are a leadership signal, not an engineering signal.

---

## The 60-90 day forecast-then-commit rule

Migrated workloads are most volatile in the first 90 days post-migration.
Traffic patterns shift as users migrate; performance tuning changes
instance sizing; rightsizing exposes oversized provisioning that was
defensive on-premises. Buying commitments based on the first 30 days of
post-migration spend usually locks in waste.

### The rule

- **Days 0-30 post-migration:** PAYG only. Watch and learn.
- **Days 30-60:** baseline starts to stabilise. Document the steady-state
  shape (peak hours, baseline floor, growth trajectory) but do not commit yet.
- **Days 60-90:** if the steady-state shape is stable across 30+ days,
  forecast the next 12-month profile. Commit to no more than 60-70% of the
  forecast steady state for the first 1-year term. Leave room for the
  workload to grow or shrink as production behaviour reveals itself.
- **Day 90+:** treat the workload as an existing workload for commitment
  purposes; reassess quarterly under the normal commitment portfolio
  cadence (see `finops-aws.md`, `finops-azure.md`, `finops-gcp.md`).

### Why 60-90 days, not 30

A 30-day baseline misses week-over-week patterns, end-of-month batch jobs,
quarterly close pressure, and the slow rampup of users from the legacy
system. Committing on 30 days routinely produces 40-60% commitment
utilisation in month 4 - the worst-of-both outcome where you paid for
capacity you don't use AND you lack flexibility for the workload that
actually emerged.

### Exceptions to the rule

- **Lift-and-shift of a workload that has been measured for years on-prem.**
  If you have 24 months of CPU and memory data from on-premises, you can
  forecast more aggressively because the steady-state is known. The 60-90
  day rule still applies for confirmation but the floor of acceptable
  commitment can be higher.
- **GPU and AI capacity with provider-side scarcity.** If commitment is the
  only way to secure capacity (Azure OpenAI PTU regions, AWS GPU instances
  in constrained regions), you may need to commit at migration. Document
  the trade-off explicitly: capacity over commitment hygiene.

---

## The double-bubble cost

During any migration there is a window where both the source environment
and the target environment are running. This is the "double bubble" - paying
twice for capacity until the source is decommissioned. It is the single
biggest hidden cost of migration projects.

### Why it gets missed

- The migration budget often funds the target build but not the parallel-run
  cost on the source side
- The source-environment cost is in someone else's budget (typically central
  IT, not the migration project), so it is invisible to the migration P&L
- The "we will turn off the source when the target is stable" decision is
  made informally; nobody owns the cutover-completion deadline; the source
  runs for months past the planned shutoff

### The fix

- **Budget the double bubble explicitly.** The migration project budget
  includes both the target build and the expected parallel-run cost on the
  source side, with an explicit shutoff date.
- **Make the source-environment cost visible to the migration project.**
  Even if the source runs in a separate cost centre, allocate a notional
  shadow charge to the migration project for the parallel-run period. The
  migration team needs a live signal that delay costs them.
- **Define exit criteria from the source environment.** Migration is not
  done when the new one works. It is done when the old one is shut down
  and the dual-cost window closes. Exit criteria should be documented at
  project kickoff, not negotiated at cutover.
- **Schedule and enforce a hard shutoff date.** Three to six months past
  the original cutover plan, the source environment shuts down whether or
  not the team is ready. Without a hard date, the source runs forever.

---

## Migration-cost estimates vs actuals

Migration cost estimates are routinely wrong. The most common reason: the
network-cost model differs radically between data centre (capacity-based,
mostly fixed pipe) and cloud (usage-based, every byte priced).

### The network-cost trap

A workload that runs cleanly on-premises with chatty inter-service traffic
because the network was free at the margin (paid-for pipe) becomes expensive
in cloud where every cross-zone byte costs $0.01/GB and every inter-region
byte costs $0.02-0.09/GB. The cost difference can be 2-5x the original
estimate.

Specific patterns to watch for:

- **Cross-zone chatter.** Microservices designed for on-premises latency
  often span availability zones in cloud, generating cross-AZ data transfer
  charges that did not exist on-premises (see `finops-aws.md` 48-pattern
  catalogue, `finops-azure.md` patterns)
- **Database replication.** Synchronous replication across zones for HA
  was free on-premises (private network); in cloud it is per-GB
- **Storage egress.** A team's S3 reads from a service in another region
  are cross-region transfer; the on-premises equivalent was free
- **Ingress and load-balancer egress.** Customer traffic costs can differ
  meaningfully from on-premises ISP arrangements

### The fix

- **Treat migration cost estimates as directional, not committed.** Plan
  for 30-50% variance in the first 90 days; budget the contingency.
- **Run a 30-day "shadow" measurement on a representative workload before
  the bulk migration.** Real cloud bills for a small subset are worth more
  than any estimate.
- **Monitor actuals from day one of cutover.** A weekly migration-cost
  review catches the network-cost surprise within 14 days, not at month end.
- **Budget for re-architecture in year one.** Some workloads will need
  re-design (e.g. inter-AZ chatter consolidated to single-AZ, replication
  changed from synchronous to asynchronous) once the cloud network-cost
  picture is real. Do not budget for "migrate once, optimise never."

---

## M&A integration

Acquired organisations bring their own tagging, accounts, commitments, and
tooling. The integration window for a meaningful FinOps merge is 6-12 months,
not 6 weeks. Plan accordingly.

### The integration sequence

1. **Inventory and freeze (months 1-2).** Inventory the acquired estate's
   accounts, subscriptions, billing relationships, commitment portfolio,
   tagging conventions, and tooling. Freeze new commitment purchases until
   the integration plan is approved.
2. **Reconcile to the parent's allocation pipeline (months 2-4).** Map the
   acquired estate's tags to the parent's tag taxonomy. Decide whether to
   re-tag or use a translation layer. Map the acquired cost centres to the
   parent's chart of accounts.
3. **Commitment portfolio rationalisation (months 3-6).** Inventory the
   acquired estate's RIs, Savings Plans, and CUDs. Identify overlaps,
   under-utilised commitments, and expiry-date clusters. Plan exchanges or
   modifications under the existing liquidity rules
   (see `finops-aws.md`, `finops-azure.md`, `finops-gcp.md`).
4. **Tooling and process integration (months 4-9).** Decide whether to
   migrate the acquired estate to the parent's FinOps tooling or run dual
   for a period. Either choice has trade-offs; document the rationale.
5. **Allocation and chargeback alignment (months 6-12).** Bring the
   acquired estate into the parent's allocation methodology. If the parent
   does chargeback, the acquired estate joins that cycle once allocation
   is stable.

### Common M&A integration failures

- **"We'll integrate FinOps after the org integration is done."** Org
  integration takes 18-24 months. FinOps cannot wait that long without
  the acquired estate's costs becoming invisible to the parent.
- **"They'll keep their own billing relationship until the contract
  expires."** Two-year contracts with overlapping provider relationships
  cost more than the early-termination fees.
- **Letting the acquired estate keep its own tagging.** The parent's
  allocation degrades for years until the eventual harmonisation; the
  harmonisation work is then 5-10x larger.

---

## Land FOCUS exports during migration

The migration window is when standing up FOCUS-conformant exports is
cheapest:

- The legacy reporting tooling is being decommissioned anyway, so there is
  no legacy stakeholder defending the old format
- The team is already touching the billing pipeline as part of the migration
- Onboarding teams expect new tooling, so introducing FOCUS does not feel
  like an additional change

What this looks like in practice:

- For data-centre-to-cloud migrations: configure the cloud provider's
  FOCUS export from day one of the new account (AWS Data Exports for
  FOCUS 1.2, Azure Cost Management FOCUS 1.2 export, GCP FOCUS 1.0 export)
- For cloud-to-cloud migrations: configure FOCUS on the target before
  cutover, so post-cutover analysis is on FOCUS-shaped data from day one
- For M&A integration: stand up FOCUS for the acquired estate as part of
  the inventory phase (months 1-2)
- For multi-cloud environments: leverage the expanded FOCUS ecosystem
  (Oracle 1.0, Nebius 1.2, Vercel 1.3, Grafana Cloud 1.2, Redis 1.2,
  Databricks 1.2) to normalise cost data across all providers from day one

The alternative - "we'll do FOCUS after the migration is stable" - means
the FOCUS adoption decision gets re-litigated in 18 months when the
migration team has moved on and the new owners have no incentive to do
optional refactoring work.

As of December 2024, the expanded FOCUS provider support significantly
reduces the complexity of multi-cloud cost normalisation during migrations.

---

## Architecture review integration

Cost-aware architecture either lands at design review or is deferred
forever. The migration project's architecture review is the right venue.

### What "cost-aware architecture review" means

Add the following to the standard architecture review checklist:

- **Forecasted run-rate cost** for the proposed design at expected steady
  state, with a 50% upside scenario
- **Network cost analysis** for inter-service, inter-zone, inter-region
  flows, especially if the on-premises baseline was free network
- **Storage tier analysis** - hot / warm / cold storage classification with
  lifecycle policies named upfront, not added later
- **Commitment-plan placeholder** - what commitment purchases will the
  workload's steady state warrant, and when (per the 60-90 day rule)
- **Iron Triangle trade-off statement** - cost / speed / quality / carbon
  trade-offs the design embeds, with the team's explicit choice on which
  axis the design optimises

The deliverable: an ADR or equivalent that future readers can cite when
asking "why was this designed this way?"

### Why this matters

Architectural decisions made at migration time without cost review compound
into structural debt that takes years to unwind. A cross-AZ-chatty
microservice design that was acceptable in the migration architecture
becomes a $50K/month line item the first year and a refactor project the
second. Catching it at design review costs an hour of conversation; fixing
it post-migration costs a quarter of engineering time.

---

## Anti-patterns

- **"We'll tag it later."** Later is 18 months and 25% untagged spend.
  The intake gate is the prevention.
- **Buying 3-year commitments during migration.** Workloads are most
  volatile in the 6 months after migration; commit after stabilisation.
- **Closing the dual-cost window quietly.** The source environment cost is
  often forgotten; every month it runs past the planned shutoff is pure
  waste.
- **Treating migration cost estimates as committed numbers.** They are
  directional. Plan for 30-50% variance and monitor actuals from day one.
- **Migration projects with no post-migration FinOps owner.** The
  migration team disbands; nobody owns the workload's cost trajectory;
  optimisation never happens. Name the post-migration owner at project
  kickoff.
- **M&A integration measured in weeks, not quarters.** 6-week timelines
  produce 24-month integration debt.
- **FOCUS-after-migration thinking.** The migration window is the cheapest
  moment; deferring is more expensive.
- **Architecture review without cost analysis.** Locks in structural debt
  that takes years to unwind.

---

## Maturity progression

### Crawl

- Documented intake checklist exists, even if enforced manually
- Mandatory tags applied at migration via runbook step (not yet enforced
  in CI/CD)
- Forecast and commitment plan deferred until 60-90 days post-migration
- Double-bubble cost named in the migration project budget, even if
  rough

### Walk

- Intake gate enforced via CI/CD or cutover-runbook step; bypasses are
  logged and reviewed
- Tag policy verified pre-deploy; allocation pipeline picks up new
  workloads automatically
- Forecast and commitment plan are formal artefacts owned by Engineering +
  FinOps jointly
- Migration cost estimates include explicit network-cost analysis and
  30-50% variance budget
- Source-environment shutoff date is a tracked deliverable
- FOCUS exports configured during migration, not after
- Architecture review includes cost-aware checklist; ADRs document
  trade-offs

### Run

- Intake gate is fully automated; bypasses require leadership exception
  approval
- Migration projects have a named post-migration FinOps owner from
  kickoff; ownership transfers cleanly when the migration team disbands
- Cost-aware architecture review is the default; teams design for cost
  trade-offs without prompting
- M&A integration follows a documented playbook with month-by-month
  milestones
- Migration-cost actuals fed back into the estimate methodology
  quarterly; estimate accuracy improves over time

---

## Cross-references

- `finops-allocation-showback.md` - new workloads must land with allocation
  configured; the intake gate enforces this
- `finops-tagging.md` - the prerequisite for the tag-related intake gate
  items
- `finops-aws.md` - AWS-specific commitment timing for post-migration
  workloads (the 60-90 day rule applies)
- `finops-azure.md` - Azure-specific commitment timing; the EA-to-MCA
  transition is a related onboarding scenario
- `finops-gcp.md` - GCP-specific commitment timing
- `finops-fabric.md` - the Pro/PPU-to-Fabric migration governance trap is
  a precedent migration scenario where forecasting before commitment
  matters
- `finops-anomaly-management.md` - new workloads should be added to the
  anomaly-monitoring scope as part of the intake gate
- `optimnow-methodology.md` - "Diagnose before prescribing" applies
  especially to migration: understand what the workload actually does
  before recommending architecture or commitment

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
