# Changelog

What changed for the people who use the skill, the connector or the package, one
version at a time. Newest first. Each GitHub Release still carries the generated
commit list and the attached files; this page is the readable account.

Three surfaces ship on different clocks. The **plugin** (Claude directory, Claude Code
marketplace, the installer) reads the repository, so content reaches it at merge. The
**hosted connector** at `mcp.optimnow.io` and the **PyPI package** ship at the tagged
release. "Unreleased" below means merged to `main`, not yet tagged.

## 1.50.0 (unreleased)

### Ask in your own words

- **Every reference and runbook now declares the questions it answers.** 515 questions
  across the 91 files, in English and French, written the way a FinOps lead, a finance
  partner, an engineer, an AI product owner or an executive asks them: "Our AWS bill
  has NAT gateway charges but I do not think anything uses them", "Which of my RIs are
  about to expire without a renewal decision?", "Nos VM Azure sont arrêtées mais
  toujours facturées : pourquoi ?". The skill searches them when none of its routing
  keywords matches, and the ChatGPT, Gemini and `llms-full.txt` copies carry them
  inside each file.
- **The connector's finders take a `query`.** `find_references(query=...)` and
  `find_playbooks(query=...)` rank the library by the user's sentence: word overlap on
  the declared questions, the title and the section headings, each word weighted by
  its rarity across the library, a named provider halving the files written for
  another provider. Up to five results, each with `match_score`, `matched_question`
  and `suggested_section`, the heading to pass to `get_reference(section=)`. No
  embedding, no network call, and the sentence is never written to the connector's
  zero-result log, only its word count.
- **An Executive persona.** Fifteen questions a CTO, CIO or CFO asks, across ten
  files, from "Are we spending the right amount on cloud for a company our size?" to
  "What would it take to cut our cloud bill by 20% without slowing delivery?". The
  entry points gain a rule for that reader: lead with the decision and its business
  impact, keep billing mechanics to what the decision needs, hand detection queries to
  the team as an annex.
- **The README's "What you can ask, by role" is generated from the index** and checked
  in CI, so every listed question is answered by a file that exists, and the Executive
  block appears with the four other roles.
- **How it was measured.** Before merge, the fifteen probe wordings of the coverage
  battery were run through a local build of the connector in fresh contexts: all
  fifteen called the finders with `query` first and read the expected file, including
  two symptom wordings the connector had never routed before. The cycle on the hosted
  connector follows this release.
- **Ranking fixes from the pre-release review.** "VMs", "RIs" or "GPUs" now match
  their singular, so "which of our VMs run for nothing" finds the idle VM runbook;
  US spellings and word families meet the British text ("license optimization"
  ranks like "licence optimisation", "tagging" meets "tag"); a service name such as
  RDS, EC2, AKS or BigQuery names its provider; a tie goes to the file named after
  the query; and a query made only of common words next to a facet returns the
  facet's list instead of nothing.

### Private overlays

- **A convention for your own layer.** Negotiated rates, tag taxonomy, coverage
  targets, decisions already taken, a client account's profile: none of it belongs in
  the public files, and none of it needs a fork. `docs/OVERLAYS.md` describes a second,
  private skill folder that cites the public sections by heading and never restates a
  mechanic; `docs/overlay-template/` is a minimal one to copy; `scripts/check-overlay.py`
  verifies that the headings it cites still exist, that its questions follow the public
  rules and that it copies no public sentence, after every public release.

### Content

- **Azure Cosmos DB**: the autoscale rule corrected to Microsoft's 66% average-hourly-
  peak rule; autoscale costs nothing extra on multi-region write accounts; the minimum
  throughput floor; backup tiers (the continuous 7-day tier has no storage charge, the
  30- and 35-day tiers bill storage, every restore is charged); Dev/Test pricing offers
  before scheduling. Verified on Microsoft Learn, 9 November 2026.
