# First-time DGX Spark setup

Derived from the verified dual-node recipes in this organization. Every step here is required by at least one measured recipe; no untested shortcuts are included.

## Hardware baseline

| Requirement | Why |
|---|---|
| 2× NVIDIA DGX Spark (GB10, SM121, 128 GiB UMA each) | All current recipes use tensor-parallel 2 across two nodes |
| Direct ConnectX-7 QSFP cable between nodes | NCCL/RoCE interconnect; Wi-Fi or an external switch is not validated |
| ~200 GiB free NVMe per node | 181 GiB is the largest verified checkpoint; add headroom for KV and logs |
| Same Linux username, UID, and GID on both nodes | Required by SSHFS model-cache sharing and rsync scripts |

## Node software

1. **NVIDIA driver and CUDA** — use the DGX Spark factory image or the current NVIDIA DGX software release. Do not mix driver versions between nodes.
2. **Docker** — install Docker Engine and the NVIDIA Container Toolkit. Configure the non-root deployment user for Docker without sudo.
3. **Passwordless SSH** — from head to worker (`ssh-keygen`, then `ssh-copy-id <worker-user>@<worker-ip>`). Ray and the launch scripts depend on this.
4. **Hugging Face CLI** — install `huggingface-cli` on the head node for model download.
5. **rsync** — required on both nodes for model cache distribution.

## Networking

All dual-node recipes use a direct CX7 QSFP cable with RoCE. NCCL must be pinned to the CX7 interfaces; the on-board Ethernet cannot carry NCCL traffic without hanging.

Key NCCL environment variables used across recipes:

```bash
export NCCL_SOCKET_IFNAME=enp1s0f1np1
export NCCL_IB_HCA=rocep1s0f1
```

The exact interface names may differ per system — verify with `ip link show` and `ibdev2netdev` on each node before launching.

Ray may use private IP aliases between nodes; NCCL cannot. Always let NCCL discover the CX7 link via the pinned interface names.

## Storage and model cache

| Approach | Used by | When to choose |
|---|---|---|
| rsync to both nodes' local NVMe | GLM-5.3-Flash, Step-3.7-Flash, Hunyuan 3 | Default: simplest, no runtime network dependency |
| SSHFS shared mount | Inkling-Small | When both nodes must read the same cache without a copy step |

Both work. rsync is faster at steady state (local NVMe read); SSHFS avoids a distribution step but adds network latency on every model load.

## EarlyOOM (DGX Spark specific)

Disable earlyoom before loading large models. The near-UMA memory model means vLLM/Ray can exceed the threshold during model load and trigger a premature OOM kill.

```bash
sudo systemctl disable --now earlyoom
```

Restore it after the workload if the node is shared.

## Verification before first launch

1. Both nodes see the GPU: `nvidia-smi` returns one GB10 device per node.
2. Direct link is up: `ip link show <cx7-interface>` shows `state UP` on both nodes.
3. RDMA device is visible: `ibstat` or `ibdev2netdev` returns the CX7 port.
4. Passwordless SSH works head → worker with no prompt.
5. Free disk space is at least checkpoint size + 20% on each node.
6. Docker runs without sudo: `docker info` succeeds as the deployment user.

## What is not covered here

- Single-node recipes (no verified single-Spark recipe exists yet).
- Three or more nodes (no recipe exists).
- Distributed training or fine-tuning (no recipe exists).
- Image or video generation as a standalone workload (no recipe exists).

See [GAP-ANALYSIS.md](GAP-ANALYSIS.md) for the full gap list.