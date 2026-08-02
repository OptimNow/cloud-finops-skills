---
name: cross-cloud-coding-agent-token-waste
scope: cross-cloud
service: AI coding agents (Claude Code / Cursor / GitHub Copilot / Codex)
waste_category: ai-ml-inefficiency
confidence: likely
---

# Coding-Agent Token Waste

## Problem

Agentic coding tools (Claude Code, Cursor, GitHub Copilot, Codex, and the
open-source CLIs) bill by the token, and the whole conversation history is
re-sent as input on every turn, so spend compounds with conversation length
rather than with the number of tasks completed. In the sessions OptimNow has
metered, input dominates - on the order of 85% of session cost - but the exact
split varies with cache configuration and task shape, so measure your own
before building a business case on it. The result is a cost line that grows faster than headcount or output,
driven by mechanisms that never surface on a monthly dashboard: a broken cache
prefix, quadratic context re-ingestion, self-validation loops, and every request
defaulting to the frontier model. Unlike a cloud resource there is no instance to
rightsize; the waste sits in the harness and the prompt, and it is only visible
if you meter the agent logs directly.

This is the client-side, developer-tooling counterpart to
`cross-cloud-agent-loop-burn` (a production agent flat-lining on a provider API).
Both are ai-ml-inefficiency, but the detection surface and the levers differ.

## Symptoms

- Cache-read tokens are a small share of input tokens: caching is off, or a
  mid-session model switch keeps discarding the warm prefix
- Average tokens per task sit far above a sane baseline, with high variance from
  one session to the next
- Coding-tool spend grows faster than the number of developers or merged tasks
- Retry and self-validation loops re-run whole sequences; tool output is re-sent
  into context every turn
- No per-seat or per-key budget cap, and no model-tier routing: routine edits run
  on the most expensive model
- A single bill-shock session dominates a week's spend
- Seat licences and token spend are tracked separately, so nobody owns the
  blended cost per developer

## Detection

Coding-agent spend lives in local session logs, not the cloud bill, so detection
uses agent-log meters rather than CUR / Cost Management queries.

```bash
# 1. Team-wide readout from local agent logs: tokens, cache ratio, cost by model.
#    ccusage reads the logs the coding agents already write locally.
npx ccusage@latest            # daily / session breakdown across detected agents

# Flag:
#   cache-read tokens << input tokens        -> caching off or prefix broken
#   tokens/session >> team baseline          -> context bloat or a loop
#   one session or user dominating the total -> a runaway or bill-shock event
```

```bash
# 2. Per-session drill-down: route the agent through a local proxy meter to see
#    per-tool token spend, including large tool results that get re-sent into
#    every later turn and silently multiply the input bill.
uv tool install token-viewer     # or: pipx install token-viewer
tokview show --watch             # terminal 1: live dashboard
tokview wrap claude              # terminal 2: run the agent through the proxy
```

```bash
# 3. Named waste detectors, priced in dollars. CodeBurn reads the session files
#    the agents already write and scans for low cache-hit ratios, unused MCP
#    servers, and bloated context files, with copy-paste fixes.
npx codeburn                     # interactive dashboard by task / model / tool
npx codeburn optimize            # waste scan with estimated token and $ savings
```

All three read local session data - no API keys leave the machine, which is
usually what unblocks the security review. Tool homepages:
[ccusage](https://github.com/ccusage/ccusage),
[tokview](https://github.com/chopratejas/tokview),
[CodeBurn](https://github.com/getagentseal/codeburn).

Two independent signals raise confidence from possible to likely: for example a
low cache-read ratio AND tokens-per-task above the team's P90. A single signal on
its own (no budget cap, say) is worth fixing but is not proof of active waste.

## Fix

Safest-first. Measure before you optimise, and validate any token-saving tool on
your own workload before a fleet rollout.

1. **Meter first.** Deploy a log-reading meter (ccusage, CodeBurn) or a
   local proxy meter (tokview)
   across every agent so you have tokens, cache-hit ratio, and cost per session
   per developer. Everything below is guesswork without this baseline.
2. **Fix the cache before anything else.** Cache-read is roughly 90% cheaper than
   fresh input, and input dominates session cost, so the cached prefix is
   the single biggest lever. Turn on prompt caching, keep the system prompt and
   static context stable, and avoid mid-session model switches that throw the warm
   cache away.
3. **Cap and route.** Set per-seat or per-key dollar budgets (native admin
   controls, or a gateway such as LiteLLM or Portkey) and route routine work to a
   cheaper tier (RouteLLM, Cursor Auto, a cheap-tier-in-front gateway). Reserve
   the frontier model for work where it raises the success rate, which usually
   also shrinks human verification time.
4. **Cut context re-ingestion.** This is the quadratic driver behind bill-shock.
   Use minimum-viable-context (one file, not the repository), summarisation or
   compaction near the context limit, and proxies that compress command output
   before it reaches the model. A/B test these: several token-saving plugins have
   measured net-negative because they broke an already-cached prefix.
5. **Kill runaway loops.** Enforce a max-budget-per-run and a concurrent-subagent
   cap (now first-party guardrails in Claude Code and Codex), and alert when
   tokens-per-task cross P90 so a loop is caught in minutes, not on the invoice.
   For the production-agent flat-line variant, see `cross-cloud-agent-loop-burn`.

## Anti-pattern

- Rolling out compression or token-saving plugins fleet-wide on vendor claims
  without an A/B test. Published and self-measured results span both directions -
  from single-digit percentage savings to a net token *increase* - and the
  deciding factor is whether the plugin preserves the cached prefix on your
  workload. Run the A/B before the rollout, not after.
- Optimising the per-token rate card (swapping to a cheaper model) while ignoring
  cache-read discounts and context re-ingestion, which dominate the bill. Evaluate
  cost per completed task, not price per million tokens.
- Reacting to a viral headline figure as if it were typical. The large
  coding-agent bills that circulate are usually driven by a specific mechanism
  (quadratic context re-ingestion, a broken cache prefix, an unbounded agent
  loop) rather than by ordinary heavy usage: diagnose the mechanism in your own
  logs before acting on someone else's number.
- Banning agents outright to control spend. That pushes the workload onto personal
  accounts (shadow AI) and destroys attribution. Prefer per-key budgets and
  routing over prohibition.

## See also

- `references/finops-ai-dev-tools.md` - seat + token cost governance for AI coding
  assistants (the blended cost-per-developer view)
- `references/finops-for-ai.md` - agentic loops anti-pattern, the token-engineering
  input/output menu, cache economics, cost per completed task
- `references/finops-anthropic.md` - Claude admin spend controls and cache-read
  pricing
- `playbooks/cross-cloud-agent-loop-burn.md` - the production-agent flat-line
  variant (provider-side usage-telemetry detection), distinct from this
  developer-tooling pattern
- `references/finops-waste-detection-playbooks.md` - Category 7 (AI/ML
  inefficiency) taxonomy and the confidence tiers

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
