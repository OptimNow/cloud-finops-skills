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

**FOCUS export support:** As of March 2026, Azure supports FOCUS v1.2 exports, providing
standardised billing data that can be normalised alongside other cloud providers. Configure
FOCUS exports alongside traditional Cost Management exports for multi-cloud environments.

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
data pipelines. FinOps Hubs support FOCUS v1.2 format as of March 2026, enabling
standardised multi-cloud cost reporting.

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

### Compute commitment instruments

Azure provides four distinct instruments for reducing compute costs, plus Azure Hybrid
Benefit which acts as a licensing overlay. As with AWS, these instruments are designed
to be layered, not chosen in isolation.

**Instrument comparison:**

| Instrument | Discount depth | Flexibility | Commitment type | Term | Covers |
|---|---|---|---|---|---|
| Azure Reservation | Up to 72% | Lowest - locked to VM family, region, size | Capacity-based (specific SKU) | 1yr or 3yr | VMs, Dedicated Hosts, App Service (Isolated), specific services |
| Azure Savings Plan for Compute | Up to 65% | High - any VM family, region, size | Spend-based ($/hr) | 1yr or 3yr | VMs, Dedicated Hosts, Container Instances, App Service (Premium v3 / Isolated v2) |
| Azure Hybrid Benefit (AHB) | Up to 40% (Windows), 55% (SQL) | Highest - no commitment, no lock-in | Licensing overlay | None | VMs, SQL Database, SQL MI, Red Hat/SUSE Linux |
| Spot Virtual Machines | Up to 90% | Variable - can be evicted with 30s notice | None (market-priced) | None | VMs, VMSS, AKS node pools |

**Critical distinctions:**

1. **Azure Hybrid Benefit is not a commitment - it is free money.** If you have Windows
   Server or SQL Server licenses with Software Assurance, AHB eliminates the license
   component from VM pricing. No contract, no lock-in, no restart needed. This should
   be enabled on all eligible VMs before any other commitment decision. Windows licence
   costs can account for 44% of a Windows VM price (e.g. D4_v5 Windows at ~0.35/hr =
   ~0.19 compute + ~0.15 licence). Use the AHB Workbook from FinOps Toolkit for
   compliance tracking across the fleet.

2. **Savings Plans for Compute cover more than VMs.** Unlike Reservations (which are
   resource-specific), Compute Savings Plans also cover Container Instances and App
   Service Premium v3 / Isolated v2. If you run a mix of VMs, containers, and App
   Service, a Compute Savings Plan is the only instrument that covers all three.

3. **Reservations offer deeper discounts but less flexibility.** A Reservation locks to
   a specific VM family and region. If you change instance family or region mid-term, the
   Reservation does not follow. A Savings Plan is spend-based and applies wherever it
   finds eligible usage - but the discount is ~7% shallower than a Reservation.

4. **Azure allows Reservation exchanges and refunds - but with limits.** You can exchange
   a Reservation for a different SKU (same or higher value) or request a pro-rated refund
   up to $50,000 per rolling 12 months. This is significantly more liquidity than AWS
   offers (where Savings Plans cannot be modified and Standard RIs can only be sold on
   the marketplace). However, Microsoft has been tightening these policies - verify
   current exchange and refund terms before relying on them for liquidity.

5. **Savings Plans cannot be exchanged, cancelled, or refunded** once purchased. The
   commitment runs for the full term. This makes phased purchasing and portfolio
   diversification critical for Savings Plans (see "Commitment portfolio liquidity" below).

6. **Spot is not a commitment** - it is a market mechanism with a 30-second eviction
   notice and no SLA. It belongs in the compute cost strategy but should not be compared
   directly against commitment instruments.

### Compute commitment decision tree

