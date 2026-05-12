---
name: aws-mig-candidate
scope: aws
service: AWS EC2
waste_category: overprovisioned
confidence: possible
---

# AWS MIG (Multi-Instance GPU) Candidate

## Problem

NVIDIA Multi-Instance GPU (MIG) partitions a single A100 or H100 into up
to 7 hardware-isolated GPU instances, each with dedicated SM compute and
memory. On AWS, MIG is available on `p4d` / `p4de` (A100 40 GB / 80 GB)
and `p5` / `p5e` / `p5en` (H100 / H200). A workload that uses well under
1/7 of an A100 or H100 - measured by both compute fraction and memory -
is paying for a whole GPU when it could share the hardware via MIG. With
`p4d.24xlarge` at ~$33/hour (8 x A100) and `p5.48xlarge` at ~$98/hour (8 x
H100), running multiple light workloads on a MIG-partitioned single
server can recover 4-7x of the GPU bill compared to one GPU per workload.

## Symptoms

- Workload runs on A100 (P4d/P4de) or H100 (P5/P5e/P5en)
- DCGM `DCGM_FI_PROF_GR_ENGINE_ACTIVE` < 14% over 14 days (= 1/7 of full
  engine usage)
- DCGM `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` < 10% (ML inference using small
  fraction of tensor cores)
- DCGM `DCGM_FI_DEV_FB_USED` < 10 GB (out of 40 GB or 80 GB total)
- Workload does NOT need NCCL or multi-GPU collective communication
- Workload has predictable, isolated memory and compute requirements

## Detection

```promql
# DCGM telemetry signature for MIG candidate
avg_over_time(DCGM_FI_PROF_GR_ENGINE_ACTIVE{gpu="0"}[14d]) < 0.14
  AND avg_over_time(DCGM_FI_DEV_FB_USED{gpu="0"}[14d]) < 10737418240  # bytes = 10 GB
  AND avg_over_time(DCGM_FI_PROF_PIPE_TENSOR_ACTIVE{gpu="0"}[14d]) < 0.10
```

The 14% threshold is intentional: it is the inverse of 7 (max MIG slices
per A100), so a workload below that usage genuinely fits in one slice. For
H100 the same threshold applies (also 7 slices).

Prerequisite: the instance must be A100 or H100. G5 / G6 / G4dn / P3 do
**not** support MIG.

## Fix

1. **Choose a MIG profile** matching the workload's memory and compute
   needs. A100 40 GB supports profiles like `1g.5gb`, `2g.10gb`,
   `3g.20gb`, `7g.40gb`. A100 80 GB and H100 80 GB scale these
   proportionally (`1g.10gb` etc.). Pick the smallest profile that fits
   the model with 20% headroom.
2. **Enable MIG mode** on the GPU:
   `sudo nvidia-smi -i 0 -mig 1` (requires reboot or process restart).
3. **Create the MIG instances** with `nvidia-smi mig -cgi <profile-id> -C`.
4. **Expose slices to workloads**:
   - **Kubernetes (EKS)**: install the NVIDIA Device Plugin with the
     `--mig-strategy=single` or `--mig-strategy=mixed` flag; pods request
     `nvidia.com/mig-1g.5gb: 1` instead of `nvidia.com/gpu: 1`.
   - **SageMaker**: as of late 2025, SageMaker managed endpoints have
     limited native MIG exposure. For SageMaker, the practical route is to
     run inference on a self-managed EKS cluster with MIG-enabled nodes,
     using SageMaker only for training / Studio / managed catalogue
     features. Verify current SageMaker MIG support before planning.
5. **Benchmark each slice in isolation** - because MIG is hardware
   isolation, neighbouring slices cannot impact this one. Compare slice
   throughput / latency to full-GPU baseline.

## Anti-pattern

- Enabling MIG on a workload that uses NCCL all-reduce or any cross-GPU
  collective communication. MIG explicitly prevents inter-slice
  communication; the workload will fail or fall back to slow CPU paths.
- Picking a profile too small (e.g. `1g.5gb` for a model that occasionally
  needs 8 GB during request bursts). MIG slices cannot grow - the workload
  will OOM at peak.
- Activating MIG on a single-workload instance and then never partitioning
  it to multiple tenants - MIG without multi-tenancy gives all the
  constraints with none of the cost recovery.
- Forgetting that MIG configuration changes require GPU reset (workloads
  must drain). Plan MIG changes as a scheduled maintenance, not a hot swap.

## See also

- `playbooks/aws-multi-gpu-underutilized.md` - related pattern when 8 GPUs
  are present but only 1 is used (MIG fixes the within-GPU case;
  single-GPU rightsize fixes the across-GPU case)
- `playbooks/aws-gpu-instance-oversized.md` - the general rightsize
  playbook for GPUs that should stay whole but on a smaller SKU
- `references/finops-for-ai.md` - DCGM telemetry, MIG in Kubernetes
  pod-level cost attribution
- `references/finops-waste-detection-playbooks.md` - Category 7 (AI/ML
  inefficiency) taxonomy
