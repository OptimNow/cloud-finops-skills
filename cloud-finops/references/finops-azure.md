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

## Azure Optimization Patterns

> 48 cloud inefficiency patterns covering compute, storage, databases, networking,
> and other Azure services. Use to diagnose waste, validate architecture, or build
> optimization roadmaps. Source: PointFive Cloud Efficiency Hub.

---

### Compute Optimization Patterns (13)

**Underutilized Azure Reserved Instance Due To Workload Drift**
Service: Azure Reservations | Type: Commitment Misalignment

As workloads evolve, Azure Reserved Instances (RIs) may no longer align with actual usage  - due to refactoring, region changes, autoscaling, or instance-type drift. When this happens, the committed usage goes unused, while new workloads run on non-covered SKUs, resulting in both underutilized reservations and full-price on-demand charges elsewhere.

- Evaluate whether any existing workloads could be migrated to match the reservation scope
- For new workloads, consider provisioning on RI-covered instance types when technically viable
- Where appropriate, exchange the reservation for a more relevant SKU

**Oversized Hosting Plan For Azure Functions**
Service: Inefficiency Type | Type: Explanation

Teams often choose the Premium or App Service Plan for Azure Functions to avoid cold start delays or enable VNET connectivity, especially early in a project when performance concerns dominate. However, these decisions are rarely revisited -even as usage patterns change.

- Move low-usage or non-critical Function Apps to the Consumption Plan
- Pilot plan downgrades in non-production or latency-tolerant environments
- Use cost modeling tools to estimate savings from switching to Consumption Plan

**Missing Scheduled Shutdown For Non Production Azure Virtual Machines**
Service: Azure Virtual Machines | Type: Inefficient Configuration

Non-production Azure VMs are frequently left running during off-hours despite being used only during business hours. When these instances remain active overnight or on weekends, they generate unnecessary compute spend.

- Enable Azure’s built-in auto-shutdown setting for applicable non-prod VMs
- Alternatively, configure shutdown/start schedules using Azure Automation or Logic Apps
- Preserve state using managed disks, snapshots, or generalized images

**Orphaned And Overprovisioned Resources In Aks Clusters**
Service: Azure AKS | Type: Inefficient Configuration

Clusters often accumulate unused components when applications are terminated or environments are cloned. These include PVCs backed by Managed Disks, Services that still front Azure Load Balancers, and test namespaces that are no longer maintained.

- Delete unused PVCs to release backing Managed Disks
- Clean up Services that are no longer in use to avoid unnecessary load balancer charges
- Scale down underutilized node pools

**Orphaned Kubernetes Resources 230Dd**
Service: Azure AKS | Type: Orphaned Resource

Kubernetes environments often accumulate unused resources over time as applications evolve. Common examples include Persistent Volume Claims (PVCs) backed by Azure Disks, Services that trigger load balancer provisioning, or stale ConfigMaps and Secrets.

- Before deletion, verify resources are truly orphaned
- Delete orphaned PVCs to release Azure Managed Disks
- Remove Services that no longer front active workloads to deallocate Load Balancers and public IPs

**Outdated Azure App Service Plan**
Service: Azure App Service | Type: Outdated Resource

Applications running on App Service V2 plans may incur higher operational costs and degraded performance compared to V3 plans. V2 uses older hardware generations that lack access to platform-level enhancements introduced in V3, including improved cold start times, faster scaling, and enhanced networking options.

- Evaluate workload compatibility with V3-based plans (e.g., Premium v3 or Isolated v2)
- Plan a phased migration of applications from V2 to V3 to improve performance and reduce cost per resource unit
- Update infrastructure-as-code templates and provisioning defaults to prefer V3-based plans

**Outdated Virtual Machine Version In Azure**
Service: Azure Virtual Machines | Type: Outdated Resource

Many organizations choose a VM SKU and version (e.g., `D4s_v3`) during the initial planning phase of a project, often based on availability, compatibility, or early cost estimates. Over time, Microsoft releases newer hardware generations (e.g., `D4s_v4`, `D4s_v5`) that offer equivalent or better performance at the same or reduced cost.