```
START: What Azure compute service runs the workload?
│
├── Virtual Machines (including VMSS)
│   │
│   ├── Does the VM run Windows Server or SQL Server with SA licenses?
│   │   └── YES → Enable Azure Hybrid Benefit immediately (up to 40-55%
│   │             savings, no commitment, no restart). Then continue below
│   │             for additional commitment discounts on top of AHB.
│   │
│   ├── Is the workload fault-tolerant and interruptible?
│   │   ├── YES → Use Spot VMs (up to 90% discount)
│   │   │         - Start with 20-30% Spot allocation in non-production
│   │   │         - Use VMSS with Spot priority for auto-scaling pools
│   │   │         - Implement eviction handling (30-second notice)
│   │   │         - Good for: batch, dev/test, CI/CD, stateless tiers
│   │   │
│   │   └── NO → Is the workload stable and predictable (90+ days)?
│   │       ├── NO → Stay on PAYG. Re-evaluate quarterly.
│   │       │
│   │       └── YES → Has it been right-sized? (see Compute rightsizing below)
│   │           ├── NO → Right-size first. Do not commit to waste.
│   │           │
│   │           └── YES → Will it stay on the same VM family + region?
│   │               ├── YES → Azure Reservation (up to 72%)
│   │               │         Deepest discount. Can be exchanged for a
│   │               │         different SKU if workload changes (subject
│   │               │         to exchange policy limits).
│   │               │
│   │               └── NO / UNSURE → Savings Plan for Compute (up to 65%)
│   │                     Covers any VM family and region. ~7% shallower
│   │                     than Reservations but protects against family
│   │                     or region changes. Cannot be exchanged or
│   │                     refunded once purchased.
│   │
│   └── Special case: GPU / N-series VMs
│       - Capacity scarcity is a primary concern (NC, ND, NV families)
│       - Reservations may be necessary to secure capacity in constrained regions
│       - Savings Plans do not reserve capacity - only provide pricing benefit
│       - For ML training: consider Spot VMs with checkpointing
│       - For containerised GPU workloads: see AKS GPU optimisation below
│
├── Azure Kubernetes Service (AKS)
│   │
│   ├── AKS node pools run on VMs → commitment applies to underlying VMs
│   │   (use VM decision tree above for node pool instances)
│   │
│   ├── Spot node pools → use Spot priority for fault-tolerant pods
│   │   - Configure pod disruption budgets for graceful eviction
│   │   - Use taints/tolerations to isolate Spot-eligible workloads
│   │   - Can save 60-90% on non-critical node pools
│   │
│   ├── GPU node pools → special optimisation considerations
│   │   - Enable Dynamic Resource Allocation (DRA) for GPU-aware scheduling
│   │   - Use MPS (Multi-Process Service) for GPU sharing on NVIDIA GPUs
│   │   - Consider MIG (Multi-Instance GPU) for A100/H100 partitioning
│   │   - See "AKS GPU optimisation" section below for detailed guidance
│   │
│   └── Consider: cluster autoscaler + right-sized node pools before committing
│       Pod rightsizing (VPA) saves 20-40%; node pool rightsizing saves 15-30%.
│       Commit after these optimisations are stable, not before.
│
├── App Service
│   │
│   ├── Consumption Plan → no commitment needed (pay per execution)
│   │
│   ├── Premium v3 / Isolated v2 → Savings Plan for Compute applies
│   │   - Only relevant if App Service spend is significant (>$2K/month)
│   │   - Reservations also available for Isolated tier
│   │
│   └── Legacy plans (V2) → migrate to V3 first for better price-performance,
│       then evaluate commitment on the new tier
│
├── Azure Functions
│   │
│   ├── Consumption Plan → pay per execution, no commitment available
│   │   - Focus on optimising execution duration and memory allocation
│   │
│   ├── Premium Plan → runs on App Service infrastructure
│   │   Savings Plan for Compute applies. But first: does the workload
│   │   actually need Premium? Move non-critical functions to Consumption
│   │   Plan before committing to Premium.
│   │
│   └── Dedicated (App Service Plan) → same as App Service above
│
├── Container Instances
│   │
│   └── Savings Plan for Compute covers Container Instances
│       - Only worth committing if usage is sustained and predictable
│       - For short-lived or burst containers, PAYG is usually cheaper
│
└── Azure Databricks
    │
    └── Databricks has its own commitment model (DBCU pre-purchase)
        - Separate from Azure Reservations and Savings Plans
        - See finops-databricks.md for Databricks-specific guidance
```

