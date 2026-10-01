---
name: finops-open-weight-vendors
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Usage Optimization", "Architecting & Workload Placement"]
fcp_phases: ["Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Procurement", "Finance"]
fcp_maturity_entry: "Walk"
---

# FinOps for open-weight model vendors (DeepSeek, Qwen, Kimi, GLM)

> Billing mechanics for the open-weight model vendors sold through their **own hosted
> APIs**: DeepSeek, Alibaba's Qwen on Model Studio, Moonshot's Kimi, and Z.ai's GLM.
> Covers the three buying channels for a single checkpoint, per-vendor rate structure
> and discount mechanics (time-of-day pricing, cache-hit multipliers, batch, context
> steps, seat subscriptions), licensing as a cost input, and data residency as the
> decision that precedes price comparison.
>
> `finops-ai-self-hosted-vs-managed.md` covers running open weights on your own GPUs
> versus buying a Western managed API. This file covers the third channel neither of
> those two describes: buying the model from the lab that trained it.
>
> Built by OptimNow. Grounded in hands-on enterprise delivery, not abstract frameworks.
>
> **Source caveat:** vendor rate cards in this space change on a scale of weeks, and
> several claims below (licence terms, prior flat rates, subscription tier prices above
> the entry tier) are corroborated by secondary reporting rather than a vendor document.
> Those are flagged inline. Verify against the primary pricing pages before any
> commitment or client deliverable:
> - <https://api-docs.deepseek.com/quick_start/pricing>
> - <https://www.alibabacloud.com/help/en/model-studio/model-pricing>
> - <https://platform.kimi.ai/docs/pricing/chat-k3>
> - <https://docs.z.ai/guides/overview/pricing>

---

## TL;DR

"Open weight" describes the licence on a checkpoint. It says nothing about what you
pay, and increasingly nothing about whether the model you are actually buying is open
at all. Three things follow, and they are the whole file:

1. **The same checkpoint has a different price on every channel.** What a host sells is
   the serving, not the model.
2. **The vendors' own APIs are no longer uniformly cheap.** The current flagships from
   Moonshot and Z.ai price in the same band as Western mid-tier models, and DeepSeek's
   August 2026 repricing raised its rate card rather than lowering it.
3. **The interesting FinOps surface is the discount mechanics, not the headline rate.**
   Time-of-day pricing, cache-hit multipliers that vary by an order of magnitude between
   vendors, context-length steps, and seat subscriptions metered in credit windows are
   where the controllable spend sits.

---

## The three buying channels for an open-weight model

A single checkpoint (say GLM-5.2 or a DeepSeek V4 variant) can be bought three ways.
The model is identical. The price, the contract, and the jurisdiction are not.

| Channel | What you are buying | Billing shape | Who owns the operational tax |
|---|---|---|---|
| **Vendor's own hosted API** | Inference from the lab that trained the model, usually first to serve a new release | Per token, vendor's own rate card and discount mechanics | Vendor |
| **Third-party host** (Together AI, Fireworks, Baseten, DeepInfra; AWS Bedrock for selected open-weight models) | The **serving**: SLA, data-processing location, an existing procurement relationship, consolidated billing | Per token, host's rate card. On Bedrock, it lands on the AWS invoice and inside the AWS commercial relationship | Host |
| **Self-hosting** on rented or owned GPUs | The weights, running on capacity you control | Per GPU-hour, 24/7 regardless of utilisation | You |

Two distinctions worth holding firmly, because clients routinely collapse them:

- **A third-party host is not GPU rental.** Together, Fireworks and Bedrock sell tokens
  and absorb capacity, batching and uptime. RunPod, Lambda and CoreWeave sell hours and
  hand you the stack. The first is a managed API that happens to serve an open model;
  the second is self-hosting with someone else's hardware. Their cost mechanics have
  nothing in common. `finops-ai-self-hosted-vs-managed.md` prices the second and is not
  duplicated here.
- **The premium a third-party host charges over the vendor's own API is not margin on
  the model.** It buys data-processing location, an enterprise SLA with credits, and a
  procurement path that Legal and Security have already cleared. Whether that premium
  is worth paying is a compliance and risk question with a price attached, not a rate
  negotiation. Price the channels only after that question is settled - see "Data
  residency decides the channel before price does" below.

