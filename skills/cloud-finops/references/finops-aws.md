---
name: finops-aws
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Usage Optimization", "Data Ingestion", "Reporting & Analytics"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "Procurement"]
fcp_maturity_entry: "Walk"
---

# FinOps on AWS

> AWS-specific guidance covering cost management tools, compute rightsizing, SageMaker
> operational FinOps, cost allocation, and governance. Covers CUR and Data Exports,
> Cost Explorer, Compute Optimizer, Trusted Advisor, EC2 and GPU rightsizing,
> CloudFront flat-rate plans, S3 Files, and multi-org billing.
>
> Commitments (Savings Plans, RIs, Spot, EDP) and the enumerated per-service pattern
> catalogue live in their own files - see the routing table below.

---

## Commitments and the pattern catalogue live in their own files

Two large sections were split out of this file so a routine question does not load
material it does not need:

| You want | Read |
|---|---|
| Savings Plans, RIs, Spot, commitment decision tree, portfolio liquidity, EDP negotiation | `finops-aws-commitments.md` |
| The enumerated per-service inefficiency catalogue | `finops-aws-patterns.md` |
| A specific named waste pattern with a runnable detection query | `playbooks/aws-*.md` |

## AWS cost data foundation
<!-- src:37b46c22605776cb -->

### Cost and Usage Report (CUR)

CUR is the most granular billing data source AWS provides. It is the correct data source
for any serious FinOps implementation on AWS.

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
  FOCUS 1.2 export and GCP's FOCUS 1.0 export, enabling true cross-cloud
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

Cost Explorer provides pre-built visualizations and the Cost Explorer API for
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
- **Rightsizing recommendations** - EC2 rightsizing based on CloudWatch utilization
- **Savings Plans recommendations** - commitment purchase recommendations based on usage
- **Cost anomaly detection** - ML-based anomaly alerts (set up before you need them)
- **Cost categories** - virtual tags for billing-layer cost allocation

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

---

## Compute rightsizing

### EC2 rightsizing

Rightsizing is the highest-ROI optimisation for most AWS environments at Crawl/Walk maturity.

**Data sources for rightsizing analysis:**
- AWS Compute Optimizer - ML-based recommendations using CloudWatch metrics
- AWS Cost Explorer rightsizing recommendations (simpler, less granular)
- Third-party tools (CloudHealth, Apptio, cast.ai for containers)

**Rightsizing process:**
1. Enable Compute Optimizer in all accounts (free for EC2 recommendations)
2. Wait 14 days minimum for sufficient utilization data
3. Export recommendations and filter for "Over-provisioned" findings
4. Prioritize by potential monthly savings
5. Validate recommendations with workload owners - check peak utilization, not average
6. Apply changes in non-production first, then production with monitoring period

**Common rightsizing mistakes:**
- Acting on CPU metrics alone without checking memory (CloudWatch memory requires agent)
- Downsizing during off-peak analysis periods without accounting for peak loads
- Rightsizing stateful databases without testing failover behaviour
- Missing network-intensive workloads that appear CPU-idle but are IO-bound

### Container rightsizing (ECS / EKS)

Container rightsizing requires different tooling than EC2 rightsizing.

- AWS Compute Optimizer provides ECS on Fargate recommendations
- For EKS, use Kubernetes VPA (Vertical Pod Autoscaler) recommendations or cast.ai
- Right-size the pod requests/limits before right-sizing the underlying node group
- Node group rightsizing savings are partially offset by bin-packing efficiency changes

### GPU instance rightsizing

GPU instances (G4dn, G5, G6, P3, P4d/P4de, P5/P5e/P5en, Inf2, Trn1) are
the highest-dollar rightsizing candidates in any AWS account running ML.
GPU rightsizing is **not** the same problem as CPU rightsizing because the
basic `nvidia-smi` / CloudWatch `GPUUtilization` metric reports whether
the GPU did anything in the interval, not how much of its capacity was
used. A workload using 1 SM out of 108 on an H100 reports `GPU-Util: 100%`.
For real signals, use NVIDIA DCGM Exporter metrics (`DCGM_FI_PROF_GR_ENGINE_ACTIVE`,
`DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`, `DCGM_FI_PROF_DRAM_ACTIVE`,
`DCGM_FI_DEV_FB_USED`). See `finops-for-ai.md` section "GPU utilization is
misleading" for the metric reference.

The four highest-leverage GPU rightsizing patterns, each with a dedicated
playbook:

- **Oversized GPU instance** - workload uses < 30% of GPU compute and
  < 40% of GPU memory.
  [aws-gpu-instance-oversized](../playbooks/aws-gpu-instance-oversized.md)
