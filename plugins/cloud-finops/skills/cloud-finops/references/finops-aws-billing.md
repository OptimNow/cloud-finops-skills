---
name: finops-aws-billing
fcp_domain: "Understand Usage & Cost"
fcp_capability: "Data Ingestion"
fcp_capabilities_secondary: ["Allocation", "Reporting & Analytics", "Anomaly Management", "Budgeting", "Invoicing & Chargeback", "Governance, Policy & Risk"]
fcp_phases: ["Inform", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Finance"]
fcp_personas_collaborating: ["Engineering", "Procurement"]
fcp_maturity_entry: "Crawl"
business_coverage: ["aws:bill:deep", "aws:budget:deep"]
---

# AWS Billing Data, Allocation and Governance

> AWS cost data and the controls around it: CUR and Data Exports for FOCUS, Cost
> Explorer, the Pricing Calculator, managed dashboards, Cost Anomaly Detection, account
> structure, tagging and Cost Categories, AWS Config, SCPs including cost-preventive
> ones, Budgets, spend limits, the AWS FinOps Agent, Extended Support audits, the
> billing hierarchy and separate invoices, and multi-organisation billing. Usage
> optimisation (rightsizing, SageMaker, databases, CloudFront flat-rate plans, S3
> Files) is in `finops-aws.md`; commitments are in `finops-aws-commitments.md`.

---

## AWS cost data foundation
<!-- src:37b46c22605776cb -->

### Cost and Usage Report (CUR)

CUR is the most granular billing data source AWS provides. For attribution and custom
tooling, build on CUR; the console is for ad-hoc views.

**Why CUR over Cost Explorer API:**
- Line-item granularity - every resource charge, every hour
- Includes resource tags, usage types, and pricing details not available in Cost Explorer
- Exportable to S3 for integration with third-party tools, Athena, or Redshift

**CUR setup checklist:**
- [ ] Enable CUR (or CUR 2.0 via AWS Data Exports - see below) in the management (payer) account
- [ ] Configure S3 bucket with appropriate retention and access policies
- [ ] Enable resource IDs (required for tag-level allocation)
- [ ] Select hourly granularity (daily is insufficient for anomaly detection)
- [ ] Enable Athena integration for SQL-based analysis

### AWS Data Exports for FOCUS 1.2

AWS Data Exports is the modern delivery mechanism for billing data, replacing the legacy
CUR for new deployments. As of **19 November 2025**, AWS Data Exports for FOCUS 1.2 is
generally available - the canonical path for FOCUS-conformant cost data on AWS.

**What this means in practice:**
- New customers should set up Data Exports for FOCUS 1.2 directly, not legacy CUR + FOCUS
  format flag.
- Existing CUR consumers can run CUR and Data Exports in parallel during transition.
- FOCUS 1.2 data flows into the same S3-backed pattern: configure once, query via Athena
  or any FOCUS-aware tool.
- For multi-cloud customers, the FOCUS 1.2 schema aligns with Azure Cost Management's
  FOCUS 1.2 preview and GCP's FOCUS 1.0 / 1.2 preview export (the exports still
  diverge in Tags shape, precision and column set; see `finops-focus.md`), enabling cross-cloud
  normalisation in a single warehouse.

**Cross-account delivery (March 2026, GA).** AWS Data Exports now supports
delivery directly to an S3 bucket in a different (authorised) account. This is
the path AWS-native landing zones and centralised FinOps warehouses have been
asking for: payer accounts can publish FOCUS 1.2 / CUR 2.0 exports straight into
the FinOps team's analytics account without an intermediate copy step or a
cross-account replication rule. Configure via the destination bucket policy on
the receiving side and the export configuration on the source side.
- Removes the previous "copy from payer S3 to analytics S3" pipeline that many
  organisations had to operate themselves.
- Simplifies the IAM model: one bucket policy on the analytics side rather than
  per-payer-account IAM roles.
- Especially useful for organisations that consolidate billing across multiple
  AWS Organizations (M&A integrations, multi-payer setups, partner-resold
  accounts).

**SQL-based row filtering at the source.** AWS Data Exports has supported SQL
row filtering (a `WHERE` clause on the CUR 2.0 table) alongside column
selection since its launch in November 2023. It is an existing capability, not
a recent one, but it is under-used: an AWS how-to published on 26 August 2026
shows how to automate pre-filtered per-account or per-service exports at the
source, without a custom Lambda / Glue / Athena post-processing pipeline. Where
this pays off:
- Partner sharing - publish a dataset scoped to only the accounts or services a
  partner is entitled to see.
- Program or cost-centre isolation - a pre-filtered export per program without a
  downstream copy step.
- Audit scoping - hand auditors a dataset limited to the rows in scope rather
  than the full CUR.

Filtering at the source reduces the operational overhead of sharing scoped cost
data and removes the need for organisations to maintain their own filtering
pipeline. Source (AWS how-to, 26 August 2026):
https://aws.amazon.com/blogs/aws-cloud-financial-management/automating-filtered-cost-and-usage-report-exports-with-aws-data-exports/

Sources: https://aws.amazon.com/about-aws/whats-new/2025/11/aws-data-exports-focus-1-2-available/
and https://aws.amazon.com/about-aws/whats-new/2026/03/aws-data-exports-cross-account-delivery-cost/

**Common CUR analysis queries (Athena):**
```sql
-- Top 10 services by cost, current month
SELECT line_item_product_code,
       ROUND(SUM(line_item_unblended_cost), 2) AS total_cost
FROM cur_table
WHERE month = MONTH(CURRENT_DATE) AND year = YEAR(CURRENT_DATE)
GROUP BY line_item_product_code
ORDER BY total_cost DESC
LIMIT 10;

-- Untagged resources by cost
SELECT line_item_resource_id,
       line_item_product_code,
       ROUND(SUM(line_item_unblended_cost), 2) AS cost
FROM cur_table
WHERE resource_tags_user_environment IS NULL
  AND line_item_line_item_type = 'Usage'
GROUP BY 1, 2
ORDER BY cost DESC;
```

