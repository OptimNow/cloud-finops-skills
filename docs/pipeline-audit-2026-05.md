# Pipeline audit: refresh pipeline, May 2026

> Phase 1 of the Roadmap P1 work captured in [CLAUDE.md](../CLAUDE.md). This
> document is the audit deliverable. Hardening (Phase 2), stabilisation
> (Phase 3) and publication (Phase 4) are tracked separately. Nothing in this
> document modifies pipeline code.

**Audit date:** 2026-05-11
**Auditor:** Claude (Opus 4.7, agent-assisted)
**Scope:** every Python module under `pipeline/`, including the frozen entry
point. State directory inspected for shape, not content. The MCP server
(`pipeline/mcp_server/`) and `sources.yaml` accuracy are explicitly out of
scope (see section 11).

---

## Correction (2026-05-15): root cause was max_tokens, not prompt-instruction failure

The first production run of the Harden PR A and B code on the 15 May 2026
scheduled scan surfaced three concrete failures that materially correct the
original audit. **The audit below should be read with these corrections in
mind; some of its conclusions and recommendations were wrong.**

**Correction 1: the actual root cause of the April-May 2026 truncations was
`max_tokens: 4096` in `pipeline/config.yaml`, not prompt-instruction
failure.** Reference files like `finops-aws.md` (2657 lines, ~12K output
tokens) cannot be returned in full when the model is capped at 4096 output
tokens. The model writes from the top, hits the cap, and stops mid-file -
which presents as "the model truncated despite being told to preserve the
footer". It is deterministic on any file >3K tokens, not the "~5% of the
time" the audit hypothesised. The fix is a one-line config bump
(`max_tokens: 16384`); the elaborate tool-use migration the audit
recommended as Phase-2 Item 1 was solving a problem we did not have.

**Correction 2: the tool-use migration (Harden Item 1) does not work
reliably with the current Opus.** Under `tool_choice` forcing, the model
regressed to the legacy XML tool-call format and emitted XML strings
*inside* the JSON `hunks` field (e.g. `<parameter name="before">...`).
Python then iterated the string character-by-character, producing 1200+
malformed-hunk warnings per file. The migration was rolled back on
2026-05-15; forensic preserved at
`pipeline/applier/file_updater.py.harden-a-tool-use-attempt.bak`.
Free-form rewrite is the production path again, now with an adequate
`max_tokens` budget and a real-API smoke test.

**Correction 3: 79 passing tests with hand-crafted mocks of the Anthropic
response gave false confidence.** None of the Harden PR A or B tests
talked to the real API. The tool-use migration looked correct in tests but
failed instantly in production because the mocks I wrote never emitted the
shape (XML-in-JSON) that the real model emits. The audit and Harden plan
both implicitly assumed mock fidelity. A `pipeline/smoke_test.py` is now
in place that runs the real API against the smallest reference file
before any production batch.

**Correction 4: the guard rails are reactive, not preventive - and the
original audit didn't catch that distinction.** The three guards
(`validate_post_apply`, lines 75-116) only fire inside
`apply_with_guard_rails`, which only runs during `--execute`. Preview mode
(`--preview`) showed proposals to the user without validation. On
2026-05-15 the user saw a diff in their terminal with everything after
line 288 of a 2657-line file deleted - a max-tokens artefact that the
guard rails would have rolled back at execute time but that should never
have been displayed at all. Preview-mode guard rails were added to
`_process_change` (via `_validate_content`) on the same day so an unsafe
proposal now prints "REJECTED by guard rail" instead of a 1000-line
unified diff.

**What remains valid from the original audit:**
- The module-by-module contracts (section 2) - accurate
- The destructive-actions inventory (section 4) - accurate
- The state-directory shape (section 5) - accurate
- The guard-rail logic and tests (section 6) - accurate; the guard rails
  themselves work, the gap was where they were invoked
- The implicit-assumptions list (section 7) - mostly accurate; should add
  "config.yaml max_tokens is sized for the largest reference file" as
  assumption #12, which was violated since at least the original 2024
  implementation
- The unfreeze criteria (section 10) - U1 and U3 still apply; U6 (tool-use
  migration) should be removed since the migration was rolled back

**What is wrong in the original audit:**
- The framing in the Executive Summary and section 8 that tool-use
  migration is the highest-value remediation - it isn't, max_tokens is
- The "~5% of the time on long files" framing in section 6's
  introduction - it was 100% on files >3K tokens
- The unfreeze criterion U6 (tool-use migration done) - cannot be met
  with current Opus behaviour
- The implicit framing throughout that 79 passing mock tests means the
  pipeline is safe to run - they meant nothing for production fitness

The rest of the document below is the original audit, preserved unchanged
for the historical record. Read it knowing what we now know.

---

## 1. Executive summary

The pipeline scans 30 cloud-provider and FinOps content sources every 15 days,
classifies relevant changes via Claude Sonnet, generates a CHANGES.md report,
optionally opens a GitHub issue, and is reviewed and applied through a
separate `run_apply.py` flow that calls Claude Opus to rewrite the target
reference files. Between 15 April and 1 May 2026, two consecutive runs of the
applier silently truncated 8 reference files in `skills/cloud-finops/references/`
(see `CLAUDE.md` "Lessons learned"). Hard guard rails landed in
`pipeline/applier/file_updater.py` after the incident and the runner was
renamed `run_apply.py.FROZEN` until the rest of the pipeline reaches the same
discipline.

The audit finds:

- **The applier guard rails work as documented.** All three guards
  (`validate_post_apply` lines 75-116, `apply_with_guard_rails` lines
  119-172, run-level fail-safe via `MAX_RUN_FAILURES = 2`) are present in
  code. All 9 unit tests in `pipeline/tests/test_file_updater_guards.py`
  pass on Python 3.12. The full test suite (43 tests across 4 files) is
  green.
