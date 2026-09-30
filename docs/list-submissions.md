# Curated-list submissions

Submission kit for the curated GitHub lists, prepared on 2026-09-26. Every fact
below was re-verified on that date against the public repository, PyPI, the hosted
endpoint and the target lists' own files. Re-run the "Facts" checks before opening
a PR on a later date; forks, stars and issue numbers move.

The entries are written so that no sentence is shared between two lists. Keep it
that way when editing: list maintainers read each other's PRs.

Two rules for all of them: the PR body says plainly that Jean (OptimNow) maintains
the project, and the submissions are spaced at least three days apart, in the
order below. Never add the `🤖🤖🤖` agent fast-track marker that the punkpeye
lists offer; these are human submissions.

---

## Facts, as verified on 2026-09-26

| Fact | Value | How checked |
|---|---|---|
| Stars | 55 | `GET /repos/OptimNow/cloud-finops-skills` |
| Forks | 17, none by OptimNow | `GET /repos/OptimNow/cloud-finops-skills/forks` |
| External issues | #97 (crmvet, open), #103 (ramos2501, closed) | issue API |
| Repository created | 2026-02-25 | repo API (`created_at`) |
| PyPI | `cloud-finops-mcp` 1.37.0 | `https://pypi.org/pypi/cloud-finops-mcp/json` |
| Install command | `uvx cloud-finops-mcp` (stdio); `pip install cloud-finops-mcp` | `mcp_server/README.md` lines 112 and 118 |
| Transports | stdio (default) and streamable HTTP | `mcp_server/README.md` "Streamable HTTP" |
| Hosted endpoint | `https://mcp.optimnow.io/mcp` answers `initialize`, serverInfo 1.37.0 (custom domain since 2026-09-30; the former `cloud-finops-mcp.fly.dev` host still answers) | POST with an `initialize` request |
| Auth | none; the server reads bundled files, no credentials, no outbound HTTP client | `server.py` grep |
| Tools | `list_references`, `find_references`, `get_reference`, `list_playbooks`, `find_playbooks`, `get_playbook`, all `readOnlyHint: true` | `server.py` |
| Licence | CC BY-SA 4.0 (`LICENSE.md`; GitHub shows "Other") | repo API `license.spdx_id = NOASSERTION` |
| Glama server page and badge | `https://glama.ai/mcp/servers/OptimNow/cloud-finops-skills` (badge SVG returns 200) | curl |
| Glama connector | `io.github.OptimNow/cloud-finops` (badge SVG returns 200) | curl |
| awesome-ai-tokenomics | listed since 2026-09-21, PR #61 merged; maintainer bkotrys: "We checked the one-liner against the repository, the MCP server code and PyPI, and every claim holds. Accepted." | README line 244 and the PR page |
| Unaffiliated repositories carrying the skill | Lynricsy/HyperSkills, majiayu000/claude-skill-registry, viktorbezdek/skillstack, yangheng95/opencorvus, MrSahalImran/share-tuner | GitHub code search `"cloud-finops-skills" NOT user:OptimNow` (60 hits) |
| Not yet listed on | punkpeye/awesome-mcp-servers, VoltAgent/awesome-agent-skills, TensorBlock/awesome-mcp-servers, punkpeye/awesome-remote-mcp-servers | grep of each README; code search of the TensorBlock catalogue |
| Prior PRs by OptimNow on those four lists | none | issue search |

Do not cite PyPI download counts anywhere: the daily shape is a small baseline with
spikes on release days, which reads as CI and mirrors.

---

## Why the PRs were not opened from the Claude session

The session that prepared this kit is scoped to `OptimNow/cloud-finops-skills`. It
could read the target repositories but could neither fork them into the OptimNow
account nor open pull requests on them. Each PR below is therefore a copy-and-paste
job in the GitHub web interface, about five minutes each. No fork exists yet; nothing
to delete.

