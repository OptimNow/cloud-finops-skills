# Changelog

What changed for the people who use the skill, the connector or the package, one
version at a time. Newest first. Each GitHub Release still carries the generated
commit list and the attached files; this page is the readable account.

Surfaces ship on different clocks. The **Claude directory plugin** reads the
repository, so content reaches it at merge. The **Claude Code marketplace install**
(`cloud-finops@optimnow`) is pinned by the version in `plugin.json`, so it moves at
each tagged release, as do the **hosted connector** at `mcp.optimnow.io` and the
**PyPI package**. The **installer** copies the repository as it is when you run it.
An "Unreleased" section, when there is one, lists what is merged to `main` and not
yet tagged.

## Unreleased

### New and corrected content

- **AWS regional NAT gateway, Cost Explorer forecast horizon, CloudTrail free copy.**
  `finops-aws-patterns-networking.md` no longer tells you to deploy one NAT gateway per
  Availability Zone as the only option: a regional NAT gateway is one route for all
  zones, but it is billed per zone it spans, so moving from three zonal gateways to one
  regional gateway does not cut the hourly charge. `finops-forecasting.md` adds that Cost
  Explorer forecasts up to 18 months ahead and not on a grouped chart, and
  `finops-aws-patterns-other.md` that only the first copy of CloudTrail management events
  is free, so team trails that duplicate an organisation trail are billed.
- **AWS invoices and payment currency.** `finops-aws-billing.md` adds that AWS issues an
  invoice on each one-time purchase (an All Upfront RI is charged immediately) as well as
  at period close, and that with a non-USD payment currency the rate is set when the
  invoice is created, so compare it with the treasury rate before switching currency.
- **SageMaker training plans.** `finops-aws-commitments.md` adds them as a capacity
  reservation, not a discount: paid up front for one target resource, final (no
  cancellation or resizing, extension only), not Savings Plan coverage.
- **Blended unit rates and mix effects.** `finops-kpis-benchmarking.md` warns that a
  blended rate can rise after a good decision, such as deleting cold-tier data, and
  says to hold the mix constant or split by tier and show total cost beside it.
- **AWS commitment sharing is now set per commitment.** `finops-aws-billing.md` said RI
  and Savings Plans sharing is set per account. Since 17 November 2026 each commitment
  can carry its own sharing, scoped with a Cost Category, and a credit can be split and
  moved to the team that should use it; `finops-aws-commitments.md` explains how to keep
  one business unit's plan off another's usage, and what that costs in utilisation.
- **OpenAI background windows replace Flex for work that can wait.**
  `finops-ai-self-hosted-vs-managed.md` said OpenAI offers Batch and Flex at 50% off.
  Flex is not offered on new models and is being wound down; the Responses API's
  two-hour and eight-hour background windows bill at 0.7x and 0.6x Standard (beta,
  17 November 2026), and Batch at 0.5x stays cheaper where the model offers it.
- **AWS savings from native CUR 2.0 columns.** `finops-allocation-showback.md` maps the
  14 opt-in `cost_analytics_` columns (20 November 2026) to the FOCUS cost columns, so
  negotiated and commitment savings need no price-list join, and names their gaps.
- **Splitting a shared NAT gateway bill on AWS.** `finops-allocation-showback.md` and
  `finops-aws-patterns-networking.md` add Networking flexible cost allocation
  (16 November 2026), which splits NAT gateway, in-Region EC2 and VPC peering data
  charges by the resource that generated them, and what Flow Logs must still cover.
- **Anthropic Linked billing.** `finops-anthropic.md`: a customer can pay for its own
  Claude usage in your app (beta, 17 November 2026); unit economics need the per-request
  `billing_policy`, and the customer's spend cap can stop the feature for that customer.
- **Vertex AI Deferred tier.** `finops-vertexai.md` adds the Deferred tier (GA
  16 November 2026, 50% off, Interactions API) and when to pick it over Batch or Flex.