- **Multi-GPU instance running single-GPU workload** - 7 of 8 GPUs idle
  on a `g5.48xlarge` or `p4d.24xlarge`.
  [aws-multi-gpu-underutilized](../playbooks/aws-multi-gpu-underutilized.md)
- **MIG candidate** - workload uses < 1/7 of an A100 or H100; partition
  via NVIDIA Multi-Instance GPU.
  [aws-mig-candidate](../playbooks/aws-mig-candidate.md)
- **GPU for CPU-bound workload** - the GPU is idle while the CPU is
  saturated; migrate to a `c7i` or `inf2` instance.
  [aws-gpu-for-cpu-bound-workload](../playbooks/aws-gpu-for-cpu-bound-workload.md)
- **Outdated GPU generation** - P3 (V100) or G4dn (T4) workloads that
  would run cheaper per inference on G5, G6, P4d, or P5.
  [aws-outdated-gpu-generation](../playbooks/aws-outdated-gpu-generation.md)

**EKS Auto Mode / ECS Managed Instances GPU fee reduction.** As of 1 July
2026, AWS reduced the EKS Auto Mode management fee for GPU and accelerated
instance types - a 35% reduction for G-series instances and a 60% reduction
for P-series and Trainium instances. The identical fee reduction applies to
ECS Managed Instances. The reduction is applied automatically with no
customer action required. This meaningfully narrows the cost gap between
managed GPU infrastructure and self-managed node groups, making EKS Auto
Mode a more cost-competitive option for GPU workloads (ML inference,
fine-tuning, and batch). Re-evaluate the EKS Auto Mode vs Karpenter /
self-managed cost comparison for GPU node pools in light of this change.
Source: https://aws.amazon.com/about-aws/whats-new/2026/07/amazon-eks-auto-mode-gpu-price

---

## SageMaker operational FinOps

SageMaker spend has two cost shapes that differ from generic EC2 and need
their own operational discipline.

### The billed-while-idle trap

SageMaker real-time endpoints and notebook instances are billed at the
underlying instance hourly rate **as long as they are provisioned**,
whether traffic flows through them or not. This differs from
consumption-based services like Lambda or Bedrock on-demand. What makes this
expensive is the spread: idling a small `ml.m5.xlarge` endpoint costs low
hundreds of dollars a month, a `ml.g4dn.xlarge` GPU endpoint a few times that,
and a `p4d.24xlarge` endpoint is in the tens of thousands - roughly two orders
of magnitude between the cheapest and the most expensive thing you can forget
to switch off (indicative, August 2026; pull current rates from the AWS
pricing API or <https://optimtoken.optimnow.io> before quoting a number).
Forgotten POC endpoints, never-decommissioned A/B
variants, and notebook instances left `InService` over a weekend are the
two highest-density waste patterns in any account running SageMaker.

Detection and remediation playbooks:
- [aws-sagemaker-idle-endpoint](../playbooks/aws-sagemaker-idle-endpoint.md)
- [aws-sagemaker-notebook-always-on](../playbooks/aws-sagemaker-notebook-always-on.md)

### Inference deployment pattern selection

SageMaker offers four deployment patterns. The right choice is workload-
driven: matching the wrong pattern to the wrong workload is itself a waste
pattern (a real-time endpoint serving bursty traffic, a serverless endpoint
behind a strict latency SLA).

| Pattern | Best fit | Optimisation focus | When to avoid |
|---|---|---|---|
| **Real-time endpoint** | User-facing API, strict latency, steady traffic | Rightsizing, autoscaling, GPU vs CPU choice | Intermittent or bursty traffic; long-running batch |
| **Serverless inference** | Intermittent or low-volume traffic, no dedicated capacity needed | Memory configuration, cold-start tolerance, cost per request | Strict p99 SLA; high sustained throughput |
| **Asynchronous inference** | Bursty traffic, large payloads, tolerable response delay | Queue depth, scale-down settings, scale-to-zero | Synchronous request-response APIs |
| **Batch transform** | Offline scoring, scheduled jobs, large datasets | Spot, partitioning, instance type for throughput | Interactive inference; user-facing immediate response |

The default in most teams is real-time. The most common silent waste is a
real-time endpoint serving traffic that would be a clean fit for
serverless or asynchronous - keeping the endpoint always-on for what is
actually a few requests per hour or per day.

### Endpoint consolidation - MME and Inference Components

When several lightly-used real-time endpoints exist in the same account
and region (each on its own dedicated instance), consolidation onto a
shared endpoint is one of the largest savings opportunities in SageMaker.
Two consolidation mechanisms:

- **Multi-Model Endpoints (MME)** - one container, multiple models loaded
  dynamically from S3 on demand. Best for tens to thousands of small,
  homogeneous models that share a runtime (all sklearn, all XGBoost, all
  TensorFlow Serving). Cold-start on cache-miss adds 100 ms - 2 s of
  latency.
- **Inference Components (IC)** - newer mechanism (introduced 2023). Each
  Inference Component is a model + container deployed onto a shared
  instance pool with per-component autoscaling. Best for 5-50 models with
  heterogeneous frameworks or different scaling characteristics. IC is
  generally the right default for new builds unless MME's homogeneous-
  runtime model is a genuine fit.

Decision: same container + same framework + many small models → MME;
heterogeneous frameworks or per-model scaling needs → Inference Components.

Detection and remediation playbook:
[aws-sagemaker-mme-consolidation](../playbooks/aws-sagemaker-mme-consolidation.md)

### Notebook hygiene

SageMaker notebook instances are valuable while someone is actively
working in them and a pure cost drag when they are not. The practical
controls:

- **Lifecycle Configurations (LCC)** with the standard
  `auto-stop-idle` script (AWS publishes the reference in the
  `amazon-sagemaker-notebook-instance-lifecycle-config-samples` repo).
  Run every 5 minutes, stop the instance after N hours of kernel
  inactivity. A 2-hour idle threshold is the practical default; 4 hours
  for teams running long evaluations.
- **EventBridge scheduled stop/start** for predictable office-hours
  patterns (start 09:00 weekday, stop 19:00 weekday, never weekends).
  Cheaper and more predictable than LCC for teams that never use
  notebooks off-hours.
- **Migrate new work to SageMaker Studio**. Studio bills the Studio app
  per-second, supports native idle shutdown via the Studio admin console,
  and avoids the per-notebook EBS footprint. Existing notebook instances
  do not need in-place migration.

Detection and remediation playbook:
[aws-sagemaker-notebook-always-on](../playbooks/aws-sagemaker-notebook-always-on.md)

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
  data transfer charges) - use Cost Categories for virtual allocation of untaggable costs
