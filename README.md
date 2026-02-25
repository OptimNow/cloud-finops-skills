# cloud-finops-skill

> A comprehensive Cloud FinOps Agent Skill built by [OptimNow](https://optimnow.io).
> Provides expert, framework-aligned guidance on cloud financial management across
> AWS, Azure, GCP, Anthropic, Bedrock, Azure OpenAI, Vertex AI, Databricks, Snowflake,
> OCI, AI workloads, GenAI capacity planning, and tagging governance — grounded in
> hands-on enterprise delivery experience.

[![GitHub Stars](https://img.shields.io/github/stars/OptimNow/cloud-finops-skill?style=flat)](https://github.com/OptimNow/cloud-finops-skill/stargazers)
[![FinOps Framework](https://img.shields.io/badge/FinOps-Framework%202024-blue)](https://www.finops.org/framework/)
[![Agent Skills](https://img.shields.io/badge/Agent-Skills%20Spec-green)](https://agentskills.io/specification)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
- **Azure OpenAI Service** - PTU reservations, GPT model pricing, spillover, fine-tuning costs
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
        └── finops-oci.md                       ← OCI optimization
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

---

## Contributing

Contributions welcome. To suggest improvements:

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

## License

MIT License. See [LICENSE.md](./LICENSE.md).

This skill is independently maintained and is not affiliated with or endorsed by the
FinOps Foundation.
