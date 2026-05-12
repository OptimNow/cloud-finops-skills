---
name: aws-sagemaker-mme-consolidation
scope: aws
service: AWS SageMaker
waste_category: overprovisioned
confidence: likely
---

# AWS SageMaker Endpoint Sprawl - MME / Inference Components Consolidation

## Problem

A common SageMaker pattern is "one endpoint per model": each model gets its
own dedicated real-time endpoint with its own instance(s). When models
share a runtime and each receives only light traffic, the total spend is
dominated by paying for idle dedicated capacity rather than serving
requests. Three lightly-used endpoints at `ml.m5.xlarge` cost ~$510/month
combined; six cost ~$1,020/month; nine cost ~$1,530/month - and most of
that is the per-endpoint hourly base, not the actual inference work. The
fix is to consolidate compatible models onto a single endpoint using either
**Multi-Model Endpoints (MME)** or the newer **Inference Components (IC)**.

## Symptoms

- An account / region has more than three real-time endpoints with
  CloudWatch `Invocations` < 100/hour at peak
- Most endpoints run the same instance type (sign that the team has been
  stamping out copies of a default pattern)
- Models share a runtime (all sklearn, all XGBoost, all PyTorch with the
  same base image) or at least share a small set of containers
- Endpoint instance CPU/GPU utilisation is < 30% on average
- Average request latency budget allows 100 ms - 2 s of slack (room for
  the MME model-load step on cache miss)

## Detection

```sql
-- Athena over CUR 2.0: count of distinct SageMaker endpoints per account
-- and region, with average hours and cost (high counts at low cost-per-
-- endpoint = sprawl candidate)
SELECT
  line_item_usage_account_id      AS account_id,
  product_region                  AS region,
  COUNT(DISTINCT line_item_resource_id) AS endpoint_count,
  SUM(line_item_usage_amount)     AS total_instance_hours,
  SUM(line_item_unblended_cost)   AS total_cost_month,
  AVG(line_item_unblended_cost)   AS avg_cost_per_endpoint
FROM cur2
WHERE line_item_usage_start_date >= date_trunc('month', current_date - interval '1' month)
  AND line_item_usage_start_date <  date_trunc('month', current_date)
  AND product_servicecode = 'AmazonSageMaker'
  AND line_item_usage_type LIKE '%SageMaker:host-%'
GROUP BY 1, 2
HAVING COUNT(DISTINCT line_item_resource_id) >= 3
ORDER BY total_cost_month DESC;
```

Then, for each high-count account/region pair, list the endpoints and pull
`Invocations` per endpoint from CloudWatch. A cluster of endpoints with
< 100 invocations / hour at peak is the consolidation target.

## Fix

The right shape depends on whether the models share a container.

1. **Multi-Model Endpoints (MME)** when models share a single container
   image and runtime (e.g. all sklearn, all XGBoost, all TensorFlow
   Serving). The endpoint loads models on demand from S3 into instance
   memory; cold-start on first invocation per model is in the 100 ms - 2 s
   range. Best for tens to thousands of small homogeneous models.
2. **Inference Components (IC)** when models use heterogeneous frameworks
   or have different scaling requirements. Each Inference Component is a
   model + container deployed onto a shared endpoint instance pool, with
   per-component autoscaling. Best for fewer (5-50) but more diverse
   models. IC is the newer mechanism (introduced 2023) and is generally
   preferred for new builds unless MME's homogeneous-runtime model is a
   genuine fit.
3. **Migration order**: pick the two or three lowest-traffic endpoints
   first, deploy them on an MME or IC pilot, route 10% of traffic, watch
   latency p95 / p99, then complete the migration. Decommission the
   per-model endpoints only after the pilot survives a full week.
4. **Capacity sizing**: the consolidated endpoint should be sized for
   peak concurrent loaded models, not for the sum of the underlying
   instance sizes. Typically one `ml.m5.2xlarge` replaces 4-6
   `ml.m5.xlarge` per-model endpoints.

## Anti-pattern

- Forcing MME on latency-sensitive APIs with strict p99 budgets - the
  model-load cold-start adds 100 ms - 2 s on cache miss, which can violate
  user-facing SLAs.
- Consolidating models with very different scaling profiles onto MME -
  one bursty model can evict the others from the cache and degrade overall
  hit rate. IC handles this case better via independent component scaling.
- Picking IC when models are truly homogeneous and small - MME is cheaper
  to operate and has lower per-model overhead in that regime.
- Skipping the pilot phase. A direct cutover to a consolidated endpoint
  without a traffic-shadowing window has been the most common cause of
  consolidation rollbacks.

## See also

- `references/finops-aws.md` - SageMaker AI Savings Plan, deployment
  pattern selection, MME vs Inference Components decision
- `playbooks/aws-sagemaker-idle-endpoint.md` - the deletion-first option
  when an endpoint receives literally zero traffic
- `references/finops-waste-detection-playbooks.md` - Category 7 (AI/ML
  inefficiency) taxonomy
