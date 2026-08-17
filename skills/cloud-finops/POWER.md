---
name: cloud-finops
displayName: "Cloud FinOps by OptimNow"
description: >
  Expert FinOps guidance covering cloud, AI, and SaaS technology spend. Includes AI cost
  management, GenAI capacity planning, self-hosted vs managed AI inference decisioning,
  Anthropic billing, AWS (EC2, Bedrock, SageMaker, GPU rightsizing, Savings Plans,
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
  - self-hosted llm
  - self-hosted inference
  - build vs buy llm
  - vllm
  - sglang
  - llama.cpp
  - gpu rental
  - runpod
  - coreweave
  - hybrid inference routing
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
  - anomaly management
  - cost anomaly
  - masked anomaly
  - layered detection
  - threshold tuning
  - new-region detection
  - cost allocation
  - showback
  - allocation methodology
  - effectivecost
  - amortised vs unblended
  - blended cost trap
  - defensible allocation keys
  - shared services allocation
  - invoiceid reconciliation
  - unallocated spend
  - chargeback
  - soft chargeback
  - hard chargeback
  - financial accountability
  - erp readiness
  - cfo sponsorship
  - inter-bu p&l
  - transfer pricing
  - intercompany cloud recharge
  - cross-border tax
  - pillar 2 minimum tax
  - sox chargeback controls
  - methodology dispute
  - chargeback revolt
  - onboarding workloads
  - migration cost hygiene
  - intake gate
  - 60-90 day commitment rule
  - double bubble cost
  - migration network cost trap
  - m&a integration
  - focus during migration
  - cost-aware architecture review
  - post-migration owner
  - kubernetes finops
  - k8s allocation
  - opencost
  - kubecost
  - container rightsizing
  - karpenter
  - cluster autoscaler
  - pod disruption budgets
  - spot diversification
  - idle node cost
  - node efficiency
  - waste detection
  - waste detection playbooks
  - orphaned resources
  - idle resources
  - overprovisioned resources
  - commitment mismatches
  - schedule blindness
  - modernization opportunities
  - ai ml inefficiency
  - two-signal classification
  - obvious likely possible
  - realised savings
  - wasteline
  - optimnow waste taxonomy
  - sagemaker
  - sagemaker endpoint
  - sagemaker notebook
  - sagemaker studio
  - sagemaker mme
  - multi-model endpoints
  - inference components
  - sagemaker deployment pattern
  - async inference
  - serverless inference
  - batch transform
  - notebook auto-shutdown
  - lifecycle configuration
  - gpu rightsizing
  - oversized gpu
  - multi-gpu underutilized
  - mig
  - multi-instance gpu
  - gpu partitioning
  - outdated gpu generation
  - gpu modernization
  - cpu-bound ai workload
  - gpu for cpu workload
  - dcgm
  - nvidia dcgm
  - dcgm exporter
  - gpu telemetry
  - tensor core
  - gpu memory bandwidth
  - gpu utilization misleading
  - agentic finops
  - agentic cost anatomy
  - agent-initiated payments
  - x402
  - mpp
  - agent wallets
  - cost per completed task
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

This power covers cloud, AI, SaaS, and adjacent technology spend domains. Apply the
OptimNow lens to every answer: diagnose before prescribing, connect cost to value,
recommend progressively. Then load the domain reference(s) matching the query. Load
`references/optimnow-methodology.md` in full only for strategy, engagement-design, or
methodology questions - not for routine billing-mechanics queries.

### Domain routing

| Query topic | Load reference |
|---|---|
| OptimNow methodology, engagement approach, four pillars, FinOps strategy design, practice positioning | `references/optimnow-methodology.md` |
| AI costs, LLM inference, token economics, agentic cost patterns, AI ROI, AI cost allocation, GPU cost attribution, GPU telemetry, DCGM metrics, "GPU utilization is misleading", tensor core activity, GPU memory bandwidth, RAG harness costs | `references/finops-for-ai.md` |
| Agentic FinOps, true agents vs pipelines vs workflows, agentic cost anatomy, cost per completed task, cost-safe agent architecture, agent-initiated payments, x402, MPP, agent wallets | `references/finops-agentic.md` |
| AI investment governance, AI Investment Council, stage gates, incremental funding, AI value management, AI practice operations | `references/finops-ai-value-management.md` |
| GenAI capacity planning, provisioned vs shared capacity, traffic shape, spillover, throughput units | `references/finops-genai-capacity.md` |
| Self-hosted vs managed AI inference, build vs buy LLM, vLLM, SGLang, llama.cpp, GPU rental, RunPod, CoreWeave, Lambda, hidden cost surface, ML-Ops maturity rubric, hybrid routing (LiteLLM, Portkey) | `references/finops-ai-self-hosted-vs-managed.md` |
| AWS billing data, CUR, Data Exports for FOCUS 1.2, Cost Explorer, EC2/compute rightsizing, SageMaker operational FinOps, cost allocation, governance, CloudFront flat-rate plans, S3 Files, multi-org billing | `references/finops-aws.md` |
| AWS Savings Plans, Reserved Instances, Spot, commitment decision tree, commitment portfolio liquidity, phased purchasing, EDP negotiation, Convertible RI exchange | `references/finops-aws-commitments.md` |
| AWS per-service inefficiency catalogue, enumerated AWS optimisation patterns | `references/finops-aws-patterns.md` |
| AWS Bedrock billing, Bedrock provisioned throughput, model unit pricing, Bedrock batch inference, Application Inference Profiles, Bedrock Projects, prompt caching, IAM Principal Cost Allocation | `references/finops-bedrock.md` |
| Azure cost management, Cost Management exports, FOCUS exports, Retail Prices API, compute rightsizing and Advisor calibration, Log Analytics cost control, AKS, storage tiering, networking cost, tagging and Azure Policy, EA-to-MCA transition | `references/finops-azure.md` |
| Azure Reservations, Savings Plans, Azure Hybrid Benefit, AHB, Spot VMs, compute and database commitment decision trees, commitment portfolio liquidity, 1 February 2027 exchange retirement, phased purchasing, MACC | `references/finops-azure-commitments.md` |
| Azure per-service inefficiency catalogue, enumerated Azure optimisation patterns | `references/finops-azure-patterns.md` |
| Azure OpenAI Service, Azure AI Foundry, PTU reservations, locality constraint, GPT-4o, GPT-5 pricing, AOAI spillover, fine-tuning costs | `references/finops-azure-openai.md` |
| Anthropic billing, Claude API costs, Claude Code costs, Opus, Sonnet, Haiku pricing, Fast mode, prompt caching, Batch API, long-context pricing, Managed Agents | `references/finops-anthropic.md` |
| GCP billing, Compute Engine, Cloud SQL, GCS, BigQuery billing export, BigQuery optimisation, FOCUS export, Sustained Use Discounts, SUDs, Committed Use Discounts, CUDs, Flexible CUDs, Spot VMs, Cloud Carbon Footprint | `references/finops-gcp.md` |
| GCP Vertex AI billing, Vertex provisioned throughput, Gemini pricing, Vertex batch prediction, default PAYG spillover | `references/finops-vertexai.md` |
| Tagging strategy, naming conventions, IaC enforcement, MCP governance | `references/finops-tagging.md` |
| FinOps framework 2026, 4 domains, 22 capabilities including Executive Strategy Alignment, Usage Optimization, Architecting & Workload Placement, Sustainability, KPIs & Benchmarking, Governance Policy & Risk, Automation Tools & Services, maturity model, phases, personas | `references/finops-framework.md` |
| Databricks clusters, jobs, Spark optimisation, Unity Catalog costs, allocation and governance, DBU executor attribution, DBCU commitments, Photon multiplier, serverless premium, amortised vs PAYG split, Azure VM RI vs DBU clarification | `references/finops-databricks.md` |
| Microsoft Fabric capacity FinOps, F-SKUs, Capacity Units, CU smoothing window, throttling, pause/resume, Reserved Capacity, Pro/PPU to Fabric migration governance, Capacity Metrics app, shared-capacity allocation | `references/finops-fabric.md` |
| Snowflake warehouses, query optimisation, storage, credits, QUERY_ATTRIBUTION_HISTORY, Budgets, Cortex governance, resource monitor scope | `references/finops-snowflake.md` |
| AI coding tools, Cursor costs, Claude Code costs, Copilot costs, Windsurf costs, Codex costs, dev tool FinOps, seat + usage billing, BYOK coding agents, LiteLLM proxy | `references/finops-ai-dev-tools.md` |
| OCI compute, storage, networking optimisation, Cost Reports, FOCUS Reports, cost-tracking tags, Budgets, Universal Credits | `references/finops-oci.md` |
| GreenOps, cloud carbon, sustainability, carbon-aware workloads | `references/greenops-cloud-carbon.md` |
| SaaS management, licence optimisation, shadow IT, SaaS sprawl, renewal governance, SMP, SAM | `references/finops-sam.md` |
| ITAM, IT asset management, BYOL, marketplace channel governance, licence compliance, vendor negotiation, FinOps-ITAM collaboration, entitlement management, consumption-based SaaS overages | `references/finops-itam.md` |
| Cost anomaly management, anomaly detection, masked anomalies, layered detection, threshold tuning, AWS Cost Anomaly Detection config, Azure anomaly detection, GCP budget anomaly alerts, new-region detection, security integration | `references/finops-anomaly-management.md` |
| Cost allocation methodology, showback, EffectiveCost vs BilledCost (FOCUS), amortised vs unblended (AWS legacy), blended-cost trap, defensible allocation keys, shared-services allocation (network, observability, security, ingress), InvoiceId reconciliation, unallocated spend signal, showback report design and routing | `references/finops-allocation-showback.md` |
| Chargeback, soft chargeback, hard chargeback, financial accountability, Finance and accounting prerequisites for chargeback, ERP readiness (SAP CO, Oracle, Workday, NetSuite), inter-BU P&L impact, CFO sponsorship, transfer pricing for intercompany cloud recharge, cross-border tax (VAT, withholding, permanent establishment, Pillar 2, GILTI / FDII / BEAT), SOX-equivalent controls, methodology dispute process, chargeback-revolt anti-pattern | `references/finops-chargeback.md` |
| Onboarding workloads, migration-time cost hygiene, intake gate, mandatory tags at go-live, 60-90 day forecast-then-commit rule, double-bubble cost (parallel-run source and target), migration cost estimate vs actuals, network-cost trap (data-centre to cloud), M&A integration patterns, FOCUS-during-migration, architecture review integration, post-migration FinOps owner | `references/finops-onboarding-workloads.md` |
| Kubernetes FinOps, K8s cost allocation, OpenCost, Kubecost, GKE Cost Allocation, EKS Split Cost Allocation, AKS Cost Analysis, FOCUS-emitting K8s allocation, container rightsizing (VPA, p95/p99 with safety margins), node-level autoscaling (Karpenter, Cluster Autoscaler), Pod Disruption Budgets, Spot diversification, idle node cost, node efficiency KPI | `references/finops-kubernetes.md` |
| Waste detection playbooks, orphaned resources, idle resources, overprovisioned resources, commitment mismatches, schedule blindness, modernization opportunities, AI/ML inefficiency, egress / data transfer waste, cross-AZ egress cost, two-signal classification, classification confidence (obvious / likely / possible), realised vs potential savings, WasteLine appliance, OptimNow waste taxonomy | `references/finops-waste-detection-playbooks.md` |
| Named waste pattern (e.g. zombie NAT, snapshot sprawl, idle ELB, cross-AZ egress, orphan Azure disks, Log Analytics ingestion sprawl, idle GKE Autopilot, idle SageMaker endpoint, oversized GPU instance, agent-loop flat-line burn) | `playbooks/<slug>.md` (see `playbooks/README.md` for the full pattern list) |
| Multi-domain query | Load all relevant references, synthesise |

### Reasoning sequence (apply to every response)

1. **Apply the OptimNow lens** - diagnose before prescribing, connect cost to value, recommend progressively (load `references/optimnow-methodology.md` in full only for strategy or engagement questions)
2. **Load** the domain reference(s) matching the query
3. **Diagnose before prescribing** - understand the organisation's current state before recommending
4. **Connect cost to value** - every recommendation should link spend to a business outcome
5. **Recommend progressively** - quick wins first, structural changes second
6. **Reference open-source FinOps tools** (FinOps Toolkit, OpenCost, Kubecost, Infracost, etc.) where they genuinely fit the problem
7. **Never quote an undated price** - see "Price figures" below

---

## Price figures (apply whenever a number is quoted)

Billing **mechanics** are durable and are what these references are for. Price
**figures** are volatile and go stale here within weeks. Treat the two differently.

1. **Prefer a live source.** If a pricing tool is available in the session (for
   example the OptimNow AI Pricing Hub: `compare-llm-models`, `estimate-llm-cost`,
   `compare-compute-pricing`), call it before quoting any token or instance price.
   If no such tool is available, point the user at <https://optimtoken.optimnow.io>
   rather than quoting from memory.
2. **Every figure carries its as-of date and source.** Write `$X per 1M input tokens
   (list price, <source>, <date>)`, not `$X per 1M input tokens`. A figure with no
   date cannot be used in a client deliverable.
3. **Figures inside these references are illustrative, not authoritative.** They exist
   to make a worked example concrete. The durable, quotable part is the *mechanics*:
   batch and cache-read multipliers, commitment term structure, the shape of a
   break-even calculation. Quote those with confidence; date the absolute numbers.
4. **Never interpolate.** If the live source has no figure for the model, SKU, or
   region asked about, say so. Do not derive one from a neighbouring model, a previous
   generation, or another region.

---

## Core FinOps principles (always apply)

These six principles from the FinOps Foundation (2026 framework) underpin every recommendation:

1. Teams need to collaborate
2. Business value drives technology decisions
3. Everyone takes ownership for their technology usage
4. FinOps data should be accessible, timely, and accurate
5. FinOps should be enabled centrally
6. Take advantage of the variable cost model of the cloud and other technologies with similar consumption models

---

## The three phases (Inform → Optimize → Operate)

FinOps is an iterative cycle, not a linear progression: Inform (visibility, allocation,
anomaly detection), Optimize (commitment discounts, rightsizing, unit economics),
Operate (governance and automation embedded in engineering and finance workflows).
See `references/finops-framework.md` for the full phase model.

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
