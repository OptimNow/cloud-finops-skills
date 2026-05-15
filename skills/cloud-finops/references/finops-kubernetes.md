---
name: finops-kubernetes
fcp_domain: "Understand Usage & Cost"
fcp_capability: "Allocation"
fcp_capabilities_secondary: ["Usage Optimization", "Architecting & Workload Placement"]
fcp_phases: ["Inform", "Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Engineering"]
fcp_personas_collaborating: ["Platform Engineering", "SRE", "Finance"]
fcp_maturity_entry: "Walk"
---

# FinOps on Kubernetes

> Kubernetes is the hardest variant of cloud-cost allocation. The cloud bill
> shows node-hours, but teams ship workloads as pods across shared namespaces.
> Without allocation, chargeback is impossible. Without rightsizing, allocation
> is misleading. Without thoughtful autoscaling, both are working against
> uncoordinated infrastructure.
>
> This file is the cross-cluster discipline (EKS, GKE, AKS). Provider-specific
> node mechanics live in the per-cloud files: AKS in
> `finops-azure.md` (Node Auto Provisioning, Azure Linux 2 retirement, MIG /
> MPS / DRA for GPU partitioning), EKS in `finops-aws.md` (commitment options
> for node groups including Karpenter integration), GKE in `finops-gcp.md`
> (Spot VMs, Autopilot vs Standard).

---

## Why K8s allocation is hard

The cloud provider invoices for node-hours. The team consumes pods. Bridging
the two requires mapping per-pod resource consumption back to the node-hour
cost the bill records. Three structural complications make this hard:

1. **Pods do not appear in the bill.** The billing data has no `pod_name` or
   `namespace` column. Allocation must be built from cluster-side telemetry
   (Prometheus, Kubecost, OpenCost) and joined against the node bill.
2. **Idle node capacity is real.** The cluster runs at some utilisation
   (typically 40-70%); the gap between requested capacity and used capacity
   is paid for but not consumed by any pod. This idle cost has to land
   somewhere - either as overhead on each pod's allocation, or as a
   separate "platform overhead" line item.
3. **Shared cluster resources have no obvious owner.** Ingress controllers,
   service meshes, observability daemonsets, the control plane itself - all
   serve every team. Their cost has to be allocated by a chosen methodology,
   not by a tag on the resource.

K8s cost allocation is a discipline that has to be built. There is no
provider button to turn on.

---

## Tooling

Three tooling categories serve K8s cost allocation. They are not mutually
exclusive; many organisations use a layered combination.

### OpenCost (CNCF)

The CNCF reference implementation. Open-source, self-hosted, vendor-neutral.
Provides per-namespace, per-pod, per-controller allocation by joining
Prometheus metrics with cloud billing data. The `OpenCost` model is also
the FOCUS-aligned reference for K8s cost allocation - emits cost rows in
FOCUS-conformant shape that are joinable to the rest of the FOCUS dataset.

**When to pick OpenCost:**
- Multi-cloud K8s estate where you want consistent allocation methodology
  across EKS, GKE, AKS, and on-premises K8s
- Mature data engineering team that can self-host and integrate with the
  existing FOCUS warehouse
- Strong preference for vendor-neutral, open-source primitives

**Trade-off:** OpenCost is a primitive. The dashboards and chargeback
workflows on top are your job.

### Kubecost

Commercial layer on top of OpenCost. Adds dashboards, chargeback workflows,
budget alerts, anomaly detection, multi-cluster aggregation, savings
recommendations, and SaaS-hosted options. Free tier covers single-cluster
basics; paid tiers add multi-cluster and enterprise features.

**When to pick Kubecost:**
- Single-cluster or small multi-cluster setup that wants out-of-the-box
  dashboards rather than build-your-own
- Engineering teams that want self-service per-namespace cost views
  without a data-engineering investment
- Evaluating whether K8s allocation is worth investing in - the free tier
  is the cheapest way to find out

**Trade-off:** vendor lock-in to a vendor's data model and SaaS roadmap.
Migration to OpenCost-only later requires re-platforming the dashboards.

### Cloud-native K8s cost allocation

GKE, EKS, and AKS all expose some level of native cost allocation:

- **GKE Cost Allocation** - native per-namespace, per-label cost in Cloud
  Billing. Lowest-friction option for GKE-only estates.
- **EKS Split Cost Allocation** - native per-pod allocation in CUR / Data
  Exports for FOCUS. Available for EKS clusters with the AWS-managed
  metrics; per-pod attribution flows directly into CUR.
- **AKS Cost Analysis** - per-namespace cost in Azure Cost Management.
  Less granular than GKE or EKS native; OpenCost or Kubecost typically add
  meaningful value on top.

