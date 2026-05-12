---
name: aws-multi-gpu-underutilized
scope: aws
service: AWS EC2
waste_category: overprovisioned
confidence: obvious
---

# AWS Multi-GPU Instance with Single-GPU Workload

## Problem

High-end GPU instances pack multiple GPUs in a single server: `g5.48xlarge`
(8 x A10G), `p4d.24xlarge` (8 x A100 40 GB), `p4de.24xlarge` (8 x A100 80
GB), `p5.48xlarge` (8 x H100). Pricing is for the whole server: ~$16/hour
for `g5.48xlarge`, ~$33/hour for `p4d.24xlarge`, ~$98/hour for
`p5.48xlarge`. When the workload runs on a single GPU and the other seven
sit idle, the customer is paying 7/8 of the bill for thin air. This is one
of the highest-confidence waste patterns: per-GPU telemetry shows it
unambiguously.

## Symptoms

- Instance type is multi-GPU (G5.48xl, G6.48xl, P4d, P4de, P5, P5e/P5en)
- DCGM shows GPU 0 active, GPUs 1-7 idle
- Framework code uses single-device tensor placement (`.to('cuda:0')` or
  `device='cuda'` without index), or model is too small to need data
  parallelism
- No NCCL traffic between GPUs in the workload's network telemetry
- The instance was sized for a future scale-out plan that never materialised

## Detection

CloudWatch alone does not expose per-GPU breakdown. Two paths to get the
per-device signal:

1. **DCGM Exporter** scraped by Prometheus / CloudWatch agent, with the
   `gpu` label preserved:

   ```promql
   # Average utilisation per device over 14 days
   avg_over_time(DCGM_FI_DEV_GPU_UTIL{instance="<id>"}[14d])
   ```

   GPU 0 > 30% and GPUs 1-7 < 5% is the signature.

2. **One-off check via SSM**: run `nvidia-smi --query-gpu=index,utilization.gpu,utilization.memory --format=csv -l 60`
   over a representative workload window and inspect the per-index columns.

The more reliable DCGM signal is per-GPU `DCGM_FI_PROF_GR_ENGINE_ACTIVE`
(real engine activity, not the legacy "did anything" boolean). On a
correctly multi-GPU workload, all 8 devices should be > 50% during peak;
single-GPU workload on the same hardware will show GPU 0 high and the rest
near zero.

## Fix

1. **Confirm the workload is genuinely single-device.** Read the model
   loader and inference code. Look for `nn.DataParallel`,
   `nn.parallel.DistributedDataParallel`, `tf.distribute.MirroredStrategy`,
   or framework-equivalent constructs. If absent, the workload is
   single-device by design.
2. **Check peak windows for re-training or batch eval.** A workload that
   is single-GPU at inference time can fan out to all GPUs during a weekly
   retraining job. If retraining genuinely needs the multi-GPU box,
   schedule it separately on an on-demand or Spot instance and keep the
   inference endpoint on a single-GPU SKU.
3. **Pick the target single-GPU SKU.** From `p4d.24xlarge` (8 x A100): a
   `g5.xlarge` or `g5.2xlarge` is the right target for small/medium
   models; a `p4d.24xlarge` split via MIG (see
   [aws-mig-candidate.md](aws-mig-candidate.md)) is the right move if the
   workload genuinely needs A100 features. From `g5.48xlarge`: a
   `g5.xlarge` or `g5.2xlarge`.
4. **Benchmark and cut over** following the same procedure as standard GPU
   rightsizing (see [aws-gpu-instance-oversized.md](aws-gpu-instance-oversized.md)).

## Anti-pattern

- Assuming a workload is single-GPU based on average DCGM telemetry
  without checking peak hours - a model that fans out to 8 GPUs once per
  week for retraining will report 7/8 idle on average.
- Migrating away from a multi-GPU instance that is reserved or covered by
  a Savings Plan without first calculating the commitment penalty. The
  per-hour saving may be offset by stranded commitment cost; recover the
  commitment through portfolio rebalancing first.
- Replacing an 8-GPU instance with 8 single-GPU instances for parallel
  workloads - the per-instance overhead (EBS root volume, network ENIs,
  monitoring agents) adds up and may exceed the original cost. MIG is the
  right tool for that case if the GPUs are A100/H100.

## See also

- `playbooks/aws-mig-candidate.md` - when the workload should stay on the
  large GPU but only use a hardware-partitioned slice
- `playbooks/aws-gpu-instance-oversized.md` - the general GPU rightsizing
  playbook
- `references/finops-for-ai.md` - DCGM telemetry and per-pod GPU
  attribution
- `references/finops-waste-detection-playbooks.md` - Category 7 (AI/ML
  inefficiency) taxonomy
