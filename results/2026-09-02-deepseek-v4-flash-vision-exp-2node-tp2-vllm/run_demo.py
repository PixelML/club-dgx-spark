#!/usr/bin/env python3
"""LIVE demo run: WW1 voxel diorama prompt -> extract HTML -> render with
playwright chromium -> send the rendered PNG back to the model as a vision
proof. Writes demo/ww1-voxel-diorama.html, demo/preview.png, and
demo/demo_receipt.json. Not imported by the notebook."""
import base64
import json
import os
import re
import time

import requests

BASE = os.environ["VISION_ENDPOINT"].rstrip("/")
MODEL = os.environ.get("MODEL_ID", "apollo-deepseek-v4-flash-vision-exp")
HERE = os.path.dirname(os.path.abspath(__file__))
DEMO_DIR = os.path.join(HERE, "demo")
os.makedirs(DEMO_DIR, exist_ok=True)

PROMPT = (
    "Design and create a voxel diorama of an active world-war-one warzone. "
    "Make it detailed, impressive, and varied, and use colorful voxels. "
    "Make the scene feel intricate with great attention to detail. Make the "
    "scene feel animated and interactive, with realistic destruction "
    "physics, soldier combat, and logistics. Include various different "
    "vehicles, land, air, and sea. Use webGL and whatever libraries to get "
    "this done but make sure I can paste it all into a single HTML file "
    "and open it in Chrome."
)
SYSTEM_PROMPT = "Return only one complete HTML file in a single ```html fence. No explanation."

# Attempt 1 (max_tokens=8000, reasoning left on, no system message) spent
# 27,466 characters of its reasoning field before the 8,000-token budget
# ran out and the HTML was cut off at 955 bytes. Kept as
# demo_receipt_attempt1_failed.json / ww1-voxel-diorama_attempt1_failed.html
# / preview_attempt1_failed.png / vision_proof_attempt1_failed.json.
# Attempt 2 disables reasoning at the request level
# (chat_template_kwargs.thinking=false, confirmed empirically against this
# endpoint: /v1/chat/completions returns message.reasoning=null and
# finish_reason=stop for a trivial prompt with this flag set), raises the
# budget to 32,000 tokens, and adds a system message asking for exactly one
# fenced HTML block.
t0 = time.time()
payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": PROMPT},
    ],
    "temperature": 0.7,
    "max_tokens": 32000,
    "chat_template_kwargs": {"thinking": False},
}
r = requests.post(f"{BASE}/chat/completions", json=payload, timeout=1200)
r.raise_for_status()
resp = r.json()
dt = time.time() - t0

msg = resp["choices"][0]["message"]
content = msg.get("content") or ""
reasoning = msg.get("reasoning") or ""
usage = resp.get("usage", {})

# Extract every ```html ... ``` (or bare <html>...</html>) block, take the
# largest.
blocks = re.findall(r"```html\s*(.*?)```", content, re.S)
if not blocks:
    blocks = re.findall(r"```\s*(<!DOCTYPE.*?</html>)\s*```", content, re.S)
if not blocks:
    m = re.search(r"(<!DOCTYPE.*?</html>)", content, re.S | re.I)
    blocks = [m.group(1)] if m else []
if not blocks:
    blocks = [content]  # fall back to raw content

html = max(blocks, key=len)
html_path = os.path.join(DEMO_DIR, "ww1-voxel-diorama.html")
with open(html_path, "w") as f:
    f.write(html)

receipt = {
    "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "prompt": PROMPT,
    "request_params": {"temperature": 0.7, "max_tokens": 32000, "chat_template_kwargs": {"thinking": False}, "system_message": SYSTEM_PROMPT},
    "wall_time_s": round(dt, 3),
    "usage": usage,
    "finish_reason": resp["choices"][0].get("finish_reason"),
    "reasoning_chars": len(reasoning),
    "content_chars": len(content),
    "html_blocks_found": len(blocks),
    "extracted_html_bytes": len(html.encode("utf-8")),
    "html_path": "demo/ww1-voxel-diorama.html",
}
with open(os.path.join(DEMO_DIR, "demo_receipt.json"), "w") as f:
    json.dump(receipt, f, indent=2)

print("HTML bytes:", receipt["extracted_html_bytes"])
print("finish_reason:", receipt["finish_reason"])
print("usage:", usage)

# --- Render headless -----------------------------------------------------
from playwright.sync_api import sync_playwright

render_ok = True
render_error = None
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto("file://" + html_path)
        page.wait_for_timeout(8000)
        page.screenshot(path=os.path.join(DEMO_DIR, "preview.png"))
        browser.close()
except Exception as e:
    render_ok = False
    render_error = repr(e)

receipt["render_ok"] = render_ok
receipt["render_error"] = render_error
with open(os.path.join(DEMO_DIR, "demo_receipt.json"), "w") as f:
    json.dump(receipt, f, indent=2)
print("render_ok:", render_ok, render_error or "")

# --- Send preview.png back to the model as a vision proof -----------------
preview_path = os.path.join(DEMO_DIR, "preview.png")
if os.path.exists(preview_path):
    with open(preview_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    vision_payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe what you see in this scene in three sentences."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }],
        "temperature": 0,
        "max_tokens": 500,
        "chat_template_kwargs": {"thinking": False},
    }
    vt0 = time.time()
    vr = requests.post(f"{BASE}/chat/completions", json=vision_payload, timeout=180)
    vr.raise_for_status()
    vresp = vr.json()
    vdt = time.time() - vt0
    vmsg = vresp["choices"][0]["message"]
    vision_receipt = {
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wall_time_s": round(vdt, 3),
        "usage": vresp.get("usage"),
        "finish_reason": vresp["choices"][0].get("finish_reason"),
        "response_text": vmsg.get("content"),
        "response_reasoning": vmsg.get("reasoning"),
    }
    with open(os.path.join(DEMO_DIR, "vision_proof.json"), "w") as f:
        json.dump(vision_receipt, f, indent=2)
    print("vision description:", vmsg.get("content"))
else:
    print("no preview.png produced; skipping vision proof call")