- **The other modules still rely on prompt-only or implicit
  guarantees.** The fetcher does not validate that an HTTP 200 has a
  non-empty body; the classifier and applier both round-trip free-form
  markdown that is regex-parsed (no tool-use structured output); the
  proposer writes `CHANGES.md` without well-formedness validation; no
  module emits a per-run structured report.
- **The pipeline writes to only one location in the public content
  tree** (`applier/file_updater.py:154`), and that one write is
  guard-railed. No other module can touch
  `skills/cloud-finops/references/` or `skills/cloud-finops/playbooks/` directly. This
  was the explicit pre-condition for the snapshot+rollback discipline to
  be sufficient.
- **24 deprecation warnings** are emitted on every test run from the
  widespread use of `datetime.utcnow()` (Python 3.12 deprecation). Not a
  correctness issue today; will break on Python 3.13+.
- **20+ `.bak` files** sit under `skills/cloud-finops/references/.backups/` as
  forensic artefacts from the April-May 2026 runs. The current code
  retains every snapshot for ever; no retention or cleanup policy.

The audit recommends nine concrete hardening items (section 9) and proposes
four measurable unfreeze criteria on top of the four already in the Roadmap
(section 10).

---

## 2. Module-by-module contracts

For each module: entry function signatures, inputs, outputs, side effects,
failure modes, and gaps. Every claim cites `pipeline/<file>:<line>`.

### 2.1 `pipeline/run_scan.py` (entry point, 379 LOC)

**Entry:** `main()` at `pipeline/run_scan.py:202`.

**CLI flags:** `--force`, `--lookback N`, `--no-email`, `--sources <freq>`,
`--github-issue` (`pipeline/run_scan.py:206-231`).

**Inputs:**
- `pipeline/config.yaml` via `load_config()` at line 35
- `pipeline/sources.yaml` via `load_sources()` at line 244
- `state/last-run.json` via `load_state()` at line 60 (defaults to empty
  shell if absent, line 66-76)
- Reference file content via `load_reference_contents()` at line 41 - reads
  every `*.md` under `skills/cloud-finops/references/`, capped at 300 lines per
  file (line 55) to stay under the Anthropic input-TPM ceiling

**Outputs:**
- `state/CHANGES.md` (via `generate_changes_report()` at line 302)
- `state/pending-changes.json` (via `save_pending_changes()` at line 309)
- `state/history/scan-<timestamp>.md` (lines 316-321)
- Updated `state/last-run.json` (line 335, also line 289 on the
  no-new-items early exit and line 357 after GitHub issue creation)
- Optional GitHub issue (via `create_github_issue()` at line 354, only when
  `--github-issue` and classified changes exist)
- Optional email alert (via `send_alert_email()` at line 342, only when
  `not args.no_email and config["email"]["enabled"] and classified`)

**Side effects:**
- HTTP requests for every source (30 sources, RSS + web)
- Anthropic API calls (one per fetched item, line 294)
- `state/` directory created if missing (line 82)
- `state/history/` directory created (line 317)

**Failure modes:**
- `ImportError` from alerter modules: caught and ignored
  (`pipeline/run_scan.py:344-345`, `pipeline/run_scan.py:359-360`)
- Generic `Exception` from alerter modules: caught, logged, run continues
  (lines 347, 362). Means an SMTP failure does not abort the scan, but
  also means a programming bug in the alerter is silenced.
- No structured run report on success or failure. Auditing requires
  scrolling `state/scan.log`.

**Gaps:**
- `datetime.utcnow()` used at lines 142, 280, 287, 324 - deprecated since
  Python 3.12, removed in a future version.
- `state["processed_urls"]` is capped at 500 (line 330) but the cap is
  applied via `list(set(...))[-500:]`. `set()` does not preserve insertion
  order in pre-3.7 Python; Python 3.7+ preserves dict insertion order but
  not set ordering. This means the cap may evict arbitrary URLs rather
  than the oldest ones - subtle, may cause re-fetch flicker.
- No idempotency check: re-running the same scan duplicates URL
  processing for any URL that fell off the 500-cap.
- `save_pending_changes()` has a well-documented merge strategy (lines
  87-199, "Correctif A") that explicitly preserves decided items - this
  is good and was a deliberate hardening from prior work.

### 2.2 `pipeline/run_apply.py.FROZEN` (frozen entry point, 274 LOC)

**Status:** Renamed to `.FROZEN` to make non-executable from the CLI; will
be renamed back when unfreeze criteria are met. Cannot run from the command
line until then.

**Entry:** `main()` at `pipeline/run_apply.py.FROZEN:82`.

**CLI flags:** `--list`, `--preview N`, `--approve i,j,k`, `--reject i,j`,
`--execute`, `--pr` (lines 86-104).

**Inputs:**
- `pipeline/config.yaml`
- `state/pending-changes.json` via `load_pending()` at line 46

**Outputs:**
- Mutated `state/pending-changes.json` (status flips between
  `PENDING_REVIEW`, `APPROVED`, `REJECTED`, `APPLIED` - lines 147, 157,
  184)
- New git branch `content/<day>-<month>-<year>` if on main (line 198,
  via `git_utils.create_and_checkout_branch`)
- Git commit on that branch with message
  `Content update - <day> <month> <year>` plus a per-change bullet list
  (lines 212-218)
- `git push -u origin <branch>` (line 221)
- GitHub PR via `gh pr create` (line 230)

**Side effects:**
- Anthropic API calls during `--preview` and `--execute` (one per
  affected file in each change)
- File writes to `skills/cloud-finops/references/<filename>` (only path that
  writes the public tree, via `applier/file_updater.py:154`)
- File copies to `skills/cloud-finops/references/.backups/<filename>.<iso>.bak`
  (via `applier/file_updater.py:151`)