- **Copilot code review on Azure Repos is billed to Azure.** `finops-ai-dev-tools.md`
  (17 November 2026): budget it in Azure Cost Management, and cap Adaptive effort with
  the maximum review effort level.
- **Snowflake prompt caching for AI_COMPLETE.** `finops-snowflake.md` (GA 18 November
  2026): put shared instructions first and row data last, and where to measure the hits.
- **What's new digest** runs to 21 November 2026.
- **Azure reservation renewals now bring up the 1 February 2027 price rise.** A question
  about buying or renewing Azure reservations is answered from
  `finops-azure-commitments.md`, which covered the exchange retirement of that date and
  only pointed elsewhere for the price rise on the same day. Its section "Commitment
  liquidity after February 2027" now states the rise (North Europe 17%, France 11%, West
  Europe and Norway 9%, Southeast Asia 8%) and what a reservation bought before the date
  keeps. Renewal questions now reach that section through the connector, and the
  unused-reservation playbook names the rise too.

### Install and listings

- The Claude Code marketplace description counts 49 runbooks; it still said 44.

## 1.53.0 (20 November 2026)

### New and corrected content

- **Azure price rise of 1 February 2027: what takes it and how to size it.**
  `finops-azure.md` now says which VM series take which rise (the v3 to v6 and AMD v7
  series take the regional rise; the listed v1 and v2 series take about 25% in every
  region instead, as an account team states it in writing, with no public page), that
  Managed Disks and every Azure Files tier but Transaction Optimized are in scope, what
  a reservation and a savings plan protect, and how to size the impact meter by meter,
  phased by reservation expiry. `finops-azure-commitments.md` adds the NP and HC
  retirement on 31 May 2027.
- **Savings sized net of the cost of acting.** `finops-waste-detection-playbooks.md`
  now says to size a potential saving after the engineering, test and migration cost
  of the change, with its break-even, and to record a change that breaks even after
  the workload's planned end, or that cuts already committed usage, with that reason
  rather than report it as a missed saving.
- **Third-party "guaranteed" commitments.** `finops-aws-commitments.md` now explains
  the 30-day or one-year "insured" commitments some vendors sell: the Reserved Instance
  or Savings Plan is bought in your own accounts, AWS still bills its whole term, and the
  protection is the vendor's contractual promise of a resale or rebate, paid for with a
  share of the savings. It lists the questions to ask before buying.
- **Azure OpenAI regional deployments cost more than Data Zone in Europe.**
  `finops-azure-openai.md` said a Regional deployment costs about the same as Data
  Zone. That holds in East US 2 (+10% over Global), not in Europe: Azure's price list
  shows +21% in Sweden Central, Germany West Central, France Central and UK South and
  +32% in West Europe, against a flat +10% for Data Zone. Where an EU Data Zone meets
  the residency requirement, it is the cheaper in-region option.
- **AI gateway budgets, ledgers and new models.** `finops-ai-dev-tools.md` explains why a
  LiteLLM hard budget refuses parallel Claude Code calls while little has been spent: it
  reserves each call's full output ceiling before sending it. It gives the two remedies,
  sizing the budget for the ceiling or lowering it with `CLAUDE_CODE_MAX_OUTPUT_TOKENS`.
  `finops-for-ai.md` adds a two-pass check of the gateway ledger against the invoice
  (tokens first, to find traffic that bypassed the gateway, then cost, to find a wrong
  rate) and warns that LiteLLM records a model missing from its price map at zero spend.
- **Hosted AI gateways become the invoice.** `finops-for-ai.md` now says that a gateway
  that bills you (OpenRouter, Cloudflare AI Gateway with Unified Billing) passes provider
  token prices through with no markup and charges a fee on the credit purchase instead.
  Credit purchases are prepayments, not usage, and cost is allocated from the gateway's
  per-request logs.
