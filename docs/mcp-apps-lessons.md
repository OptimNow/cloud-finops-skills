# MCP Apps rendering in Claude: the forensic record

Why the `ui://cloud-finops/*` widgets do or do not render in Claude, and how that
understanding changed three times between 16 and 20 August 2026.

Split out of `CLAUDE.md` in August 2026, for the same reason `docs/ROADMAP.md` was:
`CLAUDE.md` is read in full at the start of every agent session, and this entry had
grown to roughly 119 lines of dated diary. The operational rules that an agent
editing this repo actually needs were extracted into a short summary that stays in
`CLAUDE.md` (see its "MCP Apps rendering" lesson); everything below is the evidence
behind them.

**Read this as a chronological record, not as a set of conclusions.** Each dated
section was written from the evidence available on that day, and later sections
overturn parts of earlier ones. Superseded claims are marked inline rather than
deleted, because the sequence of wrong hypotheses is itself the useful part: it
records which explanations were tested and eliminated. If you want the current
state, read the 2026-08-20 section and the "Where this stands" section at the end.

---

## 2026-08-16: MCP Apps rendering in Claude is allowlisted, not earned by conformance

*(Original entry title. The headline claim was later overturned - see 2026-08-20.)*

The `ui://cloud-finops/playbook-viewer` MCP App shipped in PR #133 had never
been opened in a real host - only against a test harness that simulates the
`postMessage` handshake. The 2026-08-16 session finally validated it, and the
result reorders the whole "publish a remote MCP server" plan.

### What the validation established

Running MCPJam Inspector against the local stdio server (no hosting, no public
endpoint, about an hour of work):

- The viewer **works**. It renders in MCPJam's ChatGPT host emulation:
  frontmatter parsed into badges, the six sections laid out with their
  colour coding, the footer line present. The prototype is a validated
  component, not a hypothesis.
