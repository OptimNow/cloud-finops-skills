# Pipeline Harden plan: Phase 2 of Roadmap P1

> Companion to [`docs/pipeline-audit-2026-05.md`](pipeline-audit-2026-05.md). The
> audit answers **what** needs fixing; this plan answers **how** to fix it. Both
> documents land before any pipeline code changes. Phase 3 (Stabilise) and
> Phase 4 (Publish) remain tracked separately in [CLAUDE.md](../CLAUDE.md).

**Plan date:** 2026-05-11
**Author:** Claude (Opus 4.7, agent-assisted), reviewed by Jean
**Status:** Items 1 (applier tool-use) **rolled back**; items 2-5 partially
landed; new items added on 2026-05-15. See the Status update box below.

---

## Status update (2026-05-15): tool-use rolled back, max_tokens was the real fix

The first production run of the Harden code on 15 May 2026 surfaced
material issues with this plan. See
[`docs/pipeline-audit-2026-05.md`](pipeline-audit-2026-05.md) "Correction
(2026-05-15)" section for the full forensic.

Summary:
- **Item 1 (applier tool-use migration): ROLLED BACK.** Opus regressed to
  legacy XML format under `tool_choice` and emitted XML inside the JSON
  `hunks` field. 1200+ malformed-hunk warnings per file. Free-form rewrite
  is the production path again. Forensic at
  `pipeline/applier/file_updater.py.harden-a-tool-use-attempt.bak`.
- **The actual fix for the May 2026 truncation incidents:**
  `pipeline/config.yaml` `max_tokens: 4096` -> `16384`. The audit
  misidentified the root cause; this plan inherited that error.
- **Item 2 (per-run structured report): LANDED.** Working.
- **Item 3 (fetcher content-type/min-payload/bozo validation): LANDED.**
  Caught 5 dead sources on the first run (databricks, snowflake, infracost,
  azure-updates, azure-openai-pricing); sources.yaml was fixed.
- **Item 4 (classifier tool-use migration): LANDED, but suspect.** Same
  Opus-emits-XML risk exists; the classifier-side hasn't yet shown the
  failure in production but should be considered fragile until proven.
- **Item 5 (proposer well-formedness validation): LANDED.** Working.
- **Plus dropped-URL tracking** (`classify_items` returns
  `(classified, dropped_urls)`; URLs that hit API errors are NOT marked
  as processed, so they retry next scan).
- **Plus preview-mode guard rails** (`_validate_content` called from
  `_process_change` before showing a diff). Closes the gap that allowed
  a 90%-deletion proposal to display to the user without warning.
- **Plus `pipeline/smoke_test.py`**, a real-API smoke test to run before
  any production batch. The 79 passing mock-based tests were
  self-confirming and gave false production-readiness signal in May 2026.

The text below is the original plan, preserved for the record. Read it
knowing that Item 1 did not work in production and that the actual
production fix was a one-line config change.

---

## 0. Context

The audit identified 5 items that block the unfreeze of `run_apply.py.FROZEN`.
This plan takes each item and lays out the schema decisions, file changes,
test additions, prompts to revise, and rollback story. Once this plan is
approved, the Harden work can begin as one or two PRs (sequencing
recommendation in section 1).

