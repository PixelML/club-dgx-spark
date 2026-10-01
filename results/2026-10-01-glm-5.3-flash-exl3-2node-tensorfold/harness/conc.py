#!/usr/bin/env python3
"""Concurrency bench: C parallel streams of a short prose prompt, thinking off, fixed output length.
Aggregate = total completion tokens / wall time from first send to last finish. Median of N rounds."""
import json, os, sys, time, statistics, threading
sys.argv = [sys.argv[0], os.environ.get("URL", "http://HOST:8888/v1"), os.environ.get("MODEL", "GLM-5.3-Flash-EXL3"), "/dev/null"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench.py")).read().split("res = {}")[0])
OUT = os.environ.get("OUT", "bench_conc.json"); N = int(os.environ.get("N", "3")); TOK = int(os.environ.get("TOK", "512"))
TOPICS = ["the printing press", "the steam engine", "the telegraph", "the transistor"]

def round_(c):
    res = [None] * c
    def one(i):
        t0 = time.time()
        ttft, dt, u = stream(f"Write a detailed essay about the history of {TOPICS[i]}. " + pad(3), TOK, False)
        res[i] = (ttft, u["completion_tokens"], u["completion_tokens"] / dt, t0, time.time())
    th = [threading.Thread(target=one, args=(i,)) for i in range(c)]
    for t in th: t.start()
    for t in th: t.join()
    wall = max(r[4] for r in res) - min(r[3] for r in res)
    return {"aggregate_tok_s": sum(r[1] for r in res) / wall, "per_request_tok_s": statistics.mean(r[2] for r in res),
            "ttft_s": statistics.mean(r[0] for r in res), "completion_tokens": sum(r[1] for r in res)}

stream("Say hi.", 8)  # warm
out = {"method": f"C parallel streams, unique prose prompt each, thinking off, ignore_eos, {TOK} output tokens, temperature 0, median of {N} rounds; aggregate = total tokens / wall time"}
for c in (1, 2, 3, 4):
    rounds = [round_(c) for _ in range(N)]
    m = {k: statistics.median(r[k] for r in rounds) for k in rounds[0]}
    m["aggregate_range"] = [min(r["aggregate_tok_s"] for r in rounds), max(r["aggregate_tok_s"] for r in rounds)]
    out[f"c{c}"] = m
    print(f"c={c}", json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in m.items()}), flush=True)
    json.dump(out, open(OUT, "w"), indent=1)
