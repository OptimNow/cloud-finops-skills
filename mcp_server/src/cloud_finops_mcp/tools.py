"""Tool implementations exposed by the MCP server.

Each tool returns a JSON-serialisable ``dict``. The server module wraps these
as MCP tools using the ``mcp`` SDK.

The reference tools (``list_references`` / ``get_reference`` / ``find_references``)
serve the long-form provider and discipline files. The playbook tools
(``list_playbooks`` / ``get_playbook`` / ``find_playbooks``) serve the
named-pattern runbooks - small, retrieval-friendly chunks scoped to one waste
pattern each.
"""

from __future__ import annotations

import difflib
import functools
import logging
import math
import re
import unicodedata
from typing import Any

from .metadata import (
    Playbook,
    Question,
    Reference,
    find_sections,
    get_by_name,
    get_index,
    get_playbook_by_name,
    get_playbook_index,
    section_labels,
    section_text,
    split_sections,
    strip_frontmatter,
)

logger = logging.getLogger(__name__)

# Cap on the headings listed back after a section miss. finops-azure has 100
# H2+H3 headings; listing them all is ~900 tokens, still an order of magnitude
# below the 21K-token body the caller is trying not to fetch, so the cap is
# generous on purpose and only exists to bound a pathological file.
SECTION_LIST_LIMIT = 120

# Ambiguity is reported, not resolved by silence: the caller gets the best
# match plus a short list of the runners-up so a wrong pick is one cheap,
# correctly-spelled retry away.
OTHER_MATCH_LIMIT = 5

# --- free-text query -------------------------------------------------------
#
# ``find_*(query=...)`` exists because the facet filters are exact-match on
# framework vocabulary, and the probe battery showed the model rarely owns
# that vocabulary when the user does not: "NAT" matches no service, a symptom
# sentence matches no capability. The query ranks what the facets left by word
# overlap with the ``questions:`` each file declares it answers (written in the
# user's words, English and French), then its title and description, then its
# H2/H3 headings. Plain Python, deterministic, no embedding and no network, so
# it stays inside the closed-world contract the six retrieval tools make.

# At most this many ranked entries come back. A query is a routing step, not a
# listing: the caller wants the file to fetch next, plus a runner-up or two.
QUERY_RESULT_LIMIT = 5

# Below this score an entry shares too little with the query to be worth
# fetching - one incidental word out of five, say. Scores are coverage
# fractions weighted by surface; see _score_against_query.
QUERY_MIN_SCORE = 0.2

_QUESTION_WEIGHT = 1.0
# A query that names one provider ("reduce AWS costs") halves the score of a file
# written for another provider. Provider names are common words, so frequency
# weighting alone lets an Azure question win that query on "reduce" and "cost".
# Cross-provider files (FinOps practice, allocation, contracts) are untouched.
_OTHER_PROVIDER_FACTOR = 0.5
_PROVIDER_WORDS = {
    "aws": "aws",
    "amazon": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "google": "gcp",
    "oci": "oci",
}
_REFERENCE_PROVIDER_PREFIXES = (
    ("finops-aws", "aws"),
    ("finops-bedrock", "aws"),
    ("finops-azure", "azure"),
    ("finops-fabric", "azure"),
    ("finops-gcp", "gcp"),
    ("finops-vertexai", "gcp"),
    ("finops-oci", "oci"),
)
_TITLE_WEIGHT = 0.5
_HEADING_WEIGHT = 0.35

_QUERY_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Function words in the two languages the questions are written in. Kept
# short on purpose: the list only has to stop a query's grammar from matching
# every file, not model either language.
_STOPWORDS = frozenset(
    """
    a an the of to in on at for and or is are be been was were we our us my i me
    it its do does did not no should can could would will how what which who why
    when where this that these those with without from by as you your they them
    their have has had if than then so but about any all still just also into
    over per vs more much many some one
    le la les l un une des de du d et ou au aux en dans sur pour par que qui
    quoi qu ne pas est sont nous notre nos vos votre ce cet cette ces il elle
    ils elles se sa son ses y comment pourquoi quand quel quelle quels quelles
    faut plus sans avec dont encore
    """.split()
)


