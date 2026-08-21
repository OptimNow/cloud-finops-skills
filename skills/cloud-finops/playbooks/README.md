# Cloud FinOps Playbooks

Named-pattern runbooks for the highest-frequency waste and cost-anomaly
patterns across AWS, Azure, GCP, and cross-cloud concerns. Each playbook is
a small (~2-6 KB), self-contained chunk optimised for **retrieval-augmented
generation** (RAG) - so ChatGPT, Gemini, or any LLM that fetches knowledge
chunks pulls exactly the relevant pattern instead of loading the full
provider reference file. AI/ML playbooks (SageMaker, GPU) sit at the upper
end of the band because the detection queries and remediation steps need
more space; cloud-native patterns (NAT gateways, orphaned disks) stay
closer to ~2-3 KB.

## Catalogue

`SKILL.md` and `POWER.md` carry representative examples only and defer here for
the full list. Over the MCP server, `list_playbooks()` and
`find_playbooks(scope=, service=, waste_category=, confidence=)` return the same
set with its facets.

### AWS

| Playbook | Pattern | Waste category | Confidence |
|---|---|---|---|
| [aws-cross-az-egress](aws-cross-az-egress.md) | Cross-AZ Egress Chatterbox | egress | likely |
| [aws-expiring-commitment-no-decision](aws-expiring-commitment-no-decision.md) | Expiring Commitment Without a Renewal Decision | commitment-mismatch | obvious |
| [aws-gpu-for-cpu-bound-workload](aws-gpu-for-cpu-bound-workload.md) | GPU Instance for a CPU-Bound Workload | overprovisioned | likely |
| [aws-gpu-instance-oversized](aws-gpu-instance-oversized.md) | Oversized GPU Instance | overprovisioned | likely |
| [aws-idle-load-balancer](aws-idle-load-balancer.md) | Idle Load Balancer | idle | obvious |
| [aws-mig-candidate](aws-mig-candidate.md) | MIG (Multi-Instance GPU) Candidate | overprovisioned | possible |
| [aws-multi-gpu-underutilized](aws-multi-gpu-underutilized.md) | Multi-GPU Instance with Single-GPU Workload | overprovisioned | obvious |
| [aws-orphaned-ebs-volumes](aws-orphaned-ebs-volumes.md) | Orphaned EBS Volumes | orphaned | obvious |
| [aws-outdated-gpu-generation](aws-outdated-gpu-generation.md) | Outdated GPU Generation | modernization | possible |
| [aws-oversized-rds](aws-oversized-rds.md) | Oversized RDS Instance | overprovisioned | likely |
| [aws-sagemaker-idle-endpoint](aws-sagemaker-idle-endpoint.md) | SageMaker Idle Endpoint | idle | obvious |
| [aws-sagemaker-mme-consolidation](aws-sagemaker-mme-consolidation.md) | SageMaker Endpoint Sprawl (MME / inference components) | overprovisioned | likely |
| [aws-s3-cold-data-in-standard](aws-s3-cold-data-in-standard.md) | S3 Cold Data Sitting in Standard | overprovisioned | possible |
| [aws-s3-incomplete-multipart-uploads](aws-s3-incomplete-multipart-uploads.md) | S3 Incomplete Multipart Uploads Never Aborted | orphaned | obvious |
| [aws-s3-noncurrent-version-sprawl](aws-s3-noncurrent-version-sprawl.md) | S3 Noncurrent Version Sprawl | orphaned | likely |
| [aws-sagemaker-notebook-always-on](aws-sagemaker-notebook-always-on.md) | SageMaker Always-On Notebook Instance | idle | obvious |
| [aws-snapshot-sprawl](aws-snapshot-sprawl.md) | Snapshot Sprawl | orphaned | likely |
| [aws-zombie-nat-gateway](aws-zombie-nat-gateway.md) | Zombie NAT Gateway | idle | obvious |

### Azure

| Playbook | Pattern | Waste category | Confidence |
|---|---|---|---|
| [azure-app-service-overprovisioned](azure-app-service-overprovisioned.md) | App Service Plan Overprovisioned | overprovisioned | likely |
| [azure-idle-sql-database](azure-idle-sql-database.md) | Idle SQL Database | idle | likely |
| [azure-log-analytics-sprawl](azure-log-analytics-sprawl.md) | Log Analytics Ingestion Sprawl | overprovisioned | likely |
| [azure-orphan-disks](azure-orphan-disks.md) | Orphan Managed Disks | orphaned | obvious |
| [azure-unused-reservation](azure-unused-reservation.md) | Unused Azure Reservation | commitment-mismatch | obvious |

### GCP

| Playbook | Pattern | Waste category | Confidence |
|---|---|---|---|
| [gcp-cloud-functions-cold-starts](gcp-cloud-functions-cold-starts.md) | Cloud Functions Cold Starts | overprovisioned | possible |
| [gcp-cud-mismatch](gcp-cud-mismatch.md) | Resource-Based CUD Mismatch | commitment-mismatch | likely |
| [gcp-idle-gke-autopilot](gcp-idle-gke-autopilot.md) | Idle GKE Autopilot Cluster | idle | likely |
| [gcp-orphan-persistent-disks](gcp-orphan-persistent-disks.md) | Orphan Persistent Disks | orphaned | obvious |

### Cross-cloud