- Evaluate alternative VM versions (e.g., v4 or v5) within the same family to identify better cost/performance options
- Plan and schedule VM resizing during maintenance windows to avoid unplanned downtime
- Coordinate with application owners to validate compatibility and risk tolerance

**Underutilized Azure Virtual Machine**
Service: Azure Virtual Machines | Type: Overprovisioned Resource

Azure VMs are frequently provisioned with more vCPU and memory than needed, often based on template defaults or peak demand assumptions. When a VM operates well below its capacity for an extended period, it presents an opportunity to reduce costs through rightsizing.

- Analyze average CPU and memory utilization of running VM’s to determine
- Review whether application requirements justify the current VM size
- Evaluate if the workload would perform similarly on a lower SKU within the same VM series

**Inefficient Use Of Photon Engine In Azure Databricks**
Service: Databricks | Type: Suboptimal Configuration

Photon is optimized for SQL workloads, delivering significant speedups through vectorized execution and native C++ performance. However, Photon only accelerates workloads that use compatible operations and data patterns.

- Ensure that Photon is only enabled for workloads structured to benefit from vectorized execution
- Refactor SQL logic and data models to align with Photon-optimized patterns (e.g., filter pushdowns, supported UDFs)
- Use built-in tools such as query plans and job profiles to verify Photon execution

**Missing Shared Scope Configuration For Azure Reservations**
Service: Azure Reservations | Type: Suboptimal Configuration

When reservations are scoped only to a single subscription, any unused capacity cannot be applied to matching resources in other subscriptions within the same tenant. This leads to underutilization of the committed reservation and continued on-demand charges in other parts of the organization.

- Change reservation scope from *Single* to *Shared* in the Azure Portal or via API
- Reevaluate periodically to ensure the scope aligns with current organizational structure and usage distribution

**Suboptimal Architecture Selection For Azure Virtual Machines**
Service: Azure Virtual Machines | Type: Suboptimal Pricing Model

Azure provides VM families across three major CPU architectures, but default provisioning often leans toward Intel-based SKUs due to inertia or pre-configured templates. AMD and ARM alternatives offer substantial cost savings; ARM in particular can be 30–50% cheaper for general-purpose workloads.

- Assess workload compatibility with ARM or AMD architectures
- Propose migration to ARM-based SKUs for supported workloads to reduce compute costs
- Use AMD-based instances as an intermediate option when ARM compatibility is not feasible

**Idle Azure App Service Plan Without Deployed Applications**
Service: Azure App Service | Type: Unused Resource

App Service Plans continue to incur charges even when no applications are deployed. This can occur when applications are deleted, migrated, or retired, but the associated App Service Plan remains active.

- Decommission App Service Plans with no active applications unless a future use case is explicitly confirmed
- In cases with low utilization, consider consolidating multiple lightly used plans into a single plan to reduce spend
- Establish governance practices to routinely identify and remove orphaned plans after application lifecycle events

**Inactive And Stopped Vm**
Service: Azure Virtual Machines | Type: Unused Resource

This inefficiency arises when a virtual machine is left in a stopped (deallocated) state for an extended period but continues to incur costs through attached storage and associated resources. These idle VMs are often remnants of retired workloads, temporary environments, or paused projects that were never fully cleaned up.

- Identify virtual machines that have remained in a stopped (deallocated) state for the entire lookback period
- Review whether any activity has occurred from the associated managed disks, network interfaces, or backup processes
- Evaluate whether the VM is part of a dev/test or legacy environment with no recent usage

---

### Storage Optimization Patterns (16)

**Archival Blob Container Storing Objects In Non Archival Tiers**
Service: Azure Blob Storage | Type: Inefficient Configuration

This inefficiency occurs when a blob container intended for long-term or infrequently accessed data continues to store objects in higher-cost tiers like Hot or Cool, instead of using the Archive tier. This often happens when containers are created without lifecycle policies or default tier settings.