**FinOps consequence.** Model selection and channel selection are two decisions, not
one. A routing layer that treats "GLM-5.2" as a single line item will silently mix
three different unit costs, three jurisdictions and three contracts in one cost centre.
Allocate by model *and* channel from the start.

---

## Per-vendor billing mechanics

> *All figures below are illustrative, list price, read from the vendor pricing pages on
> 23 August 2026 unless dated otherwise. Prices in this segment move on a scale of weeks
> and this file does not move with them. For a current figure, call a live pricing tool
> if one is available, otherwise check <https://optimtoken.optimnow.io>. What is durable
> here is the shape of each vendor's discount mechanics, not the absolute numbers.*

### DeepSeek: time-of-day pricing

DeepSeek introduced peak and off-peak rates with the V4 line, effective 16:00 UTC on
16 August 2026. This is the first mainstream LLM rate card where **when you run a job
changes its unit cost**, and it is the mechanic in this file with the most direct
FinOps consequence.

| Mechanic | How it works |
|---|---|
| Peak windows | 01:00-04:00 and 06:00-10:00 UTC, Monday to Friday. Seven peak hours per weekday |
| Off-peak | All other hours. Weekends are off-peak all day |
| Multiplier | Peak is exactly 2x off-peak, on input and output alike |
| Cache hits | Priced at roughly **3% of the cache-miss input rate** - materially deeper than the ~10% multiplier at OpenAI, Anthropic and Moonshot |

Illustrative off-peak rates per 1M tokens (input cache-miss / output), read
23 August 2026: DeepSeek V4 Flash $0.22 / $0.66; V4 Pro $0.66 / $1.98. Peak is double
each figure. Cache-hit input off-peak is $0.007 on Flash and $0.022 on Pro.

**Read the change correctly, because the framing traps forecasters.** Off-peak is not a
discount applied to the previous flat rate. The flat rate was replaced by a higher peak
rate, and off-peak is half of that new peak. Secondary reporting puts the prior V4-Pro
flat output rate at $0.87 per 1M tokens against $1.98 off-peak today, which means every
tier costs more than it did before, and the off-peak "discount" still lands above the
old flat price. A forecast that models the announcement as a saving will be wrong in
the wrong direction. *(Prior flat rate from press coverage of the August 2026
announcement, not from DeepSeek documentation - verify before quoting to a client.)*

**The 3% cache multiplier is the strongest lever on this rate card**, deeper than the
time-of-day mechanic. A stable system prompt or retrieved corpus that hits cache turns
input cost into a rounding error. It rewards prompt-prefix discipline far more than it
rewards scheduling.

### Qwen (Alibaba Model Studio): context steps and a two-track catalogue

| Mechanic | How it works |
|---|---|
| Context-length step | Price steps **above 256K input tokens**, not at the context limit. Illustrative for Qwen3.5-Plus, International (Singapore), read 23 August 2026: $0.40 / $2.40 per 1M tokens up to 256K input, stepping to $0.50 / $3.00 from 256K to 1M |
| Batch inference | 50% of the real-time rate on both input and output, where the model supports batch calls |
| Explicit context cache | Cache creation billed at 125% of the standard input price; cache hits at 10%. An implicit, automatic cache is also documented at a shallower discount - verify which one a given model uses before modelling the saving |
| Discount exclusivity | Batch and caching **do not stack**. Batch suits bulk offline jobs, caching suits high-frequency requests sharing a prefix. Pick one per workload |
| Endpoint pricing | The China (Beijing) and International (Singapore) endpoints carry different rate cards for the same model. Never quote a Qwen price without saying which endpoint it came from |

**The catalogue trap.** Alibaba runs a deliberate two-track strategy: the smaller Qwen3
and Qwen3-Coder lines ship as open weights, while the Plus and Max flagships are
proprietary and API-only, with no published weights. The model most clients actually
buy on Model Studio is therefore **not an open-weight model at all**. Treating the
vendor as "the open-weight channel" and then routing production traffic to a Max-tier
endpoint gives you a closed model with none of the exit optionality that justified the
choice. Check the specific model, not the vendor.

*(A prior version of this guidance recorded no published Qwen batch discount. Alibaba's
own pricing documentation states 50%, verified 23 August 2026.)*

### Kimi (Moonshot): the proof that open weight does not imply cheap

