---
name: finops-waste-detection-playbooks
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Anomaly Management", "Architecting & Workload Placement", "Automation, Tools & Services"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "SRE"]
fcp_maturity_entry: "Crawl"
---

# FinOps Waste Detection Playbooks

> Waste detection is the most concrete entry point to Cloud FinOps. Unlike
> commitment strategy or chargeback, waste hunting produces realised savings
> in the first month, with low organisational change required. This file is
> the OptimNow taxonomy for systematic waste detection - what to hunt for,
> how to detect it, how to fix it safely, and how to track realised savings
> over time.
>
> Operationally, OptimNow runs the **WasteLine** appliance - a private,
> read-only AWS waste-assessment tool with 49 detection rules across the
> seven categories below. WasteLine automates the detection-and-classification
> work; this file is the doctrine the appliance encodes. For Azure and GCP,
> use the in-cloud catalogues (`finops-azure.md` 48-pattern catalogue,
> `finops-gcp.md` 26-pattern catalogue) until WasteLine extends to those
> providers.

---

## The seven waste categories

Every cloud waste pattern fits into one of seven categories. Understanding the
category drives the detection method, the classification confidence, and the
fix-safety posture.

| Category | What it is | Typical $ impact | Classification confidence |
|---|---|---|---|
| **Orphaned** | Resource exists but no longer serves any workload | High per-resource, easy to spot | Usually obvious; some "DR-just-in-case" exceptions |
| **Idle** | Resource is attached and running but does no useful work | Variable; multiplied across many resources | Usually likely; needs two signals to confirm |
| **Overprovisioned** | Resource works but is sized far above observed demand | High aggregate; needs methodology to right-size | Usually possible; needs workload-owner sign-off |
| **Commitment mismatches** | RIs / Savings Plans / CUDs underutilised, expiring soon, or covering the wrong things | High dollar, low complexity to fix | Usually obvious in the data; political to act on |
| **Schedule blindness** | Workload runs 24/7 with a clear business-hours pattern | Variable; 60-70% savings on dev / test environments | Usually likely; depends on workload sensitivity |
| **Modernization opportunities** | Workload runs on older-generation instances or pre-Graviton x86_64 when ARM equivalents exist | 10-40% per workload, low risk | Usually possible; revalidation required |
| **AI / ML inefficiency** | SageMaker endpoints idle, Bedrock provisioned throughput underutilised, training jobs on-demand instead of Spot | High per-workload, growing rapidly | Usually likely; product team has the context |

These categories are not equal in priority. **Orphaned and idle** are where
most engagements should start - low-risk wins build the credibility for
harder commitment and modernization work later. **Commitment mismatches and
modernization** should land after at least one quarter of orphaned/idle
hunting has produced realised savings.

---

## Cross-category detection principles

### Two-signal classification rule

Never act on a single metric. The two-signal rule:

- **Compute idle** = low CPU AND low network for 30+ days (not CPU alone)
- **Idle load balancer** = no traffic AND no healthy targets (not just one)
- **Orphaned snapshot** = parent volume deleted AND not referenced by an AMI
- **NAT Gateway zombie** = low data processed AND route-table review confirms
  no active subnets depend on it

Single-signal detection produces false positives that erode trust. Two
signals reduce false-positive rates dramatically without losing real waste.

### Classification confidence tiering

Every detection should land in one of three confidence tiers:

| Tier | Definition | Action |
|---|---|---|
| **Obvious** | Both detection signals strongly positive; no plausible defensive use | Auto-decommission with snapshot + 30-day grace period |
| **Likely** | Both signals positive; some plausible exceptions exist | Owner notification with 14-day deadline; decommission on ack or timeout |
| **Possible** | One strong signal, one ambiguous; needs context | Owner conversation; decommission only after explicit approval |

The classification keeps the decommission workflow safe. Obvious waste does
not need a meeting; possible waste cannot be batched.

### Realised savings vs potential savings