def _fold(text: str) -> str:
    """Lowercase ASCII fold, so ``Coûte`` matches ``coute`` and ``Réservation`` ``reservation``."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def _stem(token: str) -> str:
    """Crude plural folding: ``gateways`` to ``gateway``, ``policies`` to ``policy``,
    ``processes`` to ``process``."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith(("sses", "xes")):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


@functools.lru_cache(maxsize=8192)
def query_tokens(text: str) -> frozenset[str]:
    """The content words of ``text``: folded, stemmed, stopwords and single letters dropped.

    Cached per string: the index's questions and headings are tokenised on
    every query and never change between calls.
    """
    return frozenset(
        _stem(tok)
        for tok in _QUERY_TOKEN_RE.findall(_fold(text))
        if tok not in _STOPWORDS and len(tok) > 1
    )


def _weight(tokens, idf: dict[str, float]) -> float:
    """Summed inverse document frequency of ``tokens``; a word the index never saw weighs 1.0."""
    return sum(idf.get(tok, 1.0) for tok in tokens)


def _idf(corpus: list, title_text) -> dict[str, float]:
    """Inverse document frequency of every content word over one index.

    A word's document frequency is the number of files whose questions, title
    text or headings carry it, so a provider name present in most files weighs
    little and a service or symptom word weighs more. Smoothed: a word in every
    file weighs just above 1.0, a word in a single file about 1 + ln(N / 2).
    Computed per call over the whole index of the kind, not the facet-filtered
    subset, so the weights describe the library and not the user's filter.
    """
    df: dict[str, int] = {}
    for item in corpus:
        bag: set[str] = set(query_tokens(title_text(item)))
        for question in item.questions:
            bag |= query_tokens(question.text)
        for heading in item.headings:
            bag |= query_tokens(heading)
        for tok in bag:
            df[tok] = df.get(tok, 0) + 1
    n = len(corpus)
    return {tok: 1.0 + math.log((n + 1) / (count + 1)) for tok, count in df.items()}


def _coverage(query: frozenset[str], text: str, idf: dict[str, float]) -> float:
    """Share of the lighter side's weight that ``query`` and ``text`` have in common.

    Each content word weighs its inverse document frequency, so ``nat`` or
    ``gcp`` counts for more than ``cost`` or ``aws``. The shared weight is
    divided by the lighter of the two sides: a long query that contains a
    whole declared question scores it 1.0 instead of being diluted by its own
    extra words. A one-word text is divided by the query side, so a lone
    ``Timing`` heading cannot score 1.0 from a paragraph.
    """
    if not query:
        return 0.0
    text_tokens = query_tokens(text)
    shared = query & text_tokens
    if not shared:
        return 0.0
    denominator = _weight(query, idf)
    if len(text_tokens) > 1:
        denominator = min(denominator, _weight(text_tokens, idf))
    return _weight(shared, idf) / denominator


def _score_against_query(
    query: frozenset[str],
    questions: list[Question],
    title_text: str,
    headings: list[str],
    idf: dict[str, float],
) -> tuple[float, Question | None]:
    """Score one indexed file against a tokenised query.

    Returns ``(score, best_question)``. The score is the best question's
    coverage at full weight, plus title/description coverage at half weight,
    plus the best heading's coverage at about a third - so a file that
    declares the user's question outranks one that merely shares its nouns,
    and a file with no ``questions:`` block yet is still reachable through
    its title and headings.
    """
    best_question: Question | None = None
    best_coverage = 0.0
    for question in questions:
        coverage = _coverage(query, question.text, idf)
        if coverage > best_coverage:
            best_question, best_coverage = question, coverage
    title_coverage = _coverage(query, title_text, idf)
    heading_coverage = max((_coverage(query, h, idf) for h in headings), default=0.0)
    score = (
        _QUESTION_WEIGHT * best_coverage
        + _TITLE_WEIGHT * title_coverage
        + _HEADING_WEIGHT * heading_coverage
    )
    return score, best_question


def _provider_of(item) -> str | None:
    """The provider a file is written for: a playbook's scope, a reference's name prefix."""
    scope = getattr(item, "scope", None)
    if scope in {"aws", "azure", "gcp", "oci"}:
        return scope
    for prefix, provider in _REFERENCE_PROVIDER_PREFIXES:
        if item.name.startswith(prefix):
            return provider
    return None