| Playbook | Pattern | Waste category | Confidence |
|---|---|---|---|
| [cross-cloud-agent-loop-burn](cross-cloud-agent-loop-burn.md) | Agent-Loop Flat-Line Burn | ai-ml-inefficiency | likely |
| [cross-cloud-coding-agent-token-waste](cross-cloud-coding-agent-token-waste.md) | Coding-Agent Token Waste | ai-ml-inefficiency | likely |
| [cross-cloud-schedule-blindness](cross-cloud-schedule-blindness.md) | Schedule Blindness (non-production 24/7) | schedule-blindness | obvious |
| [cross-cloud-untagged-spend-drift](cross-cloud-untagged-spend-drift.md) | Untagged Spend Drift | orphaned | likely |

The `commitment-mismatch` category is served by one playbook per provider
(`aws-expiring-commitment-no-decision`, `azure-unused-reservation`,
`gcp-cud-mismatch`); the deeper sizing and portfolio reasoning behind each
stays in the commitments reference files, which those playbooks link.

## How playbooks differ from reference files

The reference files in `../references/` carry the linear, narrative
treatment of each provider (billing mechanics, commitment strategy, sizing
methodology, full pattern catalogues). They are written to be read end-to-end
by an analyst building a mental model of a domain.

Playbooks are the opposite: each one is scoped to **one named pattern**, and
exists so an LLM doing retrieval over knowledge chunks can answer a specific
question ("what is a zombie NAT gateway and how do I detect one?") without
loading a full provider reference such as `finops-aws.md`.

The two layers cover the same patterns from different angles:
- **Reference file** = narrative context, cross-pattern reasoning, billing
  mechanics that explain *why* a pattern matters
- **Playbook** = symptoms, detection query, fix, anti-pattern, sources

## Format

Every playbook follows this structure:

```
---
name: <pattern slug>
scope: aws | azure | gcp | cross-cloud
service: <provider service or N/A>
waste_category: orphaned | idle | overprovisioned | commitment-mismatch | schedule-blindness | modernization | ai-ml-inefficiency | egress
confidence: obvious | likely | possible
---

# <Human-readable title>

## Problem
<2-4 sentences: what the pattern is, why it accrues cost>

## Symptoms
<bullet list of observable signals>

## Detection
<a query block (CUR / KQL / BigQuery SQL / CLI) that finds the pattern>

Detection blocks are the part of a playbook a reader copy-pastes, so a query
that cannot run is worse than no query at all - it returns empty and reads as
"no waste found". Before merging a new or edited Detection block:

- **Run it against a live account**, or state the prerequisite that stops you.
  A query needing the CloudWatch agent, a diagnostic setting, or a specific
  export is fine; leaving that unsaid is not.
- **Check the metric/table/column actually exists.** Namespaces
  (`AWS/NATGateway`, not `NATGateway/`), required dimensions (SageMaker
  `Invocations` needs `VariantName`), and table names (Azure Resource Graph
  has no billing table) are the recurring failure modes.
- **Distinguish "no results" from "no data".** Where an empty result could
  mean the telemetry is missing rather than the waste is absent, include the
  command that tells the two apart.
- **Do not present pseudo-code as runnable.** If a step is illustrative, label
  it.

## Fix
<bullet list of remediation steps, ordered safest-first>

## Anti-pattern
<what NOT to do, common mistakes when fixing>

## See also
<links to related references and playbooks>

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
```

The trailing `---` + OptimNow / CC BY-SA footer is required on every
playbook. Playbooks redistribute through the PyPI bundle (`cloud-finops-mcp`)
and the `install.sh --grouped` build, so per-file attribution is the right
license-hygiene default rather than relying on reference to the repo
`LICENSE.md` alone.

## Confidence tiers (matching `finops-waste-detection-playbooks.md`)

- **obvious** - single signal is enough to act (a NAT gateway with 0 GB
  traffic for 30 days is dead, full stop)
- **likely** - two signals required to avoid false positives (low CPU AND
  low network suggests an idle EC2 instance worth investigating)
- **possible** - needs human review (a Reserved Instance under-utilisation
  could be a real waste OR a temporary workload migration in progress)

## Routing

`SKILL.md` and `POWER.md` route named-pattern queries here:

| Query topic | Load |
|---|---|
| Named waste pattern (zombie NAT, snapshot sprawl, idle ELB, etc.) | `playbooks/<slug>.md` |
| Cross-pattern catalogue / billing mechanics behind a pattern | `references/finops-<provider>.md` |

## Drift management

Patterns appear in both the reference files and the playbooks. To prevent
drift, the recommended workflow is:

1. Edits to billing-mechanics narrative happen in the reference file
2. Edits to detection queries / fix steps / anti-patterns happen in the
   playbook
3. When a pattern's *core economics* change (e.g. AWS halves NAT Gateway
   pricing), update both - the reference file's pattern catalogue entry
   should ideally link to the matching playbook (e.g.
   `[aws-zombie-nat-gateway](../playbooks/aws-zombie-nat-gateway.md)`)
   rather than repeat all the detail
4. When a provider renames a metric, moves a namespace, or changes a required
   dimension, the Detection block is the thing that breaks silently. Treat
   provider console/API changes as a reason to re-run the affected queries,
   not just to reword the prose

The `../references/finops-waste-detection-playbooks.md` file is the canonical
taxonomy and confidence rubric; playbooks instantiate it.

## Status

This directory is seeded with a curated subset of high-frequency patterns.
The full per-provider catalogues live in `../references/finops-aws-patterns.md`,
`../references/finops-azure-patterns.md`, and `../references/finops-gcp.md`;
extracting more of them into playbooks is tracked in `docs/ROADMAP.md`.

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
