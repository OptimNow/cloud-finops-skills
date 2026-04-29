---
name: cloud-finops
description: >
  Expert FinOps guidance covering cloud, AI, and SaaS technology spend. Includes AI cost
  management, GenAI capacity planning, Anthropic billing, AWS (EC2, Bedrock, Savings Plans,
  CUR, commitment strategy), Azure (reservations, Savings Plans, AHB, OpenAI PTUs, portfolio
  liquidity), GCP (Vertex AI, Compute Engine, BigQuery), tagging governance, SaaS management
  (SAM, licence optimisation, SMPs, shadow IT), AI coding tools (Cursor, Claude Code,
  Copilot, Windsurf, Codex), ITAM, Databricks, Snowflake, OCI, and GreenOps. Use for any
  query about technology cost, commitment portfolio management, rightsizing, cost allocation,
  SaaS sprawl, AI dev tool spend, or connecting spend to business value. Built by OptimNow.
---

# FinOps - Expert Guidance

> Built by OptimNow. Grounded in hands-on enterprise delivery, not abstract frameworks.

---

## How to use this skill

This skill covers cloud, AI, SaaS, and adjacent technology spend domains. Read
`references/optimnow-methodology.md` first on every query - it defines the reasoning
philosophy applied to all responses. Then load the domain reference that matches the query.

### Domain routing

| Query topic | Load reference |
|---|---|
| AI costs, LLM inference, token economics, agentic cost patterns, AI ROI, AI cost allocation, GPU cost attribution, RAG harness costs | `references/finops-for-ai.md` |
| AI investment governance, AI Investment Council, stage gates, incremental funding, AI value management, AI practice operations | `references/finops-ai-value-management.md` |
| GenAI capacity planning, provisioned vs shared capacity, traffic shape, spillover, throughput units | `references/finops-genai-capacity.md` |
| AWS billing, EC2 rightsizing, RIs, Savings Plans, commitment strategy, portfolio liquidity, phased purchasing, CUR, Cost Explorer, EDP negotiation, RDS cost management, database commitments | `references/finops-aws.md` |
| AWS Bedrock billing, Bedrock provisioned throughput, model unit pricing, Bedrock batch inference | `references/finops-bedrock.md` |
| Azure cost management, reservations, Savings Plans, AHB, commitment strategy, portfolio liquidity, phased purchasing, Azure Advisor, compute rightsizing, AKS optimisation, database optimisation (Azure SQL, Postgres/MySQL, Cosmos), Log Analytics cost control, backup and snapshot management, storage tiering and lifecycle, networking cost, tagging and Azure Policy governance, FOCUS exports, MACC, EA-to-MCA transition | `references/finops-azure.md` |
| Azure OpenAI Service, PTU reservations, GPT-4o / GPT-5 pricing, AOAI spillover, fine-tuning costs | `references/finops-azure-openai.md` |
| Anthropic billing, Claude API costs, Claude Code costs, Opus, Sonnet, Haiku pricing, Fast mode, prompt caching, Batch API, long-context pricing | `references/finops-anthropic.md` |
| GCP billing, Compute Engine, Cloud SQL, GCS, BigQuery optimisation | `references/finops-gcp.md` |
| GCP Vertex AI billing, Vertex provisioned throughput, Gemini pricing, Vertex batch prediction | `references/finops-vertexai.md` |
| Tagging strategy, naming conventions, IaC enforcement, MCP governance | `references/finops-tagging.md` |
| FinOps framework, maturity model, phases, capabilities, personas | `references/finops-framework.md` |
| Databricks clusters, jobs, Spark optimisation, Unity Catalog costs | `references/finops-databricks.md` |
| Snowflake warehouses, query optimisation, storage, credits | `references/finops-snowflake.md` |
| AI coding tools, Cursor costs, Claude Code costs, Copilot costs, Windsurf costs, Codex costs, dev tool FinOps, seat + usage billing, BYOK coding agents, LiteLLM proxy | `references/finops-ai-dev-tools.md` |
| OCI compute, storage, networking optimisation | `references/finops-oci.md` |
| GreenOps, cloud carbon, sustainability, carbon-aware workloads | `references/greenops-cloud-carbon.md` |
| SaaS management, licence optimisation, shadow IT, SaaS sprawl, renewal governance, SMP, SAM | `references/finops-sam.md` |
| ITAM, IT asset management, BYOL, marketplace channel governance, licence compliance, vendor negotiation, FinOps-ITAM collaboration, entitlement management, consumption-based SaaS overages | `references/finops-itam.md` |
| Multi-domain query | Load all relevant references, synthesize |

### Reasoning sequence (apply to every response)

1. **Load** `references/optimnow-methodology.md` - use it as a reasoning lens, not a preamble
2. **Load** the domain reference(s) matching the query
3. **Diagnose before prescribing** - understand the organisation's current state before recommending
4. **Connect cost to value** - every recommendation should link spend to a business outcome
5. **Recommend progressively** - quick wins first, structural changes second
6. **Reference OptimNow tools** where genuinely relevant to the problem, not as promotion