The only number that matters is **realised savings**: monthly baseline
minus monthly post-cleanup cost, sustained for at least 60 days. Stop
reporting "potential savings" - stakeholders learn to discount these
within one quarter and the credibility of the FinOps practice degrades.

### Use FOCUS columns for inventory scope

For any cross-cloud or multi-account waste hunt, scope inventory queries
through FOCUS columns:

- `ServiceCategory='Compute' or 'Networking' or 'Storage'`
- `ChargeClass IS NULL` (exclude refunds and corrections from the baseline)
- `EffectiveCost` per `ChargePeriod` for prioritisation by dollar impact
- `ResourceId`, `ResourceType` to filter to the resource class being hunted

Provider-native columns (CUR `line_item_*`, Azure Cost Management, BigQuery
billing export) work too but break cross-cloud reuse. Default to FOCUS
where the data exists.

---

## Category 1: Orphaned resources

### Pattern shape

Resource exists in the cloud account but no longer serves any workload.
Typical sources:

- Migration leftovers (the volume from the test instance that was deleted
  six months ago)
- "Just-in-case" snapshots from one engineering experiment that compounded
  over years
- Decommissioned services where the load balancer was kept but never
  removed
- Account consolidation where elastic IPs were detached but never released

### Common patterns

| Pattern | Signal | Detection approach |
|---|---|---|
| Unattached EBS volumes (or equivalents) | `Attachment State = available`, `LastAttached > 14 days` | Inventory across regions; cross-reference with snapshot history |
| Orphaned EBS snapshots | Source volume ID does not exist; AMI reference does not exist | Snapshot age + parent-volume status query |
| Unassociated Elastic IPs | EIP allocated, no association to running resource | Direct inventory; high $ per resource ($3.65/month each) |
| Empty S3 buckets without lifecycle | Object count = 0, no lifecycle policy, age > 90 days | List buckets, filter by metadata - never enumerate objects |
| Security groups with no attached interfaces | No ENI references, no ALB/NLB reference, no Lambda VPC config reference | Reverse-lookup query |
| AMIs with no running instances | AMI ID not referenced by any instance, launch template, or ASG | Cross-reference inventory |
| ECR repositories without lifecycle | Repository exists, no lifecycle policy, last push > 90 days | Repository metadata query |
| Stale incomplete S3 multipart uploads | Multipart upload initiated > 7 days ago, never completed | S3 multipart inventory |
| Secrets Manager secrets not accessed in 90+ days | Secret exists, `LastAccessedDate > 90 days` | CloudTrail-derived access pattern |

### Detection example (orphaned EBS volumes via FOCUS)

```sql
SELECT
  ResourceId,
  ResourceType,
  Region,
  EffectiveCost AS monthly_cost,
  Tags
FROM focus_data
WHERE ServiceCategory = 'Storage'
  AND ResourceType = 'EBS Volume'
  AND ChargeClass IS NULL
  AND ChargePeriodStart >= current_date - interval '30' day
  -- Cross-reference with EC2 inventory: include only volumes
  -- that are NOT attached to any running instance
  AND ResourceId NOT IN (
    SELECT volume_id FROM ec2_volume_attachments
    WHERE attachment_state = 'attached'
  )
ORDER BY monthly_cost DESC;
```

### Fix sequence

1. **Snapshot before delete** for any storage resource. Snapshot cost is
   pennies; restoring deleted production data costs careers.
2. **Owner identification**: tag-based first, account-context fallback.
   If no owner can be identified, the resource enters a 30-day grace
   period with a `wasteline-orphan-pending-deletion` tag.
3. **Notification**: owner gets 14 days to claim or refute. No reply =
   continue with deletion.
4. **Decommission with rollback path**: snapshot retained for 30 days
   post-delete in case the resource turns out to have been load-bearing
   in a way nobody surfaced.
5. **Realised savings**: monthly baseline - monthly post-cleanup, tracked
   to the resource ID.

### Anti-patterns

- **Bulk delete without owner notification**. Even "obvious" orphans can
  be load-bearing in unexpected ways.