The 5 blocking items, in the order they should be implemented (from the
audit's risk x value scoring):

1. Applier structured output via tool use (biggest semantic shift)
2. Per-run structured report
3. Fetcher content validation
4. Classifier structured output via tool use
5. Proposer well-formedness validation

This plan covers all five. Items 6-9 from the audit (nice-to-haves: backup
retention, pre-flight clean-tree check, `datetime.utcnow()` migration,
branch reuse safety) are scoped to the Stabilise PR or a cleanup PR -
they do not block unfreeze and are not covered in depth here.

---

## 1. Sequencing recommendation

Two viable shapes for the Harden work:

### Option A: single Harden PR (all 5 items)

Pros: one merge, one review, one deploy-and-test cycle. Matches the
audit's framing of "Items 1-5 are the Harden PR scope".

Cons: large diff, hard to bisect if one item destabilises the run. Item
1 (applier tool-use migration) is qualitatively different from items
2-5 (additive validation), so coupling them risks the bigger change
delaying the smaller ones.

### Option B: two staged Harden PRs (Recommended)

- **Harden PR A: applier tool-use migration** (item 1 only). Self-contained, ~300-400 LOC change concentrated in `pipeline/applier/file_updater.py` and `pipeline/tests/test_file_updater_guards.py`. Highest semantic shift in the work. Reviewable in isolation.
- **Harden PR B: validation pass** (items 2-5). Per-run structured report + fetcher content validation + classifier tool-use + proposer well-formedness. Each is additive; together they form a coherent "validation discipline" theme. ~200-300 LOC across multiple modules.

Why staged: item 1 is where the truncation failure mode lives. Landing it
first means the structural fix is in place before any further pipeline
work; if items 2-5 surface unexpected issues, the structural fix is not
held hostage. Items 2-5 share the "add a validator that does not exist
yet" pattern - lower risk individually, sensibly grouped.

**Recommendation: Option B.** Two PRs.

---

## 2. Item 1: Applier structured output via tool use

This is the largest design call in the plan because the chosen schema
locks the prompt, the parser, the validators, and the tests.

### 2.1 Schema decision

Three candidates were named in the audit. Detailed evaluation:

| Schema | Truncation-proof? | Prompt complexity | Failure modes | Recommendation |
|---|---|---|---|---|
| **Hunks**: `{"hunks": [{"before": str, "after": str, "rationale": str}]}` | Yes - the model never returns the whole file | Low - "identify unique anchor + replacement" | `before` not unique (>1 match) or absent (0 matches) - both detectable in Python | **Pick this** |
| **Sections**: `{"sections_to_replace": [{"heading_path": ["##", "###"], "new_body": str}]}` | Yes - new_body scoped to one section | Medium - requires the model to reason about heading hierarchy | Heading path drift; sections crossing heading boundaries | Pass - too brittle for non-uniform files |
| **Complete-with-invariants**: `{"updated_content": str, "preserved_invariants": ["footer_intact", "no_double_hr"]}` | No - still asks for the whole file | Low | Same as today, just typed | Pass - does not actually solve the truncation failure mode |

**Chosen schema: hunks.**

```json
{
  "name": "update_reference_file",
  "description": "Apply one or more targeted text replacements to a FinOps reference file. Return an empty hunks array if no change is warranted.",
  "input_schema": {
    "type": "object",
    "properties": {
      "rationale": {
        "type": "string",
        "description": "One-sentence explanation of why this file is (or is not) being updated."
      },
      "hunks": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "before": {
              "type": "string",
              "description": "The exact text to replace. MUST occur exactly once in the current file content. Include enough surrounding context to make the match unique."
            },
            "after": {
              "type": "string",
              "description": "The replacement text. Must follow the same style rules as the file: British spelling, straight dashes, no em dashes, preserve HTML comment tracking IDs."
            },
            "rationale": {
              "type": "string",
              "description": "One sentence explaining why this specific hunk."
            }
          },
          "required": ["before", "after", "rationale"]
        }
      }
    },
    "required": ["rationale", "hunks"]
  }
}
```

An empty `hunks` array replaces today's `"NO_CHANGE_NEEDED"` literal-string
sentinel.

### 2.2 New validation rules

After the tool-use call returns, before writing anything:

1. **Empty hunks** -> `result["status"] = "no_change"`, no file write, no
   snapshot. The `rationale` is logged for audit.
2. **Per-hunk match check**: for each hunk, count occurrences of
   `before` in the current file content.
   - Exactly 1 match: apply the hunk.
   - 0 matches: log warning ("hunk anchor not found"), skip this hunk,
     mark per-hunk status `"anchor_missing"`. Other hunks still apply.
   - 2+ matches: log error ("hunk anchor ambiguous"), skip this hunk,
     mark per-hunk status `"anchor_ambiguous"`. Other hunks still apply.
3. **All-hunks-failed check**: if every hunk in a non-empty array fails
   matching, the whole apply is marked `"rejected_by_anchor"` and rolled
   back. This is structurally a `RunAbortError`-eligible event (it
   suggests the model hallucinated the file content).
4. **Belt-and-suspenders**: `validate_post_apply` (lines 75-116) still
   runs after the hunks are applied. The new schema makes truncation
   structurally improbable, but the deletion-threshold, footer-presence,
   and double-HR guards remain as cheap insurance against pathological
   cases (e.g. every hunk replaces a large chunk with an empty string).

### 2.3 Prompt revision

Current `SYSTEM_PROMPT` (`pipeline/applier/file_updater.py:53-68`) has 10
rules. Migration mapping:

| Current rule | Disposition under hunks |
|---|---|
| 1. Preserve the existing file structure | **Structurally enforced** (hunks cannot delete the whole file) |
| 2. Use straight dashes, never em dashes | **Keep** (per-hunk style rule) |
| 3. Use British spelling | **Keep** |
| 4. Preserve the CC BY-SA 4.0 footer | **Structurally enforced** (hunks cannot touch text outside their `before` anchor) |
| 5. Preserve HTML comment tracking IDs | **Keep** (per-hunk: do not strip comments from the `after` string) |
| 6. Preserve the blockquote header at the top | **Structurally enforced** |
| 7. Update only the specific content | **Structurally enforced** (the entire point of hunks) |
| 8. If pricing, update tables precisely | **Keep** |
| 9. Add a source note where relevant | **Keep** |
| 10. Return COMPLETE updated file, not partial diff | **Remove** (replaced by hunks instruction) |

New system prompt (~12 lines, vs current 16):

```
You are updating a FinOps reference file by proposing one or more targeted
text replacements ("hunks").

Each hunk must specify:
- before: the exact text to replace. It MUST occur exactly once in the file.
  Include enough surrounding context (a sentence or paragraph anchor) to
  make the match unambiguous.
- after: the replacement text, in the same style as the file:
  - British spelling (optimisation, organisation, behaviour)
  - Straight dashes (-), never em dashes
  - Preserve any HTML comment tracking IDs (<!-- ... -->)
  - Preserve pricing-table column structure precisely
  - Add a source note where relevant (e.g. "As of March 2026, ...")
- rationale: one sentence explaining why this hunk.

Return an empty hunks array if no change to this specific file is warranted
by the detected change. Do not invent edits to demonstrate effort.
```

Note: rules 1, 4, 6, 7 from the old prompt disappear because hunks make
them structurally impossible to violate. This is the entire point of the
migration.

### 2.4 Code changes

| File | Change | LOC estimate |
|---|---|---|
| `pipeline/applier/file_updater.py` | Replace `_generate_update` with `_generate_hunks`; add `_apply_hunks`; rewrite `SYSTEM_PROMPT`; keep `validate_post_apply` and `apply_with_guard_rails` unchanged; update `_process_change` to call the new functions | ~120 LOC modified, ~50 LOC new |
| `pipeline/tests/test_file_updater_guards.py` | Existing 9 tests unchanged (they test the guard rails, not the LLM call) | 0 |
| `pipeline/tests/test_file_updater_hunks.py` | NEW. Tests for hunk-matching, anchor-uniqueness, empty hunks, all-hunks-failed | ~150 LOC |

Concrete signatures:

```python
def _generate_hunks(
    client: anthropic.Anthropic,
    current_content: str,
    filename: str,
    change: dict,
    config: dict,
) -> dict | None:
    """Use Claude tool-use to generate a list of replacement hunks.
    Returns the parsed tool input dict, or None on API error.
    Empty hunks array means "no change needed for this file"."""

def _apply_hunks(
    current_content: str,
    hunks: list[dict],
) -> tuple[str, list[dict]]:
    """Apply the hunks to current_content. Returns (updated_content,
    per_hunk_results). per_hunk_results is a list of dicts with
    status in {"applied", "anchor_missing", "anchor_ambiguous"}.
    Does NOT write to disk - that is apply_with_guard_rails' job."""
```

### 2.5 Test additions

New tests in `pipeline/tests/test_file_updater_hunks.py`:

1. `test_single_hunk_applies` - one hunk with unique `before`, content updates correctly
2. `test_multiple_hunks_apply_in_order` - three non-overlapping hunks all apply
3. `test_empty_hunks_array_is_no_change` - `{"hunks": []}` produces no write, status "no_change"
4. `test_hunk_with_missing_anchor_is_skipped` - `before` absent from file, hunk marked "anchor_missing", other hunks still apply
5. `test_hunk_with_ambiguous_anchor_is_skipped` - `before` matches twice, hunk marked "anchor_ambiguous"
6. `test_all_hunks_failed_triggers_rollback` - all hunks fail matching, whole apply rolled back, `RunAbortError` raised
7. `test_overlapping_hunks_are_detected` - two hunks whose anchors overlap each other, second hunk's anchor is no longer findable after first applies. Acceptable as "anchor_missing" on the second.
8. `test_belt_and_suspenders_guards_still_run` - synthesise a hunk that produces a truncated result (`after` is empty for a 200-char `before`), confirm the deletion-threshold guard still fires
9. `test_hunks_preserve_footer_structurally` - run a real-sized synthetic file, apply hunks that touch middle sections, confirm footer is byte-identical

Test 9 is the explicit verification that the new schema makes the
April-May 2026 failure mode structurally impossible.

### 2.6 Migration risks and rollback

**Risk 1: model fails to produce unique anchors.** Mitigation:
log every anchor failure with the hunk content; if anchor-failure rates
exceed a threshold (say 10% across a run), surface in the run report.
The rollback story is the existing guard rails - any bad apply is
restored from snapshot.

**Risk 2: model adopts overly defensive hunks** (e.g. tries to replace
the whole document body). Mitigation: prompt says "Do not invent edits
to demonstrate effort". Plus belt-and-suspenders deletion-threshold
guard catches large-replacement hunks.

**Risk 3: existing test suite asserts the old `_generate_update`
contract.** Mitigation: the test file `test_file_updater_guards.py`
operates against synthesised `proposed_content` strings, not LLM
output. The 9 guard tests do not touch the LLM call path. Verified
during the audit.

**Rollback path**: revert the PR. The old free-form markdown flow is
preserved by git history, no in-flight state needs migration. Backups
under `.backups/` remain valid (they're snapshots of source files, not
intermediate state).

---

## 3. Item 2: Per-run structured report

### 3.1 Schema

Path: `pipeline/state/runs/<YYYYMMDDTHHMMSSZ>/report.json`.

```json
{
  "run_id": "20260511T144530Z",
  "run_type": "scan | apply",
  "started_at": "2026-05-11T14:45:30Z",
  "finished_at": "2026-05-11T14:48:12Z",
  "exit_status": "success | partial | run_aborted | error",
  "git": {
    "repo": "OptimNow/cloud-finops-skills",
    "branch_at_start": "main",
    "head_sha_at_start": "0c9422b...",
    "branch_at_end": "content/11-may-2026",
    "head_sha_at_end": "a1b2c3d..."
  },
  "scan": {
    "sources_checked": 30,
    "sources_failed": 0,
    "items_fetched": 17,
    "items_classified_relevant": 4,
    "items_classified_irrelevant": 13,
    "items_dropped_parse_error": 0,
    "items_dropped_api_error": 0,
    "by_change_type": {"PRICING_CHANGE": 2, "NEW_SKU": 1, "BEST_PRACTICE": 1}
  },
  "apply": {
    "changes_attempted": 2,
    "files_attempted": 3,
    "files_applied": 3,
    "files_rejected_by_guard": 0,
    "files_rejected_by_anchor": 0,
    "files_run_aborted": 0,
    "per_file": [
      {
        "filename": "finops-aws.md",
        "status": "applied",
        "hunks_applied": 2,
        "hunks_anchor_missing": 0,
        "hunks_anchor_ambiguous": 0,
        "backup_path": "skills/cloud-finops/references/.backups/finops-aws.md.2026-05-11T14-46-12.bak"
      }
    ]
  },
  "github": {
    "issue_url": "https://github.com/OptimNow/cloud-finops-skills/issues/N",
    "pr_url": "https://github.com/OptimNow/cloud-finops-skills/pull/M"
  }
}
```

For scan-only runs, the `apply` block is omitted. For apply-only runs,
the `scan` block is omitted.

### 3.2 Code changes

| File | Change | LOC |
|---|---|---|
| `pipeline/run_report.py` | NEW. `RunReport` dataclass + `write_report(run_dir, report)` + `read_report(run_dir)` helpers | ~80 LOC |
| `pipeline/run_scan.py` | Build a `RunReport` incrementally, write at end (success and error paths) | ~30 LOC modified |
| `pipeline/run_apply.py` (when unfrozen) | Same incremental build | ~30 LOC modified |
| `pipeline/tests/test_run_report.py` | NEW. Schema validation, write/read round-trip, scan-only and apply-only shapes | ~80 LOC |

Important: the report is written even on error paths. Use a
try/finally in `main()` so an exception in classification or apply
still produces a report with `exit_status: "error"` and the partial
counters filled in.

### 3.3 Test additions

1. `test_scan_run_writes_complete_report` - happy path, all scan counters populated
2. `test_apply_run_writes_complete_report` - happy path with file-level per_file array
3. `test_aborted_run_writes_partial_report` - inject a `RunAbortError` mid-apply, confirm `exit_status: "run_aborted"` and per-file results up to the abort point are present
4. `test_report_is_written_on_unhandled_exception` - inject a bare `Exception`, confirm the try/finally writes a report with `exit_status: "error"`

### 3.4 Risks

Minimal. Additive change; no existing code reads run reports today.

---

## 4. Item 3: Fetcher content validation

### 4.1 New validators

After `resp.raise_for_status()` at `pipeline/scanner/fetcher.py:121`:

```python
# Content-type validation
content_type = resp.headers.get("Content-Type", "").lower()
expected = {
    "blog": ["text/html"],
    "changelog": ["text/html"],
    "pricing_page": ["text/html"],
}
allowed = expected.get(source["type"], ["text/html"])
if not any(ct in content_type for ct in allowed):
    logger.warning(
        f"  {source['name']}: content-type {content_type!r} not in {allowed}, skipping"
    )
    return []

# Minimum payload length
MIN_BODY_LENGTH = 200  # chars
if len(resp.text) < MIN_BODY_LENGTH:
    logger.warning(
        f"  {source['name']}: body length {len(resp.text)} < {MIN_BODY_LENGTH}, skipping"
    )
    return []
```

For RSS sources: `feedparser` does not surface HTTP-layer content-type
the same way. Validation there is: after parsing, if `feed.entries` is
empty AND `feed.bozo` is True (feedparser's "this feed has issues"
flag), log explicit warning and return [] (distinguishes "no news"
from "broken feed"). Today the code returns [] silently in both cases.

### 4.2 Code changes

| File | Change | LOC |
|---|---|---|
| `pipeline/scanner/fetcher.py` | Add content-type + min-length checks in `_fetch_web_page`; add `feed.bozo` distinction in `_fetch_rss` | ~25 LOC added |
| `pipeline/tests/test_fetcher.py` | Existing 21 tests unchanged; add 4 new tests | ~80 LOC added |

### 4.3 Test additions

1. `test_web_page_rejects_non_html_content_type` - mock `requests.get` to return Content-Type `application/json`, confirm `[]` returned and warning logged
2. `test_web_page_rejects_empty_body` - mock 200 with `<html></html>` (< 200 chars), confirm `[]` returned
3. `test_rss_warns_on_broken_feed` - mock feedparser to return `feed.bozo = True` with empty entries, confirm warning is logged distinct from the "no news" case
4. `test_pricing_page_accepts_text_html_charset` - mock Content-Type `text/html; charset=utf-8`, confirm fetch proceeds (substring match, not exact)

### 4.4 Risks

Risk: false rejection of a legitimate source whose CDN returns
unexpected content-type. Mitigation: the rejection is logged
explicitly with the actual content-type seen, so a quick human
inspection during the first few runs catches false positives. The
allowed-types list lives in code, easy to widen.

---

## 5. Item 4: Classifier structured output via tool use

Same migration pattern as item 1, smaller surface, lower risk.

### 5.1 Schema

Take the JSON shape from `pipeline/scanner/classifier.py:174-182` and
lift it directly into a tool-use input schema:

```python
{
    "name": "classify_finops_news",
    "description": "Classify a fetched cloud / FinOps news item against the reference files.",
    "input_schema": {
        "type": "object",
        "properties": {
            "is_relevant": {"type": "boolean"},
            "relevance_reason": {"type": "string"},
            "change_type": {
                "type": "string",
                "enum": [
                    "PRICING_CHANGE", "DEPRECATION", "NEW_SKU",
                    "CAPACITY_CHANGE", "NEW_FEATURE", "BEST_PRACTICE",
                    "GENERAL_NEWS"
                ]
            },
            "affected_files": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
            "suggested_action": {"type": "string"}
        },
        "required": [
            "is_relevant", "relevance_reason", "change_type",
            "affected_files", "summary", "suggested_action"
        ]
    }
}
```

The enum on `change_type` is a free correctness win - today the
classifier can return any string and downstream code falls through to
GENERAL_NEWS silently.

### 5.2 Code changes

| File | Change | LOC |
|---|---|---|
| `pipeline/scanner/classifier.py` | Replace the regex fence-strip + `json.loads` flow with a `tool_choice={"type": "tool", "name": "classify_finops_news"}` call; read `response.content[0].input` | ~30 LOC modified |
| `pipeline/tests/test_classifier.py` | Existing 6 tests adjusted: mock responses now use the tool-use response shape instead of free-form JSON in a TextBlock | ~50 LOC modified |

### 5.3 Test additions

1. `test_classifier_uses_tool_use` - verify the API call includes `tool_choice` and `tools`
2. `test_classifier_handles_missing_tool_use_response` - if the model returns text instead of a tool_use block (model misbehaviour), log error and skip the item (same outcome as today's JSONDecodeError path)
3. `test_classifier_enum_rejects_unknown_change_type` - prompted with a junk content, confirm the API enforces the enum

### 5.4 Risks

Same shape as item 1 but smaller. Worst case (every item drops because
tool-use isn't returned) is a degenerate scan that finds zero changes
- same outcome as a network outage. No risk to the public content
tree.

---

## 6. Item 5: Proposer well-formedness validation

### 6.1 Validation rules

After `generate_changes_report` builds the markdown string, before the
write at `pipeline/proposer/reporter.py:112`:

1. **Heading count match**: count `### \d+\. ` headings; must equal
   `len(classified_changes)`.
2. **Section presence**: for every `change_type` represented in
   `classified_changes`, the corresponding `## [P*] <Type>` heading
   must appear in the output.
3. **Approval footer intact**: the substring
   `"python pipeline/run_apply.py --execute"` must appear in the
   non-empty case.
4. **Metadata block**: the four lines `**Scan date:**`,
   `**Sources checked:**`, `**Items fetched:**`,
   `**Relevant changes found:**` must all be present.

If any check fails, raise `ReportValidationError` and abort the run.
This is a deterministic in-Python check; failure means the report
builder has a bug, not a model misbehaviour.

### 6.2 Code changes

| File | Change | LOC |
|---|---|---|
| `pipeline/proposer/reporter.py` | Add `_validate_report(content, classified_changes)` function; call it before the file write; define `ReportValidationError` exception | ~40 LOC added |
| `pipeline/tests/test_reporter.py` | Existing 7 tests unchanged; add 4 new validation tests | ~60 LOC added |

### 6.3 Test additions

1. `test_validate_accepts_well_formed_report` - happy path
2. `test_validate_rejects_heading_count_mismatch` - synthesise a report with one missing `### N. ` heading
3. `test_validate_rejects_missing_change_type_section` - synthesise a classified-change list with PRICING_CHANGE but produce a report without the PRICING_CHANGE section
4. `test_validate_rejects_missing_approval_footer` - non-empty case without the footer string

### 6.4 Risks

None substantive. Validation runs in-process before any I/O.

---

## 7. Cross-cutting: what changes about the unfreeze criteria

The audit's proposed unfreeze criteria (U1-U8) still apply unchanged.
This plan adds three operational details:

- **U1 dry-run replay**: the audit names "5 consecutive dry runs against
  the historical change archive". After Harden PR A lands, the dry runs
  must use the new hunks-based applier. After Harden PR B lands, the
  dry runs must produce a complete per-run structured report each time.
- **U6 tool-use migration done**: assertion in the unfreeze checklist
  becomes "Harden PR A merged AND `pipeline/tests/test_file_updater_hunks.py`
  passes on Python 3.10/3.11/3.12".
- **U8 pre-flight clean-tree check**: explicitly NOT in Harden scope.
  Moved to Stabilise PR (it's nice-to-have, not blocking).

---

## 8. Out of scope for the Harden PRs

The following are deliberately not in this plan; they belong to Stabilise
or a separate cleanup PR.

- **Backup retention policy** (item 6 from the audit). Adds complexity to
  `apply_with_guard_rails`; can land after unfreeze.
- **Pre-flight clean-tree check** (item 7). Convenience, not correctness.
- **`datetime.utcnow()` migration** (item 8). 24 deprecation warnings, no
  current behaviour change. Cleanup PR.
- **Branch reuse safety** (item 9). Convenience; the current behaviour is
  documented.
- **`sources.yaml` accuracy audit**. Out of scope of the audit too.
- **MCP server design**. The `pipeline/mcp_server/` directory is empty;
  whatever it's for belongs in its own design pass.
- **Prompt-quality evaluation**. Whether the classifier and applier
  prompts produce good outputs at scale. Needs a labelled eval set;
  separate work stream.

---

## 9. Verification

For the plan itself (this document):

- Every code change has a concrete file path and rough LOC estimate
- Every item has a test-additions section with named test cases
- Every item has a risks section with a rollback story where applicable
- The unfreeze criteria from the audit are still satisfiable after Harden PRs A and B land

For the Harden PRs that this plan informs:

- After Harden PR A: `python -m pytest pipeline/tests/test_file_updater_guards.py pipeline/tests/test_file_updater_hunks.py -v` -> all pass
- After Harden PR B: full suite passes on Python 3.10/3.11/3.12; per-run structured reports appear under `pipeline/state/runs/<timestamp>/report.json`; the fetcher logs distinguish "broken source" from "no news"; the classifier handles a junk content gracefully (drops the item, not the whole run)

The unfreeze checklist (audit section 10, U1-U8) becomes runnable once
Harden PR B merges. Unfreezing happens in the Stabilise PR, not in the
Harden PRs.

---

## 10. What this plan does NOT do

- Does not modify any pipeline code (that's Harden PRs A and B)
- Does not pick the Stabilise PR or Publish PR scope - those follow
- Does not commit to a specific calendar for the Harden work
- Does not change the audit doc - if a finding here contradicts the
  audit, the audit is authoritative and this plan needs a revision

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