| Mechanic | How it works |
|---|---|
| Flagship rate | Kimi K3, illustrative and read 23 August 2026: $3.00 per 1M input tokens on a cache miss, $15.00 per 1M output tokens |
| Cache hits | $0.30 per 1M input tokens - 10% of the cache-miss rate, in line with Western vendors and three times shallower than DeepSeek's |
| Context | ~1M tokens (1,048,576), single tier, no long-context premium band published |
| Taxes | The rate card is quoted excluding applicable taxes, assessed at checkout by jurisdiction. Budget gross, not net |

**This is the single most useful data point in the file for a client conversation.** K3
at $3 / $15 sits exactly at Claude Sonnet 5's list rate of $3 / $15, and 50% above the
introductory $2 / $10 that Sonnet 5 carries through 31 August 2026 (see
`finops-anthropic.md`). An open-weight flagship from a Chinese lab is priced at or above
a Western mid-tier managed model. Any business case whose premise is "we switch to open
weights and cut inference cost" has to survive that comparison first.

**A catalogue-hygiene warning specific to this vendor.** Moonshot's older, cheaper
models rotate off the pricing page quickly, and third-party price trackers keep serving
figures for models the vendor no longer lists. A tracker figure for a Kimi model is
stale far more often than it is wrong-by-a-little. Re-verify on the platform before it
reaches a forecast.

### GLM (Z.ai): a coding subscription arrives in the open-weight channel

| Mechanic | How it works |
|---|---|
| Metered API | Illustrative for GLM-5.2, read 23 August 2026: $1.40 per 1M input tokens, $0.26 cached input, $4.40 output |
| Cache multiplier | Cached input is about **19% of the input rate**, not the ~10% the market has converged on. The gap matters when the caching business case is what justifies a migration |
| Free tier models | Some Flash-class models are published at zero cost. Free is a rate, not a commitment - treat availability as unguaranteed |
| **GLM Coding Plan** | A Claude Code-style seat subscription from **$18/month** at the entry tier. Secondary reporting puts the higher tiers at $72 and $160/month - verify before quoting |

**The seat model has crossed into the open-weight vendors, and it brings the seat
model's cost problems with it.** The GLM Coding Plan is not billed per token. It meters
a credit allowance against **two rolling windows simultaneously**: a 5-hour window that
refreshes 5 hours after consumption, and a weekly window that resets every 7 days.
Credits are derived from tokens - input, cached input and output each carry a multiplier,
divided by 10,000 - so the underlying token economics are still there, one abstraction
layer down where no cost report will show them.

Three FinOps consequences, all familiar from `finops-ai-dev-tools.md`:

- **Two windows means two exhaustion modes.** A developer can be inside their weekly
  allowance and blocked by the 5-hour window, or vice versa. Capacity complaints will
  not map cleanly onto either meter.
- **Seat cost is fixed, so utilisation is the only KPI that matters.** The waste pattern
  is dormant seats, not runaway tokens. Reconcile assigned seats against active users on
  the same cadence you use for any other developer tool subscription.
- **Time-of-day pricing shows up here too**, in credit form: usage outside Monday to
  Friday 14:00-18:00 Singapore time is documented as consuming credits at a 50%
  discount. The same scheduling lever as DeepSeek's, expressed as allowance rather than
  invoice.

---

## Licensing is a FinOps input, not a Legal footnote

The licence on an open-weight model constrains what you may do with it, and two of the
four vendors here attach obligations that trigger on **revenue or user-count
thresholds**. That makes the licence a variable in the business case, not a compliance
checkbox to be cleared afterwards.

| Vendor | Licence position as of August 2026 | What it means for a commitment |
|---|---|---|
| DeepSeek | MIT across code and weights on the V4 line | Permissive. No threshold obligations reported |
| Qwen (Alibaba) | Split. Smaller Qwen3 and Qwen3-Coder models under Apache 2.0; Max-tier flagships proprietary and API-only; at least one large August 2026 release under a custom, non-Apache licence | You cannot reason about "Qwen" as one licence. Check the exact model |
| Kimi (Moonshot) | **Not modified MIT, despite widespread reporting.** K3 ships under a custom "Kimi K3 License" (Hugging Face metadata records `license: other`, `license_name: kimi-k3`). Earlier Moonshot releases were modified MIT | Reported obligations include prominent "Kimi K3" branding above 100M monthly active users or $20M monthly revenue, and a separate agreement with Moonshot for model-as-a-service operators above $20M revenue over any consecutive 12 months |
| GLM (Z.ai) | MIT or modified MIT depending on the specific model | Permissive, but still per-model |

