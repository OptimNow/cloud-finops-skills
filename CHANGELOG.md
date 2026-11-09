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
- Six section pointers in the question index now cite a full heading where a short
  phrase matched several.

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

## Earlier versions

Versions up to 1.49.1 have no entry here. Their changes are in the generated notes of
each [GitHub Release](https://github.com/OptimNow/cloud-finops-skills/releases).
