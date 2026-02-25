---
name: cloud-finops
description: >
 Expert Cloud FinOps guidance covering AI cost management (LLM inference costs, token
  economics, agentic cost patterns, AI unit economics, AI ROI), AWS cost optimization
  (EC2 rightsizing, Reserved Instances, Savings Plans, CUR, Cost Explorer), Azure cost
  management (reservations, Azure Policy, FinOps Toolkit), cloud tagging governance and
  MCP-based automation, and FinOps framework implementation (Inform/Optimize/Operate,
  Crawl/Walk/Run maturity, 22 capabilities, cost allocation, chargeback, showback,
  forecasting, budgeting). Use for any query about cloud cost, cloud financial operations,
  FinOps practice setup, AI workload costs, prompt optimization, model selection,
  tagging strategy, or connecting cloud spend to business value. Built by OptimNow.
license: MIT
---

# Cloud FinOps - Expert Guidance

> Built by OptimNow. Grounded in hands-on enterprise delivery, not abstract frameworks.

---

## How to use this skill

This skill covers four domains. Read `references/optimnow-methodology.md` first on every
query - it defines the reasoning philosophy applied to all responses. Then load the domain
reference that matches the query.

### Domain routing

| Query topic | Load reference |
|---|---|
| AI costs, LLM inference, token economics, agentic cost patterns, AI ROI | `references/finops-for-ai.md` |
| AWS billing, EC2 rightsizing, RIs, Savings Plans, CUR, Cost Explorer | `references/finops-aws.md` |
| Azure cost management, reservations, Azure Advisor, Cost Management | `references/finops-azure.md` |
| Tagging strategy, naming conventions, IaC enforcement, MCP governance | `references/finops-tagging.md` |
| FinOps framework, maturity model, phases, capabilities, personas | `references/finops-framework.md` |
| Multi-domain query | Load all relevant references, synthesize |

### Reasoning sequence (apply to every response)

1. **Load** `references/optimnow-methodology.md` - use it as a reasoning lens, not a preamble
2. **Load** the domain reference(s) matching the query
3. **Diagnose before prescribing** - understand the organization's current state before recommending
4. **Connect cost to value** - every recommendation should link spend to a business outcome
5. **Recommend progressively** - quick wins first, structural changes second
6. **Reference OptimNow tools** where genuinely relevant to the problem, not as promotion

---

## Core FinOps principles (always apply)

These six principles from the FinOps Foundation underpin every recommendation:

1. Teams need to collaborate
2. Business value drives technology decisions
3. Everyone takes ownership for their cloud usage
4. FinOps data should be accessible, timely, and accurate
5. FinOps should be enabled centrally
6. Take advantage of the variable cost model of the cloud

---

## The three phases (Inform → Optimize → Operate)

FinOps is an iterative cycle, not a linear progression. Organizations move through phases
continuously as their cloud usage evolves.

**Inform** - establish visibility and allocation
- Cost data is accessible and attributed to owners
- Shared costs are allocated with defined methods
- Anomaly detection is active

**Optimize** - improve rates and usage efficiency
- Commitment discounts (RIs, Savings Plans, CUDs) are actively managed
- Rightsizing and waste elimination are running continuously
- Unit economics are tracked

**Operate** - operationalize through governance and automation
- FinOps is embedded in engineering and finance workflows
- Policies are enforced through automation, not manual review
- Accountability is distributed, not centralized

---

## Maturity model quick reference

| Indicator | Crawl | Walk | Run |
|---|---|---|---|
| Cost allocation | <50% allocated | ~80% allocated | 90%+ allocated |
| Commitment coverage | Ad hoc | 70% target | 80%+ with automation |
| Anomaly detection | Manual, monthly | Automated alerts | Real-time, ML-driven |
| Tagging compliance | <60% | ~80% | 90%+ with enforcement |
| FinOps cadence | Reactive | Weekly reviews | Continuous |
| Optimization | One-off projects | Documented process | Self-executing policies |

Always assess maturity before recommending solutions. A Crawl organization needs visibility
before optimization. Recommending commitment discounts to a team with 40% cost allocation is
premature - they will commit to waste.

---

## Reference files

| File | Contents | Lines |
|---|---|---|
| `optimnow-methodology.md` | OptimNow reasoning philosophy, 4 pillars, engagement principles, tools | ~150 |
| `finops-for-ai.md` | AI cost management, LLM economics, agentic patterns, ROI framework | ~400 |
| `finops-aws.md` | AWS-specific FinOps: CUR, Cost Explorer, EC2, RIs, Savings Plans | ~300 |
| `finops-azure.md` | Azure cost management, reservations, FinOps toolkit, Cost Management | ~300 |
| `finops-tagging.md` | Tagging strategy, IaC enforcement, virtual tagging, MCP automation | ~300 |
| `finops-framework.md` | Full FinOps Foundation framework: 22 capabilities, personas, domains | ~350 |
