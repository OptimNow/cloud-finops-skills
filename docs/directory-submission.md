# Submitting to the Claude directory

Step-by-step for listing this repository in Anthropic's Claude directory
(<https://claude.ai/directory>), written for a first submission. Two listings are
involved, and the portal treats them as separate submissions:

1. **Plugin bundle** - this GitHub repository (skill + bundled connector reference).
2. **MCP connector** - the hosted server at `https://cloud-finops-mcp.fly.dev/mcp`.

Anthropic's documentation asks for both even though the plugin already references
the server: the connector listing gives the server its own dashboard (health, usage
per tool) and lets the two listings be paired when they come from the same
organisation. Source pages, read on 2026-09-26:

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

Expected: `Validation passed` with one warning saying `CLAUDE.md` at the plugin root
is not loaded as project context. That warning is benign; the file is for
contributors, not for the plugin.

**Hosted server check.** The portal syncs the tool list from the live server, and
Verified review calls every tool. Confirm the deployment is current before submitting
(the 2026-08 audits found it four releases behind, twice):

```bash
curl -s https://cloud-finops-mcp.fly.dev/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"check","version":"0"}}}'
```

The `serverInfo.version` in the reply must match `.claude-plugin/plugin.json`. If it
does not, run `fly deploy` from the tagged release commit first. Then exercise each of
the six tools once through MCP Inspector (`npx @modelcontextprotocol/inspector`) or as
a custom connector in Claude; the portal asks you to confirm you did.

**Materials to have ready** (the portal has no "save for later" beyond your browser
session):

| Item | Where it is | Status |
|---|---|---|
| Privacy policy URL | `https://github.com/OptimNow/cloud-finops-skills/blob/main/PRIVACY.md` | In repo; review the contact line before publishing |
| Documentation URL | `https://github.com/OptimNow/cloud-finops-skills#readme` (plugin) and `https://github.com/OptimNow/cloud-finops-skills/blob/main/mcp_server/README.md` (connector) | Exists |
| Support contact | An OptimNow email address or the optimnow.io contact page | **To decide** - the repo carries none |
| Icon | Square PNG or SVG | **To prepare** - `assets/` has only screenshots and the 1456x720 social preview |
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
| `llms-full.txt` over 256 KiB | Held for a reviewer | The one-fetch library inline is 1.2 MB. Not blocking; a reviewer reads the version before it goes live. Accept for the first submission |
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
| Sends data to services other than its declared connectors | No. The only endpoint is the declared connector. The skill directs the model to a public pricing site (optimtoken.optimnow.io) for current prices; that is a link the model may open in the conversation, not a call the plugin makes |
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

Paste `https://cloud-finops-mcp.fly.dev/mcp` (the `/mcp` path, no trailing slash;
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
| Support contact | | To decide (section 0) |
| Icon | | To prepare (section 0) |
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
> not served here: the tools carry mechanics and ratios and route current prices to
> the OptimNow AI Pricing Hub. Content is refreshed twice a month from primary
> provider sources and published under CC BY-SA 4.0. Built by OptimNow, a FinOps
> consultancy, from enterprise delivery experience.

### 2.4 Use cases

Primary use cases: answering FinOps questions with billing-grounded guidance;
finding the runbook for a suspected waste pattern; routing an advisory question
(commitment sizing, chargeback design) to the reference that serves it. Prerequisites:
none. Reads data only.

### 2.5 Company

OptimNow, <https://optimnow.io>, plus the primary contact for review updates.

### 2.6 Authentication

**No authentication.** The server serves public, read-only content. Nothing to
configure.

### 2.7 Data handling

The underlying API is OptimNow's own (the server is the product; it proxies nothing).
No personal health data, no sponsored content.

### 2.8 Test & launch

Text to paste:

> No account or credential is needed. Add `https://cloud-finops-mcp.fly.dev/mcp` as
> a custom connector (or open it in MCP Inspector) and call, in order:
> `list_references()`, `find_references(phase="Optimize", persona="Engineering")`,
> `get_reference(name="finops-aws-commitments", section="commitment decision")`,
> `list_playbooks()`, `find_playbooks(service="nat gateway")`,
> `get_playbook(name="aws-nat-gateway-endpoint-substitution")`. Each returns JSON; a miss
> returns `error` plus `suggestions` or `available_sections`, never a bare 500.

Check the playbook name against `list_playbooks()` output before pasting; names
change when the catalogue grows. Confirm the "I have run every tool" box only after
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
  and services". The pricing-hub pointer is a data-quality rule (never quote an
  undated figure), and the hub is OptimNow's own, first-party and free. It is disclosed
  in the README "Data handling" section and in PRIVACY.md.
- **Plugin folder is the repository root.** Installers receive `mcp_server/`,
  `scripts/`, `.github/` and `llms-full.txt` along with the skill. Moving the plugin to
  a subfolder would break the existing marketplace path (`source: "./"`) and every
  current install. Accepted.

## 4. Keeping the listing current

- Merging to `main` is the release: the directory scans the commit and publishes
  under the auto-publish setting. Nothing to do in the portal.
- A content PR still regenerates `llms-full.txt`; the 256 KiB hold recurs on each
  version until a reviewer clears it.
- A connector-URL change touches four places: `server.py`
  (`CANONICAL_CONNECTOR_ORIGIN`), README.md, INSTALLATION.md and `.mcp.json`. The
  connector listing's URL is edited in the portal separately.
- Delisting is a request from the plugin's page menu; relisting is also a request and
  can be declined. Prefer publishing a fix over delisting.
