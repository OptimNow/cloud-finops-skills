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

## How playbooks differ from reference files

The reference files in `../references/` carry the linear, narrative
treatment of each provider (billing mechanics, commitment strategy, sizing
methodology, full pattern catalogues). They are written to be read end-to-end
by an analyst building a mental model of a domain.

Playbooks are the opposite: each one is scoped to **one named pattern**, and
exists so an LLM doing retrieval over knowledge chunks can answer a specific
question ("what is a zombie NAT gateway and how do I detect one?") without
loading the entire 2,600-line `finops-aws.md`.

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

The `cloud-finops/references/finops-waste-detection-playbooks.md` file is
the canonical taxonomy and confidence rubric; playbooks instantiate it.

## Status

This directory is seeded with a curated subset of high-frequency patterns.
Full extraction of the 48 AWS / 48 Azure / 26 GCP patterns from the
reference files is tracked in the Roadmap section of `CLAUDE.md`.
