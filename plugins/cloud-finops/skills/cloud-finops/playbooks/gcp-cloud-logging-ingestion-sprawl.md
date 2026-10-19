---
name: gcp-cloud-logging-ingestion-sprawl
scope: gcp
service: Cloud Logging
waste_category: overprovisioned
confidence: likely
---

# GCP Cloud Logging Ingestion Sprawl

## Problem

Cloud Logging charges once per GiB when a log entry is streamed into a log bucket,
and that charge includes the first 30 days of storage. The first 50 GiB per project
per month is free; retention beyond 30 days is billed per GiB-month on top. The
ingestion charge is the lever: on Google's list rates read 19 October 2026, one
extra month of retention costs about one fiftieth of what the entry cost to ingest,
so shortening retention (the pattern `finops-gcp.md` already covers) moves the bill
far less than not ingesting the entry at all.

Ingestion grows without anyone deciding it should. Every log routed to the `_Default`
bucket is ingested unless an exclusion filter drops it, and services write verbose
logs by default. The large step changes usually come from Data Access audit logs:
they are off by default except for some BigQuery services, but once someone enables
them at organisation or folder level with `allServices`, every project below inherits
them and cannot switch them off. Google's own page warns that their volume "can be
large".

## Symptoms

- Logging is one of the top two or three SKU groups on the GCP bill, after compute
- Ingested bytes grow faster than the workloads that produce them
- One or two log names (`cloudaudit.googleapis.com%2Fdata_access`, a chatty
  application log, load balancer request logs) carry most of the volume
- An organisation or folder IAM policy has an `auditConfigs` entry for `allServices`
  with `DATA_READ` or `DATA_WRITE`
- Many projects each sit just above the 50 GiB monthly free allotment, so the free
  tier hides the volume until the estate grows

## Detection

Find the log names that carry the volume. In Cloud Monitoring, the metric
`logging.googleapis.com/byte_count` counts bytes stored in at least one log bucket,
labelled by `log`; `logging.googleapis.com/billing/bytes_ingested` gives the billed
volume by `resource_type`. In Metrics Explorer, chart `byte_count`, aggregate with sum
over 30 days and group by `log`, per project. The same query in PromQL:

```promql
topk(20, sum by (project_id, log) (
  increase(logging_googleapis_com:byte_count[30d])
))
```

Find inherited Data Access audit logging (replace the placeholders):

```bash
gcloud organizations get-iam-policy <ORG_ID> --format=json | jq '.auditConfigs'
gcloud resource-manager folders get-iam-policy <FOLDER_ID> --format=json | jq '.auditConfigs'
```

An `allServices` entry with `DATA_READ` or `DATA_WRITE` at either level applies to
every project underneath.

## Fix

1. **Exclude before you shorten retention.** Add exclusion filters on the `_Default`
   sink for the high-volume, never-queried log names found above (debug-level
   application logs, health-check request logs). Exclusion filters "control which logs
   are ingested", and the services that send the logs see no error.
2. **Narrow Data Access audit logs.** Replace an organisation-wide `allServices`
   configuration with per-service entries for the services where data-access evidence
   is required (security or regulatory scope), and use `exemptedMembers` for
   high-volume service accounts whose reads add no audit value. Agree the scope with
   Security first.
3. **Route bulk logs to cheaper storage.** Logs kept for forensics, not for querying,
   can go through a sink to Cloud Storage or BigQuery, billed at that destination's
   rates, and be excluded from `_Default`.
4. **Then set retention.** Keep `_Default` at its 30-day default unless a requirement
   says otherwise. The `_Required` bucket (Admin Activity and System Event audit logs)
   has a fixed 400-day retention and no retention charge, and needs no action.

## Anti-pattern

- **Excluding VPC Flow Logs from Logging to save on ingestion.** When flow logs are
  sent to Logging, their generation charge is waived; if they are sent and then
  excluded, the generation charge applies again. Turn down flow-log sampling or scope
  at the subnet instead.
- **Switching Data Access audit logs off everywhere.** Some of them are compliance
  evidence; remove the blanket `allServices` setting, not the logging that a control
  depends on.

## See also

- `references/finops-gcp.md` - excessive retention of logs in Cloud Logging; GCP cost
  data and governance
- `playbooks/azure-log-analytics-sprawl.md` - the Azure counterpart
- `references/finops-waste-detection-playbooks.md` - "overprovisioned" category rubric

Sources: [Google Cloud Observability pricing](https://cloud.google.com/products/observability/pricing),
[configure Data Access audit logs](https://docs.cloud.google.com/logging/docs/audit/configure-data-access),
[routing and exclusions](https://docs.cloud.google.com/logging/docs/routing/overview),
[Logging metrics list](https://cloud.google.com/monitoring/api/metrics_gcp_i_o)
(all read 19 October 2026). Lead: a FinOps X 2026 practitioner talk (StitcherAI)
reporting an inherited "log everything" setting as one estate's second-largest cost
category after compute.

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