### The web-interface procedure (same for targets 1, 2 and 4)

1. Open the target repository page on GitHub and click **Fork**, then **Create fork**.
   Leave "Copy the main branch only" ticked.
2. In the fork, open `README.md` and click the pencil icon (**Edit this file**).
3. Use the browser's find (Ctrl+F) to locate the anchor line given below, place the
   cursor at the end of that line, press Enter and paste the entry line. Check that
   the new line sits exactly where the kit says and that no blank line was added.
4. Click **Commit changes**, choose **Create a new branch for this commit and start a
   pull request**, name the branch as given below, paste the commit message, and
   click **Propose changes**.
5. On the "Open a pull request" page, replace the title with the one given below,
   paste the PR body, and click **Create pull request**. Do not tick anything else.
6. Wait for the list's CI comment (targets 1 and 4 run a validator). Fix only what it
   asks for.

---

## Target 1: punkpeye/awesome-mcp-servers

Open this one first. Category: **Cloud Platforms**, where the other cost and FinOps
servers sit (cloudscope-mcp, cloudprice-mcp, finopsmcp, Infrawise, cloud-cost-mcp,
cloudcostsmcp). Alphabetical by owner, case-insensitive: `OptimNow` goes after
`ofershap/mcp-server-s3` and before `pibblokto/cert-manager-mcp-server`.

- Fork: `https://github.com/punkpeye/awesome-mcp-servers`
- Branch: `add-optimnow-cloud-finops-skills`
- Commit message: `Add OptimNow/cloud-finops-skills to Cloud Platforms`
- PR title: `Add OptimNow/cloud-finops-skills to Cloud Platforms`
- Anchor line (insert the entry on the line after it):
  `- [ofershap/mcp-server-s3](https://github.com/ofershap/mcp-server-s3)`

Entry line (one line, paste as is):

```markdown
- [OptimNow/cloud-finops-skills](https://github.com/OptimNow/cloud-finops-skills) [![OptimNow/cloud-finops-skills MCP server](https://glama.ai/mcp/servers/OptimNow/cloud-finops-skills/badges/score.svg)](https://glama.ai/mcp/servers/OptimNow/cloud-finops-skills) 🐍 🏠 🍎 🪟 🐧 - Read-only FinOps reference library for agents: six tools that list, filter by FinOps Framework facet, and fetch guides on cloud billing mechanics, commitments, allocation and chargeback for AWS, Azure, GCP, OCI, Kubernetes and data platforms, plus named waste-pattern playbooks with detection queries. Includes AI inference spend (managed APIs, provisioned capacity, self-hosted models, coding-tool seats). Content is bundled in the package; no cloud credentials. CC BY-SA 4.0. `uvx cloud-finops-mcp`
```

The line was run through the list's own validator logic (`.github/workflows/check-glama.yml`):
Glama badge present, only permitted emojis, `owner/repo` link text, GitHub primary
link, not a duplicate. Legend choice: 🐍 Python, 🏠 local (the server reads files it
ships with and calls no remote API), all three operating systems (pure Python).

PR body:

```markdown
## What this adds

One line under Cloud Platforms, next to the other cost and FinOps servers already listed there (cloudscope-mcp, cloudprice-mcp, finopsmcp, cloud-cost-mcp).

`cloud-finops-mcp` is a Python MCP server published on PyPI. It exposes a markdown FinOps reference library as six read-only tools: `list_references`, `find_references`, `get_reference`, `list_playbooks`, `find_playbooks`, `get_playbook`. The content ships inside the wheel, so the server needs no cloud credentials and has no outbound HTTP client. Default transport is stdio (`uvx cloud-finops-mcp`); streamable HTTP is available for hosted deployments.

## Checks

- Glama listing and score badge: https://glama.ai/mcp/servers/OptimNow/cloud-finops-skills
- Alphabetical position: after ofershap/mcp-server-s3, before pibblokto/cert-manager-mcp-server
- Licence: CC BY-SA 4.0 (LICENSE.md in the repository)

## Disclosure

I maintain this project (Jean Latiere, OptimNow). This is a hand-submitted PR, not an agent fast-track one.
```