- **Skipping the snapshot step** for EBS or RDS resources. Recovery is
  cheap; data loss is not.
- **Treating empty S3 buckets as orphans without lifecycle check**. A
  bucket with `WriteOnly` access from a Lambda may legitimately appear
  empty between batch runs.

---

## Category 2: Idle resources

### Pattern shape

Resource is attached, running, and being billed, but does no useful work
during the observation window.

### Common patterns

| Pattern | Signal (both required) | Detection approach |
|---|---|---|
| Stopped EC2 for 7+ days | EC2 state `stopped`, EBS still billed | EC2 inventory + EBS attachment query |
| Idle load balancer | Zero healthy targets AND zero `RequestCount` over 14 days | CloudWatch metric query |
| CloudWatch Log Groups with no events | `LastEventTime > 30 days`, no events ingested | Log Group metadata |
| NAT Gateway low data | < 5 GB processed over 14 days, hourly charge dominates | CloudWatch `BytesOutToDestination` query |
| S3 bucket with zero requests | `AllRequests` metric = 0 over 60 days | CloudWatch S3 metrics |
| Lambda with zero invocations | `Invocations` = 0 over 30 days | CloudWatch Lambda metrics |
| DynamoDB table with no read/write | `ConsumedRead/WriteCapacity` = 0 over 30 days | CloudWatch DDB metrics |
| Redshift cluster low activity | CPU < 5% AND `DatabaseConnections` near zero | CloudWatch Redshift metrics |

### Detection example (NAT Gateway zombies)

```sql
-- 14-day NAT Gateway hours vs data processed (Athena over CUR 2.0)
SELECT
  line_item_resource_id AS nat_id,
  line_item_availability_zone AS az,
  SUM(CASE WHEN line_item_usage_type LIKE '%NatGateway-Hours' THEN line_item_usage_amount END) AS hours,
  SUM(CASE WHEN line_item_usage_type LIKE '%NatGateway-Bytes' THEN line_item_usage_amount END) / 1024.0 / 1024 / 1024 AS gb_processed,
  ROUND(SUM(line_item_unblended_cost), 2) AS cost_period
FROM cur2
WHERE line_item_usage_start_date >= current_date - interval '14' day
  AND product_servicecode = 'AmazonEC2'
  AND line_item_usage_type LIKE '%NatGateway%'
GROUP BY 1, 2
HAVING gb_processed < 5
ORDER BY cost_period DESC;
```

### Fix sequence

1. **Confirm both signals** are positive over the full observation window
   (the first signal could be temporary).
2. **Check for downstream dependencies**: route tables for NAT Gateways,
   DNS for load balancers, Lambda triggers for log groups.
3. **Owner notification with deadline**: idle resources are more likely
   than orphans to have a "but I might need it next week" defender.
4. **Decommission with rollback**: stopped instances can be deleted; NAT
   Gateways can be recreated in minutes; load balancers can be redeployed
   from IaC.
5. **For NAT specifically: consider VPC Endpoints as substitute** -
   gateway endpoints (S3, DynamoDB) are free; interface endpoints scale
   better than NAT for high-volume internal SaaS traffic.

### Anti-patterns

- **Single-metric detection**. CPU = 0 alone catches DR-standby instances.
  Always require two signals.
- **Deleting NAT without route-table review**. Cuts off management
  traffic; orphans the resources downstream.
- **Treating "stopped EC2" as cost-free**. EBS volumes attached to
  stopped instances continue to bill at full rate.

---

## Category 3: Overprovisioned resources

### Pattern shape

Resource is doing useful work but at a fraction of its allocated capacity.
Right-sizing reduces cost without functional change.

### Common patterns