**When to pick cloud-native:**
- Single-cloud K8s estate where the native option is mature (GKE Cost
  Allocation is the strongest)
- No appetite for self-hosting OpenCost or paying for Kubecost
- Allocation needs are at the namespace level, not the pod or workload level

**Trade-off:** allocation methodology is the cloud's, not yours. Cross-cloud
consistency is impossible. Joining to the rest of the FOCUS dataset is
provider-specific.

### Recommended starting choice

For most organisations: start with the native cost allocation in the cloud
the cluster runs in (GKE Cost Allocation, EKS Split Cost Allocation, AKS
Cost Analysis). If allocation needs grow past the native limits, add
OpenCost (vendor-neutral) or Kubecost (commercial). Avoid running both
OpenCost / Kubecost AND extensive native allocation simultaneously - it
duplicates the work and confuses the source of truth.

---

## FOCUS-emitting allocation

K8s allocation is most useful when the per-workload cost rows can be joined
to the rest of the cost dataset (non-K8s services, managed services,
networking). FOCUS-conformant emission makes this clean.

### How it works

OpenCost (and Kubecost via the underlying OpenCost engine) can emit cost
rows in FOCUS shape. The mapping pattern:

| FOCUS column | K8s source |
|---|---|
| `BilledCost` | Cloud node-hour cost amortised across pods that ran on the node |
| `EffectiveCost` | Same as BilledCost for K8s; cluster-side allocation does not amortise prepaid commitments separately |
| `ServiceName` | Provider's managed-K8s service (`Amazon EKS`, `Azure Kubernetes Service`, `Google Kubernetes Engine`) |
| `ServiceCategory` | `Compute` |
| `SubAccountId` | Cluster's project / subscription / account |
| `ResourceId` | Cluster + workload identifier (e.g. `cluster-name/namespace/workload`) |
| `ResourceType` | `Pod` / `Deployment` / `StatefulSet` |
| `Tags` (FOCUS JSON) | K8s labels mapped to FOCUS Tags namespace |

### K8s labels to FOCUS Tags mapping

Map K8s labels into the FOCUS `Tags` JSON column with a clear namespace
prefix to distinguish them from cloud-native tags:

```yaml
# OpenCost / Kubecost label mapping example
tags:
  k8s_namespace: "{namespace}"
  k8s_workload: "{deployment_or_statefulset_name}"
  k8s_team: "{label.team}"
  k8s_environment: "{label.env}"
  k8s_cost_center: "{label.cost-center}"
```

The downstream FOCUS warehouse then joins K8s pod costs to non-K8s costs by
the same `team` / `cost-center` dimensions. This is what makes per-team
allocation work across "the team's database in RDS" + "the team's pods in
EKS" + "the team's S3 buckets" in a single view.

### Label hygiene is the prerequisite

K8s allocation is only as good as the labels on the workloads. Recommended
mandatory labels (mirrors the cloud-tag policy in `finops-tagging.md`):

- `team` - owning team
- `env` - prod / staging / dev / sandbox
- `cost-center` - finance allocation key
- `app` - workload identifier
- `tier` - critical / standard / batch / experimental (drives PDB and Spot
  decisions)

Enforce label policy via OPA / Gatekeeper or Kyverno. Workloads without
mandatory labels do not deploy. The same enforcement discipline that applies
to cloud-resource tags applies here.

---

## Container rightsizing

Rightsizing pods is the largest single FinOps lever inside the cluster.
Reducing CPU and memory requests to match observed usage typically reclaims
30-50% of cluster spend without degrading service-level objectives, IF done
carefully.

### Methodology

1. **Collect 14+ days of CPU and memory usage** per container, per workload.
   Two weeks captures most week-over-week patterns.
2. **Compute the right percentile per resource:**
   - **Memory: p99 + 30% safety margin.** OOMKills are catastrophic; over-
     provisioning is cheaper than the pager
   - **CPU: p95 + 50% safety margin.** CPU throttling is bad but recoverable;
     OOM is not
3. **Compare to current requests.** Workloads where the request is more
   than 2x the percentile are candidates for downsize.
4. **Stage the rollout** per workload (canary like any deploy: dev →
   staging → prod canary → prod). Do not change cluster-wide in one pass;
   the blast radius of a bad rightsizing is the entire workload's pods
   restarting.
5. **Monitor for one week post-change** before declaring savings: track
   OOMKills, throttling events, latency SLO attainment. Roll back any
   workload that regresses.

### Tooling

- **VPA (Vertical Pod Autoscaler)** in recommendation-only mode is the
  default tool for generating rightsizing suggestions. Do not enable
  auto-update mode in production - the auto-update behaviour can cause
  pod restarts at inopportune moments