---

## Target 2: VoltAgent/awesome-agent-skills

Open at least three days after target 1. Their CONTRIBUTING.md names "AI and Data"
and "Other" as Community subcategories, but the README today has neither; the
closest existing subcategory is **Community Skills > Specialized Domains** (it holds
the finance, legal, health and infrastructure skills). Do not create a section. Add
at the END of that subcategory, after the last entry, which on 2026-09-26 was
`ilyautov/small-business-ru`. Re-check the last entry on the day.

- Fork: `https://github.com/VoltAgent/awesome-agent-skills`
- Branch: `add-skill-optimnow-cloud-finops-skills`
- Commit message: `Add skill: OptimNow/cloud-finops-skills`
- PR title (exactly): `Add skill: OptimNow/cloud-finops-skills`
- Anchor line (insert the entry on the line after it; it is the last `- **[` line
  before `</details>` in Specialized Domains):
  `- **[ilyautov/small-business-ru](https://github.com/ilyautov/small-business-ru/tree/main/small-business-ru/skills)**`

Entry line (nine words after the dash, their limit is ten):

```markdown
- **[OptimNow/cloud-finops-skills](https://github.com/OptimNow/cloud-finops-skills/tree/main/skills/cloud-finops)** - FinOps knowledge: cloud billing mechanics, commitments, allocation, AI spend
```

PR body:

```markdown
This adds one line at the end of Community Skills > Specialized Domains.

The skill folder is `skills/cloud-finops/` in the linked repository: a SKILL.md router plus reference files on cloud, SaaS and AI cost management, written from how the providers actually bill (commitment mechanics, allocation and chargeback, waste patterns with detection queries). It has been public since February 2026 and is updated twice a month.

Usage outside the maintainer's own account, all checkable on GitHub:

- Listed in QuesmaOrg/awesome-ai-tokenomics since 21 September 2026 (PR #61 there), after that maintainer verified the entry against the code and the PyPI package.
- 17 forks, none by the maintainer.
- Redistributed or referenced by repositories with no link to OptimNow, among them Lynricsy/HyperSkills, majiayu000/claude-skill-registry, viktorbezdek/skillstack, yangheng95/opencorvus and MrSahalImran/share-tuner (GitHub code search for "cloud-finops-skills", excluding OptimNow).
- Issues opened by external users on the repository (#97, #103).

Conflict of interest: the project is maintained by the account opening this PR (Jean Latiere, OptimNow).
```

Refresh the fork count and the redistribution list on the day (see "Facts").

---

## Target 3: TensorBlock/awesome-mcp-servers (optional, issue form)

At least three days after target 2. Submission goes through their issue form, which
their automation turns into a draft PR:
`https://github.com/TensorBlock/awesome-mcp-servers/issues/new?template=add-mcp-server.yml`.
Their catalogue had no `cloud-finops` entry on 2026-09-26 (code search of the
repository, zero hits). Form answers:

| Field | Answer |
|---|---|
| Server name | `OptimNow/cloud-finops-skills` |
| Project URL | `https://github.com/OptimNow/cloud-finops-skills` |
| Best category | `Knowledge Management & Memory` (alternative: `Cloud Platforms & Services`; they adjust during triage) |
| What can an agent do with this server? | An agent can list, filter and read FinOps reference guides on cloud and AI billing mechanics, commitments, allocation and chargeback, and fetch named waste-pattern playbooks that carry a detection query to run in the user's own account. Six read-only tools over content bundled with the package; nothing to connect to a cloud account. |
| Install or connection instructions | `Install: uvx cloud-finops-mcp` (stdio, PyPI package cloud-finops-mcp). `Alternative: pip install cloud-finops-mcp` then run `cloud-finops-mcp`. `Hosted: https://mcp.optimnow.io/mcp` (streamable HTTP). `Env: none`. |
| Transport | `multiple` |
| Auth requirements | `no auth` |
| Known supported clients | `Claude Desktop, Claude Code, Cursor, Codex CLI, Windsurf, VS Code` (the client sections in `mcp_server/README.md`) |
| License | `CC-BY-SA-4.0` |
| Before submitting | tick "I searched the repo for this project URL or name to avoid duplicates" (done on 2026-09-26; redo the search on the day) |

