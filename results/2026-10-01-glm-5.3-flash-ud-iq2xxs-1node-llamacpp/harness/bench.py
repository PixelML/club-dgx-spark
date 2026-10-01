#!/usr/bin/env python3
"""Decode/prefill bench for an OpenAI-compatible endpoint. Tokens from final usage object."""
import json, sys, time, random, statistics, urllib.request
URL = sys.argv[1]; MODEL = sys.argv[2]; N = 3  # usage: bench.py http://HOST:PORT/v1 MODEL out.json
def stream(prompt, max_tokens, think=None, ignore_eos=True):
    body = {"model": MODEL, "messages": [{"role":"user","content":prompt}], "temperature": 0,
            "max_tokens": max_tokens, "stream": True, "stream_options": {"include_usage": True}}
    if ignore_eos: body["ignore_eos"] = True
    if think is not None: body["chat_template_kwargs"] = {"enable_thinking": think}
    req = urllib.request.Request(URL + "/chat/completions", json.dumps(body).encode(), {"Content-Type":"application/json"})
    t0 = time.time(); tf = None; usage = None
    with urllib.request.urlopen(req, timeout=3600) as r:
        for line in r:
            line = line.decode().strip()
            if not line.startswith("data:") or line.endswith("[DONE]"): continue
            j = json.loads(line[5:])
            if j.get("usage"): usage = j["usage"]
            ch = j.get("choices") or []
            if ch and tf is None:
                d = ch[0].get("delta", {})
                if d.get("content") or d.get("reasoning_content") or d.get("reasoning"): tf = time.time()
    t1 = time.time()
    return tf - t0 if tf else None, t1 - (tf or t0), usage
def pad(nwords):
    random.seed(time.time())
    w = ["alpha","river","stone","lamp","orbit","cedar","quartz","lattice","ember","vector"]
    return " ".join(random.choice(w) + str(random.randint(0, 9999)) for _ in range(nwords))
res = {}
stream("Say hi.", 8)  # warm
def dec(label, prompt_fn, out=256, think=None):
    rows = []
    for _ in range(N):
        ttft, dt, u = stream(prompt_fn(), out, think)
        rows.append((ttft, u["prompt_tokens"], u["completion_tokens"], u["completion_tokens"]/dt if dt>0 else 0))
    m = lambda i: statistics.median(r[i] for r in rows)
    res[label] = {"ttft_s": m(0), "prompt_tokens": m(1), "completion_tokens": m(2), "decode_tok_s": m(3), "decode_range": [min(r[3] for r in rows), max(r[3] for r in rows)]}
    print(label, json.dumps(res[label]), flush=True)
dec("decode_short_think_off", lambda: "Write a detailed essay about the history of the printing press. " + pad(3), 256, False)
for label, words in (("prefill_4k", 2000), ("prefill_16k", 7500)):
    rows = []
    for _ in range(N):
        ttft, dt, u = stream("Summarize: " + pad(words), 1, False, ignore_eos=False)
        rows.append((ttft, u["prompt_tokens"], u["prompt_tokens"]/ttft))
    res[label] = {"prompt_tokens": statistics.median(r[1] for r in rows), "ttft_s": statistics.median(r[0] for r in rows),
                  "prefill_tok_s": statistics.median(r[2] for r in rows), "range": [min(r[2] for r in rows), max(r[2] for r in rows)]}
    print(label, json.dumps(res[label]), flush=True)
dec("decode_at_16k_think_off", lambda: "Continue listing these tokens, then describe them: " + pad(7500), 256, False)
dec("decode_short_think_on", lambda: "What is 17*23? Think briefly.", 256, True)
json.dump(res, open(sys.argv[3] if len(sys.argv) > 3 else "bench.json", "w"), indent=1)