- Enable "Tag policies" in AWS Organizations to enforce tag key capitalization consistency
- **IAM Principal Cost Allocation (2026):** tags applied to IAM users and roles can be
  propagated to CUR 2.0 and Cost Explorer with an `iamPrincipal/` prefix, enabling
  caller-based attribution when resource-level tags are not sufficient. Primary use case
  today is Amazon Bedrock  - see `finops-bedrock.md` for setup, CUR size implications,
  and when to use it vs. account separation

### Cost Categories

AWS Cost Categories create billing-layer allocation rules without requiring physical tags.
Use them for:
- Shared service allocation (split NAT Gateway cost by team account usage)
- Account-level allocation when resource-level tagging is incomplete
- Retroactive allocation adjustments

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
- Service-level budgets for top 3–5 cost drivers
- Anomaly detection monitor linked to cost anomaly detection

**Recommended alert recipients:** Both the FinOps practitioner and the engineering team
lead for the relevant account. FinOps-only alerts create a bottleneck; engineering-only
alerts lack financial context.

### Extended Support version audits (recurring action item)

Several AWS services charge an Extended Support surcharge for domains, clusters, or
instances left on end-of-standard-support versions. This is the "outdated resource
incurring extended support charges" pattern - see `finops-aws-patterns.md` for the
enumerated entries (EKS clusters, OpenSearch/Elasticsearch domains).

Make version audits a recurring FinOps action item:
- Audit Amazon OpenSearch Service domains for legacy Elasticsearch (1.5-7.8) and
  OpenSearch (1.0-1.2, 2.3-2.9) versions still incurring Extended Support charges.
- As of August 2026, AWS extended Extended Support patch coverage for these legacy
  versions by 12 months to November 2027, but from November 2026 the Extended Support
  surcharge rises to equal 100% of instance pricing (a 2x effective compute cost for
  domains still on old versions). Newer versions (ES 6.8/7.9/7.10, OpenSearch 1.3,
  2.11-2.19) have their own Standard/Extended Support windows ranging 1-3 years.
- AWS revises these support windows periodically - always check the current support
  dates before budgeting rather than relying on a cached table.

Source: https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-opensearch-service-additional-upgrade-runway-support-dates

---

## AWS-specific quick wins

These actions typically deliver savings within 30 days with low risk.

