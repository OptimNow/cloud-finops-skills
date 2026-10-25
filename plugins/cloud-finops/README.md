# Cloud FinOps by OptimNow

A Claude plugin that carries one skill: FinOps guidance for cloud, AI, SaaS and
data-platform spend, written from enterprise delivery experience and aligned with
the FinOps Foundation framework.

## What the plugin contains

Text files only, under `skills/cloud-finops/`:

- `SKILL.md`, the entry point: how to reason about a cost question, a routing table
  from query topic to reference file, and the rule on price figures (mechanics are
  durable, absolute prices are not, so a current price comes from a live source and
  carries its date).
- `references/`, one guide per provider or discipline: AWS, Azure, GCP, OCI, Bedrock,
  Azure OpenAI, Vertex AI, Anthropic billing, Databricks, Microsoft Fabric, Snowflake,
  Kubernetes, tagging, allocation and showback, chargeback, anomaly management, KPIs,
  AI cost management, agentic FinOps, SaaS and IT asset management, GreenOps.
- `playbooks/`, one short runbook per named waste pattern (idle NAT gateway,
  snapshot sprawl, expiring reservation with no decision, oversized GPU instance,
  and more): symptoms, a detection query you run in your own account, the fix and
  the anti-pattern.
- `POWER.md`, the same entry point in the format the Kiro IDE reads. Claude ignores it.

## What the plugin does not do

It runs no code. It declares no hooks, no commands, no agents and no MCP server. It
sends no data anywhere and reads nothing from your machine: the model reads these
files as context and answers from them. It cannot see your cloud account; for a
question about your own resources it hands you the detection query to run yourself.
The skill names one public website for current prices, the OptimNow AI Pricing Hub;
whether the model opens it is decided in your session, and the plugin itself makes
no request. Where a reference quotes a dated figure from one of that site's guides, the
skill also names the `get_live_figures` tool of the separate MCP connector below, for
sessions where you have added that connector; without it, the skill gives the guide's
link.

The hosted MCP connector that serves the same library is a separate product, added
on its own, so that the content is not loaded twice in one session.

## Updates

Content is updated weekly from primary provider sources. Every merge
to the `main` branch of the repository is a new plugin version.

## License and source

Licensed under CC BY-SA 4.0 (see `LICENSE`). Credit OptimNow when you reuse the
content. The full repository, with the installer for other tools, the MCP server,
the contribution guide and the change history, is at
<https://github.com/OptimNow/cloud-finops-skills>.
