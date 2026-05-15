---
name: aws-sagemaker-idle-endpoint
scope: aws
service: AWS SageMaker
waste_category: idle
confidence: obvious
---

# AWS SageMaker Idle Endpoint

## Problem

A SageMaker real-time endpoint is billed at the underlying instance hourly
rate as long as the endpoint is provisioned, whether traffic flows through
it or not. A small `ml.m5.xlarge` endpoint costs ~$170/month; a single
`ml.g4dn.xlarge` GPU endpoint costs ~$540/month; an `ml.p4d.24xlarge`
endpoint costs ~$27,500/month. Forgotten demo endpoints, A/B test variants
that were never decommissioned, and "we might need it again" endpoints are
among the highest-density waste patterns in any AWS account running ML.

## Symptoms

- CloudWatch `AWS/SageMaker.Invocations` for the endpoint over the last 30
  days is zero or near-zero
- The endpoint was created during a POC, a model-comparison exercise, or
  a launched-then-replaced deployment, and no application currently calls it
- The endpoint's `EndpointName` no longer maps to any running service or
  data product in the team's service catalogue
- Multiple variants exist on the same endpoint (A/B test artefacts) but
  only one is receiving traffic
- The owning team / cost-centre tag is empty or stale

## Detection

```sql
-- Athena over CUR 2.0: SageMaker endpoint hours vs invocations last month
-- (join CUR to a CloudWatch invocation extract; or filter manually after
-- pulling the list of endpoints with non-zero hours)
SELECT
  line_item_resource_id           AS endpoint_arn,
  line_item_usage_type            AS usage_type,
  SUM(line_item_usage_amount)     AS instance_hours,
  SUM(line_item_unblended_cost)   AS cost_month
FROM cur2
WHERE line_item_usage_start_date >= date_trunc('month', current_date - interval '1' month)
  AND line_item_usage_start_date <  date_trunc('month', current_date)
  AND product_servicecode = 'AmazonSageMaker'
  AND line_item_usage_type LIKE '%SageMaker:host-%'
GROUP BY 1, 2
HAVING SUM(line_item_usage_amount) > 600   -- > 600 hours/month = always-on
ORDER BY cost_month DESC;
```

Then cross-check each `endpoint_arn` against CloudWatch:

```
aws cloudwatch get-metric-statistics \
  --namespace AWS/SageMaker \
  --metric-name Invocations \
  --dimensions Name=EndpointName,Value=<endpoint-name> \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time   $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 --statistics Sum
```

A 30-day Sum of zero (or below ~50 across the whole month) is the strong
signal: the endpoint pays the full hourly rate while serving no traffic.

## Fix

Apply the safest-first ladder. The right action depends on whether the
endpoint is genuinely idle or just lightly used.

1. **Delete** if the endpoint has zero invocations for 30+ days AND no
   owner can produce a use case. Confirm with the owning team via Slack /
   ticket, then `aws sagemaker delete-endpoint --endpoint-name <name>`. Also
   delete the endpoint configuration if it is not reused.
2. **Move to asynchronous inference** if the endpoint serves a workload
   that tolerates delayed responses (background scoring, batch enrichment,
   media processing). Async inference supports scale-to-zero, which removes
   the always-on bill entirely. Create a new endpoint with
   `EndpointConfig.AsyncInferenceConfig`, migrate the caller, then delete
   the real-time variant.
3. **Move to serverless inference** if traffic is genuinely intermittent
   (a few requests per hour or per day) and the workload can tolerate cold
   starts of 1-15 s. Serverless inference bills per-request rather than
   per-hour, with no idle charge.
4. **Rightsize** if the endpoint legitimately needs to stay available but
   the instance is too large. See
   [aws-gpu-instance-oversized](aws-gpu-instance-oversized.md) for the GPU
   rightsizing playbook.

## Anti-pattern

- Deleting an endpoint that serves an end-of-month batch job or a quarterly
  cron. Always check the last 60-90 days of invocations, not just the last
  30, before deletion.
- Deleting the endpoint without also cleaning up the associated
  `EndpointConfig` and any unused model artefacts in S3 (the S3 storage is
  small but accumulates, and stale `EndpointConfig` objects clutter the
  inventory).
- Migrating to async inference for a user-facing latency-sensitive API
  ("just in case the new pattern saves money"). Async is wrong for any
  request-response workload where the caller blocks on the result.

## See also

- `references/finops-aws.md` - SageMaker billing model, deployment pattern
  selection (real-time vs serverless vs async vs batch), Inference Components
  and Multi-Model Endpoints
- `playbooks/aws-sagemaker-mme-consolidation.md` - the related pattern when
  several lightly-used endpoints exist in the same account
- `playbooks/aws-gpu-instance-oversized.md` - the rightsizing playbook for
  endpoints that should stay alive but on a smaller GPU
- `references/finops-waste-detection-playbooks.md` - Category 7 (AI/ML
  inefficiency) taxonomy

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