### Savings Plan vs Reservation - detailed comparison

| Dimension | Azure Reservation | Azure Savings Plan for Compute |
|---|---|---|
| Commitment | Specific SKU for 1yr or 3yr | $/hr spend for 1yr or 3yr |
| Discount depth | Up to 72% | Up to 65% |
| VM family | Locked to one family | Any family |
| Region | Locked to one region | Any region |
| Size | Flexible within family (instance size flexibility) | Any size |
| Covers App Service | Isolated tier only | Premium v3 + Isolated v2 |
| Covers Container Instances | No | Yes |
| Exchangeable | Yes (for equal or greater value, $50K/12mo refund cap) | No |
| Refundable | Pro-rated, up to $50K per 12 months | No |
| Cancellable | Yes (with early termination fee) | No |
| Payment options | Monthly or Upfront | Monthly or Upfront |
| Scoping | Subscription, resource group, management group, shared | Subscription, resource group, management group, shared |

**Key takeaway:** Reservations offer deeper discounts AND more liquidity (exchanges,
refunds). Savings Plans offer broader coverage but zero liquidity once purchased. This
inverts the common assumption that "flexibility = Savings Plans." For Azure specifically,
Reservations are often the better choice when workloads are moderately stable, because
you retain the ability to exchange if things change.

### Spot Virtual Machines

For fault-tolerant, interruptible workloads, Spot offers up to 90% discount over PAYG.

**Appropriate for Spot:** Batch processing, dev/test, CI/CD, stateless pods in AKS,
ML training with checkpointing, scale-out processing with VMSS.

**Not appropriate:** Stateful databases, workloads with strict SLA requirements,
single-instance workloads with no failover.

**Key constraint:** 30-second eviction notice (vs 2 minutes on AWS), no SLA guarantees.

**Spot best practices:**
- Start with 20-30% Spot allocation in non-production, increase based on stability
- Use VMSS with Spot priority for auto-scaling pools with automatic fallback
- Configure eviction policy: Deallocate (preserves disk) or Delete (lowest cost)
- Set max price at PAYG rate - never bid above PAYG
- For AKS: use Spot node pools with taints/tolerations for workload isolation
- Monitor eviction rates by VM family and region - some combinations are more stable

### Azure Hybrid Benefit (AHB)

Organisations with existing Windows Server or SQL Server licenses (with Software
Assurance) can apply them to Azure resources, eliminating the licence premium.

**Why AHB is the #1 quick win:**
- Up to 40% savings on Windows VMs, up to 55% on SQL Database
- No architectural change, no restart needed - single CLI command per VM
- Also applies to SQL Managed Instance and Red Hat/SUSE Linux
- Zero commitment, zero risk, immediate effect
- Use the AHB Workbook from FinOps Toolkit for compliance tracking across the fleet
- **Enable on all eligible VMs before evaluating any other commitment**

### Compute commitment layering strategy

Azure applies discounts in a specific order. The layering sequence matters.

**Discount application order (Azure-defined):**
1. Azure Hybrid Benefit (licence overlay, applied first to eligible VMs)
2. Spot pricing (market rate, for Spot-eligible workloads)
3. Reservations (capacity-based, applied to matching PAYG usage)
4. Savings Plans (spend-based, applied to remaining eligible PAYG usage)
5. MACC discount (portfolio-wide, applied last to remaining spend)

**Recommended layering approach:**

```
Layer 0: Azure Hybrid Benefit (free - no commitment, immediate)
  ↓ eliminates licence cost on all eligible Windows/SQL VMs
Layer 1: Spot (for interruptible workloads)
  ↓ removes 15-40% of compute from the commitment equation
Layer 2: Savings Plans for Compute (broad baseline)
  ↓ covers predictable floor across VMs/App Service/Container Instances
Layer 3: Reservations (high-stability VM workloads)
  ↓ captures the extra ~7% discount for workloads locked to a family+region
  ↓ retains exchange/refund liquidity if workload changes
Layer 4: MACC (portfolio-wide, if applicable)
  ↓ applies on top of everything above for remaining PAYG spend
Layer 5: PAYG (variable / new workloads)