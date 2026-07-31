---
name: cross-cloud-agent-loop-burn
scope: cross-cloud
service: GenAI inference (Bedrock / Anthropic API / Azure OpenAI)
waste_category: ai-ml-inefficiency
confidence: likely
---

# Agent-Loop Flat-Line Burn

## Problem

A stuck or retrying AI agent produces constant token spend with no output
value - and crucially, no spike. A max-iteration loop, a retry storm against a
failing tool, or a self-validating agent that never converges holds token
throughput roughly flat while it burns. Spike-based cost anomaly detection never
fires: with no day-over-day jump for a percentage threshold to catch, the spend
joins the baseline and the first human signal is the invoice a day or a billing
cycle later. This is the flat-line variant of the "agentic loops" anti-pattern
in `finops-for-ai.md`, made worse by every retry re-billing the full context as
input.

## Symptoms

- Token throughput on one model, API key, or agent identity holds at a steady,
  non-zero level for hours with no completed tasks downstream
- Application telemetry shows no unit-of-work growth (conversations closed,
  documents processed) while token consumption stays flat
- Logs show repeated near-identical requests: same prompt hash, zero-diff
  outputs, or `max_retries` / `max_iterations` exhaustion
- Cost-per-completed-task climbs while cost-per-token is unchanged; the workload
  never triggers a cost anomaly alert because the total plateaued, never jumped

## Detection

**Detect on usage telemetry, not billing data.** Cost exports lag - cloud Cost
Explorer / CUR land 24-48 hours later, and Bedrock application-inference-profile
cost tags are daily-grained. Usage metrics land in minutes, and a flat line is
only visible at sub-hour granularity, so query the usage surface.

**AWS Bedrock** - CloudWatch runtime metrics in the `AWS/Bedrock` namespace, per
`ModelId`, at 60-second period. Watch `InputTokenCount` and `OutputTokenCount`
(Sum) holding above a floor across consecutive minutes while `Invocations` keeps
climbing (`InvocationThrottles` may also rise if the loop hammers a rate limit):

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock --metric-name InputTokenCount \
  --dimensions Name=ModelId,Value=<model-id> \
  --start-time "$(date -u -d '2 hours ago' +%FT%TZ)" \
  --end-time "$(date -u +%FT%TZ)" \
  --period 60 --statistics Sum
```

For per-application attribution (which agent is burning), invoke through an
**application inference profile** and read its cost-allocation tags in Cost
Explorer / CUR - good for after-the-fact ownership, too coarse for live alerts.

**Anthropic API** - the Usage & Cost Admin API usage endpoint
`/v1/organizations/usage_report/messages` supports 1-minute buckets
(`bucket_width=1m`; data appears within ~5 minutes). Group by `api_key_id` or
`model` to isolate the identity holding a flat line. The cost endpoint
`/v1/organizations/cost_report` is daily-only and cannot see the pattern.
Requires an Admin API key (`sk-ant-admin01-...`):

```bash
curl "https://api.anthropic.com/v1/organizations/usage_report/messages?\
starting_at=2026-07-20T00:00:00Z&ending_at=2026-07-20T02:00:00Z&\
bucket_width=1m&group_by[]=api_key_id" \
  -H "anthropic-version: 2023-06-01" -H "x-api-key: $ANTHROPIC_ADMIN_KEY"
```

**Azure OpenAI** - Azure Monitor metrics on the Cognitive Services account at
PT1M grain: `ProcessedPromptTokens` (input), `GeneratedTokens` (output), and
`TokenTransaction` (total inference tokens), split by `ModelDeploymentName`:

```kusto
AzureMetrics
| where ResourceProvider == "MICROSOFT.COGNITIVESERVICES"
  and MetricName in ("ProcessedPromptTokens", "GeneratedTokens")
  and TimeGenerated > ago(2h)
| summarize tokens = sum(Total) by bin(TimeGenerated, 1m), MetricName
| order by TimeGenerated asc
```

**Log-side heuristics** - the second signal that separates a stuck loop from
legitimate steady traffic: identical prompt hashes across requests, zero-diff
outputs, and `max_retries` / `max_iterations` exhaustion in agent-framework logs.

## Fix

1. **Cap the loop at the framework.** Set `max_iterations` / `max_retries` and a
   per-task token budget. An agent with no iteration ceiling is the root cause.
2. **Add loop breakers.** Detect repeated near-identical tool calls or prompt
   hashes and abort; back off exponentially on tool failure instead of retrying
   at full rate.
3. **Alarm on sustained token throughput, not cost.** Fire when token throughput
   stays above a floor for N consecutive minutes with no downstream completions -
   the detection layer spike-based cost monitors miss.
4. **Kill-switch runbook.** Document who can disable the offending API key,
   deployment, or agent, and how. Disabling stops the burn in seconds, well ahead
   of any billing signal.
5. **Track cost-per-completed-task.** A rising cost-per-task with a flat
   cost-per-token is the economic tell; wire it into the weekly unit-economics
   review (`finops-for-ai.md`).

## Anti-pattern

- Relying on percentage-based cost anomaly detection for agentic workloads. A
  flat-line burn has no percentage jump to catch; it needs a sustained-throughput
  signal on usage telemetry.
- Alarming on the cost report or billing export. By the time daily cost data
  confirms the burn, the money is spent.
- Capping only output tokens. In a loop the re-billed input context usually
  dominates, so a `max_tokens` output cap does not stop a retry storm.
- Treating the plateau as the new normal. A baseline that rose with no matching
  output growth is a masked anomaly (see `finops-anomaly-management.md`), not a
  healthy steady state.

## See also

- `references/finops-for-ai.md` - "agentic loops" anti-pattern and
  cost-per-completed-task unit economics
- `references/finops-anomaly-management.md` - usage-first detection for AI/token
  workloads and the flat-line failure mode
- `references/finops-bedrock.md` - Bedrock cost tracking and inference profiles
- `references/finops-anthropic.md` - Admin API monitoring and spend controls
- `references/finops-waste-detection-playbooks.md` - "ai-ml-inefficiency"
  category rubric

Sources (official provider docs; every metric and endpoint name above verified
against these):

- AWS Bedrock runtime CloudWatch metrics - https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-runtime-metrics.html
- AWS Bedrock application inference profiles - https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-application-inference-profiles.html
- Anthropic Usage & Cost Admin API - https://docs.claude.com/en/api/usage-cost-api
- Azure OpenAI monitoring data reference - https://learn.microsoft.com/en-us/azure/foundry/openai/monitor-openai-reference

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
