---
name: finops-aws-patterns-compute
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Anomaly Management"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["SRE", "Platform Engineering"]
fcp_maturity_entry: "Crawl"
business_coverage: ["aws:waste:deep"]
---

# AWS Optimization Patterns: Compute

> The AWS pattern catalogue for EC2, Lambda, EKS, ECS and Fargate, EMR, Athena,
> AppStream, WorkSpaces and Step Functions: the signal to look for and the
> remediation for each. A lookup surface, retrieved when hunting a specific
> pattern. For named patterns with runnable detection queries, prefer
> `playbooks/`. The other families are listed in `finops-aws-patterns.md`; billing
> mechanics are in `finops-aws-billing.md`, commitments in `finops-aws-commitments.md`.

> Source: the [Cloud Efficiency Hub](https://www.pointfive.co/efficiency-hub),
> an open, practitioner-governed library powered by PointFive, credited here as
> the Hub asks of anyone who reuses its content.

---

## Compute Optimization Patterns (42)

**Idle Emr Cluster Without Auto Termination Policy**
Service: AWS EMR | Type: Inactive Resource

Amazon EMR clusters often run on large, multi-node EC2 fleets, making them costly to leave running unnecessarily. If a cluster becomes idle - no longer processing jobs - but is not terminated, it continues accruing EC2 and EMR service charges.

- Enable an auto-termination policy on EMR clusters that are intended to be short-lived or batch-oriented
- Review and shut down idle clusters that are no longer actively running jobs
- Educate data engineering teams on the cost implications of leaving clusters running

**EMR billing basis by deployment mode.** The EMR charge sits on top of the compute
underneath, and what it meters depends on the mode:

- **EMR on EC2:** the EMR price is added to the price of each EC2 instance in the cluster,
  billed per second with a one-minute minimum, so an idle cluster pays both.
- **EMR on EKS:** the EMR charge is added to the EKS costs (EC2 nodes or Fargate) and
  metered on the vCPU and memory of the EMR driver and executor pods, from the start of
  the EMR image download until the pod terminates, rounded up to the second. AWS's own
  example charges the job's pods, not the node capacity. AWS pages differ on whether that
  means requested or consumed resources (the pricing page says "requested", the
  development guide "consumption"), so check the bill against executor requests before
  assuming oversized requests cost nothing extra. The charge applies to any pod running
  an image derived from the EMR runtime, whatever registry holds the image and however
  the job is submitted (StartJobRun, the Spark operator or spark-submit).
- **EMR Serverless:** billed on the vCPU, memory and storage the workers consume, from
  when a worker is ready until it stops, per second with a one-minute minimum, with no
  node cost underneath.

The cheaper mode for a workload depends on price ratios that move: the EMR on EKS charge
fell 30% on 23 October 2026, so recompute any earlier EC2 versus EKS comparison with
current pricing. Sources: <https://aws.amazon.com/emr/pricing/>,
<https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/spark-operator.html>,
<https://aws.amazon.com/about-aws/whats-new/2026/10/emr-eks-reduces-emr-charge-30-percent/>

**Inactive Aws Workspace**
Service: AWS WorkSpaces | Type: Inactive Resource

If an AWS WorkSpace has been provisioned but not accessed in a meaningful timeframe, it may represent waste - particularly if it is set to monthly billing. Many organisations leave WorkSpaces active for users who no longer need them or have shifted roles, leading to persistent charges without corresponding business value.

- Decommission WorkSpaces that are no longer needed
- Switch billing mode from monthly to auto-stop for WorkSpaces with intermittent usage
- Automate reviews of WorkSpaces based on last login data to flag stale resources for cleanup or conversion

**Suboptimal Region For Ec2 Instance**
Service: AWS EC2 | Type: Inefficient Architecture

Workloads are sometimes deployed in specific AWS regions based on legacy decisions, developer convenience, or perceived performance requirements. However, regional EC2 pricing can vary significantly, and placing instances in a suboptimal region can lead to higher compute costs, increased data transfer charges, or both.

- Identify EC2 instances that generate significant cross-region or cross-AZ data transfer
- Review the current region's EC2 pricing compared to other AWS regions supporting the same instance type
- Evaluate whether the instance communicates heavily with services or users located in another region

**Suboptimal Region For Internet Only Ec2 Instance**
Service: AWS EC2 | Type: Inefficient Architecture

When an EC2 instance is dedicated primarily to internet-facing traffic, regional differences in data transfer pricing can drive a substantial portion of total costs. Hosting such workloads in a region with higher egress rates leads to elevated expenses without improving performance.

- Identify EC2 instances whose primary traffic flows are outbound to the public internet rather than within AWS or private networks
- Review the region associated with each instance and compare public Data Transfer Out pricing against lower-cost regions
- Assess latency requirements, regulatory considerations, and service availability constraints that may impact regional choices

**Suboptimal Use Of On Demand Instances In A Non Production Eks Cluster**
Service: AWS EKS | Type: Inefficient Architecture

Running non-production clusters solely on On-Demand Instances results in unnecessarily high compute costs. Development, testing, and QA environments typically tolerate interruptions and do not require the continuous availability guaranteed by On-Demand capacity.

- Identify non-production EKS clusters based on environment tagging, naming conventions, or cluster metadata
- Review node group configurations to determine whether all nodes use On-Demand Instances
- Assess workload criticality and tolerance for Spot interruptions based on application requirements

**Excessive Lambda Duration From Synchronous Waiting**
Service: AWS Lambda | Type: Inefficient Configuration

Some Lambda functions perform synchronous calls to other services, APIs, or internal microservices and wait for the response before proceeding. During this time, the Lambda is idle from a compute perspective but still fully billed.

- Redesign functions to offload synchronous calls using asynchronous patterns (e.g., queues, event buses, Step Functions)
- Break apart long-running workflows into smaller chained or event-driven Lambdas
- Optimise memory allocation to minimise idle cost when waiting cannot be avoided

**Idle Ecs Container Instances Due To Asg Minimum Capacity**
Service: AWS ECS | Type: Inefficient Configuration

When ECS clusters are configured with an Auto Scaling Group that maintains a minimum number of EC2 instances (e.g., min = 1 or higher), the instances remain active even when there are no tasks scheduled. This leads to idle compute capacity and unnecessary EC2 charges. Instead, ECS Capacity Providers support target tracking scaling policies that can scale the ASG to zero when idle and automatically increase capacity when new tasks or services are scheduled.

- Configure an ECS Capacity Provider for the cluster and attach a target tracking scaling policy
- Set the ASG minimum capacity to 0 to allow scale-down during idle periods
- Ensure ECS services are configured with appropriate scaling triggers (e.g., CPU or memory utilisation)

**Missing Scheduled Shutdown For Non Production Ec2 Instances**
Service: AWS EC2 | Type: Inefficient Configuration

Non-production EC2 instances are often provisioned for daytime-only usage but remain running 24/7 out of convenience or oversight. This results in unnecessary compute charges, even if the workload is inactive for 16+ hours per day.

- Implement scheduled shutdowns using AWS Instance Scheduler or EventBridge rules
- Ensure stateful data is retained via attached EBS volumes or AMIs
- Set start/stop windows aligned to working hours (e.g., 8 a.m.-6 p.m. weekdays)

**Orphaned And Overprovisioned Resources In Eks Clusters**
Service: AWS EKS | Type: Inefficient Configuration

In EKS environments, cluster sprawl can occur when workloads are removed but underlying resources remain. Common issues include persistent volumes no longer mounted by pods, services still backed by ELBs despite being unused, and overprovisioned nodes for workloads that no longer exist.

- Remove unused PVCs to deprovision backing EBS volumes
- Delete idle Services to release associated ELBs and IP addresses
- Clean up inactive namespaces and workloads

**Outdated Eks Cluster Incurring Extended Support Charges**
Service: AWS EKS | Type: Inefficient Configuration

When an EKS cluster remains on a Kubernetes version that has reached the end of standard support, AWS begins charging an additional Extended Support fee. These charges often arise from delays in upgrade cycles, uncertainty about workload compatibility, or overlooked legacy clusters.

- Identify clusters running Kubernetes versions that have reached end of standard support
- Confirm whether the cluster is incurring Extended Support charges
- Review upgrade history and backlog to understand why the version was not updated

**Suboptimal Appstream Fleet Auto Scaling Policies**
Service: AWS AppStream 2.0 | Type: Inefficient Configuration

When fleet auto scaling policies maintain more active instances than are required to support current usage - particularly during off-peak hours - organisations incur unnecessary compute costs. Fleets often remain oversized due to conservative default configurations or lack of schedule-based scaling.

- Adjust minimum instance counts in auto scaling policies to reflect observed demand
- Implement schedule-based scaling to reduce instance counts during predictable low-usage periods and increase during peak hours
- Regularly review and update scaling policies based on current usage data to ensure ongoing efficiency

**Suboptimal Memory To Cpu Ratio In Eks Cluster Node**
Service: AWS EKS | Type: Inefficient Configuration

When the EC2 instance types used for EKS node groups have a memory-to-CPU ratio that doesn't match the workload profile, the result is poor bin-packing efficiency. For example, if memory-intensive containers are scheduled on compute-optimized nodes, memory may run out first while CPU remains unused.

- Review container-level memory and CPU requests and limits across the cluster
- Assess node-level resource utilisation to detect fragmentation (e.g., memory maxed out while CPU remains idle)
- Compare the vCPU-to-memory ratio of node types to the average resource profile of scheduled workloads

**Inefficient Workflow Design In Aws Step Functions**
Service: AWS Step Functions | Type: Misconfiguration

Improper design choices in AWS Step Functions can lead to unnecessary charges. For example, using Standard Workflows for short-lived, high-frequency executions leads to excessive per-transition charges, while complex workflows with many state transitions multiply per-transition cost across the lifetime of the application.

- Choose Express workflows for short-lived, high-volume executions
- Use Standard workflows for long-running, infrequent executions
- Combine simple logic steps into a single Lambda or use intrinsic functions

**Recursive Invocation Loop Between Lambda And Sqs**
Service: AWS Lambda | Type: Misconfigured Architecture

When a Lambda function processes messages from an SQS queue but fails to handle certain messages properly, the same messages may be returned to the queue and retried repeatedly. In some cases, especially if the Lambda is also writing messages back to the same or a chained queue, this can create a recursive invocation loop.

- Introduce a dead-letter queue (DLQ) to route failed messages after a maximum number of retries
- Set a maximumReceiveCount on the SQS redrive policy to avoid indefinite reprocessing
- Refactor the Lambda logic to prevent re-enqueuing the same message unintentionally

**Inefficient Snapstart Configuration In Lambda**
Service: AWS Lambda | Type: Misconfigured Performance Optimization

SnapStart reduces cold-start latency, but when configured inefficiently, it can increase costs. High-traffic workloads can trigger frequent snapshot restorations, multiplying costs.

- Implement concurrency controls to reduce excess restorations during high traffic bursts
- Optimise function initialisation to minimise Init phase duration by loading only essential dependencies
- Use pre-snapshot hooks (for Java) to prepare code execution and reduce overhead before the snapshot is taken

**Unnecessary Multi Az Deployment For Non Production Ec2 Instances**
Service: AWS EC2 | Type: Misconfigured Redundancy

Multi-AZ deployment is often essential for production workloads, but its use in non-production environments (e.g., development, test, QA) offers minimal value. These environments typically do not require high availability, yet still incur the full cost of redundant compute, storage, and data transfer.

- Reconfigure EC2 workloads in non-production environments to use a single Availability Zone
- Avoid distributing instances or traffic across multiple AZs unless justified by a specific requirement
- Establish environment-based architectural guidelines to limit Multi-AZ usage

**Unconverted Convertible Ec2 Reserved Instances**
Service: AWS EC2 | Type: Misconfigured Reservation

Convertible Reserved Instances provide valuable pricing flexibility - but that flexibility is often underused. When EC2 workloads shift across instance families or OS types, the original RI may no longer apply to active usage.

- Use the AWS Management Console or CLI to convert unused Convertible RIs to match current EC2 instance usage
- Ensure the new reservation configuration has equal or greater value, as required by AWS
- Monitor usage regularly to identify when new conversions may be needed

**Unmanaged Growth Of Athena Query Output Buckets**
Service: AWS Athena | Type: Missing Lifecycle Policy

Athena generates a new S3 object for every query result, regardless of whether the output is needed long term. Over time, this leads to uncontrolled growth of the output bucket, especially in environments with repetitive queries such as cost and usage reporting.

- Implement S3 Lifecycle Policies on Athena output buckets to automatically expire objects after a set period (e.g., 30, 60, 90 days)
- Use prefixes or tags to differentiate between temporary query outputs and long-term reports, applying tailored retention rules
- Regularly review and adjust retention policies to balance cost efficiency with business and compliance needs

**Orphaned Kubernetes Resources E7E68**
Service: AWS EKS | Type: Orphaned Resource

In Kubernetes environments, resources such as ConfigMaps, Secrets, Services, and Persistent Volume Claims (PVCs) are often created dynamically by applications or deployment pipelines. When applications are removed or reconfigured, these resources may be left behind if not explicitly cleaned up.

- Delete orphaned Persistent Volume Claims to release underlying storage (e.g., EBS volumes)
- Remove unused Services, especially those of type LoadBalancer, to eliminate unnecessary networking charges
- Clean up ConfigMaps and Secrets that are no longer referenced by any active workload
- Implement tagging/labelling standards for all workloads to simplify orphan detection

**Stale Dedicated Hosts For Stopped Ec2 Mac Instances**
Service: AWS EC2 | Type: Orphaned Resource

When an EC2 Mac instance is stopped or terminated, its associated dedicated host remains allocated by default. Because Mac instances are the only EC2 type billed at the host level, charges continue to accrue as long as the host is retained.

- Release Mac dedicated hosts after stopping or terminating Mac EC2 instances if no longer needed
- Update automation workflows to include host deallocation logic when applicable
- Enable lifecycle tracking of dedicated hosts to avoid forgotten allocations

**Underutilized Ec2 Commitment Due To Workload Drift**
Service: AWS EC2 | Type: Overcommitted Reservation

When EC2 usage declines, shifts to different instance families, or moves to other services (e.g., containers or serverless), organisations may find that previously purchased Standard Reserved Instances or Savings Plans no longer match current workload patterns. This misalignment results in underutilised commitments - where costs are still incurred, but no usage is benefiting from the associated discounts.

- Review existing workloads to identify candidates that could migrate to the underutilised instance families
- For new or scaling workloads, prioritise launching on instance types that align with unused commitments
- Where possible, upgrade existing workloads to fit larger reserved types - while tracking the change to avoid overcommitment in future renewals

**Overprovisioned Memory Allocation For Lambda Functions**
Service: AWS Lambda | Type: Overprovisioned Resource

Each Lambda function must be configured with a memory setting, which indirectly controls the amount of CPU and networking performance allocated. In many environments, memory settings are defined arbitrarily or left unchanged as functions evolve.

- Use tools like AWS Lambda Power Tuning to benchmark and optimise memory and vCPU settings
- Incorporate right-sizing into CI/CD workflows to evaluate configuration during deployment
- Apply consistent tagging or governance to track functions requiring periodic review

**Underutilized Ec2 Instance**
Service: AWS EC2 | Type: Overprovisioned Resource

EC2 instances are often overprovisioned based on rough estimates, legacy patterns, or performance buffer assumptions. If an instance consistently uses only a small fraction of its provisioned CPU or memory, it likely represents an opportunity for rightsizing.

- Review average CPU and memory utilisation of running EC2 instances.
- Determine whether actual usage justifies the selected instance type or size
- Confirm whether performance buffers, licensing rules, or other constraints require overprovisioning

**Underuse Of Fargate Spot For Interruptible Workloads**
Service: AWS Fargate | Type: Pricing Model Misalignment

Many teams run workloads on standard Fargate pricing even when the workload is fault-tolerant and could tolerate interruptions. Fargate Spot provides the same performance characteristics at up to 70% lower cost, making it ideal for stateless jobs, batch processing, CI/CD runners, or retry-friendly microservices.

- Update ECS/EKS task definitions or profiles to enable Fargate Spot
- For mixed environments, use capacity providers or placement strategies to route eligible tasks to Spot
- Monitor interruption rates and implement retry logic where necessary

**Recursive Lambda Function Invocation**
Service: AWS Lambda | Type: Recursive Invocation Misconfiguration

Recursive invocation occurs when a Lambda function triggers itself directly or indirectly, often through an event source like SQS, SNS, or another Lambda. This loop can be unintentional - for example, when the function writes output to a queue it also consumes.

- Refactor logic to prevent self-invocation or recursive event loops
- Avoid writing to the same queue or stream that triggers the function
- Implement Dead Letter Queues to prevent retry loops

**Excessive Lambda Retries Retry Storms**
Service: AWS Lambda | Type: Retry Misconfiguration

Retry storms occur when a function fails and is automatically retried repeatedly due to default retry behaviour for asynchronous events (e.g., SQS, EventBridge). If the error is persistent and unhandled, retries can accumulate rapidly - often invisibly - creating a large volume of billable executions with no successful outcome.

- Configure DLQs to isolate and inspect failed invocations
- Implement exponential backoff or circuit breaker patterns in retry logic
- Set appropriate retry limits on event source mappings

**Suboptimal Architecture Selection In Aws Fargate**
Service: AWS Fargate | Type: Suboptimal Architecture Selection

AWS Fargate supports both x86 and Graviton2 (ARM64) CPU architectures, but by default, many workloads continue to run on x86. Graviton2 delivers significantly better price-performance, especially for stateless, scale-out container workloads.

- Update Fargate task definitions to use `"runtimePlatform": { "cpuArchitecture": "ARM64" }` where supported
- Rebuild container images for multi-architecture compatibility if needed
- Benchmark ARM-based performance to validate expected savings

**Suboptimal Architecture Configuration For Lambda Functions**
Service: AWS Lambda | Type: Suboptimal Configuration

While many AWS customers have migrated EC2 workloads to Graviton to reduce costs, Lambda functions often remain on the default x86 architecture. AWS Graviton2 (ARM) offers lower pricing and equal or better performance for most supported runtimes - yet adoption remains uneven due to legacy defaults or lack of awareness.

- Update Lambda function configurations to use ARM/Graviton2 where compatible
- Benchmark function performance and duration to validate equal or improved performance
- For stable, high-throughput functions, consider pairing architecture changes with Compute Savings Plans
- **Lambda Managed Instances is a different cost model, and it now reaches Graviton5.**
  Lambda Managed Instances runs functions on EC2 instances in your account while Lambda
  keeps managing instance lifecycle, patching, routing and scaling. The point for FinOps
  is that it bills through EC2 pricing rather than standard per-invocation Lambda
  billing, so the architecture question becomes an instance-generation question. Since
  9 September 2026 it supports Graviton5-powered C9g, C9gd, M9g and M9gd instances,
  which AWS states deliver up to 25% better compute performance than Graviton4. Two
  things to check: a capacity provider pinned to a specific older instance type does not
  move on its own, whereas one left on `default` has Graviton5 added to the pool Lambda
  picks from; and "up to 25% faster" is a performance claim, not a price cut - it only
  becomes a saving if the workload finishes sooner or packs onto fewer instances, so
  benchmark before counting it. Source:
  https://aws.amazon.com/about-aws/whats-new/2026/09/aws-lambda-graviton5-ec2/

**Suboptimal Architecture Selection In Aws Lambda**
Service: AWS Lambda | Type: Suboptimal Configuration

Lambda functions default to the x86\_64 architecture, which is more expensive than Arm64. For many workloads, especially those written in interpreted languages (e.g., Python, Node.js) or compiled to architecture-neutral bytecode (e.g., Java), there is no dependency on x86-specific binaries.

- Benchmark representative functions on both architectures to validate performance and compatibility
- For functions using architecture-neutral runtimes or dependencies, migrate to Arm64 via configuration update
- Ensure CI/CD pipelines and IaC templates default to Arm64 for new functions

**Inefficient File Format And Layout For Athena Queries**
Service: AWS Athena | Type: Suboptimal Data Layout or Format

Storing raw JSON or CSV files in S3 - especially when written frequently in small batches - leads to excessive scan costs in Athena. These formats are row-based and verbose, requiring Athena to scan and parse the full content even when only a few fields are queried.

- Convert raw data to columnar formats such as Parquet or ORC to reduce scan size
- Partition data based on common query dimensions (e.g., date, tenant ID)
- Consolidate small files into larger batches to improve scan efficiency

**Inefficient Processor Selection In Ec2 Instances**
Service: AWS EC2 | Type: Suboptimal Instance Family Selection

Many organisations default to Intel-based EC2 instances due to familiarity or assumptions about workload compatibility. However, AWS offers AMD and Graviton-based alternatives that often deliver significantly better price-performance for general-purpose and compute-optimized workloads.

- Check for architecture-specific performance issues or compatibility blockers before switching
- Benchmark representative workloads on Intel, AMD, and Graviton instance types
- Migrate to the instance family that offers the best price-performance for the workload

**Overreliance On Lambda At Sustained Scale**
Service: AWS Lambda | Type: Suboptimal Pricing Model

Lambda is designed for simplicity and elasticity, but its pricing model becomes expensive at scale. When a function runs frequently (e.g., millions of invocations per day) or for extended durations, the cumulative cost may exceed that of continuously running infrastructure.

- Establish thresholds for Lambda usage that trigger cost-efficiency reviews
- Evaluate total Lambda cost versus equivalent EC2/ECS/EKS workloads
- Consider replatforming long-running or consistently triggered workloads to containerised or instance-based compute

**Suboptimal Use Of Compute Savings Plans For Specialized Instances**
Service: AWS EC2 | Type: Suboptimal Pricing Model

Accelerated EC2 instance types such as `p5.48xlarge` and `p5en.48xlarge (often used for ML/AI workloads)` are eligible for Compute Savings Plans, but the discount rates offered are modest compared to more common instance families. When organisations rely solely on CSPs, these lower priority instances are typically the last to benefit from the plan, especially if other instance types consume most of the discounted hours.

- Consider using dedicated EC2 Instance Savings Plans instead of CSPs for predictable, high-utilisation p5 workloads
- Model CSP allocation on actual discount percentages in order to determine whether p-type instances are likely to be left uncovered
- Compare total cost of ownership between CSPs and dedicated instance savings plans for your specific usage patterns

**Suboptimal Use Of On Demand Instances In Fault Tolerant Ec2 Workloads**
Service: AWS EC2 | Type: Suboptimal Pricing Model

Many EC2 workloads - such as development environments, test jobs, stateless services, and data processing pipelines - can tolerate interruptions and do not require the reliability of On-Demand pricing. Using On-Demand instances in these scenarios drives up cost without adding value.

- Reconfigure eligible workloads to use Spot Instances via launch templates or Auto Scaling policies
- Use mixed-instance and capacity-optimized allocation strategies for better availability
- Apply On-Demand only where availability, SLA, or licensing requirements demand it

**Underutilized Kubernetes Workload**
Service: AWS EKS | Type: Underutilization

When Kubernetes workloads request more CPU and memory than they consume, nodes must reserve capacity that remains unused. This leads to lower node density, forcing the cluster to maintain more instances than necessary.

- Identify workloads where average CPU and memory usage are consistently much lower than requested values
- Analyse container-level metrics to assess request-to-usage ratios over time
- Use Vertical Pod Autoscaler recommendations, if available, to identify right-sizing opportunities

**Underutilized Or Overprovisioned Appstream Instances**
Service: AWS AppStream 2.0 | Type: Underutilization

AppStream fleets often default to instance types designed for worst-case or peak usage scenarios, even when average workloads are significantly lighter. This leads to consistently low utilisation of CPU, memory, or GPU resources and inflated infrastructure costs.

- Right-size AppStream fleets by selecting smaller or less specialised instance types that meet current workload demands
- Conduct performance testing after downgrading to ensure that application responsiveness and user experience are preserved
- Update provisioning templates or fleet configurations to reflect optimised instance types going forward

**Underutilized Instances In Ec2 Auto Scaling Group**
Service: AWS EC2 | Type: Underutilized Resource

Oversized instances within Auto Scaling Groups lead to inflated baseline costs, even when scaling adjusts the number of instances dynamically. When workloads consistently use only a fraction of the available CPU, memory, or network capacity, there is an opportunity to downsize to smaller, less expensive instance types without sacrificing performance.

- Evaluate smaller instance types that better match the workload's actual resource requirements.
- Update the launch template or configuration for the Auto Scaling Group to use the selected instance type, and deploy changes during a low-traffic window if needed.
- After downsizing, monitor performance metrics to ensure the workload continues to meet application and SLA expectations.

**Inactive Appstream Image Builder Or App Block Builder Instances**
Service: AWS AppStream 2.0 | Type: Unused Resource

When AppStream builder instances are left running but unused, they continue to generate compute charges without delivering any value. These instances are commonly left active after configuration or image creation is completed but can be safely stopped or terminated when not in use.

- Stop or decommission builder instances that are no longer required.
- Implement an automated workflow - such as a scheduled Lambda function - that stops builder instances after a defined period of inactivity.
- Establish operational guidelines to ensure builder instances are shut down after image creation or testing tasks are completed.

**Inactive Ec2 Instance**
Service: AWS EC2 | Type: Unused Resource

This inefficiency occurs when an EC2 instance remains in a running state but is not actively utilised. These instances may be remnants of past projects, forgotten development environments, or temporarily created for testing and never decommissioned.

- Identify EC2 instances that have been running throughout the lookback period
- Review CPU utilisation, network throughput, and disk activity for sustained inactivity
- Check for the absence of inbound or outbound connections over the same period

**Inactive Eks Cluster**
Service: AWS EKS | Type: Unused Resource

Clusters that no longer run active workloads but remain provisioned continue incurring hourly control plane costs and may also maintain associated infrastructure like node groups or VPC components. Inactive clusters often persist after environment decommissioning, project shutdowns, or migrations.

- Identify EKS clusters with no active Deployments, StatefulSets, DaemonSets, CronJobs, or running pods over a representative time window
- Review node group activity and verify whether any EC2 instances or Fargate tasks are currently attached to the cluster
- Analyse cluster API server logs or CloudWatch metrics to confirm minimal API usage and cluster activity

**Inactive Kubernetes Workload**
Service: AWS EKS | Type: Unused Resource

Workloads with consistently low CPU and memory usage may no longer serve active traffic or scheduled tasks, but continue reserving resources within the cluster. These idle deployments often remain after project migrations, feature deprecations, or experimentation.

- Identify Kubernetes workloads (Deployments, StatefulSets, DaemonSets, or CronJobs) with minimal CPU and memory usage over a representative time window
- Review service exposure, pod restart patterns, and ingress configurations to validate inactivity
- Assess workload labels, annotations, and namespaces to determine original ownership and purpose

**Unnecessary Costs From Unused Lambda Versions With Snapstart**
Service: AWS Lambda | Type: Version Sprawl

Many teams publish new Lambda versions frequently (e.g., through CI/CD pipelines) but do not clean up old ones. When SnapStart is enabled, each of these versions retains an active snapshot in the cache, generating ongoing charges.

- Delete unused Lambda function versions with SnapStart enabled to eliminate unnecessary cache charges
- Implement version lifecycle management practices in CI/CD pipelines to automatically clean up old versions
- Retain only the most recent versions required for rollback or audit purposes

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