| Pattern | Signal | Detection approach |
|---|---|---|
| EC2 with consistently low CPU | p95 CPU < 30% over 14 days, no memory pressure | CloudWatch + Compute Optimizer cross-reference |
| EBS on suboptimal type | gp2 → gp3 (always cheaper, equal perf), io1/io2 with low IOPS | EBS inventory + IOPS observation |
| RDS with low CPU and connections | CPU < 25% AND connections << max | CloudWatch RDS metrics |
| S3 bucket > 100 GB without lifecycle / Intelligent-Tiering | Bucket size > 100 GB, no lifecycle, no IT enabled | S3 metadata query |
| S3 versioning without noncurrent expiration | Versioning ON, no rule to expire noncurrent versions | S3 lifecycle inspection |
| CloudWatch Log Groups without retention | `RetentionInDays = null` (i.e. infinite) | Log Group metadata |
| DynamoDB provisioned without autoscaling | Provisioned billing mode, no autoscaling target | DDB metadata |
| Fargate services at fixed task count | No autoscaling configured | ECS service inspection |
| Redundant CloudTrail trails | Multiple trails recording same events in same account/region | CloudTrail trail enumeration |

### Detection example (EBS gp2 → gp3 migration candidates)

```sql
SELECT
  ResourceId,
  Region,
  Tags['team'] AS team,
  EffectiveCost AS gp2_monthly_cost,
  -- gp3 base price + IOPS + throughput vs gp2 base price
  -- gp3 is ~20% cheaper than gp2 for equivalent specs in most regions
  EffectiveCost * 0.8 AS estimated_gp3_cost,
  EffectiveCost * 0.2 AS estimated_monthly_savings
FROM focus_data
WHERE ServiceCategory = 'Storage'
  AND ResourceType = 'EBS Volume'
  AND Tags['volume_type'] = 'gp2'  -- mapping from provider tag
  AND ChargeClass IS NULL
  AND ChargePeriodStart >= current_date - interval '30' day
ORDER BY estimated_monthly_savings DESC;
```

### Fix sequence

1. **Right-sizing recommendations from multiple sources**: AWS Compute
   Optimizer, native CloudWatch percentiles, and the WasteLine appliance
   all generate recommendations - cross-reference for confidence.
2. **Stage rollouts**: dev → staging → prod canary → prod, with one week
   monitoring per stage. Right-sizing too aggressively causes throttling
   or OOMKills that destroy trust in the recommendation pipeline.
3. **Memory headroom matters**. CPU is the easy metric; memory regressions
   are catastrophic. For workloads where memory is the constraint, default
   to a 30% margin above p99.
4. **Document the recommendation rationale**. The owner needs to be able
   to defend the change in their sprint review. "Compute Optimizer
   recommended this" is enough; "we just thought it was high" is not.
5. **Track realised savings per recommendation**. Some recommendations
   will fail in production and get reverted - the savings number must
   reflect what stuck, not what was proposed.

### Anti-patterns

- **Bulk right-sizing in one pass**. Blast radius is the entire
  optimisation programme's credibility.
- **CPU-only sizing recommendations**. Memory regressions cause OOMs;
  network regressions cause throttling that masquerades as application
  bugs.
- **Right-sizing immediately after a major workload change** (deployment,
  feature launch, traffic event). Wait 14+ days for the new baseline to
  stabilise.
- **Ignoring volume-type modernisation**. gp2 → gp3 is the cheapest
  optimisation in most accounts; there is rarely a reason not to do it.

---

## Category 4: Commitment mismatches

### Pattern shape

Reserved Instances, Savings Plans, or Committed Use Discounts that are
underutilised, expiring soon, locked to the wrong configuration, or
missing where eligible spend would benefit. Provider-specific commitment
mechanics live in `finops-aws.md`, `finops-azure.md`, `finops-gcp.md`.

### Common patterns

| Pattern | Signal | Detection approach |
|---|---|---|
| RI utilisation < 80% | `Utilization` metric below threshold over 30 days | Cost Explorer Reservations utilisation |
| RI approaching expiration | `ExpirationDate < 60 days from now` | Reservation inventory + expiration sort |
| Savings Plan utilisation < 80% | Cost Explorer Savings Plans utilisation report | SP utilisation query |
| Eligible spend not covered by SP | On-demand spend in regions/families that an SP would cover | Coverage gap analysis |
| ElastiCache without reserved coverage | Long-running clusters, no reserved nodes | ElastiCache + Reservations cross-reference |

