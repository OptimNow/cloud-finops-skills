---
name: finops-anomaly-management
fcp_domain: "Understand Usage & Cost"
fcp_capability: "Anomaly Management"
fcp_capabilities_secondary: ["Budgeting"]
fcp_phases: ["Inform", "Operate"]
fcp_personas_primary: ["FinOps Practitioner"]
fcp_personas_collaborating: ["Engineering", "Finance", "Security"]
fcp_maturity_entry: "Crawl"
---

# FinOps Anomaly Management

> Anomaly management is the entry-point capability of the Inform phase. Without it,
> teams discover cost incidents on the next invoice instead of within the day they
> happen, and structural optimisation work runs on top of an unstable baseline.
> This file covers native tooling per cloud, threshold philosophy, the layered-detection
> pattern that catches masked anomalies, and the integration points that turn an alert
> into action.

---

## Why anomaly management comes first

Cost anomalies are the cheapest signal a FinOps practice gets. An unsanctioned workload
that costs $50K/month is visible the day it appears in CloudWatch, not the day finance
notices the invoice variance. The gap between those two moments is what anomaly
management closes.

Three failure modes if it is missing:

- **Late discovery**: a leaked credential, a runaway batch job, or a developer test
  in an unintended region runs unnoticed for 20-30 days. The cost is the full month's
  burn, not the first day's.
- **Unattributed surprises**: when finance flags an unexpected $80K on the monthly
  reconciliation, no one knows which team or workload caused it. The investigation
  itself costs days of engineering time.
- **Optimisation built on noise**: rightsizing recommendations and commitment purchases
  assume the baseline is meaningful. If the baseline contains undetected anomalies,
  optimisation work mis-calibrates against them.

Anomaly management is required at Crawl maturity. The native tooling is free or
near-free. There is no good reason to defer it.

---

## Native tooling per cloud

### AWS Cost Anomaly Detection

Built into AWS Cost Management. ML-based, free to use, alerts via SNS or email.

**Configuration recommendations:**
- Create monitors at multiple scopes simultaneously: service-level, linked-account level,
  and tag-based for high-value cost categories. A single aggregate monitor will miss
  the masked-anomaly pattern (see below).
- Set alert thresholds as **absolute dollar amounts**, not just percentages. A 100%
  increase on $10 is $10; a 20% increase on $50,000 is $10,000. The percentage view
  surfaces noise; the dollar view surfaces material change.
- Route alerts to both the FinOps practitioner and the engineering team owner. If the
  team that caused the anomaly does not see the alert, no remediation happens.
- Review alert history monthly. Tune thresholds to reduce false positives. A monitor
  that alerts every week trains people to ignore it.

For multi-account organisations, configure monitors in the management (payer) account
so they cover the full consolidated bill. Per-account monitors miss anomalies that
span accounts (e.g. a workload that moved subscriptions).

### Azure Cost Management anomaly detection

Built into Azure Cost Management. Available at subscription and resource-group scopes.
Less granular than AWS Cost Anomaly Detection but adequate for most use cases.

**Configuration recommendations:**
- Enable at billing-account or billing-profile scope for full visibility. Subscription-only
  scope misses anomalies in subscriptions you have not explicitly configured.
- Combine with **scheduled exports** to Storage and downstream alerting (Power BI,
  Logic Apps, or FinOps Hubs). The native UI does not do automatic distribution.
- Use **budget alerts** as a complement, not a substitute. Budget alerts trigger on a
  spend threshold; anomaly alerts trigger on a deviation from baseline. Both are needed.