def _query_provider(tokens: frozenset[str]) -> str | None:
    """The one provider a query names, or None when it names none or several."""
    named = {_PROVIDER_WORDS[tok] for tok in tokens if tok in _PROVIDER_WORDS}
    return next(iter(named)) if len(named) == 1 else None


def _rank_by_query(
    items: list, query: str, title_text, corpus: list
) -> list[tuple[Any, float, Question | None]]:
    """``(item, score, matched_question)`` for the items worth returning, best first.

    ``title_text`` maps an item to the text scored at title weight: title plus
    description for a reference, title plus service for a playbook. ``corpus``
    is the whole index of that kind, which sets the word weights; ``items`` is
    the facet-filtered subset actually ranked. Ties break on name so the order
    is stable from one call to the next.
    """
    tokens = query_tokens(query)
    if not tokens:
        return []
    idf = _idf(corpus, title_text)
    named = _query_provider(tokens)
    ranked: list[tuple[Any, float, Question | None]] = []
    for item in items:
        score, question = _score_against_query(
            tokens, item.questions, title_text(item), item.headings, idf
        )
        if named and _provider_of(item) not in (None, named):
            score *= _OTHER_PROVIDER_FACTOR
        if score >= QUERY_MIN_SCORE:
            ranked.append((item, score, question))
    ranked.sort(key=lambda entry: (-entry[1], entry[0].name))
    return ranked[:QUERY_RESULT_LIMIT]


def _query_entry(item, score: float, question: Question | None) -> dict[str, Any]:
    """A listing entry plus what the query matched, so the next call can go to the section."""
    entry = item.to_dict()
    entry["match_score"] = round(score, 2)
    entry["matched_question"] = question.text if question else None
    entry["suggested_section"] = question.section if question is not None else None
    return entry


def _query_miss_help(kind: str, query_text: str) -> dict[str, Any]:
    """Explain a ``query`` that matched nothing, in place of a bare ``total: 0``."""
    if not query_tokens(query_text):
        return {
            "hint": (
                f"The query has no content words once common words are set aside, so no "
                f"{kind} was compared. Name the service, the resource or the symptom, for "
                "example 'NAT gateway', 'expiring reservations' or 'PTU utilisation'."
            )
        }
    return {
        "hint": (
            f"No {kind} shares a content word with the query - its questions, title "
            "and headings were all checked. Try fewer or more specific words (the "
            "service or the symptom), or drop the query and browse with the facets. "
            "If the library should answer this, the user can report the wording at "
            "https://github.com/OptimNow/cloud-finops-skills/issues/new/choose; this server does not log it."
        )
    }


def _loggable(filters: dict[str, Any], query_text: str) -> dict[str, Any]:
    """The zero-result log line for a query miss.

    The query text itself is never written: PRIVACY.md promises that the miss
    log holds facet values, not conversation text, and a ``query`` is the
    user's sentence. The word count keeps the coverage signal that the log
    exists for (how often users phrase questions the library does not catch).
    """
    kept = {k: v for k, v in filters.items() if k != "query"}
    kept["query_words"] = len(query_tokens(query_text))
    return kept


def _log_zero_result(tool: str, active: dict[str, Any]) -> None:
    """Log a faceted query that matched nothing.

    A zero-result query is the purest coverage signal there is: an agent
    (so, a user) asked for something the bundled set does not have. The
    marker string is grepped from the hosted deployment's logs during the
    periodic coverage review (see the maintainer coverage-probe doctrine),
    which is why it must stay stable.
    """
    logger.info("zero-result query: %s filters=%r", tool, active)


def list_references() -> dict[str, Any]:
    """Return all bundled references with their discriminating FCP facets.

    Useful as a discovery call: the agent inspects the result and decides which
    reference(s) to fetch via ``get_reference``.

    Each entry is a summary, not the full record - see ``Reference.to_dict``
    for what is withheld and why. ``approx_tokens`` is the size hint: the
    library spans roughly 3K to 26K tokens per file, so it is the difference
    between one cheap fetch and a fifth of a context window.
    """
    refs = [r.to_dict() for r in get_index()]
    return {"references": refs, "total": len(refs)}