| Action | Typical savings | Risk | Effort |
|---|---|---|---|
| Delete unattached EBS volumes | 100% of volume cost | None | Low |
| Release unneeded Elastic IPs | ~$3.60/IP/month | None | Low |
| Delete unused snapshots (>90 days old) | Variable | Low (verify no restore needed) | Low |
| Schedule dev/test EC2 stop outside business hours | 60–70% of instance cost | Low | Low |
| Move S3 infrequently accessed data to Infrequent Access | 40% storage cost | Low | Low |
| Right-size over-provisioned RDS instances | 20–50% RDS cost | Medium (test first) | Medium |
| Convert gp2 EBS volumes to gp3 | 20% EBS cost (same IOPS baseline) | Low | Low |
| Review and right-size NAT Gateway usage | Variable | Medium | Medium |

---

## Database cost optimisation

Database services often represent 20-40% of cloud spend, yet many organisations treat them as black boxes from a cost perspective. This section covers the AWS surface. For the equivalent treatments elsewhere, see "Database optimisation patterns" in `finops-azure.md` and "Databases Optimization Patterns" in `finops-gcp.md`.

### Common database cost drivers

**1. Overprovisioning for peak load**
- Databases sized for Black Friday traffic that run at 10% utilisation for 11 months
- Solution: auto-scaling where the engine supports it, or scheduled scaling for predictable patterns
- Aurora Serverless v2 for genuinely variable load; RDS Proxy where the pressure is connection churn rather than compute

**2. High availability in non-production**
- Multi-AZ deployments double infrastructure costs
- Dev/test rarely needs synchronous replication
- Solution: single-AZ for non-prod, with automated backups sized to the recovery requirement

**3. Storage inefficiencies**
- Provisioned IOPS (io1/io2) where gp3 suffices
- Retained backups and snapshots beyond business requirements
- Uncompressed or poorly indexed tables driving storage growth
- Solution: regular storage audits, lifecycle policies, compression strategies

**4. Backup retention overkill**
- 35-day retention when 7 days meets actual RTO/RPO
- Manual snapshots never deleted after migrations
- Solution: align retention to documented recovery requirements, automate cleanup

### Database-specific optimisation strategies

**For transactional workloads (OLTP):**
- Right-size on connection count and active sessions, not just CPU and memory
- Implement connection pooling to reduce instance size requirements
- Reach for RDS Proxy before sizing up an instance to absorb connection churn

**For analytical workloads (OLAP):**
- Evaluate Redshift for columnar storage rather than scaling an OLTP engine into a reporting role
- Implement result caching to reduce repeated query costs
- Schedule large queries off-peak

**For mixed workloads:**
- Separate OLTP and OLAP with read replicas or a warehouse offload
- Use change data capture (CDC) for real-time sync instead of expensive ETL

### Commitment and licensing

Commitment mechanics for databases - which instrument covers RDS, how Reserved Instances interact with the Database Savings Plan, the size-flexibility rules - live in the "Database commitment discount decision tree" of `finops-aws-patterns.md`, which is where `finops-aws-commitments.md` routes the question. Two points belong with the workload rather than with the instrument:

- **Commercial engines (Oracle, SQL Server)**: licence cost routinely exceeds infrastructure cost, so edition choice and BYOL move the bill more than instance sizing does. `finops-itam.md` covers the BYOL governance side.
- **DynamoDB**: On-Demand versus Provisioned capacity swings cost by roughly an order of magnitude in either direction depending on traffic shape. Decide it from the measured traffic profile rather than from a default.

### Quick wins checklist

- [ ] Identify databases with <20% average CPU utilisation for downsizing (playbook: `aws-oversized-rds`)
- [ ] Review Multi-AZ configurations in non-production environments
- [ ] Audit backup retention policies against actual recovery requirements
- [ ] Check for orphaned snapshots from deleted databases (playbook: `aws-snapshot-sprawl`)
- [ ] Evaluate storage tier options (gp3 versus provisioned IOPS)
- [ ] Implement connection pooling for high-connection workloads
- [ ] Schedule non-production databases to stop outside business hours
- [ ] Review commercial database licences for BYOL opportunities

---

## CloudFront flat-rate pricing plans

AWS introduced per-distribution flat-rate plans for CloudFront in late 2025. They
bundle CDN, WAF, Route 53, CloudWatch Logs ingest, ACM, CloudFront Functions and
S3 storage credits into a single monthly price, removing the bill variance that
made CloudFront costs hard to forecast.

> *Plan prices and allowances below are list values as of August 2026. The durable content
> in this section is the shape of the trade-off - what each tier locks behind it, where the
> request ceiling bites before the bandwidth one, what the plan does not include - not the
> specific dollar amounts. Verify against the CloudFront pricing page before quoting.*