**Failure modes:**
- `_create_content_pr()` aborts on branch-create failure (lines 203-205),
  commit failure (lines 217-218), or push failure (lines 222-223). Each
  exits with a logger error and no PR is opened. **Files have already
  been written to disk at this point** - the abort happens after apply.
- If `args.execute` succeeds and `--pr` is omitted, files are on disk
  but uncommitted. The user is expected to run `git diff
  skills/cloud-finops/references/` (line 188).
- No rollback of applied changes if PR creation fails. The applier's
  guard rails roll back individual files when the *content* fails
  validation, but not when the *downstream git/PR* fails.

**Gaps:**
- `datetime.utcnow()` at line 196.
- Branch reuse logic at lines 202-208: if not on main, reuses current
  branch. Means content commits can land on an in-progress feature branch
  inadvertently. The safer behaviour would be to refuse and require a
  fresh branch.
- No verification that `skills/cloud-finops/references/` has no unstaged changes
  before apply. A user with mid-edit state in those files could lose
  uncommitted edits when the applier overwrites.

### 2.3 `pipeline/scanner/fetcher.py` (165 LOC)

**Entry:** `fetch_source(source, lookback_days)` at line 47, dispatches to
type-specific fetchers based on `source["type"]`.

**Inputs:** a source dict from `sources.yaml`, plus `lookback_days`.

**Outputs:** `list[FetchedItem]` where each `FetchedItem`
(`pipeline/scanner/fetcher.py:25-37`) carries source metadata + a
`content_snippet` capped at 2000 chars (RSS, line 104) or 4000 chars (web,
line 142).

**Failure modes:**
- HTTP errors via `resp.raise_for_status()` (line 121) raise
  `requests.HTTPError` which is caught by the broad `except Exception` at
  line 65 and logged. **The status check exists** (contrary to a common
  assumption); what is missing is content validation after status passes.
- `feedparser.parse(rss_url)` (line 73) does not raise on most parse
  failures - it returns a feed with `entries=[]`. A broken feed therefore
  silently returns zero items, which the run logs only as
  `"  <source-name>: 0 fetched, 0 new"`.
- `_parse_feed_date()` (line 150) returns `None` if both
  `published_parsed` and `updated_parsed` are missing or unparsable. An
  item with no date is **not** filtered by the lookback cutoff (line 83
  only filters when `published` is truthy), so old items can flow through.

**Gaps (high impact):**
- No content-type check after `requests.get()`. A 200 response with a JSON
  body, a CDN error page, or any non-HTML payload will be passed to
  BeautifulSoup, which will parse it as HTML and return the text. This is
  the failure mode the Roadmap names explicitly: "scanner validates fetch
  results (HTTP status, content-type, minimum payload length) so a
  200-with-empty-body cannot become a 'this source has no news'
  classification".
- No minimum-payload-length check. An empty 200 (`<html></html>`)
  produces a `FetchedItem` with empty `content_snippet`, which is then
  passed to the classifier as a candidate for relevance scoring.
- `datetime.utcnow()` at lines 74, 141 (deprecated).
- `except Exception` at line 65 swallows programming bugs alongside
  network errors.

### 2.4 `pipeline/scanner/classifier.py` (221 LOC)

**Entry:** `classify_items(items, reference_summaries, config)` at line 69.

**Inputs:**
- `items`: list of `FetchedItem` from the fetcher
- `reference_summaries`: dict mapping filename to *full* file content
  (historical parameter name; the values are no longer 10-line summaries)
- `config`: pipeline config with `classification.model`,
  `classification.max_tokens`, `classification.temperature`, and
  `urgency_scores`

**Outputs:** `list[ClassifiedChange]` (lines 26-41), filtered to
`is_relevant=True` only (line 104), sorted by `urgency_score` descending
(line 125).

**LLM call:** Sonnet 4 (`claude-sonnet-4-20250514` per
`config.yaml:10`), one call per item via
`pipeline/scanner/classifier.py:199-205`. System blocks use
`cache_control: ephemeral` on the reference-files block (line 194) so
multi-item runs reuse the cached prefix for up to 5 minutes.

**Prompt strategy:** Free-form JSON wrapped in markdown fences expected
(lines 174-182 define the exact JSON shape requested). Response is
regex-fence-stripped (lines 209-213) then `json.loads()` (line 214).

**Failure modes:**
- `json.JSONDecodeError`: logged, returns `None` (lines 216-218). The
  item is silently dropped from the classified output.
- `anthropic.APIError`: logged, returns `None` (lines 219-221). Same
  silent drop.
- No retry on transient errors (rate limits, 5xx). One transient error
  per item means that item is lost from this scan.
- No validation that the parsed JSON has the required fields. `result.get("is_relevant", False)`
  (line 104) is defensive, but missing `change_type`,
  `affected_files`, etc. fall through to defaults that may not match
  intent.

**Gaps:**
- **No tool-use structured output.** The Roadmap names this explicitly:
  "the Anthropic API calls in `applier/file_updater.py` switch to the
  structured output (tool-use) pattern". Same argument applies to the
  classifier - tool-use would replace the regex fence-strip + `json.loads`
  with a typed JSON response guaranteed by the API.
- Cache eviction risk: the 5-minute ephemeral TTL may expire mid-run if
  classification of one item is slow. A multi-minute API stall could
  force a cache miss on the next item, re-uploading ~50-100K tokens
  unexpectedly.

### 2.5 `pipeline/proposer/reporter.py` (114 LOC)

**Entry:** `generate_changes_report(classified_changes, output_path, scan_metadata)`
at line 32.

**Inputs:** the classified-change list, an output path (resolved from
config), and scan metadata (`sources_checked`, `items_fetched`).