**The rule that survives every rate change: verify per model, not per family.** Kimi is
the cautionary case - the ecosystem reported K3 as modified MIT because the previous
generation was, and the actual LICENSE file in the repository says something else. A
family-level assumption carried into a business case is a legal exposure that arrives
at exactly the moment the deployment succeeds, because the thresholds are triggered by
growth.

**Practical sequencing.** Legal signs off on the specific checkpoint before Procurement
signs a volume commitment, not after. For a model-as-a-service or embedded-product use
case, that review is not optional at any scale, because the obligation attaches to
revenue you are forecasting rather than to spend you are incurring. The broader
licence-obligation discipline sits in `finops-itam.md`.

---

## Data residency decides the channel before price does

The vendors in this file process inference in China on their own APIs. Alibaba is the
partial exception, operating an International (Singapore) endpoint alongside the China
one, with a separate rate card.

Frame this as a determination, not a debate:

1. **Establish where the workload's data may be processed.** This is an existing answer
   inside the client's organisation, held by Legal, Security or the DPO. It is not a
   FinOps judgement and FinOps should not manufacture one.
2. **That answer eliminates channels before any price is compared.** If the vendor's own
   API is out of scope for a workload, its rate card is not a cheaper option that was
   rejected - it is not an option, and it does not belong in the comparison at all.
3. **A third-party host is the mechanism for keeping the model while changing the
   jurisdiction.** Together, Fireworks and Bedrock serve several of these checkpoints
   from US and EU regions under a Western contract. The premium over the vendor's own
   API is the price of that, and framing it that way makes the number defensible to a
   CFO rather than looking like a margin you failed to negotiate away.
4. **Workloads differ inside one organisation.** A public-documentation summariser and a
   customer-data extraction pipeline can legitimately land on different channels running
   the same model. Do not force a single estate-wide answer.

The recurring anti-pattern is the mirror of the one in
`finops-ai-self-hosted-vs-managed.md`: residency theatre in one direction (assuming a
managed API cannot meet an EU requirement when it can), and residency blindness in the
other (routing production traffic to whichever endpoint the benchmark used, and
discovering the jurisdiction at audit).

---

## FinOps guidance

### Route through a gateway, not through client code

Send simple, high-volume work through a routing layer (LiteLLM, Portkey, or a custom
proxy) rather than wiring vendor SDKs into applications. In this segment the gateway
earns its keep faster than usual:

- **The vendors are genuinely interchangeable for simple work.** Classification, routing,
  extraction and summarisation run acceptably on several of these models. That is exactly
  the traffic where a rate change should trigger a re-route, and only a gateway makes
  re-routing a config change.
- **Rate cards move on a scale of weeks.** DeepSeek repriced its entire line in a single
  announcement. Applications with a hardcoded vendor cannot respond.
- **It is the only place channel-level cost allocation can be enforced.** The gateway
  tags every call with model *and* channel, which is what makes the allocation
  recommended earlier in this file achievable rather than aspirational.
- **Keep frontier and high-stakes work on managed Western APIs** unless a specific
  evaluation says otherwise. The hybrid pattern in
  `finops-ai-self-hosted-vs-managed.md` applies unchanged; these vendors are another
  origin behind the same router.

### Treat every tracker figure as a same-week snapshot

Third-party price trackers, comparison sites and aggregator pages lag this segment
badly, and they keep listing models the vendors have retired. Two rules:

- **Re-verify on the vendor platform before any figure enters a forecast, a business
  case, or a client deliverable.** Not the tracker, not this file - the vendor's own
  pricing page, and record the date you read it.
- **A missing figure is a missing figure.** If a model, tier or endpoint is not listed,
  say so. Do not interpolate from a neighbouring model or the other endpoint. This is
  the general rule from SKILL.md "Price figures", and it bites hardest here because the
  catalogues churn.

### Schedule async work against time-of-day pricing

DeepSeek's peak windows and the GLM Coding Plan's off-peak credit discount create a
scheduling lever that most cost models have no field for. The mechanics:

- **Identify latency-tolerant work first.** Evaluation runs, batch classification,
  document enrichment, nightly summarisation, index rebuilds. This is the same
  workload-classification exercise that qualifies a job for a Batch API - the output of
  one feeds the other.
- **Shift it off-peak.** With a 2x peak multiplier, moving an async job out of the seven
  weekday peak hours halves its unit cost with no quality change and no code change.
  Weekends are off-peak all day on DeepSeek, which makes a weekend batch window the
  cheapest capacity on that rate card.
- **Check the peak window against the working day in your time zone.** The windows are
  fixed in UTC, so whether they overlap your engineers' interactive usage is an accident
  of geography. For a Central European team, the DeepSeek peak windows fall largely
  before and during the morning - close enough to the working day to matter, which makes
  scheduling a real decision rather than a free win.
- **Do not stack assumptions.** Where a vendor forbids combining batch and cache
  discounts (Alibaba states this explicitly), a model that applies both overstates the
  saving by the size of the smaller one.

### Maturity progression

| Stage | What good looks like |
|---|---|
| **Crawl** | Know whether these vendors are in the estate at all, and on which channel. Shadow usage on a personal API key is the common starting state. Establish the residency determination before optimising anything - a workload that should not be on the vendor API is a compliance finding, not a saving |
| **Walk** | Route through a gateway. Allocate by model and channel. Re-verify rates against vendor pages on a fixed cadence rather than on rumour. Apply the cache and batch mechanics per vendor, respecting the exclusivity rules. Reconcile any seat subscriptions against active users |
| **Run** | Schedule latency-tolerant workloads against time-of-day windows automatically. Re-evaluate channel placement per workload as rate cards move, with the routing change as a config deploy. Licence review is a standing gate in the model-onboarding process, not a one-off. Feed realised unit cost per completed task back into the routing policy - see `finops-agentic.md` |

The gate for entering this segment at all is **Walk**: an organisation that cannot yet
allocate AI spend by model will not be able to tell whether adding a fourth vendor
helped. Adding vendors is a rate-optimisation move, and rate optimisation on an
unallocated estate is guesswork with extra steps.

---

## Common anti-patterns

- **"Open weight, therefore cheap."** Kimi K3 at $3 / $15 disproves it at the top of the
  range, and Moonshot is not an outlier. Price the specific model.
- **"Open weight, therefore we can leave."** True only if the model you are buying has
  published weights. On Model Studio, the Plus and Max tiers do not. Exit optionality
  that was never checked is not optionality.
- **Reading a time-of-day repricing as a discount.** Off-peak is half of a raised peak,
  not a cut to the old flat rate. Model the delta against what you actually paid last
  month.
- **Assuming a licence from the family name.** Kimi K3 is not modified MIT even though
  its predecessors were, and the obligations trigger on revenue and user growth.
- **Comparing a vendor API price to a Bedrock or Together price as if they were the same
  purchase.** They are not: the premium buys jurisdiction, SLA and contract. Compare
  them only after residency has narrowed the field.
- **Quoting a tracker figure.** In this segment a tracker is a lead, not a source.
- **Copying the cache multiplier across vendors.** It ranges from about 3% (DeepSeek) to
  about 19% (GLM) of the input rate. A caching business case built on a borrowed
  assumption can be off by a factor of six.

---

## References (other files in this skill)

- `finops-ai-self-hosted-vs-managed.md` for the self-hosting channel, GPU-hour mechanics,
  the hidden operational cost surface, and the ML-Ops maturity rubric
- `finops-for-ai.md` for AI cost mechanics, allocation, tiered routing economics
- `finops-anthropic.md`, `finops-bedrock.md`, `finops-azure-openai.md`,
  `finops-vertexai.md` for the Western managed-API comparators
- `finops-ai-dev-tools.md` for seat-plus-usage coding-tool billing, which the GLM Coding
  Plan now mirrors
- `finops-agentic.md` for cost per completed task, the denominator that makes
  cross-vendor routing decisions comparable
- `finops-itam.md` for licence-obligation governance and vendor negotiation

---

> Sources: DeepSeek API pricing documentation, Alibaba Cloud Model Studio pricing
> documentation, Moonshot Kimi platform pricing, Z.ai pricing and DevPack documentation,
> all read 23 August 2026. Licence terms and non-current rates corroborated by secondary
> reporting as flagged inline. OptimNow methodology.

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