- **AWS Savings Plan return.** `finops-aws-commitments.md` adds the return of a
  Savings Plan bought in error to the portfolio liquidity mechanisms, with its limits:
  $100 an hour or less, and a deadline at seven days or at the end of the calendar
  month (UTC), whichever comes first, so a plan bought on the 30th can be returned
  only until the next day ends. It adds the yearly quota, the accounts that may
  request it, and the deletion of a queued purchase before it starts. Reported in
  issue 379.
- **Snapshots that keep billing after deletion.** `aws-snapshot-sprawl` gains a step:
  check the EBS Recycle Bin before declaring a clean-up saving, because a deleted
  snapshot that matches a retention rule is billed until the retention expires.
  `finops-aws-patterns-storage.md` adds the same mechanic and EC2 Fast Launch for
  Windows, whose temporary instances and pre-provisioned snapshots are billed at
  standard rates.
- **Microsoft FinOps toolkit 15: check a hub's version before quoting it.**
  `finops-azure-billing.md` brings the toolkit section up to release 15 (October 2026):
  Data Explorer or Fabric behind a hub, the three network modes, the local hub, the
  as-is support model, and the defects release 15 fixed that changed figures
  (commitment purchases counted as savings, swapped eligibility columns since release
  14, retention reset on upgrade). The agents section adds the toolkit's agent plugin
  and what to check before using it on a client estate.
- **Savings from the FOCUS cost columns.** `finops-allocation-showback.md` adds the
  three subtractions (negotiated, commitment, total) and the rules that make the total
  quotable: commitment purchase rows stay out of every savings sum, a negative value
  is a finding, a zero usually means a missing price. The ESR formula in
  `finops-azure-commitments.md` now says the same, and its MACC section warns that a
  burndown computed from amortised cost without purchases understates the burn.
- **Azure units carry a block size.** `finops-azure-billing.md` explains which FOCUS
  quantity to divide by, and why quantities are summed within one unit only.
- **Three new Azure network runbooks**: a DDoS Protection plan with no virtual
  network, an ExpressRoute circuit left `NotProvisioned`, and an idle virtual network
  gateway (with the point-to-site case that makes a gateway without connections look
  idle when it is not). `azure-snapshot-sprawl` now finds full snapshots billed at the
  Premium SSD rate.
- **The connector's search no longer answers a short query on one word of it.** A
  `query` of two or three words used to return a file that shared a single minor
  word with it: "NAT gateway charges" on Azure returned the VNet gateway runbook on
  "gateway", and the French "charges" (workloads) of a Spot question matched the
  English word. Such a file now comes back only when the shared word carries at least
  40% of the query's weight. Sentences are ranked as before, because one distinctive
  word in a sentence is often the right match. A two-word compound can still slip
  through ("NAT gateway" on Azure still returns the VNet gateway runbook).
- **The "what changed" digest is in two files.** `finops-whats-new.md` keeps the
  scheduled changes and the current and previous month, so "what changed last month"
  and "what is coming" are still answered there. The earlier months of the 90-day
  window are in `finops-whats-new-earlier.md`, generated from the same list. The one
  file had reached its size budget. On the connector, the earlier months are
  `get_reference(name="finops-whats-new-earlier")`.
- **Vertex AI spend caps: the alerts are fixed.** `finops-vertexai.md` adds a fifth
  mechanic: a spend cap budget's alerts (50%, 80%, 100%) and recipients cannot be
  customised, so other thresholds need an ordinary budget beside the cap.
- **Concurrent licences are sized on peak use.** `finops-sam.md` adds that a floating
  licence pool is sized on peak simultaneous checkouts from the licence-server log, not
  on headcount, and that a long idle timeout inflates that peak.
- **GenAI capacity: idle reserved capacity held as an access hedge.** `finops-genai-capacity.md`
  now separates deliberate idle capacity, kept because provider capacity is scarce, from
  waste: price the hedge against the cost of losing access, report it on its own line,
  give it an owner and a review date, and allocate the pool by business priority.