def _section_miss(ref: Reference, section: str, body: str) -> dict[str, Any]:
    """Loud failure for a section query that matched no heading.

    Silently returning the whole body would hand back the 26K tokens the
    caller was explicitly trying to avoid, and an empty result would leave it
    unable to tell a typo from a file with no sections. So the miss returns
    the vocabulary instead: every available heading, plus difflib's nearest
    guesses, which is everything needed to get the second call right.
    """
    labels = section_labels(body)
    if not labels:
        detail = (
            f"Reference '{ref.name}' has no H2 or H3 sections to select from. "
            "get_reference without 'section' returns it whole."
        )
    else:
        detail = (
            f"No section of '{ref.name}' matches {section!r}. 'available_sections' "
            "lists every heading in the file; get_reference without 'section' "
            "returns the full body."
        )
    _log_zero_result("get_reference", {"name": ref.name, "section": section})
    result: dict[str, Any] = {
        "error": detail,
        "available_sections": labels[:SECTION_LIST_LIMIT],
        "suggestions": difflib.get_close_matches(
            section, [s.heading for s in split_sections(body)], n=3, cutoff=0.4
        ),
    }
    if len(labels) > SECTION_LIST_LIMIT:
        result["available_sections_truncated"] = len(labels) - SECTION_LIST_LIMIT
    return result


def get_reference(name: str, section: str | None = None) -> dict[str, Any]:
    """Return one reference: the whole body, or a single section of it.

    With ``section`` omitted the payload is exactly what it has always been -
    ``{"name", "content", "lines"}`` with ``content`` the file verbatim,
    frontmatter included. Callers and the reference-browser widget depend on
    that, so it is pinned by a test.

    With ``section`` set, ``content`` is the matched H2/H3 span prefixed by the
    reference's H1 so the chunk is self-describing, and ``partial: True`` says
    plainly that this is not the whole file.

    On either kind of miss - unknown name, or a section that matches no
    heading - returns an error carrying enough vocabulary to retry.
    """
    if not isinstance(name, str) or not name.strip():
        return {
            "error": "Parameter 'name' is required and must be a non-empty string.",
            "suggestions": [],
        }

    ref = get_by_name(name)
    if ref is None:
        all_names = [r.name for r in get_index()]
        suggestions = difflib.get_close_matches(name, all_names, n=3, cutoff=0.5)
        return {
            "error": f"No reference named '{name}'. See list_references() for the full set.",
            "suggestions": suggestions,
        }

    try:
        content = ref.path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"error": f"Failed to read '{name}': {exc}", "suggestions": []}

    # An absent, empty, or whitespace-only section is the full-body path. A
    # model that fills the parameter in with "" should get the document, not
    # an error about a heading it never meant to ask for.
    if not isinstance(section, str) or not section.strip():
        return {
            "name": ref.name,
            "content": content,
            "lines": ref.lines,
        }

    body = strip_frontmatter(content, source=ref.path.name)
    matches = find_sections(body, section)
    if not matches:
        return _section_miss(ref, section, body)

    best = matches[0]
    chunk = f"# {ref.title}\n\n{section_text(body, best)}"
    result: dict[str, Any] = {
        "name": ref.name,
        "title": ref.title,
        "section": best.heading,
        "section_level": best.level,
        "partial": True,
        "note": (
            f"Section extract of '{ref.name}', not the full reference. "
            "get_reference without 'section' returns the whole body."
        ),
        "content": chunk,
        "lines": chunk.count("\n"),
        "full_lines": ref.lines,
    }
    if len(matches) > 1:
        result["other_matching_sections"] = [
            s.label for s in matches[1 : 1 + OTHER_MATCH_LIMIT]
        ]
    return result


def _matches_scalar(value: str | None, filter_value: str) -> bool:
    return value is not None and value.casefold() == filter_value.casefold()


def _matches_list(values: list[str], filter_value: str) -> bool:
    fv = filter_value.casefold()
    return any(v.casefold() == fv for v in values)


