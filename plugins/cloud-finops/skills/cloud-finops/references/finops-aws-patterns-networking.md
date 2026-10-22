---
name: finops-aws-patterns-networking
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Anomaly Management"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["SRE", "Platform Engineering"]
fcp_maturity_entry: "Crawl"
---

# AWS Optimization Patterns: Networking

> The AWS pattern catalogue for NAT gateways, VPC endpoints, load balancers,
> cross-AZ transfer, CloudFront and Elastic IPs: the signal to look for and the
> remediation for each. A lookup surface, retrieved when hunting a specific
> pattern. For named patterns with runnable detection queries, prefer
> `playbooks/`. The other families are listed in `finops-aws-patterns.md`; billing
> mechanics are in `finops-aws-billing.md`, commitments in `finops-aws-commitments.md`.

> Source: the [Cloud Efficiency Hub](https://www.pointfive.co/efficiency-hub),
> an open, practitioner-governed library powered by PointFive, credited here as
> the Hub asks of anyone who reuses its content.

---

## Networking Optimization Patterns (15)

**Elastic Load Balancer With Only One Ec2 Instance**
Service: AWS ELB | Type: Inefficient Architecture

An ELB with only one registered EC2 instance does not achieve its core purpose - distributing traffic across multiple backends. In this configuration, the ELB adds complexity and cost without improving availability, scalability, or fault tolerance.

- If no scaling is planned or needed, remove the ELB and route traffic directly to the EC2 instance using a static IP or DNS entry
- If future scaling is expected, consider retaining the ELB but update documentation and monitoring to ensure it doesn't remain in this state long-term
- Document architectural decisions around ELB usage to prevent future misconfigurations

**Imbalanced Data Transfer Between Availability Zones**
Service: AWS Data Transfer | Type: Inefficient Architecture

Some architectures unintentionally route large volumes of traffic between resources that reside in different Availability Zones - such as database queries, service calls, replication, or logging. While these patterns may be functionally correct, they can lead to unnecessary data transfer charges when the traffic could be contained within a single AZ.

- Identify resources that receive or send high volumes of traffic to other Availability Zones within the same region
- Review VPC flow logs, CloudWatch metrics, or billing data to assess regional data transfer patterns
- Determine whether the resource acts as a centralised destination for data aggregation, storage, or processing

**Karpenter Nodes Landing In Other Availability Zones After Spot Exhaustion**
Service: AWS EKS | Type: Inefficient Architecture

When Spot capacity runs out in one Availability Zone, Karpenter places new nodes (often On-Demand fallback) in the zones that still have capacity. The cluster stays healthy, but calls that used to stay zone-local now cross zones and are billed at the Regional data transfer rate in each direction, with no health or utilisation alert. The cost surfaces only in inter-AZ data transfer lines. See the waste pattern in `finops-kubernetes.md` and the Spot best practices in `finops-aws-commitments.md`. Source: AWS Fundamentals, "Networking Is Still Hard" (8 September 2026), https://awsfundamentals.com/blog/cross-az-traffic-karpenter (practitioner write-up, not AWS documentation).

- Alert on the On-Demand to Spot ratio, on nodes per zone, and on `DataTransfer-Regional-Bytes`, and correlate spikes with Spot exhaustion events
- Widen NodePool instance families and sizes so more Spot pools qualify and the fallback fires less often
- Set `trafficDistribution: PreferClose` on Services and use topology spread constraints; even spread alone only makes the cross-zone charge consistent

**Managed Nat Gateway With Excessive Data Transfer**
Service: AWS NAT Gateway | Type: Inefficient Architecture

NAT Gateways are convenient for enabling outbound access from private subnets, but in data-intensive environments, they can quietly become a major cost driver. When large volumes of traffic flow through the gateway - particularly during batch processing, frequent software updates, or hybrid cloud integrations - the per-GB charges accumulate rapidly.

- Identify NAT Gateways with consistently high data processing volumes over the lookback period
- Review per-GB transfer charges to assess whether NAT Gateway usage represents a significant portion of total networking costs
- Determine whether traffic patterns are driven by expected workload behaviour or architectural inefficiencies

**Suboptimal Configuration Of A Cloudfront Distribution**
Service: AWS CloudFront | Type: Inefficient Configuration

This inefficiency occurs when compression is either disabled or not functioning effectively on a CloudFront distribution. Static assets such as text, JSON, JavaScript, and CSS files are compressible and benefit significantly from compression.

- Enable compression for all applicable content types in CloudFront settings
- Review and adjust cache behaviors to ensure compression is applied at the edge
- Coordinate with origin services to ensure headers support compression (e.g., avoid disabling with restrictive cache-control headers)

**Suboptimal Cross Az Routing To Nat Gateway**
Service: AWS NAT Gateway | Type: Inefficient Configuration

NAT Gateways are designed to serve private subnets within the same Availability Zone. When subnets in one AZ are configured to route traffic through a NAT Gateway in a different AZ, the traffic crosses AZ boundaries and incurs inter-AZ data transfer charges in addition to the standard NAT processing fees.

- Update route tables to ensure that each subnet routes outbound traffic through the NAT Gateway in the same AZ
- Ensure one NAT Gateway is deployed per Availability Zone for fault tolerance and cost efficiency
- Review and revise any infrastructure templates or automation that create non-AZ-aware routing

**Suboptimal Routing Through Nat Gateway Instead Of Vpc Endpoint**
Service: AWS NAT Gateway | Type: Inefficient Configuration

Workloads in private subnets often access AWS services like S3 or DynamoDB. If this traffic is routed through a NAT Gateway, it incurs both hourly and data processing charges.

- Create VPC Gateway Endpoints for services like S3 and DynamoDB in applicable regions
- Use Interface Endpoints for other AWS services frequently accessed by private subnet workloads
- Update route tables to redirect traffic through the appropriate VPC endpoint instead of NAT Gateway

**Missing Vpc Endpoints For High Volume Aws Service Access**
Service: AWS VPC | Type: Inefficient Network Configuration

When EC2 instances, Lambda functions, or containerised workloads access AWS-managed services without VPC Endpoints, that traffic exits the VPC through a NAT Gateway or Internet Gateway. This introduces unnecessary egress charges and NAT processing costs, especially for data-intensive or high-frequency workloads.

- Provision Gateway Endpoints for S3 and DynamoDB in each VPC that accesses those services
- Create Interface Endpoints (via AWS PrivateLink) for services with frequent or latency-sensitive access (e.g., Secrets Manager, CloudWatch Logs)
- Ensure routing tables and DNS settings support private resolution to AWS services

**Inactive Application Load Balancer Alb**
Service: AWS ELB | Type: Unused Resource

Application Load Balancers that no longer serve active workloads may persist after application migrations, architecture changes, or testing activities. When no incoming requests are processed through the ALB, it continues to generate baseline hourly and LCU charges.

- Identify Application Load Balancers with no active HTTP/HTTPS requests or minimal LCU consumption over a representative time period
- Confirm there are no listener rules, target groups, or backend services depending on the load balancer
- Review application dependencies, DNS records, and security group configurations to validate safe removal

**Inactive Classic Load Balancer Clb**
Service: AWS ELB | Type: Unused Resource

Classic Load Balancers that no longer serve active workloads will persist if they are not properly decommissioned. This often happens after application migrations, architecture changes, or testing activities.

- Identify Classic Load Balancers with no active connections or data transfer over a representative time period
- Confirm there are no health checks, listener rules, or target instances relying on the load balancer
- Review application and infrastructure dependencies to ensure decommissioning will not disrupt services

**Inactive Gateway Load Balancer Glb**
Service: AWS ELB | Type: Unused Resource

Gateway Load Balancers that no longer have active traffic flows can continue to exist indefinitely unless proactively decommissioned. This often happens after network topology changes, security architecture updates, or environment deprecations.

- Identify Gateway Load Balancers with no active traffic or minimal packet forwarding over a representative time window
- Confirm there are no attached target appliances or ongoing inspection flows depending on the load balancer
- Review networking configurations, route tables, and security group dependencies to validate safe removal

**Inactive Nat Gateway**
Service: AWS NAT Gateway | Type: Unused Resource

NAT Gateways are frequently left running after environments are re-architected, workloads are shut down, or connectivity patterns change. In many cases, they continue to incur hourly charges despite no active traffic flowing through them.

- List all NAT Gateways currently provisioned in each region
- Review flow logs, CloudWatch metrics, or billing data to confirm whether any data has been processed through the gateway during the lookback period
- Validate that no private subnet or route table is actively routing traffic through the NAT Gateway

**Inactive Network Load Balancer Nlb**
Service: AWS ELB | Type: Unused Resource

Network Load Balancers that are no longer needed often persist after architecture changes, service decommissioning, or migration projects. When no active TCP connections or traffic flow through the NLB, it still generates hourly operational costs.

- Identify Network Load Balancers with no active connections or minimal data processing over a defined monitoring window
- Confirm there are no registered targets, listener rules, or backend services depending on the NLB
- Review networking and security configurations to ensure the load balancer is not being used for future failover or redundancy scenarios

**Inactive Vpc Interface Endpoint**
Service: AWS VPC | Type: Unused Resource

VPC Interface Endpoints are commonly deployed to meet network security or compliance requirements by enabling private access to AWS services. However, these endpoints often remain provisioned even after the original use case is deprecated.

- Identify all VPC Interface Endpoints currently provisioned in your account
- Review data transfer activity to determine whether any data has flowed through the endpoint over a representative time period
- Confirm whether the associated AWS service or endpoint service is still used by any workloads in the environment

**Unassociated Elastic Ip Address**
Service: AWS EIP | Type: Unused Resource

Elastic IPs are often provisioned but forgotten - left unassociated, or still attached to EC2 instances that have been stopped. Since 1 February 2024 AWS charges $0.005/hr (~$3.60/month) for **every** public IPv4 address, attached or not, so an unassociated EIP is not a special "idle" penalty - it is the ordinary IPv4 charge buying you nothing. The saving from releasing one is the full address cost, and the same charge applies to in-use addresses, which makes IPv4 footprint reduction (IPv6, shared NAT egress, private endpoints) a distinct optimisation lever rather than a hygiene task.

- Release any EIPs that are no longer required
- Automate audits to identify unassociated or inactive EIPs on a recurring basis
- Count public IPv4 addresses in use, not just orphaned ones - at scale the attached-address charge is usually the larger line
- Update IaC templates or provisioning workflows to clean up networking assets during teardown

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