- **FOCUS consolidators: the CID dashboards carry a per-user charge.** The build,
  borrow or buy table in `finops-focus.md` now says that the Quick Sight layer of AWS
  Cloud Intelligence Dashboards is billed per author and per reader each month, or as
  reader-session capacity, so the audience size is a running cost of that option.
- **Two new Azure runbooks.** `azure-hybrid-benefit-unclaimed` finds the Windows
  Server, SQL Server, RHEL and SLES VMs that pay for a licence the organisation
  already owns, with one Resource Graph query per licence switch.
  `azure-database-extended-support` finds the PostgreSQL and MySQL flexible servers
  billed the extended support surcharge since September and October 2026, and those
  that join them on 1 February 2027. The catalogue now holds 46 runbooks.
- **Azure mechanics added after the same Microsoft Learn pass.** Backup: which
  recovery points can move to the archive tier, and what Instant Restore snapshots
  cost under the Standard and Enhanced policies. Databases: SQL Managed Instance stop
  and start, the serverless billing basis, storage billed on the configured maximum,
  Flexible Server storage that never shrinks (`finops-azure-data.md`). Compute and
  AKS: the Scheduled Actions API, the VM availability metric, memory metrics without
  an agent, Advisor's lookback period, the per-node OS disk and tag propagation in AKS,
  Log Analytics retention per table and dedicated clusters (`finops-azure.md`).
  Billing: three traps of the Retail Prices API, what Policy tag inheritance
  overwrites and which role it needs, who can buy a commitment through a partner
  (`finops-azure-billing.md`). Licensing: the separate SQL Server licence switch on
  VMs and the Linux values (`finops-itam.md`).
- **Sizing stacked savings in cascade.** `optimnow-methodology.md` now states the
  rule and its order: each lever is computed on what the previous one left, licence
  setting first, then schedule, then rightsizing.

- **Azure corrections after a pass against Microsoft Learn (14 November 2026).**
  Log Analytics: usage above a commitment tier is billed at the tier's own rate, not
  pay-as-you-go, so a tier pays from its break-even volume; `Heartbeat` and
  `AzureActivity` are free to ingest, `AzureDiagnostics` and `W3CIISLog` cannot move
  to the Basic plan, and the daily cap alerts nobody by default and now stops
  security tables too (`finops-azure.md`, `azure-log-analytics-sprawl`). AKS: a
  system node pool needs at least 4 vCPUs and cannot use B-series or Spot, and the
  "Spot pools without taints" query, which could never return a row, is gone
  (`finops-azure.md`). Start/stop: the Terraform resource for VM auto-shutdown and
  the status of Start/Stop VMs v2 are corrected (`finops-azure.md`,
  `cross-cloud-schedule-blindness`). App Service reservations cover Premium v3 and
  later and Isolated v2 (`finops-azure-commitments.md`). The policy library no longer
  blocks Premium SSD v2 or every public IP, and one FOCUS export replaces the actual
  plus amortized pair (`finops-azure-billing.md`). A VM on an ephemeral OS disk cannot
  be deallocated on a schedule (`finops-azure-data.md`).
- **Google Cloud guide corrected after a full read of Google's pages (15 November
  2026).** Sustained use discounts: 30% on N1, M1 and M2, 20% on N2, N2D and C2, and
  none on E2 or the newer series, where the guide said about 20% for general-purpose
  families. Compute flexible CUDs: rates by machine series, with no 1-year discount on
  M1 to M4 and lower rates on H3, H4D and G2 and G4 GPUs; GPUs covered on G2 and G4 only; the move of spend-based CUDs from
  credits to a discounted rate and what it does to a savings query. CUD sharing is on
  by default only for billing accounts created since 16 June 2026. Spot VMs: no notice
  by default, a 120-second notice on request. BigQuery fluid scaling. What the FOCUS
  export leaves out (`finops-gcp.md`).
