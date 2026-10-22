---
name: finops-aws-patterns-storage
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Usage Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Anomaly Management"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["SRE", "Platform Engineering"]
fcp_maturity_entry: "Crawl"
---

# AWS Optimization Patterns: Storage

> The AWS pattern catalogue for S3, EBS, EFS, snapshots and AWS Backup: the signal
> to look for and the remediation for each. A lookup surface, retrieved when
> hunting a specific pattern. For named patterns with runnable detection queries,
> prefer `playbooks/`. The other families are listed in `finops-aws-patterns.md`;
> billing mechanics are in `finops-aws-billing.md`, commitments in `finops-aws-
> commitments.md`.

> Source: the [Cloud Efficiency Hub](https://www.pointfive.co/efficiency-hub),
> an open, practitioner-governed library powered by PointFive, credited here as
> the Hub asks of anyone who reuses its content.

---

## Storage Optimization Patterns (28)

**Overprovisioned Throughput In Efs**
Service: AWS EFS | Type: Explanation

When file systems are launched with Provisioned Throughput, teams often overestimate future demand - especially in environments cloned from production or sized “just to be safe.” Over time, many workloads consume far less throughput than allocated, especially in dev/test environments or during periods of reduced usage. These overprovisioned settings can silently accrue substantial monthly charges that go unnoticed without intentional review.

- Reconfigure overprovisioned file systems with a reduced Provisioned Throughput value
- For workloads with low and predictable throughput, consider switching to Elastic Throughput
- For dev/test systems cloned from production, adjust throughput settings independently

**Excessive Listbucket Api Calls To An S3 Bucket**
Service: AWS S3 | Type: Inefficient Architecture

ListBucket requests are commonly used to enumerate objects in a bucket, such as by backup systems, scheduled sync jobs, data catalogs, or monitoring tools. When these operations are frequent or target buckets with large object counts, they can generate disproportionately high request charges.

- Identify buckets with a high volume of ListObjects or ListObjectsV2 API requests during the lookback period
- Review whether these requests are part of scheduled automation, backup jobs, or inventory scans
- Check if the frequency of list operations aligns with actual business or operational requirements

**Delayed Transition Of Objects To Intelligent Tiering In An S3 Bucket**
Service: AWS S3 | Type: Inefficient Configuration

Some S3 lifecycle policies are configured to transition objects from Standard storage to Intelligent-Tiering after a fixed number of days (e.g., 30 days). This creates a delay where objects reside in S3 Standard, incurring higher storage costs without benefit.

- Identify buckets where Intelligent-Tiering is the intended or primary storage class
- Review how new objects are placed into those buckets - determine whether they are uploaded directly into Intelligent-Tiering or initially stored in S3 Standard and later moved to Intelligent-Tiering via a Lifecycle Policy
- Evaluate whether the delay provides any functional or operational benefit, or if it is a legacy configuration

**Infrequently Accessed Objects Stored In S3 Standard Tier**
Service: AWS S3 | Type: Inefficient Configuration

S3 Standard is the default storage class and is often used by default even for data that is rarely accessed. Keeping large volumes of infrequently accessed data in S3 Standard leads to unnecessary costs.

- Identify buckets or prefixes where large volumes of data are stored in the S3 Standard tier
- Assess whether the data is actively accessed or retained for archival, compliance, or backup purposes
- Review historical trends to determine whether data access is infrequent, irregular, or absent

**Missing S3 Gateway Endpoint For Intra Region Ec2 Access**
Service: AWS S3 | Type: Inefficient Configuration

When EC2 instances within a VPC access Amazon S3 in the same region without a Gateway VPC Endpoint, traffic is routed through the public S3 endpoint and incurs standard internet egress charges - even though it remains within the AWS network. This results in unnecessary egress charges, as AWS treats this traffic as data transfer out to the internet, billed under the S3 service.

- Deploy a Gateway VPC Endpoint for S3 in VPCs that generate large intra-region S3 traffic
- Update route tables and access policies to route S3 traffic through the endpoint
- Validate that EC2-to-S3 traffic is using the private path and no longer incurring egress charges

**Missing S3 Lifecycle Policy For Incomplete Multipart Uploads**
Service: AWS S3 | Type: Inefficient Configuration

Multipart upload allows large files to be uploaded in segments. Each part is stored individually until the upload is finalised by a “CompleteMultipartUpload” request.

- Identify S3 buckets that are used for large file uploads or automation-driven data ingestion
- Review whether an S3 Lifecycle rule exists to abort incomplete multipart uploads
- Consult with application owners or platform teams to confirm upload workflows and fault tolerance

**Overprovisioned Ebs Volume**
Service: AWS EBS | Type: Inefficient Configuration

EBS volumes often remain significantly overprovisioned compared to the actual data stored on them. Because billing is based on the total provisioned capacity - not actual usage - this creates ongoing waste when large volumes are only partially used.

- If the volume is attached to a running EC2 instance and can tolerate replacement, create a smaller volume of the same type and migrate the data
- For volumes that cannot be replaced easily, plan to adjust provisioning defaults in AMIs, launch templates, or infrastructure-as-code going forward
- Document sizing assumptions and consider automated checks to catch overprovisioning at creation time

**Suboptimal Lifecycle Policy For Small Files On An S3 Bucket**
Service: AWS S3 | Type: Inefficient Configuration

This inefficiency occurs when small files are stored in S3 storage classes that impose a minimum object size charge, resulting in unnecessary costs. Small files under 128 KB stored in Glacier Instant Retrieval, Standard-IA, or One Zone-IA are billed as if they were 128 KB.

- Review if the bucket contains a high proportion of small objects (e.g., under 128 KB)
- Evaluate whether these small objects are stored in Glacier Instant Retrieval, Standard-IA, or One Zone-IA storage classes
- Assess the access patterns of the small files to determine if frequent retrieval justifies Standard storage

**Suboptimal Use Of Efs Storage Classes**
Service: AWS EFS | Type: Misaligned Storage Tiering

Many organisations default to storing all EFS data in the Standard class, regardless of how frequently data is accessed. This results in inefficient spend for workloads with significant portions of data that are rarely read.

- Transition infrequently accessed data to EFS IA or Archive storage classes to reduce cost
- Enable Intelligent Tiering for workloads where access frequency is variable or difficult to predict
- Maintain Standard storage only for data that requires frequent or high-performance access

**Excessive Kms Charges From Missing S3 Bucket Key Configuration**
Service: AWS S3 | Type: Misconfiguration

S3 buckets configured with SSE-KMS but without Bucket Keys generate a separate KMS request for each object operation. This behaviour results in disproportionately high KMS request costs for data-intensive workloads such as analytics, backups, or frequently accessed objects.

- https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingBucketKeys.html

**Missing Lifecycle Policy On Replicated Efs File System**
Service: AWS EFS | Type: Misconfiguration

When replicating an EFS file system across AWS regions (e.g., for disaster recovery), the destination file system does not automatically inherit the source's lifecycle policy. As a result, files replicated to the destination will remain in the Standard storage class unless a new lifecycle policy is explicitly configured.

- Manually apply a lifecycle policy to the destination EFS file system after replication is configured
- Align the policy with the source file system or tune it based on expected access frequency in the DR region
- Periodically audit replicated EFS environments to ensure lifecycle policies remain in place as environments evolve

**Delete On Termination Disabled For Ebs Volume**
Service: AWS EBS | Type: Misconfiguration Leading to Future Orphaned Resource

When EC2 instances are provisioned, each attached EBS volume has a `DeleteOnTermination` flag that determines whether it will be deleted when the instance is terminated. If this flag is set to `false` - often unintentionally in custom launch templates, AMIs, or older automation scripts - volumes persist after termination, resulting in orphaned storage.

- Update the instance configuration to set `DeleteOnTermination=true` for non-persistent volumes
- Modify infrastructure-as-code templates and launch configurations to use the correct flag by default
- Establish policy controls or monitoring to flag instances with unnecessary persistent volume retention

**Excessive Cloudtrail Charges From Bulk S3 Deletes**
Service: AWS S3 | Type: Misconfigured Logging

When large numbers of objects are deleted from S3 - such as during cleanup or lifecycle transitions - CloudTrail can log every individual delete operation if data event logging is enabled. This is especially costly when deleting millions of objects from buckets configured with CloudTrail data event logging at the object level.

- Temporarily disable S3 data event logging before initiating bulk deletes where logging is unnecessary
- Scope CloudTrail data event logging to only include relevant prefixes or buckets requiring detailed auditability

**Misaligned S3 Storage Tier Selection Based On Access Patterns**
Service: AWS S3 | Type: Misconfigured Storage Tier

While moving objects to colder storage classes like Glacier or Infrequent Access (IA) can reduce storage costs, premature transitions without analysing historical access patterns can lead to unintended expenses. Retrieval charges, restore time delays, and early delete penalties often go unaccounted for in simplistic tiering decisions.

- Use S3 Storage Lens or CUR data to analyse per-object or per-prefix access frequency before applying lifecycle transitions
- Apply intelligent-tiering selectively where access patterns are unpredictable
- Avoid bulk transitions to IA or Glacier for data with unclear or variable access characteristics

**Unexpired Non Current Object Versions In S3**
Service: AWS S3 | Type: Missing Lifecycle Policy

When S3 versioning is enabled but no lifecycle rules are defined for non-current objects, outdated versions accumulate indefinitely. These non-current versions are rarely accessed but continue to incur storage charges.

- Implement lifecycle policies to expire or transition non-current versions after an appropriate retention period
- Tailor policies by bucket or prefix to align with business, compliance, or recovery requirements
- Retain only the number of historical versions necessary for recovery or auditing; remove excess versions automatically

**Outdated And Expensive Ebs Volume Type**
Service: AWS EBS | Type: Modernization

This inefficiency occurs when legacy volume types such as gp2 or io1 remain in use, even though AWS has released newer types - like gp3 and io2 - that offer better performance at lower cost. Gp3 allows users to configure IOPS and throughput independently of volume size, while io2 provides higher durability and more predictable performance than io1.

- Identify volumes using gp2, io1, or other legacy types
- Compare current performance needs (IOPS, throughput) with the default capabilities of newer alternatives
- Evaluate whether the volume type was chosen intentionally or inherited from legacy infrastructure

**Outdated Provisioned Iops Volume Type For High I O Workloads**
Service: AWS EBS | Type: Outdated Resource Selection

Many environments continue using io1 volumes for high-performance workloads due to legacy provisioning or lack of awareness of io2 benefits. io2 volumes provide equivalent or better performance and durability with reduced cost at scale.

- Convert high-IOPS io1 volumes to io2 where supported
- Update provisioning templates to default to io2 for performance-critical workloads
- Validate application compatibility (typically no changes required)

**Underutilized Provisioned Iops On An Ebs Volume**
Service: AWS EBS | Type: Overprovisioned Resource

This inefficiency occurs when an EBS volume has provisioned IOPS levels that consistently exceed the actual I/O requirements of the workload it supports. This can happen when performance buffers are estimated too high, usage patterns change over time, or default settings are left unadjusted.

- Review actual IOPS usage over a representative time window (e.g., 14-30 days)
- Compare provisioned IOPS to peak and average demand to assess excess capacity
- Confirm whether performance requirements or bursty workloads justify the current configuration

**Excessive Retention Of Automated Rds Backups**
Service: AWS RDS | Type: Retention

If backup retention settings are too high or old automated backups are unnecessarily retained, costs can accumulate rapidly. RDS backup storage is significantly more expensive than equivalent storage in S3.

- Adjust backup retention periods to match business or compliance needs
- Delete outdated snapshots or unnecessary automated backups
- Export long-term backups to S3 using snapshot export features

**Missing Intelligent Tiering On Efs Lifecycle Policy**
Service: AWS EFS | Type: Suboptimal Lifecycle Configuration

EFS offers lifecycle policies that transition files from the Standard tier to Infrequent Access (IA) based on inactivity, significantly reducing storage costs for cold data. When this feature is not enabled, infrequently accessed files remain in the more expensive Standard tier indefinitely.

- Enable EFS lifecycle management with a transition period (e.g., 7, 14, 30 days) aligned to actual data access patterns
- Monitor and periodically review access logs or file activity metrics to refine lifecycle timing
- If access latency is not a concern, consider more aggressive transitions to IA for archival-type data

**Unarchived Long Term Ebs Snapshots**
Service: AWS EBS | Type: Suboptimal Storage Tier

EBS Snapshot Archive is a lower-cost storage tier for rarely accessed snapshots retained for compliance, regulatory, or long-term backup purposes. Archiving snapshots that do not require frequent or fast retrieval can reduce snapshot storage costs by up to 75%.

- Archive eligible snapshots using the `ModifySnapshotTier` API, AWS CLI, or console
- Confirm organisational retention policies before archiving
- Ensure teams understand how to restore archived snapshots and the longer retrieval times involved

**Lack Of Deduplication And Change Block Tracking In Aws Backup**
Service: AWS Backup | Type: Underutilization

AWS Backup does not natively support global deduplication or change block tracking across backups. As a result, even traditional incremental or differential backup strategies (e.g., daily incremental, weekly full) can accumulate redundant data.

- Where supported, use third-party backup tools with CBT and deduplication (e.g., Commvault, Veeam, Druva)
- Reevaluate backup frequency and retention periods based on RPO/RTO requirements
- Consolidate redundant backup plans across environments and services

**Inactive And Detached Ebs Volume**
Service: AWS EBS | Type: Unused Resource

EBS volumes frequently remain detached after EC2 instances are terminated, replaced, or reconfigured. Some may be intentionally retained for reattachment or backup purposes, but many persist unintentionally due to the lack of automated cleanup.

- Identify EBS volumes that are not attached to any EC2 instance (“available”)
- Review usage data to confirm that no read or write activity has occurred over a defined lookback period
- Check whether the volume is intentionally retained for manual recovery, reattachment, or snapshot purposes, especially if it's part of a known backup or disaster recovery process managed outside of AWS

**Inactive And Unmounted Efs File System**
Service: AWS EFS | Type: Unused Resource

EFS file systems that are no longer attached to any running services - such as EC2 instances or Lambda functions - continue to incur storage charges. This often occurs after workloads are decommissioned but the file system is left behind.

- Delete EFS file systems that are no longer in use and have no attached mount targets
- If data must be retained, consider exporting it to a lower-cost storage service (e.g., S3 Glacier) before deletion
- Establish periodic audits to identify and clean up orphaned file systems

**Inactive S3 Bucket**
Service: AWS S3 | Type: Unused Resource

S3 buckets often persist after projects complete or when the associated workloads have been retired. If a bucket is no longer being read from or written to - and its contents are not required for compliance, backup, or retention purposes - it represents ongoing cost without delivering value.

- Identify S3 buckets with no read or write activity during the defined lookback period
- Review object access patterns to confirm that stored data is not being queried or updated
- Check whether the bucket was associated with a decommissioned workload, environment, or application

**Unaccessed Ebs Snapshot**
Service: AWS EBS | Type: Unused Resource

This inefficiency arises when snapshots are retained long after they've served their purpose. Snapshots may have been created for backups, migrations, or disaster recovery plans but were never deleted - even after the related workload or volume was decommissioned.

- EBS Snapshot Pricing
- Working with Snapshots

**Unused Ebs Volume Attached To A Stopped Ec2 Instance**
Service: AWS EBS | Type: Unused Resource

This inefficiency occurs when an EC2 instance is stopped but still has one or more attached EBS volumes. Although the compute resource is not generating charges while stopped, the attached volumes continue to incur full storage and performance-related costs.

- Identify EC2 instances in a stopped state during the defined lookback period
- Check whether attached EBS volumes remain actively provisioned
- Validate whether the instance or its volumes are needed for recovery, migration, or scheduled activation

**Unused S3 Storage Lens Advanced**
Service: AWS S3 | Type: Unused Resource

S3 Storage Lens Advanced provides valuable insights into storage usage and trends, but it incurs a recurring cost. Organisations often enable it during an optimisation initiative but fail to turn it off afterwards.

- Disable S3 Storage Lens Advanced when not actively needed
- Use the free tier for basic visibility and re-enable Advanced only during optimisation cycles
- Set a periodic review of observability tools to ensure paid features still deliver value

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
