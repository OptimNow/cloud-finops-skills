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
claude plugin validate ./cloud-finops-skills/plugins/cloud-finops
```

Expected (Claude Code 2.1.286, run 2026-10-01): a line `Validating plugin manifest:
.../plugins/cloud-finops/.claude-plugin/plugin.json` followed by `Validation passed`,
with no warnings. Running it on the repository root instead validates the marketplace
manifest, which is a different check.

**Hosted server check.** The portal syncs the tool list from the live server, and
Verified review calls every tool. Confirm the deployment serves what you expect before
submitting (the 2026-08 audits found it four releases behind, twice).

`serverInfo.version` in the `initialize` reply names the deployed release since
1.37.0; it must equal `version` in `plugins/cloud-finops/.claude-plugin/plugin.json` at the tag you
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
| Icon | Plugin: `plugins/cloud-finops/.claude-plugin/icon.svg`, picked up by the portal without a manifest field (the validator warned "Add .claude-plugin/icon.svg (square, >=128px) or set icon in plugin.json" on 2026-10-01). Connector: `assets/icon.png` (96x96 PNG, square), uploaded in the portal | The SVG redraws the favicon mark in the brand palette; the raster favicon is 868 KB and would ship in every install |
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
| Plugin path | `plugins/cloud-finops` (the manifest is in that folder; the repository root holds the marketplace, the installer, the MCP server and the tooling, none of which the plugin ships) |
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
| A file over 256 KiB | None expected | `llms-full.txt` (1.2 MB) left the tree on 2026-09-30; it is built at release time and attached to the GitHub Release. `scripts/check-plugin-file-limits.sh` fails CI if any file in the plugin folder crosses the limit again |
| `UNREAD_ASSET_REFERENCED`, `MCP_FORWARDS_CREDENTIAL_ENV`, `RUNTIME_FETCH_EXEC`, `ROOT_CLAUDE_MD` | None expected | The first validation (2026-10-01, plugin path empty) returned 13 holds and 6 warnings under these codes, every one raised by files outside the skill: CLAUDE.md, INSTALLATION.md, install.sh, the guard scripts and the workflows. The plugin path now points at `plugins/cloud-finops`, which holds the manifest, a README, LICENSE and the skill only; the one in-skill trigger (`$ANTHROPIC_ADMIN_KEY` beside an API URL in a playbook) became a placeholder, and the three `npx` launcher lines in another playbook became install pointers. `scripts/check-plugin-content.sh` fails CI if any of the four patterns comes back |
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
offered; for a new listing an Anthropic reviewer publishes each version until they
change the setting. For this listing they did: on 1 October 2026 the Overview tab read
"Auto-publish: On: versions that pass go live automatically".

**Setting up the push webhook** (done 2026-10-01; the `ping` delivery answered 200).
The portal supplies the two values, GitHub holds the webhook, and nothing in this
repository changes. Without it the directory still finds a new commit on `main`, at
its scheduled check about every 6 hours; with it, within minutes of the push.

1. In the portal, on the **Plugin submitted for review** page (or later: the plugin's
   **Settings** tab, **Updates**, **Set up**), select **Generate secret**. The next
   screen shows a **Payload URL** and a **secret**. The secret is shown once: keep the
   tab open until the GitHub side is saved, and paste it nowhere else.
2. In a second tab, open
   <https://github.com/OptimNow/cloud-finops-skills/settings/hooks> and select
   **Add webhook**. The page needs admin rights on the repository; a member without
   them does not see it.
3. Fill in the form:

   | Field | Value |
   |---|---|
   | Payload URL | the URL from the portal, unchanged |
   | Content type | `application/json` |
   | Secret | the secret from the portal. GitHub signs every delivery with it; the directory rejects a delivery it cannot verify |
   | SSL verification | leave **Enable SSL verification** |
   | Which events | **Just the push event**; the directory listens to pushes on the tracked branch and nothing else |
   | Active | checked |

4. Select **Add webhook**. GitHub sends a `ping` delivery at once.
5. Open the webhook, then **Recent deliveries**: the `ping` row must show a green
   check and a `200` response. A `401` or `403` means the secret was copied wrong, a
   `404` a truncated Payload URL; fix the field with **Edit**, then **Redeliver** on
   that row.
6. Back in the portal, finish the screen.

If the secret is lost before the GitHub side is saved, **Set up** on the plugin's
**Settings** tab generates a new one; replace it in the GitHub webhook (**Edit**,
**Secret**), the old value stops working.

The webhook changes detection, not publication. While the auto-publish setting read
"an Anthropic reviewer publishes each version", every new version waited for a
**Publish** click and the reviewer. Since auto-publish was switched on (seen
1 October 2026), a version that passes the scan goes live on its own, and the listing
notes that an update "can take up to an hour to show". A version found by the
scheduled check rather than the push still publishes the same way; only detection is
slower. The 1.40.0 release on 1 October was found that way although its push delivery
succeeded, probably because the previous version was still scanning.

### 1.7 After submission

The **Versions** tab shows each scanned commit, its version label, its state
(Scanning, Serving, Superseded) and whether it arrived via push or scheduled check.
With auto-publish on, a version that passes goes live without a **Publish** click; if
the setting is ever turned off again, a passing version waits for that click. A
content commit keeps the previous version label (content PRs never bump `plugin.json`),
so several rows can share one label: the newest commit is the one serving. Ten
submissions per 24 hours per organisation, drafts and withdrawals included.

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

**Routing check after a description change.** No harness in the repository measures
tool routing; the probe battery is maintainer-local and read by hand from claude.ai
transcripts. After any deploy that changes the tool descriptions or the
`instructions` string, run these five prompts in fresh claude.ai chats with the
connector on and memory off, twice each because routing is stochastic, and record
whether a tool-call block appears and which tool it names:

1. "How do I detect cold data sitting in S3 Standard?" (P11 class, the control:
   grounded before the change, must stay grounded)
2. "My NAT gateway processes 10TB a month to S3, what should I do?" (P13, the
   symptom phrasing that converted only under imperative wording, so the one most
   at risk)
3. "Should I delete these old EBS snapshots?" (P31, never converted before: a free
   upside if it does now)
4. "Which of my RIs are about to expire?" (P12, closed as structural: expect no
   call, and note whether the model still offers to check the library)
5. "How much should we commit in Savings Plans for our EC2 fleet?" (P05, the
   advisory phrasing that flipped after PRs #171 and #176)

A drop on prompt 2 across both runs while prompt 1 still grounds is the signal that
the wording change cost routing. Baselines per probe are in the routing entry of
`docs/ROADMAP.md` (cycles 4 to 7).

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

- **Imperative tool descriptions.** Until 2026-09-30 `find_playbooks` opened with
  "ALWAYS call this before answering ...", `get_playbook` and the server
  `instructions` told the model what not to reply ("never reply that you lack account
  access", "do NOT ask for a data export first"), and `get_reference` said "ALWAYS
  before answering an advisory question". The review criteria reject descriptions that
  "tell Claude how to behave" beyond the tool's function. Those sentences were the
  August 2026 routing work (PRs #171, #176, #184, #187), each answering a measured
  under-calling in the probe cycles, and imperative placement was the wording that
  converted probe P13. They were rewritten the same day as neutral descriptions of
  what each tool returns and which questions it serves (the detection query is
  written to be run in the user's account, so an account-data question does not need
  an export), keeping the service-noun vocabulary the host's tool-search indexes. A
  test in `mcp_server/tests/test_conformance.py` pins the absence of ALWAYS / NEVER /
  MUST / "do NOT" / "IS the answer". The cost is a possible drop in spontaneous
  routing on symptom phrasings; the manual five-prompt check in section 2.8 measures
  it after each deploy, and the README already tells users to ask for the library by
  name when an answer arrives without a tool call.
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
- **Plugin folder.** Until 2026-10-01 the plugin folder was the repository root, on
  the reasoning that moving it would break the marketplace path and every install.
  The first portal validation showed the real cost: 13 holds from developer tooling,
  each of which would send every content release to a human reviewer. The plugin
  moved to `plugins/cloud-finops/`; the marketplace entry's `source` follows it, the
  plugin `name` and the marketplace name are unchanged, and the 1.39.0 version bump is
  what makes existing `cloud-finops@optimnow` installs fetch the new layout.

## 4. Keeping the listing current

- Merging to `main` is the release: the directory scans the commit and publishes
  under the auto-publish setting. Nothing to do in the portal.
- No file in `plugins/cloud-finops/` may exceed 256 KiB and the folder stays under
  480 files (`scripts/check-plugin-file-limits.sh`). `llms-full.txt` is built at
  release time and attached to the GitHub Release, never committed.
- The plugin stays skill-only (`scripts/check-plugin-skill-only.sh`): no `.mcp.json`
  in the plugin folder, no `mcpServers` key in `plugin.json`.
- The plugin folder holds markdown, LICENSE and the manifest only, with no
  uppercase `$VAR` beside a URL, no curl-pipe-to-shell and no package launcher
  (`scripts/check-plugin-content.sh`). Developer tooling stays at the repository
  root, where the scanner never reads it.
- A connector-URL change touches three places: `server.py`
  (`CANONICAL_CONNECTOR_ORIGIN`), README.md and INSTALLATION.md. The connector
  listing's URL is edited in the portal separately.
- Delisting is a request from the plugin's page menu; relisting is also a request and
  can be declined. Prefer publishing a fix over delisting.