- **Kubecost / OpenCost** rightsizing recommendations are based on the
  same VPA logic with extra context (cost impact per recommendation)
- **StormForge / CAST AI / PerfectScale** are commercial alternatives
  that include load-based recommendations and integration with HPA. Worth
  evaluating at scale (>100 workloads); overkill for smaller clusters

### Landmines

- **Memory requests below true usage** cause OOMKills and pager storms.
  Always err on the side of memory headroom.
- **CPU limits below burstable demand** cause silent throttling that slows
  APIs without a clear failure signal. Many engineering teams set CPU
  requests but NOT CPU limits to avoid this; evaluate per workload (limits
  prevent runaway processes; they also prevent legitimate bursts).
- **VPA recommendations are statistical, not guarantees.** A workload that
  ran at 200m CPU for 14 days may need 2 cores during the next product
  launch. Treat VPA as a starting point, not the final answer.
- **Rightsizing without autoscaling is wasted work.** Reducing pod requests
  on a fixed node pool just creates more headroom on the same nodes; the
  bill does not change. Pair rightsizing with autoscaling tuning (next
  section).

---

## Node-level autoscaling

Container rightsizing reduces what pods request. Autoscaling reduces what
the cluster provisions. Both are needed.

### Karpenter vs Cluster Autoscaler

For most modern AWS EKS clusters, Karpenter outperforms Cluster Autoscaler
on cost efficiency because Karpenter provisions the right shape node, not
just "a node from the configured node pool." The same pattern applies to
GKE (Karpenter is now available on GKE) and to AKS (Node Auto Provisioning
is the AKS-native equivalent; see `finops-azure.md`).

**The measurement that matters:** node efficiency, defined as
`SUM(requested CPU) / SUM(provisioned CPU)`. Same for memory. A cluster
running at 40% node efficiency is paying for 60% headroom; one running at
75% is well-tuned. Higher than 85% is risky - no headroom for bursts or
node failures.

### Karpenter consolidation tuning

Karpenter's `consolidationPolicy: WhenUnderutilized` is powerful but chatty.
Aggressive `consolidateAfter` settings cause pod churn that affects SLOs.

Recommended starting points:

- `consolidateAfter: 30s` for dev / staging clusters
- `consolidateAfter: 5m` for prod clusters
- `disruptionBudget` configured to limit simultaneous node drains
- `expireAfter: 720h` (30 days) to force a rolling refresh of nodes for
  patching cadence

Tune up or down based on the observed pod-disruption rate vs the savings
delivered.

### Pod Disruption Budgets are non-negotiable

Every workload with an SLO must have a PDB. No exceptions. PDBs are how the
cluster autoscaler (Karpenter or CA) knows it cannot drain a node without
violating the workload's availability commitment.

PDB anti-pattern: setting `minAvailable: 100%` because "we cannot tolerate
any disruption." This blocks all consolidation. The right answer is
`minAvailable: N-1` where N is the replica count, with a corresponding
`maxUnavailable` budget on the Deployment.

### Spot / preemptible diversification

A single-instance-type Spot setup is asking for simultaneous termination of
the entire workload. Diversify:

- **Multiple instance types** within the same family and across families
  (e.g. m6i, m6a, m7i for general-purpose workloads). Karpenter's
  `nodepool` spec accepts a list; use it.
- **Multiple availability zones.** Spot interruptions correlate within a
  zone; spreading reduces the blast radius.
- **Mixed Spot + On-Demand** with priority. Karpenter and Cluster Autoscaler
  both support this; the on-demand fraction acts as the safety net.

For workloads that cannot tolerate any interruption, Spot is not the right
answer. Stay On-Demand or use commitment discounts on the on-demand portion.

### Idle node cost

Even with rightsizing and autoscaling, the cluster will have some idle
node-hours - capacity provisioned for safety margin, headroom for bursts,
or pods waiting to schedule. Show this gap explicitly:

- **Allocated cost** - sum of pod-hour costs across all running pods (per
  the allocation methodology)
- **Provisioned cost** - sum of node-hour costs the cluster paid for
- **Idle cost = Provisioned - Allocated** - the cost not attributable to
  any pod

Idle cost is often 20-40% of total cluster cost and is a useful KPI on its
own. It belongs to the Platform team's budget, not the application teams'.

---

## Crawl / Walk / Run progression

### Crawl - allocation

- Cluster-native allocation enabled (GKE Cost Allocation, EKS Split Cost
  Allocation, or AKS Cost Analysis)
- Mandatory labels defined (`team`, `env`, `cost-center`, `app`, `tier`)
- Manual per-namespace cost reports distributed monthly via dashboard or
  email
