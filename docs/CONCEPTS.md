# Concepts: skill, connector, plugin and live prices

The README says what the library covers and how to install it. This page explains
the delivery shapes behind it, for readers who want to know what a skill is, how the
MCP connector differs from it, why the plugin and the connector are listed separately,
and what to expect from each in practice. It moved here from the README in October
2026 so that the README could lead with coverage.

## What is a Skill? What is an MCP server?

**A Skill** is a structured knowledge folder you attach to an AI agent. Without it,
general-purpose LLMs make confident but incorrect statements on FinOps topics: they
miscalculate PTU break-even rates, confuse Azure and AWS reservation mechanics, and
give advice that ignores how billing works. The answers sound plausible; they are
wrong on the details that matter. The skill corrects that by injecting verified,
curated FinOps knowledge directly into the model's context. The closest analogy is
RAG, minus the infrastructure: no vector database, no embedding pipeline. You copy a
folder and the model gains structured expertise. The same files work with Claude,
GPT, Gemini, or any other model.

**An MCP server** (MCP: Model Context Protocol, the open standard that lets an AI
client call external tools at run time) exposes the same library the other way round,
as read-only tools the model queries on demand. One URL to paste, nothing to install.

**Who this is for:** FinOps practitioners building or evaluating AI-assisted cost
analysis, cloud engineers who want a cost-aware assistant in their workflow, developers
building internal FinOps agents, and Finance or IT managers evaluating the AI tooling
their teams deploy. If you can copy a folder and follow the installation steps, you can
use this.

## Skill + installer, or MCP?

Same content, 2 delivery shapes, and they behave differently because of how models
use them. The comparison below comes from running the same battery of practitioner
questions through both (probe cycles, August 2026; the method is summarised in the
routing record of [ROADMAP.md](ROADMAP.md)).

- **Pushed into context**: as a native skill (Claude Code, Claude.ai / Desktop, Kiro),
  or as rules files written by `install.sh` for tools without skill support (Cursor,
  Windsurf, Codex, Aider, Copilot, Gemini). The guidance is already there when the
  model reasons, with no per-question decision to make. This is why this surface
  grounds both *advisory* answers (commitment sizing, chargeback design, allocation
  methodology) and *symptom* questions ("my NAT gateway processes 10TB/month to S3"),
  where the measured probe runs show it handing over the matching runbook first try.
- **Fetched on demand**: the MCP server. The model must decide to call a tool per
  question, and that decision is this surface's real limit. Measured behaviour:
  lookup and discovery questions ("show me the idle waste runbooks") route reliably;
  advisory and specific-symptom questions route on some phrasings and not others, and
  the tool descriptions name the questions each tool serves to move that probability,
  not to force the call. Version 1.50.0 adds a `query` parameter that ranks the
  library by the user's own sentence: a local run of the probe wordings on
  9 November 2026 saw it called on every one, and the measurement on the hosted
  connector follows the release. Its strengths: distribution (paste one URL, the right path
  for non-technical users and for hosts with neither skill support nor an installer
  target), faceted queries over the library's metadata, and interactive widgets on
  hosts that render MCP Apps (Claude.ai does not render them yet; see below).
- **Both work together, but the gain is unproven.** The August runs found the skill
  alone grounding symptom questions the connector missed, and suggested that with both
  enabled the connector may take those questions over without calling a tool. A probe
  pass with both enabled, on the hosted connector after 1.50.0, settles it (ROADMAP,
  "Routing record"). Until then the advice is the plugin by default on Claude, the
  connector for other hosts and for faceted retrieval.