- Identify blob containers with large volumes of data stored in the Hot or Cool tier
- Evaluate access patterns to confirm whether the data is rarely or never read
- Review whether the container’s data retention requirements align with archival use cases

**High Transaction Cost Due To Misaligned Tier In Azure Blob Storage**
Service: Azure Blob Storage | Type: Inefficient Configuration

Azure Blob Storage tiers are designed to optimize cost based on access frequency. However, when frequently accessed data is stored in the Cool or Archive tiers -either due to misconfiguration, default settings, or cost-only optimization -transaction costs can spike.

- Move frequently accessed data to the Hot tier, either manually or via lifecycle management policies
- Evaluate default tiering settings on upload processes to prevent misplacement of active data
- Incorporate access pattern analysis into storage tier selection decisions

**High Transaction Cost Due To Misaligned Tier In Azure Files**
Service: Azure Files | Type: Inefficient Configuration

Azure Files Standard tier is cost-effective for low-traffic scenarios but imposes per-operation charges that grow rapidly with frequent access. In contrast, Premium tier provides consistent IOPS and throughput without additional transaction charges.

- Evaluate cost-performance tradeoffs between Standard and Premium tiers
- If justified, migrate data to a new Azure Files Premium account (required for tier change)
- Use performance metrics and transaction volume to guide future provisioning decisions

**Inactive Blobs In Storage Account**
Service: Azure Blob Storage | Type: Inefficient Configuration

Storage accounts can accumulate blob data that is no longer actively accessed -such as legacy logs, expired backups, outdated exports, or orphaned files. When these blobs remain in the Hot tier, they continue to incur the highest storage cost, even if they have not been read or modified for an extended period.

- Identify storage accounts with large amounts of data in the Hot tier
- Analyze blob-level access patterns using logs or metrics to confirm that data has not been read or written over a defined lookback period
- Determine whether the data is still relevant to any active workload, process, or compliance requirement

**Sftp Feature Enabled On Azure Storage Account Without Usage**
Service: Azure Storage Account | Type: Inefficient Configuration

Azure users may enable the SFTP feature on Storage Accounts during migration tests, integration scenarios, or experimentation. However, if left enabled after initial use, the feature continues to generate flat hourly charges  - even when no SFTP traffic occurs.

- Disable the SFTP feature on any Storage Account where it is no longer needed
- Coordinate with owners to confirm that alternate access methods (e.g., HTTPS, SDK) are sufficient
- Consider including SFTP enablement in governance reviews to catch idle services before they accumulate charges

**Missing Performance Plus On Eligible Managed Disks**
Service: Azure Managed Disks | Type: Misconfiguration

For Premium SSD and Standard SSD disks 513 GiB or larger, Azure now offers the option to enable Performance Plus  - unlocking higher IOPS and MBps at no extra cost. Many environments that previously required custom performance settings continue to pay for additional throughput unnecessarily.

- Enable Performance Plus on all eligible disks using Azure CLI, API, or portal
- Decommission paid performance tiers or custom throughput settings where Performance Plus provides equivalent capability
- Incorporate Performance Plus enablement into provisioning templates for large disks going forward

**Outdated And Expensive Premium Ssd Disk**
Service: Azure Managed Disks | Type: Modernization

Workloads using legacy Premium SSD managed disks may be eligible for migration to Premium SSD v2, which delivers equivalent or improved performance characteristics at a lower cost. Premium SSD v2 decouples disk size from performance metrics like IOPS and throughput, enabling more granular cost optimization.

- Identify Premium SSD managed disks provisioned using the original Premium SSD offering (not v2)
- Review disk IOPS, throughput, and sizing requirements to ensure compatibility with Premium SSD v2 capabilities
- Analyze whether the current SKU size (e.g., P30, P40) exceeds actual capacity and performance needs

**Outdated And Expensive Standard Ssd Disk**
Service: Azure Managed Disks | Type: Modernization

