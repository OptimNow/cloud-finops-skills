# cloud-finops-mcp

<!-- mcp-name: io.github.OptimNow/cloud-finops -->

MCP server exposing the [OptimNow Cloud FinOps skill](https://github.com/OptimNow/cloud-finops-skills)
(reference library + named-pattern playbooks) as queryable tools for any
MCP-aware client (Claude Code, Cursor, Codex CLI, Windsurf, Aider, Cline, etc.).

The skill itself ships in canonical Claude Agent-Skills format and is also installable
via the cross-tool installer (`./install.sh`) for direct context injection. This MCP
server is the **enrichment path**: instead of loading the full skill into the
prompt, the agent calls tools to discover, filter, and fetch only what it needs.

## What the server exposes

Seven tools, all read-only: three over references, three over playbooks, and
`get_live_figures`, the one tool that leaves the bundled content (see "Live figures"
below).

**References** - long-form provider and discipline files. They vary by more than
tenfold, from ~160 lines (roughly 2K tokens) to ~1,000 lines (roughly 15K tokens), so
budget context per file rather than assuming a uniform size. Every listing entry
carries an `approx_tokens` hint for exactly that reason.

| Tool | Purpose |
|---|---|
| `list_references()` | Browse the knowledge library: what guidance exists, with its FinOps Framework facets and an `approx_tokens` size hint. |
| `get_reference(name, section?)` | Read one guide - mechanics, decision rules, worked examples. Whole by default, or one H2/H3 section when the question is narrower than the file. |
| `find_references(query?, domain?, capability?, phase?, persona?, maturity?, persona_primary_only?)` | Route a FinOps question (commitment sizing, chargeback design, ...) to the guides that serve it, by FinOps Framework facet or by `query`: the question in the user's own words, ranked against the questions each guide declares it answers. |

The reference faceted query supports any combination of:

- `domain` - FinOps Framework domain (e.g. `Optimize Usage & Cost`, `Quantify Business Value`)
- `capability` - FinOps capability (matches both primary and secondary)
- `phase` - `Inform`, `Optimize`, `Operate`
- `persona` - matches both primary and collaborating personas
- `persona_primary_only` - optional flag: match `persona` against the primary
  list only. Broad personas (Engineering) collaborate on nearly every file,
  so the default match barely narrows; the flag is the reading-list cut.
- `maturity` - `Crawl`, `Walk`, `Run`
- `query` - the question in the user's own words, English or French. Ranks the
  facet-filtered guides by the `questions:` each declares in its frontmatter, then
  by title and headings, and returns at most five, each with `match_score`,
  `matched_question` and `suggested_section` (the heading to pass to
  `get_reference`). Word overlap only, each word weighted by its rarity across the
  index and a named provider halving the files written for another provider: no
  embedding, no network call

The listing prints the primary facets only. Secondary capabilities and
collaborating personas are still fully filterable through `find_references`;
they are kept out of the payload because they do not help a caller *choose*
while costing a sixth of a call that every session makes.

### Section-level retrieval

`get_reference` takes an optional `section`. It exists because the largest
references run to about 15K tokens and the Azure pattern catalogue
(`finops-azure-patterns`) is an enumerated list, and an agent asking about storage
lifecycle wants one heading out of them, not the file. The AWS pattern catalogue
was split by service family on 2026-10-22 (`finops-aws-patterns-compute`,
`-storage`, `-databases`, `-networking`, `-other`, with `finops-aws-patterns` as
the index), so it is fetched by file.

```python
get_reference("finops-azure-patterns")                       # ~8,800 tokens
get_reference("finops-azure-patterns", section="storage")    # ~2,700 tokens
get_reference("finops-aws-billing", section="billing hierarchy")  # ~2,700 of ~13,000 tokens
```

- Matches **H2 and H3** headings, case-insensitively and partially, so a natural
  phrase works. A heading's trailing count is ignored, so `"storage optimization
  patterns"` finds `"Storage Optimization Patterns (16)"`. H3 is not an extra:
  the Azure catalogue carries a single H2, so an H2-only splitter would leave it
  un-sectionable.
- An H2 span includes its H3 children; an H3 span stops at its sibling. Headings
  inside fenced code blocks are not boundaries.
- The returned `content` is prefixed with the reference's H1 so the chunk is
  self-describing, and the payload carries `partial: true`, `section`,
  `section_level` and `full_lines`.
- **A section that matches nothing is a loud failure.** It returns
  `available_sections` - every heading in the file - plus near-miss suggestions,
  rather than silently handing back the whole body the caller was trying to
  avoid. That error is ~140 tokens, so a wrong first guess costs almost nothing.
- Omitting `section` is unchanged in every respect: `content` is the file
  verbatim, frontmatter included.

**Playbooks** - small named-pattern runbooks (~90-150 lines, ~3-8 KB each):

| Tool | Purpose |
|---|---|
| `list_playbooks()` | Browse the waste runbooks: which patterns of idle, orphaned, overprovisioned or leaking spend have a ready-made runbook. Carries the same `approx_tokens` hint. |
| `get_playbook(name)` | Read one runbook: symptoms, detection queries, fix, anti-pattern. |
| `find_playbooks(query?, scope?, service?, waste_category?, confidence?)` | "We are wasting money on X - how do I find and fix it?" - filter runbooks by provider, service, waste category, confidence, or pass the symptom in the user's words as `query` and get the runbooks ranked by the questions each one declares. Also the route for questions about your own estate ("which of my RIs are about to expire"): the server cannot see your account, so the runbook's detection query is the answer it hands over. |

The playbook faceted query supports:

- `scope` - `aws`, `azure`, `gcp`, or `cross-cloud`
- `service` - provider service (e.g. `AWS NAT Gateway`); exact-match
- `waste_category` - `orphaned`, `idle`, `overprovisioned`, `commitment-mismatch`,
  `schedule-blindness`, `modernization`, `ai-ml-inefficiency`, `egress`
- `confidence` - `obvious`, `likely`, `possible` (OptimNow three-tier model)
- `query` - the symptom in the user's own words; the same ranking as for
  references, over each runbook's declared questions, title and service

All filters across both surfaces AND together. String matches are case-insensitive
and exact (no substring matching).

**When to use which surface:**

- A **playbook** answers *"how do I detect/fix this specific pattern?"* (zombie NAT,
  snapshot sprawl, idle ELB). It includes problem statement, symptoms, a detection
  query (CUR / KQL / BigQuery SQL / CLI), fix steps, and the anti-pattern.
- A **reference** answers anything broader: billing mechanics, commitment strategy,
  allocation methodology, persona-specific framings, or cross-pattern reasoning.

The server stores no prices. References carry billing *mechanics* - multipliers,
commitment term structure, the shape of a break-even calculation - and any absolute
figure inside them is illustrative and dated inline. What it can fetch live is narrower
than a price lookup: the current figures of a named OptimToken guide, through
`get_live_figures` below, passed through as the guide publishes them (a guide's worked
example can carry a dated price, such as an on-demand hourly rate). It serves no
other current price and says nothing about other tools: a figure in a reference is
illustrative and dated inline. The skill's own "Price figures" rule (in `SKILL.md`) is
where the OptimNow AI Pricing Hub is suggested.

### Live figures

Some references quote a figure from an [OptimToken](https://optimtoken.optimnow.io)
guide with the day it was read ("measured on the 2026-10-25 OptimToken catalogue").
The quoted figure goes stale; the guide's own `figures.json`, rebuilt with the page
every night, carries the current one.

| Tool | Purpose |
|---|---|
| `get_live_figures(guide)` | The current value of a figure a reference quotes with a date. Fetches `https://optimtoken.optimnow.io/guides/<guide>/figures.json` and returns it unchanged. |

Guides with figures today: `savings-plans-vs-reserved-instances`, `arm-against-x86`,
`batch-api-economics`. The authoritative list is the "Figures as JSON" lines of
<https://optimtoken.optimnow.io/llms.txt>; more guides will appear there.

```python
get_live_figures("savings-plans-vs-reserved-instances")
# {"document": {"guide": "savings-plans-vs-reserved-instances",
#               "title": "...", "url": "https://optimtoken.optimnow.io/guides/...",
#               "page": "...", "dataSource": "compute",
#               "snapshotDate": "2026-10-25", "dateModified": "2026-10-25",
#               "note": "...", "figures": {...}},
#  "fetched_at": "2026-10-25T09:50:48Z", "source": "live",
#  "note": "Figures from the OptimToken catalogue of 2026-10-25, ..."}
```

- **The document is returned as received**, nested under `document` so none of its
  keys is shadowed. Figures are not recomputed or rounded; discounts are fractions
  (`0.2743` is 27.4%), and each key names a median, a range or a count.
  `snapshotDate` is the catalogue the figures were computed from and is the date to
  quote them by.
- **Checked before it is returned.** Whatever the file holds lands in a model's
  context, so a file is returned whole or refused whole: numbers, and text short
  enough to be a label (300 characters, 10,000 across the file), with no line
  break, angle bracket or link in it; `url` and `page` on `optimtoken.optimnow.io`;
  dates as `YYYY-MM-DD`. A refused file returns `{"error", "fallback"}`, and the
  error never quotes the file. This bounds what a tampered site can say to a
  model; it cannot tell a wrong number from a right one.
- **Cache:** six hours per guide in process memory (the file changes once a day),
  the guide list likewise. A cached answer says `"source": "cached"` with
  `cache_age_seconds`; `fetched_at` stays the time of the original fetch. Failures
  are not cached.
- **A miss** (HTTP 404) returns `{"error", "available_guides", "suggestions"}`, the
  list read from llms.txt and the suggestions by string distance, like the other
  tools' misses. Any other failure (timeout, HTTP error, invalid JSON, an envelope
  without `guide` or `figures`) returns `{"error", "fallback"}`: the dated figure in
  the reference stands, quoted with its date. A slug outside `^[a-z0-9-]{1,80}$` is
  rejected before any request. The tool never raises.
- **The request:** one HTTPS GET to `optimtoken.optimnow.io` (two on a miss, the
  second for llms.txt), 5-second timeout, 128 KiB body cap, redirects followed only on
  that host, User-Agent `cloud-finops-mcp/<version>
  (+https://github.com/OptimNow/cloud-finops-skills)`. Standard library only, no
  new dependency. It carries the slug and nothing from the conversation.

## Install

```bash
pip install cloud-finops-mcp
```

Or run without installing via [`uv`](https://docs.astral.sh/uv/):

```bash
uvx cloud-finops-mcp
```

## Configure your MCP client

### Claude.ai / Claude Desktop (hosted - nothing to install)

The server is deployed at:

```
https://mcp.optimnow.io/mcp
```

(Until 30 September 2026 it was `https://cloud-finops-mcp.fly.dev/mcp`. That host
still answers tool calls but is deprecated; re-add the connector with the URL above.)

The simplest route is the connector's Claude directory listing,
<https://claude.ai/directory/optimnow-cloud-finops>: one click, with that URL already set. To add it by
hand, use **Settings -> Connectors -> Add custom connector** and paste exactly that
URL - the `/mcp` path, no trailing slash.

Do not wire a remote server through `claude_desktop_config.json`: Desktop silently
drops `"type": "http"` entries from that file, and the `npx mcp-remote` bridge adds
enough startup latency to blow Desktop's initialize timeout.

Claude Code can use the same hosted URL without any install:

```bash
claude mcp add --transport http cloud-finops https://mcp.optimnow.io/mcp
```

For the local clients below, install the package first, then point the client at the
`cloud-finops-mcp` console script.

### Claude Code

Project-level, in `.mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "cloud-finops": {
      "command": "cloud-finops-mcp"
    }
  }
}
```

For user scope there is no `~/.claude/mcp.json` - Claude Code does not read that
path. Register the server once for every project with:

```bash
claude mcp add --scope user cloud-finops -- cloud-finops-mcp
```

Restart Claude Code, then run `/mcp` to confirm the server is connected.

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cloud-finops": {
      "command": "cloud-finops-mcp"
    }
  }
}
```

### Codex CLI

`~/.codex/config.toml`:

```toml
[mcp_servers.cloud-finops]
command = "cloud-finops-mcp"
```

### Any other MCP client

The server speaks MCP over stdio. Point any compatible client at `cloud-finops-mcp`
(or `python -m cloud_finops_mcp`). Clients that read an `mcpServers` JSON block,
Windsurf among them, take the Cursor snippet above, in the file their own
documentation names.

## Streamable HTTP (hosted deployments)

stdio is the default and is what every local client above spawns. For a hosted
deployment, the same seven tools are served over streamable HTTP:

```bash
cloud-finops-mcp --transport http
```

- Route is `/mcp` (the SDK default, and what hosting platforms probe).
- Binds `0.0.0.0`; port comes from `$PORT`, falling back to `8000`. `--host` and
  `--port` override both.
- Runs **stateless**: a new transport and session per request, no server-side
  session affinity. The server is a read-only retrieval surface with no
  per-user state, so this costs nothing and is what allows horizontal or
  serverless scaling.
- No extra dependency. `uvicorn` and `starlette` already ship as hard
  dependencies of `mcp`, so there is no `[http]` extra to install.

Nothing about the tools changes between transports. `tests/test_e2e_http.py`
mirrors the stdio suite over HTTP so the two cannot silently diverge.

## No widgets

Until 1.50.0 five tools linked an MCP Apps view (a playbook explorer, a playbook
viewer, a reference browser). 1.51.0 removed them, the HTML and the `ui://`
resources included. They never rendered in claude.ai, and its tool search listed
exactly those five tools as needing an opt-in step before they could be called,
while `get_reference`, which had no view, was called freely. A tool result is now
plain structured data that the model reads and relays.
`tests/test_no_widgets.py` fails if a tool links a view again. The record is in
`docs/mcp-apps-lessons.md`; the code is at tag `v1.50.0`.

