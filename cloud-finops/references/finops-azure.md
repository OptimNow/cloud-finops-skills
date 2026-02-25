# FinOps on Azure

> **Status:** Placeholder. This file should be populated from the content in
> `~/github/azure-finops-master`.
>
> **To populate this file:**
> ```bash
> # From inside cloud-finops-skill/
> # Review your local Azure repo and copy relevant content sections here
> # Suggested source files from azure-finops-master to draw from:
> # - Any modules covering Azure Cost Management + Billing
> # - Reservations and Savings Plans content
> # - Azure-specific tagging (Azure Policy, resource groups, management groups)
> # - Azure Advisor cost recommendations
> # - FinOps Toolkit / FinOps Hubs content
> # - Azure Hybrid Benefit guidance
> ```
>
> **Structure to follow** (mirrors finops-aws.md for consistency):
> 1. Azure cost data foundation (Cost Management exports, billing scopes)
> 2. Commitment discounts (Reservations vs Azure Savings Plans)
> 3. Compute rightsizing (Azure Advisor, Compute Optimizer equivalent)
> 4. Cost allocation (management groups, subscriptions, resource groups, tags)
> 5. Governance tools (Azure Policy, Budgets, Cost Alerts)
> 6. Azure-specific quick wins
>
> The sections below are a starting skeleton. Replace and expand with content
> from your Azure course material.

---

## Azure cost data foundation

### Azure Cost Management exports

Azure Cost Management is the native cost visibility tool for Azure. For serious FinOps
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

### FinOps Toolkit and FinOps Hubs

Microsoft's open-source FinOps Toolkit provides pre-built solutions for Azure FinOps
implementation, including Power BI report templates, Azure Workbooks, and FinOps Hubs
for automated cost data ingestion.

**FinOps Hubs** normalize cost exports into a consistent schema and feed Power BI reports.
Recommended for organizations that want production-grade reporting without building custom
data pipelines.

Repository: https://github.com/microsoft/finops-toolkit

---

## Commitment discounts

### Azure Reservations vs Azure Savings Plans

> **Populate from azure-finops-master:** Add specific discount percentages, term options
> (1-year vs 3-year), scope options (shared vs single subscription), and exchange/refund policies.

| Dimension | Azure Reservations | Azure Savings Plans for Compute |
|---|---|---|
| Flexibility | Low - locked to specific VM family/region | High - applies across VM families and regions |
| Discount depth | Higher (up to 72% for some VM families) | Lower but broader coverage |
| Coverage scope | Specific resource type | Compute (VMs, Dedicated Hosts) |
| Best for | Stable workloads with known VM types | Variable workloads, mixed VM families |

**Azure Hybrid Benefit (AHB):**
Organizations with existing Windows Server or SQL Server licenses can apply them to Azure
VMs, reducing costs by up to 40–85% on license fees. Often overlooked in Azure cost reviews.

> **Add from azure-finops-master:** AHB eligibility, SQL Managed Instance benefits,
> the AHB Workbook from Microsoft FinOps Toolkit for compliance tracking.

---

## Compute rightsizing

### Azure Advisor

Azure Advisor provides cost optimization recommendations including VM rightsizing based on
CPU and memory utilization data from Azure Monitor.

**Rightsizing with Azure Advisor:**
- Access via Azure Portal → Advisor → Cost tab
- Recommendations based on 7–30 days of utilization data (configurable)
- Shows estimated monthly savings per recommendation
- Can be exported to CSV for bulk review

> **Add from azure-finops-master:** Advisor recommendation categories, how to act on
> bulk recommendations programmatically, integration with Azure Policy for enforcement.

---

## Cost allocation on Azure

### Billing scope hierarchy

Azure cost allocation uses a hierarchy of billing scopes:

```
Billing Account
└── Management Group (org-level governance)
    └── Subscription (primary isolation boundary)
        └── Resource Group (workload grouping)
            └── Resource (individual service)
```

**Allocation strategy:**
- Use Management Groups for policy inheritance and org-level cost views
- Use Subscriptions as the primary cost allocation boundary (equivalent to AWS accounts)
- Use Resource Groups to group resources by workload or team within a subscription
- Use Tags for cross-cutting dimensions (Environment, CostCenter, Project)

### Azure-specific tagging considerations

> **Add from azure-finops-master:** Azure Policy deny effects for missing tags,
> tag inheritance from resource groups, which resource types do not support tags,
> Azure Cost Management tag filters.

**Key difference from AWS:** Azure supports tag inheritance policies through Azure Policy -
resources can inherit tags from their resource group automatically. This simplifies
governance for teams that organize resources by resource group.

---

## Governance tools

### Azure Policy

Azure Policy enforces organizational standards across subscriptions. For FinOps, use it to:
- Require mandatory tags on all resource creation (`deny` effect)
- Audit existing resources for tag compliance (`audit` effect)
- Automatically apply tags from resource groups (`modify` effect)
- Restrict deployments to approved regions (cost control + data residency)
- Restrict approved VM SKUs (prevent accidental deployment of expensive GPU VMs)

> **Add from azure-finops-master:** Example policy definitions for tag enforcement,
> how to assign policies at Management Group scope, remediation task patterns.

### Azure Budgets and Alerts

Configure at minimum:
- Subscription-level monthly budget with 80% and 100% actual cost alerts
- Forecasted cost alert at 100% (triggers before the budget is exceeded)
- Resource group level budgets for high-spend workloads

> **Add from azure-finops-master:** Budget scope options, action groups for automated
> response, integration with Azure Logic Apps for custom alerting workflows.

---

## Azure-specific quick wins

> **Populate from azure-finops-master with specific actions, typical savings ranges,
> and implementation steps. Suggested actions to cover:**

| Action | Typical savings | Risk | Effort |
|---|---|---|---|
| Delete unattached managed disks | 100% of disk cost | None | Low |
| Remove unassociated public IP addresses | Small but guaranteed | None | Low |
| Shut down idle VMs (CPU <5% for 14 days) | 100% of VM compute cost | Low | Low |
| Schedule dev/test VM auto-shutdown | 60–70% of VM cost | Low | Low |
| Move cold blob storage to Cool or Archive tier | 50–90% storage cost | Low | Low |
| Enable Azure Hybrid Benefit on eligible VMs | Up to 40% license cost | None | Low |
| Right-size over-provisioned VMs (Azure Advisor) | 20–50% VM cost | Medium | Medium |
| Convert to Reserved Instances for stable workloads | 30–72% compute cost | Medium | Medium |

---

## Key resources

- **Microsoft FinOps Toolkit:** https://github.com/microsoft/finops-toolkit
- **Azure FinOps Guide (community):** https://github.com/dolevshor/azure-finops-guide
- **Azure Cost Management docs:** https://docs.microsoft.com/azure/cost-management-billing/
- **FinOps Foundation Azure guidance:** https://www.finops.org/wg/azure/