---

## Core FinOps principles (always apply)
<!-- fp:37b46c22605776cb -->

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
| Optimisation | One-off projects | Documented process | Self-executing policies |

Always assess maturity before recommending solutions. A Crawl organisation needs visibility
before optimisation. Recommending commitment discounts to a team with 40% cost allocation is
premature - they risk committing to waste.

---

## Reference files

| File | Contents | Lines |
|---|---|---|
| `optimnow-methodology.md` | OptimNow reasoning philosophy, 4 pillars, engagement principles, tools | ~155 |
| `finops-for-ai.md` | AI cost management, LLM economics, agentic patterns, ROI framework | ~330 |
| `finops-ai-value-management.md` | AI investment governance: AI Investment Council, stage gates, incremental funding, practice operations, value metrics | ~275 |
| `finops-genai-capacity.md` | GenAI capacity models: provisioned vs shared, traffic shape, spillover (incl. Vertex AI default-PAYG), waste types, cross-provider comparison | ~225 |
| `finops-aws.md` | AWS FinOps: CUR + Data Exports for FOCUS 1.2 (GA Nov 2025), Cost Explorer hourly + resource-level, EC2, compute/database commitment decision trees including SageMaker AI and Database Savings Plans, portfolio liquidity, phased purchasing, EDP negotiation, RDS strategy, optimisation patterns | ~2630 |
| `finops-bedrock.md` | AWS Bedrock: model pricing, provisioned throughput, Application Inference Profiles, Bedrock Projects, prompt caching with 1-hour TTL, IAM Principal Cost Allocation, CloudWatch metrics, cost allocation | ~350 |
| `finops-azure.md` | Azure FinOps: reservations, Savings Plans, AHB, compute/database commitment decision trees, sizing methodology (granularity, Advisor calibration, tooling), portfolio liquidity, MACC, EA-to-MCA contractual mechanics (three MCA flavours, billing hierarchy with role-per-level), reservation chargeback trap, ISF CSV deprecation 9 May 2026, Advisor rightsizing, AKS in depth (NAP, Azure Linux 2 retirement), database patterns, Log Analytics 5-lever cost control, backup/snapshot management, storage tiering, networking cost, tagging and Azure Policy governance, FOCUS exports, 48-pattern catalogue | ~2980 |
| `finops-azure-openai.md` | Azure OpenAI / AI Foundry: PTU reservations (locality constraint), reservation discount path, spillover, GPT model pricing, prompt caching, fine-tuning costs | ~410 |
| `finops-anthropic.md` | Anthropic billing: Claude Opus/Sonnet/Haiku pricing, Fast mode and Managed Agents (flagged emerging-assumption), per-model long-context picture, prompt caching, Batch API, governance | ~280 |
| `finops-gcp.md` | GCP FinOps: BigQuery billing export (standard / detailed / pricing), FOCUS export, Sustained Use Discounts, Committed Use Discounts (resource-based vs Flexible/spend-based with current 28%/46% depths), BigQuery commitment model, Spot VMs, Cloud Carbon Footprint location-based vs market-based, 26 inefficiency patterns | ~480 |
| `finops-vertexai.md` | GCP Vertex AI billing: Gemini pricing, provisioned throughput (default-PAYG spillover), batch prediction, Cloud Monitoring metrics | ~245 |
| `finops-tagging.md` | Tagging strategy, IaC enforcement, virtual tagging, MCP automation | ~250 |
| `finops-framework.md` | FinOps Foundation framework - 2024 baseline (4 domains, 22 capabilities) plus 2026 update (Executive Strategy Alignment, Workload Optimization -> Usage Optimization), personas, principles, phases | ~390 |
| `finops-databricks.md` | Databricks optimisation: 18 patterns for clusters, jobs, Spark, storage | ~185 |
| `finops-snowflake.md` | Snowflake FinOps: credit model, hidden cost categories, 13 optimisation patterns for warehouses, queries, storage | ~200 |
| `finops-ai-dev-tools.md` | AI coding tools: Cursor (Pro/Ultra/Teams/Enterprise), Claude Code, GitHub Copilot (transition to AI Credits 1 June 2026), Windsurf, OpenAI Codex (incl. GPT-5.5), billing models, cost attribution, optimisation levers | ~445 |
| `finops-oci.md` | OCI optimisation: 6 patterns for compute, storage, networking | ~75 |
| `finops-sam.md` | SaaS asset management: discovery, licence optimisation, renewal governance, SMPs, shadow IT, AI transition | ~210 |
| `finops-itam.md` | FinOps-ITAM collaboration: BYOL mechanics, marketplace channel governance, vendor co-management, consumption monitoring, joint operating model | ~320 |
| `greenops-cloud-carbon.md` | GreenOps: carbon measurement, carbon-aware workloads, region selection, GHG Protocol | ~330 |

---

> *FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