**What to expect in practice, on either surface.** Neither the skill nor the server
can see your cloud account. For "which of *my* X" questions ("which of my RIs are
about to expire?") the deliverable is the runbook's detection query, which you run
yourself, and the measured behaviour is that models ask you for a data export instead
of volunteering that runbook. The reliable way to get it is to ask explicitly: "check
the playbook library" or "show me the runbook for this". Routing is probabilistic, not
guaranteed: the same question phrased 2 ways can ground differently. When an answer
arrives without a visible tool call or file read, asking for the library by name is
the one-turn fix.

**With your own cloud or cost connector in the session.** Since 1.50.0 the skill
carries rules for running a runbook's detection through a tool you connected: ask
before the first read, read only, say which accounts and regions were covered, treat
a cost platform's figures as a first signal. Measured on 10 November 2026 with a mock
account (Claude Sonnet, headless, 38 runs): with the skill loaded, the model asked
before reading in 5 runs out of 5, against 0 out of 2 before the rule. The limit is
loading. A request worded as an operation ("use the connector to check my account",
"delete the orphaned volumes") did not load the skill in 8 natural runs out of 8, and
on the delete order the model removed volumes without a snapshot in 3 runs out of 10.
The hosted connector carries no such rule: the Claude directory does not let a
connector instruct the model about other tools. So name the skill when you ask
("with the cloud-finops skill, check my account for..."), and give your account
connector a read-only role: that role is the guarantee, the rule is not.

Using a non-Claude model through an API? Add the **response contract** from
[INSTALLATION.md](../INSTALLATION.md) ("API integration / Recommended response
contract") to your system prompt so answers stay structured and billing-grounded.

## Plugin and connector

The Claude plugin built from this repository contains text files only: the skill
instructions in `SKILL.md`, the reference files and the runbooks. It runs no code,
declares no MCP server and sends no data anywhere. Installing it puts FinOps
knowledge into the model's context, and nothing else.

The plugin is listed in the [Claude directory](https://claude.ai/customize/plugins/id/9d1f1714-07ca-4cb4-b658-bddba8f2ec92%40anthropic-plugin-directory),
where it installs in one click and is kept current from this repository. The hosted
MCP connector has its own [listing in the same directory](https://claude.ai/directory/optimnow-cloud-finops),
live since 8 November 2026, where it is added in one click; it can also be added by URL
as described in the README install table.

The hosted MCP connector is optional and is installed separately: as a custom
connector in Claude.ai or Claude Desktop, or with `claude mcp add` in Claude Code. It
serves the same library through 7 read-only tools and, on hosts that render MCP Apps,
as interactive views. It is offered separately, as an MCP connector and not as part
of the plugin, on purpose: both carry the same content, and a plugin that also
declared the server would load the tool definitions in every session next to the
skill and put the same library into context twice. If you use Claude, start with the
plugin. Add the connector for an assistant other than Claude, for retrieval by
question or facet, or for the views. Both together work, with the caveat above: no
measurement yet shows the pair answering better than the plugin alone.

## The MCP server: seven tools

Hosted (nothing to install) or from PyPI; both paths are in the README install table.
Also listed on the
[MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=finops) as
`io.github.OptimNow/cloud-finops`, and on
[PyPI](https://pypi.org/project/cloud-finops-mcp/).

Seven read-only tools: six across 2 surfaces of bundled content, and one that fetches
live figures. The split between the 2 surfaces is deliberate: the 2 content types have
different shapes, and different questions attached to them.

**References**: the long-form provider and discipline files. Reach for these for
billing mechanics, commitment strategy, allocation methodology, or any reasoning that
spans patterns.

| Tool | What it answers |
|---|---|
| `list_references()` | What guidance exists? The catalogue with its FinOps Framework facets and an `approx_tokens` size hint per file |
| `get_reference(name, section?)` | One guide: mechanics, decision rules, worked examples. Whole, or a single H2/H3 section when the question is narrower than the file |
| `find_references(query?, domain?, capability?, phase?, persona?, maturity?, persona_primary_only?)` | "How should we size Savings Plans?" "What must be true before chargeback?" Routes a FinOps question to the guides that serve it; `query` takes the question in your own words, English or French, and ranks the guides by the questions each one declares it answers (`persona_primary_only` cuts to the primary audience) |

**Playbooks**: small named-pattern runbooks, one waste pattern each. Reach for these
for "how do I detect and fix this specific thing".

| Tool | What it answers |
|---|---|
| `list_playbooks()` | What cloud waste can we hunt with a ready-made runbook? |
| `get_playbook(name)` | The step-by-step runbook: symptoms, detection queries, fix, anti-pattern |
| `find_playbooks(query?, scope?, service?, waste_category?, confidence?)` | "Which VMs run for nothing?" "Why is the NAT bill so high?" "Which of my RIs are about to expire?" Finds the runbook for a specific waste suspicion; `query` takes the symptom in your own words and ranks the runbooks by the questions each one declares it answers. The server cannot see your account; the runbook's detection query is the answer it hands over |

Both listings carry `approx_tokens` per entry, because the references vary by more
than tenfold, roughly 2K tokens for the smallest and about 15K for the largest. An
agent that needs one part of a large file passes `section`
(`get_reference("finops-azure-patterns", section="storage")`) and pays for that section
instead of the whole file. The AWS pattern catalogue needs no section call: it is split
into one file per service family (`finops-aws-patterns-compute`, `-storage`,
`-databases`, `-networking`, `-other`). Matching is case-insensitive and partial; a
phrase that matches no heading returns the file's available headings rather than
silently falling back to the full body.

The faceted queries are the reason this is a server and not just a folder of markdown:
every file carries YAML frontmatter mapping it to a FinOps Framework capability, phase,
persona and maturity gate, and a client that only fetches files cannot filter on any
of it.

**Live figures**: one tool, and the only one that leaves the bundled content. Reach for
it when a reference quotes a figure from an OptimToken guide with its date and the
answer needs the current value.

| Tool | What it answers |
|---|---|
| `get_live_figures(guide)` | "Is the Compute Savings Plan premium still about 9 points?" Fetches the guide's `figures.json` (rebuilt daily) and returns it unchanged, with the `snapshotDate` to quote the figures by. Guides today: `savings-plans-vs-reserved-instances`, `arm-against-x86`, `batch-api-economics` |

It makes one HTTPS request to `optimtoken.optimnow.io`, carrying the guide slug and
nothing from the conversation, and caches the answer for six hours. When the call
fails, the dated figure in the reference stands, quoted with its date. Privacy detail
in [PRIVACY.md](../PRIVACY.md).

On hosts that support MCP Apps (SEP-1865), the tool results render as interactive
widgets: a playbook explorer with facet filters and a coverage matrix, a playbook
viewer with copyable detection queries and a checkable fix list, and a reference
browser with a reading panel. Hosts without MCP Apps support get the plain results;
nothing about the tools changes. Claude.ai is one of them for now: in the last test
(30 September 2026) the tool calls worked and returned plain results, and no widget
rendered. Details in [mcp_server/README.md](../mcp_server/README.md).

## Live prices are not in this repository

The skill carries billing **mechanics**, which stay true for years. It deliberately
does not carry current price **figures**, which go stale inside a packaged skill within
weeks. The skill tells the model to use a live pricing tool if one is connected in the
session, and otherwise to point you at a live source such as
[OptimToken](https://optimtoken.optimnow.io), OptimNow's free price comparison for LLM
token rates and compute instance rates, each figure carrying its own as-of date. Its
MCP connector is optional and documented in its own repository; see
[INSTALLATION.md](../INSTALLATION.md#companion-connector-optimnow-ai-pricing-hub-optional).
The one exception is narrow: the dated figures some references quote from an OptimToken
guide can be refreshed through `get_live_figures` (above), which passes the guide's
current figures through without holding any of them here.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