## Example tool calls

Agent prompt: *"Use the cloud-finops MCP to find references for the Optimize phase
aimed at Engineering."*

Calls `find_references(phase="Optimize", persona="Engineering")` and gets back the
filtered subset (AWS, Azure, GCP, Bedrock, Databricks, etc.) without loading the full
skill into the prompt.

Agent prompt: *"Pull the AWS reference."*

Calls `get_reference(name="finops-aws")` and gets back the full markdown body
(about 670 lines, roughly 9K tokens) instead of the entire knowledge base. Check the
size range noted above before fetching several.

Agent prompt: *"What does the Azure pattern catalogue say about storage?"*

Calls `get_reference(name="finops-azure-patterns", section="storage")` and gets back
the storage chapter (~2,700 tokens) rather than the whole catalogue (~8,800).

Agent prompt: *"Show me the obvious-confidence AWS waste playbooks."*

Calls `find_playbooks(scope="aws", confidence="obvious")` and gets back the list
of high-signal AWS patterns (zombie NAT gateway, orphaned EBS volumes, etc.).

Agent prompt: *"Our AWS bill has NAT gateway charges but I do not think anything
uses them."*

Calls `find_playbooks(query="AWS bill has NAT gateway charges but nothing uses them")`
and gets back the zombie NAT gateway runbook first, with the question it matched,
ranked by the questions each runbook declares it answers (English and French).

