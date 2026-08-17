# Installation Guide

The skill ships in a single canonical Claude / Agent-Skills format and is converted on
the fly to the shape each target tool expects. One installer (`./install.sh`) handles
the conversion for every supported tool. Per-tool blocks below are copy-pasteable.

## Prerequisites

- `git` (for clone / fetch - only required if running the installer remotely)
- `bash` (macOS / Linux / WSL). The script targets bash 3.2, the macOS default,
  so no Homebrew bash upgrade is needed.
- For the Claude Projects zip: `python3` or `zip`

---

## Quick reference: one installer, twelve tools

```bash
# Auto-detect tools in the current project / $HOME and install for each
curl -sL https://raw.githubusercontent.com/OptimNow/cloud-finops-skills/main/install.sh | bash

# Or install for a specific tool
curl -sL https://raw.githubusercontent.com/OptimNow/cloud-finops-skills/main/install.sh | bash -s -- --tool <name>

# Other useful flags
./install.sh --list              # list supported tools
./install.sh --dry-run           # print what would happen
./install.sh --user              # install at $HOME paths (Claude Code)
./install.sh --inline            # cursor/windsurf/codex/aider: embed the whole
                                 # library instead of a routing file (~1MB)
./install.sh --dest <dir>        # override target directory
```

Supported tools: `claude-code`, `claude-projects`, `cursor`, `windsurf`, `chatgpt`,
`gemini`, `gemini-cli`, `codex`, `aider`, `copilot`, `kiro`, `mcp`.