### Detection example (RI utilisation gap)

```sql
SELECT
  reservation_id,
  instance_type,
  region,
  scope,
  expiration_date,
  utilization_pct,
  effective_hourly_cost,
  -- Wasted hours = total hours - utilised hours
  (1 - utilization_pct) * 730 AS wasted_hours_per_month,
  (1 - utilization_pct) * 730 * effective_hourly_cost AS wasted_dollars_per_month
FROM ri_utilization_report
WHERE utilization_pct < 0.80
  AND DATEDIFF('day', current_date, expiration_date) > 30  -- exclude near-expiry
ORDER BY wasted_dollars_per_month DESC;
```

### Fix sequence

1. **Distinguish underutilised from expiring**: underutilised commitments
   may be modifiable (RI exchange / modify); expiring commitments need a
   renewal decision.
2. **Modify before recommending new purchases**: the AWS / Azure / GCP
   liquidity rules described in the per-cloud files allow exchange or
   modification of existing commitments. Use them before adding more.
3. **Quarterly reassessment cadence**: commitment portfolio review is a
   quarterly cycle, not a one-off optimisation.
4. **Coverage gap analysis**: for stable spend not covered by an SP, build
   a tranche purchase recommendation - never a single large commitment.

See `finops-aws.md`, `finops-azure.md`, `finops-gcp.md` for the
provider-specific commitment portfolio strategies.

### Anti-patterns

- **Letting RIs expire without a decision**. The default behaviour is
  "do nothing"; the right behaviour is "renew, modify, or let expire
  intentionally". Expiry calendar surfaced 90 days in advance.
- **Recommending new commitments while existing commitments are
  underutilised**. Always modify or exchange first.
- **100% coverage targets**. Always silent waste - see `finops-aws.md`
  on portfolio liquidity.

---

## Category 5: Schedule blindness

### Pattern shape

Workload runs 24 hours a day, 7 days a week, but only does meaningful
work during business hours. Dev, test, and staging environments are the
classic case. Some production workloads (batch processing, weekly
reporting jobs) also fit.

### Common patterns

| Pattern | Signal | Detection approach |
|---|---|---|
| EC2 with clear business-hours pattern | High utilisation 9am-6pm weekdays, near-zero rest of time | CloudWatch CPU + network usage windowed analysis |
| Redshift cluster without pause/resume | Cluster running 24/7, low overnight CPU | CloudWatch Redshift metrics + scheduling metadata |

### Fix sequence

1. **Identify the schedule pattern from observed usage**, not from
   assumed business hours. Some teams really do work weekends or split
   shifts.
2. **Pilot on dev/test environments first**. Production scheduling has
   complications (long-running batch jobs, cross-time-zone teams) that
   dev does not.
3. **Tag-driven scheduling pattern**: workloads tag themselves with the
   schedule they support (`schedule=business-hours`, `schedule=24x7`,
   `schedule=batch-overnight`). Scheduler reads tags. New workloads
   default to a tag that requires explicit opt-out from scheduling.
4. **Realised savings**: 60-70% on dev / test that moves to business
   hours; 30-40% on production batch workloads that pause overnight.

### Anti-patterns

- **Scheduling production without owner sign-off**. Production downtime
  windows need explicit approval from the workload owner; never inferred.
- **Hard-coding schedules in IaC without tag indirection**. Hard-coded
  schedules drift; tag-driven scheduling adapts to workload changes.

---

## Category 6: Modernization opportunities

### Pattern shape

Workload runs on older-generation instance families, x86_64 architectures
where ARM (Graviton) equivalents exist, or services on AWS Extended
Support pricing. Modernization typically delivers 10-40% savings with low
operational risk if the workload supports the target architecture.

### Common patterns

