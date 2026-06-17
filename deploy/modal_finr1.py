"""Host Fin-R1 on Modal as a multi-tenant, key-metered API you can sell access to.

Architecture (everything runs on Modal — the customer only runs the local
terminal, which is a thin client):

    customer's terminal
        │  POST /v1/chat/completions   Authorization: Bearer sk-finr1-<their key>
        ▼
    ┌──────────────── one Modal GPU container ────────────────┐
    │  FastAPI gateway  ──► validates key against a persistent │
    │   (public URL)         key store (modal.Dict), meters    │
    │                        usage, then proxies to …          │
    │  vLLM OpenAI server on 127.0.0.1  (private, no public    │
    │   port — only the gateway can reach it)                  │
    └──────────────────────────────────────────────────────────┘

You deploy this once. The **endpoint URL is the same for every customer**; each
customer gets their own **API key** that you issue (and can revoke) with the
admin CLI at the bottom. Per-key request/token counts are recorded for billing.

    pip install modal && modal setup
    modal deploy deploy/modal_finr1.py                 # deploy the service
    modal run deploy/modal_finr1.py --action create --customer alice   # mint a key
    modal run deploy/modal_finr1.py --action list      # see usage per key
    modal run deploy/modal_finr1.py --action revoke --key sk-finr1-…   # cut off

See deploy/README.md for the full walkthrough.
"""

import subprocess
import time

import modal

APP_NAME      = "fin-r1"
MODEL_NAME    = "SUFE-AIFLM-Lab/Fin-R1"   # ~7B; ~15GB fp16
MAX_MODEL_LEN = 32768
GPU           = "A10G"                     # 24GB fits 7B fp16; use L40S/A100 for headroom
VLLM_PORT     = 8000                       # bound to localhost only — never public

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm==0.6.6",
        "huggingface_hub[hf_transfer]==0.26.2",
        "fastapi==0.115.6",
        "httpx==0.27.2",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "VLLM_DO_NOT_TRACK": "1"})
)

app = modal.App(APP_NAME, image=image)

# Persistent, multi-container stores. `api_keys`: key -> metadata + usage.
api_keys = modal.Dict.from_name("fin-r1-api-keys", create_if_missing=True)
hf_cache = modal.Volume.from_name("huggingface-cache", create_if_missing=True)


