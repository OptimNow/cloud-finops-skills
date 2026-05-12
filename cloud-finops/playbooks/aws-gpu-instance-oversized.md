---
name: aws-gpu-instance-oversized
scope: aws
service: AWS EC2
waste_category: overprovisioned
confidence: likely
---

# AWS Oversized GPU Instance

## Problem

GPU instances are the most expensive on-demand SKUs in EC2. A `g5.xlarge`
(A10G, 24 GB) is ~$1.00/hour ~= $730/month; a `g5.12xlarge` (4 x A10G)
is ~$5.67/hour ~= $4,140/month; a `p4d.24xlarge` (8 x A100 40 GB) is
~$32.77/hour ~= $23,920/month. Picking an instance with more GPU compute
and memory than the workload uses is one of the highest-dollar waste
patterns in AWS - and one of the hardest to spot, because the basic
`GPUUtilization` CloudWatch metric (equivalent to `nvidia-smi`'s
`GPU-Util`) reports whether the GPU did anything in the interval, not how
much of its compute capacity was actually used (see
[finops-for-ai.md](../references/finops-for-ai.md), section on GPU
telemetry).

## Symptoms

- CloudWatch `GPUUtilization` < 30% over a 14-day window
- CloudWatch `GPUMemoryUtilization` < 40% over the same window
- The model's loaded weights fit in well under half of the GPU memory
- Model latency p95 is far below the SLA (room to move to a smaller GPU
  without violating user-facing budgets)
- The instance was picked because "we always use g5.12xlarge for ML" or
  "the model file is large" rather than from measurement

## Detection

Two-tier signal: cheap (CloudWatch) for triage, expensive (DCGM) for the
real decision.

CloudWatch quick scan:

```
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name GPUUtilization \
  --dimensions Name=InstanceId,Value=<id> \
  --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time   $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Average,Maximum
```

Note: `GPUUtilization` in CloudWatch is the legacy `nvidia-smi` metric and
overestimates real compute usage. Treat any value < 30% as "investigate
further", not "definitely oversized".

DCGM (deploy DCGM Exporter on the instance via SSM or Helm) gives the
honest answer:

| Metric | Threshold for "oversized" |
|---|---|
| `DCGM_FI_PROF_GR_ENGINE_ACTIVE` | < 20% over 14 days |
| `DCGM_FI_PROF_SM_ACTIVE` | < 25% over 14 days |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | < 15% for ML inference workloads |
| `DCGM_FI_DEV_FB_USED` | < 40% of total frame buffer |

If three of the four are below threshold, the instance is a strong
rightsize candidate.

## Fix

1. **Identify the target instance type.** Smaller in the same family
   first (`g5.12xlarge` → `g5.4xlarge` → `g5.xlarge`), then cross-family
   if memory or compute profile changes (G5 → G6 for L4 efficiency; P4d →
   G5 if A100 perf is overkill; G5 → Inf2 if model is supported on AWS
   Neuron).
2. **Benchmark on the target.** Run the production workload (same model,
   same batch size, same load pattern) on the target instance for 24-48
   hours. Compare `ModelLatency` p50/p95/p99 and `ThroughputPerInstance`.
3. **Validate peak.** Average utilisation hides bursts. Replay peak hour
   traffic against the candidate; check that latency stays inside SLA at
   2x peak.
4. **Validate memory.** Confirm the model + activations + KV cache (for
   LLMs) fits within the target's frame buffer with 20% headroom for
   request-size variability.
5. **Cut over** behind a weight-shifted endpoint variant (`InitialVariantWeight`
   ramp 10% → 50% → 100%) so a regression is reversible.

## Anti-pattern

- Rightsizing on **average** utilisation only. Models with batch jobs,
  monthly retraining, or end-of-quarter spikes will look oversized for 28
  days then break on day 29.
- Trusting `GPUUtilization` (CloudWatch / `nvidia-smi`) without DCGM
  cross-check. The metric is a "did the GPU do anything" boolean dressed
  up as a percentage - a workload touching 1 SM out of 108 on an H100
  reports `GPU-Util: 100%`.
- Picking a smaller instance whose frame buffer is too small for the
  model. Always size on memory first, compute second.
- Forgetting that lower-tier GPUs may need a different software stack
  (CUDA version, driver, framework backend) - test the full stack, not
  just the model file.

## See also

- `references/finops-for-ai.md` - "GPU utilization is misleading" section
  on DCGM metrics
- `playbooks/aws-multi-gpu-underutilized.md` - related pattern when only
  one of several GPUs is doing work
- `playbooks/aws-gpu-for-cpu-bound-workload.md` - when the GPU is so idle
  the right move is to leave GPU entirely
- `playbooks/aws-outdated-gpu-generation.md` - related modernisation move
- `references/finops-waste-detection-playbooks.md` - Category 7 (AI/ML
  inefficiency) taxonomy
