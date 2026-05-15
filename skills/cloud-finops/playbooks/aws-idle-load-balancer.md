---
name: aws-idle-load-balancer
scope: aws
service: AWS ELB (ALB / NLB / Classic)
waste_category: idle
confidence: obvious
---

# AWS Idle Load Balancer

## Problem

Application Load Balancers and Network Load Balancers carry an hourly
charge (around $0.0225/hr for ALB = $16.40/month) plus an LCU/NLCU usage
component. A load balancer with no targets, or with targets that receive
no requests, still pays the full hourly. Idle ELBs accumulate after
service decommissions, blue/green migrations, and one-off load tests.

## Symptoms

- CloudWatch `RequestCount` (ALB) or `ActiveFlowCount_TCP` (NLB) is zero
  or near-zero over a 7-30 day window
- The ELB has no registered targets, OR all registered targets are
  unhealthy
- The ELB was created during a project that has since shipped or been
  cancelled
- A team has multiple ALBs but only one of them carries production
  traffic - the others are forgotten leftovers

## Detection

```sql
-- Athena over CUR 2.0: ELB hours billed by resource, no LCU pressure
SELECT
  line_item_resource_id           AS elb_arn,
  line_item_usage_account_id      AS account,
  SUM(CASE WHEN line_item_usage_type LIKE '%LoadBalancer%' AND line_item_usage_type LIKE '%Hours' THEN line_item_usage_amount END) AS hours,
  SUM(CASE WHEN line_item_usage_type LIKE '%LCU%' THEN line_item_usage_amount END) AS lcu_units,
  SUM(line_item_unblended_cost)   AS cost_30d
FROM cur2
WHERE line_item_usage_start_date >= current_date - interval '30' day
  AND product_servicecode = 'AWSELB'
GROUP BY 1, 2
HAVING SUM(CASE WHEN line_item_usage_type LIKE '%LCU%' THEN line_item_usage_amount END) < 1
ORDER BY cost_30d DESC;
```

Cross-check with the API:

```bash
# ALBs/NLBs with zero registered healthy targets
aws elbv2 describe-target-groups \
  --query 'TargetGroups[].TargetGroupArn' --output text \
  | tr '\t' '\n' \
  | while read tg; do
      health=$(aws elbv2 describe-target-health --target-group-arn "$tg" \
        --query 'length(TargetHealthDescriptions[?TargetHealth.State==`healthy`])')
      [[ "$health" == "0" ]] && echo "ZERO HEALTHY TARGETS: $tg"
    done
```

## Fix

1. Cross-reference idle ELBs with DNS records. If `prod.example.com`
   still points at an idle ELB, the deletion is a production incident in
   waiting.
2. Delete the load balancer. Confirm dependent target groups, listeners,
   and Route 53 records are also cleaned (target groups carry no charge but
   leave the catalogue dirty).
3. For ELBs whose only purpose is internal service-to-service routing,
   evaluate **VPC Endpoints**, **PrivateLink**, or **Service Connect** -
   often cheaper and remove the ELB entirely.

## Anti-pattern

- Deleting an ELB that is the target of a Route 53 alias record. The DNS
  goes stale silently and traffic 404s for hours before anyone notices.
- Aggressively consolidating production ALBs into one shared ALB. The
  blast radius of a misconfigured rule grows; prefer one ALB per product
  domain over one ALB per organisation.

## See also

- `references/finops-aws.md` - ELB pricing tiers, LCU mechanics
- `playbooks/aws-zombie-nat-gateway.md` - same idle-resource pattern,
  different service

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
