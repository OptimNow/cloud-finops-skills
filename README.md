# Cloud FinOps Skill & MCP

> Open-source FinOps knowledge skill and MCP server for AI agents - Claude, ChatGPT,
> Gemini, Cursor, and any MCP-compatible client. Cloud cost optimisation across AWS,
> Azure, GCP and OCI, AI cost management and inference economics, Kubernetes, data
> platforms, allocation, chargeback, anomaly management, and named-pattern waste
> detection playbooks.
> Built by [OptimNow](https://optimnow.io), grounded in enterprise delivery experience.

[![GitHub Stars](https://img.shields.io/github/stars/OptimNow/cloud-finops-skills?style=flat)](https://github.com/OptimNow/cloud-finops-skills/stargazers)
[![PyPI](https://img.shields.io/pypi/v/cloud-finops-mcp?label=cloud-finops-mcp)](https://pypi.org/project/cloud-finops-mcp/)
[![Latest release](https://img.shields.io/github/v/release/OptimNow/cloud-finops-skills?label=release)](https://github.com/OptimNow/cloud-finops-skills/releases/latest)
[![FinOps Framework](https://img.shields.io/badge/FinOps-Framework-blue)](https://www.finops.org/framework/)
[![Agent Skills](https://img.shields.io/badge/Agent-Skills%20Spec-green)](https://agentskills.io/specification)
[![Kiro Power](https://img.shields.io/badge/Kiro-Power-orange)](https://kiro.dev/docs/powers/installation/)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

---

## Install in 5 seconds

| Tool | One-step install |
|---|---|
| <img src="https://img.shields.io/badge/-Claude%20Code-D97757?logo=anthropic&logoColor=white" alt="Claude Code" height="22"/> | At the Claude Code prompt: `/plugin marketplace add https://github.com/OptimNow/cloud-finops-skills.git` then `/plugin install cloud-finops@optimnow` |
| <img src="https://img.shields.io/badge/-Claude.ai%20%2F%20Desktop-D97757?logo=anthropic&logoColor=white" alt="Claude.ai / Claude Desktop" height="22"/> | [Download the latest release zip](https://github.com/OptimNow/cloud-finops-skills/releases/latest), then **Settings -> Skills -> Upload zip** |
| <img src="https://img.shields.io/badge/-ChatGPT-10A37F?logo=openai&logoColor=white" alt="ChatGPT" height="22"/> | Self-host: `./install.sh --tool chatgpt --grouped` _(a public Cloud FinOps GPT is on the Roadmap)_ |
| <img src="https://img.shields.io/badge/-Gemini-4285F4?logo=googlegemini&logoColor=white" alt="Gemini" height="22"/> | Self-host: `./install.sh --tool gemini` _(a public Cloud FinOps Gem is on the Roadmap)_ |
| <img src="https://img.shields.io/badge/-Cursor-000000?logo=cursor&logoColor=white" alt="Cursor" height="22"/> <img src="https://img.shields.io/badge/-Windsurf-3DDC91?logoColor=white" alt="Windsurf" height="22"/> <img src="https://img.shields.io/badge/-Codex-412991?logo=openai&logoColor=white" alt="Codex" height="22"/> <img src="https://img.shields.io/badge/-Aider-0F172A?logoColor=white" alt="Aider" height="22"/> <img src="https://img.shields.io/badge/-Copilot-181717?logo=githubcopilot&logoColor=white" alt="Copilot" height="22"/> <img src="https://img.shields.io/badge/-Kiro%20IDE-FF6F00?logoColor=white" alt="Kiro IDE" height="22"/> <img src="https://img.shields.io/badge/-Gemini%20CLI-4285F4?logo=googlegemini&logoColor=white" alt="Gemini CLI" height="22"/> | One-liner: `curl -sL https://raw.githubusercontent.com/OptimNow/cloud-finops-skills/main/install.sh \| bash -s -- --tool <name>` |
| <img src="https://img.shields.io/badge/-Auto--detect-555555?logo=gnubash&logoColor=white" alt="Auto-detect" height="22"/> | `curl -sL https://raw.githubusercontent.com/OptimNow/cloud-finops-skills/main/install.sh \| bash` |
| <img src="https://img.shields.io/badge/-MCP%20hosted-7C3AED?logoColor=white" alt="MCP hosted" height="22"/> | Nothing to install: `claude mcp add --transport http cloud-finops https://cloud-finops-skills-590a051d.alpic.live/`. For Claude.ai / Desktop, **Settings -> Connectors -> Add custom connector** with exactly that URL (trailing slash included - the widget sandbox domain is derived from it) |
| <img src="https://img.shields.io/badge/-MCP%20package-7C3AED?logoColor=white" alt="MCP package" height="22"/> | `pip install cloud-finops-mcp` then add to your MCP client config (Claude Code / Cursor / Codex / Windsurf / Cline). Snippets: `./install.sh --tool mcp` |

Full options, troubleshooting, and the model-agnostic API loader: see
[INSTALLATION.md](./INSTALLATION.md). A version-tagged zip
(`cloud-finops-vX.Y.Z.zip`) is attached to every
[GitHub release](https://github.com/OptimNow/cloud-finops-skills/releases).

---

## What is a Skill? What is an MCP server?

**A Skill** is a structured knowledge folder you attach to an AI agent. Without it,
general-purpose LLMs make confident but incorrect statements on FinOps topics - they
miscalculate PTU break-even rates, confuse Azure and AWS reservation mechanics, and give
advice that ignores how billing actually works. The answers sound plausible; they are
wrong on the details that matter. The skill corrects that by injecting verified, curated
FinOps knowledge directly into the model's context. The closest analogy is RAG, minus
the infrastructure: no vector database, no embedding pipeline - you copy a folder and
the model gains structured expertise. The same files work with Claude, GPT, Gemini, or
any other model.

**An MCP server** (MCP: Model Context Protocol, the open standard that lets an AI
client call external tools at run time) exposes the same library the other way round -
as read-only tools the model queries on demand. Actual retrieval: one URL to paste,
nothing to install.

**Who this is for:** FinOps practitioners building or evaluating AI-assisted cost
analysis, cloud engineers who want a cost-aware assistant in their workflow, developers
building internal FinOps agents, and Finance / IT managers evaluating the AI tooling
their teams deploy. If you can copy a folder and follow the installation steps, you can
use this.

## Skill + installer, or MCP?

Same content, two delivery shapes - and they behave differently, because of how models
use them (field-tested with the same battery of practitioner questions through both):

- **Pushed into context** - as a native skill (Claude Code, Claude.ai / Desktop, Kiro),
  or as rules files written by `install.sh` for tools without skill support (Cursor,
  Windsurf, Codex, Aider, Copilot, Gemini). The guidance is already there when the
  model reasons, which is what grounds *advisory* answers - commitment sizing,
  chargeback design, allocation methodology - without the model having to decide
  anything.
- **Fetched on demand** - the MCP server. The model must decide to call a tool, which
  it reliably does for lookup questions ("show me the idle waste runbooks") and much
  less for advisory ones. Its strengths: distribution (paste one URL - the right path
  for non-technical users and for hosts with neither skill support nor an installer
  target), faceted queries over the library's metadata, and interactive widgets on
  hosts that render MCP Apps.
- **Both is legitimate.** Skill loaded for the doctrine, connector added for the
  widgets or for hosts where the skill is not loaded. Details on the six tools:
  [MCP server](#mcp-server-cross-tool-search-style-retrieval) below.

Using a non-Claude model through an API? Add the **response contract** from
[INSTALLATION.md](./INSTALLATION.md) ("API integration / Recommended response
contract") to your system prompt so answers stay structured and billing-grounded.

---

## Live prices come from OptimToken, not from this repo

This skill carries billing **mechanics**, which stay true for years. It deliberately
does not carry current price **figures**, which go stale inside a packaged skill within
weeks. Those live in **[OptimToken](https://optimtoken.optimnow.io)** - LLM token rates
for 250+ models and compute instance rates across seven clouds, each figure carrying
its own as-of date:

| | |
|---|---|
| <img src="https://img.shields.io/badge/-OptimToken%20web-7C3AED?logoColor=white" alt="OptimToken web" height="22"/> | [optimtoken.optimnow.io](https://optimtoken.optimnow.io) - compare model and instance prices in the browser, no setup |
| <img src="https://img.shields.io/badge/-OptimToken%20MCP-7C3AED?logoColor=white" alt="OptimToken MCP" height="22"/> | Hosted, nothing to install. Point your client at `https://ai-pricing-hub-mcp-9604f763.alpic.live/` - config snippets in [INSTALLATION.md](./INSTALLATION.md#companion-connector-optimnow-ai-pricing-hub-optional) |

**Recommended setup on Claude:** install the skill and add the OptimToken connector
next to it. The skill carries the doctrine and routes pricing questions to the hub,
so they get answered with a dated figure and its source rather than from a number the
model remembers.

---

## What this skill covers

| Domain family | What is covered |
|---|---|
| **AI & GenAI economics** | FinOps for AI (inference economics, unit economics, ROI), agentic FinOps (agent cost anatomy, x402 / MPP), AI value management (Investment Council, stage gates), GenAI capacity planning (provisioned vs shared, spillover), self-hosted vs managed inference, open-weight vendor APIs (DeepSeek, Qwen, Kimi, GLM), AI coding tools (Cursor, Claude Code, Copilot, Windsurf, Codex) |
| **AI platform billing** | Anthropic (Fast mode, long-context cliffs, prompt caching), AWS Bedrock, Azure OpenAI Service (PTUs, spillover), GCP Vertex AI |
| **Cloud providers** | AWS (CUR / Data Exports, rightsizing, SageMaker, Savings Plans / RIs / EDP, billing hierarchy and separate invoices per business unit, pattern catalogue), Azure (Cost Management, Reservations, AHB, EA-to-MCA, pattern catalogue), GCP (CUDs, BigQuery), OCI |
| **Data platforms** | Databricks (DBU / DBCU, allocation), Microsoft Fabric (F-SKUs, CU smoothing), Snowflake (warehouses, Cortex governance) |
| **FinOps disciplines** | The FinOps Framework (22 capabilities, maturity model), tagging governance, allocation and showback (FOCUS), chargeback (Finance / tax prerequisites), anomaly management, KPIs and benchmarking, workload onboarding and M&A, Kubernetes (EKS / GKE / AKS) |
| **SaaS & licensing** | SaaS asset management (SMPs, shadow IT, renewals), ITAM collaboration (BYOL, marketplace governance, entitlements) |
| **GreenOps** | Cloud carbon measurement, carbon-aware workloads, region selection, GHG Protocol reporting |
| **Waste detection** | OptimNow's eight-category waste taxonomy, two-signal classification, three-tier confidence, WasteLine appliance for AWS - plus named-pattern runbooks across AWS, Azure, GCP and cross-cloud (full catalogue in [playbooks/README.md](./skills/cloud-finops/playbooks/README.md)) |

The per-file catalogue with routing lives in
[SKILL.md](./skills/cloud-finops/SKILL.md) - one row per reference, one row per
playbook family.

### Coverage, published deliberately

Coverage has two structural surfaces, answering different questions. The first is the
**named waste-pattern runbooks**: which specific, detectable waste patterns have a
ready-made playbook, per provider. A dashed cell is a known hole in the *runbook*
catalogue, with its prioritised backlog public in [docs/ROADMAP.md](docs/ROADMAP.md) -
it does not mean the skill cannot answer on that theme, because the reference library
covers the underlying mechanics even where no runbook exists.

![Waste-playbook runbook coverage heat map](assets/playbook-coverage.svg)

The second surface is the **reference library mapped to the FinOps Framework**: which
of the 22 Framework capabilities have a reference that owns them. This is where
commitment strategy, chargeback, allocation and the other advisory themes live - none
of which need a runbook to be answerable.

![FinOps Framework capability coverage](assets/fcp-coverage.svg)

Both maps regenerate from file frontmatter and CI fails if either drifts (details in
[playbook-coverage.md](playbook-coverage.md) and [fcp-coverage.md](fcp-coverage.md)).
A third, behavioural surface - does the library actually ground answers to real
practitioner questions - is measured with a rotating probe battery on the maintainer
side; gaps it finds land in the same public backlog.

---

## Design principles

- **AI cost management is a first-class domain.** Most FinOps resources treat AI
  workloads as an edge case. This skill treats them as a primary concern, with
  dedicated reference files for each major AI platform.
- **Visibility before optimisation.** The skill follows a consistent sequence:
  establish what you are spending, understand what is driving it, then act. It does
  not recommend optimisation steps before the visibility preconditions are met.
- **Provider-mechanics-first, vendor-claim-skeptical.** Guidance is grounded in how
  billing actually works (CUR columns, Azure cost-management semantics, BigQuery
  export, FOCUS conformance) rather than in vendor marketing or framework
  positioning. Vendor sustainability and savings claims are read critically, with
  primary sources cited.
- **Maturity is contextual, not aspirational.** Verticals where cloud is not a
  revenue generator do not need to reach Run; Crawl plus selective Walk is the right
  state when cloud is a cost centre. Verticals where cloud IS the product need Run
  because cloud efficiency directly drives gross margin. Pushing every organisation
  toward the same maturity ceiling is malpractice.
- **Connect cost to business value.** Every recommendation answers the CFO test:
  what business outcome does this protect or unlock. Cost reduction without a value
  lens is a leak.
- **Mechanics live here, price figures do not.** Billing mechanics are durable;
  absolute prices are volatile and go stale inside a packaged file. Current-price
  questions route to OptimToken (see above), and any figure a reference does quote
  carries its date and source inline.
- **FinOps is an operating discipline, not a culture.** The discipline lives in
  allocation, anomaly management, commitment management, rightsizing, and
  governance, all of which produce measurable outputs. "Culture of FinOps" framing
  tends to substitute slideware for those outputs. In the agentic era this matters
  more, not less: agents execute discipline, not culture.

These principles will grow into a `skills/cloud-finops/doctrine/` directory of
opposable theses with their own primary sources.

---

## Usage examples

These questions illustrate what the skill is designed to answer accurately - a
general-purpose LLM without it produces plausible but unreliable answers to most of
them, particularly on billing mechanics and capacity economics.

<div>
  <a href="https://www.loom.com/share/cc76d419adc64b1784e58621d6934d3e">
    <p>Cloud FinOps skill - Watch Video</p>
  </a>
  <a href="https://www.loom.com/share/cc76d419adc64b1784e58621d6934d3e">
    <img style="max-width:300px;" alt="Demo video: the Cloud FinOps skill answering practitioner questions in Claude" src="https://cdn.loom.com/sessions/thumbnails/cc76d419adc64b1784e58621d6934d3e-906aded8593a48f3-full-play.gif#t=0.1">
  </a>
</div>

- "We're spending $40K/month on AWS Bedrock and have no idea which features are driving it. Where do we start?"
- "How do I calculate the break-even utilisation rate for provisioned throughput - and should we choose Azure OpenAI PTUs or Bedrock provisioned capacity for 500K requests/day?"
- "Our monthly bill jumped from $12K to $38K after a developer enabled Fast mode in Claude Code. How do I get this under control?"
- "Should we self-host Llama 4 on rented H100s instead of paying per token - and what hidden costs do TCO calculators miss?"
- "We have $80K/month in EC2. Reserved Instances or Savings Plans - and what quick wins come first?"
- "Our client wants separate AWS invoices per business unit. Their AWS contact suggested Cost Categories - is that right?"
- "We're migrating from EA to MCA - what FinOps work do we need to do before the switch?"
- "Which VMs run for nothing, and which runbook finds them?"
- "We need to start reporting our cloud carbon emissions - where do we begin?"

---

## Directory structure

```
cloud-finops-skills/
├── README.md                    <- This file
├── INSTALLATION.md              <- Per-tool setup, troubleshooting, API loader
├── CLAUDE.md / AGENTS.md        <- Project context for AI assistants and contributors
├── llms.txt                     <- LLM discovery index (cross-agent)
├── install.sh                   <- Cross-tool installer (12 targets)
├── mcp_server/                  <- cloud-finops-mcp PyPI package
└── skills/cloud-finops/         <- The skill - install this folder
    ├── SKILL.md                 <- Entry point + per-file routing catalogue
    ├── POWER.md                 <- Kiro IDE entry point (same references)
    ├── references/              <- The reference library, one file per domain
    └── playbooks/               <- Named-pattern runbooks (~3-8 KB each) + catalogue
```

---

## MCP server (cross-tool, search-style retrieval)

Hosted (nothing to install) or from PyPI - both paths are in the
[install table](#install-in-5-seconds) above. Also listed on the
[MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=finops) as
`io.github.OptimNow/cloud-finops`, and on
[PyPI](https://pypi.org/project/cloud-finops-mcp/).

Six read-only tools across two surfaces. The split is deliberate: the two content
types have different shapes, and different questions attached to them.

**References** - the long-form provider and discipline files. Reach for these for
billing mechanics, commitment strategy, allocation methodology, or any reasoning that
spans patterns.

| Tool | What it answers |
|---|---|
| `list_references()` | What guidance exists? The catalogue with its FinOps Framework facets and an `approx_tokens` size hint per file |
| `get_reference(name, section?)` | One guide - mechanics, decision rules, worked examples. Whole, or a single H2/H3 section when the question is narrower than the file |
| `find_references(domain?, capability?, phase?, persona?, maturity?, persona_primary_only?)` | "How should we size Savings Plans?" "What must be true before chargeback?" - routes a FinOps question to the guides that serve it (`persona_primary_only` cuts to the primary audience) |

**Playbooks** - small named-pattern runbooks, one waste pattern each. Reach for these
for "how do I detect and fix this specific thing".

| Tool | What it answers |
|---|---|
| `list_playbooks()` | What cloud waste can we hunt with a ready-made runbook? |
| `get_playbook(name)` | The step-by-step runbook: symptoms, detection queries, fix, anti-pattern |
| `find_playbooks(scope?, service?, waste_category?, confidence?)` | "Which VMs run for nothing?" "Why is the NAT bill so high?" - finds the runbook for a specific waste suspicion |

Both listings carry `approx_tokens` per entry, because the references vary by more
than tenfold - roughly 2K tokens for the smallest, over 25K for the provider pattern
catalogues. The catalogues are enumerated lists, so an agent that wants one pattern
family passes `section` (`get_reference("finops-aws-patterns", section="storage")`)
and pays for that section instead of the whole file. Matching is case-insensitive and
partial; a phrase that matches no heading returns the file's available headings rather
than silently falling back to the full body.

The faceted queries are the reason this is a server and not just a folder of markdown:
every file carries YAML frontmatter mapping it to a FinOps Framework capability, phase,
persona and maturity gate, and a client that only fetches files cannot filter on any
of it.

On hosts that support MCP Apps (SEP-1865), the tool results render as interactive
widgets - a playbook explorer with facet filters and a coverage matrix, a playbook
viewer with copyable detection queries and a checkable fix list, and a reference
browser with a reading panel. Hosts without MCP Apps support get the plain results;
nothing about the tools changes. Details in
[mcp_server/README.md](./mcp_server/README.md).

---

## This skill is actively maintained

This is a living repository. Reference files are refreshed twice a month (around the
1st and the 15th), driven by an automated scan of around 30 data sources - cloud
provider pricing pages, release notes, billing changelogs, and FinOps community
publications. Changes are reviewed before being applied, so the content reflects
verified updates rather than raw feed output.

AI cost management is moving particularly fast - new model releases, capacity options,
and billing mechanics appear every few weeks. Watch or star this repo to be notified
when updates are published.

---

## Contributing

Practitioner experience is the highest-value contribution. Frameworks and vendor docs
are already public; what is rare is "we tried X in production, this is what actually
billed". Corrections to billing mechanics, new or improved playbooks, real-world
counter-examples, and adversarial review of the recommendations are all welcome - the
repo is opinionated, and it should also be falsifiable.

The full guide - contribution types, process, conventions, and what we push back on -
is in [CONTRIBUTING.md](./CONTRIBUTING.md). One check before anything else: if your
change names another OptimNow tool (an MCP tool name, an endpoint URL, a provenance
field), read [DEPENDENCIES.md](./DEPENDENCIES.md) first - most cross-repo breakage
here is documentation drift that no CI check catches.

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

| Tool | What it does |
|---|---|
| [OptimToken](https://optimtoken.optimnow.io) | Compare what 250+ models cost per request, with caching and batch factored in, plus compute instance rates across seven clouds. Also available as an MCP connector - this skill routes price questions here |
| [AI ROI Calculator](https://airoicalculator.optimnow.io) | Whether an AI project pays for itself: three-layer cost model, payback, break-even, sensitivity. Also an [MCP server](https://github.com/OptimNow/ai-roi-calculator-mcp) |
| [AI Cost Readiness Assessment](https://aicostsfinops.optimnow.io) | Where your organisation stands on AI cost management |
| [MCP for Tagging](https://github.com/OptimNow/finops-mcp) | Tag governance automation |
| [FinOps Maturity Assessment](https://optimnow.io) | Crawl / Walk / Run positioning |

---

## Acknowledgements

This skill incorporates content derived from the following sources:

- **[FinOps Foundation](https://www.finops.org/)** - framework definitions, capability
  descriptions, and maturity model structure are based on the FinOps Framework.
- **[Point Five](https://www.pointfive.co)** - cloud optimisation recommendations
  informed several provider-specific best practices and quick-win patterns.
- **[Tokenomics Foundation](https://www.tokeneconomics.com/)** - the token complexity
  classes in the agentic FinOps reference are adapted from *Big-T Notation* by
  Dan Neff (Adobe), published by the Tokenomics Foundation under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

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
