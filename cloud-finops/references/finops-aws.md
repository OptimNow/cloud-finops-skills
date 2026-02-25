# FinOps on AWS

> AWS-specific guidance covering cost management tools, commitment discounts, compute
> rightsizing, cost allocation, and governance. Covers CUR, Cost Explorer, Compute
> Optimizer, Trusted Advisor, Savings Plans, Reserved Instances, and AWS-native
> FinOps patterns.

---

## AWS cost data foundation

### Cost and Usage Report (CUR)

CUR is the most granular billing data source AWS provides. It is the correct data source
for any serious FinOps implementation on AWS.

**Why CUR over Cost Explorer API:**
- Line-item granularity - every resource charge, every hour
- Includes resource tags, usage types, and pricing details not available in Cost Explorer
- Exportable to S3 for integration with third-party tools, Athena, or Redshift
- Supports FOCUS (FinOps Open Cost and Usage Specification) format export

**CUR setup checklist:**
- [ ] Enable CUR in the management (payer) account
- [ ] Configure S3 bucket with appropriate retention and access policies
- [ ] Enable resource IDs (required for tag-level allocation)
- [ ] Select hourly granularity (daily is insufficient for anomaly detection)
- [ ] Enable Athena integration for SQL-based analysis
- [ ] Consider enabling FOCUS format for tool-agnostic downstream use

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

**Cost Explorer limitations to know:**
- 24–48 hour data lag (unacceptable for real-time AI cost management)
- Cannot filter by resource-level tags without enabling resource-level data (additional cost)
- API queries are charged ($0.01 per request)
- Granularity limited to daily in the UI (hourly requires API)

**Useful Cost Explorer features:**
- **Rightsizing recommendations** - EC2 rightsizing based on CloudWatch utilization
- **Savings Plans recommendations** - commitment purchase recommendations based on usage
- **Cost anomaly detection** - ML-based anomaly alerts (set up before you need them)
- **Cost categories** - virtual tags for billing-layer cost allocation

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

## Commitment discounts

### Reserved Instances vs Savings Plans

The single most common commitment discount question. The answer depends on workload
characteristics, not a general preference.

| Dimension | Reserved Instances | Savings Plans |
|---|---|---|
| Flexibility | Low - locked to instance family, region, OS | High - applies across instance families and services |
| Discount depth | Up to 72% (Standard RI, full upfront) | Up to 66% (Compute Savings Plan) |
| Coverage scope | Specific EC2 instance type | EC2, Fargate, Lambda (Compute SP) |
| Convertibility | Convertible RIs allow instance family changes | N/A - flexible by design |
| Best for | Stable, predictable workloads with known instance types | Variable workloads or mixed instance families |

**Decision framework:**

1. Analyze 90+ days of historical usage - identify truly steady-state workloads
2. For workloads with stable instance types: evaluate Standard RIs (highest discount)
3. For workloads with variable instance types or mixed EC2/Fargate/Lambda: Compute Savings Plans
4. For EC2 with some flexibility needs: Compute Savings Plans or Convertible RIs
5. Layer commitments: buy Savings Plans first (broadest coverage), then RIs for specific
   high-stability workloads

**Key metrics:**
- **RI/SP Utilization:** Target >80%. Below this, you are paying for unused commitment.
- **RI/SP Coverage:** Target 70% (Walk), 80%+ (Run). Remaining on-demand is acceptable buffer.
- **Break-even period:** Should be <9 months for the commitment to be worth the risk.

**Before purchasing any commitment:**
- [ ] Confirm the workload has run stably for 90+ days
- [ ] Confirm no planned architecture changes in the commitment period
- [ ] Confirm the workload is tagged and attributable to an owner
- [ ] Verify utilization will sustain through the commitment term
- [ ] Do not commit to waste - rightsize first, commit second

### Spot Instances

For fault-tolerant, interruptible workloads, Spot offers up to 90% discount over on-demand.

**Appropriate workloads for Spot:**
- Batch processing, data pipelines, ML training jobs
- CI/CD build environments
- Stateless web tier behind a load balancer (with proper drain handling)
- Development and test environments

**Not appropriate for Spot:**
- Stateful applications without checkpoint/resume logic
- Production databases
- Workloads with strict latency or availability SLAs

**Spot best practices:**
- Use Spot Instance pools (multiple instance types and AZs) to reduce interruption risk
- Implement interruption handling (2-minute warning via EC2 metadata service)
- Use EC2 Auto Scaling mixed instances policy for automatic on-demand fallback

---

## Compute rightsizing

### EC2 rightsizing

Rightsizing is the highest-ROI optimization for most AWS environments at Crawl/Walk maturity.

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
- Rightsizing stateful databases without testing failover behavior
- Missing network-intensive workloads that appear CPU-idle but are IO-bound

### Container rightsizing (ECS / EKS)

Container rightsizing requires different tooling than EC2 rightsizing.

- AWS Compute Optimizer provides ECS on Fargate recommendations
- For EKS, use Kubernetes VPA (Vertical Pod Autoscaler) recommendations or cast.ai
- Right-size the pod requests/limits before right-sizing the underlying node group
- Node group rightsizing savings are partially offset by bin-packing efficiency changes

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

### AWS Budgets

Configure at minimum:
- Account-level monthly cost budget with 80% and 100% alerts
- Service-level budgets for top 3–5 cost drivers
- Anomaly detection monitor linked to cost anomaly detection

**Recommended alert recipients:** Both the FinOps practitioner and the engineering team
lead for the relevant account. FinOps-only alerts create a bottleneck; engineering-only
alerts lack financial context.

---

## AWS-specific quick wins

These actions typically deliver savings within 30 days with low risk.

| Action | Typical savings | Risk | Effort |
|---|---|---|---|
| Delete unattached EBS volumes | 100% of volume cost | None | Low |
| Release unassociated Elastic IPs | $3.65/IP/month | None | Low |
| Delete unused snapshots (>90 days old) | Variable | Low (verify no restore needed) | Low |
| Schedule dev/test EC2 stop outside business hours | 60–70% of instance cost | Low | Low |
| Move S3 infrequently accessed data to Infrequent Access | 40% storage cost | Low | Low |
| Right-size over-provisioned RDS instances | 20–50% RDS cost | Medium (test first) | Medium |
| Convert gp2 EBS volumes to gp3 | 20% EBS cost (same IOPS baseline) | Low | Low |
| Review and right-size NAT Gateway usage | Variable | Medium | Medium |
