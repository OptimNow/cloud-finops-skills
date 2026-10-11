# FinOps Foundation YouTube channel review: feasibility, plan and handover kit

Written 2026-10-11 from a cloud Claude Code session. The question was whether the
FinOps Foundation YouTube channel (<https://www.youtube.com/@finopsfoundation/videos>)
can be mined, video by video, for knowledge that bridges gaps in the Cloud FinOps
skill, with a summary of each talk, at reasonable cost and without losing quality.

Nothing in this folder is end-user content. It sits outside `plugins/cloud-finops/`,
so the Claude directory scanner never sees it, and nothing here is installed by the
plugin. The folder can be moved under the maintainer-local `pipeline/` folder with
one `git mv` if it is better kept private.

---

## Scope decision (2026-10-11, after the first read of this document)

The maintainer narrowed the first pass to two sets, in this order:

| Set | Playlist | Videos | Hours | Uploaded |
|---|---|---|---|---|
| Tokenomicon FinOps X (Amsterdam) | "Tokenomicon FinOps X" | 5 | 1.3 | about 12 days before 2026-10-11 |
| FinOps X 2026 | "FinOps X 2026 Keynotes, Breakout Sessions, and Lightning Talks" | 76 | 39.7 | about 3 months before 2026-10-11 |
| **Total** | no overlap between the two | **81** | **41** | |

Cadence: **five videos per day**, Tokenomicon first, then FinOps X 2026 in channel
order (newest upload first). That is 16 daily batches with 6 in the last, or 17 with
one. The processing order and status live in `digests/_queue.tsv`; each day's output
is one file, `digests/YYYY-MM-DD.md`, holding for each of its videos:

1. **Summary**: 150 to 250 words in our own words, with speaker, organisation,
   event and upload date.
2. **Takeaways**: three to six bullets, each tied to a timestamp in the talk.
3. **Skill changes**: what to add or update, naming the target reference file and
   section (or the new playbook or reference to create), with the proposed text
   and, for every billing mechanic, the primary page it was verified against or
   the explicit note that it is unconfirmed. "Nothing to add" is a valid verdict
   and is written as such, with the reason.

The one manual step is unchanged, but it is now about six minutes: the 81
transcripts are fetched from a laptop with

```powershell
python fetch_youtube_transcripts.py --catalogue channel-catalogue.tsv --playlist Tokenomicon --playlist "FinOps X 2026" --out transcripts
```

and the `transcripts` folder (about 10 MB, 81 JSON files) is placed in a private
Google Drive folder shared with the account the cloud session uses. A daily routine
in the cloud then reads the next five from Drive, writes the digest, verifies the
mechanics, commits to this branch and sends the day's digest as a notification. The
tier system below stays as the map for anything beyond these two sets.

---

## Verdict

- **Feasible, with one manual step.** The channel enumerates fine from a cloud
  container (570 videos, 60 playlists, all listed in `channel-catalogue.tsv`), but
  YouTube refuses transcript and player requests coming from cloud-provider IP
  ranges. On 2026-10-11 both routes were refused from this session:
  `youtube-transcript-api` returned `IpBlocked`, and `yt-dlp` got HTTP 429 and
  then a "sign in to confirm you are not a bot" check. The fetch has to run once
  from a laptop on a normal home or office connection. The script for that is in
  this folder; it runs unattended for 25 to 45 minutes. Everything after that is
  automatable. Confidence that the laptop run works: high (standard tooling,
  residential connections are normally served; a throttle mid-run is handled by
  resume).
- **Cost: tens of dollars of API credits, not hundreds.** The whole channel is
  about 325 hours of speech, roughly 3.9 million tokens of transcript. Summarising
  and extracting claims from every talk costs between 15 and 30 dollars at list
  price depending on the model, half that through the Batch API; the gap
  synthesis adds 6 to 14 dollars. The figures come from the AI Pricing Hub and are
  tabulated below. For comparison, one monthly content batch of the existing
  pipeline costs 13 to 15 dollars of credits (CLAUDE.md, 2026-05-15 entry).
- **Quality is controllable, on one condition.** A talk is a lead, never a
  source: the skill's sourcing rule (mechanics cite provider documentation) applies
  unchanged, and the standing verification fan-out that the 9 September 2026 batch
  introduced is the step that makes transcript-derived content safe. Auto-captions
  garble FinOps vocabulary (Savings Plans, FOCUS, vendor names); summaries survive
  that, extracted mechanics do not, hence the verification step.
- **The highest-yield subset is visible before a single transcript is read.** The
  Foundation curates its channel by FinOps capability, and its capability playlists
  land exactly on the capabilities the skill covers only as a secondary
  (`fcp-coverage.md`): Forecasting, Budgeting, Reporting & Analytics, Unit
  Economics, Governance, Executive alignment, Intersecting Disciplines. The gap map
  below is the first deliverable of this review and needed no transcript.

The original recommendation was a scoped first pass over tier 1 (301 videos, 160
hours). The maintainer narrowed it further to the 81-video scope above; the tiers
remain the map for any later extension.

---

## What was measured on 2026-10-11

| Item | Value |
|---|---|
| Videos on the channel | 570 |
| Total duration | 324.8 hours; mean 34.2 minutes |
| Duration spread | 94 under 10 min; 103 between 10 and 25; 289 between 25 and 50; 84 over 50 (longest 3 h 11, a 2022 vendor showcase) |
| Playlists | 60, with 985 memberships; 6 videos sit in no playlist |
| Spoken text to process | about 2.9 million words, about 3.9 million tokens, at 150 words per minute (confidence moderate: Q&A and slide-heavy talks run slower) |
| Views, whole channel | 487,000; the most viewed video is the "What is FinOps?" explainer (20,000) |
| Enumeration of channel and playlists from the cloud container | works (browse endpoint) |
| Transcript fetch from the cloud container | blocked (`IpBlocked`; `yt-dlp` 429 then bot check) |
| Upload dates | not available from the channel listing; the fetch script collects them per video. 144 titles carry a year marker, which `year_hint` records |

---

## The counterargument first

The skill is a library of billing mechanics and decision rules. The channel is
mostly practice talks, case studies, panels and sponsor sessions. Three
consequences follow, and they shape the scope recommendation.

1. **Yield per talk will be low.** Most talks will produce a summary and nothing
   for the skill. A realistic expectation is a few dozen concrete proposals from
   the whole channel, concentrated in a handful of capabilities. Confidence: low,
   no transcript has been read yet; this is the number to measure on the first
   batch before deciding to continue.
2. **Where the skill is deepest, the channel is thinnest.** Rate Optimization has
   5 videos, Allocation 22, Workload Optimization 39. What a talk says about
   billing mechanics is second-hand and often dated; under the sourcing rule it
   can only be a lead to the provider page. Expect almost no change to the
   provider references and the playbooks from this source.
3. **The Foundation's written material covers the same capabilities in a cleaner
   form.** The framework and capability pages, playbooks and working-group papers
   are CC BY 4.0 text, need no transcription, and are already the kind of source
   the content pipeline scans. If the only goal were to fill the secondary-only
   capabilities, the written pages would be cheaper per usable paragraph. What the
   videos add is what the pages do not carry: practitioner numbers, failure
   stories, the FinOps X 2026 material that is not written up yet, and the AI cost
   management practice talks that run ahead of the written framework.

So the project is worth running for the summaries and for the practice-side
capabilities, and it should be sized as a scoped pass with a yield check, not as a
full-channel commitment.

---

## Where the channel sits against the skill

The Foundation's playlists overlaid on `fcp-coverage.md`. `[~]` means the
capability is touched only as a secondary; `[ ]` means a true gap.

| FCP capability | Skill today | Channel material (videos / hours) | Reading |
|---|---|---|---|
| Forecasting | `[~]`; `finops-forecasting.md` is on the roadmap's active list (budget season was the trigger) | Forecasting 9 / 5 h, plus forecasting talks inside FinOps X 2026 | The most direct feed. Drafts the new reference |
| Budgeting | `[~]` by design (cross-cutting, roadmap note) | Budgeting 7 / 4 h | Material for the existing budgeting sections, no new file |
| Unit Economics | primary owner is `finops-for-ai.md` (AI side only); `finops-unit-economics.md` deferred P2 "until non-AI demand emerges" | Unit Economics 16 / 9 h, Metrics & KPIs 4 / 2 h | The non-AI demand the roadmap waits for is visible here (Canva, Duolingo and Palo Alto Networks in the playlist; Equifax and Gerdau in FinOps X 2026) |
| Reporting & Analytics | `[~]` | Reporting & Analytics 15 / 9 h, Data Ingestion 14 / 7 h, FOCUS 26 / 12 h | Candidate section or file. The roadmap defers a cost-warehouse file (P3); the FOCUS semantic-layer talks are its material |
| Governance, Policy & Risk | `[~]` | Cloud Policy & Governance 20 / 10 h | Candidate |
| Executive Strategy Alignment | `[~]` | FinOps Executive Stories 13 / 2 h | Short clips, low depth expected |
| FinOps Practice Operations | primary (`finops-framework.md`, `optimnow-methodology.md`), thin | Practice Operations 44 / 25 h, Adopting FinOps 21 / 9 h, Journeys 18 / 6 h | Largest body, mostly narrative. Good for operating-model patterns, weak on mechanics |
| Intersecting Disciplines | `[~]` | Intersecting Disciplines 9 / 5 h, the FinOps + ITFM and TBM talks | Candidate section |
| FinOps Assessment | `[~]` | one assessment walkthrough | Low |
| Education & Enablement | `[ ]`, deliberately deferred | Education & Enablement 15 / 8 h | Material exists if that decision changes |
| Scopes: data centre, hybrid | SaaS and ITAM covered; data centre not | FinOps for Data Center 2, Scopes 9 / 5 h, on-prem talks (Target, Sony) | Candidate |
| FinOps for AI | nine references, deep | FinOps for AI 11, AI for FinOps 8, Tokenomicon 5, and 33 of the 76 FinOps X 2026 titles | Yield is case numbers and new patterns (AI cost controls, agent trust, cost to serve), not mechanics |
| AWS, Azure, GCP, commitments, waste | deep | Rate Optimization 5, Allocation 22, Workload Optimization 39 | Low marginal yield |

Confidence in this map: moderate. It is built from the Foundation's playlists and
from titles, not from content. The transcripts will move individual rows, not the
shape.

---

## Pipeline

| Phase | What | Where it runs | Status |
|---|---|---|---|
| 0 | Enumerate the channel and its playlists, tag and tier every video | cloud session | done, this folder |
| 1 | Fetch transcripts and per-video metadata | **laptop** (the manual step) | script ready, `fetch_youtube_transcripts.py` |
| 2 | Per-talk summary and claim extraction, one request per talk | Anthropic API, Batch | to build once phase 1 output exists |
| 3 | Gap synthesis, one call per reference file | API or Claude Code session | to build |
| 4 | Verification fan-out: every proposed mechanic checked against its primary source | Claude Code session (needs web access and the repo) | the existing standing step from the content pipeline |
| 5 | Human review, content PRs through the normal process (no version bump) | maintainer | as today |

**Phase 2 request shape.** Input: the transcript (mean about 7,000 tokens) plus a
fixed prompt carrying the SKILL.md domain routing table and the 22 FCP
capabilities (about 1,500 tokens, cacheable). Output: one JSON record per talk,
about 900 tokens, rendered afterwards to markdown. Every claim must point at a
transcript timestamp so it can be checked against the video, and every claim is
typed so the mechanics can be sent to phase 4 and the opinions kept out of the
references.

```json
{
  "id": "gzqak-gAv-o",
  "summary": "150 to 250 words in our own words",
  "speakers_orgs": ["..."],
  "event": "FinOps X 2026",
  "upload_date": "2026-09-30",
  "fcp_capabilities": ["Forecasting"],
  "skill_references": ["finops-kpis-benchmarking.md"],
  "claims": [
    {"claim": "...", "type": "mechanic | practice | metric | case-number | opinion",
     "timestamp_s": 812, "verifiable_against": "provider doc | framework page | none"}
  ],
  "novelty_vs_skill": "covered | partial | gap | contradicts",
  "novelty_rationale": "...",
  "proposed_action": "none | extend <file> <section> | new playbook <slug> | new reference <name>",
  "quality_flags": ["auto_captions", "vendor_pitch", "pre_2023", "non_english"]
}
```

**Phase 3 request shape.** One call per reference file: the file body plus every
claim tagged to it. Output: a verdict per claim (already covered, partial, gap,
contradiction) and, for gaps, a draft insertion with its source (video URL and
timestamp) and the primary page it must be verified against. The provider pattern
catalogues are read by section, as the MCP server already does.

**Phase 4** is the fan-out of read-only agents that the 9 September 2026 batch
made a standing step: one agent per proposed mechanic, verdict table back,
unconfirmed claims dropped or marked. About ten minutes of wall-clock per ten
claims, no pipeline credits.

**The per-talk summary deliverable.** One markdown record per talk (summary, key
claims with timestamps, capability tags, verdict, proposed action, link), plus an
index per playlist. A Google Sheet export (one row per talk) is a cheap addition if
the summaries are meant to be browsed rather than grepped.

---

## Cost

Figures from the AI Pricing Hub (`estimate-llm-cost`, source optimtoken.optimnow.io,
tier 1, prices verified, upstream timestamp 2026-10-11T09:37Z). The hub costs a
custom request shape at list price with no batch or cache discount; the batch
column is derived from the batch prices the hub returned for each model (half of
list). Tier 1 is 301 of 570 talks, so about 53% of a whole-channel figure.

**Phase 2, whole channel: 570 requests at 8,500 input and 900 output tokens.**

| Model | List, as returned | Batch, derived |
|---|---|---|
| Claude Haiku 5.5 (triage only, 300 output tokens) | $0.57 | $0.29 |
| Claude Sonnet 5.5 | $14.82 | $7.41 |
| Claude Opus 5.5 | $29.64 | $14.82 |
| Claude Fable 5.1 (derived from the hub's rates, $10 / $50 per 1M) | $74.10 | $37.05 |

**Phase 3: 36 requests at 24,000 input and 3,000 output tokens.**

| Model | List, as returned | Batch, derived |
|---|---|---|
| Claude Opus 5.5 | $5.62 | $2.81 |
| Claude Fable 5.1 | $14.04 | $7.02 |

**Phase 4** depends on the number of proposals. A rough shape of 50 claims at
60,000 tokens each is 15 to 25 dollars on Opus 5.5 through the API, or session
usage with no credits if it runs inside Claude Code as it does today. Confidence:
low.

**Recommended mix and totals.**

| Scope | Mix | Credits, approximate |
|---|---|---|
| Tier 1 (301 talks) | Opus 5.5 batch for phase 2, Fable 5.1 for phase 3, phase 4 inside Claude Code | about $25 |
| Whole channel | same mix | about $30 |
| Whole channel, everything at list price on Opus 5.5 including phase 4 via API | upper bound | about $60 |

Why Opus 5.5 rather than Sonnet 5.5 for phase 2: the per-talk extraction is where
an invented claim would originate, the difference is 7 to 15 dollars on the whole
channel, and a stronger extractor means fewer corrections in phase 5, which is
the expensive step. Sonnet 5.5 is the right choice if the budget is the
constraint. Confidence in the cost figures: moderate; the per-talk token shape is
an estimate from durations, so the real bill can differ by a third either way.

**Time.** Phase 1 on a laptop: about 25 minutes for tier 1, 45 for the whole
channel, unattended. Phase 2 through the Batch API: results usually within the
hour, 24 hours at most. Phase 3: minutes. Phase 4: about ten minutes per ten
claims. Phase 5: the real cost, measured in hours of review, and the reason to
scope the first pass.

---

## Quality rules

These are the repo's existing rules applied to a new source, plus two that are
specific to transcripts.

1. **A talk is a lead, not a source.** Any billing mechanic a talk mentions goes
   through phase 4 against the provider's own page before it enters a reference
   (CLAUDE.md, Content rules, Sourcing). Practice patterns and case numbers can be
   cited to the talk itself, by video URL and timestamp, as what a named
   practitioner reported.
2. **Dates come from metadata, not from the model.** The applier has been caught
   inventing "as of" dates by copying neighbouring sources (9 September 2026
   lesson). The talk's upload date is in the fetched record; the summary carries
   it; nothing is dated by inference.
3. **Auto-captions are flagged.** The record says whether the track was
   human-made or auto-generated (`is_generated`). A mechanic extracted from an
   auto-generated track needs the phase 4 check twice over; a figure heard in an
   auto-generated track is not reusable without the slide or the primary page.
4. **No verbatim reuse, no transcript in the repository.** The talks belong to
   their speakers and to the Foundation. Summaries are written in our own words
   with attribution and a link. Transcript files stay on the laptop and in a
   private drop (Drive); they are never committed, and never enter the plugin
   folder (which is markdown-only and scanned on every commit).
5. **Figures follow the dated-price rule.** A price heard in a talk is, at best,
   an illustrative dated figure; the AI Pricing Hub remains the live source.
6. **Old talks are discounted.** 2021 and 2022 content predates FOCUS 1.0, GenAI
   cost management and the 2025 framework revision. It is tier 2 or 3 by playlist
   and is summarised, not mined, unless a tier 1 gap points back to it.
7. **Measure yield before widening scope.** The first 50 tier 1 talks give the
   proposals-per-talk rate; if it is near zero outside the practice capabilities,
   the whole-channel run is not worth its review hours.

---

## Scope and tiers

Tiers are assigned from the Foundation's own playlists, in `channel-catalogue.tsv`
(column `tier`; a video in several playlists takes the best tier).

| Tier | Rule | Videos | Hours |
|---|---|---|---|
| 1 | FinOps X 2026, FinOps X 2025, FinOps X Europe 2024, Tokenomicon, FinOps for AI, AI for FinOps, FOCUS, State of FinOps, and every capability playlist where the skill has no primary owner or is thin (Forecasting, Budgeting, Reporting & Analytics, Data Ingestion, Unit Economics, Metrics & KPIs, Policy & Governance, Practice Operations, Executive Stories, Intersecting Disciplines, Security intersection, Scopes, Data Center, Invoicing & Chargeback, Anomaly Management, Licensing & SaaS, Onboarding Workloads) | 301 | 160 |
| 2 | FinOps X 2024, 2023 and 2022, FinOps X Days, Summits, Allocation, Rate and Workload Optimization, Optimizing for Value, Architecting, Sustainability, Public Sector, Multi-cloud, Journeys, Adopting FinOps, Personas, Working Groups, Education & Enablement, Cloud Updates, Insights, APJ summits, and the 6 videos in no playlist | 198 | 130 |
| 3 | Vendor Showcase, Sponsor Sessions, Tooling, Tools & Services, Women in FinOps, FinOpsBE, Careers, Program Information, What is FinOps, Community Perspectives, Industry Events, LATAM | 71 | 34 |

The largest playlists, for orientation:

| Playlist | Videos | Hours | Tier |
|---|---|---|---|
| FinOps X 2026 Keynotes, Breakout Sessions, and Lightning Talks | 76 | 40 | 1 |
| FinOps X 2024: Keynotes, Breakout Sessions, and Cloud Announcements | 70 | 49 | 2 |
| FinOps X 2023: Keynotes, Breakout Sessions, and Clips | 65 | 35 | 2 |
| FinOps Summits | 51 | 63 | 2 |
| FinOps Practice Operations | 44 | 25 | 1 |
| Workload Optimization | 39 | 22 | 2 |
| FinOps X 2022: Keynotes, Breakout Sessions, and Clips | 36 | 17 | 2 |
| FinOps X 2025 - Keynotes & Breakouts | 34 | 25 | 1 |
| FinOps X Europe 2024 | 33 | 25 | 1 |
| FinOps Community Perspectives | 31 | 4 | 3 |
| FinOps Open Cost and Usage Specification (FOCUS) | 26 | 12 | 1 |
| Allocation | 22 | 10 | 2 |
| Cloud Policy & Governance | 20 | 10 | 1 |
| Unit Economics | 16 | 9 | 1 |
| Reporting & Analytics | 15 | 9 | 1 |
| Data Ingestion | 14 | 7 | 1 |
| Invoicing & Chargeback | 14 | 8 | 1 |
| FinOps for AI | 11 | 6 | 1 |
| Forecasting | 9 | 5 | 1 |
| AI for FinOps | 8 | 2 | 1 |
| Budgeting | 7 | 4 | 1 |

Tier 3 is summarised from titles only, or skipped. Tier 2 is run after tier 1 has
shown its yield.

---

## The manual step: running the fetch on a laptop

The script needs Python 3.10 or newer and two open-source packages: `yt-dlp`
(lists the channel and reads per-video metadata) and `youtube-transcript-api`
(reads the caption tracks). It never downloads video or audio.

**Windows (PowerShell)**

1. Install Python from <https://www.python.org/downloads/> if `python --version`
   in PowerShell does not answer. Tick "Add python.exe to PATH" in the installer.
2. Get this folder onto the laptop: `git pull` on the branch that carries it, or
   download `fetch_youtube_transcripts.py` and `channel-catalogue.tsv` from GitHub.
3. Open PowerShell in the folder (in Explorer, Shift + right-click, "Open
   PowerShell window here"), then create an isolated environment so nothing is
   installed system-wide:

   ```powershell
   python -m venv yt-env
   .\yt-env\Scripts\Activate.ps1
   pip install yt-dlp youtube-transcript-api
   ```

   If the second line is refused with an execution-policy message, run
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once in that
   window and repeat it. The prompt shows `(yt-env)` when the environment is
   active.
4. Trial run on five videos:

   ```powershell
   python fetch_youtube_transcripts.py --catalogue channel-catalogue.tsv --tiers 1 --out transcripts --limit 5
   ```

   Expect five lines starting with `ok (auto, ...)` or `ok (manual, ...)`, and
   five `.json` files in a new `transcripts` folder. Open one in a text editor: it
   holds the title, the upload date, the transcript as one string and the
   timestamped segments.
5. Full tier 1 run (about 25 minutes, unattended):

   ```powershell
   python fetch_youtube_transcripts.py --catalogue channel-catalogue.tsv --tiers 1 --out transcripts
   ```

   The run can be stopped with Ctrl+C and started again: videos already fetched
   are skipped. For the whole channel, drop `--tiers 1`. To skip the per-video
   metadata call and run twice as fast, add `--no-metadata` (the upload dates are
   then missing, which rule 2 above needs, so prefer the default).
6. When it ends, the last line reads `fetched N, already present M, failed K`. A
   few failures are normal (videos without captions, live-stream recordings): they
   are listed as `<id>.error.txt` files and the run moves on.

**macOS or Linux (Terminal)**: identical, except step 3 activates with
`source yt-env/bin/activate`.

**What to do if it stops with "YouTube is blocking this IP".** The script stops
deliberately so the block does not deepen. Wait a few hours (or switch to another
connection, a phone hotspot works) and run the same command again; it resumes.
Raising `--sleep 2.0` to `--sleep 5.0` makes a repeat less likely.

**A warning about a missing JavaScript runtime (deno)** can appear from `yt-dlp`
during the metadata step. It concerns media formats, which this script never
downloads; the title, date and description still come through. If the metadata
step fails on every video, rerun with `--no-metadata` and report it (confidence
on this point: moderate, it was not reproducible from the cloud session).

**Alternatives if a laptop run is not wanted.** `youtube-transcript-api`
documents a rotating residential proxy option (a paid third-party service, a few
dollars a month) that lets the fetch run unattended from a server; it works
around YouTube's block rather than avoiding it, and YouTube's terms treat
automated access as a grey area, so the laptop run is the cleaner path. `yt-dlp`
can also use the cookies of a signed-in browser on the laptop, which is not
needed when the plain run works.

---

## Handing the transcripts back

The output folder is about 120 KB per video (the timestamped segments are the
bulk): roughly 35 MB for tier 1, 70 MB for the whole channel. Two options:

- **Zip the folder and put it in a private Google Drive folder** shared with the
  account used by the cloud session, then say so in the session. The Drive
  connector reads it from there and phases 2 to 5 run in the cloud.
- **Run phases 2 to 5 locally** in Claude Code on the laptop, from the same
  checkout, which is also where the private `pipeline/` folder already lives.

Transcripts are never pushed to this repository, in either option.

---

## Decisions needed

1. **Scope of the first pass.** Recommended: tier 1 only (301 talks), with the
   yield check after the first 50. Alternatives: tiers 1 and 2 (499), or the whole
   channel (570).
2. **Model mix.** Recommended: Opus 5.5 through the Batch API for the per-talk
   step, Fable 5.1 for the per-reference synthesis, the verification fan-out inside
   Claude Code. Budget alternative: Sonnet 5.5 for the per-talk step.
3. **Where the summaries live.** Recommended: maintainer-local under `pipeline/`
   (gitignored) with a Google Sheet export for browsing; only the gap report and
   the resulting content changes reach this repository. Alternative: a
   `summaries/` folder in this `docs/youtube-review/` folder, which publishes a
   digest of 300 to 570 talks under the repo's CC BY-SA licence.
4. **Where phases 2 to 5 run.** In the cloud session from a Drive drop, or
   locally on the laptop next to the pipeline.

---

## What happens once the transcripts exist

1. A batch script for phase 2 (Anthropic SDK, Batch API, prompt caching on the
   fixed prefix), run on the first 50 tier 1 talks, and a yield reading.
2. The per-talk summaries, rendered to markdown and, if wanted, to a Sheet.
3. The gap report per reference, with every mechanic through the verification
   fan-out and a verdict table.
4. Content PRs through the normal process: routing tables, llms.txt, the
   coverage artefacts, no version bump. The probable first new file is
   `finops-forecasting.md`, which the roadmap already lists as triggered; the
   probable first extensions are the unit-economics and reporting material in
   `finops-kpis-benchmarking.md` and `finops-allocation-showback.md`.

---

## Files in this folder

| File | What |
|---|---|
| `README.md` | this document |
| `channel-catalogue.tsv` | the 570 videos as listed on 2026-10-11: `id` (the video URL is `https://www.youtube.com/watch?v=<id>`), `duration_s`, `view_count`, `year_hint` (from the title only, blank for most; the fetch adds the real upload date), `tier`, `playlists` (the Foundation's playlists the video belongs to, `; `-separated), `title` |
| `digests/_queue.tsv` | the 81 videos of the 2026-10-11 scope in processing order, with a `status` column (`pending`, `done`, `skipped`) and the date of the digest that covered each one |
| `digests/YYYY-MM-DD.md` | one file per daily batch of five: summary, takeaways and proposed skill changes per video |
| `fetch_youtube_transcripts.py` | the phase 1 script: enumerates the channel or reads the catalogue, fetches the English caption track (human-made preferred, auto-generated otherwise, translated as a last resort) and per-video metadata, writes one JSON per video, resumes on rerun, stops cleanly on an IP block |

To refresh the catalogue after new uploads, run the script without `--catalogue`:
it enumerates the channel itself and writes `_catalogue.json` next to the
transcripts (the playlist tags and tiers in the committed TSV are then missing for
the new videos; new FinOps X talks are tier 1 by default).
