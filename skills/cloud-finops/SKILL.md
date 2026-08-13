---
name: cloud-finops
description: >
  Expert FinOps guidance covering cloud, AI, and SaaS technology spend. Includes AI cost
  management, GenAI capacity planning, self-hosted vs managed inference,
  Anthropic billing, AWS (EC2, Bedrock, SageMaker, GPU rightsizing, Savings Plans,
  CUR, commitment strategy), Azure (reservations, Savings Plans, AHB, OpenAI PTUs, portfolio
  liquidity), GCP (Vertex AI, Compute Engine, BigQuery), tagging governance, SaaS management
  (SAM, licence optimisation, SMPs, shadow IT), AI coding tools (Cursor, Claude Code,
  Copilot, Windsurf, Codex), ITAM, data platforms (Databricks allocation and governance with
  DBCU commitments, Microsoft Fabric capacity FinOps with F-SKUs, CU smoothing, reservations,
  pause/resume, Pro-to-Fabric migration), Snowflake, OCI, and GreenOps (AWS Sustainability
  Console, CSRD). Use for any query about technology cost,
  commitment portfolio management, rightsizing, cost allocation, SaaS sprawl, AI dev tool spend,
  or connecting spend to business value. Built by OptimNow.
---

# FinOps - Expert Guidance

> Built by OptimNow. Grounded in hands-on enterprise delivery, not abstract frameworks.

---

## How to use this skill

This skill covers cloud, AI, SaaS, and adjacent technology spend domains. Apply the
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
| AWS billing data, CUR, Data Exports for FOCUS 1.2, Cost Explorer, EC2/compute rightsizing, SageMaker operational FinOps, cost allocation, governance, CloudFront flat-rate plans, S3 Files, multi-org billing, expensive IAM actions, cost-preventive SCPs, deny high-cost actions, sandbox account guardrails | `references/finops-aws.md` |
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

---

## Core FinOps principles (always apply)
<!-- fp:37b46c22605776cb -->

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

> *FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
