---
name: finops-oci
fcp_domain: "Understand Usage & Cost"
fcp_capability: "Data Ingestion"
fcp_capabilities_secondary: ["Anomaly Management", "Usage Optimization"]
fcp_phases: ["Inform", "Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Finance"]
fcp_maturity_entry: "Crawl"
---

# FinOps on OCI

> Oracle Cloud Infrastructure FinOps guidance covering cost data foundations
> (Cost Reports, FOCUS, cost-tracking tags, Budgets, Universal Credits) and 6
> inefficiency patterns for diagnosing waste and building optimisation roadmaps.

---

## OCI cost data foundations

OCI's billing and cost-management primitives differ from AWS / Azure / GCP in
naming and structure but cover the same conceptual ground. The five primitives
below are the FinOps practitioner's starting kit on any OCI engagement.

### Cost Reports (legacy CSV exports)

OCI's billing data export. Cost Reports are CSVs delivered daily to a tenancy-
owned Object Storage bucket, with one row per usage record. The schema covers
service, SKU, compartment, tags, region, usage quantity, list rate, discounted
rate, and effective cost.

**Practical setup:**
- Cost Reports are auto-generated daily once enabled at the tenancy root.
- Files land in a dedicated Oracle-managed Object Storage bucket; access requires
  a policy granting your tenancy read on `bling-bucket` (the canonical name).
- Retention: typically 365 days of historical reports retained, but verify per
  tenancy as Oracle has changed retention policy historically.
- Daily granularity (no hourly), which is similar to Azure Cost Management
  exports - the same daily-vs-hourly capacity-sizing nuance applies for OCI as
  documented for Azure.

Source: https://docs.oracle.com/iaas/Content/Billing/Concepts/costusagereportsoverview.htm

### FOCUS Reports - the cross-cloud-conformant export

OCI publishes a **FOCUS-conformant cost export** alongside the legacy Cost Reports.
As of March 2026, OCI supports FOCUS v1.0, while AWS and Azure have progressed to
v1.2, with additional providers like Databricks, Vercel, and Grafana Cloud joining
the FOCUS ecosystem. This is the path for multi-cloud customers who want OCI cost
data in a standardised schema for cross-cloud normalisation. Coexistence pattern:
enable both - FOCUS for multi-cloud normalisation into a unified warehouse, legacy
Cost Reports for OCI-native columns the FOCUS schema doesn't surface.

### Cost-tracking tags - first-class billing-attribution primitive

OCI distinguishes three tag types, and only one of them flows into cost reports:

| Tag type | Scope | Surfaces in Cost Reports? |
|---|---|---|
| **Freeform tags** | User-applied key/value | Limited - not native cost-allocation primitive |
| **Defined tags** | Schema-enforced via tag namespaces | Yes, but verbose in cost data |
| **Cost-tracking tags** | Subset of defined tags explicitly marked for billing | **Yes - the canonical cost-allocation tag** |

**Practical implication:** mark the tags you want to allocate cost by - typically
`cost_centre`, `team`, `application`, `environment` - as cost-tracking tags
(maximum 10 per tenancy as of 2026, verify current limit). They then propagate
to Cost Reports and become the primary cost-allocation grouping dimension. Tags
not marked as cost-tracking still apply to resources but require manual joins to
attribute spend.

Day-1 audit on any OCI engagement: list cost-tracking tags via the Tagging
console, verify against the customer's intended allocation dimensions, and add
missing ones before the next billing cycle (the cap forces deliberate choice).

### OCI Budgets

OCI Budgets provide spend caps with email and event-grid alerts at the
**compartment** or **cost-tracking tag** scope. Budgets are alert-only by default
- they do not enforce hard stops the way Azure Budgets or Snowflake Budgets can.

**Practical setup:**
- One budget per top-level cost-allocation boundary (compartment for org-by-
  project tenancies; cost-tracking tag for org-by-team tenancies).
- Alert thresholds at 50%, 80%, 100% of forecast.
- Route alerts to both FinOps and engineering team leads (FinOps-only alerts
  create a bottleneck).

Source: https://docs.oracle.com/iaas/Content/Billing/Concepts/budgetsoverview.htm

### Universal Credits - Oracle's commercial commitment construct

Universal Credits are Oracle's multi-year spend commitment, analogous to AWS EDP
and Azure MACC. The customer commits to a defined dollar amount over 1-3 years;
eligible OCI consumption draws down against that commitment.

**FinOps responsibility under Universal Credits:**
- **Burndown alignment** - track actual spend vs commitment trajectory monthly.
  An optimisation programme that succeeds in reducing OCI spend can leave the
  customer with an unspent Universal Credit balance at term end (the same
  optimisation paradox documented for Azure MACC).
- **Coverage** - most native OCI services count toward Universal Credit burndown,
  but third-party Marketplace listings and certain Oracle SaaS products may not.
  Verify product eligibility at procurement, not at burn-time.
- **Annual commitment vs three-year commitment** - longer term gives deeper
  discount but compounds the optimisation-vs-burndown tension. Evaluate
  consumption stability before committing for three years.

The Universal Credits / FinOps interaction mirrors the MACC framing in
`finops-azure.md` - read that section for the full optimisation-paradox and
operational-cadence guidance, then apply OCI-specific coverage rules.

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

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