- **Vertex AI guide corrected the same day.** Grounding with Google Search is charged
  per query on Gemini 3 and 4, not per prompt; a tuned endpoint costs 1.5x only on a
  non-global endpoint; Gemini 4 cache reads are 95% off; Provisioned Throughput can be
  reduced only at renewal (`finops-vertexai.md`).
- **Four provider changes of early November 2026.** DynamoDB bulk put items and its
  separate meter (`finops-aws-patterns-databases.md`); MWAA tags now reach the compute
  (`finops-aws-billing.md`); Snowflake's AI Gateway is GA, cost controls included, and per-user
  quotas take overrides and role scope (`finops-snowflake.md`); Databricks budgets can
  call a webhook (`finops-databricks.md`).

### Upgrading

- **Claude directory plugin**: the new content is already there if your copy follows
  the directory; otherwise update or reinstall the plugin.
- **Claude Code marketplace** (`cloud-finops@optimnow`): run
  `/plugin update cloud-finops@optimnow` once this version is tagged.
- **Hosted connector** (`https://mcp.optimnow.io/mcp`): nothing to do. The five new
  runbooks and `finops-whats-new-earlier` appear in its catalogue, and the short-query
  ranking applies, when this version is deployed, which the release does itself.
- **If you read the digest by section**: the months before the previous one left
  `finops-whats-new` for `finops-whats-new-earlier`. A saved `get_reference` call that
  names one of those months in `finops-whats-new` now gets the list of sections that
  remain, not the text: name the new file.
- **PyPI package**: `pip install -U cloud-finops-mcp`.
- **ChatGPT and Gemini**: run the installer again and re-upload the knowledge files,
  which now include `finops-whats-new-earlier` and the five new runbooks. On ChatGPT,
  paste the new `instructions.md` too: its digest row names the second file.

### For maintainers

- **CI reports the plugin folder's total size.** Since 16 November 2026 the Claude
  directory has held each new version for a reviewer, with "Files the policy review
  couldn't cover", although no file is over 256 KiB and the folder has 106 files. The
  hold began with the commit that took the folder past 2 MiB. Anthropic documents no
  total, so 2 MiB is inferred from that one crossing. The file-limits step now prints
  the total as git stores the files and, above 95% of 2 MiB, names the five largest
  files and raises a warning on the pull request. It does not fail: the folder is
  already 2.12 MB, and what to do about it waits on Anthropic's answer.

## 1.52.0 (14 November 2026)

### New and corrected content

- **Azure storage, backup and databases have their own guide.** `finops-azure.md` had
  reached its size budget, so every Azure question loaded all of it. Its sections on
  backup and snapshots, storage tiering and databases (Azure SQL, Flexible Server,
  Cosmos DB) move, unchanged, to `finops-azure-data.md`; rightsizing, Log Analytics,
  AKS and networking stay. A backup or database question now loads about 6,000 tokens
  instead of about 15,000.
- **Corrections from the 14 November news digest.** BigQuery principal-based
  reservation assignments are GA, with project caps and opt-in compute cost attribution
  (`finops-gcp.md`); AgentCore Runtime V2 is now the default for new runtimes
  (`finops-agentic.md`); on Claude paid plans usage past the limit bills at API rates,
  Fable runs on credits from the first request on Pro and standard seats, and credits
  bought from 7 December 2026 expire after 12 months (`finops-ai-dev-tools.md`).
- **Dated changes.** Gemini 4 Carbon and Argon promotional pricing ends 30 November 2026,
  Hydrogen gains a cache-write meter on 12 January 2027, and Gemini 4 long completions
  bill on timeout (`finops-vertexai.md`); six Copilot models retire on 14 December 2026;
  Fabric unified SQL pools from January 2027 (`finops-fabric.md`); AWS Marketplace trials
  convert to paid automatically (`finops-sam.md`).
