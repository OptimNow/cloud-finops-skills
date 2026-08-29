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
invisible at design time and only surfaces after weeks of CUR review. The
per-GB rates above are illustrative list rates as at May 2026 and vary by
region - verify against live pricing before sizing a business case.

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

For attribution, VPC Flow Logs + Athena partition queries can pinpoint the
source / destination ENIs - but only after enrichment. A v5 flow record
carries a single `az-id` and `vpc-id`, both describing the interface that
captured the flow; there is no source-AZ / destination-AZ pair in the log.
So the prerequisite is an ENI inventory table mapping private IP to AZ and
VPC, refreshed at least daily from `aws ec2 describe-network-interfaces`.
Without it, no Flow Logs query can answer the cross-AZ question.

```sql
-- Cross-AZ talkers, VPC Flow Logs (v5) joined twice against the ENI
-- inventory: once for the source address, once for the destination.
-- flow_direction = 'egress' keeps each flow counted once - both the sending
-- and the receiving ENI log the same conversation. Drop that predicate only
-- if your log format predates v5, and halve the totals if you do.
-- Unmatched addresses (internet endpoints, ENIs deleted since the last
-- inventory refresh) fall out of the inner joins by design.
SELECT
  f.srcaddr,
  f.dstaddr,
  src.availability_zone AS src_az,
  dst.availability_zone AS dst_az,
  SUM(f.bytes)          AS bytes_total
FROM vpc_flow_logs f
JOIN eni_inventory src ON f.srcaddr = src.private_ip
JOIN eni_inventory dst ON f.dstaddr = dst.private_ip
WHERE f.start >= to_unixtime(current_timestamp - interval '7' day)
  AND f.flow_direction = 'egress'
  AND src.vpc_id = dst.vpc_id
  AND src.availability_zone <> dst.availability_zone
GROUP BY 1, 2, 3, 4
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

- `references/finops-aws-patterns.md` - Networking Optimization Patterns,
  including cross-AZ transfer and the AZ-misaligned NAT Gateway pattern
- `references/finops-aws.md` - CUR and Data Exports setup, where the
  usage-type breakdown comes from
- `references/finops-kubernetes.md` - Karpenter and AZ-aware node
  scheduling
- `playbooks/aws-zombie-nat-gateway.md` - related egress pattern

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