| Pattern | Signal | Detection approach |
|---|---|---|
| EC2 on older generation | Instance family in t2/m4/c4/r4/i3 (newer equivalents available) | EC2 inventory + family taxonomy |
| x86_64 with Graviton equivalent | Instance family has a Graviton variant | EC2 inventory + Graviton mapping table |
| io1 EBS migrable to io2 | io1 volumes (io2 is same price, better durability) | EBS inventory by type |
| RDS on older instance class | RDS family is db.t2 / db.m4 / db.r4 / etc. | RDS inventory |
| RDS on Extended Support | Engine version flagged as Extended Support (paid surcharge) | RDS engine version + AWS pricing |
| Lambda x86_64 with ARM64 available | Lambda runtime supports both architectures | Lambda function inventory |
| Fargate task definition x86_64 | Task definition lists x86_64 architecture | Fargate inventory |

### Fix sequence

1. **Validate the workload supports the target architecture**: most
   stateless workloads do; some with native compiled dependencies do not.
2. **Test in lower environment first**: deploy on the new architecture
   in dev, run integration tests, confirm performance is equivalent.
3. **Stage the migration**: production canary (5-10% of traffic), then
   25%, 50%, 100%. Each stage held for 48-72 hours with metrics monitored.
4. **Have a rollback plan**: blue-green deployment or feature flag that
   reverts to the old architecture if metrics regress.
5. **Track realised savings against the new instance type cost**. ARM
   typically delivers 20-30% savings on equivalent workloads; older →
   newer generation typically 15-25%.

### Anti-patterns

- **Bulk migrating production without validation**. Some workloads have
  ARM-incompatible dependencies (legacy compiled binaries, older Java
  versions, some database drivers). Validation in staging is mandatory.
- **Treating modernization as one-time work**. New instance generations
  ship every 12-18 months. Modernization is a continuous process, not
  a project.
- **Ignoring Extended Support charges**. RDS Extended Support pricing is
  significant (typically 2-3x the base rate); migration to a supported
  version is usually the highest-ROI single optimisation in an account.

---

## Category 7: AI / ML inefficiency

### Pattern shape

AI workloads (SageMaker, Bedrock, GPU-instance training) generate waste
patterns that traditional FinOps tooling does not catch. Idle endpoints,
unused notebook instances, training jobs on-demand instead of Spot, and
provisioned throughput locked to the wrong model version are the
high-frequency patterns.

For broader AI cost-management discipline (token economics, agentic
patterns, ROI frameworks), see `finops-for-ai.md`,
`finops-ai-value-management.md`, `finops-genai-capacity.md`. For
provider-specific AI billing, see `finops-bedrock.md`,
`finops-azure-openai.md`, `finops-vertexai.md`, `finops-anthropic.md`.

### Common patterns

