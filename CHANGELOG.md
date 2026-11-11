# Changelog

What changed for the people who use the skill, the connector or the package, one
version at a time. Newest first. Each GitHub Release still carries the generated
commit list and the attached files; this page is the readable account.

Surfaces ship on different clocks. The **Claude directory plugin** reads the
repository, so content reaches it at merge. The **Claude Code marketplace install**
(`cloud-finops@optimnow`) is pinned by the version in `plugin.json`, so it moves at
each tagged release, as do the **hosted connector** at `mcp.optimnow.io` and the
**PyPI package**. The **installer** copies the repository as it is when you run it.
"Unreleased" below means merged to `main`, not yet tagged.

## Unreleased

### Install and listings

- **The advice on plugin and connector now rests on a measurement.** On claude.ai in
  November 2026, with both installed, Claude did not call the connector in any of 34
  chats, and every answer that used the library took it from the plugin: the pair
  behaves as the plugin alone. The
  connector on its own answered 15 of 16 test questions from the library with Claude
  Opus 5.5 and 7 with Claude Sonnet 5.5, against 16 and 13 for the plugin. The plugin's
  listing text, the README, CONCEPTS and INSTALLATION now say so, where they said that
  no measurement existed. So: on Claude, the plugin; the connector for assistants that
  cannot load it.
- CONCEPTS no longer offers the connector "for the views": they went in 1.51.0.
- **The connector's listing in the Claude directory is being updated.** A new
  one-liner and description: what Cloud Financial Management is, what a guide, a
  runbook and a tool are, the current counts (48 guides, 44 runbooks, 7 tools) and
  five example questions, from an executive's to an engineer's. The listing no longer
  declares an MCP App, since the views went in 1.51.0. Submitted on 11 November 2026;
  the public page changes once the review approves it.

### New and corrected content

- **GCP billing export history depends on the dataset location.** Corrected: a
  multi-region dataset backfills from the start of the previous month, a single-region
  one does not, and the pricing export never does (`finops-gcp.md`).
- **Bedrock's daily token quota is now one pool per account and Region**, shared by all
  models since 21 September 2026 (`finops-bedrock.md`).
- **CUR backfill and tag backfill.** How to get history into a new CUR 2.0 or FOCUS
  export, what an organisation change rules out, and the 12-month cost allocation tag
  backfill (`finops-aws-billing.md`).
- **Spotting keys that never cache** from provider usage data when there are no local
  agent logs (`cross-cloud-coding-agent-token-waste` playbook).

### For maintainers

- **The weekly price check retries a throttled request.** Its first run in GitHub
  Actions, on 11 November 2026, read 97 live prices, found no drift in 160 figures and
  still went red: one Azure Retail Prices request out of 47 was answered "429 Too
  Many Requests" and the script did not try again. It now retries a 429, a 5xx or a
  dropped connection up to four times, waiting what the server asks, and the report
  says how many requests were retried. Any other error fails at once, as before.

## 1.51.0 (10 November 2026)

### The connector answers in text, without widgets

- **The connector's interactive views are removed.** Five of its tools linked a view
  (a runbook explorer, a runbook viewer, a guide browser). They never displayed in
  Claude, and they had two costs, both seen on 10 November 2026: Claude placed those
  five tools behind an opt-in step, the "Use" card, so the two search tools and the
  runbook reader were rarely called; and after fetching a runbook the model answered
  "the runbook is above" without giving the detection query. A tool result is now
  the text the model reads and relays. The seven tools keep their names, parameters
  and results.
- **Measured before and after.** With the connector alone on claude.ai, the same
  16 questions were grounded 3 times by Sonnet 5.5 and 11 times by Opus 5.5, almost
  always through the one content tool that had no view. On this version, measured
  the night of the release: 7 by Sonnet 5.5 and 15 by Opus 5.5, with no "Use" card
  and with the query or the commands in the answer. One question, a NAT gateway
  sending 10 TB a month to S3, still gets no call on either model.
- **With the plugin, nothing changes.** In that cycle Claude did not call the
  connector at all when the plugin was present (13 of 16 grounded on Sonnet 5.5, 16
  of 16 on Opus 5.5, all through the skill).

### New and corrected content

- **CloudWatch Logs account-level retention policies.** The skill now warns that an
  account policy replaces a log group's own retention even when that is longer, so a
  short baseline can delete compliance logs, and says to dry-run it first.