- For workloads on FOCUS-conformant exports, run a custom anomaly query (see "Layered
  detection" below) on the FOCUS dataset to catch what the native tool misses.

### GCP budget anomaly alerts

GCP relies primarily on Budgets with threshold alerts and forecasted-spend alerts. The
native anomaly detection is less mature than AWS or Azure. For meaningful anomaly
management on GCP, build on the BigQuery billing export (detailed export, not standard).

**Configuration recommendations:**
- Configure Budgets at the billing-account level with **forecasted-spend alerts** at
  50%, 90%, and 100% thresholds. Forecasted alerts catch trajectory changes earlier
  than actual-spend alerts.
- Build a custom anomaly detection job on the BigQuery billing export. A daily query
  comparing the trailing 7 days against the prior 30-day baseline catches most cost
  spikes within a day.
- Route alerts via Pub/Sub to Slack or PagerDuty. Email-only alerts get filtered.
- For FOCUS-aligned multi-cloud detection, query the GCP FOCUS export the same way
  you query AWS / Azure FOCUS data.

---

## Threshold philosophy

Two common mistakes:

1. **Percentage-only thresholds.** A 50% spike on a $100/day service is $50. A 10%
   spike on a $50,000/day service is $5,000. The first triggers an alert no one acts
   on; the second does not trigger an alert at all. Use absolute dollar floors alongside
   percentage thresholds.
2. **Aggregate-only thresholds.** A monthly total within ±5% of plan looks healthy
   even when a $50K/month new workload appeared and a $50K/month commitment offset
   absorbed the delta. The total moved by zero; the anomaly was real. See "Layered
   detection" for the fix.

Recommended starting thresholds:

| Maturity | Threshold philosophy |
|---|---|
| Crawl | Absolute floor: alert on any daily delta > $1,000 in a $100K/month account. Tune monthly. |
| Walk | Absolute + percentage: alert on > $1,000 OR > 20% deviation from 7-day baseline, per scope. |
| Run | ML-driven (Cost Anomaly Detection / Azure / custom z-score) with absolute floor as backstop. Alert routing differentiated by severity. |

---

## The layered-detection pattern (catching masked anomalies)

The single most common failure mode in anomaly management is the **masked anomaly**:
two changes of opposite sign in the same billing period that net to a small total
delta. Aggregate monitors do not see it. The classic shape:

- A team spins up unsanctioned compute in an unexpected region (say $80K/month).
- Independently, the FinOps team buys a Reservation that reduces another workload's
  on-demand spend by roughly the same amount.
- The aggregate monthly total moves by 1-2%. No alert fires.
- The unsanctioned workload runs for the full month before anyone investigates.

The fix is **layered detection**: configure anomaly monitors at multiple scopes
simultaneously, so a deviation in any one of them alerts independently of the aggregate.

**Recommended layers:**
- Service (compute, storage, networking, AI, databases)
- Region (each region monitored separately)
- Account or subscription
- Tag dimension that matters most for the org (team, environment, cost-center)
- New-resource detection (any first-time spend in a service-region pair above a small floor)

A custom z-score query against a FOCUS dataset can do this in one pass:

```sql
WITH baseline AS (
  SELECT
    ServiceName,
    Region,
    BillingAccountId,
    ResourceTags['team'] AS team,
    AVG(EffectiveCost) AS mean_cost,
    STDDEV(EffectiveCost) AS std_cost
  FROM focus_daily_cost
  WHERE ChargePeriodStart BETWEEN current_date - interval '60' day
                              AND current_date - interval '31' day
    AND ChargeClass IS NULL
    AND ChargeCategory = 'Usage'
  GROUP BY 1, 2, 3, 4
),
recent AS (
  SELECT ServiceName, Region, BillingAccountId, ResourceTags['team'] AS team,
         AVG(EffectiveCost) AS recent_cost
  FROM focus_daily_cost
  WHERE ChargePeriodStart >= current_date - interval '30' day
    AND ChargeClass IS NULL
    AND ChargeCategory = 'Usage'
  GROUP BY 1, 2, 3, 4
)
SELECT r.*, b.mean_cost, b.std_cost,
       (r.recent_cost - b.mean_cost) / NULLIF(b.std_cost, 0) AS z_score
FROM recent r
JOIN baseline b USING (ServiceName, Region, BillingAccountId, team)
WHERE ABS((r.recent_cost - b.mean_cost) / NULLIF(b.std_cost, 0)) > 3
  AND r.recent_cost > 100  -- floor: ignore noise
ORDER BY ABS(z_score) DESC;
```

Run daily. Route z-scores above 3 to a triage queue. Cross-reference with commitment
purchases in the same period to separate "real new spend" from "commitment offset".

**Treat commitment-discount application as its own axis.** A drop attributable to a
new Reservation should not cancel out an unrelated rise in a different workload. Report
both as discrete events in the alert payload, not as a netted total.

---

## New-region and new-service detection

A separate, simpler signal: **alert on any first-time spend** in a service-region
pair that has never been used before in the account, above a small floor (e.g. $100).

This catches:
- Test deployments in unintended regions (the most common source of leaked-credential
  cryptomining incidents).
- Developers spinning up services finance has no contract with.
- Migration drift where workloads end up in regions outside the approved list.

Implementation: a daily query against the billing export comparing the unique set of
(service, region) pairs in the trailing 7 days against the prior 90 days. New pairs
go to the alert queue regardless of dollar value.

---

## Integration with Security

**Sudden spend in unexpected regions is also a Security signal.** Cryptomining,
exfiltration, and compromised credentials all show up first as unexpected compute
or networking cost. A FinOps anomaly that looks like a developer mistake may actually
be an active incident.

Operating model:
- Anomaly alerts that trigger on new-region or new-service patterns CC the Security
  team automatically.
- Security and FinOps share a triage queue for these signals.
- For confirmed incidents, Security owns containment; FinOps owns the post-incident
  cost recovery work (refund requests, marketplace reversals, account isolation).

This is one of the cheapest cross-functional integrations available, and it pays for
itself the first time it catches a real security incident.

---

## Anti-patterns

- **Single-threshold monitor on total spend.** The masked-anomaly failure mode is
  exactly what this configuration produces. Always run layered detection.
- **Monthly anomaly review only.** A masked anomaly can run for the full month before
  anyone notices. Daily detection is the floor.
- **Email-only alert routing.** Cost alerts buried in inbox folders do not get acted
  on. Route to Slack, PagerDuty, or the team's existing incident channel.
- **Alerting only the FinOps practitioner.** The team that caused the anomaly is the
  team that has to fix it. Route alerts to the engineering owner directly, copying
  FinOps for visibility.
- **No alert tuning cadence.** A monitor that fires three false positives a week
  trains people to ignore real alerts. Review alert history monthly; raise thresholds
  on chronic false-positive scopes.
- **Treating "it balanced out" as stability.** Two unrelated changes netting to zero
  is not a healthy month. It is a hidden risk that will compound the next time the
  offset disappears.
- **Aggregating commitment-discount application into the deviation calculation.** A
  Reservation purchase that lowers one workload's on-demand spend should be reported
  as a discrete event, not netted against unrelated spend changes.

---

## Maturity progression

### Crawl

- Native cloud anomaly detection enabled in production accounts (AWS Cost Anomaly
  Detection, Azure anomaly detection, GCP forecasted-spend alerts)
- Absolute-dollar threshold floors set at the level of "would surprise the CFO if
  missed"
- Alerts routed to FinOps practitioner via email or Slack
- Monthly review of alert history with manual threshold tuning

**Quick win:** Enable AWS Cost Anomaly Detection or its Azure / GCP equivalent across
all production accounts. The configuration takes under an hour per account. The first
real alert typically pays for the next year of FinOps practice operations.

### Walk

- Layered detection: monitors at service, region, account, and primary tag scope
- Custom anomaly queries on FOCUS / billing exports to catch the masked-anomaly pattern
- New-region and new-service detection running daily
- Alerts routed differently by severity: low-severity to a Slack channel, high-severity
  to PagerDuty or the team's incident channel
- Anomaly investigation has a documented runbook (who triages, what data they need,
  what the escalation path is)
- Cross-functional integration with Security for new-region patterns

### Run

- ML-driven anomaly detection in production with absolute-dollar floors as backstop
- Anomaly alerts trigger automated investigation: the alert payload includes the
  resources involved, the owning team, the recent change history, and the suspected
  cause
- Triage SLA defined and tracked (e.g. 2 hours for high-severity, 1 business day for
  low)
- Anomaly history fed back into forecasting and budget models, so future budgets
  account for the variance class observed in the past
- Post-incident review for any anomaly that ran undetected for more than 7 days, with
  a root-cause action on the detection layer that missed it

---

## Where the alert lands (integration points)

An anomaly alert that does not land in a workflow someone already watches gets ignored.
Recommended integration points by audience:

| Audience | Where the alert lands | Mechanism |
|---|---|---|
| Engineering team owner | Slack channel for the team, PagerDuty if high-severity | Webhook from alert system; include resource ID, region, owning team, dollar amount |
| FinOps practitioner | Slack channel for FinOps, dashboard | Same webhook, plus daily digest |
| Finance | Monthly variance report with anomaly history annotated | CSV export from FOCUS query, included in the close packet |
| Leadership | Anomaly count and resolution SLA in the monthly business review | Aggregate metric, not individual alerts |
| Security | New-region and new-service patterns CC'd in real time | Alert webhook with `ServiceName`, `Region`, `BillingAccountId` payload |

The anti-pattern is sending every alert to every audience. Tier the routing by
severity and audience need.

---

## Cross-references

- `optimnow-methodology.md` - the maturity-aware framing this file builds on
- `finops-aws.md` - AWS Cost Anomaly Detection in the broader AWS context
- `finops-azure.md` - Azure Cost Management in the broader Azure context
- `finops-gcp.md` - BigQuery billing export, the substrate for custom GCP anomaly
  detection
- `finops-tagging.md` - tag dimensions are how layered detection becomes useful;
  anomaly maturity correlates with tagging maturity
- `finops-framework.md` - Anomaly Management capability in the FinOps Framework, plus
  the Inform-phase context

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
