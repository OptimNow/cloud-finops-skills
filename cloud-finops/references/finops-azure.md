# FinOps on Azure

> Azure-specific guidance covering cost management tools, commitment discounts, compute
> rightsizing, database and storage optimization, cost allocation, and governance.
> Covers Cost Management exports, Azure Advisor, Reservations, Savings Plans, Azure
> Hybrid Benefit, Azure Policy, AKS optimization, and Log Analytics cost control.
>
> Distilled from the [Azure FinOps Master](https://github.com/yourorg/azure-finops-master)
> course (7 sessions + case studies).

---

## Azure cost data foundation

### Azure Cost Management exports

Azure Cost Management is the native cost visibility tool. For serious FinOps
implementations, configure scheduled exports to Azure Storage for downstream processing.

**Export types:**
- **Actual cost** - charges as they appear on the invoice (use for billing reconciliation)
- **Amortized cost** - reservation and savings plan charges spread across the usage period
  (use for team-level showback and allocation)

**Export setup checklist:**
- [ ] Configure exports at the appropriate billing scope (Management Group for org-wide view)
- [ ] Select both actual and amortized cost exports
- [ ] Set daily granularity
- [ ] Export to Azure Data Lake Storage Gen2 for Power BI integration
- [ ] Consider FinOps Hubs (Microsoft FinOps Toolkit) for automated ingestion and normalization

### Retail Prices API for validation

Use the Azure Retail Prices API to verify EA discounts against public pricing. Useful for:
- Comparing PAYG vs Reserved Instance pricing with ROI calculation
- Evaluating Spot VM savings potential (60-90% off PAYG)
- Estimating database and storage tier costs across regions
- Validating that EA discount percentages match contracts

### FinOps Toolkit and FinOps Hubs

Microsoft's open-source FinOps Toolkit provides pre-built solutions including Power BI
report templates, Azure Workbooks, and FinOps Hubs for automated cost data ingestion.

**FinOps Hubs** normalize cost exports into a consistent schema and feed Power BI reports.
Recommended for organizations that want production-grade reporting without building custom
data pipelines.

Repository: https://github.com/microsoft/finops-toolkit

### Azure Resource Graph for cost analysis

Azure Resource Graph (ARG) enables large-scale resource inventory and compliance analysis
with KQL queries. Use it for:
- VM analysis by family, OS disk type, hybrid benefit status
- Storage disk type summary (Premium, Standard SSD, Standard HDD, Ultra)
- Tagging compliance analysis with percentages
- Resource distribution by business unit/owner

---

## Commitment discounts

### Azure Reservations vs Azure Savings Plans

| Dimension | Azure Reservations | Azure Savings Plans for Compute |
|---|---|---|
| Flexibility | Low - locked to specific VM family/region | High - applies across VM families and regions |
| Discount depth | Higher (up to 72% for some VM families) | Lower but broader coverage |
| Coverage scope | Specific resource type | Compute (VMs, Dedicated Hosts) |
| Best for | Stable workloads with known VM types | Variable workloads, mixed VM families |

**Decision framework:**
1. Analyze 90+ days of historical usage - identify truly steady-state workloads
2. For workloads with stable VM types: evaluate Reservations (highest discount)
3. For workloads with variable types or mixed compute: Azure Savings Plans
4. Layer commitments: Savings Plans first (broadest coverage), then RIs for specific
   high-stability workloads

**Key metrics (same as AWS):**
- **Utilization:** Target >80%. Below this, you are paying for unused commitment.
- **Coverage:** Target 70% (Walk), 80%+ (Run). Remaining on-demand is acceptable buffer.

**Before purchasing any commitment:**
- [ ] Confirm the workload has run stably for 90+ days
- [ ] Confirm no planned architecture changes in the commitment period
- [ ] Confirm the workload is tagged and attributable to an owner
- [ ] **Do not commit to waste** - rightsize and shut down idle resources first, commit second

### Azure Hybrid Benefit (AHB)

Organizations with existing Windows Server or SQL Server licenses (with Software Assurance)
can apply them to Azure VMs, eliminating the license premium.

**Why this matters:** Windows license costs can account for 44% of a Windows VM price.
Example: D4_v5 Windows at ~0.35/hr = ~0.19 (compute) + ~0.15 (Windows license). Without
AHB, you double-pay for licenses you already own.

**AHB details:**
- Up to 40% savings on Windows VMs, up to 55% on SQL Database
- No architectural change, no restart needed - single CLI command per VM
- Also applies to SQL Managed Instance and Red Hat/SUSE Linux
- Use the AHB Workbook from FinOps Toolkit for compliance tracking across the fleet
- **Priority: #1 quick win** - enable on all eligible VMs immediately

### Spot Virtual Machines

For fault-tolerant, interruptible workloads, Spot offers up to 90% discount over PAYG.

**Appropriate for Spot:** Batch processing, dev/test, CI/CD, stateless pods in AKS
**Not appropriate:** Stateful databases, workloads with strict SLA requirements

**Key constraint:** 30-second eviction notice, no SLA guarantees. Start with 20-30% spot
allocation in non-production, increase based on stability observations.

---

## Compute rightsizing

### VM cost model

**Cost drivers:** Compute (SKU, hours, licensing), storage (managed disks),
networking (egress), indirect costs (monitoring, backups).

**Critical insight:** When stopped (deallocated), you still pay for storage and
public IPs. You save compute and license costs.

### VM SKU naming convention

Understanding Azure VM names is essential for rightsizing decisions:

```
D 4 a s _v5
│ │ │ │   │
│ │ │ │   └── Generation (newer = better price/performance)
│ │ │ └────── Premium storage support
│ │ └──────── AMD CPU (cheaper than Intel)
│ └────────── vCPU count
└──────────── Family (D=general, B=burstable, E=memory, F=compute, N=GPU)
```

**Other modifiers:** `p` = ARM CPU (cheapest, requires workload compatibility),
`m` = more memory, `d` = local temp SSD.

### VM family selection

| Family | Memory per vCPU | Best for | Cost position |
|---|---|---|---|
| **B-series** | Varies | Spiky, mostly-idle workloads (dev/test, small web) | 15-55% cheaper than D-series |
| **D-series** | 4 GB | General purpose | Baseline |
| **E-series** | 8 GB | Memory-optimized (databases, caches) | Premium over D |
| **F-series** | 2 GB | Compute-optimized (batch, gaming) | Cheaper per vCPU |

**AMD-based variants** (Das, Eas): Better price/performance vs Intel equivalents.
**ARM-based variants** (Dps, Eps): Cheapest option for compatible workloads (web, containers).

### Azure Advisor for rightsizing

Azure Advisor provides cost optimization recommendations based on CPU/memory utilization
from Azure Monitor.

**Rightsizing with Azure Advisor:**
- Access via Azure Portal > Advisor > Cost tab
- Recommendations based on 7-30 days of utilization data (configurable)
- Uses P95 CPU utilization as primary metric
- Shows estimated monthly savings per recommendation
- Can be exported to CSV for bulk review

**Azure Advisor limitations:**
- Conservative recommendations - does not account for SKU feature constraints
- Don't follow blindly - always validate with workload owners
- Missing memory analysis if Azure Monitor agent not installed
- Doesn't catch network-intensive workloads that appear CPU-idle

**Manual rightsizing approach:** Monitor CPU (avg, max, P95), memory, network I/O over
30 days. Candidates: VMs with <20% avg CPU utilization. RI opportunities: VMs with >80%
uptime.

### Automated start/stop schedules

The highest-impact quick win for non-production environments.

**Savings math:** Office hours (10h x 5 days/week = 217h/month vs 730h/month) = up to
70% cost reduction on non-production compute.

**Implementation options:**
- Azure DevTest Labs auto-shutdown (simplest, shutdown only)
- **Start/Stop VMs v2** (Microsoft recommended, supports both start and stop)
- Azure Automation Runbooks (most customizable)
- Infrastructure as Code (Terraform `azurerm_dev_test_schedule`, Bicep)

**Tagging strategy for automation:** Use `startTime` and `stopTime` tags on VMs.
Automation reads tags to determine schedule. This allows per-VM scheduling without
modifying the automation logic.

### VM generation upgrades

Newer VM generations improve price/performance ratio. Examples:
- D2s_v3 > D2s_v5: sometimes cheaper AND better performance
- E4_v3 > E4as_v5: AMD variant gives further savings

Review VM generations quarterly and upgrade where possible.

### Region placement for cost

Azure pricing varies significantly by region. India is cheaper, Brazil is expensive.
Dev/test workloads can often use cheaper regions without user-facing impact.
Use the Retail Prices API to compare regions programmatically.

---

## Database cost optimization

### Azure SQL Serverless (auto-pause)

**Best for:** Dev/test databases, intermittent usage, low average utilization.

- Auto-pause delay: configurable 1-7 days (or disabled)
- Auto-resume: automatic on first connection
- Billing: per-second compute; storage charged even when paused
- 100% automated - no scripts or runbooks needed

**Key decision:** Higher per-second compute rate than provisioned, but if the database is
idle most of the time, total cost is much lower.

### Elastic Pools

Share compute resources across multiple databases on the same logical server.

**Best for:** SaaS apps (one DB per tenant), databases with different peak times,
consolidation of small databases.

**Savings:** 20-40% cost reduction vs individual databases. Constraint: must be same
logical server, region, subscription.

### DTU vs vCore pricing

- **DTU:** Predictable pricing, good for small/uncertain workloads
- **vCore:** Better for migrations (license reuse via AHB), more control over compute/storage
- **Serverless (vCore):** Higher hourly rate but auto-pause makes it cheaper for intermittent use

### PostgreSQL/MySQL Flexible Server start/stop

- Manual start/stop via Portal, CLI, or API
- When stopped: **70-80% cost reduction** (storage-only billing)
- Auto-restart after 7 days (PostgreSQL) or 30 days (MySQL) if not manually started
- HA must be disabled for start/stop to work
- Ideal for dev/test environments

### Database architecture principles

- **Only keep active working set in relational DB.** Move cold data to Blob (Cool/Archive tier).
- **Avoid "one instance per application" by default.** Consolidate databases to increase utilization.
- **Active data in Premium, cold data in Blob.** Avoid storing backups on premium disks.
- **High availability has a cost.** Balance resilience requirements against budget per environment.

---

## Storage cost optimization

### Blob lifecycle management

**Tier pricing (approximate, per GB/month):**

| Tier | Price | Best for | Minimum retention |
|---|---|---|---|
| Hot | ~$0.018 | Frequent access | None |
| Cool | ~$0.01 | Infrequent (30+ days) | 30 days |
| Archive | ~$0.002 | Rare access (compliance) | 180 days |

**Typical lifecycle policy:**
1. Move to Cool after 30 days of no access (50% savings)
2. Move to Archive after 90 days (90% savings)
3. Delete temporary/log data after 180 days

**Lifecycle actions:** `tierToCool`, `tierToArchive`, `delete`,
`enableAutoTierToHotFromCool` (auto-promote on access).

### Ephemeral OS disks

- **Savings:** 100% on OS disk storage costs (uses VM cache or temp disk instead)
- Best for stateless workloads, scale sets, dev/test VMs
- Requirement: VM must support ephemeral disks, cache/temp disk >= OS disk size
- Example: 100 VMs x 128GB P10 disks = ~$640/month eliminated

### Recovery Services Vault archive

- Archive tier: ~$0.0025/GB/month vs Standard: ~$0.05/GB/month = **95% savings**
- Move backups >90 days old to archive tier automatically
- Example: 10TB backup archive saves ~$486/month vs Standard tier

### Snapshot and version cleanup

- Lifecycle policies can auto-delete old blob versions and snapshots
- Enable blob versioning for data protection, then auto-delete versions >30 days
- Snapshot cleanup alone can reduce storage costs 20-40%

---

## Monitoring cost optimization (Log Analytics)

Log Analytics is a hidden cost driver. Unmanaged, it can exceed the cost of the
workloads it monitors.

### Pricing structure

- **Ingestion:** ~$2.50/GB (first 5GB/day free per subscription)
- **Retention:** First 30 days included, then ~$0.10/GB/month for 31-730 days
- **Archive:** ~$0.02/GB/month (data >90 days)
- **Commitment tiers** (high-volume workspaces): 100GB/day = 22% savings, 200GB/day = 27%,
  500GB/day = 36%

### Top cost control actions

**1. Set daily ingestion cap**
- Prevents cost spikes from misconfigured apps, verbose logging, or security incidents
- Set at 120-150% of normal daily usage
- Configure alerts at 80% and 100% of cap
- **Warning:** When cap is reached, data collection stops until next day

**2. Optimize retention**
- Operational logs: 30 days (included in ingestion cost)
- Security logs: 90 days (if compliance requires it)
- Everything else: 30 days default
- Extending retention from 30 to 90 days doubles cost

**3. Filter verbose sources**
- Container Insights filtering: 40-60% ingestion reduction
- Application Insights sampling (50% sample rate = 50% savings)
- Performance counter optimization: 30-40% reduction
- Disable verbose diagnostic settings on unused resources

**4. Use Basic Logs for low-value data**
- Basic Logs: ~$0.60/GB (50% cheaper), limited retention (30 days), limited queries
- Use for verbose, low-value logs; keep Analytics tier for important operational/security logs

**5. Table-level retention**
- SecurityEvent: 90+ days (compliance)
- Heartbeat: 30 days
- Perf counters: 30 days
- ContainerLog: 7-30 days

### Cost impact examples

| Scenario | Before | After | Savings |
|---|---|---|---|
| Optimize retention (500GB/mo, 90d > 30d) | $2,750/mo | $1,250/mo | 55% |
| Filter container logs (error/warn only) | 30GB/day | 12GB/day | 60% |
| Commitment tier (150GB/day) | $11,250/mo | $8,820/mo | 22% |

---

## AKS (Kubernetes) cost optimization

### Key cost drivers

1. Node pool sizing (VM SKUs) - largest cost component
2. Node count and autoscaling configuration
3. Storage (Premium vs Standard disks)
4. Networking (load balancers, public IPs, egress)
5. Add-ons (monitoring, security)

### Optimization strategies

**Pod rightsizing:**
- Set appropriate resource requests and limits on all pods
- Methodology: Monitor actual usage 2-4 weeks > Set requests at P80 > Set limits at
  P95 or 2x requests > Review quarterly
- Use Vertical Pod Autoscaler (VPA) for automated recommendations
- **Savings: 20-40%**

**Node pool rightsizing:**
- Match node sizes to pod requirements
- Use multiple node pools for different workload types
- Enable cluster autoscaler for dynamic scaling
- **Savings: 15-30%**

**Spot node pools:**
- 60-90% discount on node compute costs
- Use taints and tolerations to place only fault-tolerant, stateless pods on spot nodes
- Start with 20-30% spot allocation, increase based on stability
- **Savings: 60-90%**

**Horizontal Pod Autoscaler (HPA):**
- Scale pods based on CPU/memory or custom metrics
- Reduce pod count during low traffic, scale during peaks
- **Savings: 20-50%**

### Policy-based governance with Kyverno

Kyverno policies automate cost governance in AKS clusters:
- Enforce node affinity rules (ensure workloads land on correct, cost-optimized pools)
- Prevent expensive workloads on general-purpose nodes
- Enable workload isolation for chargeback/showback
- Require resource requests/limits on all pods

---

## Cost allocation on Azure

### Billing scope hierarchy

```
Billing Account
 > Management Group (org-level governance)
    > Subscription (primary isolation boundary)
       > Resource Group (workload grouping)
          > Resource (individual service)
```

**Allocation strategy:**
- Use Management Groups for policy inheritance and org-level cost views
- Use Subscriptions as the primary cost allocation boundary (equivalent to AWS accounts)
- Use Resource Groups to group resources by workload or team within a subscription
- Use Tags for cross-cutting dimensions (Environment, CostCenter, Project)

### Azure-specific tagging considerations

**Key difference from AWS:** Azure supports tag inheritance policies through Azure Policy.
Resources can inherit tags from their resource group or subscription automatically. This
simplifies governance for teams that organize resources by resource group.

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

## Governance tools

### Azure Policy for FinOps

Azure Policy enforces organizational standards across subscriptions. Key FinOps policies:

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

**Assign policies at Management Group scope** for org-wide enforcement.
Use remediation tasks to apply `modify` policies to existing resources retroactively.

### Azure Budgets and Alerts

Configure at minimum:
- Subscription-level monthly budget with 80% and 100% actual cost alerts
- Forecasted cost alert at 100% (triggers before the budget is exceeded)
- Resource group level budgets for high-spend workloads

**Alert recipients:** Both the FinOps practitioner and the engineering team lead.
FinOps-only alerts create a bottleneck; engineering-only alerts lack financial context.

Use Action Groups for automated responses (Logic Apps, Azure Functions, webhooks).

### Environment definitions

Formalize environment tiers with different governance levels:

| Environment | Allowed SKUs | Schedule | Commitment eligible | Backup |
|---|---|---|---|---|
| Sandbox | B-series only | Auto-delete after 7 days | No | No |
| Dev | B-series, small D/E | Business hours only | No | No |
| Pre-Production | Match prod families, smaller | Business hours only | No | Optional |
| Production | Any approved | 24/7 | Yes (after 90-day stability) | Yes |

**Principle: Shut down waste before committing to anything.** Reduce baseline cost first,
then layer commitments (RIs, Savings Plans) on top of the optimized baseline.

---

## Azure-specific quick wins

Ordered by priority: highest savings + lowest risk first.

| # | Action | Typical savings | Risk | Effort |
|---|---|---|---|---|
| 1 | Enable Azure Hybrid Benefit on eligible VMs | Up to 40-55% on license cost | None | Very Low |
| 2 | Schedule dev/test VM auto-shutdown (business hours) | 60-70% of VM cost | Low | Low |
| 3 | Delete unattached managed disks | 100% of disk cost | None | Low |
| 4 | Remove unassociated public IP addresses | 100% of IP cost | None | Low |
| 5 | Shut down idle VMs (CPU <5% for 14+ days) | 100% of VM compute cost | Low | Low |
| 6 | Move cold blob storage to Cool or Archive tier | 50-90% storage cost | Low | Low |
| 7 | Set Log Analytics daily cap + optimize retention | 30-60% monitoring cost | Low | Low |
| 8 | Use ephemeral OS disks for stateless workloads | 100% of OS disk cost | Low | Low |
| 9 | Auto-pause dev SQL databases (Serverless tier) | 70-90% during idle | Low | Low |
| 10 | Use B-series for dev/test web servers | 15-55% vs D-series | Low | Medium |
| 11 | Right-size over-provisioned VMs (Azure Advisor) | 20-50% VM cost | Medium | Medium |
| 12 | Convert to Reserved Instances for stable workloads | 30-72% compute cost | Medium | Medium |
| 13 | Archive backups >90 days in Recovery Services Vault | 95% on old backups | Low | Medium |
| 14 | Filter Container Insights to error/warning only | 40-60% Log Analytics | Low | Medium |

---

## Case study: 2-tier web app optimization

**Baseline:** 12 VMs across prod/pre-prod/dev (D4_v5 Windows web + E8_v5 Linux DB),
all running 24/7. Monthly cost: ~5,071 EUR. Non-prod CPU utilization: 3-5%.

**Optimization waterfall (compute only):**

```
Current compute       3,747 EUR/mo
 - AHB               - 675  --> 3,073  (enable today, no downtime)
 - Start/Stop        -1,440 --> 1,633  (non-prod business hours only)
 - Rightsize Web     -  97  --> 1,536  (D4_v5 > B2ms for non-prod)
 - Rightsize DB      - 331  --> 1,205  (E8_v5 > E2_v5 for non-prod)
                               ------
Optimized compute     1,205 EUR/mo  (-67.9% compute reduction)
Annual savings       30,515 EUR/year
```

**Implementation order matters:**
1. **Week 1:** AHB - zero risk, zero downtime, immediate savings
2. **Week 1-2:** Start/Stop automation - low risk, high impact
3. **Week 3:** Rightsize non-prod web tier (stateless, easy rollback)
4. **Week 4-6:** Rightsize non-prod DB tier (stateful, validate carefully per VM)

**Key lesson:** 44% of Windows VM cost was license premium the company was double-paying.
AHB alone saved 675 EUR/month with a single CLI command per VM.

---

## Key resources

- **Microsoft FinOps Toolkit:** https://github.com/microsoft/finops-toolkit
- **Azure FinOps Guide (community):** https://github.com/dolevshor/azure-finops-guide
- **Azure Cost Management docs:** https://docs.microsoft.com/azure/cost-management-billing/
- **FinOps Foundation Azure guidance:** https://www.finops.org/wg/azure/
- **Azure Retail Prices API:** https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
