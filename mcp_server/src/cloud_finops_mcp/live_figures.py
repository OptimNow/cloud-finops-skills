"""Live figures from the OptimToken guides (``get_live_figures``).

Some references quote a figure from an OptimToken guide with the date it was
read: the Compute Savings Plan discount, the gap between a flexible and a
locked commitment. The quoted figure goes stale; the guide's own
``figures.json``, rebuilt with the page every night, carries the current one.
This module fetches that file and hands it back as received.

It is the server's only outbound request, and it is kept narrow on purpose:

- one host (:data:`HOST`), one path shape, a slug validated before any URL is
  built, and redirects followed only on that host;
- the document is passed through, never recomputed or rounded. Duplicated
  computation is the failure this family keeps paying for (see the standing
  decision in docs/ROADMAP.md), so the figures stay OptimToken's;
- the tool never raises. A failure returns an error dict that tells the model
  to fall back on the dated figure in the reference.

Stdlib only (``urllib.request``): the package pins its dependency set, and one
GET does not justify a new one.
"""

from __future__ import annotations

import difflib
import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from . import __version__

logger = logging.getLogger(__name__)

HOST = "optimtoken.optimnow.io"
FIGURES_URL = "https://" + HOST + "/guides/{slug}/figures.json"
LLMS_TXT_URL = "https://" + HOST + "/llms.txt"
USER_AGENT = f"cloud-finops-mcp/{__version__} (+https://github.com/OptimNow/cloud-finops-skills)"

TIMEOUT_SECONDS = 5
# The directory policy asks a tool's token use to stay commensurate with the task
# (Software Directory Policy 5.B). The three files are 3 to 9 KB today; 128 KiB
# (about 32,000 tokens, twice the largest reference) bounds a pathological file
# without ever truncating a real one, and the cap returns an error, not a cut file.
MAX_BODY_BYTES = 128 * 1024
# The file is rebuilt once a day (refresh at 12:30 UTC, then a deploy), so six
# hours keeps a hosted instance to a handful of requests per guide per day
# while never serving a figure more than one rebuild behind.
CACHE_TTL_SECONDS = 6 * 60 * 60

SLUG_RE = re.compile(r"^[a-z0-9-]{1,80}$")

# One line per guide that exports figures, in llms.txt's link-list form:
# - [<title>](https://optimtoken.optimnow.io/guides/<slug>): <description> Figures as JSON: <url>
_GUIDE_LINE_RE = re.compile(
    r"^- \[(?P<title>[^\]]+)\]\(https://optimtoken\.optimnow\.io/guides/(?P<slug>[a-z0-9-]+)\):"
    r".*Figures as JSON: https://optimtoken\.optimnow\.io/guides/(?P=slug)/figures\.json\s*$",
    re.M,
)

FALLBACK = "Use the dated figure in the reference and say which day it is from."

_LLMS_KEY = "llms.txt"

# slug (or _LLMS_KEY) -> (stored_at epoch seconds, fetched_at ISO string, value).
# Only successes are stored, so a transient failure is retried on the next call.
_cache: dict[str, tuple[float, str, Any]] = {}

# Indirections the tests monkeypatch: the wall clock (to age the cache) and
# the HTTP GET (so the suite runs offline).
_now = time.time


class _SameHostRedirect(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only when it stays on :data:`HOST`.

    PRIVACY.md says this tool talks to one host; a redirect elsewhere would
    make that untrue, so it surfaces as the redirect's HTTP error instead.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).hostname != HOST:
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_SameHostRedirect)


def _fetch(url: str) -> tuple[int, bytes]:
    """GET ``url`` and return ``(status, body)``.

    An HTTP error status is returned, not raised. A network failure or a
    timeout raises (``URLError``, ``TimeoutError``, ``OSError``) and the caller
    turns it into an error dict. The body is read up to one byte past the cap
    so an oversized file is detectable without reading all of it.
    """
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, text/plain"}
    )
    try:
        with _opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, response.read(MAX_BODY_BYTES + 1)
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def reset_cache() -> None:
    """Drop every cached guide and the cached guide list (tests use this)."""
    _cache.clear()


def _cached(key: str) -> tuple[str, Any, int] | None:
    """The cached ``(fetched_at, value, age_seconds)`` for ``key``, if still fresh."""
    entry = _cache.get(key)
    if entry is None:
        return None
    stored_at, fetched_at, value = entry
    age = _now() - stored_at
    if age >= CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    return fetched_at, value, int(age)