Standard SSD disks can often be replaced with Premium SSD v2 disks, offering enhanced IOPS, throughput, and durability at competitive or lower pricing. For workloads that require moderate to high performance but are currently constrained by Standard SSD capabilities, migrating to Premium SSD v2 improves both performance and cost efficiency without significant operational overhead.

- Identify Managed Disks using the Standard SSD offering that are eligible for migration to Premium SSD v2
- Review workload performance requirements to confirm suitability for Premium SSD v2 characteristics
- Verify regional availability of Premium SSD v2 before planning migration

**Excessive Retention Of Audit Logs**
Service: Azure Blob Storage | Type: Over-Retention of Data

Audit logs are often retained longer than necessary, especially in environments where the logging destination is not carefully selected. Projects that initially route SQL Audit Logs or other high-volume sources to LAW or Azure Storage may forget to revisit their retention strategy.

- Azure Storage Lifecycle Management Overview

**Overprovisioned Managed Disk For Vm Limits**
Service: Azure Managed Disks | Type: Overprovisioned Resource

Each Azure VM size has a defined limit for total disk IOPS and throughput. When high-performance disks (e.g., Premium SSDs with high IOPS capacity) are attached to low-tier VMs, the disk’s performance capabilities may exceed what the VM can consume.

- Resize disks to match the performance envelope of the associated VM
- Downgrade to lower disk tiers (e.g., Premium SSD → Standard SSD) when full performance is not needed
- Establish guardrails to ensure disk and VM configurations are aligned during provisioning and resizing events

**Long Retained Azure Snapshot**
Service: Azure Snapshots | Type: Retained Unused Resource

Snapshots are often created for short-term protection before changes to a VM or disk, but many remain in the environment far beyond their intended lifespan. Over time, this leads to an accumulation of snapshots that are no longer associated with any active resource or retained for operational need.Since Azure does not enforce automatic expiration or lifecycle policies for snapshots, they can persist indefinitely and continue to incur monthly storage charges.

- Manually review long-retained snapshots with application or infrastructure owners
- Delete snapshots no longer needed for recovery, rollback, or compliance retention
- Adopt tagging standards to track purpose, owner, and expected retention period at time of snapshot creation

**Inactive And Detached Managed Disk**
Service: Azure Managed Disks | Type: Unused Resource

Managed Disks frequently remain detached after Azure virtual machines are deleted, reimaged, or reconfigured. Some may be intentionally retained for reattachment, backup, or migration purposes, but many persist unintentionally due to the lack of automated cleanup processes.

- Identify Managed Disks that are in an unattached state (not linked to any VM)
- Review metrics or activity logs to determine whether the disk has seen any read or write operations during the lookback period
- Check whether the disk is intentionally retained for recovery, migration, or reattachment

**Inactive Files In Storage Account**
Service: Azure Blob Storage | Type: Unused Resource

Files that show no read or write activity over an extended period often indicate redundant or abandoned data. Keeping inactive files in higher-cost storage classes unnecessarily increases monthly spend.

- Identify storage accounts or containers containing blobs with no reads or modifications over a defined lookback period
- Analyze blob access logs and object metadata to validate inactivity
- Review creation timestamps, tags, and business ownership metadata to assess ongoing relevance

**Inactive Tables In Storage Account**
Service: Azure Table Storage | Type: Unused Resource

Tables with no read or write activity often represent deprecated applications, obsolete telemetry, or abandoned development artifacts. Retaining inactive tables increases storage costs and operational complexity.

- Identify Azure Table Storage tables with no read or write operations over a defined lookback period
- Review table creation dates, metadata, and ownership tags to assess relevance and intended retention
- Check for compliance, legal hold, or audit requirements before initiating deletions or exports

**Managed Disk Attached To A Deallocated Vm**
Service: Azure Managed Disks | Type: Unused Resource

This inefficiency occurs when a VM is deallocated but its attached managed disks are still active and incurring storage charges. While compute billing stops for deallocated VMs, the disks remain provisioned and billable.

- Identify managed disks attached to deallocated VMs during the defined lookback period
- Review disk activity to confirm no read/write operations occurred while the VM was deallocated
- Evaluate whether the disk is still needed for backup, migration, or future reactivation