@app.cls(
    gpu=GPU,
    volumes={"/root/.cache/huggingface": hf_cache},
    scaledown_window=5 * 60,     # idle 5 min → scale to zero (pay only for use)
    timeout=10 * 60,
)
@modal.concurrent(max_inputs=32) # one GPU replica serves many in-flight requests
class FinR1Service:

    @modal.enter()
    def start_vllm(self):
        """Boot vLLM on localhost when the container starts; wait until ready."""
        import httpx
        self.proc = subprocess.Popen([
            "vllm", "serve", MODEL_NAME,
            "--host", "127.0.0.1",
            "--port", str(VLLM_PORT),
            "--served-model-name", MODEL_NAME,
            "--max-model-len", str(MAX_MODEL_LEN),
            "--gpu-memory-utilization", "0.92",
            "--enable-prefix-caching",
        ])
        health = f"http://127.0.0.1:{VLLM_PORT}/health"
        for _ in range(600):                      # up to ~20 min for first weight pull
            try:
                if httpx.get(health, timeout=2).status_code == 200:
                    return
            except Exception:
                pass
            time.sleep(2)
        raise RuntimeError("vLLM did not become ready in time")

    @modal.asgi_app()
    def gateway(self):
        from fastapi import FastAPI, Request, HTTPException
        from fastapi.responses import JSONResponse
        import httpx

        web  = FastAPI(title="Fin-R1 API")
        VLLM = f"http://127.0.0.1:{VLLM_PORT}"

        def authorize(request: Request):
            auth = request.headers.get("authorization", "")
            if not auth.lower().startswith("bearer "):
                raise HTTPException(401, "Missing API key. Send 'Authorization: Bearer <key>'.")
            key  = auth.split(" ", 1)[1].strip()
            meta = api_keys.get(key)
            if not meta or not meta.get("active", False):
                raise HTTPException(401, "Invalid or revoked API key.")
            return key, meta

        def meter(key: str, meta: dict, usage: dict):
            # Best-effort per-key accounting for billing. (Concurrent updates can
            # race; swap in a real DB if you need exact counts.)
            try:
                meta["requests"]          = meta.get("requests", 0) + 1
                meta["prompt_tokens"]     = meta.get("prompt_tokens", 0) + (usage.get("prompt_tokens") or 0)
                meta["completion_tokens"] = meta.get("completion_tokens", 0) + (usage.get("completion_tokens") or 0)
                meta["last_used"]         = time.time()
                api_keys[key]             = meta
            except Exception:
                pass

        @web.post("/v1/chat/completions")
        async def chat(request: Request):
            key, meta = authorize(request)
            body = await request.body()
            async with httpx.AsyncClient(timeout=300) as client:
                r = await client.post(
                    f"{VLLM}/v1/chat/completions",
                    content=body,
                    headers={"Content-Type": "application/json"},
                )
            try:
                data = r.json()
            except Exception:
                return JSONResponse({"error": "upstream returned non-JSON"}, status_code=502)
            if r.status_code == 200:
                meter(key, meta, data.get("usage") or {})
            return JSONResponse(data, status_code=r.status_code)

        @web.get("/v1/models")
        async def models(request: Request):
            authorize(request)
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(f"{VLLM}/v1/models")
            return JSONResponse(r.json(), status_code=r.status_code)

        @web.get("/health")
        async def health():
            return {"status": "ok"}

        return web


# ── admin: issue / revoke / list keys (run with `modal run`) ──────────────────

@app.function()
def _issue(customer: str) -> str:
    import secrets
    key = "sk-finr1-" + secrets.token_hex(24)
    api_keys[key] = {
        "customer": customer, "active": True, "created": time.time(),
        "requests": 0, "prompt_tokens": 0, "completion_tokens": 0,
    }
    return key


@app.function()
def _revoke(key: str) -> bool:
    meta = api_keys.get(key)
    if not meta:
        return False
    meta["active"] = False
    api_keys[key]  = meta
    return True


@app.function()
def _list() -> list:
    rows = []
    for k, m in api_keys.items():
        rows.append({
            "key":      k[:14] + "…",
            "customer": m.get("customer", ""),
            "active":   m.get("active", False),
            "requests": m.get("requests", 0),
            "tokens":   m.get("prompt_tokens", 0) + m.get("completion_tokens", 0),
        })
    return rows


@app.local_entrypoint()
def main(action: str = "list", customer: str = "", key: str = ""):
    """modal run deploy/modal_finr1.py --action create|revoke|list [--customer X] [--key Y]"""
    if action == "create":
        if not customer:
            print("Pass --customer <name>"); return
        new_key = _issue.remote(customer)
        print(f"\n  Issued key for '{customer}':\n    {new_key}\n")
        print("  Give the customer:")
        print(f"    FINGPT_API_KEY={new_key}")
        print("    FINGPT_ENDPOINT=<your gateway URL>/v1/chat/completions\n")
    elif action == "revoke":
        if not key:
            print("Pass --key <full key>"); return
        print("Revoked." if _revoke.remote(key) else "Key not found.")
    else:
        rows = _list.remote()
        if not rows:
            print("No keys issued yet."); return
        print(f"\n  {'KEY':<16} {'CUSTOMER':<16} {'ACTIVE':<7} {'REQS':>6} {'TOKENS':>10}")
        for r in rows:
            print(f"  {r['key']:<16} {r['customer']:<16} {str(r['active']):<7} "
                  f"{r['requests']:>6} {r['tokens']:>10}")
        print()