**Outputs:**
- Returns the report content as a string (line 114)
- Writes the same content to `output_path` (line 112) after creating
  parent directories (line 110)

**Side effects:** disk write at line 112. No LLM call. No subprocess.

**Failure modes:**
- No try/except. Any exception propagates to `run_scan.py` which has no
  catch around `generate_changes_report` (line 302), so the entire scan
  aborts. Not necessarily bad - a report writer failing is something to
  notice - but inconsistent with how the alerters are wrapped.

**Gaps:**
- No validation that the produced report is well-formed before write. The
  Roadmap calls this out: "proposer validates that proposed CHANGES.md is
  well-formed before write".
- `datetime.utcnow()` at line 42.

### 2.6 `pipeline/applier/file_updater.py` (330 LOC) - primary audit subject

**Entries:**
- `preview_change(change, references_dir, config)` at line 179 (dry run)
- `execute_change(change, references_dir, config)` at line 192 (apply with
  guard rails)

Both delegate to `_process_change(change, references_dir, config, dry_run)`
at line 207.

**LLM call:** Opus 4 (`claude-opus-4-20250514` per `config.yaml:15`),
one call per affected file via
`pipeline/applier/file_updater.py:305-311`. System prompt has 10 rules
(lines 53-68) including "preserve the existing file structure" and
"preserve the CC BY-SA 4.0 footer line exactly as it is" - exactly the
rules the April-May incident showed cannot be enforced by prompt alone.

**Prompt strategy:** Free-form markdown expected. Response is checked for
the literal string `"NO_CHANGE_NEEDED"` (line 315) and otherwise
regex-fence-stripped (lines 319-324).

**Failure modes:**
- `anthropic.APIError`: logged, returns `None` (lines 328-330). The
  affected file is then marked `"no_change"` at line 231 - **a silent
  failure-mode collision**: legitimate "no change needed" and "API
  failed" produce the same downstream state. Worth fixing.
- `RunAbortError` from `apply_with_guard_rails`: caught at line 258,
  result is marked `"run_aborted"`, exception is re-raised (line 263)
  so the run_apply caller does not commit anything.
- Reference file missing at the expected path: logged warning, skipped
  (lines 220-222).

**Guard rails:** see section 6.

**Gaps:**
- **No tool-use structured output.** Returning the complete file content
  in a `content` block is the exact LLM behaviour the truncation incident
  exploited. A tool-use response with a typed "ranges to replace" or
  "diff hunks" schema would make truncation impossible by construction,
  not by post-hoc validation.
- Silent collision between "no change needed" and "API failed" (above).
- Backup files accumulate indefinitely under `.backups/`. As of
  2026-05-11 there are 20+ bak files surviving from the April-May
  incident runs. No retention policy.

### 2.7 `pipeline/alerter/email_sender.py` (184 LOC)

**Entry:** `send_alert_email(classified_changes, full_report, config)` at
line 21.

**Behaviour:** Tries SMTP if `FINOPS_SMTP_PASS` is set in the environment
(line 30); otherwise builds the subject and logs an informational message
indicating Gmail MCP mode is expected (lines 34-39). No actual sending
in CLI mode unless SMTP is configured.

**Inputs (env vars when SMTP path):** `FINOPS_SMTP_HOST`, `FINOPS_SMTP_PORT`,
`FINOPS_SMTP_USER`, `FINOPS_SMTP_PASS`, `FINOPS_EMAIL_TO`,
`FINOPS_EMAIL_FROM` (lines 143-150).

**Outputs:** SMTP message (line 173) with both plain-text (the full
report) and HTML (the table built by `build_email_body`) parts.

**Failure modes:**
- Missing env vars: logged error, returns silently (lines 153-160).
- SMTP errors: not caught here - propagate to `run_scan.py:347` which
  catches generic `Exception` and continues the run.

**Gaps:**
- `datetime.utcnow()` at line 44.
- No SMTP-side validation that the message was actually delivered (SMTP
  `sendmail` returns successfully if accepted by the server, not on
  delivery).

### 2.8 `pipeline/alerter/github_issue.py` (217 LOC)

**Entry:** `create_github_issue(classified_changes, full_report, config)`
at line 18.

**Behaviour:** Reads `state/CHANGES.md` (line 35), skips if no `### `
headings present (line 38), resolves the target repo from
`config.github.repo` or via `gh repo view` (lines 121-143), ensures the
`content-update` label exists (lines 146-165), checks for an existing
open issue with the same title (lines 93-118), and otherwise creates a
new issue with the body transformed into checkboxes (lines 168-206).

**Subprocess shell-outs:**
- `gh issue create --title --body --label content-update --repo <repo>`
  (lines 65-76)
- `gh issue list --label content-update --state open --json title,url --repo <repo>`
  (lines 98-109)
- `gh label create content-update ...` (lines 149-159)
- `gh repo view --json nameWithOwner -q .nameWithOwner` (lines 128-139)

**Failure modes:**
- `gh` not installed: logged error, returns `None` (lines 77-79, 115).
- `gh` command timeout (30s for create, 10s for list/repo): logged,
  returns `None`.
- Non-zero return code from `gh issue create`: logged error, returns
  `None` (lines 84-86).

**Gaps:**
- No retry on transient `gh` failures (e.g. rate limits).
- Title collision check (`_find_existing_issue`) compares exact strings;
  any title format drift between runs would create duplicate issues.

### 2.9 `pipeline/git_utils.py` (179 LOC)

**Entries:** `get_current_branch()`, `branch_exists()`,
`create_and_checkout_branch()`, `has_uncommitted_changes()`,
`commit_changes()`, `push_branch()`, `create_pr()`.

**Behaviour:** Thin shell-out helpers around `git` and `gh`. All run from
`REPO_ROOT = Path(__file__).parent.parent` (line 13) which assumes the
pipeline lives at a specific depth relative to the repo root.