def _store(key: str, value: Any) -> str:
    stored_at = _now()
    fetched_at = (
        datetime.fromtimestamp(stored_at, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
    _cache[key] = (stored_at, fetched_at, value)
    return fetched_at


def _failure(message: str) -> dict[str, Any]:
    logger.warning("get_live_figures failed: %s", message)
    return {"error": message, "fallback": FALLBACK}


def _note(document: dict[str, Any]) -> str:
    snapshot = document.get("snapshotDate") or "the snapshotDate above"
    return (
        f"Figures from the OptimToken catalogue of {snapshot}, passed through as "
        "published. When quoting one, give that snapshotDate with it and link the "
        "document's url. Each figure is a median, a min-max range or a count, as "
        "its key names it; say which. figures.unit says what the numbers measure "
        "(discounts are fractions: 0.2743 is 27.4%). A dated figure inside a "
        "reference is the fallback when this tool fails."
    )


def available_guides() -> list[dict[str, str]] | None:
    """The guides that publish figures, read from OptimToken's llms.txt.

    Returns ``[{"slug": ..., "title": ...}, ...]``, or None when the list
    cannot be read. Cached like a guide, for the same reason.
    """
    hit = _cached(_LLMS_KEY)
    if hit is not None:
        return hit[1]
    try:
        status, body = _fetch(LLMS_TXT_URL)
    except Exception as exc:  # noqa: BLE001 - every failure degrades to None
        logger.warning("llms.txt fetch failed: %r", exc)
        return None
    if status != 200 or len(body) > MAX_BODY_BYTES:
        logger.warning("llms.txt fetch returned HTTP %s (%d bytes)", status, len(body))
        return None
    text = body.decode("utf-8", errors="replace")
    guides = [
        {"slug": m.group("slug"), "title": m.group("title")}
        for m in _GUIDE_LINE_RE.finditer(text)
    ]
    _store(_LLMS_KEY, guides)
    return guides


def _not_found(guide: str) -> dict[str, Any]:
    guides = available_guides()
    result: dict[str, Any] = {
        "error": f"No OptimToken guide publishes figures under {guide!r}.",
        "available_guides": guides or [],
        "suggestions": difflib.get_close_matches(
            guide, [g["slug"] for g in guides or []], n=3, cutoff=0.5
        ),
    }
    if guides is None:
        result["fallback"] = FALLBACK
    logger.info("get_live_figures miss: %r", guide)
    return result


def get_live_figures(guide: str) -> dict[str, Any]:
    """Fetch the current ``figures.json`` of one OptimToken guide.

    On success returns ``{"document": <figures.json as received>,
    "fetched_at": <UTC ISO 8601>, "source": "live" | "cached", "note": ...}``,
    plus ``cache_age_seconds`` when served from the cache. The document is
    nested rather than merged so none of its keys (it has its own ``note``) is
    shadowed by the ones added here.

    On a 404, returns ``{"error", "available_guides", "suggestions"}`` read from
    llms.txt. On any other failure (invalid slug, timeout, non-200, a body over
    128 KiB, invalid JSON, an envelope without ``guide`` or ``figures``) returns
    ``{"error", "fallback"}``. An invalid slug is rejected before any request.
    Never raises.
    """
    if not isinstance(guide, str) or not SLUG_RE.fullmatch(guide):
        return {
            "error": (
                f"{guide!r} is not a guide slug: expected lowercase letters, digits "
                "and hyphens, 1 to 80 characters (e.g. 'savings-plans-vs-reserved-instances')."
            ),
            "fallback": FALLBACK,
        }

    hit = _cached(guide)
    if hit is not None:
        fetched_at, document, age = hit
        return {
            "document": document,
            "fetched_at": fetched_at,
            "source": "cached",
            "cache_age_seconds": age,
            "note": _note(document),
        }

    url = FIGURES_URL.format(slug=guide)
    try:
        status, body = _fetch(url)
    except Exception as exc:  # noqa: BLE001 - the tool never raises
        return _failure(f"Could not reach {url}: {exc!r}")
    if status == 404:
        return _not_found(guide)
    if status != 200:
        return _failure(f"{url} returned HTTP {status}.")
    if len(body) > MAX_BODY_BYTES:
        return _failure(f"{url} is larger than {MAX_BODY_BYTES} bytes.")
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return _failure(f"{url} did not return valid JSON.")
    if not isinstance(document, dict) or "guide" not in document or "figures" not in document:
        return _failure(f"{url} returned JSON without the 'guide' and 'figures' keys.")

    fetched_at = _store(guide, document)
    return {
        "document": document,
        "fetched_at": fetched_at,
        "source": "live",
        "note": _note(document),
    }


__all__ = ["available_guides", "get_live_figures", "reset_cache"]
