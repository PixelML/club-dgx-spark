import sys, json, time, os
import os
OUT = os.environ.get("OUT", "bench_long.json")
sys.argv = [sys.argv[0], os.environ.get("URL", "http://HOST:8888/v1"), os.environ.get("MODEL", "glm-5.3-flash"), "/dev/null"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench.py")).read().split("res = {}")[0]
exec(src)
out = {}
for label, words, n in (("ctx_128k", 34500, 1), ("ctx_245k", 66000, 1)):
    ttft, dt, u = stream("Count the distinct prefixes in: " + pad(words), 128, False)
    out[label] = {"prompt_tokens": u["prompt_tokens"], "ttft_s": ttft, "prefill_tok_s": u["prompt_tokens"]/ttft, "completion_tokens": u["completion_tokens"], "decode_tok_s": u["completion_tokens"]/dt}
    print(label, json.dumps(out[label]), flush=True)
    json.dump(out, open(OUT, "w"), indent=1)