### Tier summary

| Plan | Monthly cost | Data transfer out | Requests | S3 credit | WAF rules | Cache behaviours |
|---|---|---|---|---|---|---|
| Free | $0 | 100 GB | 1M | 5 GB | 5 | 5 |
| Pro | $15 | 50 TB | 10M | 50 GB | 25 | 10 |
| Business | $200 | 50 TB | 125M | 1 TB | 50 | 50 |
| Premium | $1,000 | 50 TB | 500M | 5 TB | 75 | 100 |

Pay-as-you-go pricing for 50 TB of data transfer out from North America runs
roughly $4,250 at $0.085/GB. The Pro plan delivers the same 50 TB for $15. For
bandwidth-heavy workloads the effective discount is at the 99% mark - this is
not the usual "simplified pricing" code for "we repriced the meter". It is a
genuine offer aimed at mid-market customers who would otherwise move to
Cloudflare.

### Request-bound vs bandwidth-bound

The break-even average response size (bandwidth cap / request cap) is the number
that decides which tier fits:

| Plan | Break-even avg response size |
|---|---|
| Free | 100 KB |
| Pro | 5 MB |
| Business | 400 KB |
| Premium | 100 KB |

If your average response is smaller than the break-even, you hit the request
ceiling first - you are request-bound. Pro is designed for software binaries,
video chunks, large assets. For API responses or web pages averaging under
400 KB you will exhaust the 10M request budget long before the 50 TB bandwidth,
and Business becomes the real entry point.

**Model the p95 month, not the average.** Flat-rate tiers care about worst-case
volume - a traffic spike during a launch can push you past the cap exactly when
performance matters.

### What is included

- CloudFront CDN distribution
- AWS WAF with bot management (**mandatory** - WebACL must be associated, you
  cannot opt out)
- DDoS protection (blocked attack traffic does not count against allowances)
- Route 53 DNS, with caveats (see below)
- CloudWatch Logs ingestion (storage and queries still billed separately)
- ACM TLS certificates
- CloudFront Functions (serverless edge compute)
- S3 storage credit at the bundled tier

The WAF inclusion is load-bearing for the value math. 25 WAF rules at $1/rule/month
is $25/month of standalone WAF value, which by itself exceeds the $15 Pro price.
If you were going to adopt WAF anyway, Pro pays for itself on that line alone.

### Route 53 gotchas

- Hosted zone must live in the same AWS account as the CloudFront distribution.
  Cross-account Route 53 setups disqualify you from flat-rate entirely.
- ALIAS records pointing at CloudFront or other supported AWS services do not
  count against the DNS query allowance. CNAME records do count.
- If you exceed the DNS query limit AWS may automatically transition the hosted
  zone back to pay-as-you-go without prompting.
- DNSSEC KMS charges and health checks are billed separately.

### What is not included (the real filter)

Lambda@Edge is not supported. There is no migration path, no compatibility
shim, and CloudFront Functions is not a replacement for most Lambda@Edge
workloads (2 MB memory, 10 KB code, JavaScript only, no network access, no AWS
SDK). If your architecture relies on Lambda@Edge - even accidentally after
years of incremental drift - flat-rate is off the table until you can remove or
replace that dependency.

Other exclusions that will disqualify real distributions:

- Real-time logs (Kinesis streaming), Parquet log format
- Continuous deployment, staging distributions, multi-tenant distributions
- Anycast IP list configuration, dedicated IP/SSL, field-level encryption
- Shield Advanced combined subscriptions, Firewall Manager
- WAF targeted bots, CAPTCHA (challenge only), Partner Managed Rules, Account
  Takeover Protection, WAF Rule Groups (must be individual rules)
- Shared CloudFront Functions or WAF WebACLs across distributions - each plan
  requires dedicated, non-shared resources
- Legacy cache settings and origin access identity (OAI) - must migrate to
  cache policies and origin access control (OAC)

### The tier-locked features that drive up-tier selection

| Feature | Minimum tier |
|---|---|
| Geographic restrictions, rate limiting | Free |
| Common bot detection, Origin Shield, custom response headers, private VPC origins | Business |
| Automatic origin failover (origin groups) | Premium |
| Mutual TLS (mTLS) | Premium |

Origin failover is the biggest one. If high availability to multiple origins
matters to you (the December 2021 us-east-1 event is the usual reference), you
are looking at Premium at $1,000/month or staying on pay-as-you-go.

### Multi-tenant SaaS constraint

