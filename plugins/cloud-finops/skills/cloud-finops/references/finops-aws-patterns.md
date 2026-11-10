---
name: finops-aws-patterns
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Anomaly Management"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["SRE", "Platform Engineering"]
fcp_maturity_entry: "Crawl"
business_coverage: ["aws:waste:deep"]
questions:
  - "Where is the list of AWS cost optimisation patterns, and how is it organised?"
  - "Which file covers AWS compute, storage, database or networking inefficiencies?"
  - "Is there a catalogue of AWS waste patterns we can run through account by account?"
  - "Où trouver le catalogue des gaspillages AWS par famille de services ?"
---

# AWS Optimization Pattern Catalogue

> The enumerated AWS inefficiency catalogue, split by service family so a
> question loads only the family it is about. This file is the index: open the
> family file below. For named waste patterns with runnable detection queries,
> prefer `playbooks/`. For billing mechanics see `finops-aws-billing.md`; for
> commitments see `finops-aws-commitments.md`.

---

## The family files

| File | Covers | Patterns |
|---|---|---|
| `finops-aws-patterns-compute.md` | EC2, Lambda, EKS, ECS / Fargate, EMR, Athena, AppStream, WorkSpaces | 42 |
| `finops-aws-patterns-storage.md` | S3, EBS, EFS, snapshots, AWS Backup | 28 |
| `finops-aws-patterns-databases.md` | RDS, Aurora, DynamoDB, ElastiCache, MemoryDB, OpenSearch, DMS; RDS cost strategy; database commitment decision tree (incl. Redshift) | 33 |
| `finops-aws-patterns-networking.md` | NAT gateways, VPC endpoints, load balancers, cross-AZ transfer, CloudFront, Elastic IPs; Direct Connect flat-rate pricing | 15 |
| `finops-aws-patterns-other.md` | CloudWatch Logs, AWS Config, CloudTrail, EventBridge, OpenSearch, EDP, Marketplace; security service billing (WAF, GuardDuty, Inspector, Access Analyzer) | 13 |

Each pattern gives the service, the type of inefficiency, the signal to look for
and the remediation. The database file also carries the RDS cost management
strategy and the database commitment discount decision tree.

> Source: the [Cloud Efficiency Hub](https://www.pointfive.co/efficiency-hub),
> an open, practitioner-governed library powered by PointFive, credited here as
> the Hub asks of anyone who reuses its content.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