### AWS Cost Explorer

Cost Explorer provides pre-built visualisations and the Cost Explorer API for
programmatic access. It is the right tool for quick analysis and reporting; CUR is the
right tool for detailed attribution and custom tooling.

**Cost Explorer capabilities and limitations (as of April 2026):**
- 24-48 hour data lag (unacceptable for real-time AI cost management)
- **Hourly granularity** is now an opt-in feature in Cost Explorer (no longer API-only).
  Enable per management account; data retained 14 days. Source:
  https://docs.aws.amazon.com/cost-management/latest/userguide/ce-services-hourly.html
- **Resource-level daily granularity** is also an opt-in feature - exposes per-resource
  daily cost without requiring the legacy "resource-level data" paid tier. Retention
  and limits documented per service. Source:
  https://docs.aws.amazon.com/cost-management/latest/userguide/ce-resource-daily.html
- API queries are charged ($0.01 per request)
- For programmatic deep analysis, CUR / Data Exports remain the right tool - Cost
  Explorer is for visualisation and pre-built recommendations

**Useful Cost Explorer features:**
- **Rightsizing recommendations** - EC2 rightsizing based on CloudWatch utilisation
- **Savings Plans recommendations** - commitment purchase recommendations based on usage
- **Cost anomaly detection** - ML-based anomaly alerts (set up before you need them)
- **Cost categories** - virtual tags for billing-layer cost allocation
- **Bedrock product attributes** (since 8 October 2026) - group and filter Bedrock cost
  by model, model provider, inference type and feature in Cost Explorer, Budgets and
  Dashboards; the attribute keys, the 1 September 2026 data start and the known gaps
  are in `finops-bedrock.md`, "Cost Explorer integration"

### AWS Pricing Calculator in the console (estimates on your own rates)

The Pricing Calculator inside the Billing and Cost Management console is a different
tool from the public calculator.aws site. It needs an account and has its own APIs,
and it is the one that can price an estimate on the organisation's own rates rather
than list prices. It produces two kinds of estimate:

| | Workload estimate | Bill estimate |
|---|---|---|
| What it models | The added usage of one workload; nothing outside it is counted | The whole consolidated bill: last month's usage, active Savings Plans and RIs, sharing preferences, discounts and credits as on the latest anniversary bill, plus the changes you model |
| Who can run it | Standalone, management and member accounts | Management and standalone accounts only |
| Commitments | Cannot model new commitments; can apply existing coverage | Add, change or remove EC2 RIs and Compute or EC2 Instance Savings Plans without touching the real bill |
| Speed | Immediate | 20 minutes to 12 hours per run |
| Cost (as of October 2026) | Free | 5 free per month, then $2 each |

