---
name: gcp-idle-gke-autopilot
scope: gcp
service: GCP GKE Autopilot
waste_category: idle
confidence: likely
---

# GCP Idle GKE Autopilot Cluster

## Problem

GKE Autopilot bills per-pod CPU / memory / ephemeral-storage requested,
plus a flat **management fee** (~$0.10/cluster/hour = ~$72/month per
cluster) regardless of workload activity. Even when no user workloads
run, Autopilot keeps system-managed pods alive (control-plane logging,
metrics agent, GMP collectors, networking). Dev / test / sandbox
clusters left running over weekends and abandoned-after-the-PoC
clusters accumulate this management fee silently.

## Symptoms

- Cluster has fewer than 5 user-namespace pods running
- Last `kubectl apply` or commit to the GitOps repo touching this
  cluster is older than 30 days
- The cluster lives in an environment-named project (`*-dev-*`,
  `*-sandbox-*`, `*-poc-*`) that has matured past its initial purpose
- Cost-per-cluster trend is flat at the management-fee floor (~$72/mo
  for Autopilot, more if there is any pod activity)

## Detection

```sql
-- BigQuery billing export: GKE Autopilot management fee + minimum compute
SELECT
  project.id                              AS project,
  resource.global_name                    AS cluster,
  SUM(cost) / NULLIF(SUM(usage.amount), 0) AS unit_cost,
  SUM(cost)                               AS cost_30d
FROM `<project>.<dataset>.gcp_billing_export_resource_v1_<account>`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND service.description = 'Kubernetes Engine'
  AND sku.description LIKE '%Autopilot%'
GROUP BY 1, 2
ORDER BY cost_30d DESC;
```

```bash
# For each suspect cluster, count user-namespace pods
gcloud container clusters get-credentials <cluster> --region <region> --project <project>
kubectl get pods --all-namespaces \
  -o json | jq '[.items[] | select(.metadata.namespace | startswith("kube-") | not) | select(.metadata.namespace != "gmp-system")] | length'
```

## Fix

1. **For dev / sandbox clusters**: delete the cluster. Re-create on demand
   from Terraform / GitOps when needed - GKE Autopilot cluster creation
   is fast (5-10 min).
2. **For low-traffic shared clusters**: consolidate workloads onto one
   shared cluster across teams via namespace isolation. Saves the per-
   cluster management fee, trades against blast-radius concerns.
3. **For automatically-provisioned PoC clusters**: build a GitHub /
   GitLab Action that auto-deletes clusters after 14 days of no activity.
   Tag the cluster with `expires-on=YYYY-MM-DD` at creation; the action
   reaps anything past that.
4. **Replace with serverless alternatives** where the workload fits:
   Cloud Run for stateless HTTP, Cloud Functions for event-driven, GKE
   Standard with Spot VMs for batch.

## Anti-pattern

- Deleting a GKE cluster without dumping persistent volumes first.
  Autopilot clusters with attached PDs that have `reclaimPolicy: Retain`
  leave the PDs behind (a different orphan pattern - see
  `playbooks/gcp-orphan-persistent-disks.md`), but data inside the PV
  may still be needed and the cluster delete loses Helm release
  history.
- Aggressive consolidation onto one shared cluster across security
  boundaries. Multi-tenant Autopilot is feasible but namespace-level
  RBAC + NetworkPolicies must be in place; mixing prod and untrusted
  PoC namespaces in one cluster creates lateral-movement risk.

## See also

- `references/finops-gcp.md` - GCP cost data foundations, Autopilot
  management fee pricing
- `references/finops-kubernetes.md` - GKE cost attribution, cluster
  consolidation patterns
- `playbooks/gcp-orphan-persistent-disks.md` - related orphan pattern

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