- Two conformance defects were found by auditing the HTML against
  `modelcontextprotocol/ext-apps` `specification/2026-01-26/apps.mdx`
  *before* the first live run, and fixed in PR #135: an incomplete
  `ui/initialize` handshake (missing `protocolVersion` / `clientInfo` /
  `capabilities`; the spec's reference call passes `protocolVersion:
  "2026-01-26"`), and `target="_blank"` links, which the host sandbox
  swallows because it grants `allow-scripts` and `allow-same-origin` but
  not `allow-popups` - clicks now go through the host's `ui/open-link`.
- MCPJam's accepted resource mime types, from its own error message:
  `text/html;profile=mcp-app` (the spec value, which is what the server
  declares), `text/html+skybridge`, `text/html`. A deliberate experiment
  substituting the older `text/html+mcp` disproved the mime-type
  hypothesis cleanly and is *not* retained.

### The finding that changed the plan

The same server renders as plain text in Claude - in MCPJam's Claude emulation,
and in real Claude Desktop against the local stdio server. The cause is not
conformance. Anthropic's
[Use interactive connectors in Claude](https://support.claude.com/en/articles/13454812-use-interactive-connectors-in-claude)
names the connectors that may render UI (Amplitude, Asana, Box, Canva,
Clay, Figma, Hex, Slack) and states that a self-built interactive
connector "must meet additional design, security, and testing
requirements", pointing at the Connectors Directory submission and review
process. `anthropics/claude-ai-mcp#471` reports exactly this failure for a
spec-correct custom remote connector on Claude Web and was closed as *not
planned* - consistent with intended behaviour rather than a bug.

**So SEP-1865 conformance is an eligibility condition, not an entry
ticket.** A custom connector, remote or local, gets the text fallback no
matter how correct it is. The path to rendering in Claude is: conformant
server, then publicly reachable remote deployment, then Connectors
Directory submission, then Anthropic review - the last two outside the
maintainer's control and on an unpublished timeline.

> **Superseded by the 2026-08-20 finding below.** The claim that a custom
> connector "gets the text fallback no matter how correct it is", and the
> reading of Directory review as the gate, are both wrong for widgets. The
> 2026-08-19 update narrowed the first claim (`ui.domain` is an observable,
> fixable mechanism), and the 2026-08-20 update refuted both outright:
> Skybridge-built custom connectors render without any Directory listing.

### Consequences

- A remote deployment (Alpic) is **necessary but nowhere near sufficient**
  for interactive rendering. It must therefore be justified on
  distribution grounds alone: letting a non-technical user paste a URL
  into claude.ai instead of installing a PyPI package. That is the
  decision taken on 2026-08-16, with the interactive viewer explicitly
  *not* counted as a benefit.

  > **Superseded in part by the 2026-08-20 finding below** as to *why*
  > rendering was absent. The decision itself stands unchanged: the Alpic
  > deployment is still justified on distribution grounds, and the
  > interactive viewer is still not counted as a benefit, because rendering
  > for this connector remains unconfirmed.

- Do not treat the "Interactive" badge in the Connectors Directory as
  reachable by shipping correct code.

  > **Superseded by the 2026-08-20 finding below.** Directory review is not
  > the gate for widget rendering; implementation shape is. Correct code in
  > the Skybridge shape does reach rendering on other connectors in this
  > family.

- The transferable discipline: **validate a host-dependent feature in a
  real host before planning the infrastructure that depends on it.** An
  hour in MCPJam, costing nothing and requiring no deployment, produced a
  finding that would otherwise have surfaced at the end of a multi-day
  hosting project. The prototype had sat unvalidated since PR #133
  precisely because the only test in place asserted the resource existed,
  never that it rendered.

  > **Not superseded.** This is the durable lesson of the whole sequence and
  > the reason it survives in `CLAUDE.md`.

---

## 2026-08-19: the gate has an observable mechanism (`ui.domain`)

Claude Desktop's `mcp-ext-apps-host` attempts to set up MCP Apps for custom
connectors and validates a `ui.domain` on the widget resource:
sha256(connector URL exactly as the host displays it in its error log -
for a root-entered connector that is the ROOT url WITH its trailing
slash)[:32] + `.claudemcpcontent.com`.

*(Corrected 2026-08-20: the original "no trailing slash" note here was wrong -
hashing `/mcp` while the host saw `https://.../` reproduced the failure on this
repo's own connector; Skybridge, which passes, hashes `https://<host><pathname>`
per request.)*

A wrong or missing value logs `ui.domain validation failed for connector "<url>"`
in the Desktop logs (observed live for ai-pricing-hub on 2026-08-19, including the
fix-it one-liner the error prints).

So the 2026-08-16 claim that a custom connector "gets the text fallback no matter
how correct it is" is no longer the whole story - but whether a correct `ui.domain`
is *sufficient* for rendering was still unproven for this repo's connector at that
point: the render test needs the connector added to the account and the Alpic
deployment current.

The real render attempt happened on 2026-08-19 (four prompts through the connector
on claude.ai): tools executed, the host reserved the widget iframe, the frame stayed
blank - the predicted failure.

`ui.domain` was therefore applied on 2026-08-20: the three widget resources declare
`meta={"ui": {"domain": ...}}` where the value is DERIVED in `server.py` from
`CANONICAL_CONNECTOR_URL` (sha256 of the ROOT connector URL exactly as users enter
it, **trailing slash included** - `CANONICAL_CONNECTOR_ORIGIN + "/"` in `server.py`
- first 32 hex chars + `.claudemcpcontent.com`) and pinned by tests.

**When touching this, never hash an internal path instead of the public URL** -
that wrong-input variant is exactly what broke `ai-pricing-hub-mcp`.

*Correction to an earlier note in this entry: ai-pricing-hub was NOT fixed on
2026-08-19 - no such fix existed in that repo and its failures were still logging at
17:30 that day; it needs the same change as this one.*

---

## 2026-08-20: rendering for custom connectors IS possible - the gate is implementation shape, not the Directory

Two facts landed the same day.

**First**, a Desktop render test on this repo's connector called `find_playbooks`
(visible as `tool_approval_gate` log entries, MCP Apps runtime activating right
after), logged NO `ui.domain` error - and still showed no widget.

**Second, and decisive**: the Skybridge-built companions (`ai-pricing-hub-mcp`,
`ai-roi-calculator-mcp`) DO render their widgets in Claude as plain custom
connectors (user-confirmed with a screenshot of `compare-models-side-by-side`
rendering in the chat).

**So the 2026-08-16 "Directory review is the gate" conclusion is wrong for
widgets.**

What Skybridge does that this server did not, in likely order of relevance:

1. Registers each widget **TWICE** - an apps-sdk variant (mime
   `text/html+skybridge`, `openai/*` meta, tool `openai/outputTemplate` pointing at
   it) alongside the spec variant (`text/html;profile=mcp-app`, `ui.resourceUri`).
2. Computes `ui.domain` **per request** from the URL Claude actually calls (sha256
   of host+path), instead of a static precomputed hash.
3. Declares a **`ui.csp` block** (`{resourceDomains, connectDomains}`) in the
   resource-read `_meta`.

Items (1) and (3) were mirrored in `server.py` the same day (PR #174), which moved
the failure forward to a `ui.domain` mismatch on the ROOT connector URL, fixed by
hashing the root-with-slash form (PR #175).

Item (2) was **not** adopted: `server.py` keeps a static `UI_DOMAIN` derived at
import from `CANONICAL_CONNECTOR_URL`. Because Alpic serves the MCP at the root as
well as at `/mcp`, and the documented connector URL (README, INSTALLATION.md) is
the root form, the static constant matches what the host hashes - provided it stays
byte-for-byte identical to the documented URL.

**Keep `ui.domain`; it stays required.**

---

## 2026-09-30: first render test on the custom domain - tools reach claude.ai, widgets still do not

Context: the connector moved to `https://mcp.optimnow.io/mcp` (PR #210) and was
redeployed on Fly. Before the test, the deployed server was called directly and
advertised the expected sandbox domain for that URL on all three widget resources
(`5164c823f8a966e5cb0f8571d5141bd9.claudemcpcontent.com`) with the CSP origins set to
the new host, so the static-hash input was known to be right before the host was
involved.

Test, on claude.ai (web), fresh custom connector at the canonical URL, new chat:

1. "Use the cloud-finops tools to list the playbooks for AWS." The host loaded the
   tools, the model called `find_playbooks` and returned the 21 AWS playbooks as a
   plain table. **Tool calls work on the new URL.**
2. "Open the playbook explorer." The model answered that the connector "only has
   list/find/get tools, with no UI or resources", found no artifact to open, and then
   built its own artifact from the tool results, with a caveat that the copied text
   was unverified.

What this establishes:

- The failure is upstream of the hash. The `ui.domain` value was verified correct for
  the URL as entered, and the host still did not mount a frame on a tool result that
  carries the widget metadata. Whatever gates rendering here, it is not the constant.
- The host exposed no `ui://` resource to the model at all. The model's statement is
  the first direct evidence that the resources are filtered out before the model sees
  them, rather than served and failing to render.
- The model's fallback (build an artifact by hand) is not the feature and should not be
  mistaken for it: its own note says the playbook text was copied without a
  character-level check.

Not established: whether Claude Desktop behaves the same (no Desktop log was
collected), and whether the apps-sdk variant would render on a host that reads it.
The domain move itself is done and verified; rendering stays unproven.

---

## Where this stands

- `ui.domain` is required, and is derived in `mcp_server/src/cloud_finops_mcp/server.py`
  from the documented connector URL, byte for byte. Since the move to Fly (2026-09-09)
  the MCP is served at `/mcp` only, so that URL is `CANONICAL_CONNECTOR_ORIGIN + "/mcp"`
  with no trailing slash; on Alpic it had been the root-with-slash form. The rule is
  the same either way: hash exactly what the user is told to paste. Since 2026-09-30
  the origin is `https://mcp.optimnow.io` and the literal hash is pinned by
  `test_ui_domain_pins_the_custom_domain_hash`.
- The dual widget registration (apps-sdk variant alongside the SEP-1865 spec
  variant) and the `ui.csp` block are the Skybridge-parity shape, shipped in
  PR #174. Do not remove either while trying to simplify the server.
- The tool-side widget link is declared under all three key shapes
  (`ui.resourceUri`, the flat `ui/resourceUri`, and `openai/outputTemplate`)
  because different hosts read different ones.
- **Rendering for this repo's connector is still not happening, as of the
  2026-09-30 test on claude.ai.** The hash was verified correct before the test and
  the host still surfaced no resources to the model. Treat interactive rendering as
  unproven, not as shipped, and do not cite it as a benefit of the hosted deployment.
- The next diagnostic step, if this is picked up again, is a Claude Desktop render
  test against the current Fly deployment at the canonical URL, reading the
  `mcp-ext-apps-host` log: a `ui.domain` error would contradict the direct
  verification and point back at the constant; no error plus no frame confirms
  host-side gating and means the remaining lever is the resource shape, not the URL.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
