---
name: aws-spot-candidate
scope: aws
service: Amazon EC2 / EC2 Auto Scaling / EKS / ECS on Fargate / EMR
waste_category: commitment-mismatch
confidence: possible
questions:
  - "Which of our workloads could run on Spot instances?"
  - "Our CI and batch fleets run fully on demand. How do we move them to Spot?"
  - "Does Spot usage count towards our Savings Plan commitment?"
  - "How do we find on-demand capacity that no reservation covers and that tolerates interruption?"
  - "Quelles charges pourraient tourner sur des instances Spot, et comment les repérer ?"
---

# AWS Spot Candidate

## Problem

Interruption-tolerant capacity billed at the On-Demand rate, with no Savings
Plan or RI behind it. Only uncovered usage qualifies: Spot spend does not
apply to a Savings Plan commitment, so moving covered usage strands it. Spot
is not a commitment; it is filed here because detection is the coverage-gap
query. Confidence is `possible`: billing finds the spend, but interruption
tolerance is a human judgement and Spot capacity must exist for the shape.

## Symptoms

- On-Demand hours outside SP/RI coverage in Auto Scaling groups, EKS or
  Karpenter node pools, or EMR
- Non-production, CI and batch fleets 100% On-Demand
- ECS services on Fargate with no `FARGATE_SPOT` provider

## Detection

**1. Spend.** `Usage` is the On-Demand line item type; SP- and RI-covered rows
(`SavingsPlanCoveredUsage`, `DiscountedUsage`) drop out
([CUR 2.0](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-line-item.html)).

```sql
-- Athena over CUR 2.0: uncovered On-Demand EC2 hours, last full month
SELECT product_region_code, product_instance_type,
       element_at(resource_tags, 'user_environment') AS environment,
       SUM(line_item_usage_amount)       AS instance_hours,
       SUM(line_item_unblended_cost)     AS uncovered_od_cost
FROM cur2
WHERE line_item_usage_start_date >= date_trunc('month', current_date - interval '1' month)
  AND line_item_usage_start_date <  date_trunc('month', current_date)
  AND line_item_product_code = 'AmazonEC2'
  AND line_item_line_item_type = 'Usage'
  AND line_item_usage_type LIKE '%BoxUsage%'
GROUP BY 1, 2, 3
ORDER BY uncovered_od_cost DESC;
```

`environment` NULL on every row means the tag is not activated; list the
active keys with `map_keys(resource_tags)`.

**2. Workload read** (read-only, target region):

```bash
# Running non-Spot instances and their Auto Scaling group
aws ec2 describe-instances --region eu-central-1 \
  --filters "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[] | [?InstanceLifecycle==null].[InstanceId,InstanceType,Tags[?Key=='aws:autoscaling:groupName']|[0].Value]"
# EKS managed node groups and Karpenter: capacity type per node
kubectl get nodes -L eks.amazonaws.com/capacityType -L karpenter.sh/capacity-type
```

For EMR, check `Market` in `aws emr list-instance-groups`; for ECS, the
service's `capacityProviderStrategy`. Then all four must hold: stateless or
checkpointed; tolerates a two-minute notice; not a single instance without
failover; no strict latency or availability SLA.

**3. Availability gate**, before any move (eu-central-1):

- Build the list first: 10 or more instance types, all AZs
  ([Spot best practices](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html)),
  with attribute-based selection or `ec2-instance-selector` (from
  [GitHub](https://github.com/aws/amazon-ec2-instance-selector)).
- Score that list per AZ (illustrative list; use your own):

  ```bash
  aws ec2 get-spot-placement-scores --region eu-central-1 \
    --instance-types m5.xlarge m5a.xlarge m6i.xlarge m6a.xlarge m7i.xlarge \
                     m7a.xlarge r5.xlarge r6i.xlarge r7i.xlarge m5n.xlarge \
    --target-capacity 64 --target-capacity-unit-type vcpu \
    --region-names eu-central-1 --single-availability-zone
  ```

  Fewer than three types always scores low, so one type understates
  availability. The score is point-in-time, does not predict interruptions,
  and caps target capacity by your recent Spot usage; repeat it over several
  days ([Spot placement score](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-placement-score.html)).
- [Spot Instance Advisor](https://aws.amazon.com/ec2/spot/instance-advisor/):
  interruption band and average saving per type, last 30 days, Region level,
  no AZ.
- Already on Spot: EC2 Capacity Manager interruption rate by Region, AZ and
  account (since 5 January 2026). Enable it first, per account or
  organisation-wide from the management account; `aws ec2
  get-capacity-manager-attributes` shows the status read-only.
- Unified Operations support plan only: `get-capacity-manager-supportability-scores
  --market-type spot` scores each type and AZ pair; after the move,
  `SpotCapacityRequestFulfillmentRate` shows what was delivered (interrupted
  instances still count)
  ([Capacity Manager](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/capacity-manager.html)).
- `describe-spot-price-history` (90 days) estimates the saving only. The price
  moves slowly on long-term supply and demand; capacity moves in real time.

## Fix

Cheapest first. Test each move with the AWS Fault Injection Service action
`aws:ec2:send-spot-instance-interruptions` before production.

1. **ECS on Fargate:** add `FARGATE_SPOT` with a weight; keep `FARGATE` as
   `base`. Fargate does not replace missing Spot capacity with On-Demand: a
   one-task service waits until capacity returns.
2. **EKS:** a `SPOT` managed node group with several same-size types (EKS sets
   `price-capacity-optimized` and Capacity Rebalancing), or allow `spot` in the
   Karpenter NodePool; pin fault-intolerant Pods to On-Demand.
3. **Auto Scaling:** mixed instances policy, `price-capacity-optimized`, the
   diversified list, all AZs, `CapacityRebalance` on, `OnDemandBaseCapacity`
   for the floor.
4. **EMR:** instance fleets; primary and core On-Demand, task nodes on Spot.
5. **Interruptions:** an EventBridge rule on the rebalance recommendation and
   the two-minute notice that checkpoints or drains. No maximum price.
6. Re-baseline Savings Plan coverage before the next purchase.

## Anti-pattern

- One instance type or one AZ.
- Moving SP- or RI-covered usage.
- Stateful work without checkpoint and resume.
- Judging availability from one score on one type.
- Reading the Spot price as an availability signal.
- On-Demand failover as the interruption strategy (AWS discourages it).
- Promising "up to 90%" instead of the realised 60-80% in the commitments
  reference (a working estimate).

## See also

- `references/finops-aws-commitments.md` - Spot doctrine and sources
- `references/finops-aws-patterns-compute.md` - Spot catalogue entries
- `playbooks/aws-graviton-candidate.md` - Graviton types widen the Spot pool
- `references/finops-waste-detection-playbooks.md` - category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