Include the hosted endpoint only if `curl -sS -X POST https://mcp.optimnow.io/mcp`
with an `initialize` body answers on the day.

---

## Target 4: punkpeye/awesome-remote-mcp-servers (optional)

At least three days after target 3, and only if the hosted endpoint answers an
`initialize` handshake on the day (their CI checks it on every PR). Two prerequisites
their CONTRIBUTING.md states:

1. **Star the repository from the OptimNow account** before opening the PR. PRs from
   accounts that have not starred it are not merged.
2. **The Glama connector badge is required.** The connector already exists:
   `https://glama.ai/mcp/connectors/io.github.OptimNow/cloud-finops`. No action needed
   unless the badge URL below stops returning an SVG.

Entry format is three lines. The name links to a homepage or documentation page, not
to a GitHub repository; the PyPI project page is the non-GitHub documentation page
for the server. Category: **Knowledge & Memory** (documentation and knowledge servers
such as Hugging Face and HAIDAA sit there; their Cloud Platforms section is hosting
providers only). Alphabetical, case-insensitive: "Cloud FinOps" goes after `bsv.cx`
and before `docs2mcp`.

- Fork: `https://github.com/punkpeye/awesome-remote-mcp-servers`
- Branch: `add-cloud-finops-connector`
- Commit message: `Add Cloud FinOps by OptimNow to Knowledge & Memory`
- PR title: `Add Cloud FinOps by OptimNow to Knowledge & Memory`
- Anchor: the three-line `bsv.cx` entry in Knowledge & Memory; insert after its third
  line (the one starting with `🔓 - Timestamp and verify evidence`).

Entry (three lines, the second and third indented by two spaces; description is 110
characters, their limit is 120):