**Managed Disk Attached To A Stopped Vm**
Service: Azure Managed Disks | Type: Unused Resource

Disks attached to VMs that have been stopped for an extended period, particularly when showing no read or write activity, may indicate abandoned infrastructure or obsolete resources. Retaining these disks without validation leads to unnecessary monthly storage costs.

- Identify Managed Disks attached to virtual machines that have remained in a stopped state over a representative time window
- Analyze disk activity metrics to detect absence of read/write operations during the lookback period
- Review VM metadata, ownership tags, and decommissioning records to assess whether the disk is still required

---

### Databases Optimization Patterns (8)

**Business Critical Tier On Non Production Sql Instance**
Service: Azure SQL | Type: Inefficient Configuration

Non-production environments such as development, testing, or staging often do not require the high availability, failover capabilities, and premium storage performance offered by the Business Critical tier. Running these workloads on Business Critical unnecessarily inflates costs.

- Migrate non-production SQL instances from the Business Critical tier to a lower-cost alternative, such as General Purpose.
- Use downtime windows or database copy strategies to minimize risk during tier transitions, depending on instance size and availability requirements.
- Monitor performance after migration to ensure the workload remains stable and meets operational needs.

**Unnecessary Use Of Ra Grs For Azure Sql Backup Storage**
Service: Azure SQL | Type: Inefficient Configuration

Azure SQL databases often use the default backup configuration, which stores backups in RA-GRS storage to ensure geo-redundancy. While suitable for high-availability production systems, this level of resilience may be unnecessary for development, testing, or lower-impact workloads.

- For non-critical or non-regulated workloads, change the backup redundancy setting to LRS (or ZRS where supported)
- Document any exceptions where RA-GRS must be retained for compliance
- Incorporate backup configuration reviews into provisioning and governance processes

**Infrequently Accessed Data Stored In Azure Cosmos Db**
Service: Azure Cosmos DB | Type: Inefficient Storage Tiering

Azure Cosmos DB is optimized for low-latency, globally distributed workloads -not long-term storage of infrequently accessed data. Yet in many environments, cold data such as logs, telemetry, or historical records is retained in Cosmos DB due to a lack of lifecycle management.

- Export infrequently accessed data to lower-cost storage services:
- Use Blob Storage Cool for rarely accessed but readily retrievable data
- Use Blob Storage Archive for long-term retention with delayed retrieval

**Overprovisioned Azure Database For Postgresql Flexible Server**
Service: Azure Database for PostgreSQL – Flexible Server | Type: Overprovisioned Resource

Azure Database for PostgreSQL – Flexible Server often defaults to general-purpose D-series VMs, which may be oversized for many production or development workloads. PostgreSQL typically does not require a high sustained high CPU, making it well-suited to memory-optimized (E-series) or burstable (B-series) instances.

- Resize the PostgreSQL Flexible Server to a smaller or more suitable VM family based on actual workload behavior
- For low-CPU workloads, consider B-series (burstable) or E-series (memory-optimized) configurations
- Review usage patterns quarterly to ensure the selected SKU remains aligned with performance needs

**Overprovisioned Compute Tier In Azure Sql Database**
Service: Azure SQL | Type: Overprovisioned Resource

Azure SQL Database resources are frequently overprovisioned due to default configurations, conservative sizing, or legacy requirements that no longer apply. This inefficiency appears across all deployment models: * Single Databases may be assigned more DTUs or vCores than the workload requires * Elastic Pools may be oversized for the actual demand of pooled databases * Managed Instances are often deployed with excess compute capacity that remains underutilized Because billing is based on provisioned capacity, not actual consumption, organizations incur unnecessary costs when sizing is not aligned with workload behavior.

- Downsize the compute tier (DTUs or vCores) to better match observed usage
- For Elastic Pools, reduce the total eDTUs/vCores and consider consolidating lightly used databases
- For Managed Instances, assess whether the vCore allocation can be reduced or workloads refactored