- **The 14 November content scan (issue 367).** Billing changes that break existing
  rules or floors: RDS backup storage is billed per snapshot, so allocation rules that
  matched a DB instance ARN no longer catch it (`finops-aws-patterns-databases.md`, the
  snapshot runbook); FSx for Lustre Intelligent-Tiering has a lower minimum that only new
  file systems get, and logically air-gapped vaults can archive EBS backups
  (`finops-aws-patterns-storage.md`); custom billing views accept Billing Conductor and
  billing transfer views as sources (`finops-aws-billing.md`). New options to price:
  Graviton5 `db.r9g`, tempdb on local NVMe for RDS SQL Server, G7 in more Regions,
  pipeline-free ingestion on OpenSearch Serverless (`finops-aws.md`), Daybreak models on
  bedrock-runtime (`finops-bedrock.md`), DeepSeek V4 on SageMaker JumpStart
  (`finops-open-weight-vendors.md`), ChatGPT Enterprise through AWS Marketplace
  (`finops-sam.md`), doubled Codex allowances on ChatGPT Pro (`finops-ai-dev-tools.md`),
  BigQuery cross-cloud caching and the limits of compute cost attribution
  (`finops-gcp.md`), Azure Storage Discovery plans (`finops-azure-patterns.md`).
- **Effort levels on Claude models.** How the effort setting, always-on thinking and the
  prompt cache decide what a task costs, and why the per-token ratio does not rank
  models by cost per task (`finops-anthropic.md`).
- **Two allocation and detection notes.** Unit signals to baseline per workload for AI
  anomalies (`finops-anomaly-management.md`), and where tags stop for AI and API spend
  (`finops-tagging.md`).
- **Fast mode routes corrected.** Fable 5.2 and Mythos 5.2 fast mode run on Vertex AI and
  on Anthropic-hosted Foundry deployments, which the risk section had ruled out; on
  Foundry the speed is set by a `-fast` deployment, not by the request
  (`finops-anthropic.md`).
- **Fractional GPUs in the GPU rightsizing runbook.** The `g6f` sizes (1/8 to 1/2 of an
  L4), their GRID-only driver, and the GRID and DCV licences included on EC2 for
  workstation comparisons (`aws-gpu-instance-oversized` playbook).
- **Regulated placement in France.** The SREN law decree of 14 April 2026 and the
  SecNumCloud 3.2 arrêté: which State data must sit on a qualified offer, the
  derogation window, and what it changes for estimates (`finops-onboarding-workloads.md`).
- **Price and test the exit.** The Data Act switching floor (notice, 30-day transition,
  30-day retrieval) and why data ownership in a contract is not a tested exit
  (`finops-on-prem-hybrid.md`).
- **Claude Code telemetry as a chargeback key.** `OTEL_RESOURCE_ATTRIBUTES` for team
  and cost-centre keys, what is sent by default, and why its cost figure splits the
  invoice rather than replacing it; and why a Claude subscription is not a cheaper route
  for API workloads (`finops-ai-dev-tools.md`).
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
- **A reported Azure price rise now carries its status where it is stated.** Partner
  blogs report a separate rise of about 25% on v1 and v2 VM series from 1 February 2027;
  no Microsoft page states it (checked 11 November 2026). The guide said so in a note at
  the end of the passage, and an answer quoted the figure as Microsoft's. The figure and
  its status now sit in one sentence, with what Microsoft did publish, and the digest row
  says the rise is reported and unconfirmed (`finops-azure.md`, `finops-whats-new.md`).

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
- **A 46-second demo in the README.** The same NAT gateway question put to Claude
  Opus 5.5 on 11 November 2026, alone and then with the plugin: what Claude alone
  already gets right, and the 4 places where the answer differs. One run each.
