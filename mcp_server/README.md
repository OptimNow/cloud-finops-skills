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

Six tools, all read-only, split across two surfaces.

**References** - long-form provider and discipline files (~300-500 lines each):

| Tool | Purpose |
|---|---|
| `list_references()` | List all references with their FCP metadata. |
| `get_reference(name)` | Fetch the full markdown body of one reference. |
| `find_references(domain?, capability?, phase?, persona?, maturity?)` | Faceted query over the FinOps Capability/Phase frontmatter. |

The reference faceted query supports any combination of:

- `domain` - FinOps Framework domain (e.g. `Optimize Usage & Cost`, `Quantify Business Value`)
- `capability` - FinOps capability (matches both primary and secondary)
- `phase` - `Inform`, `Optimize`, `Operate`
- `persona` - matches both primary and collaborating personas
- `maturity` - `Crawl`, `Walk`, `Run`

**Playbooks** - small named-pattern runbooks (~80-130 lines each):

| Tool | Purpose |
|---|---|
| `list_playbooks()` | List all named-pattern playbooks with their metadata. |
| `get_playbook(name)` | Fetch the full markdown body of one playbook. |
| `find_playbooks(scope?, service?, waste_category?, confidence?)` | Faceted query over the playbook frontmatter. |

The playbook faceted query supports:

- `scope` - `aws`, `azure`, `gcp`, or `cross-cloud`
- `service` - provider service (e.g. `AWS NAT Gateway`); exact-match
- `waste_category` - `orphaned`, `idle`, `overprovisioned`, `commitment-mismatch`,
  `schedule-blindness`, `modernization`, `ai-ml-inefficiency`, `egress`
- `confidence` - `obvious`, `likely`, `possible` (OptimNow three-tier model)

All filters across both surfaces AND together. String matches are case-insensitive
and exact (no substring matching).

**When to use which surface:**

- A **playbook** answers *"how do I detect/fix this specific pattern?"* (zombie NAT,
  snapshot sprawl, idle ELB). It includes problem statement, symptoms, a detection
  query (CUR / KQL / BigQuery SQL / CLI), fix steps, and the anti-pattern.
- A **reference** answers anything broader: billing mechanics, commitment strategy,
  allocation methodology, persona-specific framings, or cross-pattern reasoning.

Neither surface serves current prices. References carry billing *mechanics* -
multipliers, commitment term structure, the shape of a break-even calculation - and
any absolute figure inside them is illustrative and dated inline. For a current
price, use a live pricing tool such as the
[OptimNow AI Pricing Hub](https://optimtoken.optimnow.io) rather than a figure
remembered from a reference body.

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
https://cloud-finops-skills-590a051d.alpic.live/mcp
```

Add it via **Settings -> Connectors -> Add custom connector** and paste that URL.
Do not wire a remote server through `claude_desktop_config.json`: Desktop silently
drops `"type": "http"` entries from that file, and the `npx mcp-remote` bridge adds
enough startup latency to blow Desktop's initialize timeout.

Claude Code can use the same hosted URL without any install:

```bash
claude mcp add --transport http cloud-finops https://cloud-finops-skills-590a051d.alpic.live/mcp
```

For the local clients below, install the package first, then point the client at the
`cloud-finops-mcp` console script.

### Claude Code

Project-level (`.mcp.json` at the repo root) or user-level (`~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "cloud-finops": {
      "command": "cloud-finops-mcp"
    }
  }
}
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

### Windsurf

`~/.windsurf/mcp.json`:

```json
{
  "mcpServers": {
    "cloud-finops": {
      "command": "cloud-finops-mcp"
    }
  }
}
```

### Any other MCP client

The server speaks MCP over stdio. Point any compatible client at `cloud-finops-mcp`
(or `python -m cloud_finops_mcp`).

## Streamable HTTP (hosted deployments)

stdio is the default and is what every local client above spawns. For a hosted
deployment, the same six tools are served over streamable HTTP:

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

Note that a self-hosted MCP server added to Claude as a custom connector will
**not** render the bundled MCP Apps viewer, however conformant it is: Claude
gates interactive rendering to connectors accepted into its Connectors
Directory. See the `Lessons learned` entry in the repo's CLAUDE.md.

## Example tool calls

Agent prompt: *"Use the cloud-finops MCP to find references for the Optimize phase
aimed at Engineering."*

Calls `find_references(phase="Optimize", persona="Engineering")` and gets back the
filtered subset (AWS, Azure, GCP, Bedrock, Databricks, etc.) without loading the full
skill into the prompt.

Agent prompt: *"Pull the AWS reference."*

Calls `get_reference(name="finops-aws")` and gets back the full markdown body
(~300 lines) instead of the entire knowledge base.

Agent prompt: *"Show me the obvious-confidence AWS waste playbooks."*

Calls `find_playbooks(scope="aws", confidence="obvious")` and gets back the list
of high-signal AWS patterns (zombie NAT gateway, orphaned EBS volumes, etc.).

Agent prompt: *"Walk me through the zombie NAT gateway pattern."*

Calls `get_playbook(name="aws-zombie-nat-gateway")` and gets back the ~90-line
runbook (problem, symptoms, detection query, fix, anti-pattern, see-also).

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

## Versioning

The PyPI package version tracks the skill release. The trigger is a
`.claude-plugin/plugin.json` version bump reaching `main`, not a hand-cut tag:
the `auto-tag-on-plugin-bump` workflow reads the new version, creates the
matching `vX.Y.Z` tag, and publishes both the skill release zip and a new
`cloud-finops-mcp` wheel, so the bundled references match what the rest of the
repo ships. Versions must be full three-part semver (`v1.27.0`); the workflow
rejects anything else.

Because a `plugin.json` bump publishes, content PRs never touch it. Version
bumps live in dedicated release PRs that move `plugin.json`,
`.claude-plugin/marketplace.json` `metadata.version`, and this package's
`pyproject.toml` together. See the release-train rule in the repo's CLAUDE.md.

## License

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) - same as the parent
skill. Credit OptimNow.