**Overprovisioned Storage In Azure Sql Elastic Pools Or Managed Instances**
Service: Azure SQL | Type: Overprovisioned Resource

Azure SQL deployments often reserve more storage than needed, either due to default provisioning settings or anticipated future growth. Over time, if actual usage remains low, these oversized allocations generate unnecessary storage costs.

- Where supported, reduce provisioned storage to better align with actual usage
- For Managed Instances, safely execute `DBCC SHRINKFILE` or equivalent operations before resizing
- Incorporate storage reviews into regular database hygiene practices

**Overbilling Due To Tier Switches And Allocation Overlaps In Dtu Model**
Service: Azure SQL | Type: Suboptimal Pricing Model

Workloads that frequently scale up and down within the same day -whether manually, via automation, or platform-managed -can encounter hidden cost amplification under the DTU model. When a database changes tiers (e.g., S7 → S4), Azure treats each tiered segment as a separate allocation and applies full-hour rounding independently.

- Minimize same-day tier switches unless operationally justified
- Schedule up/down-scaling during off-peak windows to reduce risk of overlapping billing
- Move to the vCore or serverless pricing model for more transparent and granular cost control

**Idle Azure Sql Elastic Pool Without Databases**
Service: Azure SQL | Type: Unused Resource

An Azure SQL Elastic Pool continues to incur costs even if it contains no databases. This can occur when databases are deleted, migrated to single-instance configurations, or consolidated elsewhere  - but the pool itself remains provisioned.

- Decommission any Elastic Pool with no active databases unless a valid business case exists for retaining it
- Review infrastructure-as-code templates and automation pipelines to ensure pool cleanup is included in deprovisioning workflows
- Establish periodic audits to catch and remove idle pools across subscriptions and teams

---

### Networking Optimization Patterns (5)

**Suboptimal Load Balancer Rule Configuration In Azure Standard Load Balancer**
Service: Azure Load Balancer | Type: Inefficient Configuration

As organizations migrate from the Basic to the Standard tier of Azure Load Balancer (driven by Microsoft’s retirement of the Basic tier), they may unknowingly inherit cost structures they didn’t previously face. Specifically, each load balancing rule -both inbound and outbound -can contribute to ongoing charges.

- Audit existing Standard Load Balancer rule sets to identify unused entries
- Remove unnecessary inbound and outbound rules, especially in non-production environments
- Avoid blanket rule creation in templated environments unless explicitly required

**Inactive Azure Load Balancer**
Service: Azure Load Balancer | Type: Unused Resource

In dynamic environments  - especially during autoscaling, testing, or infrastructure changes  - it's common for load balancers to remain provisioned after their backend resources have been decommissioned. When this happens, the load balancer continues to incur hourly charges despite serving no functional purpose.

- Delete Azure Load Balancers that have no backend pool members and no observed traffic
- Implement automation or tagging policies to detect and flag inactive networking resources
- Update infrastructure-as-code or deployment scripts to ensure load balancers are removed alongside their dependent compute resources

**Inactive Azure Load Balancer 0Fe41**
Service: Azure Load Balancer | Type: Unused Resource

Standard Load Balancers are frequently provisioned for internal services, internet-facing applications, or testing environments. When a workload is decommissioned or moved, the load balancer may be left behind without any active backend pool or traffic  - but continues to incur hourly charges for each frontend IP configuration.Because Azure does not automatically remove or alert on inactive load balancers, and because they may not show significant outbound traffic, these resources often persist unnoticed.

- Delete load balancers that have no active backend pool and are no longer needed
- Review associated resources (e.g., front-end IP configurations, probes, rules) to ensure they can be safely removed
- Establish tagging or documentation standards to track ownership and intended usage

**Inactive Web Application Firewall Waf**
Service: Azure WAF | Type: Unused Resource

Azure WAF configurations attached to Application Gateways can persist after their backend pool resources have been removed  - often during environment reconfiguration or application decommissioning. In these cases, the WAF is no longer serving any functional purpose but continues to incur fixed hourly costs.

