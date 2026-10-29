---
name: finops-azure-billing
fcp_domain: "Understand Usage & Cost"
fcp_capability: "Data Ingestion"
fcp_capabilities_secondary: ["Allocation", "Reporting & Analytics", "Budgeting", "Invoicing & Chargeback", "Governance, Policy & Risk"]
fcp_phases: ["Inform", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Finance"]
fcp_personas_collaborating: ["Engineering", "Procurement"]
fcp_maturity_entry: "Crawl"
business_coverage: ["azure:bill:deep", "azure:budget:deep", "azure:contracts:partial"]
---

# Azure Billing Data, Allocation and Governance

> Azure cost data and the controls around it: Cost Management exports, FOCUS exports,
> the Retail Prices API, the FinOps Toolkit and FinOps hubs, Resource Graph, the MCA
> billing scope hierarchy and reservation ownership, cost allocation, tagging and Azure
> Policy, budgets, the EA-to-MCA transition, and agent access to cost data (the ARM MCP
> server, FinOps hubs agents). Usage optimisation (rightsizing, Log Analytics, backup,
> AKS, databases, storage, networking) is in `finops-azure.md`; commitments are in
> `finops-azure-commitments.md`.
>
> Distilled from OptimNow Azure FinOps engagement experience and primary Microsoft
> sources (Cost Management documentation, FinOps Toolkit).

---

## Azure cost data foundation

### Azure Cost Management exports

Azure Cost Management is the native cost visibility tool. For attribution and custom
tooling, build on scheduled exports to Azure Storage; the portal is for ad-hoc views.

**Export types:**
- **Actual cost** - charges as they appear on the invoice (use for billing reconciliation)
- **Amortized cost** - reservation and savings plan charges spread across the usage period
  (use for team-level showback and allocation)

**Export setup checklist:**
- [ ] Configure FOCUS exports at **Billing Account** or **Billing Profile** scope (Management Group is not supported for FOCUS exports)
- [ ] For legacy actual/amortized exports, MG scope is supported but with limitations - keep them on subscription or billing-profile scope for cleanest behaviour
- [ ] Select both actual and amortized cost exports
- [ ] Set daily granularity
- [ ] Export to Azure Data Lake Storage Gen2 for Power BI integration
- [ ] Consider FinOps Hubs (Microsoft FinOps Toolkit) for automated ingestion and normalisation

Source for scope rules: https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-improved-exports

**FOCUS export support (April 2026):**
- **Cost Management exports** support a **FOCUS 1.2 preview** dataset, with documented conformance gaps against the published 1.2 spec.
- **FinOps Toolkit v12 / FinOps Hubs** ingest the preview and provide FOCUS 1.2-aligned analytics on top.
- FOCUS 1.0 went GA in Cost Management in June 2024 - that remains the historical baseline; FOCUS 1.2 is the current direction. Configure for multi-cloud normalisation alongside traditional actual/amortized exports.
- **FOCUS 1.3** implementations are emerging across the ecosystem (AWS, Vercel, Grafana Cloud, Redis, Databricks) - Azure's roadmap for 1.3 support has not been announced as of April 2026.

Sources: https://learn.microsoft.com/en-us/cloud-computing/finops/focus/conformance-summary, https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/changelog

**Five first-class export feeds (FinOps Hubs model):** beyond actual/amortized and FOCUS, Cost Management produces three more feeds the FinOps Hubs model treats as first-class:
- **Price sheet** - negotiated price per meter, per Billing Profile
- **Reservation details** - purchases, terms, scope, utilisation
- **Reservation recommendations** - Microsoft's purchase suggestions
- **Reservation transactions** - purchase, exchange, refund history

All five feed the same Hub for unified reservation portfolio analytics. Source: https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/hubs/finops-hubs-overview

### Retail Prices API for validation

Use the Azure Retail Prices API to verify EA discounts against public pricing. Useful for:
- Comparing PAYG vs Reserved Instance pricing with ROI calculation
- Evaluating Spot VM savings potential (60-90% off PAYG)
- Estimating database and storage tier costs across regions
- Validating that EA discount percentages match contracts

### FinOps Toolkit and FinOps Hubs

Microsoft's open-source FinOps Toolkit provides pre-built solutions including Power BI
report templates, Azure Workbooks, and FinOps Hubs for automated cost data ingestion.

**FinOps Hubs** normalise cost exports into a consistent schema and feed Power BI reports.
Recommended for organisations that want production-grade reporting without building custom
data pipelines. FinOps Hubs (Toolkit v12) ingest the **FOCUS 1.2 preview** from Cost
Management and provide 1.2-aligned analytics on top, enabling standardised multi-cloud
cost reporting (see "FOCUS export support" above for the layered preview vs GA picture).

Repository: https://github.com/microsoft/finops-toolkit

### Azure Resource Graph for cost analysis

Azure Resource Graph (ARG) enables large-scale resource inventory and compliance analysis
with KQL queries. Use it for:
- VM analysis by family, OS disk type, hybrid benefit status
- Storage disk type summary (Premium, Standard SSD, Standard HDD, Ultra)
- Tagging compliance analysis with percentages
- Resource distribution by business unit/owner

---

## FOCUS exports and Retail Prices API - the data-side gaps

The Cost Management foundation section covers FOCUS exports as a setup step. This
section covers the practical patterns and known limitations when building custom
cost analytics on top.

### FOCUS export practical patterns (1.0 GA, 1.2 preview)

FOCUS 1.0 went GA in Azure Cost Management in June 2024. As of April 2026, Cost
Management additionally supports a **FOCUS 1.2 preview** export with documented
conformance gaps (see Cost Management foundation section above). FinOps Hubs /
Toolkit v12 ingest the 1.2 preview into 1.2-aligned analytics. The schema fields
below cover the 1.0 GA columns most useful for FinOps work - additional 1.2 columns
become available once the preview export is enabled.

**Multi-cloud normalisation context:** With FOCUS 1.2 implementations now available
across AWS, Azure, and emerging providers (Nebius, Vercel, Grafana Cloud, Redis,
Databricks), organisations can build unified cost reporting across their entire
cloud estate. Azure's 1.2 preview aligns with this broader ecosystem trend.

| Field | Use |
|---|---|
| `BilledCost` | What appears on the invoice - use for billing reconciliation |
| `EffectiveCost` | Amortised cost including commitment amortisation - use for showback |
| `ListCost` | Pre-discount list price - use for negotiated discount validation |
| `ContractedCost` | Cost at contracted rate before commitment discounts - use for portfolio analysis |
| `ResourceId` | Full Azure ARM resource ID - join key to Resource Graph |
| `Tags` | Resource and inherited tags - allocation key |
| `Region` | Azure region - drives carbon and latency analysis |
| `ServiceCategory` | FOCUS service taxonomy - normalises across clouds |
| `CommitmentDiscountId` | Reservation or Savings Plan ID - join to commitment portfolio |

**MCA join pattern:** under Microsoft Customer Agreement, each Billing Profile
produces its own FOCUS export. Central FinOps must **union the exports across
profiles** before analysis. For multi-profile customers (most large enterprises),
this is a daily ETL step, not a one-time configuration. Document the union logic
in the FinOps platform runbook.

**Source:** https://learn.microsoft.com/en-us/azure/cost-management-billing/dataset-schema/cost-usage-details-focus

### Retail Prices API - note for custom Power BI / third-party tooling only

**Native Azure Cost Management, Advisor, and FOCUS exports run on Microsoft's
internal pricing service** and are not affected by the public Retail Prices API
rate limit. This subsection is only relevant when a custom Power BI dashboard,
Python script, or third-party tool calls the public pricing endpoint directly.

**Endpoint:** `https://prices.azure.com/api/retail/prices`

- Pagination via `NextPageLink`, 100 items per page
- Practical rate limit: ~300 requests per minute per source IP (undocumented by
  Microsoft)
- Caching strongly recommended - prices change weekly at most for most SKUs

**Failure modes that look like success:**

- Empty pages mid-chain - the response returns 200 with an empty `Items` array
  but a populated `NextPageLink`. Naive scripts treat empty as end-of-data and
  stop.
- Truncated `NextPageLink` - silently dropped from the response on a transient
  error. The script reports "done" with incomplete data.
- Partial pagination terminating without error - the `NextPageLink` chain ends
  before all matching pages are returned.

A naive Power BI refresh or Python pull will report success while having pulled
40-60% of the actual price catalogue. The result is wrong unit-economics
calculations downstream.

**Defensive pattern:**

1. Use `$filter` to narrow the query (by `serviceFamily`, `armRegionName`,
   `priceType`) - smaller queries are more reliable.
2. Self-throttle to ~200 RPM (well below the practical ceiling).
3. Validate pagination chain completeness - track expected total via the
   `Count` field on the first page if available, or compare to the previous
   refresh's row count.
4. Cache for at least 24 hours.
5. For full-catalogue enumeration, use the **bulk Pricing CSV exports** from the
   Azure Pricing Calculator rather than the API.

Frame this as a known limitation of what can be built on the public API, not a
recurring engagement issue. Native Cost Management surfaces are unaffected.

---

## Cost allocation on Azure

### Billing scope hierarchy

The hierarchy is different on EA vs MCA. Get this right at engagement kickoff -
the wrong mental model leads to wrong recommendations on chargeback and reservations.

**EA hierarchy:** Enrollment -> Department -> Account -> Subscription, with the
Management Group / Resource Group layers sitting underneath subscriptions for
governance.

**MCA hierarchy (four billing levels):**

| Level | What it is | What it aggregates | Key role |
|---|---|---|---|
| **Billing Account** | Root container, created at signup. One per MCA signature. | Everything below. | Billing Account Owner - full visibility and control. |
| **Billing Profile** | The unit that **generates a single monthly invoice**. One invoice per Billing Profile. Payment method attached here. Pricing is tied to the Billing Profile (not enrollment-wide as under EA - relevant for multi-entity groups where negotiated discounts may not propagate the way the client assumes). | All Invoice Sections below it. | Billing Profile Owner - manage invoices, create budgets, purchase reservations and savings plans. |
| **Invoice Section** | A grouping on the invoice (department, team, project). Shows as a line on the invoice, not a separate invoice. | Subscriptions assigned to it. | Invoice Section Owner - create subscriptions in the section, manage them. |
| **Subscription** | Where resources are deployed and billed. Resource Groups and Resources sit underneath. | Resources. | Subscription Owner / Contributor / Reader (standard Azure RBAC). |

**Three sentences that anchor the hierarchy:**
1. **Invoices happen at the Billing Profile level.** That is why multi-entity groups
   often have one Billing Profile per legal entity - because invoices have to match
   legal contracts.
2. **Invoice Sections are chargeback groupings inside one invoice.** They do not mean
   separate invoices.
3. **Reservations sit on the Billing Profile.** They do not belong to an Invoice
   Section - this has direct consequences for chargeback (see "MCA reservation
   ownership and the chargeback trap" below).

**MCA visibility gap to plan for at kickoff.** Under EA, a Subscription Owner with
enrollment access can create exports and budgets at higher scopes. **Under MCA, a
Subscription Owner cannot create exports or budgets at Billing Profile or Invoice
Section level** - the user needs at least **Billing Profile Reader** or **Billing
Profile Contributor**. Sort out these roles in the engagement kickoff before you
need them, otherwise the day-1 export setup will block on a permissions ticket.

Sources: [MCA setup](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/mca-setup-account), [Cost Management scopes](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/understand-work-scopes), [Billing roles for MCA](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/understand-mca-roles)

**Allocation strategy (applies to both EA and MCA):**
- Use Management Groups for policy inheritance and org-level cost views
- Use Subscriptions as the primary cost allocation boundary (equivalent to AWS
  accounts)
- Use Resource Groups to group resources by workload or team within a subscription
- Use Tags for cross-cutting dimensions (Environment, CostCenter, Project)

### MCA reservation ownership and the chargeback trap

Under MCA, an Azure Reservation is **owned at the Billing Profile level**. Default
discount scope is **Shared**, which means the reservation benefit flows to any
eligible resource across all subscriptions under that Billing Profile - regardless
of which Invoice Section the subscription sits in.

**Reservations cannot be moved between Invoice Sections.** This is a hard limit, not
a configuration flag.

**Consequence for multi-entity engagements.** If a customer has three business units
mapped to three Invoice Sections and asks "can we attribute each BU's reservation
cost to its own invoice section?" - the answer is **no, not natively**. You cannot
do it at the billing layer. You build an allocation layer on top of Cost Management
exports (allocation rules, or BI-side logic on the FOCUS export).

**Anti-pattern to avoid.** Do not promise "we will put BU-A's reservations on BU-A's
invoice line." That is not how MCA works. Promise: "we will show BU-A its share of
reservation cost in a Cost Management view and feed that to your chargeback system."

Source: [Organize your invoice based on your needs](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/mca-section-invoice)

### Azure-specific tagging considerations

**Key difference from AWS:** Azure supports tag inheritance policies through Azure
Policy. Resources can inherit tags from their resource group or subscription
automatically. This simplifies governance for teams that organise resources by
resource group.

**Tag enforcement policies (Azure Policy):**
- `deny` effect: Block resource creation without mandatory tags
- `audit` effect: Flag non-compliant resources without blocking
- `modify` effect: Auto-apply tags from resource group to child resources
- Tag inheritance from subscription level and resource group level

**Tags for automation:** Beyond cost allocation, use tags to drive automation:
- `startTime` / `stopTime` for VM scheduling
- `Environment` (dev/pre/pro) for policy differentiation
- `Owner` for accountability and notification routing

**Resource Group naming convention (recommended):**
Pattern: `rg-{bu3chars}-{name}-{env}` (e.g., `rg-fin-webapp-dev`)

---

## Governance - tagging and Azure Policy as a FinOps lever

Tagging governance and Azure Policy belong together. Policy is the mechanism that
enforces tags; tag compliance is checked via Policy. Treating them as separate
topics is how organisations end up with policies that audit but never enforce, or
tagging schemes that exist on paper but not in production.

### Tagging policy design

Mandatory tag set - the OptimNow default for FinOps allocation:

| Tag | Purpose | Allowed values |
|---|---|---|
| `CostCenter` | Allocation to finance ledger | Controlled enum from finance |
| `Environment` | Lifecycle separation | `Production`, `Staging`, `Development`, `Sandbox` |
| `Owner` | Accountability for spend | Email or distribution list |
| `Application` | Workload grouping | Controlled enum from CMDB or ServiceNow |
| `DataClassification` | Compliance and retention | `Public`, `Internal`, `Confidential`, `Restricted` |

**Critical mechanic:** tags **are not** automatically inherited from a Resource
Group to its resources. A tag on the RG does not propagate to VMs, disks, or NICs
inside it. This is a common source of "we tag everything" claims that collapse on
audit. Inheritance must be enforced via Policy with `Modify` or
`Inherit a tag from the resource group` built-in.

Tag values should be drawn from a **controlled enum**, not free text. `CostCenter`
values that drift across `12345`, `CC-12345`, `CC12345` make allocation impossible.
Validate at policy deploy time with `allowedValues`.

**Source:** https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/tag-resources

### Azure Policy effects to know

| Effect | Behaviour | Use for |
|---|---|---|
| `Audit` | Logs non-compliance, no action | Starting mode for any new policy |
| `Deny` | Blocks deployment if non-compliant | Hard rules - "no resource creation without `CostCenter`" |
| `Modify` | Adds or changes tags during deployment / via remediation | Tag inheritance from RG |
| `Append` | Adds properties during deployment | Default values for missing fields |
| `DeployIfNotExists` | Deploys a remediation resource if missing | Auto-shutdown schedule, AHB enablement, monitoring agent install |

`AuditIfNotExists` is the read-only sibling to `DeployIfNotExists` - use to flag
where remediation is needed without auto-deploying.

**Source:** https://learn.microsoft.com/en-us/azure/governance/policy/concepts/effects

### Audit-mode rollout pattern

Going straight to `Deny` on day one breaks deployments and creates tickets. The
defensible rollout sequence:

1. **Deploy in `Audit` mode** - log non-compliance for 2-4 weeks
2. **Run remediation tasks** to fix the existing fleet (`Modify` and
   `DeployIfNotExists` policies have built-in remediation)
3. **Communicate the cutover date** to all teams that deploy resources
4. **Escalate to `Deny`** for new deployments
5. **Keep `Audit` mode** for tags that are nice-to-have but not blocking

This sequence converts policy from a deployment blocker into a governance lever
without breaking the engineering workflow.

### Cost allocation patterns

Three patterns, in order of allocation cleanliness vs flexibility:

1. **Subscription-per-business-unit** - the cleanest allocation model. Each
   business unit consumes its own subscription, billing rolls up by subscription
   ID, no tags needed for business-unit allocation. Trade-off: rigid - changes to
   the org structure require subscription migrations.
2. **Tag-based allocation** - flexible but depends on tag hygiene. `CostCenter`
   becomes the allocation key. Use Cost Management's allocation rules to split
   shared subscription costs (network, governance) across consumers based on tag
   values.
3. **Hybrid** - subscription per BU for direct costs, tag-based allocation for
   shared services.

**Cost Management allocation rules** can split shared costs (a shared subscription,
RG, or service) across consumers based on tag values, fixed proportions, or
absolute amounts. Document the allocation rule logic in the FinOps runbook -
allocation-rule debugging is otherwise an audit nightmare.

### Chargeback vs showback decision

- **Showback** - costs are visible to consuming teams, no money moves. Appropriate
  for low-to-medium maturity, or organisations without internal billing plumbing.
  Most of the enterprise engagements OptimNow has run end here.
- **Chargeback** - costs flow to consuming teams' budgets. Requires finance
  process and tooling to move money internally. Appropriate when the
  organisation has the financial plumbing and the cultural readiness to be
  confronted with its consumption.

Recommend showback first. Chargeback adds organisational complexity and only pays
off when the showback signal stops driving behaviour change on its own.

### OptimNow tooling for tag governance

Two OptimNow assets for tag governance work:

- **Tag compliance MCP (open source)** -
  https://github.com/OptimNow/finops-tag-compliance-mcp - agent-accessible tag
  compliance auditing across Azure (and AWS). Recommended pattern when ongoing
  tag compliance reporting needs to be integrated with an AI agent.
- **Tagging policy generator** - generates Azure Policy / AWS SCP / GCP Org Policy
  from a tagging schema. Fastest way to bootstrap a tagging policy from an
  existing tag taxonomy without hand-writing Bicep or ARM.

### KQL: tag governance triage

```kusto
// Untagged resources by RG
resources
| where isempty(tags) or tags == dynamic({})
| summarize Untagged = count() by resourceGroup, subscriptionId
| order by Untagged desc
```

```kusto
// Resources missing CostCenter
resources
| where isnull(tags.CostCenter) or tags.CostCenter == ""
| summarize MissingCostCenter = count() by type, subscriptionId
| order by MissingCostCenter desc
```

```kusto
// Tag value drift detection - CostCenter case-insensitive variants
resources
| where isnotempty(tags.CostCenter)
| extend ccLower = tolower(tostring(tags.CostCenter)),
         ccActual = tostring(tags.CostCenter)
| summarize variants = make_set(ccActual) by ccLower
| where array_length(variants) > 1
```

The third query catches `cc-12345` / `CC-12345` / `Cc-12345` style drift - the
silent allocation killer.

---

## Azure governance tools - policy patterns and budgets

The earlier "Governance - tagging and Azure Policy as a FinOps lever" section
covers tag governance specifically. This section covers Azure Policy patterns for
FinOps more broadly, plus Azure Budgets and environment-tier definitions.

### Azure Policy for FinOps - common policy library

Azure Policy enforces organisational standards across subscriptions. Key FinOps
policies:

| Policy | Effect | Purpose |
|---|---|---|
| Require mandatory tags | `deny` | Block untagged resource creation |
| Audit tag compliance | `audit` | Visibility into tagging gaps |
| Inherit tags from resource group | `modify` | Automatic tag propagation |
| Allowed VM SKUs | `deny` | Prevent expensive GPU/M-series in dev |
| Allowed disk SKUs | `deny` | Block UltraSSD/PremiumV2 in non-prod |
| Allowed storage SKUs | `deny` | Restrict to Standard_LRS/ZRS |
| Deny expensive SQL tiers | `deny` | Only allow Basic/Standard/GeneralPurpose |
| Deny public IPs | `deny` | Use Bastion/VPN instead (cost + security) |
| Restrict regions | `deny` | Enforce approved regions |
| Enforce VM shutdown schedule | `audit` | Flag VMs without auto-shutdown tags |

**Assign policies at Management Group scope** for org-wide enforcement. Use
remediation tasks to apply `modify` policies to existing resources retroactively.

### Azure Budgets and Alerts

Configure at minimum:
- Subscription-level monthly budget with 80% and 100% actual cost alerts
- Forecasted cost alert at 100% (triggers before the budget is exceeded)
- Resource group level budgets for high-spend workloads

**Alert recipients:** Both the FinOps practitioner and the engineering team lead.
FinOps-only alerts create a bottleneck; engineering-only alerts lack financial
context.

Use Action Groups for automated responses (Logic Apps, Azure Functions, webhooks).

### Environment definitions

Formalise environment tiers with different governance levels:

| Environment | Allowed SKUs | Schedule | Commitment eligible | Backup |
|---|---|---|---|---|
| Sandbox | B-series only | Auto-delete after 7 days | No | No |
| Dev | B-series, small D/E | Business hours only | No | No |
| Pre-Production | Match prod families, smaller | Business hours only | No | Optional |
| Production | Any approved | 24/7 | Yes (after 90-day stability) | Yes |

**Principle: Shut down waste before committing to anything.** Reduce baseline cost
first, then layer commitments (RIs, Savings Plans) on top of the optimised baseline.

---

## EA-to-MCA transition - FinOps impact

Microsoft is actively migrating Enterprise Agreement (EA) customers to the Microsoft
Customer Agreement (MCA). While the transition is primarily a commercial
restructuring, it has significant FinOps operational consequences that teams must
prepare for.

### The three MCA flavours - know which one before kickoff

MCA is one programme with three distinct purchase paths. They are easy to confuse
and the answer changes who owns the billing relationship.

| Flavour | Purchase path | Who signs what | Where the FinOps team gets data |
|---|---|---|---|
| **MCA Direct** | Customer signs digitally, buys Azure directly from Microsoft via the portal. | Customer signs MCA with Microsoft. | Direct Microsoft billing portal and Cost Management. |
| **MCA Partner** (formerly **CSP**) | Customer buys through a Microsoft partner. | Partner signs MCA with Microsoft; customer signs with the partner. | Partner's billing tools first, Cost Management for resource-level data. **CSP is no longer a separate programme** - it is the indirect channel under MCA. People still say "CSP" out of habit. |
| **MCA Enterprise (MCA-E)** | Enterprise sales motion, direct with Microsoft, negotiated terms. | Customer signs MCA-E directly with Microsoft. | Direct Microsoft billing, plus negotiated rate sheet visibility. This is the path most EAs migrate to. |

**Day 1 question to ask the customer:** "Did you sign the Azure agreement directly
with Microsoft, or through a partner?" If partner, chargeback questions route through
the partner's tooling first. If direct, the standard Cost Management surfaces apply.

**What a partner customer sees in Cost Management.** Customer-tenant users see costs
only after the partner's admin agent enables the cost visibility policy, which is off
by default. Costs then show at pay-as-you-go retail rates, without the partner's
discounts or credits, and reservation usage shows zero for both actual and amortised
cost. A showback built in the customer tenant is therefore a retail-rate view;
reconciling to what the company pays needs the partner's invoice data. Changing partner
does not move cost history to the new billing account, so export it before a transfer.
Source: <https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/get-started-partners>

### What changes under MCA

| Dimension | EA | MCA |
|---|---|---|
| Billing hierarchy | Single enrollment, departments, accounts | Billing account, billing profiles, invoice sections |
| Invoice structure | Single consolidated invoice | Multiple invoices (one per billing profile) |
| Commitment flexibility | Annual upfront or monthly payments | Pay-as-you-go default, optional commitments |
| Cost Management data | Full historical visibility | Pre-migration data may not carry over |
| Power BI connector | Legacy EA connector | Deprecated - must use FOCUS exports + ADLS |
| FinOps Toolkit support | Direct EA integration | Requires migration to storage-based exports or FinOps Hubs |

### FinOps risks during transition

**Historical data visibility loss.** Cost Management may not display pre-migration
spending after the switch. Export historical data before migration begins. Without
this, year-over-year comparisons and trend analysis break.

**Power BI reporting disruption.** The legacy EA Power BI connector is deprecated
under MCA. Teams must migrate to FOCUS-aligned exports to Azure Data Lake Storage
(ADLS) and rebuild Power BI reports against the new schema. Plan for 2-4 weeks of
reporting rework.

**Savings plan and reservation visibility gaps.** Commitment discount usage
reporting changes under MCA billing scopes. Verify that existing reservation and
savings plan utilisation dashboards still function after migration. Re-scope alerts
and reports to the new billing profile hierarchy.

**Invoice reconciliation complexity.** Multiple billing profiles generate separate
invoices. Teams accustomed to a single EA invoice need new reconciliation
processes. Map cost centres and departments to MCA invoice sections before
migration.

### Migration checklist for FinOps teams

- [ ] Export 12-24 months of historical cost data from Cost Management before
  migration
- [ ] Document current EA billing hierarchy and map to planned MCA structure
- [ ] Inventory all Power BI reports using the legacy EA connector
- [ ] Plan migration to FOCUS exports + ADLS (or FinOps Hubs) for reporting
- [ ] Verify reservation and savings plan visibility in the new billing scope
- [ ] Update cost allocation rules and management group assignments
- [ ] Test showback/chargeback reports against the new invoice structure
- [ ] Update Azure Policy assignments if scoped to EA enrollment or departments

### FinOps Toolkit migration paths

Microsoft's FinOps Toolkit supports two migration approaches:

1. **Storage-based exports** - configure Cost Management exports to ADLS Gen2 in
   FOCUS format, then connect Power BI directly. Simpler but requires manual
   schema management.

2. **FinOps Hubs** - deploy the FinOps Hubs solution for automated ingestion,
   normalisation, and multi-tenant support. Recommended for organisations with
   multiple billing profiles or complex allocation requirements.

Both approaches produce FOCUS-compliant data, which is the forward-looking standard
for Azure cost reporting.

---

## Agentic FinOps on Azure - Copilot agents and MCP servers

Microsoft is extending cost and usage intelligence beyond the portal into agent
workflows. As of July 2026, four surfaces matter for FinOps practitioners. They are
frequently conflated in coverage, so exact names matter. This is the Azure-native
counterpart to the MCP-based automation pattern documented in `finops-tagging.md`.

### Azure Copilot observability agent (GA June 2026)

Generally available since June 2026, with autonomous operations in public preview.
The agent continuously analyses telemetry (application topology, dependencies,
baseline behaviour), groups related alerts, begins investigations automatically, and
recommends next steps. It is an operations surface, not a billing surface - its
FinOps value is correlating "what changed" with deployment and configuration events.
It does not restart resources or change configuration on its own, and prompts and
responses are not used to train foundation models.

### Azure Resource Manager MCP Server (public preview)

A remote MCP server (hosted at `mcp.management.azure.com` - nothing to deploy) that
gives AI agents access to Azure estate data and ARM deployments. Microsoft marketing
also calls this the "Azure FinOps MCP Server" when framing cost scenarios - same
product, two names in the same announcement. Six tools in the preview, cleanly split:

| Half | Tools | FinOps relevance |
|---|---|---|
| Read (Azure Resource Graph) | `generate_query`, `validate_query`, `execute_query` | Tenant-wide estate queries in one call: cost-driver discovery by region/owner/workload, tag hygiene sweeps, orphaned-resource detection, rightsizing candidates |
| Write (ARM deployments) | `create_template_deployment`, `get_arm_template_deployment_status`, `cancel_arm_template_deployment` | Governed remediation: tag patches, cleanup templates - every deploy is an auditable ARM operation with a correlation ID |

**Permission model:** every operation runs in the context of the signed-in user -
no service principal, no separate agent credential. The agent's effective permissions
are exactly the human's, and Azure Policy assignments apply identically. Read-only
agents need Reader plus Resource Graph Reader on the target scope; deploy-capable
agents additionally need Contributor on the target resource groups.

**Determinism caveat for recurring agents:** `generate_query` is non-deterministic -
the same prompt can produce different KQL, different result sets, and therefore
different remediation actions on different runs. Microsoft's own PoC catalogue for
this server (24 agents, including a Cost Driver Finder, FinOps Rightsizer, Tag
Hygiene Czar, and Weekly Cleanup PRs) pins literal KQL in reviewed rules files and
uses the LLM only at dev time to draft queries. Adopt the same contract before
putting a recurring FinOps agent on these tools. Microsoft's observed pattern is
worth repeating verbatim: read-only agents are ~80% of the value at ~5% of the risk -
start there, and gate any write behind an explicit user verb, a confirm step showing
the resolved template and scope, and a freeze flag. This matches the
policy-generation-over-direct-mutation doctrine in `finops-agentic.md`.

### Azure MCP Server pricing tools

Distinct from the ARM MCP Server above: the **Azure MCP Server** (the `@azure/mcp`
developer server) includes a read-only pricing tool that queries Azure retail rates
by SKU, service, and region, with `Consumption`, `Reservation`, and
`DevTestConsumption` price types and optional savings-plan pricing. Its FinOps use is
**pre-deployment cost estimation inside the IDE**: extract resource types and SKUs
from a Bicep/ARM template, query per resource, and sum monthly cost (hourly rate x
730). This moves cost estimation from a post-deploy surprise to a design-time
constraint.

### FinOps hubs AI agents (FinOps Toolkit 14+)

FinOps hubs (see "FinOps Toolkit and FinOps Hubs" above) connect AI agents to the
hub's Data Explorer databases via the Azure MCP Server. Supported paths:

- **GitHub Copilot Agent mode** with Microsoft's downloadable FinOps hub instruction
  pack - engineers query FOCUS-normalised cost data in natural language (allocation,
  anomaly detection, forecasting, Effective Savings Rate quantification), with the
  KQL shown and approvable before execution
- **Copilot Studio agent template** (added in Toolkit 14, April 2026) - publishes a
  FinOps hub agent into Microsoft Teams or Microsoft 365 Copilot, aimed at finance,
  product, and leadership audiences rather than engineers
- **Any MCP client** (Claude, Continue, and others) - the hub connection is plain
  MCP; Microsoft's instruction pack is written for Copilot but reusable

Permission requirement: Database Viewer or greater on the hub's Data Explorer
databases. The usual freshness caveat applies - answers are only as current as the
last Cost Management export (typically every 24 hours), so ask the agent for the
last refresh time before trusting its numbers.

Sources (all Microsoft, as of July 2026):
https://azure.microsoft.com/en-us/blog/from-insight-to-action-the-next-phase-of-agentic-cloud-operations/,
https://techcommunity.microsoft.com/blog/azuregovernanceandmanagementblog/introducing-the-azure-resource-manager-mcp-server/4517521,
https://techcommunity.microsoft.com/blog/azuregovernanceandmanagementblog/arm-mcp-server-a-catalog-of-24-pocs/4519069,
https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/azure-pricing,
https://techcommunity.microsoft.com/blog/finopsblog/whats-new-in-finops-toolkit-14-%E2%80%93-april-2026/4519497,
https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/hubs/configure-ai

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