One apex domain per plan. If every customer runs on a subdomain of your platform
(`customer1.yourplatform.com`) you are fine, all subdomains share the same plan.
If customers bring their own apex domains (`customer1.com`, `customer2.com`),
you need one plan per customer, capped at 100 plans per AWS account. For custom-
domain SaaS at any meaningful scale, flat-rate does not fit - stay on
pay-as-you-go.

### Overages mean throttling, not a bill

AWS does not charge overage fees. When you exceed allowances they **degrade
performance** - fewer or more distant edge locations serve your traffic. There
is no operational signal distinguishing "hit the cap" from "CloudFront is just
slow". Notifications at 50%, 80% and 100% are explicitly "may be delayed". The
failure mode is a P1 investigation that ends with "we forgot about a pricing
tier limit", which is much harder to explain than an invoice.

**Build your own alerting.** CloudWatch metrics for `Requests` and
`BytesDownloaded` with alarms at 50%, 80% and 90% of the plan limits. Do not
rely on AWS's email cadence.

### Ecosystem lock-in is part of the price

AWS can offer 50 TB for $15 because origin traffic from S3 or EC2 to CloudFront
is free. Moving that same workload to Cloudflare triggers standard AWS data
transfer out charges at roughly $0.09/GB - 50 TB/month becomes $4,500 in egress
alone, every month. The real price of CloudFront Pro is $15 plus the AWS
dependency you have already accepted.

For greenfield workloads with no AWS origins, Cloudflare's unlimited-bandwidth
Pro plan at $25/month is the correct comparison. For existing AWS shops the
comparison is not close.

### Operational gotchas

- **Historical usage affects eligibility.** AWS checks recent distribution
  traffic when you subscribe. You cannot subscribe to Pro when your usage
  clearly puts you in Business territory.
- **Disabled distributions still incur plan charges.** Disable without
  cancelling the plan and you keep paying the monthly fee for nothing.
- **Plans must be cancelled before deletion.** You cannot delete a distribution
  while a plan is attached.
- **Upgrades are immediate and prorated. Downgrades take effect next billing
  cycle.**
- **You can mix pricing models.** Keep experimental or low-traffic distributions
  on pay-as-you-go (effectively free at low volume) and move only the
  high-volume production distributions to flat-rate.
- **Unsupported features block subscription.** The console refuses to attach a
  plan while the distribution still has Lambda@Edge, real-time logs or any
  other unsupported feature active.
- **Maximum 100 plans per AWS account, 3 Free plans maximum. AWS Free Tier
  accounts are not eligible.**

### Decision flow

1. Audit existing distributions. Most accounts have zombie distributions -
   identify which ones actually serve traffic.
2. Check blockers per distribution: Lambda@Edge, shared Functions or WebACLs,
   real-time logs, Shield Advanced, cross-account Route 53. Any of these keep
   you on pay-as-you-go for that distribution.
3. Calculate average response size. Under 400 KB you are request-bound - Pro
   will not fit a high-traffic distribution.
4. Model p95 volume, not average. Pick the tier that fits your worst month.
5. Count cache behaviours. Over 10 means Pro is off the table regardless.
6. Build CloudWatch alarms at 50/80/90% of plan limits before subscribing.
7. Migrate one non-critical distribution first, watch usage counters across a
   full billing cycle, then expand.

The downside risk is low - no annual commitment, downgrades and cancellations
are supported. The upside is the first AWS pricing mechanism in years where
predictability and cost both move in the right direction for mid-market
workloads.

---

## S3 Files - filesystem access over S3

S3 Files (launched 2026) lets you mount an S3 bucket as an NFS 4.1/4.2
filesystem on EC2, Lambda, EKS or ECS. The filesystem maintains a view of your
objects and translates POSIX operations into S3 requests. Writes are synced back
to the underlying bucket. S3 itself is still not a filesystem - S3 Files is a
real filesystem layer in front of it, built on EFS infrastructure, with the
original S3 bucket as durable backing store.

### What it replaces

- FUSE-based workarounds: s3fs-fuse, goofys, Mountpoint for Amazon S3 for
  workloads that need genuine POSIX semantics
- Cases where teams ran EFS or FSx purely to give legacy applications something
  to mount, while the data of record actually lived in S3
- Ad-hoc proxy layers between S3 and ML training pipelines or agentic workloads
  that need shared file storage

### Pricing mechanics

Two cost dimensions on top of the underlying S3 bucket (us-east-1 list rates as of
August 2026 - verify against the AWS pricing page before using them in a model):

