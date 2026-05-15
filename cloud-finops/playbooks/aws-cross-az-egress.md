---
name: aws-cross-az-egress
scope: aws
service: AWS EC2 / VPC data transfer
waste_category: egress
confidence: likely
---

# AWS Cross-AZ Egress Chatterbox

## Problem

EC2 cross-AZ data transfer is billed at $0.01/GB outbound + $0.01/GB
inbound (so $0.02/GB round-trip). For latency-sensitive microservice
meshes that gossip across AZs, or for Kafka / database clusters that
replicate across AZs, this can become the single largest line item on
the AWS bill - often dwarfing the EC2 compute cost itself. The cost is
invisible at design time and only surfaces after weeks of CUR review.

## Symptoms

- `DataTransfer-Regional-Bytes` (CUR usage type) is in the top 5 line
  items for an account
- A Kafka or Cassandra cluster shows replication traffic across AZs
  for high-throughput topics
- Service mesh (Istio, Linkerd, Consul Connect) is configured without
  topology-aware routing
- VPC Flow Logs show heavy traffic between subnets in different AZs
  for the same service tier

## Detection

```sql
-- Athena over CUR 2.0: cross-AZ data transfer cost by account, last 30 days
SELECT
  line_item_usage_account_id      AS account,
  product_region                  AS region,
  SUM(line_item_usage_amount)     AS gb_cross_az,
  SUM(line_item_unblended_cost)   AS cost_30d
FROM cur2
WHERE line_item_usage_start_date >= current_date - interval '30' day
  AND line_item_usage_type LIKE '%DataTransfer-Regional-Bytes%'
GROUP BY 1, 2
ORDER BY cost_30d DESC
LIMIT 20;
```

For attribution, VPC Flow Logs + Athena partition queries can pinpoint
the source / destination ENIs:

```sql
SELECT srcaddr, dstaddr, SUM(bytes) AS bytes_total
FROM vpc_flow_logs
WHERE start >= ... 
  AND srcaz <> dstaz
  AND srcvpc = dstvpc
GROUP BY 1, 2
ORDER BY bytes_total DESC
LIMIT 50;
```

## Fix

1. **Topology-aware routing**: configure Kubernetes (Topology Aware
   Hints), service mesh (Istio locality routing), or load balancer
   target group stickiness so a request sent in AZ-a routes to a target
   in AZ-a where possible.
2. **Co-locate chatty pairs**: if Service A makes 1000 calls/sec to
   Service B, the two should be in the same AZ even if it slightly
   weakens the multi-AZ posture - a single-AZ outage is a known recovery
   pattern, a constant cross-AZ bill is not.
3. **Read replicas in each AZ**: for read-heavy databases, an in-AZ read
   replica eliminates cross-AZ read traffic at the cost of one extra
   instance.
4. **VPC Endpoints for AWS services**: replace cross-AZ traffic to
   regional service endpoints with VPC Endpoints (S3, DynamoDB, ECR,
   Secrets Manager, etc.).

## Anti-pattern

- Collapsing to a single AZ to "fix" cross-AZ cost. The first AZ outage
  costs more than years of cross-AZ data transfer.
- Adding cache layers without measuring whether the cache hit rate
  actually reduces cross-AZ traffic. Many caches add cost without
  reducing the underlying chatty pattern.

## See also

- `references/finops-aws.md` - networking cost section, CUR usage types
- `references/finops-kubernetes.md` - Karpenter and AZ-aware node
  scheduling
- `playbooks/aws-zombie-nat-gateway.md` - related egress pattern

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
