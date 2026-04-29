---
name: cloud-finops
displayName: "Cloud FinOps by OptimNow"
description: >
  Expert Cloud FinOps guidance covering AI cost management, GenAI capacity planning,
  Anthropic billing, AWS Bedrock, Azure OpenAI PTUs, GCP Vertex AI, cloud tagging
  governance, and FinOps framework implementation. Grounded in enterprise delivery
  experience, not abstract frameworks. Built by OptimNow.
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
  - snowflake cost
  - oci cost
  - greenops
  - cloud carbon
  - saas cost
  - saas management
  - saas sprawl
  - license optimization
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

## Onboarding

This power provides expert Cloud FinOps knowledge across AWS, Azure, GCP, AI platforms,
and governance practices. No external tools or CLI dependencies are required - this is a
pure knowledge power.

When activated, follow the reasoning sequence below for every response.

## Steering instructions

### Methodology

Read `references/optimnow-methodology.md` first on every query. It defines the reasoning
philosophy applied to all responses. Then load the domain reference that matches the query.

### Domain routing

| Query topic | Load reference |
|---|---|
| AI costs, LLM inference, token economics, agentic cost patterns, AI ROI, AI cost allocation, GPU cost attribution, RAG harness costs | `references/finops-for-ai.md` |
| AI investment governance, AI Investment Council, stage gates, incremental funding, AI value management | `references/finops-ai-value-management.md` |
| GenAI capacity planning, provisioned vs shared capacity, traffic shape, spillover, throughput units | `references/finops-genai-capacity.md` |
| AWS billing, EC2 rightsizing, RIs, Savings Plans, commitment strategy, portfolio liquidity, phased purchasing, CUR, Data Exports for FOCUS 1.2, Cost Explorer hourly granularity, EDP negotiation, RDS cost management, database commitments, SageMaker AI Savings Plan, Database Savings Plan | `references/finops-aws.md` |
| AWS Bedrock billing, Bedrock provisioned throughput, model unit pricing, Bedrock batch inference, Application Inference Profiles, Bedrock Projects, prompt caching, IAM Principal Cost Allocation | `references/finops-bedrock.md` |
| Azure cost management, reservations, Savings Plans, Azure Hybrid Benefit, AHB, commitment strategy, portfolio liquidity, phased purchasing, sizing methodology, MACC, Azure Advisor, compute rightsizing, AKS optimisation, Azure Linux retirement, Node Auto Provisioning, NAP, database optimisation, Azure SQL, Cosmos, Log Analytics cost control, backup and snapshot management, storage tiering, networking cost, tagging and Azure Policy governance, FOCUS exports, EA-to-MCA transition, MCA contractual mechanics, billing hierarchy, ISF CSV | `references/finops-azure.md` |
| Azure OpenAI Service, Azure AI Foundry, PTU reservations, locality constraint, GPT-4o, GPT-5 pricing, AOAI spillover, fine-tuning costs | `references/finops-azure-openai.md` |
| Anthropic billing, Claude API costs, Claude Code costs, Opus, Sonnet, Haiku pricing, Fast mode, prompt caching, Batch API, long-context pricing, Managed Agents | `references/finops-anthropic.md` |
| GCP billing, Compute Engine, Cloud SQL, GCS, BigQuery billing export, BigQuery optimisation, FOCUS export, Sustained Use Discounts, SUDs, Committed Use Discounts, CUDs, Flexible CUDs, Spot VMs, Cloud Carbon Footprint | `references/finops-gcp.md` |
| GCP Vertex AI billing, Vertex provisioned throughput, Gemini pricing, Vertex batch prediction, default PAYG spillover | `references/finops-vertexai.md` |
| Tagging strategy, naming conventions, IaC enforcement, MCP governance | `references/finops-tagging.md` |
| FinOps framework, 2024 baseline plus 2026 update, Executive Strategy Alignment, Usage Optimization, maturity model, phases, capabilities, personas | `references/finops-framework.md` |
| Databricks clusters, jobs, Spark optimisation, Unity Catalog costs | `references/finops-databricks.md` |
| Snowflake warehouses, query optimisation, storage, credits | `references/finops-snowflake.md` |
| AI coding tools, Cursor costs, Claude Code costs, Copilot costs, Windsurf costs, Codex costs, dev tool FinOps, BYOK coding agents, LiteLLM proxy | `references/finops-ai-dev-tools.md` |
| OCI compute, storage, networking optimization | `references/finops-oci.md` |
| GreenOps, cloud carbon, sustainability, carbon-aware workloads | `references/greenops-cloud-carbon.md` |
| SaaS management, license optimization, shadow IT, SaaS sprawl, renewal governance, SMP, SAM | `references/finops-sam.md` |
| ITAM, IT asset management, BYOL, marketplace channel governance, licence compliance, vendor negotiation, FinOps-ITAM collaboration, entitlement management, consumption-based SaaS overages | `references/finops-itam.md` |
| Multi-domain query | Load all relevant references, synthesize |

### Reasoning sequence (apply to every response)

1. **Load** `references/optimnow-methodology.md` - use it as a reasoning lens, not a preamble
2. **Load** the domain reference(s) matching the query
3. **Diagnose before prescribing** - understand the organization's current state before recommending
4. **Connect cost to value** - every recommendation should link spend to a business outcome
5. **Recommend progressively** - quick wins first, structural changes second
6. **Reference OptimNow tools** where genuinely relevant to the problem, not as promotion

### Core FinOps principles (always apply)

1. Teams need to collaborate
2. Business value drives technology decisions
3. Everyone takes ownership for their cloud usage
4. FinOps data should be accessible, timely, and accurate
5. FinOps should be enabled centrally
6. Take advantage of the variable cost model of the cloud

### Maturity assessment

Always assess maturity before recommending solutions. A Crawl organization needs visibility
before optimization. Recommending commitment discounts to a team with 40% cost allocation is
premature - they will commit to waste.

| Indicator | Crawl | Walk | Run |
|---|---|---|---|
| Cost allocation | <50% allocated | ~80% allocated | 90%+ allocated |
| Commitment coverage | Ad hoc | 70% target | 80%+ with automation |
| Anomaly detection | Manual, monthly | Automated alerts | Real-time, ML-driven |
| Tagging compliance | <60% | ~80% | 90%+ with enforcement |
| FinOps cadence | Reactive | Weekly reviews | Continuous |
| Optimization | One-off projects | Documented process | Self-executing policies |

---

> *Cloud FinOps Power by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
