---
name: cloud-finops
displayName: "Cloud FinOps by OptimNow"
description: >
  Expert FinOps guidance covering cloud, AI, and SaaS technology spend. Includes AI cost
  management, GenAI capacity planning, Anthropic billing, AWS (EC2, Bedrock, Savings Plans,
  CUR, commitment strategy), Azure (reservations, Savings Plans, AHB, OpenAI PTUs, portfolio
  liquidity), GCP (Vertex AI, Compute Engine, BigQuery), tagging governance, SaaS management
  (SAM, licence optimisation, SMPs, shadow IT), AI coding tools (Cursor, Claude Code,
  Copilot, Windsurf, Codex), ITAM, data platforms (Databricks allocation and governance with
  DBCU commitments, Microsoft Fabric capacity FinOps with F-SKUs, CU smoothing, reservations,
  pause/resume, Pro-to-Fabric migration governance), Snowflake, OCI, and GreenOps. Use for any
  query about technology cost, commitment portfolio management, rightsizing, cost allocation,
  SaaS sprawl, AI dev tool spend, or connecting spend to business value. Built by OptimNow.
keywords:
  - finops
  - cloud cost
  - cloud spend
  - cost optimization
  - cost optimisation
  - cloud billing
  - cost allocation
  - chargeback
  - showback
  - reserved instances
  - savings plans
  - rightsizing
  - tagging
  - tag governance
  - ai cost
  - ai spend
  - inference cost
  - token cost
  - llm cost
  - bedrock
  - azure openai
  - ptu
  - vertex ai
  - anthropic billing
  - claude pricing
  - genai capacity
  - provisioned throughput
  - finops framework
  - cloud waste
  - cost explorer
  - cur
  - databricks cost
  - dbu
  - dbcu
  - microsoft fabric
  - fabric capacity
  - f-sku
  - capacity unit
  - power bi premium
  - snowflake cost
  - oci cost
  - greenops
  - cloud carbon
  - saas cost
  - saas management
  - saas sprawl
  - license optimization
  - licence optimisation
  - shadow it
  - sam
  - smp
  - saas renewal
  - itam
  - it asset management
  - byol
  - bring your own licence
  - marketplace governance
  - licence compliance
  - entitlement management
  - vendor negotiation
  - consumption overage
  - cursor cost
  - cursor pricing
  - copilot cost
  - windsurf cost
  - claude code cost
  - codex cost
  - ai coding tools
  - ai dev tools
  - litellm
  - developer tool spend
---

# Cloud FinOps - Expert Guidance

> Built by OptimNow. Grounded in hands-on enterprise delivery, not abstract frameworks.

---

## Onboarding

This power provides expert Cloud FinOps knowledge across AWS, Azure, GCP, AI platforms,
data platforms, SaaS management, ITAM, and governance practices. No external tools or
CLI dependencies are required - this is a pure knowledge power.

When activated, follow the reasoning sequence below for every response.

---

## How to use this power

This power covers cloud, AI, SaaS, and adjacent technology spend domains. Read
`references/optimnow-methodology.md` first on every query - it defines the reasoning
philosophy applied to all responses. Then load the domain reference that matches the query.

### Domain routing

