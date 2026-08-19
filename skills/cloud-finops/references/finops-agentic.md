---
name: finops-agentic
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Architecting & Workload Placement"
fcp_capabilities_secondary: ["Usage Optimization", "Anomaly Management", "Governance, Policy & Risk"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Product", "Finance", "Leadership", "Security"]
fcp_maturity_entry: "Run"
---

# FinOps for Agentic Systems

> True agents decide at run time what to call, in what order, and for how long, so
> their cost is unbounded per task and settles across tokens, harness, and a new
> direct-payment surface. This file covers agentic cost anatomy, cost-safe
> architecture, and agent-initiated payments (x402 / MPP).

Agentic systems introduce cost patterns that require a different governance model. Unlike
static applications, agents make runtime decisions that directly affect spend - model
selection, context retention, tool invocation frequency, and retry behaviour all create
variable costs that no static budget can fully anticipate.

## Workflow, pipeline, agent - three cost problems under one word

Cost and evaluation behave differently across three system types that all get sold
as "agents":

| Type | Definition | Cost behaviour | Evaluation |
|---|---|---|---|
| **Workflow** | Traditional software with GenAI bolted into one or more steps | Bounded per invocation | Standard test set |
| **Pipeline** | Predetermined steps, LLM called at one or more of them (most chatbots) | Bounded: per-call cost × known number of calls | LLM-as-judge works (fixed trajectory) |
| **True agent** | Broad objective, tools available, decides at run time what to call, in what order, for how long | **Unbounded per task** - up to ~30x token variance on the same prompt (Pay-i-reported) | LLM-as-judge breaks: the agent constructs its own prompts, signal lives in the trajectory, not the final output |

**FinOps implications:**

- Budget and forecast per type. Workflows and pipelines can be unit-priced; true
  agents must be budgeted as a **cost distribution** (P50/P90 per task), not a point
  estimate.
- **Procurement diligence:** most vendors selling an "agent" are selling a pipeline.
  Often that is exactly what the client needs - but bounded-cost pipelines and
  unbounded-cost agents deserve different contract and budget treatment. Ask which
  one you are buying.
- Agent failures rarely occur at the last step - they occur earlier and are masked
  by later steps. Output-only quality gates therefore under-detect failure, which
  understates the true cost per successful task.

## Token complexity classes - Big-T notation

Big-T notation (Dan Neff, Adobe; published by the
[Tokenomics Foundation](https://www.tokeneconomics.com/projects/big-t-notation/)
under CC BY 4.0) applies the logic of Big-O runtime analysis to token spend: before
committing to an architecture, ask how the bill scales as usage grows, not what one
call costs. Token cost scales as **T(n · k · a)**:

- **n** - request volume and input size (the factor everyone forecasts)
- **k** - model calls per request: reasoning steps, multi-turn chains, tool calls
  that replay context. Usually invisible in the request as written ("hidden k")
- **a** - agent depth: sub-agents spawning sub-agents, multiplying k again

| Class | Scaling behaviour | Example |
|---|---|---|
| T(1) | Constant - no model call per request | Cache hit, embedding lookup |
| T(log n) | Sublinear - deterministic code shrinks input before the model sees it | Pre-filter, then summarise the survivors |
| T(n) | Linear - one call per request, cost proportional to input | Single-shot classification |
| T(n·k) | Multiplicative - k calls per request, k usually invisible | Multi-turn chat replaying full history every turn |
| T(n·k·a) | Agent-multiplicative | Orchestrator spawns sub-agents that spawn tool calls |
| T(∞) | Unbounded - loop with no termination condition | Retry loop without a cap |

This grades the "unbounded per task" verdict in the table above: workflows and
pipelines sit at T(n) or T(n·k) with a known k; true agents are T(n·k·a) with k and
a decided at run time; an uncapped retry loop is T(∞) and belongs in incident
response, not in a budget.

**FinOps implications:**

- **Change the class before optimising the coefficient.** Restructuring a workload
  from T(n·k) to T(n) - isolated contexts instead of full-history replay, bounded
  output templates - is worth more than any amount of prompt-shortening inside the
  wrong class. The framework's own worked example (illustrative, as of August 2026)
  cut a ten-document summarisation job ~34x by moving it from chat-replay T(n·k) to
  engineered T(n).
- **Forecast by class.** A workload's class names the variable that dominates its
  growth: linear workloads scale with volume, agentic ones with depth and retries.
  A cost estimate that assumed T(n) for a system built as T(n·k·a) is the usual
  anatomy of a "30x over estimate" agent pilot.
- **Hidden k is the audit target.** Reasoning tokens, retries, and context replay
  rarely appear in request logs. Per-task tracing across providers (see the cost
  anatomy section below) is what makes k and a observable at all.
- **Jevons caveat.** Class improvements get reinvested: cheaper per-task cost
  typically raises run frequency, so total spend falls less than unit cost does.
  Budget for the rebound, not just the efficiency gain.

The notation itself is durable mechanics; the framework is early-stage (published
2026) and most of its companion tooling was still unreleased as of August 2026 -
cite the classification, not the ecosystem.

## Agentic cost anatomy - where the tokens actually go

- **Refinement is the sink.** ~60% of an agentic task's cost sits in checking,
  repairing, and re-verifying - not in generating the first answer (59.4%
  review/refinement share, 53.9% average input-token share). Source: Salim et al.,
  *Tokenomics: Quantifying Where Tokens Are Used in Agentic Software Engineering*,
  [arXiv:2601.14470](https://arxiv.org/abs/2601.14470) - measured on the ChatDev
  framework across design, coding, completion, review, testing and documentation
  stages. The mechanism generalises; exact ratios vary by workload.
- **Agentic tasks consume ~1,000x the tokens** of comparable single-turn or chat
  interactions, with input rather than output tokens driving the cost. Source:
  *How Do AI Agents Spend Your Money? Analyzing and Predicting Token Consumption in
  Agentic Coding Tasks*, [arXiv:2604.22750](https://arxiv.org/abs/2604.22750) -
  eight frontier models on SWE-bench Verified; consistent with Anthropic's
  multi-agent research system write-up. Long-lived context is an operating asset
  and a dominant cost.
- **Multi-model by default:** ~3.5 different models per agent run on average, often
  across providers (Pay-i-reported). Single-provider cost views structurally
  under-count agent cost - attribution must be per task, across providers.
- **Track cost per completed task, not per token.** Per-token price for fixed
  capability has been falling (~6.67%/month compounding, Pay-i-reported), yet cost
  per completed task rises in most production workloads because task ambition grows
  faster than prices fall. Falling rate cards are not a savings forecast.
- **Search/retrieval-boundary APIs** - for agents doing live web search or scraping,
  vendors (Exa, Tavily, Firecrawl, Parallel, Valyu) meter the fetch separately from
  model tokens - per credit, per page, or per scoped extraction - instead of the
  agent paying full input-token rates to ingest raw page text. Compare that
  vendor cost against the token cost of stuffing full pages into context; the
  cheaper path depends on page size and how much of the page the task actually
  needs. This is a fast-moving, mostly early-stage vendor category - check
  viability before wiring one into a production path.

**Three architectural pillars for cost-safe agents:**

**1. Data connectivity with cost awareness**
Agents require access to real-time cost data alongside operational data. An agent that
can identify a spending anomaly but cannot correlate it to a specific resource, workflow,
or decision point is only half useful. MCP-based connectivity (e.g., OptimNow's finops-tagging
MCP server) provides standardized interfaces for cost data, tagging, and governance without
custom integration code per data source.

**2. Memory with cost controls**
Stateful agents accumulate context over time - necessary for meaningful investigation but
expensive if unbounded. Naive implementations store entire conversation histories, creating
context windows that balloon to hundreds of thousands of tokens. Effective architectures
use short-term memory for recent exchanges and long-term memory for persistent preferences
and organisational context, with explicit token budgets for each layer.

As of August 2026, Bedrock AgentCore memory, policy, and a new managed harness are
available in AWS GovCloud (US-West), extending these pillars to regulated and government
cloud environments for cost-governance planning. Source: AWS What's New - Bedrock.

**3. Policy-generation over direct mutation**
The safest agentic architecture for FinOps generates governance policies for human review
rather than executing infrastructure changes directly. An agent that identifies idle
resources and drafts a Cloud Custodian policy or OpenOps rule for review is production-safe.
An agent that stops instances autonomously is not - regardless of how sophisticated its
reasoning is. Governance, not technology capability, is the real constraint on autonomous
FinOps agents.

AgentCore's policy capability now supports natural-language-to-Cedar tool-access controls,
consistent with the policy-generation-over-direct-mutation pillar above.

**New cost surface - the managed harness.** AgentCore's managed harness is a declarative
agent runtime that removes orchestration code. It bundles compute, environment, and
observability into API calls, creating a new billing surface to track alongside AgentCore
Payments. Give it its own cost-attribution treatment - similar to the Managed Agents
session-runtime billing documented in finops-anthropic.md - so bundled runtime cost is
not silently folded into token spend. As of August 2026, this is available in AWS GovCloud
(US-West). Source: AWS What's New - Bedrock.

## Agents as cost actors: agent-initiated payments (x402 / MPP)

Agent spend historically reached the organisation through two mediated channels:
token consumption (cloud/model bill) and SaaS or API contracts signed by humans.
A third, unmediated channel is now live: agents paying for resources directly -
per request, from a funded wallet, with no account, API key, or procurement step.

**The mechanics.** Both protocols are built on HTTP `402 Payment Required`: the
agent requests a resource, receives a 402 challenge (amount, recipient, network),
pays - typically in USDC stablecoin - and retries with a payment proof; the seller
verifies, settles, and returns the resource with a receipt.

| Layer | What exists (as of July 2026) |
|---|---|
| Protocol | **x402** - open standard, created by Coinbase, now a Linux Foundation project (x402 Foundation; Coinbase and Cloudflare founding members; AWS, Stripe, Vercel among members). **MPP** (Machine Payments Protocol) - Stripe + Tempo Labs, IETF standards track, adds card rails and streaming payment sessions, backwards-compatible with x402 |
| Platform rails | **Amazon Bedrock AgentCore Payments** - managed wallets via Coinbase CDP or Stripe (Privy); every payment runs in a *payment session* with a spending cap (`maxSpendAmount`) and expiry; wallets start empty and the end user explicitly grants the agent transaction permission; AgentCore Gateway reaches paid MCP servers/APIs incl. the Coinbase x402 Bazaar catalogue. **Cloudflare Agents SDK** - agents that pay (optional human-in-the-loop confirmation per payment) and services that charge (`paidTool`, one-line middleware) |
| Control plane | **Ampersend** (Edge & Node, on x402 + Google A2A) - team wallets, funding automation, approvals, spend observability. Early entrant; expect a category |

Scale signal: x402.org self-reported counters showed ~75M transactions / ~$24M
volume / ~22k sellers over 30 days in July 2026 - an average of ~$0.32 per
transaction. Micro-transactions at high frequency, not few large charges.

**FinOps implications:**

- **Attribution gap.** This spend settles on wallet ledgers - outside the cloud
  bill and outside SaaS invoices. It is also *prepaid* (fund wallet, draw down),
  inverting the invoice-in-arrears assumption of most cost reporting. Ingest
  wallet/session ledgers as a first-class cost source next to token spend, and
  tag payment sessions to use cases.
- **Pre-spend controls are native on day one** - unusual for a new cost category.
  Session caps, expiry, explicit permission grants, merchant allowlists,
  human-in-the-loop confirmation. Make them IaC defaults so an uncapped payment
  session is an active choice, not an accident.
- **New shadow-spend vector.** x402 removes exactly the friction (accounts, KYC,
  procurement) that used to force spend through central visibility. A wallet
  funded on an engineer's card is invisible to billing exports. Define who may
  create and fund payment instruments, from which budget. Wallets hold stablecoin
  balances - custody and accounting questions belong to treasury/compliance, not
  FinOps alone.
- **Unit economics.** Cost per completed task must include direct purchases
  (paid MCP tools, specialist APIs, licensed content, agent-to-agent payments)
  alongside tokens and harness. Extends the per-query SaaS dimension described
  above: same mechanism, but contract-free and invoice-free.
- **Anomaly profile changes.** Many sub-dollar transactions behave differently
  from the few large charges existing thresholds expect; alert on session
  patterns and velocity, not only on amounts.
- **Seller side.** The same rails let an organisation charge agents for its own
  APIs, data, or MCP tools per call, without onboarding friction - a
  monetisation option to evaluate, not only a cost risk.

Sources: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/payments-how-it-works.html,
https://developers.cloudflare.com/agents/tools/payments/, https://x402.org/,
https://ampersend.ai/

**Key insight:** Agents will be advisory long before they are autonomous. Organisations
making progress treat agent development as iterative learning, not project delivery.

---

> Sources: OptimNow methodology; Big-T Notation by Dan Neff, Tokenomics Foundation (CC BY 4.0, linked inline); x402 / MPP provider documentation (linked inline).

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