Agent prompt: *"Walk me through the zombie NAT gateway pattern."*

Calls `get_playbook(name="aws-zombie-nat-gateway")` and gets back the ~90-line
runbook (problem, symptoms, detection query, fix, anti-pattern, see-also).

Agent prompt: *"Is the Compute Savings Plan premium still about 9 points?"*

Calls `get_live_figures(guide="savings-plans-vs-reserved-instances")` and reads
`figures.clouds.AWS.flexibilityPremium.oneYear.median` from the current file, quoted
with its `snapshotDate`.

## When to use this vs the installer

| If you... | Use |
|---|---|
| Want the skill loaded as static context for every chat | The cross-tool installer (`./install.sh`) |
| Have a big-codebase session with limited context budget | The MCP server (fetch on demand) |
| Want to filter references by FinOps domain/capability/phase/persona/maturity | The MCP server (`find_references`) |
| Use a client that doesn't support MCP | The cross-tool installer |

The two paths are complementary. You can install both.

## Development

```bash
git clone https://github.com/OptimNow/cloud-finops-skills.git
cd cloud-finops-skills/mcp_server
python scripts/sync_references.py        # populate src/cloud_finops_mcp/data/
pip install -e ".[dev]"
pytest
```

The suite runs offline: the `get_live_figures` tests replace the HTTP fetch with
saved copies under `tests/fixtures/live_figures/`.

