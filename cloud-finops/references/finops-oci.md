# FinOps on OCI

> Oracle Cloud Infrastructure optimization patterns covering compute, storage, and networking. 6 inefficiency patterns for diagnosing waste and building optimization roadmaps.
> Source: PointFive Cloud Efficiency Hub.

---

## Compute Optimization Patterns (1)

**Underutilized Compute Instance**
Service: OCI Compute Instances | Type: Underutilized Compute Resource

OCI Compute instances incur cost based on provisioned CPU and memory, even when the instance is lightly loaded. Instances that show consistently low usage across time, such as those used only for occasional tasks, test environments, or forgotten workloads, may be overprovisioned relative to their actual needs.

- Rightsize the instance to a smaller shape that matches workload requirements
- Replace with burstable or flexible instance types where applicable
- Implement scheduled start/stop automation for predictable idle periods

---

## Storage Optimization Patterns (4)

**Inactive Object Storage Bucket**
Service: OCI Object Storage | Type: Inactive Storage Resource

OCI Object Storage buckets accrue charges based on data volume stored, even if no activity has occurred. Buckets that haven't been read from or written to in months may contain outdated data or artifacts from discontinued projects.

- Archive or delete data from inactive buckets after stakeholder confirmation
- Apply lifecycle rules to transition or expire infrequently accessed data
- Migrate cold data to OCI Archive Storage for reduced cost

**Unattached Boot Volume**
Service: OCI Block Volume | Type: Inactive and Detached Volume

When a Compute instance is terminated in OCI, the associated boot volume is not deleted by default. If the termination settings don’t explicitly delete the boot volume, it persists and continues to generate storage charges.

- Delete unattached boot volumes that are no longer needed
- Establish lifecycle policies or instance termination settings that automatically delete boot volumes unless explicitly retained
- Periodically audit the Block Volumes service for orphaned resources

**Missing Lifecycle Policy On Object Storage**
Service: OCI Object Storage | Type: Missing Cost Control Configuration

Without lifecycle policies, data in OCI Object Storage remains in the default storage tier indefinitely -even if it is rarely accessed. This can lead to growing costs from unneeded or rarely accessed data that could be expired or transitioned to lower-cost tiers like Archive Storage.

- Create lifecycle rules to transition older objects to Archive Storage
- Set expiration policies for data older than required retention thresholds
- Standardize lifecycle policies across log or backup buckets

**Unattached Block Volume Non Boot**
Service: OCI Block Volume | Type: Orphaned Storage Resource

Block volumes that are not attached to any instance continue to incur charges. These often accumulate after instance deletion or reconfiguration.

- Delete unattached boot volumes that are no longer needed
- Establish lifecycle policies or instance termination settings that automatically delete boot volumes unless explicitly retained
- Periodically audit the Block Volumes service for orphaned resources

---

## Networking Optimization Patterns (1)

**Overprovisioned Load Balancer**
Service: OCI Load Balancer | Type: Overprovisioned Networking Resource

Load balancers incur charges based on provisioned bandwidth shape, even if backend traffic is minimal. If traffic is low, or if only one backend server is configured, the load balancer may be oversized or unnecessary, especially in test or staging environments.

- Downgrade to a smaller bandwidth shape if supported
- Decommission underutilized load balancers
- Consolidate redundant load balancers across applications or environments

---

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io)  - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
