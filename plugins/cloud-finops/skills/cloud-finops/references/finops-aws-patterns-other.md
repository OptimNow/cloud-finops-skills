---
name: finops-aws-patterns-other
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Anomaly Management"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["SRE", "Platform Engineering"]
fcp_maturity_entry: "Crawl"
---

# AWS Optimization Patterns: Other services

> The AWS pattern catalogue for CloudWatch Logs, AWS Config, CloudTrail,
> EventBridge, OpenSearch, EDP and Marketplace: the signal to look for and the
> remediation for each. A lookup surface, retrieved when hunting a specific
> pattern. For named patterns with runnable detection queries, prefer
> `playbooks/`. The other families are listed in `finops-aws-patterns.md`; billing
> mechanics are in `finops-aws.md`, commitments in `finops-aws-commitments.md`.

> Source: the [Cloud Efficiency Hub](https://www.pointfive.co/efficiency-hub),
> an open, practitioner-governed library powered by PointFive, credited here as
> the Hub asks of anyone who reuses its content.

---

## Other Optimization Patterns (13)

**Double Counting On Edp Commitments**
Service: AWS Marketplace | Type: Commitment Misalignment

Many organisations mistakenly believe that all AWS Marketplace spend automatically contributes to their EDP commitment. In reality, only certain Marketplace transactions, those involving EDP-eligible vendors and transactable SKUs, will count towards a portion of their EDP commitment.

- Request explicit confirmation of EDP eligibility for key Marketplace vendors and SKUs before purchase
- Negotiate drawdown terms into enterprise contracts when possible
- Maintain a list of verified EDP-eligible SKUs used in cost modelling

**Hidden Marketplace Spend Preventing Commitment Optimization**
Service: AWS Marketplace | Type: Commitment Misalignment

In many organisations, AWS Marketplace purchases are lumped into a single consolidated billing line without visibility into individual vendors. This lack of transparency makes it difficult to identify which Marketplace spend is eligible to count toward the EDP cap.

- Enable detailed cost allocation and tagging to isolate Marketplace spend by vendor
- Cross-reference vendor eligibility with AWS to determine which purchases count toward the 25% Marketplace cap
- Update forecasting and commitment planning to include both direct AWS and eligible Marketplace purchases

**Continuous Aws Config Recording In Non Production Environments**
Service: AWS Config | Type: Excessive Recording Frequency

By default, AWS Config is enabled in continuous recording mode. While this may be justified for production workloads where detailed auditability is critical, it is rarely necessary in non-production environments.

- Update AWS Config settings in non-production accounts to daily recording frequency instead of continuous
- Apply environment-specific configuration baselines to enforce lower granularity tracking outside of production
- Validate that compliance and auditing needs remain satisfied after reducing recording frequency

**Overly Permissive Vpc Flow Log Filters Sent To Cloudwatch Logs**
Service: AWS CloudWatch | Type: Inefficient Configuration

VPC Flow Logs configured with the ALL filter and delivered to CloudWatch Logs often result in unnecessarily high log ingestion volumes - especially in high-traffic environments. This setup is rarely required for day-to-day monitoring or security use cases but is commonly enabled by default or for temporary debugging and then left in place.

- Update the VPC Flow Log filter to ACCEPT or REJECT where appropriate
- Consider redirecting logs to S3 for lower-cost storage if detailed analysis is not required in CloudWatch
- Implement periodic audits of logging configurations to catch overly verbose setups

**Unfiltered Recording Of High Churn Resource Types In Aws Config**
Service: AWS Config | Type: Inefficient Configuration

By default, AWS Config can be set to record changes across all supported resource types, including those that change frequently, such as security group rules, IAM role policies, route tables, or network interfaces - frequent ephemeral resources in containerised or auto-scaling setups. These high-churn resources can generate an outsized number of configuration items and inflate costs - especially in dynamic or large-scale environments. This inefficiency arises when recording is enabled indiscriminately across all resources without evaluating whether the data is necessary.

- Limit AWS Config recording to only essential resource types using resource recording groups
- Exclude high-churn resource types that provide minimal compliance or operational value
- Disable Config entirely in sandbox, test, or dev accounts if configuration history is not needed

**Excessive Cloudwatch Log Volume From Persistently Enabled Debugging**
Service: AWS CloudWatch | Type: Inefficient Configuration

Engineers often enable verbose logging (e.g., debug or trace-level) during development or troubleshooting, then forget to disable it after deployment. This results in elevated log ingestion rates - and therefore costs - even when the detailed logs are no longer needed.

- Reduce log verbosity from debug/trace to info or warn levels where appropriate
- Implement logging configuration standards across environments, with production defaults
- Use dynamic log level toggling (e.g., via environment variables or feature flags) to avoid persistent debug logging

**Disabled Retry Policies In Eventbridge**
Service: AWS EventBridge | Type: Misconfiguration

By default, EventBridge includes retry mechanisms for delivery failures, particularly when targets like Lambda functions or Step Functions fail to process an event. However, if these retry policies are disabled or misconfigured, EventBridge may treat failed deliveries as successful, prompting upstream services to republish the same event multiple times in response to undelivered outcomes.

- Enable built-in retry policies on EventBridge rules to reduce reliance on external retry logic
- Confirm downstream targets are configured with error handling (e.g., DLQs, retry settings)
- Audit event patterns for high duplication rates and correlate with retry settings

**Suboptimal Log Class Configuration In Cloudwatch**
Service: AWS CloudWatch | Type: Misconfiguration

By default, CloudWatch Log Groups use the Standard log class, which applies higher rates for both ingestion and storage. AWS also offers an Infrequent Access (IA) log class designed for logs that are rarely queried - such as audit trails, debugging output, or compliance records.

- Create new log groups using the Infrequent Access class for applicable use cases
- Update application and service configurations to route logs to the new log groups
- Use subscription filters or log routing to separate high-access logs (Standard) from infrequent logs (IA)

**Excessive Aws Config Costs From Spot Instances**
Service: AWS Config | Type: Over-Recording of Ephemeral Resources

Spot Instances are designed to be short-lived, with frequent interruptions and replacements. When AWS Config continuously records every lifecycle change for these instances, it produces a large number of CIRs.

- Use tag-based exclusions to prevent AWS Config from recording ephemeral Spot Instances and other transient resources
- Apply standardised tagging (e.g., `finops:config-exclude:true`) and configure AWS Config to filter them out
- If some visibility is required, switch Config from continuous to periodic recording to reduce event volume

**Duplicate Or Overlapping Aws Cloudtrail Trails**
Service: AWS CloudTrail | Type: Redundant Configuration

AWS CloudTrail enables event logging across AWS services, but when multiple trails are configured to log overlapping events - especially data events - it can result in redundant charges and unnecessary storage or ingestion costs. This commonly occurs in decentralised environments where teams create trails independently, unaware of existing coverage or shared logging destinations. Each trail that records data events contributes to billing on a per-event basis, even if the same activity is logged by multiple trails.

- Delete or disable redundant trails that provide no unique audit or compliance value
- Consolidate overlapping trails into a single unified configuration where feasible
- Use centralised log destinations (e.g., one S3 bucket) to reduce storage and ingestion cost

**Suboptimal Use Of Intel Based Instances In Opensearch**
Service: AWS OpenSearch | Type: Suboptimal Instance Selection

AWS Graviton processors are designed to deliver better price-performance than comparable Intel-based instances, often reducing cost by 20-30% at equivalent workload performance. OpenSearch domains running on older Intel-based families consume more spend without providing additional capability.

- Migrate OpenSearch domains from Intel-based instances (e.g., `m5`, `r5`, `i4i`) to equivalent Graviton families (`m6g`, `c6g`, `r6g`, `i4g`)
- Use in-place instance type updates for clusters where supported to minimise downtime
- Benchmark performance after migration to validate expected cost-performance improvements

**Unnecessarily High Recording Granularity In Aws Config**
Service: AWS Config | Type: Suboptimal Recording Configuration

Organisations frequently inherit continuous recording by default (e.g., through landing zones) without validating the business need for per-change granularity across all resource types and environments. In change-heavy accounts (ephemeral resources, CI/CD churn, autoscaling), continuous mode drives very high CIR volumes with limited additional operational value.

- Shift suitable resource types and/or non-production environments from continuous to periodic recording where real-time change tracking isn't required.
- Scope recording frequency by environment: continuous for production or high-risk resources; periodic for development/test or low-risk resources.
- Document the rationale and ownership (e.g., security vs. platform) to ensure shared expectations on visibility vs. cost.

**Inactive Cloudwatch Log Group**
Service: AWS CloudWatch | Type: Unused Resource

CloudWatch log groups often persist long after their usefulness has expired. In some cases, they are associated with applications or resources that are no longer active.

- Identify log groups with significant stored log volume but no recent ingestion activity
- Review historical usage to determine if log data is still being used for operational, security, or compliance purposes
- Evaluate whether the log group is associated with an active application or AWS resource
- Set a retention period: by default a log group keeps data indefinitely ("Never Expire") until one is set. Events past retention are marked for deletion and stop adding to storage cost at that point, although deletion can take up to 72 hours ([CloudWatch Logs, log groups and retention](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html), read 22 October 2026)

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