- **Bring your own licence or licence-included**: the ITAM guide gains a six-step
  decision procedure (is the licence allowed there, which deployment model that forces,
  how each vendor counts cores, how to read the premium on the bill, what each side
  gives up, a default per workload class), a table of the routes open per provider for
  Windows Server, SQL Server and Oracle, and the Software Assurance renewal question.
  Every rule is linked to the vendor's page, read 9 November 2026: the 1 October 2019
  Listed Provider rule, License Mobility, the Flexible Virtualization Benefit, RDS for
  SQL Server Bring Your Own Media, Oracle's two-vCPUs-per-licence count, Cloud SQL
  without BYOL.
- **Microsoft Fabric**: the free mirroring storage allowance stops while a capacity is
  paused.
- **Vertex AI**: the Developer API reroutes `gemini-2.5-pro` and `gemini-2.5-flash` to
  3.8 Flash and 3.5 Flash-Lite from 1 December 2026, billed at the target rates.
- **AWS**: the EC2 Capacity Block upfront fee is amortised in CUR 2.0 and Cost Explorer
  since 6 November 2026 (allocation and commitments files).
- **Databricks**: Unity Gateway budgets count AI Functions spend since 1 November 2026.
- **AI coding tools**: the Claude apps gateway cost report API, OpenTelemetry plan and
  seat attributes, per-developer AWS attribution, pooled budget priority settings.
- **Azure commitments**: the file pruned of internal repetition to fit the token budget;
  no mechanic, figure or dated claim dropped.