- **Microsoft 365 Copilot Business usage-based billing.** New CSP purchases turn it on
  by default from January to March 2027, with a per-user credit limit; it cannot be
  switched off, only capped at zero (`finops-sam.md`).
- **AgentCore Runtime V2.** How a higher rate on fewer memory GB-hours compares with
  V1, and when it does not pay (`finops-agentic.md`).
- **Direct Connect flat-rate pricing.** What the tiers include, what still bills per GB,
  and the multi-Region topology trap (`finops-aws-patterns-networking.md`).
- **RI and Savings Plan credits in a Billing Conductor pro forma.** Why billing-group
  bills show on-demand equivalent by default, AWS's credit method, and the three points
  to settle before using it for chargeback (`finops-chargeback.md`).

### Connector

- **`get_live_figures` checks the file before handing it to the model.** The tool
  relays a file fetched from the OptimToken site, and until now it accepted anything
  carrying a `guide` and a `figures` key. It now returns the file only when it is
  numbers and short labels: no text over 300 characters, no line break, angle bracket
  or link in a label, source links on `optimtoken.optimnow.io` only. A file that fails
  is refused whole and the dated figure in the reference stands. If that site were
  ever tampered with, it could no longer pass a page of instructions or a link to
  another site through the connector. A wrong number would still pass.

### Upgrading

- **Hosted connector** (`https://mcp.optimnow.io/mcp`): nothing to do. The view links
  go when this version is deployed; the seven tools answer as before.
