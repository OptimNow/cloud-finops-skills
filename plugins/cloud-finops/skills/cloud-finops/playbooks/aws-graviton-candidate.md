---
name: aws-graviton-candidate
scope: aws
service: Amazon EC2 / RDS / ElastiCache / OpenSearch / Lambda
waste_category: modernization
confidence: likely
---

# AWS Graviton Candidate

## Problem

Graviton (ARM64) instances price roughly 10-20% below the equivalent
x86 size within the same family generation, and AWS positions them at up
to 40% better price-performance on top - a mechanics claim that holds
for many workloads but must be benchmarked, not assumed. The pattern is
`likely`, not `obvious`, because the price signal alone does not decide:
the workload must actually run on ARM64. The decisive split is
**managed vs self-managed**. On RDS, Aurora, ElastiCache, OpenSearch and
Lambda, AWS owns the OS and runtime, so switching is an instance-class
or architecture flag change with no application port. On self-managed
EC2, the team owns AMIs, container images, and every binary agent - the
saving is the same but the migration is a project.

## Symptoms

- Sustained spend on x86 families (m5/m6i/m7i, c5/c6i/c7i, r5/r6i/r7i,
  t3) for workloads that are Linux plus interpreted or JIT runtimes
  (Java, Python, Node, Go, .NET Core)
- Managed databases and caches still on x86 instance classes
  (`db.m6i`, `cache.m6i`) where the Graviton class (`db.m7g`,
  `cache.m7g`) is available in-region
- Lambda functions defaulted to `x86_64` architecture
- Container fleets already building multi-arch images but pinned to
  x86 node groups

## Detection

Two signals: material x86 spend (query below), then a compatibility
read per workload (managed service, or Linux with no x86-only binary
dependency).

```sql
-- Athena over CUR 2.0: spend on current-generation x86 families, by
-- service - the managed-service rows are the low-friction candidates
SELECT
  product_servicecode,
  product_instance_type,
  SUM(line_item_unblended_cost) AS monthly_cost
FROM cur2
WHERE line_item_usage_start_date >= date_trunc('month', current_date - interval '1' month)
  AND line_item_usage_start_date <  date_trunc('month', current_date)
  AND regexp_like(product_instance_type, '^(db\.|cache\.)?(m|c|r|t)[5-7](i|a|d|ad|id)?\.')
  AND NOT regexp_like(product_instance_type, 'g[d]?\.')   -- exclude already-Graviton (m7g, c7gd, ...)
GROUP BY 1, 2
ORDER BY monthly_cost DESC;
```

The regex is a coarse first pass over family naming, not an oracle -
review the output rather than piping it into automation. For the
compatibility signal on EC2 workloads, the checklist is: Linux (Graviton
runs no Windows), no closed-source x86-only binaries, and every agent in
the image (APM, security, backup) available for ARM64 - vendor agent
support is the most common blocker in practice.

## Fix

Ordered by effort, cheapest first:

1. **Lambda**: switch eligible functions to `arm64` (pure-Python/Node
   functions with no compiled x86 dependencies switch cleanly; anything
   with native wheels needs a rebuild against ARM). Lambda ARM also
   bills a lower per-GB-second rate.
2. **Managed services**: modify RDS / ElastiCache / OpenSearch instance
   classes to the `g` variant in a maintenance window. Test in
   pre-production first, but the engine is AWS's problem, not yours.
3. **Containerised EC2/EKS**: add ARM node groups, build multi-arch
   images, shift stateless workloads first, and let the scheduler prove
   compatibility service by service.
4. **Bare EC2**: rebuild AMIs on ARM64, benchmark the actual workload
   (price-performance claims are workload-dependent), then migrate.
5. Check commitment coverage **before** each wave: instance-family RIs
   (m6i) do not cover the Graviton family (m7g); Compute Savings Plans
   cover both. Migrating a fleet out from under standard RIs strands
   the commitment - see the liquidity reasoning in
   `references/finops-aws-commitments.md`.

## Anti-pattern

- Fleet-wide migration mandates before a single agent-compatibility
  pass. One x86-only security agent discovered mid-wave stalls the
  whole programme and discredits the saving.
- Benchmarking on a micro-instance and extrapolating. Graviton's
  price-performance is workload-shaped; measure the real service under
  real load in pre-production.
- Migrating workloads pinned by standard instance-family RIs and
  leaving the RIs to burn unused. Sequence commitments and migration
  together, or use the exchange window on Convertibles.
- Treating Windows workloads as candidates. Graviton is Linux-only;
  the Windows saving conversation is licence-shaped (see
  `references/finops-itam.md`), not architecture-shaped.

## See also

- `playbooks/aws-gp2-to-gp3.md` - the storage-side modernization twin,
  where the conversion carries none of this pattern's compatibility
  caveats
- `playbooks/aws-outdated-gpu-generation.md` - the GPU-side generation
  refresh, same category
- `references/finops-aws-commitments.md` - RI/SP liquidity mechanics
  that gate migration sequencing
- `references/finops-waste-detection-playbooks.md` - "modernization"
  category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