**Failure modes:**
- Every helper returns `False` / `None` on git or gh failure
  (lines 28-30, 44-45, 72-74, 88-89, etc.). No exception propagation.
  Silent error-suppression style.
- `create_and_checkout_branch` (line 48) silently reuses an existing
  branch with the same name (lines 54-55). Could clobber an unrelated
  in-progress branch if names collide.
- `commit_changes` (line 92) early-returns success when there is
  nothing to commit (line 99). Means a failed "apply" that produced
  no changes silently succeeds at commit, which then pushes an empty
  branch.

**Gaps:**
- `REPO_ROOT` is brittle: any restructure of the pipeline directory
  breaks all git operations.
- No co-author trailer in commit messages (CLAUDE.md says to include
  one when assisting Claude). Not load-bearing - just a convention drift.

---

## 3. LLM call inventory

| File:Line | Model | Prompt construction | Response parsing | Validation |
|---|---|---|---|---|
| `pipeline/scanner/classifier.py:199-205` | `claude-sonnet-4-20250514` | Free-form; SYSTEM_PROMPT + ephemeral-cached reference-files block + per-item user prompt with required JSON schema spelled out | Markdown fence strip (regex), `json.loads()` | None - `is_relevant` defaulted to False, missing fields fall through to defaults |
| `pipeline/applier/file_updater.py:305-311` | `claude-opus-4-20250514` | Free-form; 10-rule SYSTEM_PROMPT + user prompt with the current file in a code fence, expected response: complete updated file or "NO_CHANGE_NEEDED" | Literal-string check for "NO_CHANGE_NEEDED"; otherwise markdown fence strip (regex) | Hard guards `validate_post_apply` (lines 75-116) - see section 6 |

Both calls are free-form markdown round-trips with regex parsing. Neither
uses the Anthropic tool-use / structured output pattern. The classifier
silently drops items on parse error or API error; the applier silently
collapses both "no change needed" and "API failed" into the same
downstream state.

**Migration path to tool use:**

For the classifier, define a tool whose input schema is the JSON shape at
`pipeline/scanner/classifier.py:174-182` (is_relevant, relevance_reason,
change_type as enum, affected_files, summary, suggested_action). The
classifier then calls `tool_choice={"type": "tool", "name": "classify"}`
and reads `response.content[0].input` directly. Removes regex
fence-stripping and `JSONDecodeError` handling.

For the applier, the structured output would be a list of typed edit
operations rather than a complete file dump. Concrete shape options:

- `{"hunks": [{"before": str, "after": str, "rationale": str}]}` - each
  hunk is a small unique-context replacement. Truncation is impossible
  because nothing instructs the model to return the whole file.
- `{"sections_to_replace": [{"heading_path": ["##", "###"], "new_body": str}]}` -
  more structured, requires heading-stable files.
- `{"updated_content": str, "preserved_invariants": ["footer_intact", "no_double_hr"]}` -
  smaller delta from the current shape: still asks for the whole file,
  but the model explicitly asserts the invariants alongside, which moves
  the failure to a typed contract rather than a regex match.

Concrete recommendation: hunks first. It makes the truncation failure
mode structurally impossible.

---

## 4. Destructive actions inventory

Every place the pipeline writes, deletes, or mutates state outside its own
working directory.

| Action | Location | Guarded? | Notes |
|---|---|---|---|
| Write to `skills/cloud-finops/references/<filename>.md` | `pipeline/applier/file_updater.py:154` | **Yes** (snapshot+validate+rollback, run-level fail-safe) | Only public-tree write |
| Restore from snapshot on guard failure | `pipeline/applier/file_updater.py:162` | N/A (the recovery itself) | Read from backup, write to source |
| Copy reference file to `.backups/<filename>.<iso>.bak` | `pipeline/applier/file_updater.py:151` | Always - precedes every write | No retention policy |
| Write `state/last-run.json` | `pipeline/run_scan.py:84`, `pipeline/run_scan.py:289`, `pipeline/run_scan.py:335`, `pipeline/run_scan.py:357` | No locking | Concurrent runs would corrupt |
| Write `state/pending-changes.json` | `pipeline/run_scan.py:190`, `pipeline/run_apply.py.FROZEN:56` | No locking | Same concurrency caveat |
| Write `state/CHANGES.md` | `pipeline/proposer/reporter.py:112` | No validation | Overwritten every scan |
| Write `state/history/scan-<timestamp>.md` | `pipeline/run_scan.py:320` | Immutable by convention | Append-only effectively |
| `git checkout -b <branch>` | `pipeline/git_utils.py:58` (via `pipeline/run_apply.py.FROZEN:203`) | Existing-branch reuse silent | Could clobber feature branch |
| `git add <paths>` | `pipeline/git_utils.py:103` (via `pipeline/run_apply.py.FROZEN:216`) | No `--no-verify` | Hook bypass not possible by code |
| `git commit -m <msg>` | `pipeline/git_utils.py:118` | No co-author trailer | Convention drift |
| `git push -u origin <branch>` | `pipeline/git_utils.py:137` (via `pipeline/run_apply.py.FROZEN:221`) | No `--force` ever | Safe |
| `gh pr create --title --body --base main` | `pipeline/git_utils.py:158-164` (via `pipeline/run_apply.py.FROZEN:230`) | No PR existence check | Could create duplicate PR |
| `gh issue create --title --body --label content-update --repo <repo>` | `pipeline/alerter/github_issue.py:65-76` | Title-collision check via `_find_existing_issue` (line 93) | Title drift would defeat dedup |
| `gh issue list ...` | `pipeline/alerter/github_issue.py:98-109` | Read-only | Safe |
| `gh label create content-update ...` | `pipeline/alerter/github_issue.py:149-159` | "already exists" detection (line 160) | Safe |
| `gh repo view ...` | `pipeline/alerter/github_issue.py:128-139` | Read-only | Safe |
| SMTP `sendmail` | `pipeline/alerter/email_sender.py:173` | Requires explicit env vars | Off by default |