def _persona_match(ref: Reference, persona: str, primary_only: bool = False) -> bool:
    """Persona filter checks the primary list, plus collaborating by default.

    The collaborating check is opt-out for a reason found in the field: a
    persona like Engineering collaborates on nearly everything in FinOps, so
    the OR over both lists barely narrows anything (the 2026-08-19 test
    measured exactly one exclusion across the whole library). The metadata is
    descriptively correct; ``primary_only`` is the operational cut.
    """
    if _matches_list(ref.fcp_personas_primary, persona):
        return True
    if primary_only:
        return False
    return _matches_list(ref.fcp_personas_collaborating, persona)


def _capability_match(ref: Reference, capability: str) -> bool:
    """Capability filter checks both primary and secondary."""
    return _matches_scalar(ref.fcp_capability, capability) or _matches_list(
        ref.fcp_capabilities_secondary, capability
    )


def reference_vocabulary() -> dict[str, list[str]]:
    """Distinct values present in the reference index, per facet.

    Derived from the bundled data rather than hardcoded, so it cannot drift
    from what the files actually declare.
    """
    vocab: dict[str, set[str]] = {
        "domain": set(),
        "capability": set(),
        "phase": set(),
        "persona": set(),
        "maturity": set(),
    }
    for ref in get_index():
        if ref.fcp_domain:
            vocab["domain"].add(ref.fcp_domain)
        if ref.fcp_capability:
            vocab["capability"].add(ref.fcp_capability)
        vocab["capability"].update(ref.fcp_capabilities_secondary)
        vocab["phase"].update(ref.fcp_phases)
        vocab["persona"].update(ref.fcp_personas_primary)
        vocab["persona"].update(ref.fcp_personas_collaborating)
        if ref.fcp_maturity_entry:
            vocab["maturity"].add(ref.fcp_maturity_entry)
    return {k: sorted(v) for k, v in vocab.items()}


def playbook_vocabulary() -> dict[str, list[str]]:
    """Distinct values present in the playbook index, per facet."""
    vocab: dict[str, set[str]] = {
        "scope": set(),
        "service": set(),
        "waste_category": set(),
        "confidence": set(),
    }
    for pb in get_playbook_index():
        for facet, value in (
            ("scope", pb.scope),
            ("service", pb.service),
            ("waste_category", pb.waste_category),
            ("confidence", pb.confidence),
        ):
            if value:
                vocab[facet].add(value)
    return {k: sorted(v) for k, v in vocab.items()}


def _unmatched_filters(
    active: dict[str, str], vocabulary: dict[str, list[str]]
) -> list[str]:
    """Active filter names whose value appears nowhere in the index.

    A filter listed here is the reason the result set is empty - as opposed to
    a legitimate no-overlap combination of individually-valid values.
    """
    unmatched = []
    for key, value in active.items():
        known = {v.casefold() for v in vocabulary.get(key, [])}
        if value.casefold() not in known:
            unmatched.append(key)
    return unmatched


def _empty_result_help(
    active: dict[str, str], vocabulary: dict[str, list[str]]
) -> dict[str, Any]:
    """Explain a zero-match faceted query instead of returning a bare total: 0.

    The name-based tools already offer difflib suggestions on a miss; the
    faceted tools returned nothing at all, leaving the caller unable to tell a
    typo from a genuine gap in coverage.
    """
    unmatched = _unmatched_filters(active, vocabulary)
    if unmatched:
        detail = (
            "No match for "
            + ", ".join(f"{k}={active[k]!r}" for k in unmatched)
            + " - "
            + ("that value is" if len(unmatched) == 1 else "those values are")
            + " not present in the bundled set."
        )
    else:
        detail = (
            "Every filter value is valid on its own, but no single item carries "
            "all of them together; relaxing one filter widens the match."
        )
    return {
        "hint": detail,
        "valid_values": {k: vocabulary.get(k, []) for k in active},
    }