| Dimension | Rate |
|---|---|
| Filesystem storage (hot tier) | $0.30/GB-month |
| Reads | $0.03/GB |
| Writes | $0.06/GB |

Rates are identical to EFS Performance-optimised Standard. The underlying
infrastructure is the same.

**The design that makes it cheap:** you mount a petabyte bucket and pay S3 Files
rates only on the small slice you actually touch. Everything else stays at
standard S3 pricing ($0.023/GB-month Standard, or less on Intelligent-Tiering or
Infrequent Access). The hot tier is an opt-in cache, not a whole-bucket storage
class.

### The 128 KB threshold

Files below the threshold (default 128 KB, configurable) get pulled into the
hot tier on first access - small-file latency is where filesystems actually
beat object stores, so S3 Files caches them.

**Reads of 128 KB or larger stream directly from S3 even when the file is
already on the hot tier.** No S3 Files access charge. This is the key mechanic
that makes the economics work for mixed workloads - your Parquet files and
video chunks go through the free path.

### Metering minimums (the gotcha)

Every data access operation has minimums that round up:

| Operation | Metered as |
|---|---|
| Read of any size | 32 KB minimum |
| Write of any size | 32 KB minimum |
| Metadata op (list, stat, create, delete) | 4 KB read |
| Commit (fsync or close-after-write) | 4 KB write |
| Everything above minimums | Rounds up to next 1 KB |

If your workload is millions of tiny metadata-heavy operations - ML training
checkpointing and some agentic workflows fit this profile exactly - the
minimums dominate the bill. `ls` on a directory with 10,000 files is 10,000
metadata reads at 4 KB each; if that triggers prefetch it is another 10,000
writes at 32 KB minimum each. Model these patterns before you mount anything
production.

**First-read cost for small files:** $0.06/GB (the import write), not $0.03/GB.
The read is included in the import operation. Subsequent reads of the same
cached file are $0.03/GB. AWS's pricing examples were misleading on this
initially - cost the workload on your real access patterns.

**Rename cost:** a file rename is an S3 PUT plus a filesystem read (32 KB
minimum). Renaming a directory meters every object with that prefix - moving
50,000 files is 50,000 individual metered operations.

### Expiration and eviction

Untouched data on the hot tier is evicted after a configurable window (1 to
365 days, default 30). This bounds your hot-tier storage cost automatically -
you are charged for actively-used files, not for every file that has ever been
touched.

### Base storage tier constraints

S3 Files works with Standard, Intelligent-Tiering and Infrequent Access as the
underlying bucket tier. It does **not** work with Glacier Flexible Retrieval,
Glacier Deep Archive or the Intelligent-Tiering archive tiers - those require a
standard S3 restore first.

This means you can put the authoritative data on Intelligent-Tiering at roughly
$0.0125/GB-month in the infrequent tier and still mount it as a filesystem,
paying hot-tier rates only on the active working set. S3 Intelligent-Tiering
transitions between classes are free, which matters because EFS equivalents
charge per-GB tiering fees.

### S3 Files vs EFS comparison

For an illustrative 10 TB workload with 90% cold data, 500 GB hot working set,
500 GB/month reads (90% large files / 10% small files), 100 GB/month writes:

| | EFS Legacy + IA | EFS Performance-optimised + Archive | S3 Intelligent-Tiering + S3 Files |
|---|---|---|---|
| Cold storage (9 TB) | ~$225 ($0.025/GB IA) | ~$72 ($0.008/GB Archive) | ~$115 ($0.0125/GB IT infrequent) |
| Hot working set (500 GB) | $150 ($0.30/GB Std) | $150 ($0.30/GB Std) | $12 (S3 IT) + Files surcharge on sub-128 KB portion only |
| Read 500 GB large | Included in throughput | ~$15 ($0.03/GB) | $0 (direct from S3) |
| Read 50 GB small | ~$0.50 IA reads | ~$4 ($0.03 + tier surcharge) | ~$3 ($0.06/GB first read) |
| Write 100 GB | Included | $6 ($0.06/GB) | $6 ($0.06/GB via Files) |
| Tiering transitions | $0.01/GB in and out | $0.01-$0.03/GB per transition | Free (S3 IT) |

EFS wins when the workload is metadata-heavy and small-file-dominated (no 32 KB
minimums on EFS). S3 Files wins on cold storage, large-file reads (free),
tiering flexibility, and any workload where the authoritative data already
lives in S3.

### When S3 Files fits

- ML training pipelines that chew through millions of small checkpoint files
  scattered across S3 - the existing duct-tape of Mountpoint and prayer