- **PyPI package**: `pip install -U cloud-finops-mcp`. A host that rendered the views
  (MCPJam's emulation did) now shows the plain result, and the `ui://cloud-finops/*`
  resources no longer exist.
- **Claude directory plugin**: the new content is already there if your copy follows
  the directory.
- **Claude Code marketplace** (`cloud-finops@optimnow`): run
  `/plugin update cloud-finops@optimnow` once this version is tagged.
- **ChatGPT and Gemini**: re-upload the knowledge files to get the new content.

### For maintainers

- `mcp_server/tests/test_no_widgets.py` fails if a tool links a view again. It reads
  the tool metadata, the resources, the package files and the tool descriptions. The
  evidence is in `docs/mcp-apps-lessons.md` (entry of 10 November 2026); the removed
  code is at tag `v1.50.0`.
- `CLAUDE.md` goes from 355 to 88 lines: the repository tree moved to
  `docs/STRUCTURE.md`, which `scripts/check-docs-drift.sh` now checks, and the
  cross-repo rules point at `DEPENDENCIES.md`.
- The connector's directory listing needs one pass in the portal after the deploy
  (`docs/directory-submission.md`, section 4).

## 1.50.0 (10 November 2026)

### Ask in your own words

- **Every reference and runbook now declares the questions it answers.** 527 questions
  across the 92 files, in English and French, written the way a FinOps lead, a finance
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
  embedding, no network call. The sentence is capped at 1,000 characters, ranked in
  memory and discarded: it is never cached, and the connector's zero-result log
  carries only its word count. `PRIVACY.md` says so since 9 November 2026.
- **An Executive persona.** Fifteen questions a CTO, CIO or CFO asks, across ten
  files, from "Are we spending the right amount on cloud for a company our size?" to
  "What would it take to cut our cloud bill by 20% without slowing delivery?". The
  entry points gain a rule for that reader: lead with the decision and its business
  impact, keep billing mechanics to what the decision needs, hand detection queries to
  the team as an annex.
- **The README's "What you can ask, by role" is generated from the index** and checked
  in CI, so every listed question is answered by a file that exists, and the Executive
  block appears with the four other roles. Each role is a table: the question on the
  left, the file that answers it on the right.
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

### What changed, as a question you can ask

- **A dated digest of provider changes.** "What changed in cloud billing last month?",
  "What did AWS announce that affects our bill?", "Which retirements and price changes
  are coming?" now have a file that answers them: one table per month for the last 90
  days and one for the changes already scheduled, each row with its date, its effect
  on the bill and the guide that carries the mechanics. It lists what the library
  verified on the provider's own page, not every announcement, and it states the date
  it was reconciled so an answer can say how fresh it is. On the connector it is
  `get_reference(name="finops-whats-new")`, or one month with `section=`.

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
  without BYOL. The licence true-up gets its row in the joint operating model.
- **Microsoft Fabric**: the free mirroring storage allowance stops while a capacity is
  paused.
- **Detection queries that run, and facts re-checked on the provider pages**
  (9 November 2026): the runbook queries that failed or returned nothing on CUR 2.0,
  BigQuery, CloudWatch and PromQL now run, from the SageMaker, load balancer and
  Multi-AZ RDS usage types to orphaned snapshots, GPU memory units and Google's
  detailed billing export. Corrected facts include the Database Savings Plan coverage
  (MemoryDB out; DocumentDB, Keyspaces, Timestream and DMS in; DynamoDB up to 18%), the
  per-model Claude cache-read rates on Bedrock, which instruments reserve capacity, the
  order in which an EDP discount applies, and figures the library stated two ways.
- **Vertex AI**: the Developer API reroutes `gemini-2.5-pro` and `gemini-2.5-flash` to
  3.8 Flash and 3.5 Flash-Lite from 1 December 2026, billed at the target rates.
- **Claude Fable 5.2, Mythos 5.2 and Haiku 5.5** in the Anthropic guide, read on
  Anthropic's pricing page on 9 November 2026. Fable 5.2 (released that day) sits at
  0.8x the Fable 5.1 rate, with the 0.025x cache read and a 2x fast mode; Mythos 5.2 is
  the same model for verified organisations. Haiku 5.5 (7 October) costs a tenth of
  Haiku 4.5 per token below a 100K-token prompt and 5x that above it, for the whole
  request: the guide flags the threshold as the trap to watch.
- **AWS**: the EC2 Capacity Block upfront fee is amortised in CUR 2.0 and Cost Explorer
  since 6 November 2026 (allocation and commitments files).
- **Databricks**: Unity Gateway budgets count AI Functions spend since 1 November 2026.
- **Azure Functions, Azure cost access, AWS security services, acquisitions** (each read
  on the provider's page, 10 November 2026): the oversized Functions plan pattern now
  sends Linux apps to Flex Consumption (virtual network integration, scale to zero) and
  away from the classic Consumption plan, whose Linux hosting retires on 30 September
  2028; on Azure, a cost role shows nothing until the billing account's view-charges
  policy is on; a new section on what the list prices of WAF, GuardDuty, Inspector and
  IAM Access Analyzer hide; and, in the acquisition guide, a step before close on what
  can move (the AWS Seller of Record rule, a subscription holding an active MACC,
  Marketplace SaaS subscriptions, billing history).
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

### Detection through a connector you enabled

- **Rules for running a runbook's detection on your own account.** The library still
  reads no account. When your session also holds a tool that does (your cloud
  provider's connector, a query engine over your billing export, your FinOps
  platform's connector), the skill now tells the model to ask before the first read,
  naming the runbook, the account, the regions and whether the read costs anything; to
  run the Detection step only and hand you the Fix sequence, never run it; to keep the
  runbook's filters and thresholds when it turns a CLI command into an API call; to say
  which accounts and regions it covered before any finding, since an empty result is
  not a clean estate; and to treat a cost platform's figures as the first signal, not
  the confirmation. The rules are a section of `finops-waste-detection-playbooks`,
  "Running a detection through a connected account", written after running eight AWS
  detections on a real account, read-only.
- **What was measured, and what it does not do.** With a mock account and 38 headless
  runs: once the skill is loaded, the model asked before reading in 5 runs out of 5
  (0 out of 2 before the rule). A request worded as an operation ("use the connector
  to check my account", "delete the orphaned volumes") did not load the skill in 8
  runs out of 8, and on the delete order the model removed volumes without a snapshot
  in 3 runs out of 10. So the rule is an instruction, not a lock: name the skill when
  you ask, and give your account connector a read-only role. The hosted connector is
  unchanged, since the Claude directory does not let a connector instruct the model
  about other tools.
- **Every runbook's Detection step is checked as read-only.** A new CI guard reads the
  Detection blocks of all the runbooks: provider CLI calls against a closed list of
  read verbs, SQL limited to SELECT and WITH, no Kusto control command. 83 blocks and
  94 commands and statements pass.

### Tell us when it is wrong

- **Two report forms on GitHub.** "Wrong or incomplete answer" and "Question not
  covered", at
  [https://github.com/OptimNow/cloud-finops-skills/issues/new/choose](https://github.com/OptimNow/cloud-finops-skills/issues/new/choose).
  Each asks where you were (plugin, hosted connector, package, another tool), the
  question as you typed it and what came back, and nothing confidential. A confirmed
  report is checked against the provider's documentation, fixed in a content release
  that credits it, and its wording becomes a test question run before every release.
  The connector's "no match" hint now names the form, since the connector itself
  never records the text of a `query`.

### Install and listings

- The **MCP connector is listed in the Claude directory** (live 8 November 2026). The
  README has one button for the plugin and one for the connector, with a sentence on
  the difference, and a five-row install table by tool.
- The **Windsurf MCP config path** is gone from `install.sh --tool mcp`, INSTALLATION.md
  and the server README: the path printed there could not be confirmed, so Windsurf
  now follows the generic instructions (the JSON shape, in the file Windsurf's own
  documentation names). The Windsurf rules install is unchanged.
- The hosted connector's machine **suspends instead of stopping** when idle, so the
  first call after a quiet period resumes in a fraction of a second instead of a cold
  start. Takes effect with this release's deploy.
- Tool count corrected to seven everywhere it was still six, the submission kit for
  the curated GitHub lists included.
- The **plugin's listing text** (the README the Claude directory shows) is rewritten
  for the least expert reader first: what Cloud Financial Management is, who the
  plugin is for with one example question per role, and the plugin and the connector
  explained in plain words.
- **One piece of advice on plugin and connector**, the same in the plugin listing, the
  README, CONCEPTS and INSTALLATION: on Claude, start with the plugin; the connector
  suits other assistants and search by question; adding both works, but no
  measurement yet shows the pair answering better than the plugin alone. The probe
  cycle after this release measures it.

### Upgrading

- **Claude directory plugin**: the question index and the Executive rule are already
  there if your copy follows the directory; otherwise update or reinstall the plugin.
- **Claude Code marketplace** (`cloud-finops@optimnow`): run
  `/plugin update cloud-finops@optimnow` once this version is tagged.
- **Hosted connector** (`https://mcp.optimnow.io/mcp`): nothing to do; `query` appears
  on the two finders when this version is deployed.
- **PyPI package**: `pip install -U cloud-finops-mcp`.
- **ChatGPT and Gemini**: re-upload the knowledge files; the questions travel inside
  them.

### For maintainers

- 26 CI guards, seven new: `check-overlay.py` on the overlay template,
  `check-questions.py` on the index (count, vocabulary, duplicates, section resolution,
  personas, `also` links, French), the README role block `--check`,
  `check-dated-prices.sh` on the runbooks and the references,
  `check-prices.py --offline` on the price manifest, `render-whats-new.py --check`
  on the digest and its data file, and `check-detection-readonly.py` on the runbooks'
  Detection blocks. The `llms-full.txt` smoke check
  now also proves that every file's questions are in the render.
- A fresh review of the index PR after merge led to the weighted ranking, the
  named-provider rule, a tokenisation cache (a query from about 124 ms to about 7 ms)
  and the overlay check's alignment with the connector's heading match.
- A test that every declared question, asked verbatim, routes to its own file.
- CLAUDE.md slimmed: its reference sections moved to `docs/DESIGN.md`. Commits and
  pull requests carry no assistant attribution lines.
- **A weekly price-drift check.** `scripts/price-manifest.yaml` lists every
  infrastructure list price the library carries (98 provider SKUs, written in 163
  places) with the query that reads it on the AWS Price List API,
  the Azure Retail Prices API or Google's catalogue and pricing pages;
  `scripts/check-prices.py` re-reads them and compares with the figures as written;
  the `price-drift` workflow runs it every Saturday and opens one labelled issue when
  a figure has moved or a query broke. A price no API serves (the Snowflake storage
  tiers) is aged instead: the issue lists it under "Check by hand" once the date it
  was read is older than 90 days. A run that had to skip a provider for want of a
  credential fails and names the provider, and provider error text is cleared of
  account IDs before it reaches the public issue. It never edits a file. The same
  script runs in CI
  against recorded fixtures, so a figure edited without its manifest line fails the
  build.

## Earlier versions

Versions up to 1.49.1 have no entry here. Their changes are in the generated notes of
each [GitHub Release](https://github.com/OptimNow/cloud-finops-skills/releases).