- Pod requests are best-guess at workload start; rightsizing is reactive

### Walk - allocation

- OpenCost or Kubecost installed; per-pod cost rows emitted in FOCUS shape
- Label policy enforced via OPA / Gatekeeper or Kyverno; workloads without
  mandatory labels do not deploy
- Per-team and per-environment cost views routed into team-existing tools
  (Slack channels, Grafana dashboards) - see `finops-allocation-showback.md`
  for the routing pattern
- Idle cost shown separately as Platform team's overhead, not redistributed
  across application teams
- Quarterly methodology review: are the allocation keys producing
  defensible numbers?

### Run - allocation

- K8s cost rows joinable to non-K8s FOCUS dataset for unified per-team /
  per-product cost views
- Allocation feeds chargeback (see `finops-chargeback.md`) where the
  organisation has progressed there
- Multi-cluster aggregation across EKS / GKE / AKS with consistent
  methodology
- Annual allocation methodology review with stakeholder sign-off

### Crawl - rightsizing and autoscaling

- VPA in recommendation-only mode for the top 10 cluster workloads by spend
- Cluster Autoscaler configured (or Karpenter / NAP for AWS / Azure
  clusters); default consolidation settings
- PDBs configured for top-priority workloads only

### Walk - rightsizing and autoscaling

- VPA recommendations applied per workload with documented safety margins
  (1.3x memory, 1.5x CPU above the percentile)
- Karpenter (AWS / GKE) or NAP (AKS) tuned with consolidation policy
  appropriate to the cluster's tier (prod conservative, dev aggressive)
- PDBs configured for every workload with an SLO
- Spot diversified across instance types and AZs
- Node efficiency tracked as a KPI

### Run - rightsizing and autoscaling

- Continuous rightsizing in CI / CD: VPA recommendations integrated into
  the workload's deployment manifests with periodic refresh
- Consolidation policy tuned per cluster profile based on observed
  pod-disruption rate
- Pending-pod-latency SLO tracked: scale-up delay > 90s triggers an alert
- Spot mixed-instance policy with on-demand safety net; Spot interruption
  rate tracked

---

## Anti-patterns

- **K8s cost allocation by tag-only.** Tags miss what teams actually
  consume. Build from operational metrics (CPU-hours, memory-bytes,
  request counts) for the per-pod allocation, then attribute to teams via
  labels.
- **Auto-update VPA in production.** Pod restarts at inopportune moments.
  Use recommendation-only mode and apply changes through the normal deploy
  pipeline.
- **CPU limits everywhere by default.** Causes silent throttling on bursty
  workloads. Evaluate per workload; many production workloads run better
  with CPU requests but no CPU limits (memory limits stay).
- **Single-instance-type Spot.** Asking for simultaneous termination.
  Always diversify.
- **Aggressive Karpenter consolidation in prod.** Pod churn affects SLOs.
  Start conservative and tune based on measurement.
- **Allocating idle node cost to application teams.** The teams cannot
  control idle; the Platform team can. Carry idle as Platform overhead.
- **Running OpenCost AND Kubecost AND extensive native allocation.**
  Duplicates work and confuses the source of truth. Pick one primary, with
  fallbacks.
- **Treating K8s allocation as separate from cloud-cost allocation.** They
  are the same problem. Emit FOCUS-shaped rows from K8s and join them to
  the rest of the warehouse.
- **No PDBs.** Cluster Autoscaler and Karpenter cannot consolidate safely.
  Configure PDBs for every workload with an SLO.
- **Rightsizing without autoscaling.** The bill does not change because
  you reduce pod requests; the cluster still has the same nodes. Pair the
  two.

---

## Cross-references

- `finops-allocation-showback.md` - the upstream allocation methodology;
  K8s allocation is one source feeding the broader allocation pipeline
- `finops-tagging.md` - tag (label) hygiene is the prerequisite
- `finops-aws.md` - EKS-specific commitment options; Karpenter integration
  with EC2 Savings Plans and Compute Savings Plans
- `finops-azure.md` - AKS-specific deep cuts (Node Auto Provisioning,
  Azure Linux 2 retirement, MIG / MPS / DRA for GPU partitioning)
- `finops-gcp.md` - GKE-specific options (Spot VMs, Autopilot vs Standard,
  GKE Cost Allocation native)
- `finops-anomaly-management.md` - K8s cost spikes (autoscaler runaway,
  workload deployed without resource limits) feed the same anomaly
  pipeline
- `finops-chargeback.md` - K8s allocation is a precondition for K8s-
  aware chargeback
- `optimnow-methodology.md` - the maturity-aware framing this file builds on

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
