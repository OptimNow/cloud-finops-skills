# cloud-finops-skill

> Built by [OptimNow](https://optimnow.io). Covers cloud financial management across
> AWS, Azure, GCP, AI inference costs, GenAI capacity planning, and tagging governance -
> grounded in enterprise delivery experience.

[![GitHub Stars](https://img.shields.io/github/stars/OptimNow/cloud-finops-skills?style=flat)](https://github.com/OptimNow/cloud-finops-skills/stargazers)
[![FinOps Framework](https://img.shields.io/badge/FinOps-Framework%202024-blue)](https://www.finops.org/framework/)
[![Agent Skills](https://img.shields.io/badge/Agent-Skills%20Spec-green)](https://agentskills.io/specification)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

---

## What is a Skill, and why does it matter

A Skill is a structured knowledge file that you attach to an AI agent or a large language
model. It gives the model accurate, domain-specific context that it would not otherwise
have access to.

Without it, general-purpose LLMs make confident but incorrect statements on FinOps topics.
They miscalculate PTU break-even rates. They confuse Azure and AWS reservation mechanics.
They give generic advice that ignores how billing actually works on Bedrock or Azure OpenAI.
The answers sound plausible. Most of the time, they are wrong on the details that matter.

This skill corrects that by injecting verified, curated FinOps knowledge directly into the
model's context - covering billing models, cost allocation patterns, optimisation
frameworks, and governance practices across the major cloud providers and AI platforms.

**The closest analogy is RAG (Retrieval-Augmented Generation).** Like RAG, it extends a
model's knowledge beyond its training data. Unlike RAG, it requires no vector database,
no embedding pipeline, and no retrieval infrastructure. You copy a folder into your agent
setup and the model gains structured expertise on cloud financial management.

This makes it portable: the same skill works with Claude, GPT-4, Gemini, or any
MCP-compatible agent - with no changes to the files.

---

## Who this is for

- **FinOps practitioners** building or evaluating AI-assisted cost analysis tools
- **Cloud engineers and architects** who want a cost-aware assistant integrated into
  their workflow
- **Developers** building internal FinOps agents, chatbots, or automation pipelines
- **Finance and IT managers** evaluating the AI tooling their teams are deploying

No AI infrastructure experience is required to use this skill. If you can copy a folder
and follow the installation steps, you can add FinOps expertise to any compatible agent.

---

## What this skill covers

The skill provides accurate, framework-aligned guidance across the following domains:

- **FinOps for AI** - LLM inference economics, token cost management, agentic cost
  patterns, unit economics for AI features, ROI frameworks, and AI cost governance
- **AI value management** - AI Investment Council, stage gate model, incremental
  funding, practice operations, cross-functional governance for AI investments
- **GenAI capacity planning** - provisioned vs shared capacity, traffic shape analysis,
  spillover mechanics, throughput units, cross-provider comparison
- **Anthropic billing** - Claude model pricing, Fast mode, long-context cliffs,
  prompt caching, Batch API, governance controls
- **AWS Bedrock** - model pricing, provisioned throughput, batch inference, cost allocation
- **Azure OpenAI Service** - PTU pool model, deployment locality, spillover mechanics,
  model modernisation, optimisation framework, use case economics, cost visibility
- **GCP Vertex AI** - Gemini pricing, provisioned throughput, batch prediction, cost visibility
- **AWS FinOps** - CUR setup, Cost Explorer, EC2 rightsizing, Reserved Instances vs
  Savings Plans, cost allocation, SCPs, and AWS-native quick wins
- **Azure FinOps** - Azure Cost Management, Reservations, Azure Policy, FinOps Toolkit,
  Azure Hybrid Benefit, and Azure-specific optimisation patterns
- **GCP FinOps** - Compute Engine, Cloud SQL, GCS, BigQuery, networking optimisation
- **Tagging governance** - tag taxonomy design, naming conventions, IaC enforcement,
  virtual tagging, MCP-based automation, and compliance monitoring
- **FinOps Framework** - full FinOps Foundation framework, 22 capabilities, maturity model
- **Databricks** - cluster optimisation, jobs, Spark, Unity Catalog costs
- **Snowflake** - warehouse optimisation, query tuning, storage, credits
- **OCI** - compute, storage, networking optimisation
- **GreenOps and cloud carbon** - carbon measurement tooling, FinOps-to-GreenOps
  integration, carbon-aware workload shifting, region selection, GHG Protocol reporting

All guidance is framed through OptimNow's methodology: connecting cost to business value,
diagnosing before prescribing, and recommending actions matched to organisational maturity.

---

## Design principles

- **AI cost management is a first-class domain.** Most FinOps resources treat AI workloads
  as an edge case. This skill treats them as a primary concern, with dedicated reference
  files for each major AI platform.
- **Visibility before optimisation.** The skill follows a consistent sequence: establish
  what you are spending, understand what is driving it, then act. It does not recommend
  optimisation steps before the visibility preconditions are met.
- **Practical over theoretical.** Guidance is based on how billing actually works and
  what has proven effective in enterprise delivery - not on what the documentation implies.
- **Maturity-sensitive.** Recommendations reflect the organisation's current state.
  A team with no cost allocation in place receives different guidance than a team
  evaluating cross-account chargeback models.
- **Tool-aware where relevant.** The skill references OptimNow's open-source tools
  (MCP for Tagging, AI ROI Calculator, FinOps Maturity Assessment) when they directly
  apply to the question at hand.

---

## Usage examples

These questions illustrate what this skill is designed to answer accurately.
A general-purpose LLM without this skill will produce plausible but unreliable answers
to most of them - particularly on billing mechanics, capacity economics, and
provider-specific behaviour.

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
- "Our traffic is bursty - does provisioned capacity make sense or should we stay on pay-as-you-go?"
- "What's the difference between spillover on Azure vs building failover logic on Bedrock?"
- "How do I calculate the break-even utilisation rate for provisioned throughput?"

### Anthropic billing

- "We're running Claude Sonnet on both AWS Bedrock and the direct Anthropic API. Our monthly bill jumped from $12K to $38K after a developer enabled Fast mode in Claude Code. How do I get this under control and prevent it from happening again?"
- "What's the real cost impact of the 200K input token long-context cliff?"
- "How do prompt caching multipliers work on Anthropic - when do cache writes cost more than they save?"
- "Should we route Claude traffic through Bedrock or use the direct Anthropic API?"

### AWS Bedrock

- "How does Bedrock provisioned throughput work and when does it make sense vs on-demand?"
- "What CloudWatch metrics should we monitor for Bedrock cost and performance?"
- "How do we tag and allocate Bedrock costs across teams when per-request tags aren't supported?"
- "What's the batch inference discount on Bedrock and which workloads should use it?"

### Azure OpenAI Service

- "How do PTU reservations work and what are the waste risks?"
- "We reserved 500 PTUs but only deployed 150 - how do we fix this?"
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
- "What are the quick wins I should address before any commitment purchase?"
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

### GreenOps and cloud carbon

- "We need to start reporting our cloud carbon emissions - where do we begin?"
- "How do we pick lower-carbon regions without sacrificing latency?"
- "What's the Carbon Aware SDK and can we use it to shift batch jobs to cleaner time windows?"
- "How do we add carbon tracking to our existing FinOps dashboards?"

---

## Directory structure

```
cloud-finops-skills/
├── README.md                                   ← This file
├── INSTALLATION.md                             ← Setup instructions
├── LICENSE.md                                  ← CC BY-SA 4.0
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
        ├── finops-databricks.md                ← Databricks optimisation
        ├── finops-snowflake.md                 ← Snowflake optimisation
        ├── finops-oci.md                       ← OCI optimisation
        └── greenops-cloud-carbon.md            ← GreenOps and cloud carbon
```

The `SKILL.md` file at the root of the `cloud-finops/` folder is the entry point. It
routes queries to the appropriate reference file based on the domain and question type.
The agent loads `SKILL.md` first; the reference files provide the domain-specific detail.

---

## Installation

See [INSTALLATION.md](./INSTALLATION.md) for detailed setup instructions.

**Quick start (Claude Code):**
```bash
cp -r cloud-finops /path/to/your/skills/directory/
```

**For Agent Smith (OptimNow's FinOps agent):**
The skill is pre-integrated. No manual installation required.

---

## This skill is actively maintained

This is a living repository. Reference files are updated regularly as cloud providers
change pricing, introduce new services, and evolve their billing models. AI cost
management is moving particularly fast - new model releases, capacity options, and
billing mechanics appear every few weeks.

Watch or star this repo to be notified when new content is added. Recent additions
include GreenOps/cloud carbon, AI value management, and GenAI capacity planning.

---

## Contributing

Contributions are welcome. If you spot an inaccuracy, a missing provider feature, or a
gap in coverage, open an issue or submit a pull request.

To suggest improvements:

1. Review the source material at [finops.org/framework](https://www.finops.org/framework/)
2. Identify gaps or inaccuracies in existing reference files
3. Submit a pull request with proposed changes
4. For new domains, follow the structure of an existing reference file as a template

---

## Adapting this skill for your organisation

Fork this repository and customise the reference files for your organisation's context:
your cloud stack, your internal policies, your tag taxonomy, your preferred methodology.

A fork gives you a stable base that you can pull upstream updates into at your own pace,
without overwriting your customisations. Typical customisations include:

- Adding organisation-specific tag requirements to `finops-tagging.md`
- Replacing generic pricing examples with your negotiated rates
- Adding reference files for internal tools or platforms not covered here
- Adjusting the methodology file to reflect your team's own approach

---

## About OptimNow

OptimNow is a boutique FinOps consultancy helping organisations connect cloud and AI
spend to measurable business value. Based in France with European reach.

- Website: [optimnow.io](https://optimnow.io)
- LinkedIn: [OptimNow](https://linkedin.com/company/optimnow)
- GitHub: [github.com/OptimNow](https://github.com/OptimNow)

**Open-source tools built by OptimNow:**
- [AI Cost Readiness Assessment](https://aicostsfinops.optimnow.io)
- [AI ROI Calculator](https://optimnow.io)
- [MCP for Tagging](https://github.com/OptimNow/finops-mcp)
- [FinOps Maturity Assessment](https://optimnow.io)

---

## Acknowledgements

This skill incorporates content derived from the following sources:

- **[FinOps Foundation](https://www.finops.org/)** - framework definitions, capability
  descriptions, and maturity model structure are based on the FinOps Framework.
- **[Point Five](https://www.pointfive.co)** - cloud optimisation recommendations
  informed several provider-specific best practices and quick-win patterns.

All referenced content has been adapted with additional context from OptimNow's
consulting delivery experience. Any errors or opinionated interpretations are our own.

This skill is independently maintained and is not affiliated with or endorsed by the
FinOps Foundation.

---

## License

Licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
See [LICENSE.md](./LICENSE.md).

You are free to use, adapt, and redistribute this skill - including for commercial
purposes - as long as you credit OptimNow and share any derivatives under the same license.
