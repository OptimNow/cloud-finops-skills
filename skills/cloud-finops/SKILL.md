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

This skill covers cloud, AI, SaaS, and adjacent technology spend domains. Use
`references/optimnow-methodology.md` as a reasoning lens (diagnose before prescribing,
connect cost to value, recommend progressively); then load the domain reference(s)
matching the query.

### Domain routing

| Query topic | Load reference |
|---|---|
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
| Waste detection playbooks, orphaned resources, idle resources, overprovisioned resources, commitment mismatches, schedule blindness, modernization opportunities, AI/ML inefficiency, two-signal classification, classification confidence (obvious / likely / possible), realised vs potential savings, WasteLine appliance, OptimNow waste taxonomy | `references/finops-waste-detection-playbooks.md` |
| Named waste pattern (zombie NAT, snapshot sprawl, idle ELB, cross-AZ egress, oversized RDS, orphan EBS, orphan Azure disks, App Service overprovisioning, Log Analytics ingestion sprawl, idle Azure SQL, idle GKE Autopilot, orphan Persistent Disks, Cloud Functions cold starts, schedule blindness, untagged spend drift, idle SageMaker endpoint, always-on SageMaker notebook, SageMaker endpoint sprawl / MME consolidation, oversized GPU instance, multi-GPU underutilized, MIG candidate, GPU for CPU-bound workload, outdated GPU generation, agent-loop flat-line burn, coding-agent token waste) | `playbooks/<slug>.md` (see `playbooks/README.md` for the full list) |
| Multi-domain query | Load all relevant references, synthesize |

### Reasoning sequence (apply to every response)

1. **Apply the methodology lens** (`references/optimnow-methodology.md`) - diagnose before prescribing, connect cost to value, recommend progressively
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

## Reference files

