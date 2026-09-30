# Submitting to the Claude directory

Step-by-step for listing this repository in Anthropic's Claude directory
(<https://claude.ai/directory>), written for a first submission. Two listings are
involved, and the portal treats them as separate submissions:

1. **Plugin bundle** - this GitHub repository (the skill only; it declares no MCP server).
2. **MCP connector** - the hosted server at `https://mcp.optimnow.io/mcp`.

The two are kept separate on purpose (decision of 2026-09-30): the plugin does not
bundle the connector, because both serve the same library and bundling would load
the tool definitions in every session next to the skill. The connector listing gives
the server its own dashboard (health, usage per tool) and lets the two listings be
paired when they come from the same organisation. Source pages, read on 2026-09-26:

- Publish overview: <https://claude.com/docs/directory/publish>
- Submit a plugin: <https://claude.com/docs/plugins/submit>
- Plugin pre-submission checklist: <https://claude.com/docs/plugins/pre-submission-checklist>
- Submit a connector: <https://claude.com/docs/connectors/building/submission>
- Connector review criteria: <https://claude.com/docs/connectors/building/review-criteria>
- Component support by app: <https://claude.com/docs/plugins/platform-support>

---

## 0. Before opening the portal

**Account.** Submissions come from a claude.ai account on a paid plan (Pro, Max, Team
or Enterprise). On Team, an Owner submits. The listing belongs to the organisation
that submits it, and the first organisation to submit a given repository folder holds
it, so submit from the OptimNow organisation, not a personal workspace that might be
closed later.

**GitHub.** The portal checks that the GitHub account connected to that claude.ai
organisation can push to `OptimNow/cloud-finops-skills`. Connect it under the
organisation you submit from; a connection made in another Claude organisation does
not carry over.

**Local check.** From the folder that contains the repository, run:

```bash
claude plugin validate ./cloud-finops-skills
```

Expected (Claude Code 2.1.285, run 2026-09-30): a line `Validating marketplace
manifest: .../.claude-plugin/marketplace.json` followed by `Validation passed`, with
no warnings. The command picks the marketplace manifest because the folder holds
one. An earlier version printed a benign warning about `CLAUDE.md` not being loaded
as project context; it no longer appears.

**Hosted server check.** The portal syncs the tool list from the live server, and
Verified review calls every tool. Confirm the deployment serves what you expect before
submitting (the 2026-08 audits found it four releases behind, twice).

`serverInfo.version` in the `initialize` reply names the deployed release since
1.37.0; it must equal `version` in `.claude-plugin/plugin.json` at the tag you
deployed. It is a first check, not proof. Before 1.37.0 `server.py` set no version and
the field reported the `mcp` library version instead (it read `1.30.0` while the
server was serving 1.36.0 content), so a deployment that answers `1.30.0` predates
that release. Either way, confirm the served content itself:

| Check | How | Expected |
|---|---|---|
| Listing totals | `list_references()` and `list_playbooks()` | `total` equals the number of `.md` files under `references/` and `playbooks/` (README excluded) at the tag you deployed |
| Tool surface | `tools/list` | Six tools, each with a `title` and `readOnlyHint: true`; descriptions identical to `server.py` at that tag |
| Bodies | `get_reference(name=...)` on a file changed in the last release | `content` equals the file at that tag |

The hosted server is redeployed per release, not per merge (INSTALLATION.md), so
content merged to `main` after the last tag is expected to be absent until the next
release and `fly deploy`. It is not a defect. If the served content is older than the
last tag, run `fly deploy` from the tagged commit first.

Then exercise each of the six tools once through MCP Inspector
(`npx @modelcontextprotocol/inspector`) or as a custom connector in Claude; the portal
asks you to confirm you did.

**Verified 2026-09-30, after the move to `https://mcp.optimnow.io/mcp` (PR #210) and
`fly deploy`.** Both hosts answer `initialize` with `serverInfo.version` 1.37.0, list
the six tools and `list_references` total 35; the three widget resources advertise
the sandbox domain for the new URL. In claude.ai the connector loads and tool calls
succeed; widgets do not render (see `docs/mcp-apps-lessons.md`, 2026-09-30 entry).
The earlier verification follows.

**Last verified: 2026-09-26, after the 1.37.0 release and `fly deploy`.**
`serverInfo.version` reads `1.37.0`. Served content equals tag `v1.37.0` exactly: 35
references and 37 playbooks, with no body differing from the tag. Tool names,
titles, annotations, descriptions and schemas are identical to the tag; six widget
resources are served; misses return `error` with `suggestions`, `available_sections`
or `valid_values`; and the reviewer sequence in section 2.8 returns content on every
call. The same release is on PyPI (`cloud-finops-mcp` 1.37.0) and is the latest
entry on the MCP Registry, pointing at the Fly.io URL.

**Materials to have ready** (the portal has no "save for later" beyond your browser
session):

| Item | Where it is | Status |
|---|---|---|
| Privacy policy URL | `https://github.com/OptimNow/cloud-finops-skills/blob/main/PRIVACY.md` | In repo; contact line names jean@optimnow.io |
| Documentation URL | `https://github.com/OptimNow/cloud-finops-skills#readme` (plugin) and `https://github.com/OptimNow/cloud-finops-skills/blob/main/mcp_server/README.md` (connector) | Exists |
| Support contact | `jean@optimnow.io` | Decided 2026-09-26 |
| Icon | `assets/icon.png` (96x96 PNG, square) | In repo. If the portal asks for a larger size, export the same artwork from its source; do not upscale this file |
| Listing texts | Section 2.3 below | Drafted |
| Test account | Not applicable, no authentication | Say so in the Test & launch step |

---

## 1. Plugin bundle

Open <https://claude.ai/directory/manage>, select **Submit new**, then **Plugin
bundle**.

### 1.1 Source

| Field | Value |
|---|---|
| Repository | `OptimNow/cloud-finops-skills` |
| Plugin path | leave empty (the manifest is at the repository root) |
| Branch or tag | leave empty to follow `main` (see the note below) |

**Which branch to track.** The directory scans every new commit on the tracked branch
and, once published, serves it to everyone who installed the plugin. Following `main`
means each fortnightly content PR becomes a directory version, which matches the
"refreshed twice monthly" promise in the README. The documentation says to raise
`version` in `plugin.json` on every release; whether the directory publishes a commit
whose `version` is unchanged is not documented. The release-train rule in CLAUDE.md
keeps content PRs free of version bumps, so if the directory turns out to ignore
same-version commits, the fix is to track a tag that the release workflow moves
(a `Settings > Tracked branch or tag` change, no resubmission) rather than to start
bumping versions per PR. Start with `main`.

### 1.2 Validate

Select **Validate** and read the report. Findings expected on the current tree, with
their meaning:

| Expected finding | Result | Why, and what to do |
|---|---|---|
| A file over 256 KiB | None expected | `llms-full.txt` (1.2 MB) left the tree on 2026-09-30; it is built at release time and attached to the GitHub Release. `scripts/check-plugin-file-limits.sh` fails CI if any tracked non-image file crosses the limit again |
| Name made only of generic words (`cloud-finops`) | Possibly held for a reviewer | Decision taken 2026-09-26: keep the name, since renaming breaks every `cloud-finops@optimnow` install. `displayName` is "Cloud FinOps by OptimNow" so the listing is not mistaken for an official one |
| Name is taken | Blocks | Only if another organisation already holds `cloud-finops`. If so, stop and decide on a rename; do not submit under a look-alike |

Anything marked **Blocks** that is not in this table is new: fix it in the repository,
push, and select **Re-validate**. A validation result applies to one commit, so
validate again after any push.

### 1.3 Listing details

Read from `plugin.json` and the README; nothing to type. Check that the display name,
description and author look right. To change them later, edit the files and publish a
new version.

### 1.4 Data handling

| Question | Answer |
|---|---|
| Reads or stores personal data | No. Static skill files; the connector has no accounts, no database and no per-user state |
| Sends data to services other than its declared connectors | No. The plugin declares no connector and calls no endpoint. The skill directs the model to a public pricing site (optimtoken.optimnow.io) for current prices; that is a link the model may open in the conversation, not a call the plugin makes |
| Retention | None by the plugin. The hosted server keeps a coverage log of zero-result facet queries (no conversation text); the hosting platform keeps the standard web access log. See PRIVACY.md |
| Intended for people under 18 | No |

### 1.5 Compliance

Check the contact email, then select all four acknowledgements.

### 1.6 Review and submit

Keep **GitHub push webhook** (default) so the directory scans a push without waiting
for its schedule. Setting up the webhook needs admin access on the GitHub repository;
it can be done later from the plugin's **Settings** tab. Leave **Auto-publish** as
offered; for a new listing an Anthropic reviewer publishes each version anyway until
they change the setting.

### 1.7 After submission

The **Versions** tab shows each scanned commit. A version that passes is not live
until you select **Publish**. Ten submissions per 24 hours per organisation, drafts
and withdrawals included.

---

## 2. MCP connector

Same portal, **Submit new**, then **MCP connector**.

### 2.1 Connection

Paste `https://mcp.optimnow.io/mcp` (the `/mcp` path, no trailing slash;
the widget sandbox domain is derived from it). Single URL, not "users connect to
different URLs".

### 2.2 Tools

Synced from the server. Expect six tools, all in the read-only group, each with a
title. If any is flagged for a missing title or annotation, the deployment is stale:
see section 0.

### 2.3 Listing

| Field | Limit | Proposed value |
|---|---|---|
| Server name | 100 chars | `Cloud FinOps by OptimNow` |
| One-liner | 200 chars | `FinOps knowledge for AI agents: billing mechanics, commitments, allocation, AI spend and named waste runbooks across AWS, Azure, GCP and OCI. Read-only, no account needed.` |
| Description | 2,000 chars | Draft below |
| Categories | 1 to 5 | Pick the closest from the portal's list; candidates are developer tools, productivity, finance, data and analytics |
| Documentation URL | | `https://github.com/OptimNow/cloud-finops-skills/blob/main/mcp_server/README.md` |
| Privacy policy URL | | `https://github.com/OptimNow/cloud-finops-skills/blob/main/PRIVACY.md` |
| Support contact | | `jean@optimnow.io` |
| Icon | | `assets/icon.png` |
| URL slug | permanent | `cloud-finops` |

Description draft (about 1,500 characters, edit freely; the portal text cannot be
edited by Anthropic afterwards):

> Cloud FinOps by OptimNow gives Claude a curated FinOps knowledge base to query at
> run time: how cloud and AI billing actually works, how to size and manage
> commitments, how to allocate and charge back, how to manage AI and SaaS spend, and
> how to detect and fix named waste patterns.
>
> Six read-only tools over two content types. References are long-form guides per
> provider and discipline (AWS, Azure, GCP, OCI, Bedrock, Azure OpenAI, Vertex AI,
> Databricks, Snowflake, Microsoft Fabric, Kubernetes, tagging, anomaly management,
> KPIs, allocation, chargeback, GreenOps, AI coding tools, agentic FinOps), each
> tagged with its FinOps Framework capability, phase, persona and maturity gate so
> Claude can filter by facet instead of scanning. Playbooks are short runbooks, one
> waste pattern each (idle NAT gateway, expiring reservation with no decision,
> snapshot sprawl, oversized GPU, gp2 to gp3, and more), with symptoms, a detection
> query you run in your own account, the fix and the anti-pattern. On hosts that
> render MCP Apps, results appear as an interactive explorer and viewer.
>
> The server holds no account, no credential and no user data; it cannot see your
> cloud environment and hands over the detection query instead. Price figures are
> not served here: the tools carry mechanics and ratios, and any figure in a
> reference is illustrative and dated inline. Content is refreshed twice a month from primary
> provider sources and published under CC BY-SA 4.0. Built by OptimNow, a FinOps
> consultancy, from enterprise delivery experience.

### 2.4 Use cases

Primary use cases: answering FinOps questions with billing-grounded guidance;
finding the runbook for a suspected waste pattern; routing an advisory question
(commitment sizing, chargeback design) to the reference that serves it. Prerequisites:
none. Reads data only.

### 2.5 Company

OptimNow, <https://optimnow.io>; primary contact for review updates: `jean@optimnow.io`.

### 2.6 Authentication

**No authentication.** The server serves public, read-only content. Nothing to
configure.

### 2.7 Data handling

The underlying API is OptimNow's own (the server is the product; it proxies nothing).
No personal health data, no sponsored content.

### 2.8 Test & launch

Text to paste:

> No account or credential is needed. Add `https://mcp.optimnow.io/mcp` as
> a custom connector (or open it in MCP Inspector) and call, in order:
> `list_references()`, `find_references(phase="Optimize", persona="Engineering")`,
> `get_reference(name="finops-aws-commitments", section="commitment decision")`,
> `list_playbooks()`, `find_playbooks(service="AWS NAT Gateway")`,
> `get_playbook(name="aws-nat-gateway-endpoint-substitution")`. Each returns JSON; a miss
> returns `error` plus `suggestions` or `available_sections`, never a bare 500.

Facet values are exact, not fuzzy: `service="nat gateway"` returns zero results, which
is what a reviewer would then see. This sequence was run against the live server on
2026-09-26 and every call returned content. Re-check the names against
`list_playbooks()` before pasting; they change when the catalogue grows. Confirm the "I have run every tool" box only after
doing it on the deployment that is live that day.

### 2.9 Compliance

Seven acknowledgements (directory guidelines, first-party API, no financial
transactions, no AI media generation, no prompt injection, no conversation data
collection, public documentation). All apply as stated.

### 2.10 After submission

The scan lists the server as a Community connector by default. Anthropic may
escalate to Verified review on its own; there is nothing to apply for. Once both
listings exist under the same organisation, pair them from the plugin's page so people
who add both see one set of tools.

---

## 3. Things a reviewer may raise, and the position taken

- **Imperative tool descriptions.** `get_reference` says to call it "ALWAYS before
  answering an advisory question", and the server `instructions` string carries two
  routing rules. The review criteria reject descriptions that "tell Claude how to
  behave" in ways unrelated to the tool's function. These rules are about when to call
  the tool itself, were measured to be the only placement that works (CLAUDE.md,
  probe cycles 4-7), and describe the tool's function. Keep them unless a reviewer
  objects; if one does, move the sentence into the tool's "Use this when" paragraph
  rather than deleting it.
- **Routing to OptimToken.** The criteria reject descriptions that "promote products
  and services", and the data-handling step asks for "Sponsored or promoted content:
  No". The server `instructions` used to route current prices to the OptimNow AI
  Pricing Hub by URL; a reviewer can read a first-party link as promotion, so since
  2026-09-30 the connector's model-facing text names no OptimNow product and no
  `optimnow.io` URL (the widgets lost their footer link at the same time; a test in
  `mcp_server/tests/test_conformance.py` pins both). The instruction that remains is
  the data-quality rule alone: use a live pricing tool if one is connected, never quote
  an undated figure. The skill keeps its pricing-hub routing; the plugin is reviewed
  under different rules.
- **Plugin folder is the repository root.** Installers receive `mcp_server/`,
  `scripts/` and `.github/` along with the skill. Moving the plugin to
  a subfolder would break the existing marketplace path (`source: "./"`) and every
  current install. Accepted.

## 4. Keeping the listing current

- Merging to `main` is the release: the directory scans the commit and publishes
  under the auto-publish setting. Nothing to do in the portal.
- No tracked file may exceed 256 KiB and the tree stays under 480 files
  (`scripts/check-plugin-file-limits.sh`). `llms-full.txt` is built at release time
  and attached to the GitHub Release, never committed.
- The plugin stays skill-only (`scripts/check-plugin-skill-only.sh`): no `.mcp.json`
  in the tree, no `mcpServers` key in `plugin.json`.
- A connector-URL change touches three places: `server.py`
  (`CANONICAL_CONNECTOR_ORIGIN`), README.md and INSTALLATION.md. The connector
  listing's URL is edited in the portal separately.
- Delisting is a request from the plugin's page menu; relisting is also a request and
  can be declined. Prefer publishing a fix over delisting.