Workload estimates are priced at one of three **rate types**: before discounts, after
discounts (the organisation's volume and pricing discounts, and tiering), or after
discounts and purchase commitments (Savings Plan and RI coverage percentages taken from
last month's usage). A management account sets the rate type its member accounts see.
The rates refresh from the last completed anniversary bill and are available by the 15th
of the month. Usage can be imported from the account's own cost and usage data or from
a public-calculator share link (Savings Plans or RIs in a public estimate are dropped on
import).

**How to use it for a decision.** Build one workload estimate, duplicate it, change one
variable (Graviton against x86, a different instance family, another Region), and read
the two side by side; keep both in the same Region unless the Region is the variable.
For a commitment purchase, a bill estimate shows the effect on the whole bill, which a
workload estimate cannot. Two limits shape the routine: a bill scenario goes stale after
the last day of the month it was created in and can no longer run, and an account can
create 50 workload estimates a month. The estimate is an input to the forecast, not the
forecast itself (`finops-forecasting.md`).

Sources: [AWS Cloud Financial Management blog, 6 October 2026](https://aws.amazon.com/blogs/aws-cloud-financial-management/estimate-and-compare-aws-costs-with-the-aws-pricing-calculator-part-1-creating-and-comparing-workload-estimates/),
[Pricing Calculator user guide](https://docs.aws.amazon.com/cost-management/latest/userguide/pricing-calculator.html),
[rate types](https://docs.aws.amazon.com/cost-management/latest/userguide/pc-rates-discounts.html),
[bill estimates](https://docs.aws.amazon.com/cost-management/latest/userguide/pc-bill-estimate.html),
[quotas](https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html)
(all read 16 October 2026).

### AWS Managed Dashboards (zero-setup native visibility)

As of August 2026, AWS Billing and Cost Management offers a set of curated
Managed Dashboards that come pre-populated with your account data at no
additional cost and require no setup. There are five dashboards: Cost Overview,
Trends, Compute, Database, and Reservations and Savings Plans.

**Why this matters for FinOps:**
- A fast-start visibility baseline for organisations beginning or standardising
  their FinOps practice - a zero-setup native alternative or complement to
  custom CUR / Data Exports-based dashboards. Particularly useful at Crawl
  maturity, before a team has invested in Athena or a warehouse pipeline.
- Dashboards are read-only, but any dashboard can be duplicated into an editable
  custom copy for customisation.
- Exportable via PDF and CSV for sharing with Finance and stakeholders.

Managed Dashboards do not replace CUR / Data Exports for detailed attribution
and custom tooling - they are the quick-win visibility layer, not the granular
data foundation.

Source: https://aws.amazon.com/about-aws/whats-new/2026/08/aws-billing-and-cost-management-managed-dashboards/

### AWS Cost Anomaly Detection

Set up before an incident occurs. AWS Cost Anomaly Detection uses ML to identify
unexpected spending increases and sends alerts via SNS or email.

**Configuration recommendations:**
- Create monitors at the service level and the linked account level
- Set alert threshold at an absolute dollar amount, not just percentage
  (a 100% increase on $10 is $10; a 20% increase on $50,000 is $10,000)
- Route alerts to both the FinOps practitioner and the engineering team lead
- Review alert history monthly - tune thresholds to reduce false positives

**Automated spend guardrails: Budgets Actions and the access circuit breaker.**
AWS Budgets Actions natively support three responses when a budget threshold is
crossed: apply an IAM policy, apply an SCP, or stop EC2 / RDS instances. An AWS
how-to published on 1 September 2026 extends the idea to developer access
itself, which native actions do not cover: a budget alert publishes to SNS, and
a Lambda function then removes the user's IAM Identity Center permission-set
assignment or swaps it for a read-only one, with an audit trail. It is custom
automation on top of a Budgets alert, not a new Budgets Action type, so it needs
owning like any other Lambda. Treat both the native actions and the circuit
breaker as a complement to the reactive anomaly and budget alerts above, not a
replacement - they are the preventive backstop that acts without waiting for a
human. Source (AWS how-to, 1 September 2026):
https://aws.amazon.com/blogs/aws-cloud-financial-management/how-to-programmatically-manage-account-access-with-aws-budgets-alerts/

---

## AWS cost allocation

### Account structure for cost allocation

The cleanest cost allocation model uses AWS accounts as the primary allocation boundary.

**Recommended patterns:**
- One account per environment per workload (prod, staging, dev separate accounts)
- Shared services in a dedicated account with cross-account cost sharing methodology defined
- Sandbox accounts with budget limits and auto-termination policies

**Multi-account cost aggregation:**
Use AWS Organizations and the management account CUR for consolidated billing.
Cost Categories in Cost Explorer can create virtual tags across accounts.

### Tagging for AWS cost allocation

See `finops-tagging.md` for the full tagging strategy. AWS-specific notes:

- AWS propagates some tags to billing automatically - verify which tags appear in CUR
- Tag propagation is not instant - allow 24 hours for new tags to appear in billing
- Some services do not support tagging (AWS Support, Route 53 Hosted Zones, some
  data transfer charges) - account tags (below, "OU synchronisation") now cover them
  at account level; use Cost Categories for anything finer
- Enable "Tag policies" in AWS Organizations to enforce tag key capitalisation consistency
- **IAM Principal Cost Allocation (2026):** tags applied to IAM users and roles can be
  propagated to CUR 2.0 and Cost Explorer with an `iamPrincipal/` prefix, enabling
  caller-based attribution when resource-level tags are not sufficient. Primary use case
  today is Amazon Bedrock - see `finops-bedrock.md` for setup, CUR size implications,
  and when to use it vs. account separation

### Cost Categories

AWS Cost Categories create allocation rules without requiring physical tags.
Use them for:
- Shared service allocation (split NAT Gateway cost by team account usage)
- Account-level allocation when resource-level tagging is incomplete
- Retroactive allocation adjustments

**Cost Categories are a reporting layer only.** They group cost in Cost Explorer,
Budgets, CUR / Data Exports and Cost Anomaly Detection, and they have no effect on the
AWS invoice. If the requirement is a separate invoice per business unit, the mechanism
is Invoice Configuration - see "AWS billing hierarchy and separate invoices" below.

---

## AWS governance tools

### AWS Config

Use AWS Config for continuous compliance monitoring of tagging and configuration standards.

**Useful managed rules for FinOps:**
- `required-tags` - flags resources missing specified mandatory tags
- `ec2-instance-no-public-ip` - governance + potential cost reduction (NAT vs public IP)
- `s3-bucket-versioning-enabled` - data protection governance
- `restricted-ssh` - security governance

### Service Control Policies (SCPs)

SCPs in AWS Organizations can prevent resource creation without required tags.

**Example SCP - deny EC2 launch without Environment tag:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyEC2WithoutEnvTag",
    "Effect": "Deny",
    "Action": "ec2:RunInstances",
    "Resource": "arn:aws:ec2:*:*:instance/*",
    "Condition": {
      "Null": {
        "aws:RequestTag/Environment": "true"
      }
    }
  }]
}
```

**Important:** Test SCPs in a sandbox OU before applying to production. SCPs cannot be
overridden by account-level IAM policies - a misconfigured SCP can block legitimate
operations across all accounts in the OU.

### Cost-preventive SCPs: blocking expensive and long-term-effect IAM actions

Budget alerts and anomaly detection are reactive - they fire after spend has started.
A complementary preventive control is to deny, at the organisation level, the small set
of IAM actions that create large recurring charges or binding commitments with a single
API call. Both layers are needed: detection catches gradual drift and unknown workloads;
prevention removes the one-call disasters entirely.

The high-risk actions fall into three categories (magnitudes below are indicative only -
verify current pricing before relying on them):

**1. Financial commitments.** One API call creates a binding spend obligation - often
one to three years - that no delete operation can undo. Examples:
`savingsplans:CreateSavingsPlan`, `ec2:PurchaseReservedInstancesOffering`,
`route53domains:RegisterDomain`, `aws-marketplace:Subscribe`,
`shield:CreateSubscription`. The FinOps risk is commitment liability: a Savings Plan
purchased from a sandbox account is a multi-year payment obligation, not a resource
you can terminate.

**2. High fixed-cost resources billed from creation.** These charge a substantial flat
rate from the moment they exist, regardless of usage - indicatively hundreds of dollars
per month per resource, and tens of thousands per month at full scale for provisioned
model throughput. Examples: `acm-pca:CreateCertificateAuthority`,
`bedrock:CreateProvisionedModelThroughput`, `ses:PutDeliverabilityDashboardOption`,
`kendra:CreateIndex`. The FinOps risk is recurring spend with no usage signal: an idle
private CA or an unused Kendra index shows zero activity in usage dashboards while
billing at full rate.

**3. Irreversible long-term locks.** Once applied, these cannot be removed - not even
by AWS Support. Examples: `glacier:CompleteVaultLock`,
`backup:PutBackupVaultLockConfiguration`. The FinOps risk is irreversibility: a
compliance-mode vault lock applied by mistake commits you to paying for that storage
for the full retention period.

**Example SCP - deny high-cost actions with an exemption for approved teams:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyCostCommittingActions",
    "Effect": "Deny",
    "Action": [
      "savingsplans:CreateSavingsPlan",
      "ec2:PurchaseReservedInstancesOffering",
      "route53domains:RegisterDomain",
      "aws-marketplace:Subscribe",
      "acm-pca:CreateCertificateAuthority",
      "bedrock:CreateProvisionedModelThroughput",
      "kendra:CreateIndex",
      "glacier:CompleteVaultLock",
      "backup:PutBackupVaultLockConfiguration"
    ],
    "Resource": "*",
    "Condition": {
      "StringNotEquals": {
        "aws:PrincipalTag/CostGuardrailExempt": "true"
      },
      "ArnNotLike": {
        "aws:PrincipalArn": "arn:aws:iam::*:role/finops/*"
      }
    }
  }]
}
```

The two condition operators are ANDed, so the deny applies only to principals that
carry neither exemption - a principal tagged `CostGuardrailExempt=true` or assuming a
role under the `/finops/` path passes through.

**Segmentation - do not apply one policy everywhere:**
- **Sandbox and dev OUs:** apply the full deny list. Nobody experimenting in a sandbox
  has a legitimate need to purchase a Reserved Instance or lock a backup vault.
- **Production OUs:** restrict commitment-purchase actions to a dedicated FinOps or
  procurement role rather than denying outright. Denying
  `savingsplans:CreateSavingsPlan` across the whole organisation blocks legitimate
  commitment management - the exemption principal is not optional, it is the mechanism
  that keeps the commitment pipeline working.
- Fixed-cost resource creation (private CA, provisioned throughput, Kendra) can stay
  denied in production too, behind a request workflow, since these are deliberate
  architectural decisions rather than day-to-day operations.

**Living source:** the canonical community list of expensive and long-term-effect IAM
actions is Ian Mckay's gist
([List of expensive / long-term effect AWS IAM actions](https://gist.github.com/iann0036/b473bbb3097c5f4c656ed3d07b4d2222)).
It is community-maintained and evolves as AWS ships new services - re-check it before
implementing, and treat it as a starting point, not an exhaustive catalogue.

### AWS Budgets

Configure at minimum:
- Account-level monthly cost budget with 80% and 100% alerts
- Service-level budgets for top 3-5 cost drivers
- Anomaly detection monitor linked to cost anomaly detection

**Recommended alert recipients:** Both the FinOps practitioner and the engineering team
lead for the relevant account. FinOps-only alerts create a bottleneck; engineering-only
alerts lack financial context.

### Spend limits in AWS Settings (limited release)

Checked 11 October 2026: AWS is releasing this to "a limited number of customers" inside
the new AWS Settings experience, where a project wraps one AWS account. Treat
availability as account-specific until the banner on the AWS docs page comes down.

A spend limit is a monthly, pre-tax ceiling set per project, excluding credits, and AWS
describes it as "a type of AWS Budgets". It needs a Paid Plan, applies to at most 10
projects, and the minimum is the greater of $20 or AWS's own conservative estimate of
the project's likely spend, so a project already running several instances cannot set a
tight limit without stopping them first. Notifications fire at 50%, 75% and 90% of
actual cost and when the forecast reaches the limit within 10 days.

**At the limit, AWS pauses the project and stops all its resources.** Data is kept; the
owner reactivates by raising the limit and may have to restart resources by hand. A
project left paused for 90 days has its data permanently deleted. The documentation does
not say which charges continue during a pause; assume storage, snapshots and anything
not stopped still bills, and treat the ceiling as covering compute-shaped spend.

Three optional early controls act on the forecast rather than the actual:

| Control | When | What it does | Mechanism |
|---|---|---|---|
| Stop new resource launches | About 7 days before the forecast limit | New launches fail; running resources stay. Auto scaling cannot scale out | An AWS-managed SCP denying create and start actions across compute, database, storage and SageMaker |
| Pause idle resources | About 5 days before | Stops EC2 instances, RDS MySQL and PostgreSQL instances and SageMaker endpoints that meet Compute Optimizer's 14-day idle criteria | Compute Optimizer recommendations |
| Pause top cost drivers | About 4 days before | Pauses the highest-cost active resources among EC2, RDS, Lambda, Bedrock and SageMaker. AWS calls it disruptive and opt-in | For Lambda, Bedrock and SageMaker inference, the published managed SCPs deny the invoke actions, so "pause" means every call in the project is refused |

**Latency, stated as an inference.** The docs give no evaluation cadence. AWS Budgets
data refreshes up to three times a day, 8 to 12 hours apart, and Cost Anomaly Detection
reads Cost Explorer data with up to 24 hours of delay. A spend limit sits on the same
feed, so it bounds the month but does not see a burst earlier than an anomaly alert
does. For the fast-burn services, the earlier levers stay in place: Bedrock
tokens-per-minute quotas act on every request, CloudWatch alarms on `AWS/Bedrock` token
metrics act within minutes, invocation logging names the caller, and a Budgets Action or
the spend limit is the backstop (see `finops-anomaly-management.md` and the
agent-loop playbook).

**Where it fits.** Sandboxes, training accounts, side projects and dev or test
environments that can tolerate a stop measured in hours: enable the limit with the first
two controls, and put a reminder before day 90 on any paused project. Production is a
poor fit by AWS's own framing ("when it is acceptable to have a brief pause"): the
trigger is a forecast on billing data, so a revenue spike pauses the service, and the
third control pauses the resource that is the product. For production, keep the Budgets
Actions and cost-preventive SCPs above, with quotas and alarms on the fast-burn
services. The Vertex AI file documents Google's project cap with the same warning: a
shared ceiling turns a runaway prototype into a production outage on a billing
threshold.

Sources: <https://docs.aws.amazon.com/accounts/latest/reference/create-spend-limit.html>,
<https://docs.aws.amazon.com/accounts/latest/reference/update-spend-limit.html>,
<https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html#scps-for-spend-limits>,
<https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html>

### AWS FinOps Agent and the automation ladder

AWS introduced the **AWS FinOps Agent** at FinOps X 2026; it is in **public preview** as
of 10 September 2026, so treat its scope and pricing as unsettled. It packages built-in
FinOps workflows (anomaly investigation, cost reporting, optimisation summaries) over
the existing Billing and Cost Management services, runs continuously rather than on
request, delivers to email, Slack or Jira, and acts only within the IAM permissions it
is given.

More durable than the product is the four-tier ladder AWS published with it, because it
maps onto native tools that are already generally available:

| Tier | What is automated | Native example | Trust lever |
|---|---|---|---|
| 1. Read-only insights | Reporting, anomaly investigation | Agent correlating Cost Anomaly Detection alerts with CloudTrail events | Transparency - the reasoning is shown |
| 2. Human-approved mutation | One action, one approval | Compute Optimizer one-click idle EBS cleanup; Budget Actions applying an IAM policy or SCP after approval | Preview and simulate before the change |
| 3. Rule-based automation | Recurring actions under your rules | Compute Optimizer EBS automation with tag and region exclusions, snapshot before delete | Permission control - scope what is in and out |
| 4. Autonomy with boundaries | Continuous monitoring, reporting, ticketing | FinOps Agent within IAM scope | Blast-radius caps (account, region, maximum financial impact) and rollback |

**How to use it.** Climb one tier at a time and per action type, not per tool: an estate
can sit at tier 3 for unattached EBS volumes and tier 1 for everything touching
commitments. Tier 1 is a Crawl-stage action with no downside. Tiers 3 and 4 presuppose
tagging good enough to write exclusion rules against - automation over an untagged
estate deletes things nobody can identify as needed. Note what is absent from every
tier: commitment purchases. Savings Plans Purchase Analyzer simulates, it does not buy.

See `finops-agentic.md` for the vendor-neutral reasoning on policy generation versus
direct mutation. Source:
https://aws.amazon.com/blogs/aws-cloud-financial-management/automation-and-trust-in-finops/

### Extended Support version audits (recurring action item)

Several AWS services charge an Extended Support surcharge for domains, clusters, or
instances left on end-of-standard-support versions. This is the "outdated resource
incurring extended support charges" pattern - see `finops-aws-patterns-compute.md` (EKS)
and `finops-aws-patterns-databases.md` (OpenSearch, ElastiCache).

Make version audits a recurring FinOps action item:
- Audit Amazon OpenSearch Service domains for legacy Elasticsearch (1.5-7.8) and
  OpenSearch (1.0-1.2, 2.3-2.9) versions still incurring Extended Support charges.
- As of August 2026, AWS extended Extended Support patch coverage for these legacy
  versions by 12 months to November 2027, but from November 2026 the Extended Support
  surcharge rises to equal 100% of instance pricing (a 2x effective compute cost for
  domains still on old versions). Newer versions (ES 6.8/7.9/7.10, OpenSearch 1.3,
  2.11-2.19) have their own Standard/Extended Support windows ranging 1-3 years.
- Audit ElastiCache caches on Redis OSS 4 and 5 (paid Extended Support since
  1 February 2026) and 6 (from 1 February 2027). Reserved nodes do not discount the
  charge; see `finops-aws-patterns-databases.md`.
- AWS revises these support windows periodically - always check the current support
  dates before budgeting rather than relying on a cached table.

Source: https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-opensearch-service-additional-upgrade-runway-support-dates

**RDS for MySQL and PostgreSQL, and Aurora: prevent the charge at creation.** RDS
Extended Support charges begin "the day after the RDS end of standard support
date", apply to standby instances in Multi-AZ deployments, and stop when the
database is upgraded to a version in standard support or deleted; they restart if
that version later enters Extended Support. Extended Support runs for up to 3
years past the end of standard support, after which RDS upgrades the major version
automatically. Enrolment is the `EngineLifecycleSupport` parameter, and the
default enrols: a database created or restored without the setting is moved into
paid Extended Support when its version reaches end of standard support. To opt
out, pass `open-source-rds-extended-support-disabled` at create or restore time
(`--engine-lifecycle-support` in the CLI, `engine_lifecycle_support` on the
Terraform `aws_db_instance` and `aws_rds_cluster` resources, whose default is the
enrolling value). With the opt-out set, creating a database on a major version
already past its end of standard support fails, so the module default works as a
guardrail and turns a recurring bill finding into a decision at pull-request time. The setting can be changed at
any time with no downtime, but disabling it on a database already past its
standard support date upgrades it to the next supported major version
automatically, so flip it on a running production instance only inside an upgrade
window. For Aurora and Multi-AZ DB clusters the setting lives at the cluster
level. Sources: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/extended-support.html,
https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/extended-support-charges.html
and the `EngineLifecycleSupport` parameter in
https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_CreateDBInstance.html
(all read 16 October 2026); Terraform AWS provider documentation for
`aws_db_instance` and `aws_rds_cluster` (read 16 October 2026).

---

## AWS billing hierarchy and separate invoices

*Added: August 2026. Sources (read 29 August 2026): [Invoice Configuration](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/invoice-configuration.html), [Creating an invoice unit](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/invoice-configuration-create.html), [Invoicing quotas](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/billing-limits.html#limits-invoicing), [What's New - AWS Invoice Configuration, December 2024](https://aws.amazon.com/about-aws/whats-new/2024/12/aws-invoice-configuration), [AWS CFM blog - Configuring your AWS invoices](https://aws.amazon.com/blogs/aws-cloud-financial-management/configuring-your-aws-invoices-using-invoice-configuration/), [re:Post - controlling credits and reservations with Invoice Configuration](https://repost.aws/articles/ARY4wopLJsQoKXASXOEIfxFw/how-to-control-credits-and-reservations-with-the-new-invoice-configuration), [What is AWS Billing Conductor](https://docs.aws.amazon.com/billingconductor/latest/userguide/what-is-billingconductor.html), [Managing Cost Categories](https://docs.aws.amazon.com/cost-management/latest/userguide/manage-cost-categories.html).*

On AWS the **account is the atomic unit of invoicing**. Nothing splits an invoice
inside an account - two teams sharing one account appear on the same invoice whatever
tagging, Cost Category or allocation logic sits on top. Account structure is therefore
an invoicing decision, not only a governance one: if a business unit has to receive its
own invoice, its workloads must live in accounts that belong to it, and that has to be
decided before the workloads land.

The most common error in this area is treating **Cost Categories as an invoicing
mechanism**. They are not. A Cost Category named "R&D" creates a Cost Explorer
dimension, a CUR column and a Budgets filter. It creates no invoice, changes no invoice,
and is invisible to Accounts Payable. The mechanism that produces separate invoice
documents is **Invoice Configuration** (invoice units), launched December 2024.

### The four mechanisms

| Mechanism | What it changes | Membership model | Effect on the AWS invoice | Commitments and credits | Cost |
|---|---|---|---|---|---|
| **Cost Categories** | Reporting groupings in Cost Explorer, Budgets, CUR / Data Exports, Cost Anomaly Detection | Rules matching linked accounts (explicit list, most reliable) or cost allocation tags on resources. Split charge rules spread shared-cost accounts proportionally, evenly or by fixed percentage | **None** | Unchanged. Can present an amortised view, cannot change who receives the discount | See the AWS Cost Management pricing page |
| **Invoice Configuration (invoice units)** | Produces a separate invoice document per unit, inside one AWS Organization and one contract | Explicit list of member accounts plus one invoice receiver account. No OU selection, no account-tag selection. Maintained by hand or via the `invoicing` API (`CreateInvoiceUnit`, `UpdateInvoiceUnit`, `ListInvoiceUnits`) | **One invoice per unit**, issued to the receiver. Consolidated billing and volume tiering across the org are preserved | Not controlled here. Sharing is set **per account in Billing Preferences** | See the AWS Billing pricing page |
| **Billing Conductor** | A **pro forma** version of costs per billing group, with custom pricing plans, custom line items and credits | Billing groups holding explicit account lists, each with a primary account | **None.** Billing Conductor configurations do not affect the customer's existing invoices from AWS, nor credit and commitment sharing | Real sharing unchanged. The pro forma view can model a different rate, a margin or an EDP the receiving entity should not see | Standard billing groups are charged. Billing-transfer billing groups are free on an AWS managed pricing plan; a customer managed plan carries a monthly fee per organisation. See the AWS Billing Conductor pricing page for the current rate |
| **Separate AWS Organizations (one payer per BU)** | A separate payer, contract and invoice per business unit | Accounts are moved between organisations (leave then invite) | **One invoice per organisation**, natively | Not shared across the boundary. Volume tiering restarts per org; Savings Plans and RI sharing stop at the org edge | No AWS fee. The cost is the lost consolidation |
| *(multi-org case)* **Custom billing views / billing transfer** | Cost visibility and payment responsibility across several organisations | See "AWS Multi-Organisation Billing Features" below | Billing transfer moves who pays; billing views do not touch the invoice | See that section | See that section |

**Billing Conductor pricing rules can now carry an absolute rate (15 September 2026).**
Until then a pricing rule could only mark public on-demand rates up or down, on AWS's
predefined usage tiers. SKU-scoped rules can now take a custom rate and custom usage-tier
thresholds instead. A reseller or a central IT team can mirror a negotiated or internal
rate card exactly in the pro forma view, with no back-calculated percentage that drifts
when AWS changes a public price. It still changes only the pro forma (showback and
chargeback) view, never the AWS invoice. Not available in the China Regions. Source:
<https://aws.amazon.com/about-aws/whats-new/2026/09/AWS-Billing-Conductor-custom-rates-usage-tier/>.

### Three sentences that anchor the hierarchy

1. **Invoices happen at the invoice unit level**, or at the payer level if no invoice
   unit is defined. There is no third option.
2. **Cost Categories and tags are reporting groupings.** They never change what is on an
   invoice, only what a cost report can group by.
3. **Savings Plans, RIs and credits are shared org-wide by default.** Isolation is done
   **per account in Billing Preferences**, not per invoice unit - an invoice unit does
   not build a commitment fence around itself.

### Decision rule

- **Separate invoice documents inside one contract** -> Invoice Configuration.
- **Internal re-billing at a rate different from the AWS rate** (margin, managed-service
  fee, an EDP the receiving entity should not see) -> Billing Conductor, on top of
  whatever the invoice layer does.
- **Reporting, showback, shared-cost allocation** -> Cost Categories with split charge
  rules. No invoice change, and none needed.
- **Separate legal entities that cannot share a contract** -> separate AWS
  Organizations, accepting the loss of volume consolidation and Savings Plan sharing.
  Do not reach for this until the first three have been ruled out.

### Invoice unit constraints that shape the design

- **An account can only be part of one invoice unit's rule at a time.** There is no
  overlapping membership and no partial split of an account across two units.
- **A given account can be a receiver for multiple invoice units.** An account cannot be
  a member of one unit and receiver of another unless it is the receiver of both.
- **If the payer account is a member of an invoice unit, the payer must be that unit's
  receiver.** The receiver is not a member of its own unit by default.
- **Name and invoice receiver cannot be changed after creation.** Getting either wrong
  means deleting the unit and recreating it, so agree naming with Finance first.
- **A purchase order can be associated with each invoice unit** - previously a PO could
  only sit at management account level. This is often the real reason a client asks for
  invoice units in the first place.
- **Tax settings are inherited, not set per unit.** If the payer has tax inheritance
  enabled, members inherit the payer's tax settings. If the invoice issuer is not Amazon
  Web Services, Inc., members inherit the receiver's tax settings.
- **Assignment changes take effect on the next billing cycle**, never retroactively.
- **Commitment and credit isolation is a Billing Preferences job.** Credit sharing and
  RI / Savings Plans discount sharing are set per account, and must be changed **before
  the last day of the month** to apply to that month's invoices. This is the only way to
  stop an invoice unit absorbing discounts bought elsewhere in the org.
- **Quotas** on invoice units and their members exist - read the
  [AWS Billing limits page](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/billing-limits.html#limits-invoicing)
  rather than assuming a number.

**Not verified - confirm with the AWS account team before relying on it:** whether an
invoice receiver can carry **its own payment method** and **its own legal entity / VAT
number** distinct from the payer's. Everything above is documented; this is not, and it
is usually the decisive question when a business unit wants to pay AWS directly. Do not
answer it from inference.

### OU synchronisation

Neither Cost Categories nor invoice units follow the AWS Organizations OU hierarchy.
Both take explicit account lists, so both drift the moment a new account is created in
an OU.

**For Cost Categories, account tags close the gap.** Since 19 December 2025, tags on
accounts in AWS Organizations can be activated as cost allocation tags (Billing and
Cost Management, Cost Allocation Tags, filter on account tags; activation takes up to
24 hours). Once active, they apply to all metered usage in the tagged account,
including refunds, credits and charges that cannot carry a resource tag, and they work
in Cost Explorer, CUR 2.0 and FOCUS exports, Budgets, Cost Categories and Cost Anomaly
Detection. CUR 2.0 prefixes them, so an account tag and a resource tag with the same key
stay distinct; do not start a key with `accountTag`. Tagging each account when it is
created therefore replaces the explicit account list in a Cost Category rule
([account tags for cost allocation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/account-tags-cost-allocation.html),
read 23 October 2026).

**Invoice units still need the account list.** The account-tag documentation does not
cover invoice units, so keep one scheduled Lambda for them: walk the OU tree with
`ListAccountsForParent` recursively and push the resolved lists into
`UpdateInvoiceUnit` (and into `UpdateCostCategoryDefinition` for any category not yet
keyed on account tags).

Run it **before month end**. Invoice unit assignment changes only take effect on the
next billing cycle, so an account created on the 28th and synced on the 2nd sits on the
wrong invoice for a full month, and correcting that is a credit-note conversation with
AWS rather than a configuration change.

### Questions to settle before configuring

Configuration is the easy part. These are the questions that decide the design, and most
of them belong to Finance rather than to the FinOps or platform team:

1. **Who pays AWS?** A business unit with its own payment method and legal entity, or
   central IT paying one bill and Finance reallocating internally? This is the fork
   between an invoicing problem and an allocation problem.
2. **Which legal entity and VAT number sits behind each receiver?** Tax settings are
   inherited (see above), so a receiver in a different entity is not a configuration
   detail.
3. **Is a purchase order needed per invoice unit?** If yes, who raises and owns each PO.
4. **Who buys commitments, and which invoice units benefit?** Decide before the first
   Savings Plan is bought, then set Billing Preferences per account to match.
5. **How is shared cost inside a business unit's account treated?** Invoice units cannot
   split an account, so anything shared has to live in its own account or be
   handled in the reporting layer with Cost Category split charge rules - and then it is
   a showback number, not an invoice line.

---

## AWS Multi-Organisation Billing Features

*Added: March 2026. Original lead: AWS Keys to AWS Optimization podcast, S16E5. The
mechanics below were re-verified against AWS documentation in August 2026 and the
primary sources are linked inline; anything the AWS pages do not state is marked
"unconfirmed" rather than dropped.*

Two features allow FinOps teams to centralise cost visibility and billing operations
across multiple AWS organisations. They are related but solve different problems and
should not be conflated. Multi-source custom billing views reached general availability
on [25 September 2025](https://aws.amazon.com/about-aws/whats-new/2025/09/billing-view-cost-management-multiple-organizations/);
Billing Transfer reached general availability on
[19 November 2025](https://aws.amazon.com/about-aws/whats-new/2025/11/billing-transfer-multi-organization-billing-cost-management/).
(The podcast lead placed both at re:Invent 2024; the AWS What's New pages do not
support that date, so it has been corrected here.)

---

### Custom billing views (cross-organisation)

A billing view is an AWS resource that controls which accounts' cost and usage data a given account can access in Cost Explorer, budgets, and dashboards.

**What multi-source views added:**

- A payer account can share a billing view with an account in a *different* AWS
  organisation. AWS documents both scopes on the sharing page: "Within AWS
  organization" and "With any account", where an out-of-organisation recipient must
  accept the invitation
  ([Sharing custom billing views](https://docs.aws.amazon.com/cost-management/latest/userguide/share-custom-billing-views.html)).
- A recipient account can combine multiple billing views, including views received from
  other organisations, into a single aggregated view
  ([multi-source custom billing views announcement](https://aws.amazon.com/blogs/aws-cloud-financial-management/introducing-multi-source-custom-billing-views-unified-cost-management-across-multiple-organizations-on-aws/)).
- Budgets can be scoped to a billing view, including a multi-source view (same
  announcement).

**Key behaviours:**

- The owner retains control of the share. AWS states you "have the flexibility to edit
  the sharing permissions of a custom billing view at any time"
  ([Managing shared access to custom billing views](https://docs.aws.amazon.com/cost-management/latest/userguide/manage-shared-access-custom-billing-views.html)).
  Sharing runs on AWS RAM, so a share can also be edited or deleted from the RAM
  console. *Unconfirmed:* that a revocation immediately propagates into a downstream
  combined view built on that source. No AWS page states this either way, so treat it as
  a design assumption to test, not a documented guarantee.
- The recipient needs the `AWSRAMPermissionBillingViewFullAccess` managed permission to
  use a shared view as a source for another view (same announcement). Note the earlier
  edition of this section named a `billing-view:full-access` permission level; that
  string does not appear in AWS documentation and has been corrected.
- Supported tools, per the AWS announcement: Cost Explorer, Budgets, and the Billing and
  Cost Management dashboards. *Unconfirmed:* reports, forecasts, and the claim that
  Amazon Q integration is not yet supported. The AWS pages consulted do not mention any
  of the three, so the podcast lead is the only source for them.
- Creating, sharing, and combining billing views is free, and there is no fee for Cost
  Explorer console or Budgets access. Cost Explorer **API** calls are charged at $0.01
  per source in the view per API request, so a view built on several sources costs a
  multiple of a single-source call (same announcement). Note the unit: AWS prices this
  per *source*, not per organisation queried.

**Typical use cases:** enterprises managing multiple AWS organisations after M&A; FinOps teams giving an external consultant read access to cost data without console access; business unit owners needing a budget that spans accounts across multiple payers.

---

### Billing transfer

Billing transfer is a delegation mechanism that allows one payer account (the "bill transfer account") to take over payment responsibility for another AWS organisation's charges (the "bill source account").

**What this enables:**

- Decouples billing from governance. AWS lists "Separate billing and administration" as
  a key benefit: the management account that accepted the invitation keeps full
  administration of its own organisation while the bill transfer account manages and
  pays the consolidated bill
  ([Transfer billing management to external accounts](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing.html)).
- The bill transfer account receives distinct invoices for the source organisation's
  charges and can read that organisation's data in Cost Explorer, the Cost and Usage
  Report, Budgets, and the Bills page, without logging into the source account (same
  page).
- Integrates with AWS Billing Conductor: when sending the invitation the bill transfer
  account selects the pricing configuration that determines what the bill source account
  sees, which is how negotiated rates stay private or a reseller margin gets modelled
  (same page).

**Key behaviours:**

- The invite process is unidirectional, and AWS states it under an "Invitations are
  unidirectional" consideration: only the account that will manage and pay the
  consolidated bill can send an invitation, and a bill source cannot ask another account
  to take its bill (same page). Either account can withdraw the transfer afterwards.
- Commitments stay bounded at the organisation level: "Volume discount tiers, Reserved
  Instances, and Savings Plans continue to be calculated and applied at the individual
  AWS Organizations level" (same page). Credits behave differently rather than
  transferring: AWS documents credit-tracking restrictions for the bill source account,
  which loses the Credits page balance view, and credits do not appear in pro forma
  artefacts unless the bill transfer account models them through Billing Conductor.
- The bill transfer account sees two distinct views per bill source, which AWS names
  "My view" (the billing data it is financially responsible for) and the
  "Showback/chargeback view" (the data as configured through Billing Conductor). The two
  differ whenever the bill transfer account has non-public rates.
- *Unconfirmed:* that tax settings and contractual obligations need review before
  enabling billing transfer. This came from the podcast lead and no AWS page consulted
  states it. What AWS does document, and what should be read before opting in, is the
  "Important impacts" list on the same page: loss of historical Cost Explorer, Budgets
  and Anomaly Detection data for the bill source, CUR configurations going `Unhealthy`
  and needing reconfiguration, no Cost Anomaly Detection for bill source accounts, and
  no hourly granularity on pro forma data in Cost Explorer.
- An AWS managed pricing plan is free for billing transfer: "For Billing Transfer
  customers, there is no cost to use AWS Billing Conductor, when you choose an AWS
  managed pricing plan." A customer managed (custom) pricing plan is charged per AWS
  organisation per month (illustrative: $50, read on the pricing page 2 October 2026;
  check the page before quoting it), and AWS states the charge starts on
  1 June 2026, after a free trial through 31 May 2026, with two months of free usage for
  customers newly opting in after that date
  ([AWS Billing Conductor pricing](https://aws.amazon.com/aws-cost-management/aws-billing-conductor/pricing/)).
  The earlier edition of this section dated the charge to June 2025; that is not what the
  pricing page says and has been corrected.

- **Reconcile against the billing context that applied, not the one that applies now.**
  The `ListBillingViewSegments` API (25 September 2026) returns an account's billing
  context over a chosen period, split into time segments with effective date ranges.
  Each segment names the management account, the billing transfer account and the
  billing-group primary account that applied, and whether the data was billable or pro
  forma (`domain`). It returns billing context only, not cost data; it works on primary
  billing views only (custom billing views are not supported) and omits hidden
  segments, so the segments may not cover the whole period. API reference:
  <https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_billing_ListBillingViewSegments.html>. Run it before
  reconciling any month in which an account changed organisation, joined or left a
  billing transfer, or moved billing group; otherwise one allocation run mixes costs from
  two billing contexts. Source:
  <https://aws.amazon.com/about-aws/whats-new/2026/09/aws-billing-and-cost-management-billing-context-api/>.

**Typical use cases:** AWS channel partners managing resale relationships; enterprises consolidating invoicing after acquisitions; large organisations that want subsidiaries to retain governance autonomy while centralising finance operations.

---

### Feature comparison

| | Custom billing views | Billing transfer |
|---|---|---|
| What it centralises | Cost visibility / data access | Invoice payment |
| Changes billing responsibility | No | Yes |
| Governance boundary | Unchanged | Unchanged |
| Savings plans shared | No | No |
| Credits shared | No | No |
| Supported tools | Cost Explorer, budgets, dashboards | Cost Explorer, CUR, budgets, bills page |
| Pricing | Free to create and share; Cost Explorer API charged per source per request | Free (AWS managed plan) / $50/org/month (customer managed pricing plan, from 1 June 2026) |

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