| File | Contents |
|---|---|
| `optimnow-methodology.md` | OptimNow reasoning philosophy, 4 pillars, engagement principles, tools |
| `finops-for-ai.md` | AI cost management, LLM economics, harness cost surface, unit economics, ROI framework, GPU telemetry (DCGM metric reference, "GPU utilization is misleading") |
| `finops-agentic.md` | Agentic FinOps: workflow vs pipeline vs true agent cost behaviour, agentic cost anatomy, cost-safe agent architecture, agent-initiated payments (x402 / MPP) |
| `finops-ai-value-management.md` | AI investment governance: AI Investment Council, stage gates, incremental funding, practice operations, value metrics |
| `finops-genai-capacity.md` | GenAI capacity models: provisioned vs shared, traffic shape, spillover (incl. Vertex AI default-PAYG), waste types, cross-provider comparison |
| `finops-ai-self-hosted-vs-managed.md` | Self-hosted vs managed AI inference: per-token vs per-hour billing, hidden cost surface (operational, reliability, compliance, talent), 5-criteria maturity rubric, hybrid routing patterns, eight client diagnostic questions, six anti-patterns |
| `finops-aws.md` | AWS FinOps core: CUR + Data Exports for FOCUS 1.2, Cost Explorer hourly + resource-level, compute rightsizing entry points, SageMaker operational FinOps (billed-while-idle, deployment pattern selection, MME / Inference Components, notebook hygiene), cost allocation, governance tools, quick wins, database cost optimisation, CloudFront flat-rate plans, S3 Files, multi-organisation billing |
| `finops-aws-commitments.md` | AWS commitment discounts: Savings Plans (Compute, EC2 Instance, SageMaker AI, Database), Reserved Instances incl. Convertible terms, Spot, the commitment decision tree, portfolio liquidity and phased purchasing, EDP negotiation |
| `finops-aws-patterns.md` | AWS optimisation pattern catalogue: the enumerated per-service inefficiency list with signal and remediation. A lookup surface - prefer `playbooks/aws-*.md` for named patterns with runnable detection |
| `finops-bedrock.md` | AWS Bedrock: model pricing, provisioned throughput, Application Inference Profiles, Bedrock Projects, prompt caching with 1-hour TTL, IAM Principal Cost Allocation, CloudWatch metrics, cost allocation |
| `finops-azure.md` | Azure FinOps core: Cost Management and FOCUS exports, Retail Prices API, compute rightsizing (VM cost model and SKU naming through Advisor calibration and the band Advisor misses), Log Analytics 5-lever cost control, snapshot/backup management, AKS in depth (NAP, Azure Linux 2), database optimisation, tagging and Azure Policy governance, storage tiering, networking cost, cost allocation, agentic FinOps, EA-to-MCA contractual mechanics |
| `finops-azure-commitments.md` | Azure commitment discounts: Reservations, Savings Plans, Azure Hybrid Benefit, Spot, compute and database commitment decision trees, portfolio liquidity under the 1 February 2027 exchange retirement, phased purchasing, MACC alignment, commitment sizing methodology |
| `finops-azure-patterns.md` | Azure optimisation pattern catalogue: the enumerated per-service inefficiency list with signal and remediation. A lookup surface - prefer `playbooks/azure-*.md` for named patterns with runnable detection |
| `finops-azure-openai.md` | Azure OpenAI / AI Foundry: PTU reservations (locality constraint), reservation discount path, spillover, GPT model pricing, prompt caching, fine-tuning costs |
| `finops-anthropic.md` | Anthropic billing: Claude Opus/Sonnet/Haiku pricing, Fast mode and Managed Agents (flagged emerging-assumption), per-model long-context picture, prompt caching, Batch API, governance |
| `finops-gcp.md` | GCP FinOps: cost-data foundations (Cloud Billing console, BigQuery billing export standard / detailed / pricing, FOCUS export, Pricing API), Sustained Use Discounts, Committed Use Discounts (resource-based vs Flexible/spend-based with current 28%/46% depths), Compute SKU vCPU/RAM split, Spot VMs, BigQuery commitment model, Cloud Carbon Footprint location-based vs market-based, GKE cost attribution, 26 inefficiency patterns |
| `finops-vertexai.md` | GCP Vertex AI billing: Gemini pricing, provisioned throughput (default-PAYG spillover), batch prediction, Cloud Monitoring metrics |
| `finops-tagging.md` | Tagging strategy, IaC enforcement, virtual tagging, MCP automation |
| `finops-framework.md` | FinOps Foundation framework 2026 (4 domains, 22 capabilities including the new Executive Strategy Alignment and the renames Workload Optimization -> Usage Optimization, Architecting for Cloud -> Architecting & Workload Placement, Cloud Sustainability -> Sustainability, Benchmarking -> KPIs & Benchmarking, Policy & Governance -> Governance, Policy & Risk, FinOps Tools & Services -> Automation, Tools & Services), personas, principles, phases |
| `finops-databricks.md` | Databricks FinOps: cost data foundations (system.billing.usage, budget policies, serverless and model-serving attribution), allocation and governance (workspace + DBU executor patterns, Azure VM RI vs DBU clarification, DBCU commitments, Photon and serverless multipliers, amortised vs PAYG split, monthly cadence, sequencing), 18 inefficiency patterns |
| `finops-fabric.md` | Microsoft Fabric capacity FinOps: F-SKU model, Capacity Units and 24-hour CU smoothing, throttling behaviour, manual pause / resume, Reserved Capacity, Pro/PPU to Fabric migration governance trap, shared-capacity allocation models, Capacity Metrics app, Pro vs PPU vs F-SKU breakeven |
| `finops-snowflake.md` | Snowflake FinOps: credit model, modern cost-management primitives (QUERY_ATTRIBUTION_HISTORY, Budgets including AI feature budgets, resource-monitor scope limit, Cortex governance), 13 optimisation patterns |
| `finops-ai-dev-tools.md` | AI coding tools: Cursor (Pro/Ultra/Teams/Enterprise), Claude Code, GitHub Copilot (transition to AI Credits 1 June 2026), Windsurf, OpenAI Codex (incl. GPT-5.5), billing models, cost attribution, optimisation levers |
| `finops-oci.md` | OCI FinOps: cost-data foundations (Cost Reports, FOCUS Reports, cost-tracking tags, OCI Budgets, Universal Credits) and 6 inefficiency patterns |
| `finops-sam.md` | SaaS asset management: discovery, licence optimisation, renewal governance, SMPs, shadow IT, AI transition |
| `finops-itam.md` | FinOps-ITAM collaboration: BYOL mechanics, marketplace channel governance, vendor co-management, consumption monitoring, joint operating model |
| `greenops-cloud-carbon.md` | GreenOps: carbon measurement, carbon-aware workloads, region selection, GHG Protocol |
| `finops-anomaly-management.md` | Cost anomaly management as a standalone Inform-phase capability: native tooling per cloud (AWS Cost Anomaly Detection, Azure Cost Management, GCP Budgets), threshold philosophy (absolute dollars + percentage), layered detection across service / region / account / tag, the masked-anomaly failure mode, new-region detection, Security integration, Crawl/Walk/Run progression |
| `finops-allocation-showback.md` | Cost allocation and showback. FOCUS cost columns (EffectiveCost vs BilledCost) with AWS legacy mapping (amortised / unblended) and blended-cost trap warning. Defensible allocation keys table, shared-services hard cases (network, observability, security, ingress), InvoiceId reconciliation, unallocated > 10% as tagging signal, showback report design and routing, data-quality dispute process, Crawl/Walk/Run progression |
| `finops-chargeback.md` | Chargeback as a distinct discipline from allocation. Soft-to-hard chargeback maturity ladder, Finance and accounting prerequisites for hard chargeback (ERP readiness in SAP CO / Oracle / Workday / NetSuite, inter-BU P&L impact and incentive alignment, transfer pricing for intercompany recharges, cross-border tax incl. VAT / Pillar 2 / GILTI, SOX-equivalent controls), decision-owner table mapping prerequisites to Finance roles, methodology dispute process, chargeback-revolt anti-pattern, Walk/Run progression. Strict prerequisite is finops-allocation-showback.md |
| `finops-onboarding-workloads.md` | Migration-time cost hygiene. Intake gate that prevents new workloads landing untagged / unallocated / unforecast (mandatory checklist + three implementation patterns: PR gate, cutover gate, pre-prod gate), the 60-90 day forecast-then-commit rule for fresh workloads (and exceptions), double-bubble cost (source + target parallel-run) with explicit shutoff discipline, migration-cost-estimate-vs-actuals trap (network-cost differences between data-centre and cloud), M&A integration playbook (months 1-12 sequence), FOCUS-during-migration logic, cost-aware architecture review integration, post-migration FinOps owner |
| `finops-kubernetes.md` | Kubernetes as the cross-cluster discipline (EKS / GKE / AKS). Tooling choice (OpenCost / Kubecost / cloud-native), FOCUS-emitting K8s allocation with K8s-labels-to-FOCUS-Tags mapping, container rightsizing methodology (VPA recommendation-only, p99 + 30% memory safety, p95 + 50% CPU safety, per-workload rollout), node-level autoscaling (Karpenter > CA where available, consolidation tuning, PDB requirements, Spot diversification across instance types and AZs), idle node cost as Platform overhead. Provider-specific deep cuts stay in finops-aws.md / finops-azure.md / finops-gcp.md |
| `finops-waste-detection-playbooks.md` | OptimNow's eight-category waste taxonomy (orphaned, idle, overprovisioned, commitment mismatches, schedule blindness, modernization, AI/ML inefficiency, egress / data transfer) with patterns and detection examples per category. Two-signal classification rule, three-tier confidence (obvious / likely / possible), realised vs potential savings discipline. Operational tooling: WasteLine appliance for AWS (49 detection rules across Categories 1-7, read-only, proposal-only remediation; egress is doctrine-only); for Azure and GCP, points to in-cloud catalogues. Category 7 (AI/ML) cross-links to dedicated playbooks for SageMaker and GPU waste patterns. Crawl/Walk/Run progression from manual quarterly hunt to continuous Fargate-scheduled detection |

---

> *FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
