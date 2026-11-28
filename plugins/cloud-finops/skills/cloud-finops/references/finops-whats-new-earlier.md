---
name: finops-whats-new-earlier
fcp_domain: "Manage the FinOps Practice"
fcp_capability: "FinOps Practice Operations"
fcp_phases: ["Inform", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Leadership"]
fcp_personas_collaborating: ["Engineering", "Finance", "Procurement"]
fcp_maturity_entry: "Crawl"
questions:
  - "What changed in cloud and AI billing two or three months ago?"
  - "Which provider changes from earlier in the quarter still affect our bill?"
  - "What did AWS, Azure and Google Cloud change on billing over the summer?"
  - "Quels changements de facturation cloud datent d'il y a deux ou trois mois ?"
---

# What changed - earlier months of the 90-day digest

> The older part of the dated digest of provider and vendor changes that affect a
> cloud or AI bill. `finops-whats-new.md` carries the changes already scheduled, the
> current and the previous month, and how to answer from the digest. This file carries
> the earlier months of the same 90-day window, generated from the same list.

---

## How to read this file

- **Start from `finops-whats-new.md`.** Its "How to use this digest" section applies
  here unchanged: say the as-of date first, give each item its date, its effect on the
  bill and the guide to open, and rank by the reader's estate.
- **A question about a provider or a service reads both files.** "What did AWS change
  this quarter" is the AWS rows of both, newest first.
- **A row is a pointer.** Open the file and section named in the last column before
  turning a row into a recommendation. No prices here: rows state mechanics and ratios.

**Scope.** A month moves here when it is older than the month before the as-of date,
and its rows leave after 90 days; the guides keep the mechanics.

<!-- whats-new:start -->

**Digest as of 28 November 2026:** 30 verified changes dated from 30 August 2026 to 30 September 2026. The changes dated since 1 October 2026, and those already scheduled, are in `finops-whats-new.md`.

## September 2026

Changes dated September 2026, newest first.

| Date | Who | What changed for the bill | Read more |
|---|---|---|---|
| 30 Sep | Azure (Azure Monitor Container insights) | Support for the ContainerLog (v1) table retired. ContainerLogV2 replaces it and is the only one of the two that accepts the cheaper Basic table plan, so AKS clusters still writing v1 pay the Analytics rate on their container logs. | `finops-azure.md`, "Lever 2: Table-level tier choice" · [source](https://learn.microsoft.com/en-us/azure/azure-monitor/containers/container-insights-logs-schema) |
| 30 Sep | AWS (Bedrock (OpenAI GPT-6 Astra)) | OpenAI GPT-6 Astra on Bedrock has an Ultrafast speed tier priced at 6x Standard on every token type, cache writes and reads included, selected per request. Priority, Flex and Reserved are not available on that model. | `finops-bedrock.md`, "Service tiers and speed tiers" · [source](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-6-astra.html) |
| 30 Sep | Anthropic (Claude Code gateway) | Claude Code v2.1.286 fixes two under-counts in the gateway spend meter: 1-hour cache writes priced at the 5-minute rate, and streamed turns with a server-side tool counting only the first call's input. Nobody was over-billed, but a spend limit could trip later than set. | `finops-ai-dev-tools.md`, "Cost tracking for Claude Code" · [source](https://github.com/anthropics/claude-code/releases/tag/v2.1.286) |
| 29 Sep | Azure (Advisor commitment recommendations) | Savings plan and reservation recommendations, P3 reservations included, are produced at management group scope in the portal and the REST endpoints, aggregating every subscription under the group. Summing per-subscription recommendations by hand over-commits. | `finops-azure-commitments-sizing.md`, "Commitment sizing methodology - granularity, Advisor calibration, tooling" · [source](https://techcommunity.microsoft.com/blog/finopsblog/now-available-management-group%E2%80%93scoped-savings-plan-and-reservation-recommendatio/4560869) |
| 28 Sep | Anthropic (Claude Sonnet 5.5) | Claude Sonnet 5.5 launches at the Sonnet 5 rate, with cache reads at 0.05x input against 0.1x on Sonnet 5. It carries breaking API changes from Sonnet 5, so the upgrade is an engineering change at constant unit cost. | `finops-anthropic.md`, "Base token pricing: tiers and ratios" · [source](https://platform.claude.com/docs/en/about-claude/pricing) |
| 25 Sep | AWS (Billing and Cost Management) | The ListBillingViewSegments API returns an account's billing context over a period, in time segments naming the management account, billing transfer account and billing-group primary account that applied. Run it before reconciling a month in which an account changed organisation or billing group. | `finops-aws-billing.md`, "Billing transfer" · [source](https://aws.amazon.com/about-aws/whats-new/2026/09/aws-billing-and-cost-management-billing-context-api/) |
| 25 Sep | Azure (Reserved VM Instances) | Microsoft's retirement page makes new or renewed 1-year and 3-year reservations unavailable on all affected A, B, D, E, F and L variants of v1 to v3. Existing reservations run to term, then usage falls to pay-as-you-go unless a Compute Savings Plan absorbs it. | `finops-azure-commitments.md`, "Compute commitment instruments" · [source](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/lifecycle/retirements-and-capacity-restrictions) |
| 25 Sep | AWS (Enterprise Support (Billing API)) | The AWS Billing API now breaks the Enterprise Support charge down per linked account, prorated by time on the plan, with a flag saying whether the month's charge is estimated or final. The split no longer requires a support case. | `finops-allocation-showback.md`, "Provider support fees" · [source](https://aws.amazon.com/blogs/aws-cloud-financial-management/programmatically-understand-your-aws-enterprise-support-charges-with-the-aws-billing-api/) |
| 24 Sep | Anthropic (Claude API refusal billing) | A refusal that arrives before any output is now billed at the model's normal rates in three categories (bio, frontier_llm, reasoning_extraction), on every platform that serves Claude. With a fallback model, the refused attempt is billed on top of the retry. | `finops-anthropic.md`, "Refusals and fallback billing" · [source](https://platform.claude.com/docs/en/release-notes/api) |
| 22 Sep | Anthropic (Claude Opus 5.5) | Claude Opus 5.5 launches at 0.8x the Opus 5 rate, with cache reads at 0.05x input, half the standard multiplier. It is the first break in the Opus list rate in five generations, so moving a cache-heavy workload from Opus 5 is a rate cut. | `finops-anthropic.md`, "Base token pricing: tiers and ratios" · [source](https://platform.claude.com/docs/en/about-claude/pricing) |
| 21 Sep | AWS (Bedrock quotas) | The per-model daily token quota on bedrock-runtime is replaced by one Cross-Model Max Tokens Per Day pool per account and Region, counted from on-demand pricing. Tokens per minute stay per model, so one runaway job on any model can exhaust the day for every workload in that account. | `finops-bedrock.md`, "CloudWatch metrics for Bedrock" · [source](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-runtime.html) |
| 18 Sep | AWS (Billing Conductor) | AWS publishes a method that credits each member account its RI and Savings Plan saving from CUR 2.0 as a custom line item, because commitments bought in the management account leave billing-group pro forma bills at on-demand equivalent by default. | `finops-chargeback.md`, "Commitment benefits in an AWS Billing Conductor pro forma" · [source](https://aws.amazon.com/blogs/aws-cloud-financial-management/implementing-proportional-reserved-instance-and-savings-plans-chargeback-with-aws-billing-conductor/) |
| 18 Sep | AWS (Amazon Bedrock (Kimi K3)) | Kimi K3 is on Amazon Bedrock, the first open-weight model there with explicit prompt caching. Bedrock bills one 30-minute cache write at 1.25x input next to the 0.1x read, while Moonshot direct bills writes by TTL (1x for 5 minutes, 2x for 1 hour). | `finops-open-weight-vendors.md`, "Kimi (Moonshot): the proof that open weight does not imply cheap" |
| 16 Sep | Snowflake (Cortex AI per-user quotas) | Per-user quotas gain a weekly limit, generally available, alongside daily and monthly cycles. It follows the ISO week and resets on Monday at 00:00 UTC; with block enforcement on, a user is blocked on reaching any of the limits. | `finops-snowflake.md`, "Cortex AI cost governance" · [source](https://docs.snowflake.com/en/release-notes/2026/other/2026-09-16-weekly-per-user-quota-limits) |
| 15 Sep | AWS (Direct Connect) | 10 and 100 Gbps dedicated connections can bill at a flat hourly rate per bandwidth and tier, with data transfer out included from the Regions the tier covers. Traffic from other Regions, SiteLink and partner fees still bill separately. | `finops-aws-patterns-networking.md`, "Direct Connect flat-rate pricing" · [source](https://docs.aws.amazon.com/directconnect/latest/PricingGuide/pricing-flat-rate.html) |
| 15 Sep | AWS (Billing Conductor) | SKU-scoped pricing rules can carry a custom absolute rate and custom usage-tier thresholds, not only a mark-up or mark-down on public on-demand rates. A reseller or central IT team can mirror a negotiated or internal rate card in the pro forma view; the AWS invoice is unchanged. | `finops-aws-billing.md`, "The four mechanisms" · [source](https://aws.amazon.com/about-aws/whats-new/2026/09/AWS-Billing-Conductor-custom-rates-usage-tier/) |
| 15 Sep | Snowflake (Cortex AI Gateway) | Cortex AI Gateway enters public preview: a governed endpoint for applications and third-party agents to reach models. Consumption is recorded per request (gateway, user, model, tokens) in ACCOUNT_USAGE.AI_GATEWAY_USAGE_HISTORY, the attribution source for showback. | `finops-snowflake.md`, "Cortex AI cost governance" · [source](https://docs.snowflake.com/en/release-notes/2026/other/2026-09-15-cortex-ai-gateway) |
| 10 Sep | AWS (AWS FinOps Agent) | AWS FinOps Agent enters public preview, with a four-tier autonomy ladder from read-only insights to bounded autonomy. Autonomy is granted per action type, and the top tier is still capped by a maximum financial impact. | `finops-agentic.md`, "Agentic cost anatomy - where the tokens go" |
| 9 Sep | AWS (Lambda Managed Instances) | Lambda Managed Instances, which bills through EC2 pricing, supports Graviton5 C9g, C9gd, M9g and M9gd instances. AWS states up to 25% better compute performance than Graviton4, a performance claim and not a price cut; a capacity provider pinned to an older instance type does not move on its own. | `finops-aws-patterns-compute.md`, "Compute Optimization Patterns (42)" · [source](https://aws.amazon.com/about-aws/whats-new/2026/09/aws-lambda-graviton5-ec2/) |
| 3 Sep | AWS (CloudFront) | Flat-rate plan subscription, upgrade, downgrade and cancellation can be managed through the CLI, SDKs, CloudFormation, CDK or the PricingPlanManager API, no longer console-only. Paid plans support a two-phase flow: create the plan, then approve it to start billing. | `finops-aws.md`, "Operational gotchas" · [source](https://aws.amazon.com/about-aws/whats-new/2026/09/cloudfront-flat-rate-pricing-plans-api/) |
| 1 Sep | Anthropic (Claude Sonnet 5) | Anthropic cancelled in August 2026 the 50% increase scheduled for Sonnet 5 on 1 September 2026: the introductory rate is now the standard rate. Budgets built on it stay valid, and Sonnet 5 sits at 0.4x the Opus 5 rate instead of 0.6x. | `finops-anthropic.md`, "Base token pricing: tiers and ratios" · [source](https://platform.claude.com/docs/en/about-claude/pricing) |
| Sep | Google Cloud (Cloud Billing) | The Cloud Billing console has an Incentives page tracking conditional contract credits: spend-based milestone credits, Incremental Workload Credits and RaMP incentives, each with end date, spend target, progress and status. The tracker lags by up to three days. | `finops-gcp.md`, "Incentives page - tracking conditional contract credits" · [source](https://docs.cloud.google.com/billing/docs/how-to/incentives-program-tracker) |
| Sep | Databricks (AI Gateway external models) | A price multiplier can be set on an external model provider service so Databricks spend estimates reflect a negotiated discount instead of list rates. It applies only to requests made after it is set, and not to Databricks-hosted partner models. | `finops-databricks.md`, "Model serving attribution" · [source](https://docs.databricks.com/aws/en/ai-gateway/create-model-provider-services) |
| Sep | Databricks (SQL warehouses) | system.query.history and query tags are generally available. Clients of a shared SQL warehouse can tag each query, so the warehouse's DBUs can be split by team pro rata to query execution time, as an apportionment and not a metered figure. | `finops-databricks.md`, "Query-level attribution on SQL warehouses" · [source](https://docs.databricks.com/aws/en/release-notes/product/2026/september) |

## August 2026

Changes dated August 2026, newest first.

| Date | Who | What changed for the bill | Read more |
|---|---|---|---|
| 31 Aug | Google Cloud (BigQuery) | BigQuery restored daily token quotas for its Gemini-based generative AI functions (embedding functions excluded), per project and per user. The defaults are very high, so the quota caps spend only once a stricter override is set. | `finops-gcp.md`, "BigQuery commitments (separate from Compute CUDs)" · [source](https://docs.cloud.google.com/bigquery/docs/release-notes#August_31_2026) |
| Aug | AWS (Billing and Cost Management) | Billing and Cost Management offers five Managed Dashboards (Cost Overview, Trends, Compute, Database, Reservations and Savings Plans), pre-populated with account data at no additional cost and with no setup. They are read-only, can be duplicated into editable copies and export to PDF or CSV. | `finops-aws-billing.md`, "AWS Managed Dashboards (zero-setup native visibility)" · [source](https://aws.amazon.com/about-aws/whats-new/2026/08/aws-billing-and-cost-management-managed-dashboards/) |
| Aug | AWS (Bedrock IAM Principal Cost Allocation) | IAM Principal Cost Allocation covers inference on the bedrock-mantle endpoint as well as bedrock-runtime, with no additional setup once caller-identity allocation is enabled. Caller-based cost attribution in CUR 2.0 and Cost Explorer now reaches inference routed through bedrock-mantle. | `finops-bedrock.md`, "Tagging strategy for Bedrock" · [source](https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-iam-principal-tracking.html) |
| Aug | AWS (Bedrock AgentCore) | AgentCore memory, policy and the managed harness are available in AWS GovCloud (US-West). The managed harness bundles compute, environment and observability into API calls, a new cost surface to attribute; GovCloud rates commonly differ from commercial-Region rates. | `finops-bedrock.md`, "AgentCore in GovCloud - regulated-workload cost governance" |
| Aug | Google Cloud (Flexible committed use discounts) | Flexible GPU commitments can apply across services, not only within a single service. A team commits to GPU spend once and the discount applies across qualifying services, so the commitment holds up better when AI workloads move. | `finops-gcp.md`, "Committed Use Discounts (CUDs) - resource-based vs spend-based" · [source](https://cloud.google.com/compute/docs/instances/signing-up-flexible-committed-use-discounts) |
| Aug | Google Cloud (Cloud Billing Reports) | Billing Reports add an Originating products filter and group-by dimension and a Gemini Enterprise preset report, for native attribution of AI consumption. It is console only: the field is not in the BigQuery billing export. | `finops-vertexai.md`, "GCP Billing and BigQuery export" · [source](https://docs.cloud.google.com/billing/docs/how-to/reports/gemini-enterprise-costs) |

<!-- whats-new:end -->

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
