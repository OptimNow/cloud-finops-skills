---
name: aws-gpu-for-cpu-bound-workload
scope: aws
service: AWS EC2
waste_category: overprovisioned
confidence: likely
---

# AWS GPU Instance for a CPU-Bound Workload

## Problem

Teams provision GPU instances by reflex for anything labelled "AI" -
embeddings APIs, classical ML inference, small-model classifiers, data
preprocessing pipelines, retrieval-augmented search. In many of these,
the GPU sits idle while the actual work runs on the CPU (tokenisation,
JSON serialisation, network I/O, vector arithmetic that fits in CPU
SIMD). The customer is paying GPU prices for CPU work. A `g4dn.xlarge`
is ~$0.53/hour ~= $385/month; the equivalent CPU-bound `c7i.xlarge` is
~$0.18/hour ~= $130/month. For larger instances the gap widens: a
`g5.4xlarge` is ~$1.62/hour vs `c7i.4xlarge` at ~$0.71/hour. Multiplied
across an inference fleet, the wrong compute choice is the costliest
silent waste in an AI stack.

## Symptoms

- DCGM `DCGM_FI_PROF_GR_ENGINE_ACTIVE` < 5% sustained over 14 days
- DCGM `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` < 2% (no tensor core work)
- CloudWatch `CPUUtilization` > 60% on the same instance during the same
  windows
- Model is small (classical ML, embedding generation, sentence-transformer
  models < 500 MB), or the per-request work is dominated by tokenisation /
  network / pre-processing
- The team's stated reason for the GPU is "the inference framework
  defaults to GPU" rather than a measured perf requirement

## Detection

```promql
# Combined signature: GPU asleep, CPU busy
avg_over_time(DCGM_FI_PROF_GR_ENGINE_ACTIVE{instance="<id>"}[14d]) < 0.05
  AND avg_over_time(node_cpu_seconds_total{instance="<id>",mode!="idle"}[14d]) > 0.60
```

Or via CloudWatch + a one-off DCGM scrape:

```
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=<id> \
  --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time   $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Average,Maximum
```

If average CPU > 60% and `GPUUtilization` (even the legacy metric) < 10%,
the diagnosis is near-certain - confirm with one DCGM run, then move.

## Fix

1. **Pick a CPU target**. For most inference workloads moving off GPU,
   the right family is `c7i` (Intel Sapphire Rapids) or `c7g` (Graviton3,
   cheaper if the framework supports ARM). For latency-sensitive
   embedding APIs, consider `c7i.large` to `c7i.4xlarge`; for batch
   preprocessing, `c7g` Spot is highly cost-effective.
2. **Consider Inferentia/Trainium as a middle path**. If the workload
   genuinely benefits from hardware acceleration but doesn't need a
   general-purpose GPU, `inf2` (Inferentia2) is purpose-built for
   inference and runs ~30-40% cheaper per inference than `g5` for
   supported models. Check AWS Neuron compatibility for the model family
   (transformers, CNNs, common architectures are well supported).
3. **Optimise the model for CPU before benchmarking**. Convert to ONNX,
   quantise to INT8 (if accuracy holds), batch requests. CPU inference is
   far more sensitive to model format than GPU inference - a naively
   ported PyTorch model can be 10x slower than the same model in ONNX
   Runtime with INT8 quantisation.
4. **Benchmark**: target the same latency SLA and ~80% of original
   throughput on the candidate CPU instance. Compare cost per 1k
   inferences end-to-end (not just instance/hour).
5. **Cut over** with weight-shift / variant ramp (see
   [aws-gpu-instance-oversized.md](aws-gpu-instance-oversized.md), step 5).

## Anti-pattern

- Migrating to CPU without testing peak periods. Some workloads are CPU-
  bound 99% of the time but GPU-bound during a daily / weekly batch
  retraining or vector index rebuild. Run the migration only on the
  always-on inference fleet; keep the batch jobs on GPU.
- Skipping the ONNX / quantisation step. A direct PyTorch-on-CPU move
  produces a "CPU is too slow" verdict that is actually a model-format
  problem.
- Assuming Inferentia is a drop-in replacement. Inf2 requires AWS Neuron
  SDK compilation; not all model architectures are supported.
- Ignoring the GPU spikes that DO exist - if the workload has a 30 min /
  day window of genuine GPU need, scheduled scale-up of a single GPU
  instance for that window is cheaper than always-on GPU capacity.

## See also

- `playbooks/aws-gpu-instance-oversized.md` - when the workload needs a
  GPU but a smaller one
- `playbooks/aws-multi-gpu-underutilized.md` - when 7 of 8 GPUs are idle
- `references/finops-for-ai.md` - "GPU utilization is misleading" section
  and DCGM metric reference
- `references/finops-ai-self-hosted-vs-managed.md` - cost framing for
  self-hosted inference compute
- `references/finops-waste-detection-playbooks.md` - Category 7 (AI/ML
  inefficiency) taxonomy

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