The `mcp` target is special: it does not copy files, it prints the install hint and
the per-client MCP config snippets. See the [MCP server](#mcp-server-cross-tool) section
below.

---

## Per-tool blocks

### Claude Code (project)

```bash
./install.sh --tool claude-code
```

Copies the skill folder to `<project>/.claude/skills/cloud-finops/`. Restart Claude Code
or run `/reload-plugins` to pick up.

For auto-updating installs, prefer the plugin marketplace path:

```
/plugin marketplace add https://github.com/OptimNow/cloud-finops-skills.git
/plugin install cloud-finops@optimnow
/plugin update cloud-finops@optimnow
```

(Run those at the Claude Code prompt, not in a shell.)

### Claude Code (user-level)

```bash
./install.sh --tool claude-code --user
```

Copies to `~/.claude/skills/cloud-finops/` so the skill is available across all your
Claude Code projects.

### Claude Projects / claude.ai (web upload)

```bash
./install.sh --tool claude-projects
```

Builds `dist/claude-projects/cloud-finops.zip`. Upload via Claude.ai or Claude Desktop:
**Settings → Skills → Upload zip**.

The release workflow also attaches a version-tagged build
(`cloud-finops-vX.Y.Z.zip`) to every GitHub release - you can grab it from
https://github.com/OptimNow/cloud-finops-skills/releases without running the
installer locally.

### Cursor

```bash
./install.sh --tool cursor
```

Writes `<project>/.cursor/rules/cloud-finops.mdc` - the SKILL.md router plus an index
of every reference and playbook, with Cursor frontmatter. Cursor auto-loads
`.cursor/rules/`. Trigger by asking a FinOps question in chat.

The rule does **not** embed the reference bodies. Pair it with the
[MCP server](#mcp-server-cross-tool) so Cursor can fetch them on demand, or keep a
local checkout of the skill. See [Routing file vs `--inline`](#routing-file-vs---inline).

### Windsurf

```bash
./install.sh --tool windsurf
```

Writes `<project>/.windsurf/rules/cloud-finops.md` with Windsurf rule frontmatter
(`trigger: model_decision`). Like the Cursor rule this is a routing file, not the
full library - Windsurf enforces a per-rule character limit far below the size of
the reference set. See [Routing file vs `--inline`](#routing-file-vs---inline).

### ChatGPT (Custom GPT)

```bash
./install.sh --tool chatgpt
```

Builds two artefacts in `dist/chatgpt/`:

- `instructions.md` - target ≤ 8000 chars; the routing logic, reasoning sequence, and
  response contract that go into the GPT's Instructions field. The installer warns if
  the file exceeds the limit.
- `knowledge/*.md` - one file per reference plus one per playbook in the default build:
  - the reference files (one per domain; `optimnow-methodology.md` is **merged into
    `finops-for-ai.md`**)
  - the playbook files prefixed `playbook-<slug>.md` so they sort together in the
    GPT Knowledge UI
  - The instructions routing contract points named waste patterns
    (zombie NAT, snapshot sprawl, etc.) at `playbook-<slug>.md` and other queries at
    the matching reference filename

ChatGPT historically capped Custom GPT Knowledge at 20 files. If your upload is
rejected, re-run the installer with the grouped flag:

```bash
./install.sh --tool chatgpt --grouped
```

The grouped build still writes to `dist/chatgpt/` (so all the upload steps below still
apply) but emits a **10-file thematic bundle** (aws, azure, gcp, ai, data-platforms,
oci, cross-cutting, finops-discipline, playbooks, methodology) with a separate routing
contract that points at the grouped filenames. Same content, fewer files, easier
upload.

Then manually:

1. Open https://chatgpt.com/gpts/editor
2. Paste `dist/chatgpt/instructions.md` into the Instructions field
3. Upload all files from `dist/chatgpt/knowledge/` to the Knowledge section
4. Set name (`Cloud FinOps`), category, visibility per preference

**Public Custom GPT on the Roadmap.** A maintained public Cloud FinOps GPT is tracked
in the `Roadmap > In-flight` section of `CLAUDE.md`; until it ships, the self-host
path above is the supported install.

**Trade-off:** ChatGPT's 8K Instructions limit means routing + response contract live
inline, but the reference content is RAG-retrieved from Knowledge files. Compared to
the Claude / Cursor install, ChatGPT may miss cross-reference detail because it
retrieves chunks rather than loading the full skill into context.

### Gemini Gems (web)

```bash
./install.sh --tool gemini
```

Builds `dist/gemini/instructions.md` (a routing contract that points at the grouped
filenames) and `dist/gemini/knowledge/*.md` - **10 files** grouped by domain: aws,
azure, gcp, ai, data-platforms, oci, cross-cutting, finops-discipline, playbooks,
methodology. The `playbooks.md` bundle concatenates all named-pattern runbooks; the
instructions routing tells the model to look up the matching `## playbook: <slug>`
section inside it.

Manual upload at https://gemini.google.com/gems/. Same trade-off as ChatGPT applies.

**Public Gemini Gem on the Roadmap.** A maintained public Cloud FinOps Gem is
tracked in the `Roadmap > In-flight` section of `CLAUDE.md`; until it ships, the
self-host path above is the supported install.

### Gemini CLI

```bash
./install.sh --tool gemini-cli
```

Copies to `~/.gemini/skills/cloud-finops/`. This target always installs at `$HOME`;
`--user` is not needed and has no effect on it. Use `--dest <dir>` to install
elsewhere.

Gemini CLI implements the same `SKILL.md` standard as Claude Code and Codex CLI, so
the skill installs unmodified. It discovers user skills in `~/.gemini/skills/` (with
`~/.agents/skills/` as an alias) and reads `SKILL.md` either at the root or one
directory deep - `~/.gemini/skills/cloud-finops/SKILL.md` is the second form. At
session start it injects each enabled skill's name and description into the system
prompt and adds the skill directory to the agent's allowed file paths, so the
reference files are readable on demand. For a project-scoped install instead, use
`--dest .gemini/skills` to write the workspace-level location.
Source: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md

### OpenAI Codex CLI

```bash
./install.sh --tool codex
```

Writes `<project>/AGENTS.md` (or `AGENTS-cloud-finops.md` if a foreign `AGENTS.md`
already exists, to avoid clobbering - a re-run recognises its own output and
overwrites in place). Codex CLI reads `AGENTS.md` as project-level context.

This is a routing file. For the reference bodies, pair it with the MCP server below -
that is the intended pairing, not an optional extra. See
[Routing file vs `--inline`](#routing-file-vs---inline).

### Aider

```bash
./install.sh --tool aider
```

Writes `<project>/CONVENTIONS.md` (or `CONVENTIONS-cloud-finops.md` if a foreign one
exists). Aider auto-reads `CONVENTIONS.md`. This is a routing file; add specific
references at runtime with:

```bash
aider --read skills/cloud-finops/references/finops-bedrock.md ...
```

### GitHub Copilot

```bash
./install.sh --tool copilot
```

Writes `<project>/.github/copilot-instructions.md`. Copilot's customisation surface
is shallow - the file informs code-suggestion context but won't power deep FinOps Q&A
the way Claude / Cursor do. Use as a lightweight context hint, not a full skill load.

### Kiro IDE

```bash
./install.sh --tool kiro
```

Copies the skill to `<project>/.kiro/powers/cloud-finops/`. Kiro uses `POWER.md` as the
entry point.

### Routing file vs `--inline`

The four single-file targets - Cursor, Windsurf, Codex CLI, Aider - emit a **routing
file** by default: the SKILL.md router, an index of every reference and playbook with
its description and facets, and instructions for fetching a body on demand. That is
about 27 KB (~7K tokens).

They used to inline the entire reference library. As the library grew that reached
roughly 1 MB (~250K tokens) per artefact, which overflows or dominates the context
window of every tool that loads it, and sits far above Windsurf's documented per-rule
character limit. Nothing measured the artefacts, so the regression was invisible -
the installer reported success either way. `scripts/check-artefact-size.sh` now runs
in CI to keep it that way.

**The routing file assumes the model can reach the bodies.** Pair it with the MCP
server below, or keep a local checkout of the skill - the generated file explains both
paths and tells the model to say so rather than answer from memory if neither is
available.

If you want the old behaviour - no MCP server, no checkout, everything embedded:

```bash
./install.sh --tool cursor --inline
```

Expect the size trade-off that comes with it. The installer prints a warning
describing what you got in either mode.

### MCP server (cross-tool)

```bash
./install.sh --tool mcp
```

The `mcp` target prints install hint + per-client config snippets. It does not run
`pip` for you. The MCP server is a separate Python package (`cloud-finops-mcp`) that
exposes the references and named-pattern playbooks as queryable tools - useful
for agents that need search-style retrieval rather than full-context injection.

**Install the server:**

```bash
pip install cloud-finops-mcp
# or, no install:
uvx cloud-finops-mcp
```

**Six tools (all read-only), split across two surfaces:**

References (long-form provider/discipline files):

- `list_references()` - all references with their FCP metadata
- `get_reference(name)` - full markdown body of one reference
- `find_references(domain?, capability?, phase?, persona?, maturity?)` - faceted query
  over the FinOps Capability/Phase frontmatter

Playbooks (small named-pattern runbooks):

- `list_playbooks()` - all playbooks with scope / service / waste-category metadata
- `get_playbook(name)` - full markdown body of one playbook
- `find_playbooks(scope?, service?, waste_category?, confidence?)` - faceted query

Use a playbook for *"how do I detect/fix this specific pattern?"* (zombie NAT, snapshot
sprawl, idle ELB). Use a reference for billing mechanics, commitment strategy,
allocation methodology, or any cross-pattern reasoning.

**Configure your client** by adding the appropriate snippet to its MCP config file:

| Client | File | Snippet |
|---|---|---|
| Claude Code | `.mcp.json` (project), or `claude mcp add --scope user` (user) | JSON below / command below |
| Cursor | `~/.cursor/mcp.json` | JSON below |
| Codex CLI | `~/.codex/config.toml` | TOML below |
| Windsurf | `~/.windsurf/mcp.json` | JSON below |
| Cline / other MCP clients | client-specific | use the JSON shape |

**JSON snippet** (Claude Code, Cursor, Windsurf, generic):

```json
{
  "mcpServers": {
    "cloud-finops": {
      "command": "cloud-finops-mcp"
    }
  }
}
```

**TOML snippet** (Codex CLI):

```toml
[mcp_servers.cloud-finops]
command = "cloud-finops-mcp"
```

**Claude Code user scope.** There is no `~/.claude/mcp.json` - Claude Code does not
read that path. Register the server once for every project with:

```bash
claude mcp add --scope user cloud-finops -- cloud-finops-mcp
```

Restart your client. Verify in Claude Code with `/mcp`, in Codex CLI with
`codex mcp list`. In Cursor and Windsurf the server appears in the MCP panel.

**When to use the MCP server vs the file-based install:**

- File install (rules, AGENTS.md, .mdc) - the skill is loaded as static context for
  every chat. Best for tools that read instruction files at startup.
- MCP server - tools fetch on demand. Best for big-codebase sessions where context
  budget is tight, and for queries that benefit from FCP-faceted filtering ("give me
  the Walk-stage Rate Optimization references aimed at Engineering").

The two paths are complementary - you can install both.

Source: https://github.com/OptimNow/cloud-finops-skills/tree/main/mcp_server

---

### Companion connector: OptimNow AI Pricing Hub (optional)

This skill deliberately does not carry current price figures. Billing mechanics are
durable and belong in the reference files; absolute prices are volatile and go stale
inside a packaged skill within weeks. See "Price figures" in `SKILL.md` for the rule.

The AI Pricing Hub is where those figures live: <https://optimtoken.optimnow.io>. The
website is usable on its own and needs no setup. Adding its MCP connector lets the model
fetch a figure mid-answer instead of telling the user to go and look it up.

**It is a remote server, so there is nothing to install.** Point your client at the
endpoint:

```
https://ai-pricing-hub-mcp-9604f763.alpic.live/
```

Claude Desktop / Claude Code (`claude_desktop_config.json` or `.mcp.json`):

```json
{
  "mcpServers": {
    "ai-pricing-hub": {
      "command": "npx",
      "args": ["mcp-remote", "https://ai-pricing-hub-mcp-9604f763.alpic.live/"]
    }
  }
}
```

On Windows, wrap the command: `"command": "cmd"`, `"args": ["/c", "npx", "mcp-remote", "<url>"]`.

**Three tools (all read-only):**

- `compare-llm-models(provider?, category?, openness?, capability?, maxInputPrice?, maxOutputPrice?, minElo?, useCasePreset?, volumePreset?, limit?)` - model comparison by price, quality (ELO), and efficiency, with list and cache/batch-optimised cost
- `estimate-llm-cost(modelName?, useCasePreset?, monthlyVolume?, customInputTokens?, customOutputTokens?)` - per-request and monthly cost for a model against a use-case token profile
- `compare-compute-pricing(provider?, category?, processor?, useCase?, minVCPUs?, maxVCPUs?, minMemory?, maxMemory?, sortBy?, limit?)` - instance pricing across AWS, Azure, GCP, DigitalOcean, OCI, OVH, and Alibaba, including spot, Savings Plan, and reserved rates

**Read the provenance block before quoting anything it returns.** Every response carries
one, and it is the thing that makes the dated-price rule workable:

| Field | Why it matters |
|---|---|
| `provenance.tier` | `1` = fetched live from optimtoken.optimnow.io. `2` = served from a committed static snapshot because the upstream was unreachable |
| `provenance.dataAsOf` / `upstreamTimestamp` | The as-of date to put next to the figure |
| `provenance.notice` | Present on tier 2, and states plainly that the pricing is stale, how old the snapshot is, and which filters were *not* applied |

A tier-2 response is still usable - it is a dated snapshot, not a guess - but it must be
quoted as one. Do not present a tier-2 figure as a current price, and note that on tier 2
the compute catalogue is a subset of the live one and carries no region dimension, so a
region filter silently does not apply and a narrow query can come back empty.

Source: https://github.com/OptimNow/ai-pricing-hub-mcp

---

### Companion connector: AI ROI Calculator (optional)

The skill covers how to *govern* an AI investment - the Investment Council, stage gates,
incremental funding - and, in `finops-ai-value-management.md`, how to choose and defend a
value method. It does not compute the business case. This connector does.

Hosted, nothing to install:

```bash
claude mcp add --transport http ai-roi-calculator https://ai-roi-calculator-mc-e9dd36e7.alpic.live/mcp
```

For Claude.ai / Claude Desktop, **Settings -> Connectors -> Add custom connector** and
paste the same URL. Cursor, Windsurf, VS Code and ChatGPT take an HTTP MCP server entry
pointing at it.

**Four tools (all read-only, no credentials):**

- `calculate-roi-v4` - full ROI, payback, break-even volume, net benefit, cost breakdown
- `lookup-model-price` - list, batch and prompt-cache prices for a model
- `load-preset` - sensible defaults for one of 11 use-case scenarios
- `sensitivity-analysis` - impact ranking of volume, realisation rate, cost and value at plus or minus 20%

Its prices come from the same OptimToken catalogue as the pricing hub above, with the same
tier-1 / tier-2 provenance discipline, so a figure quoted through either connector carries
its as-of date.

**Why this is a separate server and not more tools on `cloud-finops-mcp`.** The formulas
are generated from the [AI ROI Calculator](https://github.com/OptimNow/ai-roi-calculator)
and synchronised into the server by a build step, with CI drift detection and a
golden-scenario suite. The web app and the server once returned a 7-point different ROI for
the same preset, which is what that machinery now prevents. A third copy of the same
arithmetic living in this repo would sit outside it. The full mathematical specification is
in [METHODOLOGY.md](https://github.com/OptimNow/ai-roi-calculator/blob/main/METHODOLOGY.md).

Source: https://github.com/OptimNow/ai-roi-calculator-mcp

---

## Updating

```bash
./install.sh --tool <name>
```

Re-running the installer for a tool overwrites the previous install in place. The
script is idempotent - safe to run on every release.

For Claude Code plugin users:

```
/plugin update cloud-finops@optimnow
```

---

## API integration (system-prompt injection)

For direct API use without one of the supported tools, concatenate the skill files
into your system prompt. This is the model-agnostic path - works with any LLM API
(Claude, OpenAI, Gemini, Mistral, others).

```python
import os

def load_cloud_finops_skill(skill_dir: str) -> str:
    skill_md = open(f"{skill_dir}/SKILL.md").read()
    sections = []

    # References (long-form provider / capability files)
    ref_dir = f"{skill_dir}/references"
    for filename in sorted(os.listdir(ref_dir)):
        if filename.endswith(".md"):
            content = open(f"{ref_dir}/{filename}").read()
            sections.append(f"## references/{filename}\n\n{content}")

    # Playbooks (named-pattern runbooks - SKILL.md routes named waste
    # patterns to playbooks/<slug>.md, so they must be loaded too)
    pb_dir = f"{skill_dir}/playbooks"
    if os.path.isdir(pb_dir):
        for filename in sorted(os.listdir(pb_dir)):
            if filename.endswith(".md") and filename != "README.md":
                content = open(f"{pb_dir}/{filename}").read()
                sections.append(f"## playbooks/{filename}\n\n{content}")

    return skill_md + "\n\n---\n\n" + "\n\n---\n\n".join(sections)

system_prompt = load_cloud_finops_skill("./cloud-finops")
```

For token efficiency, load only the references relevant to your use case. For most
single-domain queries, one reference file plus `optimnow-methodology.md` is sufficient.
Playbooks average ~5 KB each and the full set is ~120 KB (roughly 30K tokens), so do
not load them all by default: load the one playbook matching the named pattern, or
filter by frontmatter facet (scope, service, waste_category) first. Loading the full
set only makes sense for a deliberate whole-taxonomy review.

### Recommended response contract

For non-Claude models, prepend this contract to your system prompt to keep responses
structured and grounded in the injected references:

```text
# Cloud FinOps Response Contract - by OptimNow
# https://github.com/OptimNow/cloud-finops-skills

You are a Cloud FinOps expert providing practical, business-aligned guidance
on cloud cost management, AI workload economics, and commitment strategy.

Your knowledge comes from injected reference documents covering provider-specific
billing mechanics, pricing models, and proven optimisation patterns. Rely on
the provided references when available. Do not invent pricing figures, discount
percentages, or billing rules.

The references are authoritative on billing MECHANICS, which are durable. They are
NOT authoritative on price FIGURES, which are volatile: any absolute price in them
is illustrative and may be out of date.

RESPONSE CONTRACT
1) Context and positioning
- Identify the relevant cloud domain(s) and provider(s).
- State assumed maturity level (Crawl/Walk/Run) if the user does not specify.
- State assumptions explicitly.

2) Practical guidance
- Lead with how billing actually works before recommending actions.
- Distinguish quick wins from structural improvements.
- Avoid generic best-practice statements without grounding in billing mechanics.

3) Metrics and signals
- Use measurable indicators tied to the specific domain.
- If targets are unknown, provide directional guidance instead of fabricated numbers.

4) Business impact
- Connect recommendations to business outcomes, not just cost reduction.
- Clarify trade-offs and accountability implications.

5) Maturity awareness
- Tailor actions to the user's maturity level.
- Do not recommend advanced automation at Crawl unless explicitly requested.
- When relevant, show progression to the next maturity stage.

BEHAVIORAL RULES
- Do not hallucinate billing rules, pricing, or discount mechanics.
- If required information is missing from the references, state the limitation.
- If outside cloud cost or FinOps scope, say so briefly.
- Keep tone structured, professional, and concise.

PRICE FIGURES
- Never quote a price without its as-of date and source: "$X per 1M input tokens
  (list price, <source>, <date>)". A figure with no date is not usable in a client
  deliverable.
- If a live pricing tool is available, call it before quoting any token or instance
  price. Otherwise refer the user to https://optimtoken.optimnow.io and mark any
  figure you give as illustrative.
- Quote mechanics and ratios (batch discount, cache-read multiplier, commitment term
  structure) with confidence. Date every absolute number.
- Never interpolate a missing price from a neighbouring model, a previous generation,
  or another region. If the figure is not available, say so.
- If the pricing tool returns a "provenance" block, read it first. tier 1 = fetched
  live; tier 2 = a dated static snapshot served because the upstream was unreachable.
  Quote a tier-2 figure as a dated snapshot, never as a current price, and treat an
  empty tier-2 result as possibly degraded data rather than as "no match".

OUTPUT FORMAT
Use headers:
- Context
- Recommendation
- Metrics and signals
- Business impact
Do not output JSON unless requested.
```

---

## Troubleshooting

**Skill not activating in Claude Code:** check that the YAML frontmatter in `SKILL.md`
is valid. The `name` and `description` fields are required.

**Cursor / Windsurf rule not triggering:** verify the rule's `description` field is
specific enough that the model picks it up. The default description in the installer
already covers the major FinOps query types.

**ChatGPT instructions exceed 8K limit:** the installer warns when the build crosses
the limit. If it does, manually trim the routing table to only the providers you care
about, or upload the trimmed routing as a knowledge file and keep instructions minimal.

**ChatGPT rejects the knowledge upload (file count):** the default build produces one
knowledge file per reference and per playbook (methodology merged into
`finops-for-ai.md`), which can exceed ChatGPT's cap. Re-run with the grouped flag:
`./install.sh --tool chatgpt --grouped`. The grouped build packs the same content into
a handful of thematic files in `dist/chatgpt/` and emits a matching routing contract.

**Token budget exceeded on system-prompt injection:** load only the domain references
relevant to your query. For most use cases, `SKILL.md` + 1-2 references is enough.

**Path issues on Windows:** the installer is bash-only. Use WSL2 (`wsl.exe`) or Git
Bash. Native PowerShell is not supported.
