# Cloud FinOps by OptimNow

Cloud Financial Management, also called FinOps, is the discipline of knowing what a
company spends on cloud and AI, deciding what that spend should be, and acting on the
gap. This plugin gives Claude that expertise: how cloud and AI providers bill, where
money is wasted, how to commit, allocate and forecast, and how to run the practice.
It is written from enterprise delivery experience, aligned with the FinOps Foundation
framework, and updated weekly from the providers' own documentation.

## Who it is for

You do not need to know the vocabulary. Ask the question the way you would ask a
colleague, in English or in French, and Claude finds the guide that answers it.

- **Executives (CTO, CIO, CFO).** Decisions and their business impact, with the
  mechanics kept to what the decision needs. *"Are we spending the right amount on
  cloud for a company our size?"*
- **Finance, procurement and product.** Budgets, forecasts, contracts, what to charge
  back to whom. *"Our AWS enterprise agreement renews in six months. What should we
  check on the term sheet before signing?"*
- **FinOps practitioners.** Allocation, commitments, KPIs, the operating model.
  *"A third of our bill is unallocated. How do we reach a defensible allocation of
  shared costs?"*
- **Engineers and platform teams.** What to change, and the query to run in your own
  account to find it. *"Our NAT gateway bill is higher than the compute it serves.
  Where does it come from and what do we change?"*

When the question is about your own resources, Claude cannot see your cloud account:
it hands you the detection query to run yourself and reads the result with you.

## Plugin or connector?

The same library exists in two forms in the Claude directory. If you use Claude, start
with this plugin. Adding the connector as well works and changes nothing: in our test
of November 2026, with both installed, Claude never called the connector, and every
answer that used the library took it from the plugin.

- **This plugin** adds the knowledge to Claude as text files it reads when a cost
  question comes up. Nothing runs, nothing is sent anywhere: it works like a reference
  book on the desk. Add it once and ask.
- **The MCP connector**, listed separately, is a small service Claude can query for the
  same library, one guide or runbook at a time, by topic or by your question. It works
  like a librarian you can call. It suits sessions where you want Claude to search the
  library rather than carry it, and assistants other than Claude. On its own, in the
  same test, it answered 15 of 16 questions from the library with Claude Opus 5.5 and
  7 with Claude Sonnet 5.5, against 16 and 13 for this plugin.

## What the plugin contains

Text files only, under `skills/cloud-finops/`:

- `SKILL.md`, the entry point: how to reason about a cost question, which guide answers
  which topic, and the rule on price figures (mechanics are durable, absolute prices
  are not, so a current price comes from a live source and carries its date).
- `references/`, one guide per provider or discipline: AWS, Azure, GCP, OCI, Bedrock,
  Azure OpenAI, Vertex AI, Anthropic billing, Databricks, Microsoft Fabric, Snowflake,
  Kubernetes, tagging, allocation and showback, chargeback, anomaly management, KPIs,
  forecasting, contracts, AI cost management, agentic FinOps, SaaS and IT asset
  management, GreenOps, and a dated digest of what the providers changed over the
  last 90 days and what is already scheduled.
- `playbooks/`, one short runbook per named waste pattern (idle NAT gateway, snapshot
  sprawl, expiring reservation with no decision, oversized GPU instance, and more):
  symptoms, a detection query you run in your own account, the fix and the
  anti-pattern.
- Every guide and runbook declares, in its header, the questions it answers, written
  the way people ask them, in English and in French. That is how a question in your
  own words finds its file.
- `POWER.md`, the same entry point in the format the Kiro IDE reads. Claude ignores it.

## What the plugin does not do

It runs no code. It declares no hooks, no commands, no agents and no MCP server. It
sends no data anywhere and reads nothing from your machine: the model reads these
files as context and answers from them. It cannot see your cloud account; for a
question about your own resources it hands you the detection query to run yourself.
If your session also holds a connector to your cloud account or your cost platform,
the skill tells the model to ask you before the first read, to run a runbook's
detection only and never its fix, and to say which accounts and regions it covered.
That is an instruction to the model, not a lock, and it acts only once the skill is
loaded: give that connector a read-only role.
The skill names one public website for current prices, the OptimNow AI Pricing Hub;
whether the model opens it is decided in your session, and the plugin itself makes
no request. Where a reference quotes a dated figure from one of that site's guides, the
skill also names the `get_live_figures` tool of the separate MCP connector above, for
sessions where you have added that connector; without it, the skill gives the guide's
link.

## Updates

Content is updated weekly from primary provider sources. The Claude directory serves
each merge to the `main` branch of the repository; an install from the Claude Code
marketplace moves at each tagged release.

If an answer was wrong or incomplete, or a question found nothing, report it at
<https://github.com/OptimNow/cloud-finops-skills/issues/new/choose> with the
wording you used. Each confirmed report is checked against the provider's own
documentation, fixed, and becomes a test question run before every release.

## License and source

Licensed under CC BY-SA 4.0 (see `LICENSE`). Credit OptimNow when you reuse the
content. The full repository, with the installer for other tools, the MCP server,
the contribution guide and the change history, is at
<https://github.com/OptimNow/cloud-finops-skills>.
