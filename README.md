# cloud-finops-skill

> A comprehensive Cloud FinOps Agent Skill built by [OptimNow](https://optimnow.io).
> Provides expert, framework-aligned guidance on cloud financial management across
> AWS, Azure, GCP, Anthropic, Bedrock, Azure OpenAI, Vertex AI, Databricks, Snowflake,
> OCI, AI workloads, GenAI capacity planning, and tagging governance  - grounded in
> hands-on enterprise delivery experience.

[![GitHub Stars](https://img.shields.io/github/stars/OptimNow/cloud-finops-skill?style=flat)](https://github.com/OptimNow/cloud-finops-skill/stargazers)
[![FinOps Framework](https://img.shields.io/badge/FinOps-Framework%202024-blue)](https://www.finops.org/framework/)
[![Agent Skills](https://img.shields.io/badge/Agent-Skills%20Spec-green)](https://agentskills.io/specification)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

---

## What this skill provides

This skill enables AI agents to deliver expert FinOps guidance across multiple domains:

- **FinOps for AI** - LLM inference economics, token cost management, agentic cost
  patterns, unit economics for AI features, ROI frameworks, and AI cost governance
- **AI value management** - AI Investment Council, stage gate model, incremental
  funding, practice operations, cross-functional governance for AI investments
- **GenAI capacity planning** - provisioned vs shared capacity, traffic shape analysis,
  spillover mechanics, throughput units, cross-provider comparison
- **Anthropic billing** - Claude Opus, Sonnet, Haiku pricing, Fast mode, long-context
  cliffs, prompt caching, Batch API, governance controls
- **AWS Bedrock** - model pricing, provisioned throughput, batch inference, cost allocation
- **Azure OpenAI Service** - PTU pool model, deployment locality, spillover mechanics,
  model modernization, 4-lever optimization framework, use case economics, cost visibility
- **GCP Vertex AI** - Gemini pricing, provisioned throughput, batch prediction, cost visibility
- **AWS FinOps** - CUR setup, Cost Explorer, EC2 rightsizing, Reserved Instances vs
  Savings Plans, cost allocation, SCPs, and AWS-native quick wins
- **Azure FinOps** - Azure Cost Management, Reservations, Azure Policy for governance,
  FinOps Toolkit, Azure Hybrid Benefit, and Azure-specific optimization patterns
- **GCP FinOps** - Compute Engine, Cloud SQL, GCS, BigQuery, networking optimization
- **Tagging Governance** - tag taxonomy design, naming conventions, IaC enforcement,
  virtual tagging, MCP-based automation, and compliance monitoring
- **FinOps Framework** - full FinOps Foundation framework, 22 capabilities, maturity model
- **Databricks** - cluster optimization, jobs, Spark, Unity Catalog costs
- **Snowflake** - warehouse optimization, query tuning, storage, credits
- **OCI** - compute, storage, networking optimization
- **GreenOps & Cloud Carbon** - carbon measurement tooling, FinOps-to-GreenOps
  integration, carbon-aware workload shifting, region selection, GHG Protocol reporting

All guidance is framed through OptimNow's methodology: connecting cost to business value,
diagnosing before prescribing, and recommending progressive actions matched to
organizational maturity.

## What makes this skill different from generic FinOps resources

- **AI cost management** is a first-class domain, not an afterthought
- **OptimNow methodology** shapes reasoning - visibility before optimization,
  showback before chargeback, quick wins before structural change
- **Practical over theoretical** - real anti-patterns, real implementation steps,
  real decision frameworks
- **Tool-aware** - references OptimNow's open-source tools (MCP for Tagging,
  AI ROI Calculator, FinOps Maturity Assessment) where genuinely relevant
- **Maturity-sensitive** - recommendations match the organization's current state,
  not a generic best practice

---

## Directory structure

```
cloud-finops-skills/
├── README.md                                   ← This file
├── INSTALLATION.md                             ← Setup instructions
├── LICENSE.md                                  ← MIT
└── cloud-finops/                               ← Install this folder
    ├── SKILL.md                                ← Entry point + domain router
    └── references/
        ├── optimnow-methodology.md             ← OptimNow reasoning philosophy
        ├── finops-for-ai.md                    ← AI cost management
        ├── finops-ai-value-management.md       ← AI investment governance
        ├── finops-genai-capacity.md            ← GenAI capacity models (cross-provider)
        ├── finops-anthropic.md                 ← Anthropic billing + governance
        ├── finops-aws.md                       ← AWS-specific FinOps
        ├── finops-bedrock.md                   ← AWS Bedrock billing
        ├── finops-azure.md                     ← Azure-specific FinOps
        ├── finops-azure-openai.md              ← Azure OpenAI Service (PTUs)
        ├── finops-gcp.md                       ← GCP-specific FinOps
        ├── finops-vertexai.md                  ← GCP Vertex AI billing
        ├── finops-tagging.md                   ← Tagging and naming governance
        ├── finops-framework.md                 ← Full FinOps Foundation framework
        ├── finops-databricks.md                ← Databricks optimization
        ├── finops-snowflake.md                 ← Snowflake optimization
        ├── finops-oci.md                       ← OCI optimization
        └── greenops-cloud-carbon.md            ← GreenOps & cloud carbon
```

---

## Installation

See [INSTALLATION.md](./INSTALLATION.md) for detailed instructions.

**Quick start (Claude Code):**
```bash
cp -r cloud-finops /path/to/your/skills/directory/
```

**For Agent Smith (OptimNow's FinOps agent):**
The skill is pre-integrated into Agent Smith. No manual installation required.

---

## Usage examples

### FinOps for AI

- "We're spending $40K/month on AWS Bedrock and have no idea which features are driving it. Where do we start?"
- "How do I calculate ROI for our AI support bot?"
- "Our inference costs doubled last month - what are the most likely causes?"
- "Should we use Claude Haiku or Sonnet for our classification pipeline?"

### AI value management

- "We have 14 AI projects running across the company and no one knows the total spend. Our CFO wants a governance framework by next quarter."
- "How should we structure an AI Investment Council?"
- "What stage gate model works for AI projects that move faster than our quarterly review cycle?"
- "How do we fund AI experiments incrementally without runaway exposure?"

### GenAI capacity planning

- "We need to choose between Azure OpenAI PTUs and AWS Bedrock provisioned throughput for a production chatbot doing 500K requests/day."
- "Our traffic is bursty  - does provisioned capacity make sense or should we stay on pay-as-you-go?"
- "What's the difference between spillover on Azure vs building failover logic on Bedrock?"
- "How do I calculate the break-even utilization rate for provisioned throughput?"

### Anthropic billing

- "Our Anthropic bill jumped from $12K to $38K after a developer enabled Fast mode in Claude Code. How do I prevent this?"
- "What's the real cost impact of the 200K input token long-context cliff?"
- "How do prompt caching multipliers work on Anthropic  - when do cache writes cost more than they save?"
- "Should we route Claude traffic through Bedrock or use the direct Anthropic API?"

### AWS Bedrock

- "How does Bedrock provisioned throughput work and when does it make sense vs on-demand?"
- "What CloudWatch metrics should we monitor for Bedrock cost and performance?"
- "How do we tag and allocate Bedrock costs across teams when per-request tags aren't supported?"
- "What's the batch inference discount on Bedrock and which workloads should use it?"

### Azure OpenAI Service

- "How do PTU reservations work and what are the waste risks?"
- "We reserved 500 PTUs but only deployed 150  - how do we fix this?"
- "Is provisioned capacity on Azure OpenAI actually cheaper than pay-as-you-go for GPT-5?"
- "How does spillover work on Azure OpenAI and how do we monitor the PAYG overflow cost?"

### GCP Vertex AI

- "What's the cost difference between Gemini Flash and Gemini Pro on Vertex AI for a classification pipeline?"
- "How does provisioned throughput on Vertex AI compare to Bedrock and Azure?"
- "What Cloud Monitoring metrics should we track for Vertex AI cost visibility?"
- "When should we use Vertex AI Batch Prediction instead of on-demand inference?"

### AWS FinOps

- "We have $80K/month in EC2. Should we buy Reserved Instances or Savings Plans?"
- "How do I set up CUR for multi-account cost allocation?"
- "What are the quick wins I should do before any commitment purchase?"
- "How do I enforce mandatory tags without breaking existing deployments?"

### Azure FinOps

- "What's the Azure equivalent of AWS CUR?"
- "How do Azure Reservations compare to Azure Savings Plans?"
- "We need to enforce tagging across 15 subscriptions - what's the right approach?"
- "How do we use Azure Hybrid Benefit to reduce our VM costs?"

### Tagging governance

- "What are the minimum mandatory tags we should require?"
- "How do we enforce tags without blocking deployments?"
- "What's the difference between physical and virtual tagging?"
- "How does OptimNow's MCP for Tagging work?"

### GreenOps & cloud carbon

- "We need to start reporting our cloud carbon emissions  - where do we begin?"
- "How do we pick lower-carbon regions without sacrificing latency?"
- "What's the Carbon Aware SDK and can we use it to shift batch jobs to cleaner time windows?"
- "How do we add carbon tracking to our existing FinOps dashboards?"

---

## Contributing

This skill is actively evolving. Cloud providers update pricing, release new models,
and change capacity mechanics regularly  - and so do we. Expect frequent updates to
reference files, new domains, and expanded coverage over time.

**Fork this repo** to customize the skill for your organization's specific cloud
stack, internal policies, or preferred methodology. A fork gives you a stable base
that you can pull upstream updates into at your own pace.

To suggest improvements to the upstream skill:

1. Review the source material at [finops.org/framework](https://www.finops.org/framework/)
2. Identify gaps or inaccuracies in existing reference files
3. Submit a pull request with proposed changes
4. For new domains, follow the structure of existing reference files

---

## About OptimNow

OptimNow is a boutique FinOps consultancy helping organizations connect cloud and AI
spend to measurable business value. Based in France with European reach.

- Website: [optimnow.io](https://optimnow.io)
- LinkedIn: [OptimNow](https://linkedin.com/company/optimnow)
- GitHub: [github.com/OptimNow](https://github.com/OptimNow)

**Tools built by OptimNow:**
- [AI Cost Readiness Assessment](https://aicostsfinops.optimnow.io)
- [AI ROI Calculator](https://optimnow.io)
- [MCP for Tagging](https://github.com/OptimNow/finops-mcp)
- [FinOps Maturity Assessment](https://optimnow.io)

---

## Acknowledgements

This skill incorporates content derived from the following sources:

- **[FinOps Foundation](https://www.finops.org/)**  - framework definitions, capability
  descriptions, and maturity model structure are based on the FinOps Framework.
- **[Point Five](https://www.pointfive.co)**  - cloud optimization recommendations
  library informed several provider-specific best practices and quick-win patterns.

All referenced content has been adapted with additional context from OptimNow's
consulting delivery experience. Any errors or opinionated interpretations are our own.

---

## License

This work is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
See [LICENSE.md](./LICENSE.md).

You are free to use, adapt, and redistribute this skill  - including for commercial
purposes  - as long as you credit OptimNow and share any derivatives under the same
license.

This skill is independently maintained and is not affiliated with or endorsed by the
FinOps Foundation.