**Conclusion:** the public content tree has exactly one writer
(`applier/file_updater.py:154`), and that writer is guard-railed. The
guard-rail discipline is **necessary and sufficient** for the public
content tree as long as no other module starts writing there. Any future
module that writes to `skills/cloud-finops/references/` or
`skills/cloud-finops/playbooks/` must inherit the same snapshot+validate+rollback
contract.

---

## 5. State directory shape

`pipeline/state/` (gitignored):

```
state/
  CHANGES.md                          - latest scan report (rewritten each run)
  last-run.json                       - last-run timestamp, processed_urls (cap 500), source_last_checked dict, stats counters, current_issue_url
  last-run.backup-before-rescan.json  - artefact from a previous rescan operation
  pending-changes.json                - change queue with status field
  pending-changes.backup-before-rescan.json
  scan.log                            - stdout/stderr from scheduled runs
  history/
    scan-<YYYYMMDD-HHMMSS>.md         - one report per scan, immutable
    applied-archive-20260501-115208.json - May 1 incident archive (format undocumented)
```

**Gaps:**
- No structured per-run report. The only run-level artefact is
  `history/scan-<timestamp>.md`. There is no JSON record of "this run
  fetched X items, classified Y, attempted Z applies, A succeeded, B
  rejected by guard, C aborted". Post-hoc audit requires reading
  `scan.log`.
- `applied-archive-*.json` format is referenced but not documented. The
  May 1 file is 505 lines. Schema inference is required to use it.

`skills/cloud-finops/references/.backups/` (gitignored, but live on disk):

20+ `.bak` files surviving from the April-May 2026 runs. Pattern:
`<reference-file>.<YYYYMMDD-HHMMSS>.bak`. No retention policy in code.

---

## 6. Guard rails verification

The applier has three hard guards plus a run-level fail-safe. Each guard
quoted in full from `pipeline/applier/file_updater.py`.

**Guard 1 - deletion threshold** (lines 89-98):

```python
if original_lines > TRUNCATION_MIN_LINES:  # 100 lines
    net_change_ratio = (original_lines - updated_lines) / original_lines
    if net_change_ratio > TRUNCATION_RATIO_THRESHOLD:  # 20%
        return False, (
            f"Truncation detected: file shrank by {net_change_ratio:.1%} ..."
        )
```

A file of 100+ lines that shrinks by more than 20% net is rejected. Small
files (<100 lines) bypass the check (justified: tactical edits to short
files are legitimate). The 1 May 2026 incident reduced files by 60-80% -
well above the 20% threshold.

**Guard 2 - footer presence** (lines 100-107):

```python
tail = updated[-FOOTER_TAIL_CHARS:] if len(updated) > FOOTER_TAIL_CHARS else updated
if "OptimNow" not in tail or "CC BY-SA" not in tail:
    return False, "Footer missing: the OptimNow CC BY-SA 4.0 footer is not present ..."
```

The last 300 characters must contain both "OptimNow" and "CC BY-SA". This
catches the April 2026 `itam.md` case where the file ended mid-sentence
with no footer at all.

**Guard 3 - double horizontal-rule artefact** (lines 109-114):

```python
if "---\n\n---" in updated[-DOUBLE_HR_TAIL_CHARS:]:  # last 500 chars
    return False, "Double horizontal-rule artefact detected near end of file ..."
```

Catches the seven April 2026 files where a Sources block was removed but
both `---` separators were left behind. Tight window (last 500 chars) to
avoid false positives on intentional `---\n\n---` sequences mid-file.

**Snapshot + rollback** (`apply_with_guard_rails`, lines 119-172):

The flow is: pre-check failures counter (lines 139-143), snapshot to
`.backups/` (lines 146-151), write proposed content (lines 153-155),
validate post-apply (line 158), and on failure restore from snapshot
(line 162), increment failures, possibly raise `RunAbortError` (lines
163-169).

**Run-level fail-safe** (`MAX_RUN_FAILURES = 2` at line 38):

After two file-level rollbacks, the next attempt raises `RunAbortError`
(line 165). The exception propagates through `_process_change`
(line 263), preventing any commit. The fail-safe also runs pre-emptively
at the next call (line 139), so an aborted run cannot be retried mid-flight.

**Test coverage** (`pipeline/tests/test_file_updater_guards.py`, 9 tests):

- `TestValidatePostApply::test_accepts_a_clean_apply` - +5 lines with
  footer intact passes
- `TestValidatePostApply::test_rejects_truncation_above_threshold` -
  200 -> 50 lines without footer fails
- `TestValidatePostApply::test_rejects_missing_footer_even_at_same_size` -
  200 lines, no footer block, fails (the April `itam.md` case)
- `TestValidatePostApply::test_rejects_double_horizontal_rule_artefact` -
  footer present but `---\n\n---` near end, fails
- `TestValidatePostApply::test_skips_truncation_check_on_small_files` -
  80 -> 50 lines on a sub-100-line file passes
- `TestApplyWithGuardRails::test_clean_apply_writes_and_returns_applied` -
  clean apply writes file and returns `applied=True`, backup exists
- `TestApplyWithGuardRails::test_truncated_apply_is_rolled_back_from_snapshot` -
  truncation triggers rollback, file restored, `failures=1`
- `TestApplyWithGuardRails::test_run_aborts_after_too_many_failures` -
  exactly `MAX_RUN_FAILURES` rollbacks allowed, next raises
  `RunAbortError`, file restored even on abort
