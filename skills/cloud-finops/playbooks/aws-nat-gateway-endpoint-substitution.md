---
name: aws-nat-gateway-endpoint-substitution
scope: aws
service: AWS NAT Gateway
waste_category: egress
confidence: obvious
---

# AWS NAT-to-Gateway-Endpoint Substitution

## Problem

A NAT Gateway charges a per-GB data-processing fee (~$0.045/GB in
us-east-1; illustrative list rate, written August 2026) on every byte it
moves. When the traffic behind that fee is destined for **S3 or DynamoDB
in the same region**, the entire charge is avoidable: a **gateway VPC
endpoint** carries that traffic for free - no hourly charge, no per-GB
fee - and keeps it on the AWS network instead of hairpinning through the
NAT. This is the high-traffic end of the NAT cost distribution; the idle
end is `aws-zombie-nat-gateway`. A data pipeline writing a few TB a month
to S3 through a NAT pays hundreds of dollars for routing it could have
had for nothing.

## Symptoms

- NAT Gateway data-processing cost is a top line in the VPC's bill and
  the VPC hosts workloads that read from or write to S3 or DynamoDB
- The VPC has no gateway endpoints configured (very common in VPCs
  created by hand or by older IaC templates)
- Batch, analytics, backup, or container-image traffic peaks line up
  with NAT `BytesOutToDestination` peaks
- ECS/EKS clusters pulling images from ECR (ECR layer storage sits in
  S3, so image pulls transit the NAT without an S3 gateway endpoint)

## Detection

Two config-level signals are enough to act, because adding a gateway
endpoint costs nothing and can only remove NAT processing fees.

Step 1 - rank NAT gateways by data-processing spend (Athena over CUR 2.0):

```sql
-- NAT data-processing cost per gateway, last full month.
-- NatGateway-Bytes usage amount is already reported in GB.
SELECT
  line_item_resource_id         AS nat_id,
  SUM(line_item_usage_amount)   AS gb_processed,
  SUM(line_item_unblended_cost) AS processing_cost
FROM cur2
WHERE line_item_usage_start_date >= date_trunc('month', current_date - interval '1' month)
  AND line_item_usage_start_date <  date_trunc('month', current_date)
  AND line_item_usage_type LIKE '%NatGateway-Bytes'
GROUP BY 1
ORDER BY processing_cost DESC;
```

Step 2 - for each VPC behind a high-cost NAT, check whether gateway
endpoints already exist:

```bash
# Empty output = no gateway endpoints in the VPC = candidate confirmed.
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=vpc-XXXXXXXX" "Name=vpc-endpoint-type,Values=Gateway" \
  --query "VpcEndpoints[].{service:ServiceName,state:State}" --output table
```

Optional precision step - sizing exactly what share of NAT traffic is
S3/DynamoDB-destined requires **VPC Flow Logs delivered to S3 and queried
via Athena** (matching `dstaddr` against the regional S3 prefix list). If
flow logs are not enabled, skip it: the fix below is safe without the
sizing, and the next month's CUR shows the realised delta.

## Fix

1. Create a gateway endpoint for S3 (`com.amazonaws.<region>.s3`) and,
   if DynamoDB is used, a second one for DynamoDB. Attach them to the
   route tables of the private subnets that currently route through the
   NAT. AWS inserts prefix-list routes automatically; more-specific
   prefix-list routes win over the NAT default route, so traffic shifts
   without touching the 0.0.0.0/0 entry.
2. Verify S3 bucket policies and IAM conditions: policies that pin
   `aws:SourceIp` to the NAT's public IP will start failing, because
   endpoint traffic arrives with a private source. Replace them with
   `aws:SourceVpce` / `aws:SourceVpc` conditions.
3. Re-run the Step 1 query after one full month: NatGateway-Bytes on the
   affected gateways should drop by the S3/DynamoDB share.
4. If the remaining NAT traffic is now near zero, the gateway itself may
   have become a zombie - hand over to `aws-zombie-nat-gateway`.

## Anti-pattern

- Using an **interface endpoint** for S3 where a gateway endpoint
  suffices. Interface endpoints bill per hour per AZ plus per GB; for
  bulk S3 traffic they reintroduce the very fee the gateway endpoint
  removes. Interface endpoints for S3 exist for on-premises and
  cross-VPC access - cases a gateway endpoint cannot serve.
- Expecting the endpoint to serve traffic from peered VPCs, VPN, or
  Direct Connect. Gateway endpoints only serve traffic originating in
  their own VPC; hybrid paths need an interface endpoint or a different
  design.
- Deleting the NAT Gateway in the same change. Other traffic (package
  mirrors, external APIs, webhooks) still needs it; remove it only after
  the post-change CUR shows it idle.
- Forgetting cross-region: a gateway endpoint reaches same-region S3
  only. Traffic to a bucket in another region still transits the NAT.

## See also

- `playbooks/aws-zombie-nat-gateway.md` - the idle end of the same NAT
  distribution, which this pattern deliberately complements
- `playbooks/aws-cross-az-egress.md` - the other avoidable-transfer
  pattern inside a VPC
- `references/finops-aws.md` - CUR / Data Exports setup behind the
  detection query
- `references/finops-waste-detection-playbooks.md` - "egress / data
  transfer" category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
