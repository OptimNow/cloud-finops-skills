---
name: aws-idle-load-balancer
scope: aws
service: AWS ELB (ALB / NLB / Classic)
waste_category: idle
confidence: obvious
questions:
  - "We pay for load balancers that receive no traffic. How do we find them?"
  - "Is it safe to delete an ALB with no healthy targets?"
  - "Which of our load balancers have had zero requests for a month?"
  - "Why do idle load balancers keep costing money after a project ends?"
  - "Nous payons des load balancers sans trafic : comment les repérer et les supprimer ?"
---

# AWS Idle Load Balancer

## Problem

Application Load Balancers and Network Load Balancers carry an hourly
charge (at us-east-1 list rates read in November 2026, $0.0225/hr for an
ALB, about $16.43/month) plus an LCU/NLCU usage component. A load balancer
with no targets, or with targets that receive no requests, still pays the
full hourly. Idle ELBs accumulate after service decommissions, blue/green
migrations, and one-off load tests. The hourly and monthly figures are
illustrative; verify against live pricing before sizing a business case.

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
-- Athena over CUR 2.0: load balancers billed for hours with almost no traffic.
-- Every type bills its hourly charge as <REGION>-LoadBalancerUsage; the
-- operation tells them apart (LoadBalancing:Application, :Network, :Gateway,
-- and plain LoadBalancing for a Classic Load Balancer). ALB, NLB and GWLB
-- bill traffic as LCUs (LCUUsage). A Classic Load Balancer bills no LCU: it
-- bills GB processed (DataProcessing-Bytes), so it gets its own traffic test.
WITH lb AS (
  SELECT
    line_item_resource_id         AS elb_arn,
    line_item_usage_account_id    AS account,
    MAX(CASE WHEN line_item_usage_type LIKE '%LoadBalancerUsage'
             THEN line_item_operation END)           AS operation,
    SUM(CASE WHEN line_item_usage_type LIKE '%LoadBalancerUsage'
             THEN line_item_usage_amount END)        AS hours,
    -- COALESCE matters: a load balancer with zero traffic produces no LCU
    -- or data-processing line items at all, so the bare SUM returns NULL
    -- and NULL < 1 filters out exactly the idlest load balancers.
    COALESCE(SUM(CASE WHEN line_item_usage_type LIKE '%LCUUsage'
                       AND line_item_usage_type NOT LIKE '%ReservedLCUUsage'
                      THEN line_item_usage_amount END), 0) AS lcu_units,
    COALESCE(SUM(CASE WHEN line_item_usage_type LIKE '%DataProcessing-Bytes'
                      THEN line_item_usage_amount END), 0) AS gb_processed,
    SUM(line_item_unblended_cost) AS cost_30d
  FROM cur2
  WHERE line_item_usage_start_date >= current_date - interval '30' day
    AND product_servicecode = 'AWSELB'
  GROUP BY 1, 2
)
SELECT *
FROM lb
WHERE hours > 0
  AND CASE WHEN operation = 'LoadBalancing'   -- Classic Load Balancer
           THEN gb_processed < 1
           ELSE lcu_units < 1 END
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

# Classic Load Balancers have no target groups: list those with no instances
aws elb describe-load-balancers \
  --query 'LoadBalancerDescriptions[?length(Instances)==`0`].LoadBalancerName' \
  --output text
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

- `references/finops-aws-patterns-networking.md` - Networking Optimization Patterns,
  including the inactive ALB / NLB / CLB / GWLB patterns and LCU mechanics
- `playbooks/aws-zombie-nat-gateway.md` - same idle-resource pattern,
  different service

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