- Agentic AI workloads that need shared storage accessible by a mount command
  without the team becoming S3 API experts
- Legacy applications assuming POSIX semantics where the data of record needs
  to stay in S3 for durability, audit or downstream processing
- Any case where data gravity sits in S3 but one access path needs filesystem
  semantics

### When to stay on S3 API or EFS

- Current workloads happy with native S3 APIs - S3 Files does not replace them,
  it adds an access pattern
- Metadata-heavy workloads (directory listings, frequent stats, mass renames)
  where 4 KB per metadata op dominates the bill
- Ultra-latency-sensitive small-file reads where the $0.06/GB first-read import
  is a recurring hit
- Use cases that need filesystem features EFS supports but S3 Files does not

### Decision checklist

- [ ] Is the data already in S3 and does it need to stay there?
- [ ] What is the read/write mix between files above and below 128 KB?
- [ ] How metadata-heavy is the workload (listings, stats, renames)?
- [ ] Can the base tier run on Intelligent-Tiering or IA for the cold bulk?
- [ ] Are the 32 KB/4 KB minimums going to dominate or not?

The rate card matches EFS Performance-optimised. The savings come from the
design - free large-file reads straight from S3, pay-only-for-hot-slice
storage, and free Intelligent-Tiering transitions underneath. For workloads
with meaningful cold storage and large-file reads, this is a structurally
cheaper filesystem than EFS.

## AWS Multi-Organisation Billing Features

*Added: March 2026. Source: AWS Keys to AWS Optimization podcast, S16E5.*

Two features released at re:Invent 2024 allow FinOps teams to centralise cost visibility and billing operations across multiple AWS organisations. They are related but solve different problems and should not be conflated.

---

### Custom billing views (cross-organisation)

A billing view is an AWS resource that controls which accounts' cost and usage data a given account can access in Cost Explorer, budgets, and dashboards.

**What changed at re:Invent 2024:**

- A payer account can now share a billing view with a payer account in a *different* AWS organisation (previously limited to member accounts within the same org).
- A recipient account can combine multiple billing views -- including views received from other organisations -- into a single aggregated view, giving a unified Cost Explorer experience across several payer accounts.
- Budgets can now be scoped to a billing view, including cross-organisation views.

**Key behaviours:**

- The owner of a billing view retains full control and can modify or revoke it at any time. Changes are reflected in the recipient account and in any combined view that uses it as a source.
- Sharing outside an org requires the `billing-view:full-access` permission level for the recipient to use a view as a source in a combined view.
- Supported tools: Cost Explorer, dashboards, reports, budgets, and forecasts. Amazon Q integration is not yet supported (as of early 2026).
- Creating, sharing, and combining billing views is free. Cost Explorer API calls against a multi-organisation billing view are charged at $0.01 per organisation queried per API call (vs. the standard $0.01 per call for a single org).

**Typical use cases:** enterprises managing multiple AWS organisations after M&A; FinOps teams giving an external consultant read access to cost data without console access; business unit owners needing a budget that spans accounts across multiple payers.

---

### Billing transfer

Billing transfer is a delegation mechanism that allows one payer account (the "bill transfer account") to take over payment responsibility for another AWS organisation's charges (the "bill source account").

**What this enables:**

- Decouples billing from governance. The bill source organisation retains full control of its AWS environment, IAM, governance, and security. It simply delegates invoice responsibility to the bill transfer account.
- The bill transfer account receives the invoice and can view cost and usage data for the bill source organisation centrally, without logging into the source account.
- Integrates with AWS Billing Conductor so the bill transfer account can control what pricing data the bill source account sees (e.g. to protect negotiated rates or to model a reseller margin).

**Key behaviours:**

- The invite process is unidirectional: only the account *taking over* the bill can initiate the transfer. The bill source cannot push its bill to another account.
- Savings plans and credits remain bounded at the organisation level. They do not share across the transfer relationship.
- The bill transfer account sees two distinct views: (1) what it pays AWS for the source org's consumption (net of its own discounts); (2) what the source org sees in its own account -- the "showback view", gross of discounts. These amounts will differ if the bill transfer account has negotiated rates.
- Tax settings and contractual obligations require careful review before enabling billing transfer.
- A basic (public pricing) showback plan is free. A customised pricing plan (e.g. to apply a managed service fee) is charged at $50 per bill source organisation per month, effective June 2025.

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
| Supported tools | Cost Explorer, budgets, dashboards, reports | Cost Explorer, budgets, bills page |
| Pricing | Free (API surcharge for multi-org) | Free (basic) / $50/org/month (custom pricing plan) |

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