| Pattern | Signal | Detection approach |
|---|---|---|
| Bedrock Provisioned Throughput underutilised | p95 utilisation < 80% over 14 days | CloudWatch Bedrock utilisation |
| Bedrock PT locked to superseded model | Model version is older than the current generally-available equivalent | Bedrock inventory + model version mapping |
| Orphaned custom Bedrock models | Custom or imported model with zero invocations | Bedrock model inventory + invocation history |
| Bedrock on-demand in short bursts | Usage concentrated in short windows that batch-inference would handle | Invocation pattern analysis |
| Top-tier Bedrock model concentration | High share of tokens going to the most expensive model | Token-by-model breakdown (a conversation starter, not a hard rule) |
| Idle SageMaker notebook instances ([aws-sagemaker-notebook-always-on](../playbooks/aws-sagemaker-notebook-always-on.md)) | Notebook running, no kernel activity over 7 days | SageMaker inventory + activity check |
| Idle SageMaker endpoints ([aws-sagemaker-idle-endpoint](../playbooks/aws-sagemaker-idle-endpoint.md)) | Endpoint deployed, zero invocations over 30 days | CloudWatch SageMaker invocation metrics |
| Stale SageMaker Studio apps | Studio app running > 24 hours without user activity | Studio app metadata |
| Training jobs on-demand instead of Spot | SageMaker training job uses on-demand instances; checkpointing supported | SageMaker training job inventory |
| SageMaker endpoint sprawl ([aws-sagemaker-mme-consolidation](../playbooks/aws-sagemaker-mme-consolidation.md)) | 3+ lightly-used endpoints in same account/region, each on dedicated instance | Endpoint inventory grouped by account/region + invocation rates |
| Oversized GPU instance ([aws-gpu-instance-oversized](../playbooks/aws-gpu-instance-oversized.md)) | `DCGM_FI_PROF_GR_ENGINE_ACTIVE` < 20% AND `DCGM_FI_DEV_FB_USED` < 40% over 14 days | DCGM Exporter telemetry (CloudWatch `GPUUtilization` is misleading - see `finops-for-ai.md`) |
| Multi-GPU instance running single-GPU workload ([aws-multi-gpu-underutilized](../playbooks/aws-multi-gpu-underutilized.md)) | 7 of 8 GPUs near-zero utilisation on a multi-GPU instance | Per-GPU DCGM telemetry; CloudWatch does not expose per-device breakdown |
| GPU partition (MIG) candidate ([aws-mig-candidate](../playbooks/aws-mig-candidate.md)) | A100/H100 workload using < 1/7 of compute AND < 10 GB frame buffer | DCGM `DCGM_FI_PROF_GR_ENGINE_ACTIVE` + `DCGM_FI_DEV_FB_USED` |
| GPU instance for CPU-bound workload ([aws-gpu-for-cpu-bound-workload](../playbooks/aws-gpu-for-cpu-bound-workload.md)) | GPU idle (`GR_ENGINE_ACTIVE` < 5%) while CPU saturated (> 60%) | DCGM + CloudWatch `CPUUtilization` |
| Outdated GPU generation ([aws-outdated-gpu-generation](../playbooks/aws-outdated-gpu-generation.md)) | Significant hours on P3/G4dn while workload is compatible with G5/G6/P4d/P5 | CUR `product_instance_type` filter + workload framework check |

### Fix sequence

1. **Idle endpoints / notebooks: stop, do not delete**. Stopped resources
   can be restarted; deleted ones lose state. Notify owner with a 30-day
   stop-vs-delete decision window.
2. **Bedrock Provisioned Throughput underutilised**: switch to on-demand
   if the utilisation pattern is genuinely low; or right-size the PT
   commitment to the observed p95.
3. **Training on-demand → Spot**: validate the training job supports
   checkpointing (most modern training frameworks do). Spot delivers
   60-70% savings on long-running training jobs.
4. **Model version modernisation**: PT locked to a superseded model
   often costs more than the current equivalent. Migration requires
   the application team to validate the new model's behaviour; budget
   for the validation cycle.

### Anti-patterns

- **Treating AI workloads as standard EC2 cost-optimisation targets**.
  The AI cost surface is different - token economics, model selection,
  inference batching all matter more than instance rightsizing.
- **Aggressive idle-endpoint deletion**. SageMaker endpoints are often
  paused intentionally during product cycles; stop is safer than delete.
- **PT decisions made without product-team context**. Provisioned
  Throughput commitments are tied to product roadmap; FinOps cannot
  decide unilaterally to switch off.

---

## Operational tooling

OptimNow's WasteLine appliance is the operational tool for this
discipline on AWS. It implements the seven categories above as 49
deterministic detection rules, with read-only AWS access, classification
confidence per finding, executive reporting, and proposal-only remediation
artifacts (CLI scripts, Terraform snippets, OpenOps workflows).

What WasteLine adds beyond a manual hunt:

- **Deterministic, repeatable detection**: same scan run twice produces
  the same findings. Drift between human auditors is eliminated.
- **Region-aware pricing**: bundled pricing snapshot covering the major
  EC2 / RDS / ELB / NAT types across 12 regions
- **CUR integration**: replaces on-demand price estimates with actual
  amortised costs from the customer's CUR via Athena
