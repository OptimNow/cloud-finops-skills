---
name: finops-focus
fcp_domain: "Understand Usage & Cost"
fcp_capability: "Data Ingestion"
fcp_capabilities_secondary: ["Reporting & Analytics", "Allocation", "Invoicing & Chargeback"]
fcp_phases: ["Inform"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance", "Security", "Platform Engineering"]
fcp_maturity_entry: "Crawl"
---

# FOCUS: multi-cloud cost data normalisation and ingestion

> What the FinOps Open Cost and Usage Specification (FOCUS) normalises and what it
> does not, the version ladder from 1.0 to 1.4, how AWS, Azure and GCP exports still
> diverge under the same version label (tags, precision, column sets, invoice
> timing), a pull-based ingestion architecture with workload identity federation,
> month-end finalisation and reconciliation, and a Crawl / Walk / Run path from a
> manual export to a governed multi-cloud dataset.

---

## Scope and routing

This file owns the **cross-provider layer**: what happens after each provider's
FOCUS export has landed and before the data is useful in one table. It does not
repeat what other references own:

| Question | Go to |
|---|---|
| How to enable the export on one provider (console path, prerequisites, IAM) | `finops-aws.md` (Data Exports for FOCUS 1.2), `finops-azure.md` (Cost Management exports, MCA union pattern), `finops-gcp.md` (BigQuery FOCUS export), `finops-oci.md` (FOCUS Reports) |
| Which cost column to use for showback, chargeback, invoice reconciliation (`BilledCost`, `EffectiveCost`, `ListCost`, `ContractedCost`) and the 0.5% drift rule | `finops-allocation-showback.md` |
| Mapping Kubernetes labels into the FOCUS `Tags` column | `finops-kubernetes.md` |
| The tag taxonomy itself (which keys, which values, enforcement) | `finops-tagging.md` |
| Standing up FOCUS exports during a migration or an acquisition | `finops-onboarding-workloads.md` |
| Warehouse modelling on top of the normalised table (conformed dimensions, dbt, semantic layer) | Deliberately out of scope. See the deferred `finops-cost-warehouse.md` entry in the repository roadmap |

**Who this is for.** A FinOps practitioner who has been asked for one cost view across
two or more providers, and the engineer who has to build the pipeline that produces it.
Maturity entry is Crawl: the first section of the Crawl / Walk / Run path assumes
nothing more than console access and a spreadsheet.

---

## What FOCUS normalises, and what it does not

FOCUS normalises **column names, column semantics and value vocabularies** across
providers. `BilledCost` means the same thing in an AWS, Azure or GCP export.
`ChargeCategory` draws from the same list of values. `ServiceCategory` puts an EC2
instance, an Azure VM and a Compute Engine VM in the same bucket. That is what makes a
cross-provider `GROUP BY` possible at all, and it is a real gain over the three native
schemas.

FOCUS does **not** normalise five things that the pipeline has to handle itself:

1. **Physical encoding.** The spec defines a `Tags` column as key-value pairs. It does
   not say whether that is a JSON string, a map or an array of structs. Each provider
   picked differently (see the divergence catalogue below).
2. **Numeric precision.** The spec allows providers to choose the precision of cost
   columns. Summing three providers' rows at three precisions and comparing the total
   to a two-decimal invoice is a design decision, not a given.
3. **The column set under a version label.** Providers ship columns from later versions
   early, drop a column they cannot populate, and add provider-specific `x_` columns.
   Two "FOCUS 1.0" exports are not guaranteed to have the same columns. Each provider
   publishes a conformance-gap report for exactly this reason: read it before freezing
   the target schema.
4. **Delivery mechanics.** Where the file lands, in what format, how often, when a
   month is final, and how corrections to a prior delivery are represented. Versions
   1.3 and 1.4 address finalisation and corrections in the spec; the providers have not
   all shipped those columns yet (status table below).
5. **Business meaning.** Which cost centre owns a row, which application it belongs to,
   whether it is shared. That comes from tags and from enrichment rules, not from the
   spec.

The practical consequence: FOCUS removes the column-mapping work, which used to be most
of a multi-cloud pipeline. It leaves the type-coercion, precision, schema-pinning and
finalisation work, which is smaller but is now the whole job.

---

## The version ladder

FOCUS has shipped roughly twice a year since 1.0. What each version added, with the
ratification date, is the context for reading any provider's "supports FOCUS 1.x"
claim.

| Version | Ratified | What it added that matters to a pipeline |
|---|---|---|
| **1.0** | June 2024 | The baseline: cost columns (`BilledCost`, `EffectiveCost`, `ListCost`, `ContractedCost`), charge classification, commitment discount columns, `Tags`, `ServiceCategory`. The version most third-party tools still target. |
| **1.1** | 7 November 2024 | `ServiceSubcategory`, `CommitmentDiscountQuantity` and `CommitmentDiscountUnit`, `CapacityReservationId` and `CapacityReservationStatus`, `SkuMeter`, `SkuPriceDetails`, and a `ProviderVersion` metadata property so a dataset states which spec version it targets. |
| **1.2** | 29 May 2025 | `InvoiceId` promoted from `x_InvoiceId`, `PricingCurrency` promoted from `x_PricingCurrency`, multi-currency and virtual-currency columns, unit-cost metrics, and a schema wide enough to carry SaaS and PaaS billing next to cloud. The version AWS and Azure target today and the first with a real reconciliation key. |
| **1.3** | 5 December 2025 | A separate Contract Commitment dataset, split cost allocation columns, Service Provider and Host Provider columns (the Provider and Publisher columns are deprecated and scheduled for removal from 1.4), and **recency metadata**: providers timestamp a dataset and flag whether a period is final or still subject to revision. |
| **1.4** | 4 June 2026 | Two datasets for reconciliation (**Invoice Detail**, recording charges as they appear on the issued invoice, and **Billing Period**, with issuer-set period boundaries and status), an Invoice Reconciliation feature that joins Invoice Detail to cost and usage on `InvoiceId`, a rounding-variance tolerance for high-precision cost data against two-decimal invoice totals, three named **correction-handling** styles (Replacement, Delta, Ledger) that a generator must document, and a Dataset Completeness attribute requiring native columns to be carried as `x_` columns rather than silently dropped. |

Sources: FOCUS 1.3 announcement
(<https://www.finops.org/insights/introducing-focus-1-3/>), FOCUS 1.4 announcement
(<https://www.finops.org/insights/introducing-focus-1-4/>), Dataset Completeness
attribute (<https://focus.finops.org/docs/specification/v1-4/attributes/dataset-completeness>).

**Two rules that follow from the ladder:**

- **Pin one version for the normalised table and coerce every provider to it.** Do not
  let the table be the union of whatever each provider ships. As of October 2026, 1.2 is
  the right pin for an AWS and Azure estate; 1.0 only if a third-party tool in the path
  cannot read 1.2.
- **Ask providers for 1.3 recency metadata and 1.4 reconciliation datasets by name.**
  Until a provider ships them, month-end finalisation is a guess (see the finalisation
  section). The FOCUS validator supports 1.3 conformance testing; 1.4 validator support
  was announced for later in Q3 2026.

---

## Per-provider export status

As of October 2026. Verify against the linked page before relying on any row; this
table is the most volatile content in the file.

| | AWS | Azure | GCP | OCI |
|---|---|---|---|---|
| **Mechanism** | Billing and Cost Management, Data Exports, table `FOCUS_1_2_AWS` | Cost Management, Exports, dataset "FOCUS" | Cloud Billing export to a Google-provided immutable BigQuery dataset, table `gcp_billing_export_focus_<BILLING_ACCOUNT_ID>` | Cost and Usage Reports, FOCUS Reports |
| **Lands in** | S3 | Blob Storage | BigQuery (then Cloud Storage if a file is needed) | Object Storage |
| **Formats** | Parquet, or CSV with gzip | CSV or Parquet | BigQuery table; export to Parquet, Avro, CSV or JSON via BigQuery | CSV (gzip) |
| **Cadence** | Table configuration `TIME_GRANULARITY`: hourly, daily or monthly line items; delivered on a schedule | Daily or monthly export runs | Continuous into BigQuery; a scheduled query sets the cadence of any downstream file | Daily |
| **Versions** | 1.2 generally available since 19 November 2025 (1.0 export remains, hourly only) | 1.0 GA since June 2024 (1.0r2 adds seconds to timestamps); 1.2 in preview with documented conformance gaps | Dedicated export in preview for 1.0 and 1.2, with a conformance-gap report; the earlier SQL view over the standard export mapped to 1.0 only | 1.0 |
| **Finalisation / 1.3 recency columns** | Not shipped | Not shipped | Not shipped | Not shipped |
| **Primary source** | <https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-focus-1-2-aws.html> | <https://learn.microsoft.com/en-us/azure/cost-management-billing/dataset-schema/cost-usage-details-focus> | <https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery-tables/focus-export> and <https://focus.finops.org/docs/implementation/data-generators/google-cloud/> | See `finops-oci.md` |

Three things to take from the table:

- **Parquet is available everywhere a file is involved.** Choose it. It carries column
  types, which is most of what the ETL would otherwise have to infer from CSV headers,
  and it is a tenth of the size of gzipped CSV for billing data.
- **Align the cadence to daily on day one.** AWS can produce hourly rows and GCP can be
  queried at any interval; a first pipeline that runs daily on all three providers is
  simpler to reconcile than one with three cadences. Move AWS to hourly only when a
  consumer (anomaly detection, intra-day unit economics) needs it.
- **GCP's status is the one that changed most recently** and is the row most references
  written before mid-2026 get wrong, describing GCP as a 1.0 SQL view only. The
  dedicated export is in preview and is the right target for a new pipeline, with the
  conformance report read first.

---

## The divergence catalogue

What a 2026 pipeline has to handle after the three exports land, in the order a build
hits them. Figures are from the provider schema pages linked above unless marked
otherwise.

### Tags: three physical shapes for one logical column

| Provider | How `Tags` arrives | What the ETL does |
|---|---|---|
| **Azure** | A single string containing a JSON object of key-value pairs | Parse the JSON; keys are case-sensitive and inherited tags are not distinguished from resource tags in this column |
| **AWS** | A map column (key to value). Data Exports lets a query project one key with dot notation, so some pipelines flatten the keys they need at export time | Either flatten at export time (fragile: a new tag key means a new export definition) or keep the map and explode it in the ETL |
| **GCP** | `x_Tags`: a repeated record (array of structs) with `Key`, `Value`, `x_Inherited` (boolean) and `x_Namespace` (string) | `UNNEST` in BigQuery or explode in the ETL. GCP is the only one of the three that tells you whether a tag was inherited, which is worth preserving as a column |

Target shape for the normalised table: one long table of `(row_id, tag_key, tag_value,
inherited)` next to the wide cost table, plus the five or six mandatory allocation keys
(`cost_centre`, `application`, `owner`, `environment`) pivoted into wide columns for
query convenience. Normalise key case at load. A `CostCenter` on Azure and a
`cost_center` on AWS must land as one key, which is a tagging-governance problem first
(`finops-tagging.md`) and an ETL rule second.

### Numeric precision

The spec allows each provider to choose precision. GCP's native export types cost
columns as BigQuery `NUMERIC` (nine decimal places). Azure and AWS exports arrive at
higher precision; practitioners report 18 decimal places on Azure and float64 on AWS
(reported in the Trident Consulting FinOps X 2026 talk on multi-cloud FOCUS ingestion,
not stated on the provider schema pages; verify in your own files).

Decide the clamp explicitly and write it down:

- **Store at the highest precision you receive**, as a decimal type, never as a float.
  Rounding at load is how a pipeline loses a cent per row and a few hundred dollars per
  month on a large estate, and the loss is invisible until an invoice reconciliation.
- **Round only at presentation**, and reconcile to the invoice with a stated tolerance.
  FOCUS 1.4 formalises this as a rounding-variance tolerance between high-precision
  cost data and two-decimal invoice totals; the 0.5% drift rule in
  `finops-allocation-showback.md` is the practitioner version of the same idea.
- **Do not cast to float to make three providers match.** Float64 cannot represent
  most decimal cents exactly; the mismatch shows up as a sum that is off by a fraction
  of a cent and a controller who no longer trusts the table.

### Column-set drift under one version label

The clearest 2026 example is Azure's **1.0** dataset:

- It **includes** `BillingAccountType` and `SubAccountType` without the `x_` prefix.
  Microsoft's own conformance report records that the two columns were introduced in
  the 1.0 dataset ahead of the specification and documented in a pending FOCUS change.
  A pipeline normalising to strict 1.0 drops them; one keeping them has to source them
  from the other providers or accept nulls.
- It has **no** `AvailabilityZone`. The column existed in Azure's 1.0-preview dataset
  and was removed at GA because Azure billing does not carry zone at the line-item
  level.
- It carries **52 `x_` columns** (columns 45 to 96 of the schema page): billing
  profile, invoice section, resource group, meter hierarchy, CSP partner credit,
  exchange rate, and the USD-converted cost columns. These are where the Azure-specific
  analysis lives; dropping them all to get a "clean" FOCUS table throws away the
  resource-group join and the pricing-currency conversion.
- The **1.2 preview** has its own documented conformance gaps (several columns present
  but null, such as the capacity reservation and `CommitmentDiscountQuantity` columns).

GCP's native export carries 18 provider-specific columns and publishes a conformance
report listing where the 1.2 table deviates. AWS's "FOCUS 1.2 with AWS columns" table
adds a smaller set of `x_` columns; read the table dictionary rather than assuming.

The rule: **pin the target version, then write one explicit column map per provider**
(keep, rename, derive, drop, with a reason for each drop). Keep the `x_` columns you
need as `x_` columns in the normalised table rather than renaming them into
standard-looking names. FOCUS 1.4's Dataset Completeness attribute pushes providers
the same way: a native column may be dropped only with a documented justification.

### Billing period and invoice timing

Two issues, one confirmed and one not:

- **Confirmed: `invoice.month` and usage month differ on GCP.** Google's standard export
  documentation states that the invoice month may differ from the usage month. Rows for
  usage at the end of a month can land on the next month's invoice. Reconcile GCP to
  the invoice on the invoice-month field, never on `ChargePeriodStart` alone.
- **Unconfirmed: GCP invoice boundaries fall on US Pacific time while AWS and Azure
  use UTC.** This is widely reported by practitioners and third-party tools (it was
  stated in the Trident Consulting FinOps X 2026 talk, and appears in several cost-tool
  integration guides), and Google's own BigQuery examples truncate usage days in
  `US/Pacific`. Google's schema documentation does not state a timezone for invoice
  cut-off. Treat it as a hypothesis to test on your own account: compare a month's
  `SUM(BilledCost)` grouped by invoice month with the console invoice, and if they
  disagree by roughly the last seven to eight hours of usage, the timezone is the
  cause and daylight-saving transitions will move it twice a year.

Whatever the cause, the pipeline rule is the same: carry `BillingPeriodStart`,
`BillingPeriodEnd` and `InvoiceId` through untouched, reconcile per provider on the
provider's own billing period, and only then present a calendar-month view with a
footnote that it is not the invoice view. FOCUS 1.4's Billing Period dataset exists
because issuer-set period boundaries do not always align with calendar months.

### Target engine conventions

Small and real: FOCUS column names are PascalCase (`BilledCost`). PostgreSQL folds
unquoted identifiers to lower case, so a `CREATE TABLE` from the FOCUS names produces
columns that every later query has to quote. Snowflake upper-cases unquoted identifiers.
BigQuery preserves case. Decide a casing convention for the normalised table at the
start (snake_case is the safest across engines) and apply it in one place in the ETL,
not in every downstream query.

---

## Ingestion architecture

### Shape

```
Azure Cost Management ─export─> Blob Storage ──┐
AWS Data Exports ────────export─> S3 ───────────┼─pull─> ETL (in one cloud) ─load─> normalised table
GCP Cloud Billing ───────export─> BigQuery ─────┘        │
                                   (scheduled query ─> Cloud Storage if a file is needed)
                                                         └─> enrichment (tags, business rules) ─> gold layer
```

Four decisions the diagram encodes:

1. **Pull, do not push.** Each provider writes to its own storage on its own schedule.
   One scheduled job in one place reads all three. Push designs (a Lambda on S3 put, a
   Blob trigger, a Pub/Sub on BigQuery) mean three triggers, three retry semantics and
   three places where a late file is handled differently.
2. **Run the ETL inside a cloud provider, not on a laptop or a generic VM.** The reason
   is identity (next subsection): a job running on a cloud compute identity can
   federate into the other two providers without a stored secret.
3. **Land raw, then normalise, then enrich.** The raw landing zone keeps every column
   the provider sent, including the `x_` set. Normalisation applies the per-provider
   column map and type coercion. Enrichment adds the business keys. Three layers,
   because each is re-run for a different reason: a late provider file re-runs
   landing, a schema-pin change re-runs normalisation, a cost-centre reorganisation
   re-runs enrichment only.
4. **One orchestrator.** A managed workflow service in the cloud that hosts the ETL
   (Cloud Composer or Workflows on GCP, Step Functions on AWS, Data Factory on Azure),
   or a Kubernetes CronJob on a cluster that already has idle capacity. The ETL itself
   is a few hundred lines in a dataframe library (Polars, pandas, or Spark above a few
   hundred million rows a month). Choose the one the team already runs.

### Identity: workload identity federation, no stored keys

A pipeline that reads billing data from three providers is a credential-management
problem before it is a data problem. The pattern that removes the problem:

- The ETL runs under a **cloud compute identity** (a GCP service account on Composer, an
  IAM role on an AWS task, a managed identity on Azure).
- That identity obtains a short-lived **OIDC token** from its own provider's metadata
  service and exchanges it for a short-lived credential at each of the other two
  providers: GCP Workload Identity Federation, AWS IAM OIDC identity provider plus
  `AssumeRoleWithWebIdentity`, Azure federated identity credentials on an app
  registration or a user-assigned managed identity.
- **No long-lived key exists anywhere.** Tokens expire within an hour. A leaked token is
  a short incident, not a rotation project across three consoles.

This is why "run the ETL in a cloud provider" is a hard rule and not a preference:
federation needs an issuer the other providers trust, and that issuer is the hosting
cloud's metadata service.

### Least privilege: the three reader roles

The pipeline reads an export. It never needs billing administration rights, and it never
needs write access to the source bucket.

| Provider | Role for the pipeline identity | Scope |
|---|---|---|
| Azure | `Storage Blob Data Reader` | The export container only, not the storage account |
| AWS | `AmazonS3ReadOnlyAccess`, or better, an inline policy with `s3:GetObject` and `s3:ListBucket` on the export bucket and prefix | The export bucket and prefix only |
| GCP | `roles/storage.objectViewer` on the export bucket, or `roles/bigquery.dataViewer` on the billing dataset if reading BigQuery directly | The dataset or bucket only |

Setting up the export itself needs more (Billing Account Costs Manager or
Administrator plus BigQuery Admin on GCP, for example). That is a one-time human action
with a privileged identity, not something the pipeline identity carries.

### Network

Restrict the export storage so it is reachable only from the pipeline: a private
endpoint on the Azure storage account, a VPC endpoint policy or bucket policy with a
source-VPC condition on S3, VPC Service Controls or a bucket IAM condition on GCS.
Billing data is a map of the estate and, with tags, of the organisation. It belongs
behind the same controls as any other sensitive dataset, which is a conversation to
have with Security before the first export is enabled, not after.

---

## Month-end finalisation and reconciliation

The question every pipeline eventually gets from Finance: "is last month final?" Until a
provider ships FOCUS 1.3 recency metadata, nothing in the export answers it, and the
pipeline has to infer.

**What actually happens at month end.** Providers keep writing rows for a closed month
for several days: late-arriving usage, credits, support charges, marketplace invoices,
commitment amortisation adjustments. A row delivered on the 3rd can change a total for
a month that the dashboard showed as closed on the 1st.

**The inference pattern that works:**

1. Keep every delivery of a billing period, not just the latest, with the delivery
   timestamp. On AWS and Azure each run overwrites the month's files (a Replacement
   style in 1.4 terms); on GCP the table is append-only with an export time per row.
   Snapshot the replaced files before overwriting them so a change between deliveries
   is visible.
2. Compute `SUM(BilledCost) GROUP BY provider, BillingPeriodStart` on every run and
   store the series. A period is treated as final when the sum has not moved across
   N consecutive deliveries (three daily deliveries is a common choice) **and** the
   provider's invoice for the period has been issued.
3. Reconcile on `InvoiceId` once the invoice exists. The sum of `BilledCost` for an
   `InvoiceId` must match the invoice to within the stated tolerance; the drift rule
   and the investigation path are in `finops-allocation-showback.md`.
4. Publish a **finalisation status per provider per period** next to the data, so a
   dashboard can show "AWS September final, Azure September provisional" rather than
   one undifferentiated number.

**What to ask providers for.** 1.3 recency metadata (a dataset last-updated timestamp
and a per-period completeness flag) would make step 2 unnecessary. 1.4's Invoice
Detail dataset would make step 3 a join instead of a manual match against a PDF. Neither
has shipped from AWS, Azure or GCP as of October 2026. Ask account teams for both by
name; provider roadmaps move on customer requests that cite the spec.

**Corrections.** 1.4 names three styles a generator may use and must document:
**Replacement** (a full new snapshot of the period), **Delta** (additional rows carrying
the net change) and **Ledger** (a reversal row and a re-entry row, keeping an audit
trail). A pipeline that assumes Replacement and receives Delta double-counts; one that
assumes Delta and receives Replacement loses history. Until providers document which
they use, the snapshot-every-delivery pattern in step 1 is the defence.

---

## Minimum viable schema

The spec has grown past a hundred columns across its datasets. A first pipeline does
not need them. The Crawl-stage table that answers the first year of questions:

| Column | Why it is in the minimum set |
|---|---|
| `ProviderName` | The partition key for everything |
| `BillingAccountId`, `SubAccountId`, `SubAccountName` | Hierarchy: payer and linked account, billing profile and subscription, billing account and project |
| `BillingPeriodStart`, `ChargePeriodStart`, `ChargePeriodEnd` | Invoice period and usage period, kept separate (see invoice timing above) |
| `InvoiceId` | The reconciliation key; null until the invoice is issued |
| `BilledCost`, `EffectiveCost` | Cash view and amortised view; `ListCost` and `ContractedCost` join at Walk when rate-optimisation measurement starts |
| `BillingCurrency` | Multi-currency estates will mix EUR and USD on day one |
| `ChargeCategory`, `ChargeClass` | Usage, purchase, tax, credit, adjustment; correction rows |
| `ServiceCategory`, `ServiceName` | The cross-provider grouping that makes FOCUS worth having |
| `RegionId` | Carbon, data-residency and egress analysis later; cheap to carry now |
| `ResourceId`, `ResourceType` | Join key to inventory and to the waste playbooks |
| `CommitmentDiscountId`, `CommitmentDiscountStatus` | Commitment coverage and utilisation without a second dataset |
| `Tags` (as the long table described above) | The allocation keys |
| Provider `x_` columns needed for a known join | Azure `x_ResourceGroupName` and `x_InvoiceSectionName`, AWS `x_` cost category columns, GCP `x_Inherited` on tags. Named individually, not "all of them" |

Everything else stays in the raw landing layer and is promoted when a consumer asks for
it. The temptation to promote all columns on day one produces a table nobody can
explain and a schema-pin that breaks every time a provider adds a column.

---

## Enrichment: where the business value is

A normalised FOCUS table is a prerequisite, not an outcome. It becomes useful when a
row can be attributed to a cost centre, an application and an owner, and that is what
tags are for. Two things the ingestion layer should do that the tag strategy alone
cannot:

- **Fill tag gaps by rule, and mark that you did.** Some resources cannot be tagged
  (certain managed-service sub-resources, data transfer rows, support charges, some
  marketplace lines). The enrichment layer derives an owner from context: the
  sub-account, the resource group, the Kubernetes namespace via the K8s mapping in
  `finops-kubernetes.md`, a naming convention. Add a `tag_source` column with values
  such as `resource`, `inherited`, `derived_from_account`, `derived_from_rule`,
  `unallocated`, so a chargeback report can state how much of a team's number is
  derived rather than declared. The unallocated share is a KPI in its own right
  (`finops-kpis-benchmarking.md`).
- **Stage the layers.** Raw (as delivered), normalised (pinned version, one column map
  per provider, typed, cased), enriched (business keys, tag_source, finalisation
  status). Call them bronze, silver and gold if the data team already uses that
  vocabulary; the point is that each layer is rebuilt for a different reason.

---

## Crawl, Walk, Run

### Crawl: one manual export per provider, one spreadsheet

- Enable the FOCUS export on each provider, Parquet, daily, 1.2 where available and 1.0
  on GCP if the 1.2 preview is not acceptable to the organisation.
- Download one month from each. Open the three files side by side. Build the
  per-provider column map by hand against the minimum viable schema above, noting the
  drops and the reasons.
- Load the minimum set into one table (DuckDB or a spreadsheet is enough at this stage)
  and produce `SUM(BilledCost) BY ProviderName, ServiceCategory` for one month.
  Reconcile each provider's sum to its invoice. Write down the differences; most are
  invoice-timing and a handful are precision.
- Output: a one-page note stating the target version, the column map, the known
  reconciliation gaps and the three tag keys that exist on all three providers.

### Walk: scheduled pipeline, identity federation, finalisation status

- Build the pull job in one cloud under a federated identity with the three reader
  roles. Daily. Raw, normalised and enriched layers.
- Add the snapshot-every-delivery pattern and the per-provider, per-period
  finalisation status.
- Publish a dashboard with the finalisation status visible on it, reconciled monthly on
  `InvoiceId`. This is the artefact that earns Finance's trust in the table.
- Extend the schema only on request from a named consumer.

### Run: a platform-agnostic cost dataset in the path of engineers

- Hourly AWS rows where anomaly detection needs them (`finops-anomaly-management.md`).
- Unit economics on top of the enriched layer, with denominators joined from
  application telemetry (`finops-kpis-benchmarking.md`).
- The waste playbooks run against the normalised table rather than per-provider
  consoles; the inventory-scoping queries in `finops-waste-detection-playbooks.md`
  assume FOCUS columns for exactly this reason.
- New providers (a SaaS vendor shipping a FOCUS export, a Kubernetes allocation tool
  emitting FOCUS rows) join by writing one more column map, not a new pipeline.

---

## Anti-patterns

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| Treating "all three support FOCUS 1.2" as "the three files have the same columns" | They do not; column-set drift under one label is the norm | Pin the version, write one column map per provider, read each conformance report |
| Casting every cost column to float so the providers match | Loses cents per row; sums stop matching invoices | Decimal at the highest precision received, round at presentation |
| Reconciling GCP to a calendar month on `ChargePeriodStart` | Invoice month and usage month differ on GCP | Reconcile on the provider's billing period and `InvoiceId` |
| Dropping all `x_` columns to get a "pure" FOCUS table | Throws away the resource-group join, the exchange rate, the inherited-tag flag | Keep the named `x_` columns the consumers need, as `x_` columns |
| Push triggers per provider | Three retry semantics, three late-file behaviours | One scheduled pull job |
| A service-account key file in the orchestrator's secret store | A long-lived cross-cloud billing credential | Workload identity federation from a cloud compute identity |
| Marking a month final on the 1st because the dashboard says so | Providers write into a closed month for days | Stable-sum-across-N-deliveries plus invoice issued, published as a status |
| Promoting every FOCUS column on day one | A table nobody can explain; a schema that breaks on every provider change | Minimum viable schema, promote on request |
| Treating the normalised table as the deliverable | It answers no business question on its own | Enrichment with `tag_source`, unallocated share tracked as a KPI |

---

## Further reading

- FOCUS specification and version documentation: <https://focus.finops.org/>
- FOCUS 1.3 announcement (contract commitments, split allocation, recency metadata):
  <https://www.finops.org/insights/introducing-focus-1-3/>
- FOCUS 1.4 announcement (Invoice Detail, Billing Period, correction handling, dataset
  completeness): <https://www.finops.org/insights/introducing-focus-1-4/>
- AWS Data Exports FOCUS 1.2 table dictionary:
  <https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-focus-1-2-aws.html>
  and the GA announcement:
  <https://aws.amazon.com/blogs/aws-cloud-financial-management/data-exports-for-focus-1-2-is-now-generally-available>
- Azure FOCUS cost and usage details schema (1.0, 1.0r2, 1.2 preview, with the full
  `x_` column list):
  <https://learn.microsoft.com/en-us/azure/cost-management-billing/dataset-schema/cost-usage-details-focus>
- GCP FOCUS export structure:
  <https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery-tables/focus-export>
  and the FOCUS project's Google Cloud data-generator page (version support and the
  conformance report): <https://focus.finops.org/docs/implementation/data-generators/google-cloud/>
- Lead for the divergence catalogue and the ingestion architecture: Arjun Kaushal,
  Trident Consulting, "Configuring Multi-Cloud FOCUS Data Ingestion", lightning talk,
  FinOps X 2026 (<https://www.youtube.com/watch?v=WawKDHXAdGI>). Mechanics claims above
  were checked against the provider pages; where a claim could not be confirmed
  primarily it is marked as such in the text.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