- `TestApplyWithGuardRails::test_snapshot_is_created_in_backups_subdir` -
  backup path is under `.backups/`, ends with `.bak`, starts with the
  reference filename

All 9 pass on Python 3.12 (verified during this audit).

**Gap:** every guard depends on the LLM having returned *something*. If the
LLM API call itself fails (network error, 5xx), the file is left untouched
and the rollback path is never invoked. That is correct behaviour but not
explicitly tested - the test suite uses synthesised "proposed_content"
strings, not real API calls.

---

## 7. Implicit assumptions discovered

Things the code assumes without checking. Each is a candidate for
hardening, ordered by impact.

1. **HTTP 200 implies non-empty, HTML-shaped body**
   (`pipeline/scanner/fetcher.py:121-129`). A 200 response with a CDN
   error page, a JSON body, or an empty document is parsed by
   BeautifulSoup and produces a `FetchedItem` with potentially empty
   content. The classifier then has nothing real to classify.

2. **Feed parse errors silently produce empty entries lists**
   (`pipeline/scanner/fetcher.py:73`). A broken RSS feed logs no error -
   it just returns zero items. The scan log shows
   `"  <source>: 0 fetched, 0 new"` which is identical to
   "this source has no news".

3. **Undated feed entries pass the lookback filter**
   (`pipeline/scanner/fetcher.py:83`). The cutoff filter only runs when
   `published is not None`. An undated entry is admitted regardless of
   age.

4. **`processed_urls` cap is unordered**
   (`pipeline/run_scan.py:325-330`). `list(set(...))[-500:]` does not
   preserve oldest-first order; sets are unordered in Python. The cap
   evicts arbitrary URLs rather than the oldest.

5. **`pending-changes.json` schema is untyped**
   (`pipeline/run_scan.py:158-173`, `pipeline/run_apply.py.FROZEN:46-51`).
   Dict-based; no schema validation on read. A corrupted file would
   raise `KeyError` at field access, mid-flow.

6. **`applied-archive-*.json` format is undocumented**
   (`pipeline/state/history/applied-archive-20260501-115208.json`).
   Referenced but not defined anywhere in code.

7. **`last-run.json` read-modify-write has no locking**
   (`pipeline/run_scan.py:60-84`, `pipeline/run_apply.py.FROZEN:46-57`).
   Concurrent runs (e.g. a manual `python pipeline/run_scan.py` while
   the scheduled task is running) would corrupt the file.

8. **`REPO_ROOT` is parent-of-parent of `git_utils.py`**
   (`pipeline/git_utils.py:13`). Hard-coded relative path. Breaks if the
   pipeline directory is restructured.

9. **Branch reuse in `_create_content_pr` is silent**
   (`pipeline/run_apply.py.FROZEN:202-208`). If the user is on a feature
   branch when running `--execute --pr`, content commits land on that
   branch.

10. **Reference files have no unstaged changes at apply time** - not
    checked. The applier overwrites
    `skills/cloud-finops/references/<filename>` without first verifying that
    the working tree is clean for that file. A user mid-edit could lose
    work.

11. **`datetime.utcnow()` is fine** - deprecated in 3.12, removed in a
    future Python. Pervasive: `run_scan.py:142, 280, 287, 324`,
    `run_apply.py.FROZEN:196`, `fetcher.py:74, 141`, `reporter.py:42`,
    `email_sender.py:44`, `github_issue.py:54`, plus test files.

---

## 8. Gap analysis vs Roadmap Phase 2 (Harden) goals

The Roadmap (`CLAUDE.md` > Roadmap > In-flight > P1) names specific
Phase-2 targets. Each is mapped to current code state with a confidence
score.