- **The companion pricing connector's page is current again.** The OptimNow AI Pricing
  Hub connector went from five tools to eight on 11 and 12 November 2026 (server
  0.11.0): where to buy a model (`compare-model-hosts`), which quoted prices moved
  (`track-llm-price-changes`) and the volume at which renting GPUs costs the same as an
  API (`estimate-self-hosting-breakeven`). INSTALLATION lists the eight with their
  parameters and the fields that date a figure, including the day of a fallback
  snapshot. Nothing changes in the skill or in `cloud-finops-mcp`.

### Upgrading

- **Claude directory plugin**: the new content and the new Azure guide are already there
  if your copy follows the directory; otherwise update or reinstall the plugin.
- **Claude Code marketplace** (`cloud-finops@optimnow`): run
  `/plugin update cloud-finops@optimnow` once this version is tagged.
- **Hosted connector** (`https://mcp.optimnow.io/mcp`): nothing to do. The new guide
  `finops-azure-data` appears in its catalogue when this version is deployed, which the
  release now does itself.
- **If you call a guide by name**: the backup, storage and database sections left
  `finops-azure` for `finops-azure-data`. A saved `get_reference` call that names
  `finops-azure` with one of those sections now gets the list of sections that remain,
  not the text: name the new guide, or let `find_references` route the question.
- **PyPI package**: `pip install -U cloud-finops-mcp`.
- **ChatGPT and Gemini**: run the installer again and re-upload the knowledge files,
  which now include the new Azure guide. On ChatGPT, paste the new `instructions.md`
  too: its routing table has a row for it.

### For maintainers

- **The weekly price check retries a throttled request.** Its first run in GitHub
  Actions, on 11 November 2026, read 97 live prices, found no drift in 160 figures and
  still went red: one Azure Retail Prices request out of 47 was answered "429 Too
  Many Requests" and the script did not try again. It now retries a 429, a 5xx or a
  dropped connection up to four times, waiting what the server asks, and the report
  says how many requests were retried. Any other error fails at once, as before.
- **The hosted connector is redeployed by the release, and checked.** Until now
  `mcp.optimnow.io` moved to a new version when someone ran `fly deploy` after the tag,
  and in August 2026 it had been found four releases behind. The release workflow now
  builds the image from the tag, rolls the Fly.io app, then calls the public address:
  the version it announces must be the release, and the guides and runbooks it lists
  must be the files of the tag. The deploy starts after the PyPI publish, so behind the
  maintainer's approval, and the MCP Registry entry, which names that address, is
  published only after the check passes. A second workflow, `deploy-hosted.yml`,
  redeploys one tag by hand, to repair a failed deploy or to go back a release. The
  image also sets its own package version from `plugin.json`, where it used to trust a
  field bumped by hand. The manual workflow redeployed 1.51.0 on 12 November 2026 as a
  rehearsal; the release chain itself first runs at the next release.
- **One reading of every scheduled job.** `scripts/check-family-jobs.py` reads the
  scheduled jobs of the five OptimNow repositories, the pull requests and alarm issues
  they left and the three hosted servers, and prints first what needs a hand. What it
  cannot read it reports as not read, never as fine. A Monday-morning routine runs it.
- **A weekly check on the companion connectors' tool lists.** `INSTALLATION.md` lists
  the tools of the AI Pricing Hub and AI ROI Calculator connectors by hand, and it had
  fallen three tools behind. `scripts/check-companion-tools.py` now compares both lists
  with the servers' own `tools/list` every Saturday and opens an issue when they
  differ; it never edits the page. In CI it runs offline and only checks that the page
  still parses.
- **The weekly source scan is the laptop's, and the docs now say so.** Since October the
  README and `docs/DESIGN.md` described a cloud routine scanning about 35 sources every
  Saturday. It did not exist: the scan kept running from the maintainer's laptop on the
  1st and the 15th, over about 30 sources. From 14 November 2026 it runs every Saturday
  at 9:00 and catches up when the laptop was closed or offline at that hour.

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