## Versioning

The PyPI package version tracks the skill release. The trigger is a
`plugins/cloud-finops/.claude-plugin/plugin.json` version bump reaching `main`, not a hand-cut tag:
the `auto-tag-on-plugin-bump` workflow reads the new version, creates the
matching `vX.Y.Z` tag, and publishes both the skill release zip and a new
`cloud-finops-mcp` wheel, so the bundled references match what the rest of the
repo ships. The same workflow redeploys the hosted connector from that tag and
checks the version and the catalogue it answers. Versions must be full
three-part semver (`v1.27.0`); the workflow rejects anything else.

Because a `plugin.json` bump publishes, content PRs never touch it. Version
bumps live in dedicated release PRs that move four files together: `plugin.json`,
`.claude-plugin/marketplace.json` `metadata.version`, this package's
`pyproject.toml`, and `server.json` - which carries the version twice, in the
top-level `version` and in `packages[0].version`, both CI-gated since August 2026.
See the release-train rule in the repo's CLAUDE.md.

## Data handling

The server holds no account, credential or user data and cannot see your cloud
estate: six of the seven tools read the bundled markdown files and keep no copy of
the request. The seventh, `get_live_figures`, is the one tool that makes an outbound
request: one HTTPS GET to `optimtoken.optimnow.io`, an OptimNow site, carrying the
guide slug and the User-Agent above and nothing from the conversation (a second GET,
for the public llms.txt, when the slug is not found). OptimToken keeps its standard
web access log (Vercel). The hosted connector writes one application-log line per request without the
arguments and, for a lookup that matched nothing, the arguments that missed, which
can include a phrase the model copied from your question (the free-text `query` of
the two finders is never written to that log, only its word count). The hosting
platform keeps
the standard HTTP access log. What is logged, where it lives and for how long is in
[PRIVACY.md](https://github.com/OptimNow/cloud-finops-skills/blob/main/PRIVACY.md).

## License

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) - same as the parent
skill. Credit OptimNow.