| Roadmap Phase-2 target | Status | Evidence |
|---|---|---|
| Scanner validates HTTP status | **Done** | `pipeline/scanner/fetcher.py:121` calls `resp.raise_for_status()` |
| Scanner validates content-type | **Not started** | No content-type check after the 200 |
| Scanner validates minimum payload length | **Not started** | No body-length check; empty 200 produces empty `FetchedItem` |
| Proposer validates CHANGES.md well-formedness before write | **Not started** | `pipeline/proposer/reporter.py:112` writes unconditionally |
| Applier uses structured output (tool use) instead of regex-parsed markdown | **Not started** | `pipeline/applier/file_updater.py:305-311` is free-form markdown; same in classifier |
| Per-run structured report under `state/runs/<timestamp>/` | **Not started** | Only `state/history/scan-<timestamp>.md` exists; no JSON run report |
| Idempotency (re-running produces zero diff) | **Partial** | `pending-changes.json` merge logic is sound (lines 87-199, "Correctif A"); `processed_urls` cap unordered (gap #4 above) |
| Replay-from-state for partial failure | **Not started** | No replay flag on `run_apply.py.FROZEN` |
| Secrets handling ratchets (no API keys in commit messages, no .env in stdout) | **Mostly done** | `.env` gitignored at repo root; gitleaks pre-commit hook visible from prior commit output. Not explicitly enforced in pipeline code |
| Snapshot + apply + validate + rollback contract | **Done** | `apply_with_guard_rails` lines 119-172 + run-level fail-safe |
| Run-level fail-safe at 2+ failures | **Done** | `MAX_RUN_FAILURES = 2` line 38, enforced lines 139-143 and 164-169 |
| Tests cover guard rails | **Done** | 9 tests in `pipeline/tests/test_file_updater_guards.py`; full suite 43 tests, all green |

**Net Phase-2 picture:** Applier discipline is solid. The rest of the
pipeline still depends on prompt instructions and implicit guarantees. The
six "Not started" items above are the actionable scope of the Harden PR.

---

## 9. Recommended remediation order

Sequenced by risk x value. Each item tagged "blocks unfreeze" or
"nice-to-have". The Harden PR should land items 1-5 at minimum.

1. **[blocks unfreeze] Applier structured output (tool use).**
   Replace the free-form markdown round-trip at
   `pipeline/applier/file_updater.py:305-311` with a tool-use call that
   returns a typed list of edit hunks (proposed schema in section 3).
   Eliminates the truncation failure mode by construction rather than by
   post-hoc validation. Highest-value single change.

2. **[blocks unfreeze] Per-run structured report.**
   Every run writes `pipeline/state/runs/<timestamp>/report.json` with:
   `items_fetched`, `items_classified`, `files_attempted`,
   `files_applied`, `files_rejected_by_guard`, `files_run_aborted`, plus
   per-file outcomes. Replaces stdout-scrolling as the audit primitive.

3. **[blocks unfreeze] Fetcher content validation.**
   After `raise_for_status()`, check (a) content-type contains `text/html`
   or `application/rss+xml` (matching the requested source type), and
   (b) body length is above a minimum threshold (e.g. 200 chars). On
   either failure, log an explicit "fetcher rejected this source" record
   and return `[]`. Distinguishes "no news" from "broken source".

4. **[blocks unfreeze] Classifier structured output (tool use).**
   Same migration as the applier, but lower-risk (the failure mode is a
   dropped item, not a truncated file). Returns a tool-input dict
   instead of free-form JSON in markdown fences.

5. **[blocks unfreeze] Proposer well-formedness validation.**
   After building the CHANGES.md string, parse it back with a markdown
   parser (or a simple regex over the expected `### N. Title` pattern)
   and verify counts match `classified_changes`. Abort the run if
   mismatched.

6. **[nice-to-have] Backup retention policy.**
   In `apply_with_guard_rails`, after a successful apply, prune
   `.backups/<filename>.*.bak` files older than the most recent N (e.g.
   N=10). Keeps the recovery surface usable indefinitely without unbounded
   disk growth.

7. **[nice-to-have] Pre-flight git cleanliness check in `run_apply`.**
   Before any apply, verify `git status --porcelain skills/cloud-finops/references/`
   is empty. If not, refuse to apply (the user has in-flight edits that
   could be clobbered).

8. **[nice-to-have] `datetime.utcnow()` migration.**
   Replace every `datetime.utcnow()` with `datetime.now(timezone.utc)`
   to remove the 24 deprecation warnings. Required for Python 3.13+
   compatibility.

9. **[nice-to-have] Branch reuse safety.**
   `_create_content_pr` (`pipeline/run_apply.py.FROZEN:202-208`) should
   refuse to reuse a feature branch by default. Add an explicit
   `--reuse-current-branch` flag for the rare case where it is intended.

Items 1-5 are the Harden PR scope. Items 6-9 can land in the Stabilise
PR or a separate cleanup PR depending on bandwidth.

---

## 10. Unfreeze criteria proposal

Concrete, measurable criteria for `mv pipeline/run_apply.py.FROZEN
pipeline/run_apply.py`. Builds on the Roadmap's four criteria with four
additions.

Pre-existing (Roadmap):

- **U1.** 5 consecutive dry runs against the historical change archive
  produce zero false-positive guard-rail rejections AND zero silent
  truncations.
- **U2.** A fresh real run on a synthetic forked references directory
  completes end-to-end without manual intervention.
- **U3.** The run-level fail-safe correctly aborts a run that injects
  3+ truncations across 3 different files.
- **U4.** All `pipeline/tests/` unit tests pass on Python
  3.10/3.11/3.12.

Audit additions:

- **U5.** Per-run structured report
  (`pipeline/state/runs/<timestamp>/report.json`) is written by every
  scan and every apply, and its schema is documented in
  `pipeline/state/README.md`.
- **U6.** Applier structured output (tool use) migration complete:
  `pipeline/applier/file_updater.py:305-311` returns a tool-input dict
  rather than a free-form markdown string. The truncation tests in
  `test_file_updater_guards.py` are augmented with at least one test
  that asserts the tool-output shape.
- **U7.** Backup retention policy in place: after a successful apply,
  `.backups/<filename>.*.bak` is pruned to the most recent N.
- **U8.** Pre-flight clean-tree check refuses to apply when
  `skills/cloud-finops/references/` has unstaged changes.

The unfreeze decision is recorded in the `Lessons learned` section of
`CLAUDE.md` with citations to the PRs that landed U5-U8 and the test
evidence for U1-U4.

---

## 11. Out of scope

The audit deliberately does not cover:

- **Public-release decision** (Roadmap Phase 4). Strategic - the user
  owns it. The choice is "same repo public `pipeline/` directory" vs
  "separate `cloud-finops-skills-pipeline` repo" vs "stay private". This
  audit is informational only.
- **Prompt-quality evaluation.** Whether the classifier correctly
  distinguishes PRICING_CHANGE from NEW_SKU, whether the applier
  produces idiomatic British-spelling content, etc. Requires a labelled
  eval set, separate work stream.
- **`sources.yaml` accuracy audit.** Whether the 30 sources are still
  live, whether their RSS feeds still publish, whether new sources should
  be added or stale ones retired. The audit notes only that the source
  count is 30, not 29 as the README and Roadmap currently claim.
- **MCP server (`pipeline/mcp_server/`).** The directory exists but is
  empty (`pipeline/mcp_server/__init__.py` is the only file). Whatever
  MCP integration is planned belongs in a separate design document.
- **Live runs against production sources.** This audit reads code and
  inspects state; it does not run the pipeline.
- **Other writers to public content tree.** Verified during audit that
  only `pipeline/applier/file_updater.py:154` writes to
  `skills/cloud-finops/references/`. No `skills/cloud-finops/playbooks/` writers
  exist either. If a future module is added that writes to either
  tree, it must re-trigger this audit's destructive-actions inventory.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
