---
name: aws-outdated-gpu-generation
scope: aws
service: AWS EC2
waste_category: modernization
confidence: possible
---

# AWS Outdated GPU Generation

## Problem

GPU generations on AWS span roughly five years of NVIDIA architecture:
P3 (V100, 2017), G4dn (T4, 2019), G5 (A10G, 2021), G6 (L4, 2023), P4d
(A100 40 GB, 2020), P4de (A100 80 GB, 2022), P5 (H100, 2023), P5e/P5en
(H200, 2024). Each generation generally improves performance per dollar
for matched workloads - though the comparison is workload-specific and
hourly rates alone are misleading. A workload running on P3 (V100) or
G4dn (T4) is often cheaper per inference on G5, G6, or P4d, even though
the newer SKU's hourly rate looks higher. Modernisation is one of the few
optimisation moves where the right answer requires actual benchmarking,
not a CUR-only verdict.

## Symptoms

- Significant CUR usage hours (> 100 hours/month) on `*.p3.*` or
  `*.g4dn.*` instances
- Workload uses a recent framework version (PyTorch ≥ 1.13, TensorFlow ≥
  2.10) with CUDA ≥ 11.x compatibility
- Model is supported on newer NVIDIA generations (A10G, L4, A100, H100
  all support modern attention kernels, mixed-precision, BF16/FP8)
- No hardware-specific tie-in (e.g. licensed software pinned to a
  particular GPU generation)
- The instance was provisioned during an earlier project and never
  revisited despite the migration path being available for 2+ years

## Detection

```sql
-- Athena over CUR 2.0: hours on legacy GPU families, last month
SELECT
  line_item_usage_account_id      AS account_id,
  product_instance_type           AS instance_type,
  SUM(line_item_usage_amount)     AS hours,
  SUM(line_item_unblended_cost)   AS cost_month
FROM cur2
WHERE line_item_usage_start_date >= date_trunc('month', current_date - interval '1' month)
  AND line_item_usage_start_date <  date_trunc('month', current_date)
  AND product_servicecode = 'AmazonEC2'
  AND (product_instance_type LIKE 'p3.%'
       OR product_instance_type LIKE 'g4dn.%'
       OR product_instance_type LIKE 'g3%.%'
       OR product_instance_type LIKE 'p2.%')
GROUP BY 1, 2
HAVING SUM(line_item_usage_amount) > 100
ORDER BY cost_month DESC;
```

For each candidate, check whether the workload also appears on newer SKUs
elsewhere in the org (a sign that migration is operationally feasible).
Use `aws ec2 describe-instances --filters "Name=instance-type,Values=p3.*,g4dn.*"`
to enumerate live instances and tag-check ownership.

## Fix

1. **Pick the right next generation** based on workload profile, not on
   "the latest":
   - Inference, small/medium models: **G4dn → G5** (A10G, 24 GB) or
     **G4dn → G6** (L4, 24 GB, more energy-efficient)
   - Inference, LLMs / large models: **P3 → P4d** (A100 40 GB) or **P3
     → G5.12xl** depending on memory needs
   - Training, mid-scale: **P3 → P4d** (A100, NVLink, BF16)
   - Training, frontier: **P4d → P5** (H100) or **P5 → P5e/P5en** (H200)
2. **Benchmark on the new generation**. Run the same workload (same
   model, same batch size, same load pattern) for 48 hours. Compute:
   - Cost per 1k inferences (not hourly cost)
   - Latency p50, p95, p99
   - Throughput per instance
3. **Validate driver + CUDA + framework**. Newer GPUs need newer CUDA
   (P5 = CUDA 11.8+ minimum, H100 features at CUDA 12). Older PyTorch
   builds may not include the right kernels. Test the full stack, not
   just the model file.
4. **Account for commitment portfolio** before migration. If the legacy
   instance is covered by a Compute Savings Plan or an EC2 Instance
   Savings Plan, migrating to a different family can strand the
   commitment. Plan the move alongside commitment refresh (see
   `references/finops-aws.md` commitment portfolio section).
5. **Cut over** during a maintenance window, with a snapshot of the
   previous workload's performance benchmarks for rollback comparison.

## Anti-pattern

- Comparing only **hourly rates**. A `p5.48xlarge` ($98/hour) looks vastly
  more expensive than a `p3.16xlarge` ($24.48/hour) - but on the right
  workload the H100 can deliver 5-10x the throughput, making the
  cost-per-inference half. The decision must be cost per unit of work.
- Assuming framework compatibility. PyTorch ≤ 1.10 has no native H100
  support; some custom CUDA kernels need rewrites. Always run a
  representative inference / training step on the new hardware before
  committing.
- Migrating before the commitment runs out. A 1-year Standard RI on
  `p3.8xlarge` with 9 months left is sunk cost - migrating mid-term may
  cost more than waiting and modernising at renewal.
- Skipping the spend-impact check. Newer generations are not always
  cheaper at the **billed-amount** level; some workloads run for the
  same wall-clock time and produce a higher bill. Without the benchmark,
  modernisation can be a net negative.

## See also

- `playbooks/aws-gpu-instance-oversized.md` - rightsizing within a
  generation
- `playbooks/aws-mig-candidate.md` - if the workload needs A100/H100
  features but only a slice
- `references/finops-aws.md` - AWS commitment portfolio (impact of
  RI/SP on modernisation timing), AWS GPU family map
- `references/finops-waste-detection-playbooks.md` - Category 7 (AI/ML
  inefficiency) and the "modernization" waste category

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