- Delete WAF configurations that are no longer routing traffic or protecting active applications
- Establish periodic audits to flag and review WAFs with empty backend pools
- Use automated checks to detect and alert on WAF deployments with no active use

**Unassigned Public Ip Address**
Service: AWS VPC | Type: Unused Resource

In Azure, it’s common for public IP addresses to be created as part of virtual machine or load balancer configurations. When those resources are deleted or reconfigured, the IP address may remain in the environment unassigned.

- Delete unassigned Standard SKU public IPs that are no longer needed
- If an unassigned IP is intended for future use, consider converting it to Basic (if compatible)
- Incorporate IP resource cleanup into deprovisioning workflows

---

### Other Optimization Patterns (6)

**Transactable Vs Non Transactable Confusion In Azure Marketplace**
Service: Azure Marketplace | Type: Commitment Misalignment

Azure Marketplace offers two types of listings: transactable and non-transactable. Only transactable purchases contribute toward a customer’s MACC commitment.

- Prefer transactable listings in Azure Marketplace whenever MACC utilization is a priority
- Validate SKU eligibility against Microsoft’s Procurement Playbook or MACC eligibility lists
- Standardize sourcing templates and procurement workflows to explicitly document whether the offer contributes to MACC

**Lifecycle Visibility Gaps Inflating Renewal Costs In Azure Marketplace**
Service: Azure Marketplace | Type: Contract Lifecycle Mismanagement

When Marketplace contracts or subscriptions expire or change without visibility, Azure may automatically continue billing at higher on-demand or list prices. These lapses often go unnoticed due to lack of proactive tracking, ownership, or renewal alerts, resulting in substantial cost increases.

- Assign clear ownership of Marketplace contracts across business, finance, or procurement teams
- Set calendar-based and system-based reminders for contract renewals and entitlement expiration
- Regularly reconcile Azure billing data with vendor-provided SLA or entitlement terms

**Inefficient Use Of Azure Pipelines**
Service: Inefficiency Type | Type: Explanation

Teams often overuse Microsoft-hosted agents by running redundant or low-value jobs, failing to configure pipelines efficiently, or neglecting to use self-hosted agents for steady workloads. These inefficiencies result in unnecessary cost and delivery friction, especially when pipelines create queues due to limited agent availability.

- Audit and streamline pipelines to remove redundant or unnecessary stages
- Use conditional logic to limit execution of non-critical pipelines
- Prioritize agent capacity for pipelines supporting core or production workloads

**Overly Frequent Querying In Azure Monitor Alerts**
Service: Inefficiency Type | Type: Inefficient Configuration

While high-frequency alerting is sometimes justified for production SLAs, it's often overused across non-critical alerts or replicated blindly across environments. Projects with multiple environments (e.g., dev, QA, staging, prod) often duplicate alert rules without adjusting for business impact, which can lead to alert sprawl and inflated monitoring costs.

- Test changes gradually. Start with non-production environments and non-critical alerts

**Inefficient Private Link Routing To Azure Databricks**
Service: Azure Databricks | Type: Misconfiguration

In Azure Databricks environments that rely on Private Link for secure networking, it’s common to route traffic through multi-tiered network architectures. This often includes multiple VNets, Private Link endpoints, or peered subscriptions between data sources (e.g., ADLS) and the Databricks compute plane.

- Simplify routing by colocating Databricks and storage in the same region and VNet when possible
- Eliminate redundant Private Link endpoints that add no security or compliance value
- Use direct peering or shared services models to reduce network traversal

**Suboptimal Table Plan Selection In Log Analytics**
Service: Inefficiency Type | Type: Suboptimal Pricing Model

By default, all Log Analytics tables are created under the Analytics plan, which is optimized for high-performance querying and interactive analysis. However, not all telemetry requires real-time access or frequent querying.

- Assign the Basic plan to tables that are retained for audit, archival, or compliance purposes
- Split high-volume ingestion sources into separate tables based on access needs
- Reconfigure ingestion routes to direct non-essential logs to lower-cost tables

---

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io)  - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
