# DeepSeek-V4.1-Flash-1017, PixelML EXL3 3 bpw experts, 2x DGX Spark TP=2, vLLM + sudoingX recipe (2026-10-24)

Receipts for [the notebook](../../notebooks/2026-10-24-deepseek-v4.1-flash-1017-exl3-2node-tp2-vllm.ipynb).

## Credits

- **sudoingX** ([@sudoingX](https://github.com/sudoingX)) authored the engine, the GB10 patches and the `vllm_exl3_moe` plugin kernels, the launcher and the bench scripts: [sudoingX/dgx-spark-deepseek-v41 @ f8f20b370e41a3a220bc7d1ab96a61e4daa84964](https://github.com/sudoingX/dgx-spark-deepseek-v41/tree/f8f20b370e41a3a220bc7d1ab96a61e4daa84964) (Apache-2.0). The RDMA all-reduce ring, the L2 prefetch kernel and the grouped EXL3 prompt kernels inside it come from TensorFold, authored by **Ash** ([@ashhart](https://github.com/ashhart)) and **bertholomus** ([@bertholomus](https://github.com/bertholomus)), per the recipe's NOTICE.
- **DeepSeek-AI** ([@deepseek-ai](https://huggingface.co/deepseek-ai)) authored the base model and the Engram tables: [DeepSeek-V4.1-Flash-1017 @ 1bae0e10](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/tree/1bae0e1088993b9b82de08f59de5be5a34e42170) (MIT).
- **Turboderp** ([@turboderp](https://github.com/turboderp)) authored the EXL3 format and the exllamav3 kernels: [exllamav3 v1.6.0](https://github.com/turboderp-org/exllamav3/tree/151539c77abc7ab7425d30da7a4e8e3c5c154e7b) (MIT).
- **sfxnz** ([@sfxnz](https://github.com/sfxnz)) authored `tools/quantize_experts_exl3.py`, the script PixelML used to make the 3 bpw experts pack: [sfxnz/DeepSeek-V4.1-Flash-EXL3-vLLM-2x-DGX-Spark @ 3de91468](https://github.com/sfxnz/DeepSeek-V4.1-Flash-EXL3-vLLM-2x-DGX-Spark/tree/3de914682d0880c8e478712a60ada930339c22e4) (MIT).
- **bertholomus** ([@bertholomus](https://github.com/bertholomus)) authored the bench client `kit_bench.py` ([TensorFold @ fe6f9f7b](https://github.com/bertholomus/TensorFold/blob/fe6f9f7b373db76422ddfa121577238474c0a1b7/tools/dsv41/kit_bench.py), Apache-2.0).
- **vLLM** ([vllm-project](https://github.com/vllm-project/vllm)) @ 6e517b15c1833cf72a7f557ee32524d98682e617 (Apache-2.0).

## Files

| file | what |
|---|---|
| `pins.json` | every revision, image, launcher setting and the metric definition |
| `decode_b_final_9reps.json` | headline: `kit_bench.py decode --set b --tokens 384 --reps 9`, policy `conf` with the measured round table (boot 5) |
| `spec_counters_before_after.txt` | vLLM `/metrics` DSpark counters bracketing the headline run (acceptance = accepted / draft tokens) |
| `prefill_8k_final.json` | 8,192-token prompt, prompt tokens / TTFT (boot 5) |
| `nvsmi_head_during_decode.csv` | head-node GPU power (W), temperature (C), utilization (%) every 5 s during the headline run |
| `decode_b_spec_boot4.json`, `prefill_8k_boot4.json` | boot 4: same knobs, the recipe's default (2.7 bpw) round table, prefill chunk 512 |
| `decode_b_nospec_boot3.json` | boot 3: DSpark drafter off, 64K context |
| `depth_sweep/` | `scripts/bench/depth_sweep.sh`: fixed depths 5..0 then `conf` with the table measured from them; `run.log` has the summary table |

Masking: node names, interfaces and paths are replaced by `<node-a>`, `<node-b>`, `<fabric-if>`, `<model-dir>`. Raw receipts carry no host identifiers (checked with grep before commit).