def find_references(
    query: str | None = None,
    domain: str | None = None,
    capability: str | None = None,
    phase: str | None = None,
    persona: str | None = None,
    maturity: str | None = None,
    persona_primary_only: bool = False,
) -> dict[str, Any]:
    """Filter references by FCP frontmatter, and rank them by a free-text ``query``.

    The facets are optional and combine with AND semantics. String matches
    are case-insensitive and exact (no substring matching). Empty filters return
    the full index. A facet query that matches nothing returns ``hint`` and
    ``valid_values`` alongside ``total: 0``, so a typo is distinguishable from a
    genuine coverage gap.

    ``query`` is the user's question in their own words. The facets narrow the
    set first; the query then ranks what is left by word overlap with each
    reference's declared ``questions``, its title and description, and its
    H2/H3 headings (see ``_score_against_query``), returns at most
    ``QUERY_RESULT_LIMIT`` entries, and adds ``match_score``,
    ``matched_question`` and ``suggested_section`` to each. A query that
    matches nothing returns ``hint`` alone.

    ``capability`` and ``persona`` filter over the secondary and collaborating
    declarations too, even though the returned entries no longer print them -
    the listing shape is trimmed for tokens, the filtering is not.

    Args:
        query: the user's question or symptom, any length, English or
            French; blank is treated as absent.
        domain: one of the four FinOps Framework domains, e.g.
            ``"Optimize Usage & Cost"``.
        capability: a FinOps Capability, matched against both the primary and
            the secondary declarations, e.g. ``"Rate Optimization"``.
        phase: ``Inform``, ``Optimize``, or ``Operate``.
        persona: matched against both primary and collaborating personas, e.g.
            ``"Engineering"``.
        maturity: ``Crawl``, ``Walk``, or ``Run`` - the entry gate below which
            the reference is premature.
        persona_primary_only: when True, ``persona`` matches only
            ``fcp_personas_primary``. Use it when the default match barely
            narrows the set - broad personas like Engineering collaborate on
            nearly every file, so the collaborating list is descriptive
            rather than discriminating.
    """
    filters = {
        "domain": domain,
        "capability": capability,
        "phase": phase,
        "persona": persona,
        "maturity": maturity,
    }
    active = {k: v for k, v in filters.items() if isinstance(v, str) and v.strip()}

    matches: list[Reference] = []
    for ref in get_index():
        if "domain" in active and not _matches_scalar(ref.fcp_domain, active["domain"]):
            continue
        if "capability" in active and not _capability_match(ref, active["capability"]):
            continue
        if "phase" in active and not _matches_list(ref.fcp_phases, active["phase"]):
            continue
        if "persona" in active and not _persona_match(
            ref, active["persona"], primary_only=persona_primary_only
        ):
            continue
        if "maturity" in active and not _matches_scalar(
            ref.fcp_maturity_entry, active["maturity"]
        ):
            continue
        matches.append(ref)

    reported_filters: dict[str, Any] = dict(active)
    if persona_primary_only and "persona" in active:
        reported_filters["persona_primary_only"] = True

    query_text = query.strip() if isinstance(query, str) else ""
    if query_text:
        reported_filters["query"] = query_text
        ranked = _rank_by_query(
            matches, query_text, lambda r: f"{r.title} {r.description}", get_index()
        )
        result: dict[str, Any] = {
            "filters": reported_filters,
            "references": [_query_entry(r, score, q) for r, score, q in ranked],
            "total": len(ranked),
        }
        if not ranked:
            result.update(
                _empty_result_help(active, reference_vocabulary())
                if active and not matches
                else _query_miss_help("reference", query_text)
            )
            _log_zero_result("find_references", _loggable(reported_filters, query_text))
        return result

    result = {
        "filters": reported_filters,
        "references": [r.to_dict() for r in matches],
        "total": len(matches),
    }
    if not matches and active:
        result.update(_empty_result_help(active, reference_vocabulary()))
        _log_zero_result("find_references", reported_filters)
    return result


# --- playbook tools ---------------------------------------------------------


def list_playbooks() -> dict[str, Any]:
    """Return all bundled named-pattern playbooks.

    Each playbook is a ~90-170 line runbook scoped to one waste pattern
    (e.g. ``aws-zombie-nat-gateway``). Use this for discovery; fetch the body
    via ``get_playbook(name)``.
    """
    playbooks = [pb.to_dict() for pb in get_playbook_index()]
    return {"playbooks": playbooks, "total": len(playbooks)}


