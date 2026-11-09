#!/usr/bin/env python3
"""
check-prices.py - Compare the static list prices written in the skill with the
providers' current price lists.

Why: the references and playbooks carry mechanics, not prices, but a worked example
needs a number to be legible, so about fifty infrastructure list prices (a NAT
gateway hour, a gp3 GB-month, an App Service plan, the GKE cluster fee) sit in the
text as dated illustrative figures. AI token rates are routed to the AI Pricing Hub
and the OptimToken guide figures are served live by the connector, so neither is
checked here; nothing serves an infrastructure list price live, which is why they
were re-read by hand on 9 November 2026 and why this script exists.

What it does: reads scripts/price-manifest.yaml (one `prices:` entry per provider
SKU, one `figures:` entry per place a number is written), fetches each price from
the provider's own price list, applies the figure's derivation (730 hours a month,
1,000 GB a TB), compares with the number written in the file within the tolerance,
and prints a markdown report. A figure no API serves (a Snowflake storage tier read
from a PDF) is a `source: page` figure: never fetched, but aged against the date it
was read, and listed under "Check by hand" once it is older than `max_age_days`, so
the maintainer gets a reminder instead of silence. Exit codes:

  0  every figure within tolerance and no page-only figure past its age
  1  at least one figure drifted, or a page-only figure is due for a re-read
  2  a query failed, a manifest anchor no longer matches its file, or nothing
     could be checked, so a broken query is never read as "no drift"

What it never does: edit a content file. A drift is a proposal for the maintainer
(docs/DESIGN.md, "Content update pipeline", "Price drift check").

Modes:
  python scripts/check-prices.py                  live run, report on stdout
  python scripts/check-prices.py --output f.md    also write the report to a file
  python scripts/check-prices.py --offline        read scripts/fixtures/prices/
                                                  instead of the network (the CI run)
  python scripts/check-prices.py --record         live run that also rewrites the
                                                  fixtures of every price it could read
  python scripts/check-prices.py --provider aws   restrict to one provider

Sources and credentials, all optional:
  aws    AWS Price List API through boto3 (endpoint us-east-1); any credential the
         boto3 chain finds, pricing:GetProducts is the only action needed
  azure  Azure Retail Prices API, public, no credential
  gcp    Cloud Billing Catalog API with GOOGLE_API_KEY (Cloud Billing API enabled),
         or, without a key, the pricing page the manifest names, parsed by regex
A provider whose credential is missing is reported as skipped, not failed; the run
exits 2 for that reason only when nothing at all could be checked.

Wired into .github/workflows/price-drift.yml (weekly, live) and ci.yml (--offline).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "scripts" / "price-manifest.yaml"
FIXTURES_DIR = REPO_ROOT / "scripts" / "fixtures" / "prices"

DEFAULT_TOLERANCE = 0.02
DEFAULT_MAX_AGE_DAYS = 90
PROVIDERS = ("aws", "azure", "gcp")
AWS_PRICING_REGION = "us-east-1"
AZURE_RETAIL_URL = "https://prices.azure.com/api/retail/prices"
GCP_CATALOG_URL = "https://cloudbilling.googleapis.com/v1/{service}/skus"
HTTP_TIMEOUT = 60
USER_AGENT = "cloud-finops-skills price-drift check (+https://github.com/OptimNow/cloud-finops-skills)"

EXIT_OK, EXIT_DRIFT, EXIT_FAILED = 0, 1, 2


# --------------------------------------------------------------------------- manifest


@dataclass
class Price:
    name: str
    provider: str
    unit: str
    query: dict[str, Any]
    note: str = ""


@dataclass
class Figure:
    file: str
    anchor: str
    figure: str
    price: str = ""  # empty for a page-only figure
    derivation: str | None = None
    other: str | None = None
    tolerance: float = DEFAULT_TOLERANCE
    note: str = ""
    source: str = "api"  # api: compared with a fetched price; page: aged, never fetched
    url: str = ""
    read_on: dt.date | None = None
    max_age_days: int = DEFAULT_MAX_AGE_DAYS
    line: int = 0

    @property
    def written(self) -> float:
        return float(self.figure.replace(",", ""))

    @property
    def due_on(self) -> dt.date | None:
        return self.read_on + dt.timedelta(days=self.max_age_days) if self.read_on else None


@dataclass
class Fetch:
    """The outcome of reading one price."""

    status: str  # ok | failed | skipped
    value: float | None = None
    detail: str = ""
    method: str = ""
    raw: Any = None


@dataclass
class Result:
    figure: Figure
    expected: float | None
    live: float | None
    drift: bool
    relative: float | None


class ManifestError(Exception):
    pass


def load_manifest(path: Path) -> tuple[dict[str, Price], list[Figure]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ManifestError(f"{path} does not exist") from None
    if not isinstance(data, dict) or "prices" not in data or "figures" not in data:
        raise ManifestError(f"{path.name} needs a `prices:` mapping and a `figures:` list")

    prices: dict[str, Price] = {}
    for name, body in (data["prices"] or {}).items():
        if not isinstance(body, dict):
            raise ManifestError(f"price {name}: expected a mapping")
        missing = [k for k in ("provider", "unit", "query") if k not in body]
        if missing:
            raise ManifestError(f"price {name}: missing {', '.join(missing)}")
        if body["provider"] not in PROVIDERS:
            raise ManifestError(f"price {name}: provider must be one of {', '.join(PROVIDERS)}")
        validate_query(name, body["provider"], body["query"])
        prices[name] = Price(
            name=name,
            provider=body["provider"],
            unit=str(body["unit"]),
            query=body["query"],
            note=str(body.get("note", "")),
        )

    figures: list[Figure] = []
    for i, body in enumerate(data["figures"] or [], start=1):
        if not isinstance(body, dict):
            raise ManifestError(f"figure {i}: expected a mapping")
        where = f"figure {i} ({body.get('file', '?')})"
        missing = [k for k in ("file", "anchor", "figure") if k not in body]
        if missing:
            raise ManifestError(f"{where}: missing {', '.join(missing)}")
        figure = str(body["figure"])
        try:
            float(figure.replace(",", ""))
        except ValueError:
            raise ManifestError(f"{where}: {figure!r} is not a number as written") from None
        source = str(body.get("source", "api"))
        if source == "page":
            figures.append(parse_page_figure(where, body, figure))
            continue
        if source != "api":
            raise ManifestError(f"{where}: source must be api (the default) or page")
        if "price" not in body:
            raise ManifestError(f"{where}: missing price (or `source: page` with url and read_on)")
        if body["price"] not in prices:
            raise ManifestError(f"{where}: unknown price {body['price']!r}")
        other = body.get("other")
        if other is not None and other not in prices:
            raise ManifestError(f"{where}: unknown other price {other!r}")
        derivation = body.get("derivation")
        if derivation is not None:
            tokenise_derivation(str(derivation))  # raises on a bad expression
            if "other" in str(derivation) and other is None:
                raise ManifestError(f"{where}: derivation uses `other` without an `other:` price")
        figures.append(
            Figure(
                file=str(body["file"]),
                anchor=str(body["anchor"]),
                figure=figure,
                price=body["price"],
                derivation=str(derivation) if derivation is not None else None,
                other=other,
                tolerance=float(body.get("tolerance", DEFAULT_TOLERANCE)),
                note=str(body.get("note", "")),
            )
        )
    return prices, figures


def parse_page_figure(where: str, body: dict, figure: str) -> Figure:
    """A figure no API serves: anchored like the others, aged instead of compared."""
    for key in ("price", "derivation", "other", "tolerance"):
        if key in body:
            raise ManifestError(f"{where}: a page-only figure takes no {key}")
    missing = [k for k in ("url", "read_on") if k not in body]
    if missing:
        raise ManifestError(f"{where}: a page-only figure needs {', '.join(missing)}")
    url = str(body["url"])
    if not url.startswith(("http://", "https://")):
        raise ManifestError(f"{where}: url must start with http:// or https://")
    read_on = body["read_on"]
    if isinstance(read_on, dt.datetime):
        read_on = read_on.date()
    if not isinstance(read_on, dt.date):
        try:
            read_on = dt.date.fromisoformat(str(read_on))
        except ValueError:
            raise ManifestError(f"{where}: read_on must be a date written YYYY-MM-DD") from None
    max_age = body.get("max_age_days", DEFAULT_MAX_AGE_DAYS)
    if isinstance(max_age, bool) or not isinstance(max_age, int) or max_age <= 0:
        raise ManifestError(f"{where}: max_age_days must be a positive whole number of days")
    return Figure(
        file=str(body["file"]),
        anchor=str(body["anchor"]),
        figure=figure,
        source="page",
        url=url,
        read_on=read_on,
        max_age_days=max_age,
        note=str(body.get("note", "")),
    )


def validate_query(name: str, provider: str, query: Any) -> None:
    if not isinstance(query, dict):
        raise ManifestError(f"price {name}: query must be a mapping")
    if provider == "aws":
        if "service_code" not in query or not isinstance(query.get("filters"), dict):
            raise ManifestError(f"price {name}: an aws query needs service_code and a filters mapping")
    elif provider == "azure":
        if not isinstance(query.get("filter"), str):
            raise ManifestError(f"price {name}: an azure query needs a filter string (OData)")
    elif provider == "gcp":
        cat, page = query.get("catalog"), query.get("page")
        if cat is None and page is None:
            raise ManifestError(f"price {name}: a gcp query needs a catalog block, a page block or both")
        if cat is not None and not all(k in cat for k in ("service", "description")):
            raise ManifestError(f"price {name}: catalog needs service and description")
        if page is not None and not all(k in page for k in ("url", "regex")):
            raise ManifestError(f"price {name}: page needs url and regex")
        if page is not None:
            try:
                if re.compile(page["regex"]).groups != 1:
                    raise ManifestError(f"price {name}: the page regex needs exactly one capturing group")
            except re.error as exc:
                raise ManifestError(f"price {name}: bad page regex ({exc})") from None


DERIVATION_TOKEN = re.compile(r"\s*(rate\b|other\b|\d+(?:\.\d+)?|[+\-*/()])")


def tokenise_derivation(expr: str) -> None:
    """Accept only numbers, + - * / ( ) and the names `rate` and `other`."""
    if "**" in expr:
        raise ManifestError(f"derivation {expr!r}: no exponent, the four operations only")
    pos = 0
    while pos < len(expr):
        m = DERIVATION_TOKEN.match(expr, pos)
        if not m:
            raise ManifestError(f"derivation {expr!r}: unexpected text at {expr[pos:pos + 10]!r}")
        pos = m.end()
    if not expr.strip():
        raise ManifestError("derivation is empty")


def derive(expr: str | None, rate: float, other: float | None) -> float:
    if expr is None:
        return rate
    tokenise_derivation(expr)
    return float(eval(compile(expr, "<derivation>", "eval"), {"__builtins__": {}}, {"rate": rate, "other": other}))  # noqa: S307 - tokenised above


# --------------------------------------------------------------------------- files


def locate(fig: Figure) -> str | None:
    """Find the anchor line and confirm the written figure still sits on it.

    Returns an error message, or None when the figure is where the manifest says.
    """
    path = REPO_ROOT / fig.file
    if not path.is_file():
        return f"{fig.file}: file not found"
    lines = path.read_text(encoding="utf-8").splitlines()
    hits = [i + 1 for i, line in enumerate(lines) if fig.anchor in line]
    if len(hits) != 1:
        return f"{fig.file}: anchor {fig.anchor!r} found {len(hits)} times (needs exactly one line)"
    pattern = re.compile(r"\$\s?" + re.escape(fig.figure) + r"(?!\d|[.,]\d)")
    if not pattern.search(lines[hits[0] - 1]):
        return f"{fig.file}:{hits[0]}: ${fig.figure} is no longer on the anchor line (edit the manifest figure too)"
    fig.line = hits[0]
    return None


# --------------------------------------------------------------------------- shared


def one_distinct(prices: list[float], what: str) -> float:
    """The single list price in a set of candidates.

    Zero-priced rows (a free first tier, a Capacity Block placeholder) are dropped
    when a non-zero row exists. Several distinct non-zero values mean the query is
    too loose, which is an error for the manifest author, not a price.
    """
    nonzero = [p for p in prices if p > 0]
    candidates = nonzero or prices
    distinct = sorted({round(p, 10) for p in candidates})
    if not distinct:
        raise LookupError(f"no price in the response ({what})")
    if len(distinct) > 1:
        raise LookupError(f"ambiguous, {len(distinct)} distinct prices {distinct[:6]} ({what}); tighten the query")
    return distinct[0]


def http_get(url: str, *, params: dict | None = None, headers: dict | None = None) -> Any:
    import requests  # lazy: --offline needs neither requests nor boto3

    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    response = requests.get(url, params=params, headers=h, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    return response


# --------------------------------------------------------------------------- aws


def aws_credentials_present() -> bool:
    try:
        import boto3
    except ImportError:
        return False
    return boto3.Session().get_credentials() is not None


def aws_fetch(query: dict) -> list[dict]:
    import boto3

    client = boto3.client("pricing", region_name=AWS_PRICING_REGION)
    filters = [{"Type": "TERM_MATCH", "Field": k, "Value": str(v)} for k, v in query["filters"].items()]
    kwargs: dict[str, Any] = {"ServiceCode": query["service_code"], "Filters": filters, "MaxResults": 100}
    products: list[dict] = []
    while True:
        response = client.get_products(**kwargs)
        products.extend(json.loads(s) for s in response.get("PriceList", []))
        token = response.get("NextToken")
        if not token or len(products) >= 500:
            break
        kwargs["NextToken"] = token
    return [aws_trim(p, query.get("term", "OnDemand")) for p in products]


def aws_trim(product: dict, term: str) -> dict:
    """Keep what the extraction reads, so a fixture stays small and legible."""
    return {
        "product": {"sku": product.get("product", {}).get("sku"), "attributes": product.get("product", {}).get("attributes", {})},
        "terms": {term: product.get("terms", {}).get(term, {})},
    }


def aws_extract(products: list[dict], query: dict) -> float:
    term = query.get("term", "OnDemand")
    begin = str(query.get("begin_range", "0"))
    prices: list[float] = []
    ranges_seen: set[str] = set()
    for product in products:
        terms = product.get("terms", {})
        if term == "FlatRate":
            for plan in terms.get("FlatRate", {}).get("plans", []):
                usd = plan.get("subscriptionPrice", {}).get("pricePerUnit", {}).get("USD")
                if usd is not None:
                    prices.append(float(usd))
            continue
        for offer in terms.get(term, {}).values():
            dims = list(offer.get("priceDimensions", {}).values())
            if len(dims) > 1:
                ranges_seen.update(str(d.get("beginRange", "0")) for d in dims)
                dims = [d for d in dims if str(d.get("beginRange", "0")) == begin]
            for dim in dims:
                usd = dim.get("pricePerUnit", {}).get("USD")
                if usd is not None:
                    prices.append(float(usd))
    what = f"{len(products)} product(s), term {term}"
    if ranges_seen:
        what += f", tiers begin at {sorted(ranges_seen, key=lambda r: float(r))}, begin_range {begin}"
    return one_distinct(prices, what)


def aws_source(query: dict) -> str:
    keys = ("usagetype", "instanceType", "operation", "fromLocation", "toLocation")
    bits = [f"{k}={query['filters'][k]}" for k in keys if k in query["filters"]]
    return f"AWS Price List, {query['service_code']}, " + ", ".join(bits)


# --------------------------------------------------------------------------- azure


def azure_fetch(query: dict) -> list[dict]:
    items: list[dict] = []
    url: str | None = AZURE_RETAIL_URL
    params: dict | None = {"$filter": query["filter"]}
    while url:
        body = http_get(url, params=params).json()
        items.extend(body.get("Items", []))
        url = body.get("NextPageLink")
        params = None
        if len(items) >= 1000:
            break
    keep = ("armRegionName", "productName", "skuName", "meterName", "unitOfMeasure", "retailPrice", "type", "reservationTerm", "tierMinimumUnits")
    return [{k: it.get(k) for k in keep if k in it} for it in items]


def azure_extract(items: list[dict], query: dict) -> float:
    term = query.get("reservation_term")
    tier = query.get("tier_minimum_units")  # the tierMinimumUnits row to read when one meter has several
    selected = [
        it
        for it in items
        if (term is None or it.get("reservationTerm") == term)
        and (tier is None or float(it.get("tierMinimumUnits") or 0) == float(tier))
    ]
    what = f"{len(items)} item(s)" + (f", reservation term {term}" if term else "") + (f", tier from {tier} units" if tier is not None else "")
    return one_distinct([float(it["retailPrice"]) for it in selected if "retailPrice" in it], what)


def azure_source(query: dict) -> str:
    flt = query["filter"]
    return "Azure Retail Prices, " + (flt if len(flt) <= 110 else flt[:107] + "...")


# --------------------------------------------------------------------------- gcp


def gcp_fetch(query: dict, api_key: str | None) -> Fetch:
    catalog, page = query.get("catalog"), query.get("page")
    if catalog is not None and api_key:
        skus: list[dict] = []
        params: dict[str, Any] = {"pageSize": 5000}
        url = GCP_CATALOG_URL.format(service=catalog["service"])
        while True:
            body = http_get(url, params=params, headers={"x-goog-api-key": api_key}).json()
            for sku in body.get("skus", []):
                if sku.get("description") != catalog["description"]:
                    continue
                region = catalog.get("region")
                if region and region not in sku.get("serviceRegions", []) and "global" not in sku.get("serviceRegions", []):
                    continue
                skus.append({k: sku.get(k) for k in ("skuId", "description", "serviceRegions", "pricingInfo")})
            token = body.get("nextPageToken")
            if not token:
                break
            params["pageToken"] = token
        return Fetch(status="ok", method="catalog", raw={"method": "catalog", "skus": skus})
    if page is not None:
        text = http_get(page["url"]).text
        match = re.search(page["regex"], text)
        if not match:
            raise LookupError(f"regex {page['regex']!r} matched nothing on {page['url']}")
        start, end = max(0, match.start() - 200), min(len(text), match.end() + 200)
        return Fetch(status="ok", method="page", raw={"method": "page", "url": page["url"], "snippet": text[start:end]})
    return Fetch(status="skipped", detail="skipped: no credentials (GOOGLE_API_KEY unset and no pricing page in the manifest)")


def gcp_extract(raw: dict, query: dict) -> float:
    if raw.get("method") == "catalog":
        catalog = query["catalog"]
        factor = float(catalog.get("unit_factor", 1))
        start = float(catalog.get("start_usage_amount", 0))
        prices: list[float] = []
        for sku in raw.get("skus", []):
            for info in sku.get("pricingInfo", [])[:1]:
                for tier in info.get("pricingExpression", {}).get("tieredRates", []):
                    if float(tier.get("startUsageAmount", 0)) != start:
                        continue
                    unit_price = tier.get("unitPrice", {})
                    prices.append(float(unit_price.get("units", 0) or 0) + float(unit_price.get("nanos", 0) or 0) / 1e9)
        value = one_distinct(prices, f"{len(raw.get('skus', []))} sku(s) named {catalog['description']!r}")
        return value * factor
    page = query["page"]
    match = re.search(page["regex"], raw.get("snippet", ""))
    if not match:
        raise LookupError("the recorded page snippet no longer matches the regex")
    return float(match.group(1).replace(",", "")) * float(page.get("unit_factor", 1))


def gcp_source(query: dict, method: str) -> str:
    if method == "catalog":
        cat = query["catalog"]
        return f"Google Cloud Billing Catalog, {cat['description']}" + (f", {cat['region']}" if cat.get("region") else "")
    return f"Google pricing page, {query['page']['url']}"


# --------------------------------------------------------------------------- orchestration


def read_price(price: Price, *, offline: bool, aws_ok: bool, gcp_key: str | None) -> Fetch:
    if offline:
        fixture = FIXTURES_DIR / f"{price.name}.json"
        if not fixture.is_file():
            return Fetch(status="failed", detail=f"no fixture at scripts/fixtures/prices/{price.name}.json (run --record with credentials)")
        try:
            recorded = json.loads(fixture.read_text(encoding="utf-8"))
            raw = recorded["raw"]
            method = recorded.get("method", "")
            value = extract(price, raw)
        except (LookupError, KeyError, ValueError, json.JSONDecodeError) as exc:
            return Fetch(status="failed", detail=f"fixture: {exc}")
        return Fetch(status="ok", value=value, method=method, raw=raw, detail=f"fixture recorded {recorded.get('recorded', '?')}")

    try:
        if price.provider == "aws":
            if not aws_ok:
                return Fetch(status="skipped", detail="skipped: no credentials (no AWS credential in the boto3 chain)")
            raw = aws_fetch(price.query)
            return Fetch(status="ok", value=aws_extract(raw, price.query), method="price-list", raw=raw)
        if price.provider == "azure":
            raw = azure_fetch(price.query)
            return Fetch(status="ok", value=azure_extract(raw, price.query), method="retail-prices", raw=raw)
        fetched = gcp_fetch(price.query, gcp_key)
        if fetched.status != "ok":
            return fetched
        fetched.value = gcp_extract(fetched.raw, price.query)
        return fetched
    except LookupError as exc:
        return Fetch(status="failed", detail=str(exc))
    except Exception as exc:  # network, auth, JSON shape: anything that is not a price
        return Fetch(status="failed", detail=f"{type(exc).__name__}: {str(exc)[:200]}")


def extract(price: Price, raw: Any) -> float:
    if price.provider == "aws":
        return aws_extract(raw, price.query)
    if price.provider == "azure":
        return azure_extract(raw, price.query)
    return gcp_extract(raw, price.query)


def source_of(price: Price, fetch: Fetch) -> str:
    if price.provider == "aws":
        return aws_source(price.query)
    if price.provider == "azure":
        return azure_source(price.query)
    return gcp_source(price.query, fetch.method)


def record_fixture(price: Price, fetch: Fetch, today: str) -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "price": price.name,
        "provider": price.provider,
        "recorded": today,
        "method": fetch.method,
        "live_value": fetch.value,
        "query": price.query,
        "raw": fetch.raw,
    }
    (FIXTURES_DIR / f"{price.name}.json").write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def compare(fig: Figure, fetches: dict[str, Fetch]) -> Result | None:
    fetch = fetches[fig.price]
    if fetch.status != "ok" or fetch.value is None:
        return None
    other_value = None
    if fig.other is not None:
        other_fetch = fetches[fig.other]
        if other_fetch.status != "ok" or other_fetch.value is None:
            return None
        other_value = other_fetch.value
    expected = derive(fig.derivation, fetch.value, other_value)
    if expected == 0:
        return Result(fig, expected, fetch.value, drift=fig.written != 0, relative=None)
    relative = abs(fig.written - expected) / abs(expected)
    return Result(fig, expected, fetch.value, drift=relative > fig.tolerance, relative=relative)


def fmt(value: float) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 100:
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    if abs(value) >= 1:
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return f"{value:.6f}".rstrip("0").rstrip(".")


def build_report(
    *,
    today: dt.date,
    mode: str,
    offline: bool,
    prices: dict[str, Price],
    figures: list[Figure],
    fetches: dict[str, Fetch],
    results: list[Result],
    anchor_errors: list[str],
) -> tuple[str, int]:
    checked = [r for r in results if r is not None]
    drifts = [r for r in checked if r.drift]
    failed = [(n, f) for n, f in fetches.items() if f.status == "failed"]
    skipped = [(n, f) for n, f in fetches.items() if f.status == "skipped"]
    ok_prices = [(n, f) for n, f in fetches.items() if f.status == "ok"]
    api_figures = [fig for fig in figures if fig.source == "api"]
    unverified = [fig for fig in api_figures if fetches[fig.price].status != "ok" or (fig.other and fetches[fig.other].status != "ok")]
    page_figures = [fig for fig in figures if fig.source == "page" and fig.line]
    # Aging is a live-run concern: the CI offline run must not go red on a calendar date.
    aged = [] if offline else [fig for fig in page_figures if (today - fig.read_on).days > fig.max_age_days]

    by_provider = {p: sum(1 for n, f in ok_prices if prices[n].provider == p) for p in PROVIDERS}
    lines: list[str] = []
    lines.append(f"# Price drift check - {today.isoformat()}")
    lines.append("")
    lines.append(
        f"Mode: {mode}. {len(checked)} figure(s) compared against {len(ok_prices)} live price(s) "
        f"(aws {by_provider['aws']}, azure {by_provider['azure']}, gcp {by_provider['gcp']}). "
        f"Drift: {len(drifts)}. Failed queries: {len(failed)}. Skipped for credentials: {len(skipped)}. "
        f"Manifest errors: {len(anchor_errors)}. Page-only figures: {len(page_figures)} watched, "
        + (f"{len(aged)} past their age." if not offline else "not aged offline.")
    )
    lines.append("")

    lines.append("## Drift")
    lines.append("")
    if drifts:
        lines.append("Each row is a proposal: re-read the figure on the provider's page, change the number and its date in the file, then the `figure` field in `scripts/price-manifest.yaml`. Nothing here edits a content file.")
        lines.append("")
        lines.append("| File | Line | Written | Expected from live | Live rate | Source |")
        lines.append("|---|---|---|---|---|---|")
        for r in sorted(drifts, key=lambda r: (r.figure.file, r.figure.line)):
            fig = r.figure
            deriv = f" ({fig.derivation})" if fig.derivation else ""
            pct = f" ({r.relative:.1%} off)" if r.relative is not None else ""
            lines.append(
                f"| `{fig.file}` | {fig.line} | ${fig.figure} | ${fmt(r.expected)}{deriv}{pct} "
                f"| ${fmt(r.live)} {prices[fig.price].unit} | {source_of(prices[fig.price], fetches[fig.price])} |"
            )
    else:
        lines.append("No drift: every compared figure is within its tolerance.")
    lines.append("")

    if aged:
        lines.append("## Check by hand")
        lines.append("")
        lines.append("No API serves these figures, so they are not fetched; each one was read from the page below longer ago than its `max_age_days` allows. Re-read it there, change the number and its date in the file if they moved, and set `read_on` in the manifest to today's date either way.")
        lines.append("")
        lines.append("| File | Line | Figure | Read on | Age | URL |")
        lines.append("|---|---|---|---|---|---|")
        for fig in sorted(aged, key=lambda f: (f.file, f.line)):
            age = (today - fig.read_on).days
            lines.append(f"| `{fig.file}` | {fig.line} | ${fig.figure} | {fig.read_on.isoformat()} | {age} days (limit {fig.max_age_days}) | {fig.url} |")
        lines.append("")

    if anchor_errors:
        lines.append("## Manifest out of step with the files")
        lines.append("")
        lines.append("The figure or its anchor moved without the manifest following. Fix the manifest entry (or the file) before reading the rest.")
        lines.append("")
        lines.extend(f"- {e}" for e in anchor_errors)
        lines.append("")

    if failed:
        lines.append("## Failed queries")
        lines.append("")
        lines.append("A failed query is not a verified price. Until it is fixed, the figures below it are unverified.")
        lines.append("")
        lines.append("| Price | Provider | Error |")
        lines.append("|---|---|---|")
        for name, f in failed:
            lines.append(f"| `{name}` | {prices[name].provider} | {f.detail.replace('|', '/')} |")
        lines.append("")

    if skipped:
        lines.append("## Skipped: no credentials")
        lines.append("")
        for name, f in skipped:
            lines.append(f"- `{name}` ({prices[name].provider}): {f.detail}")
        lines.append("")

    if unverified:
        lines.append(f"{len(unverified)} figure(s) left unverified by the failed or skipped prices above.")
        lines.append("")

    lines.append("<details>")
    lines.append(f"<summary>Prices read ({len(ok_prices)})</summary>")
    lines.append("")
    lines.append("| Price | Live value | Unit | Figures | Source |")
    lines.append("|---|---|---|---|---|")
    for name, f in sorted(ok_prices):
        n_fig = sum(1 for fig in figures if fig.price == name or fig.other == name)
        lines.append(f"| `{name}` | {fmt(f.value)} | {prices[name].unit} | {n_fig} | {source_of(prices[name], f)} |")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    if page_figures:
        lines.append("<details>")
        lines.append(f"<summary>Page-only figures watched ({len(page_figures)})</summary>")
        lines.append("")
        lines.append("| File | Line | Figure | Read on | Due | URL |")
        lines.append("|---|---|---|---|---|---|")
        for fig in sorted(page_figures, key=lambda f: (f.file, f.line)):
            lines.append(f"| `{fig.file}` | {fig.line} | ${fig.figure} | {fig.read_on.isoformat()} | {fig.due_on.isoformat()} | {fig.url} |")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    if anchor_errors or failed:
        code = EXIT_FAILED
    elif not ok_prices:
        code = EXIT_FAILED
        lines.append("Nothing could be checked: every provider was skipped. Add at least one credential, or check that the Azure Retail Prices API is reachable.")
        lines.append("")
    elif drifts or aged:
        code = EXIT_DRIFT
    else:
        code = EXIT_OK
    return "\n".join(lines), code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare the list prices written in the skill with the providers' price lists.")
    parser.add_argument("--offline", action="store_true", help="read scripts/fixtures/prices/ instead of the network")
    parser.add_argument("--record", action="store_true", help="live run that also rewrites the fixtures it could read")
    parser.add_argument("--output", type=Path, help="also write the markdown report to this file")
    parser.add_argument("--provider", choices=PROVIDERS, help="restrict the run to one provider")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.offline and args.record:
        parser.error("--offline and --record exclude each other")

    today = dt.datetime.now(dt.timezone.utc).date()
    try:
        prices, figures = load_manifest(args.manifest)
    except ManifestError as exc:
        print(f"FAIL: manifest: {exc}", file=sys.stderr)
        return EXIT_FAILED
    except yaml.YAMLError as exc:
        print(f"FAIL: manifest is not valid YAML: {exc}", file=sys.stderr)
        return EXIT_FAILED

    if args.provider:
        prices = {n: p for n, p in prices.items() if p.provider == args.provider}
        figures = [f for f in figures if f.source == "page" or (f.price in prices and (f.other is None or f.other in prices))]

    anchor_errors = [e for e in (locate(fig) for fig in figures) if e]

    aws_ok = False if args.offline or args.provider not in (None, "aws") else aws_credentials_present()
    gcp_key = os.environ.get("GOOGLE_API_KEY") or None

    fetches: dict[str, Fetch] = {}
    for name, price in prices.items():
        fetches[name] = read_price(price, offline=args.offline, aws_ok=aws_ok, gcp_key=gcp_key)
        f = fetches[name]
        tag = {"ok": "ok     ", "failed": "FAILED ", "skipped": "skipped"}[f.status]
        value = f"{fmt(f.value)} {price.unit}" if f.value is not None else f.detail
        print(f"{tag} {name}: {value}", file=sys.stderr)
        if args.record and f.status == "ok":
            record_fixture(price, f, today.isoformat())

    results = [r for r in (compare(fig, fetches) for fig in figures if fig.line and fig.source == "api") if r is not None]
    mode = "offline (fixtures)" if args.offline else ("live, fixtures recorded" if args.record else "live")
    report, code = build_report(
        today=today,
        mode=mode,
        offline=args.offline,
        prices=prices,
        figures=figures,
        fetches=fetches,
        results=results,
        anchor_errors=anchor_errors,
    )
    print(report)
    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8", newline="\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