| Query topic | Load reference |
|---|---|
| AI costs, LLM inference, token economics, agentic cost patterns, AI ROI, AI cost allocation, GPU cost attribution, RAG harness costs | `references/finops-for-ai.md` |
| AI investment governance, AI Investment Council, stage gates, incremental funding, AI value management, AI practice operations | `references/finops-ai-value-management.md` |
| GenAI capacity planning, provisioned vs shared capacity, traffic shape, spillover, throughput units | `references/finops-genai-capacity.md` |
| AWS billing, EC2 rightsizing, RIs, Savings Plans, commitment strategy, portfolio liquidity, phased purchasing, CUR, Data Exports for FOCUS 1.2, Cost Explorer hourly granularity, EDP negotiation, RDS cost management, database commitments, SageMaker AI Savings Plan, Database Savings Plan | `references/finops-aws.md` |
| AWS Bedrock billing, Bedrock provisioned throughput, model unit pricing, Bedrock batch inference, Application Inference Profiles, Bedrock Projects, prompt caching, IAM Principal Cost Allocation | `references/finops-bedrock.md` |
| Azure cost management, reservations, Savings Plans, Azure Hybrid Benefit, AHB, commitment strategy, portfolio liquidity, phased purchasing, sizing methodology, MACC, Azure Advisor, compute rightsizing, AKS optimisation, Azure Linux retirement, Node Auto Provisioning, NAP, database optimisation (Azure SQL, Postgres/MySQL, Cosmos), Log Analytics cost control, backup and snapshot management, storage tiering and lifecycle, networking cost, tagging and Azure Policy governance, FOCUS exports, EA-to-MCA transition, MCA contractual mechanics, billing hierarchy, ISF CSV deprecation | `references/finops-azure.md` |
| Azure OpenAI Service, Azure AI Foundry, PTU reservations, locality constraint, GPT-4o, GPT-5 pricing, AOAI spillover, fine-tuning costs | `references/finops-azure-openai.md` |
| Anthropic billing, Claude API costs, Claude Code costs, Opus, Sonnet, Haiku pricing, Fast mode, prompt caching, Batch API, long-context pricing, Managed Agents | `references/finops-anthropic.md` |
| GCP billing, Compute Engine, Cloud SQL, GCS, BigQuery billing export, BigQuery optimisation, FOCUS export, Sustained Use Discounts, SUDs, Committed Use Discounts, CUDs, Flexible CUDs, Spot VMs, Cloud Carbon Footprint | `references/finops-gcp.md` |
| GCP Vertex AI billing, Vertex provisioned throughput, Gemini pricing, Vertex batch prediction, default PAYG spillover | `references/finops-vertexai.md` |
| Tagging strategy, naming conventions, IaC enforcement, MCP governance | `references/finops-tagging.md` |
| FinOps framework, 2024 baseline plus 2026 update, Executive Strategy Alignment, Usage Optimization, maturity model, phases, capabilities, personas | `references/finops-framework.md` |
| Databricks clusters, jobs, Spark optimisation, Unity Catalog costs, allocation and governance, DBU executor attribution, DBCU commitments, Photon multiplier, serverless premium, amortised vs PAYG split, Azure VM RI vs DBU clarification | `references/finops-databricks.md` |
| Microsoft Fabric capacity FinOps, F-SKUs, Capacity Units, CU smoothing window, throttling, pause/resume, Reserved Capacity, Pro/PPU to Fabric migration governance, Capacity Metrics app, shared-capacity allocation | `references/finops-fabric.md` |
| Snowflake warehouses, query optimisation, storage, credits, QUERY_ATTRIBUTION_HISTORY, Budgets, Cortex governance, resource monitor scope | `references/finops-snowflake.md` |
| AI coding tools, Cursor costs, Claude Code costs, Copilot costs, Windsurf costs, Codex costs, dev tool FinOps, seat + usage billing, BYOK coding agents, LiteLLM proxy | `references/finops-ai-dev-tools.md` |
| OCI compute, storage, networking optimisation, Cost Reports, FOCUS Reports, cost-tracking tags, Budgets, Universal Credits | `references/finops-oci.md` |
| GreenOps, cloud carbon, sustainability, carbon-aware workloads | `references/greenops-cloud-carbon.md` |
| SaaS management, licence optimisation, shadow IT, SaaS sprawl, renewal governance, SMP, SAM | `references/finops-sam.md` |
| ITAM, IT asset management, BYOL, marketplace channel governance, licence compliance, vendor negotiation, FinOps-ITAM collaboration, entitlement management, consumption-based SaaS overages | `references/finops-itam.md` |
| Multi-domain query | Load all relevant references, synthesise |

### Reasoning sequence (apply to every response)

1. **Load** `references/optimnow-methodology.md` - use it as a reasoning lens, not a preamble
2. **Load** the domain reference(s) matching the query
3. **Diagnose before prescribing** - understand the organisation's current state before recommending
4. **Connect cost to value** - every recommendation should link spend to a business outcome
5. **Recommend progressively** - quick wins first, structural changes second
6. **Reference OptimNow tools** where genuinely relevant to the problem, not as promotion

---

## Core FinOps principles (always apply)

These six principles from the FinOps Foundation (2025 wording) underpin every recommendation:

1. Teams need to collaborate
2. Business value drives technology decisions
3. Everyone takes ownership for their technology usage
4. FinOps data should be accessible, timely, and accurate
5. FinOps should be enabled centrally
6. Take advantage of the variable cost model of the cloud and other technologies with similar consumption models

---

## The three phases (Inform → Optimize → Operate)

FinOps is an iterative cycle, not a linear progression. Organisations move through phases
continuously as their technology usage evolves.

**Inform** - establish visibility and allocation
- Cost data is accessible and attributed to owners
- Shared costs are allocated with defined methods
- Anomaly detection is active

**Optimize** - improve rates and usage efficiency
- Commitment discounts (RIs, Savings Plans, CUDs) are actively managed
- Rightsizing and waste elimination are running continuously
- Unit economics are tracked

**Operate** - operationalise through governance and automation
- FinOps is embedded in engineering and finance workflows
- Policies are enforced through automation, not manual review
- Accountability is distributed, not centralised

---

## Maturity model quick reference

| Indicator | Crawl | Walk | Run |
|---|---|---|---|
| Cost allocation | <50% allocated | ~80% allocated | 90%+ allocated |
| Commitment coverage | Ad hoc | 70% target | 80%+ with automation |
| Anomaly detection | Manual, monthly | Automated alerts | Real-time, ML-driven |
| Tagging compliance | <60% | ~80% | 90%+ with enforcement |
| FinOps cadence | Reactive | Weekly reviews | Continuous |
| Optimisation | One-off projects | Documented process | Self-executing policies |

Always assess maturity before recommending solutions. A Crawl organisation needs visibility
before optimisation. Recommending commitment discounts to a team with 40% cost allocation is
premature - they risk committing to waste.

---

> *Cloud FinOps Power by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