def get_playbook(name: str) -> dict[str, Any]:
    """Return the full markdown content of one playbook.

    On miss, returns ``{"error": ..., "suggestions": [...]}`` so the agent can
    self-correct.
    """
    if not isinstance(name, str) or not name.strip():
        return {
            "error": "Parameter 'name' is required and must be a non-empty string.",
            "suggestions": [],
        }

    pb = get_playbook_by_name(name)
    if pb is None:
        all_names = [p.name for p in get_playbook_index()]
        suggestions = difflib.get_close_matches(name, all_names, n=3, cutoff=0.5)
        return {
            "error": f"No playbook named '{name}'. See list_playbooks() for the full set.",
            "suggestions": suggestions,
        }

    try:
        content = pb.path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"error": f"Failed to read '{name}': {exc}", "suggestions": []}

    return {
        "name": pb.name,
        "title": pb.title,
        "content": content,
        "lines": pb.lines,
    }


def find_playbooks(
    query: str | None = None,
    scope: str | None = None,
    service: str | None = None,
    waste_category: str | None = None,
    confidence: str | None = None,
) -> dict[str, Any]:
    """Filter playbooks by their pattern frontmatter, and rank them by a free-text ``query``.

    The facets are optional and combine with AND semantics. String matches
    are case-insensitive and exact (no substring matching). A facet query that
    matches nothing returns `hint` and `valid_values` alongside `total: 0`.

    ``query`` is the user's symptom in their own words ("NAT gateway charges
    but nothing uses them", "passerelle NAT qui ne sert à rien"). The facets
    narrow the set first; the query ranks what is left by word overlap with
    each playbook's declared ``questions``, its title and service, and its
    headings, returns at most ``QUERY_RESULT_LIMIT`` entries, and adds
    ``match_score``, ``matched_question`` and ``suggested_section`` to each.
    A query that matches nothing returns `hint` alone.

    The double-backtick values listed below are the accepted vocabulary for
    each facet, and are pinned against the bundled data by
    `tests/test_conformance.py` - keep them in step when content changes.

    Args:
        query: the user's symptom or question, any length, English or
            French; blank is treated as absent.
        scope: ``aws``, ``azure``, ``gcp``, or ``cross-cloud``.
        service: provider service name (e.g. ``"AWS NAT Gateway"``,
            ``"Azure Managed Disks"``). Exact-match against a free-text field -
            call ``list_playbooks`` first to see the values actually present,
            or filter on ``scope`` instead. A miss returns the valid values.
        waste_category: ``orphaned``, ``idle``, ``overprovisioned``,
            ``commitment-mismatch``, ``schedule-blindness``, ``modernization``,
            ``ai-ml-inefficiency``, or ``egress``.
        confidence: ``obvious``, ``likely``, or ``possible`` - the OptimNow
            three-tier confidence model defined in the
            `finops-waste-detection-playbooks` reference.
    """
    filters = {
        "scope": scope,
        "service": service,
        "waste_category": waste_category,
        "confidence": confidence,
    }
    active = {k: v for k, v in filters.items() if isinstance(v, str) and v.strip()}

    matches: list[Playbook] = []
    for pb in get_playbook_index():
        if "scope" in active and not _matches_scalar(pb.scope, active["scope"]):
            continue
        if "service" in active and not _matches_scalar(pb.service, active["service"]):
            continue
        if "waste_category" in active and not _matches_scalar(
            pb.waste_category, active["waste_category"]
        ):
            continue
        if "confidence" in active and not _matches_scalar(
            pb.confidence, active["confidence"]
        ):
            continue
        matches.append(pb)

    reported_filters: dict[str, Any] = dict(active)
    query_text = query.strip() if isinstance(query, str) else ""
    if query_text:
        reported_filters["query"] = query_text
        ranked = _rank_by_query(
            matches, query_text, lambda pb: f"{pb.title} {pb.service or ''}", get_playbook_index()
        )
        result: dict[str, Any] = {
            "filters": reported_filters,
            "playbooks": [_query_entry(pb, score, q) for pb, score, q in ranked],
            "total": len(ranked),
        }
        if not ranked:
            result.update(
                _empty_result_help(active, playbook_vocabulary())
                if active and not matches
                else _query_miss_help("playbook", query_text)
            )
            _log_zero_result("find_playbooks", _loggable(reported_filters, query_text))
        return result

    result = {
        "filters": active,
        "playbooks": [pb.to_dict() for pb in matches],
        "total": len(matches),
    }
    if not matches and active:
        result.update(_empty_result_help(active, playbook_vocabulary()))
        _log_zero_result("find_playbooks", active)
    return result