```markdown
- [Cloud FinOps by OptimNow](https://pypi.org/project/cloud-finops-mcp/) `https://mcp.optimnow.io/mcp`
  [![Cloud FinOps by OptimNow MCP connector](https://glama.ai/mcp/connectors/io.github.OptimNow/cloud-finops/badges/score.svg)](https://glama.ai/mcp/connectors/io.github.OptimNow/cloud-finops)
  🔓 - Fetches FinOps reference guides and waste-pattern runbooks on cloud and AI cost management; no account needed.
```

PR body:

```markdown
Adds the hosted endpoint of the OptimNow Cloud FinOps server under Knowledge & Memory.

The endpoint is a public streamable-HTTP deployment on Fly.io of the `cloud-finops-mcp` package. It serves the same six read-only retrieval tools as the package (reference guides on cloud and AI billing, commitments, allocation and chargeback; runbooks for named waste patterns) and requires no authentication. Glama connector: io.github.OptimNow/cloud-finops. The repository behind it is already submitted to awesome-mcp-servers as an installable server.

The repository has been starred from this account as the guidelines require.

I operate this server and maintain the project (Jean Latiere, OptimNow).
```

Edit the last paragraph of the body if the awesome-mcp-servers PR (target 1) has not
been merged by then ("already submitted" is accurate either way; do not write
"listed" unless it is).

---

## Hand-filled forms (drafts only, Jean submits)

### hesreallyhim/awesome-claude-code

Web form only, filled by a human:
`https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml`.
Eligibility: the form requires 14 days of development since the first commit or 100
stars; the repository dates from 2026-02-25, so condition (a) holds. One resource per
submission.

| Field | Answer |
|---|---|
| Display Name | `Cloud FinOps Skill` |
| Category | `Skills` |
| Link | `https://github.com/OptimNow/cloud-finops-skills` |
| Author Name | `Jean Latiere (OptimNow)` |
| Author Link | `https://github.com/OptimNow` |
| Description | A Claude Code plugin and skill that gives the agent Cloud FinOps knowledge: reference files on cloud and AI billing mechanics, commitments, allocation and chargeback, plus named waste-pattern playbooks that carry a detection query. Installs with `/plugin marketplace add`; a read-only MCP server over the same library is available separately. |

The description is 342 characters (their range is 10 to 500), three sentences at
most, descriptive, and does not address the reader. Tick the five required boxes;
leave the sixth ("Do not check the following box") unchecked as instructed.

### Anthropic Claude directory (plugin bundle)

The link `https://clau.de/plugin-directory-submission` redirects to
`https://claude.com/docs/directory/publish`. The submission itself is made in the
developer portal at `https://claude.ai/directory/manage` (Submit new > Plugin bundle);
the earlier Console form is no longer supported. The portal reads name, description
and author from `.claude-plugin/plugin.json` and the marketplace manifest from
`.claude-plugin/marketplace.json`; there is no free-text form to fill for those. What
to enter or check:

| Field | Value |
|---|---|
| Plugin name | `cloud-finops` (keep; `displayName` is "Cloud FinOps by OptimNow") |
| Repository | `OptimNow/cloud-finops-skills` |
| Plugin path | empty (manifest at the repository root) |
| Marketplace manifest | `.claude-plugin/marketplace.json` (marketplace name `optimnow`) |
| Branch or tag | empty, follows `main` |
| Description (from plugin.json) | `Expert FinOps guidance for cloud, AI, SaaS, and data-platform spend (multi-provider, model-agnostic).` |
| Category | closest available among the portal's list; candidates in order: developer tools, finance, data and analytics, productivity |

The full step-by-step, the expected reviewer holds and the connector listing answers
are in [`directory-submission.md`](directory-submission.md); this table is only the
short form.

### JackyST0/awesome-agent-skills

Requires 64 stars. The repository had 55 on 2026-09-26. Skip until
`GET /repos/OptimNow/cloud-finops-skills` reports at least 64.

---

## Ruled out on 2026-09-20, not re-checked

ComposioHQ, travisvn, BehiSecc and karanb192 `awesome-claude-skills`,
heilcheng/awesome-agent-skills, rohitg00/awesome-claude-code-toolkit,
ccplugins/awesome-claude-code-plugins, composio-community/awesome-claude-plugins
(190 to 200 open PRs each, no merges for months); jmfontaine/awesome-finops (no merge
since August 2025); quemsah/awesome-claude-plugins (auto-generated ranking);
libukai/awesome-agent-skills (maintainer-only merges); kirodotdev-labs/awesome-kiro
(external PRs closed).

---

## Schedule

Let D be the date target 1 is opened.

| Step | Not before |
|---|---|
| Target 1, punkpeye/awesome-mcp-servers | D |
| Target 2, VoltAgent/awesome-agent-skills | D + 3 days |
| Target 3, TensorBlock issue form (optional) | D + 6 days |
| Target 4, punkpeye/awesome-remote-mcp-servers (optional) | D + 9 days |
| hesreallyhim form, Anthropic portal | any time, independent of the above |

Record the actual dates and PR URLs below as they happen.

| Target | Date | URL | Outcome |
|---|---|---|---|
| 1 | 2026-09-27 | https://github.com/punkpeye/awesome-mcp-servers/pull/15223 | Opened; validator labels has-glama, has-emoji, valid-name. Awaiting maintainer |
| 2 | | | |
| 3 | | | |
| 4 | | | |