- **AWS-native ingestion**: imports Cost Optimization Hub and Compute
  Optimizer recommendations and deduplicates with WasteLine's own
  findings
- **Multi-account / multi-tenant**: scheduled Fargate scans with S3
  history, dashboard with executive view
- **Anonymised MCP server**: AI agents can query the findings without
  the underlying scan data being exposed - resource IDs, ARNs, account
  IDs, and tags are stripped at the MCP boundary

For Azure and GCP waste detection, the cloud-specific catalogues in
`finops-azure.md` (48-pattern catalogue) and `finops-gcp.md` (26-pattern
catalogue) cover the same waste taxonomy applied to those providers.
WasteLine extension to Azure and GCP is on the roadmap.

---

## Crawl / Walk / Run progression

### Crawl - manual hunt

- Quarterly hunt across the seven categories using native AWS tooling
  (Cost Explorer, Compute Optimizer, Trusted Advisor) plus per-cloud
  Azure / GCP equivalents
- Manual two-signal classification with spreadsheet tracking
- Owner notification via email or Slack with manual deadline tracking
- Realised savings tracked monthly per resource ID

### Walk - tool-assisted hunt

- WasteLine deployed against AWS estate (or equivalent automation for
  Azure / GCP) running monthly
- Findings routed into team Slack channels with classification
  confidence
- Tag-driven aging policies for orphaned and idle resources (Joe Daly
  pattern: tag with date, snapshot + terminate after configured grace
  period, opt-out via tag)
- Lifecycle policies for snapshots, logs, S3 storage classes
- Quarterly waste-reduction KPI tracked alongside other FinOps metrics

### Run - continuous detection

- WasteLine on scheduled Fargate scans across all accounts; results
  persisted to S3 history
- Continuous waste detection feeding directly into the team's existing
  workflows (PR cost annotations, Slack notifications, JIRA tickets)
- Automated decommission for the obvious tier (orphaned snapshots past
  the grace period, unattached EBS volumes past 30 days untagged)
- Likely tier still requires owner ack; possible tier always requires
  human review
- Realised savings tracked as a continuous KPI; waste is a metric that
  trends down quarter-over-quarter

---

## Anti-patterns (across all categories)

- **Single-metric detection** producing false positives that erode trust
- **Bulk delete based on one signal**. Always require two signals and
  classify confidence
- **Reporting "potential savings"**. Stakeholders learn to discount these.
  Track realised savings only.
- **Skipping owner notification for "obvious" waste**. Even obvious
  orphans can be load-bearing in unexpected ways.
- **Treating waste detection as a one-time project**. Cloud waste
  regenerates as workloads change. Continuous detection is the only
  durable answer.
- **Aggressive deletion before snapshot or rollback path is in place**.
  Customer-critical data loss is career-ending.
- **No realised-savings tracking**. Without the closing-the-loop
  measurement, the programme has no signal of its own effectiveness and
  no defence against the inevitable "are we sure this is working?"
  conversation.

---

## Cross-references

- `finops-aws.md` - AWS-specific commitment, EC2, RDS, EDP guidance
  (the Category 4 details)
- `finops-azure.md` - Azure 48-pattern catalogue (Azure-side equivalents
  to the seven categories above)
- `finops-gcp.md` - GCP 26-pattern catalogue (GCP-side equivalents)
- `finops-tagging.md` - tag enforcement is the prerequisite for
  owner-driven decommission workflows
- `finops-allocation-showback.md` - waste hunting reads from the same
  FOCUS dataset as showback; shared infrastructure
- `finops-anomaly-management.md` - anomaly detection catches sudden waste
  events; this file catches sustained-state waste
- `finops-kubernetes.md` - K8s-cluster-specific waste (idle nodes,
  oversized requests) is covered there
- `finops-for-ai.md` - broader AI cost discipline behind the Category 7
  patterns
- `finops-bedrock.md`, `finops-azure-openai.md`, `finops-vertexai.md` -
  provider-specific AI inefficiency context
- `optimnow-methodology.md` - the maturity-aware framing this file
  builds on

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