- **The Anthropic, open-weight vendor and AI coding tool guides now give ratios and point
  to the AI Pricing Hub for the rate of the day** (maintainer decision of 9 November 2026).
  The Claude table reads as tiers relative to Opus 5 with each model's cache-read
  multiplier (output is 5x input on every row), the Fast mode and Batch sections as the 2x
  and 0.5x multipliers they are, and the tool and Managed Agents meters as mechanics; the
  DeepSeek, Qwen, Kimi and GLM sections keep the peak ratio, the context step, the cache
  multiples and the seat-tier ratios; the Cursor, Claude Code, Copilot and Devin Desktop
  plan tables keep each tier's position relative to the entry tier and the annual-billing
  discount, with the vendor pricing page and the date it was read (9 November 2026 for
  Claude, Copilot, Devin Desktop and Cursor's current lineup). Ask the hub, or
  `compare-llm-models` on the `ai-pricing-hub` connector, for the dollar figure; the
  worked examples keep their one dated figure.
- **Every other price in the reference files now carries its date and region in its own
  paragraph.** The AWS figures (CloudFront plans and
  pay-as-you-go tiers, WAF, S3, S3 Files, EFS, data transfer out, the Cost Explorer API)
  were re-read on the Price List API and the pricing pages on 9 November 2026, the Azure
  networking figures on the Retail Prices API and the Anthropic tool and runtime rates on
  the pricing page the same day. Three corrections: Azure internet egress above 10 TB
  ($0.083 then $0.07 per GB, where the file said $0.05 and $0.04), global VNet peering at
  $0.035/GB each side where the file quoted the $0.01 intra-region rate, and the block
  storage range in the self-hosting reference ($0.08 to $0.17 per GB-month at hyperscaler
  list, not $0.05 to $0.10). The CI guard that keeps a date in every runbook price paragraph now
  covers the references too: a table is dated by the sentence right above it, a rounded
  magnitude ("$50K/month") is not a price, and the worked-example figures that read like
  rates ("a 20% increase on $50,000") sit in an allowlist.
- **1 November scan applied** (eleven items, each read on the provider's page on
  9 November 2026): ECS Managed Instances consolidation and ECS GPU sharing with NVIDIA
  MPS; Aurora Serverless v2 to 384 ACUs on PostgreSQL; RDS storage autoscaling on
  additional Oracle and SQL Server volumes; Neptune online index rebuild; ElastiCache
  data tiering on r7gd and r8gd; the OpenSearch Serverless warm tier; why Savings Plans
  recommendations differ between the management and a member account; GPT-6.1 Terra's
  place in the Bedrock cost tiers and GPT-5.6 in GovCloud; Azure VNet flow logs
  filtering at collection.
- Six section pointers in the question index now cite a full heading where a short
  phrase matched several.
- **Every illustrative price in the runbooks now carries its date and region beside
  the figure**, so an answer that quotes "$0.045 per GB for a NAT gateway" carries
  "us-east-1, November 2026" with it. The AWS figures were re-read on the Price List
  API on 9 November 2026 and had not moved since May; the Azure and Google figures
  were re-read on the Retail Prices API and the pricing pages the same day. Four
  corrections: the EBS tier rates (gp3, gp2 and io2 each their own), the RDS backup
  storage rate and its free allowance, the Azure Premium SSD P30 rate, and the
  Archive tier rate; App Service figures are now given per operating system, since
  a Linux and a Windows P1v3 differ by a factor of two. A CI guard keeps a date in
  every runbook paragraph that carries a price.

### Tell us when it is wrong

- **Two report forms on GitHub.** "Wrong or incomplete answer" and "Question not
  covered", at
  [https://github.com/OptimNow/cloud-finops-skills/issues/new/choose](https://github.com/OptimNow/cloud-finops-skills/issues/new/choose).
  Each asks where you were (plugin, hosted connector, package, another tool), the
  question as you typed it and what came back, and nothing confidential. A confirmed
  report is checked against the provider's documentation, fixed in a content release
  that credits it, and its wording becomes a test question run before every release.
  The connector's "no match" hint now names the form, since the connector itself
  never records what you typed.

### Install and listings

- The **MCP connector is listed in the Claude directory** (live 8 November 2026). The
  README has one button for the plugin and one for the connector, with a sentence on
  the difference, and a five-row install table by tool.
- The hosted connector's machine **suspends instead of stopping** when idle, so the
  first call after a quiet period resumes in a fraction of a second instead of a cold
  start. Takes effect with this release's deploy.
- Tool count corrected to seven everywhere it was still six.

### Upgrading

- **Claude directory plugin**: update the plugin, or reinstall it, to get the question
  index and the Executive rule.
- **Hosted connector** (`https://mcp.optimnow.io/mcp`): nothing to do; `query` appears
  on the two finders when this version is deployed.
- **PyPI package**: `pip install -U cloud-finops-mcp`.
- **ChatGPT and Gemini**: re-upload the knowledge files; the questions travel inside
  them.

### For maintainers

- 22 CI guards, three new: `check-overlay.py` on the overlay template,
  `check-questions.py` on the index (count, vocabulary, duplicates, section resolution,
  personas, `also` links, French), and the README role block `--check`.
- A fresh review of the index PR after merge led to the weighted ranking, the
  named-provider rule, a tokenisation cache (a query from about 124 ms to about 7 ms)
  and the overlay check's alignment with the connector's heading match.
- A test that every declared question, asked verbatim, routes to its own file.
- CLAUDE.md slimmed: its reference sections moved to `docs/DESIGN.md`. Commits and
  pull requests carry no assistant attribution lines.
- **A weekly price-drift check.** `scripts/price-manifest.yaml` lists every
  infrastructure list price the library carries (ninety provider SKUs, written in 150
  places) with the query that reads it on the AWS Price List API,
  the Azure Retail Prices API or Google's catalogue and pricing pages;
  `scripts/check-prices.py` re-reads them and compares with the figures as written;
  the `price-drift` workflow runs it every Saturday and opens one labelled issue when
  a figure has moved or a query broke. A price no API serves (the Snowflake storage
  tiers) is aged instead: the issue lists it under "Check by hand" once the date it
  was read is older than 90 days. It never edits a file. The same script runs in CI
  against recorded fixtures, so a figure edited without its manifest line fails the
  build.

## Earlier versions

Versions up to 1.49.1 have no entry here. Their changes are in the generated notes of
each [GitHub Release](https://github.com/OptimNow/cloud-finops-skills/releases).
