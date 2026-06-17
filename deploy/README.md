# Hosting Fin-R1 on Modal and selling access

The `ask` verb talks to **Fin-R1** (`SUFE-AIFLM-Lab/Fin-R1`) over an OpenAI
`/v1/chat/completions` endpoint. This directory hosts the model entirely on
[Modal](https://modal.com) as a **multi-tenant API you control**: you deploy one
endpoint, then mint an API key per customer. The customer runs only the local
terminal (a thin client) — all inference, auth, and usage metering happen on your
Modal deployment.

```
customer's terminal ──Bearer sk-finr1-<their key>──►  your Modal gateway (public URL)
                                                         │  validate key + meter usage
                                                         ▼
                                                       vLLM on 127.0.0.1  (private)
```

[`modal_finr1.py`](./modal_finr1.py) is the whole service: a FastAPI **gateway**
that checks each key against a persistent store (`modal.Dict`) and proxies valid
requests to a private vLLM server in the same GPU container. vLLM is bound to
localhost, so customers can only reach it *through* the gateway — they can't
bypass your auth.

## One-time: deploy the service (you, the owner)

```bash
pip install modal
modal setup                     # browser auth, one-time
modal deploy deploy/modal_finr1.py
```

Modal prints a public URL for the gateway, e.g.:

```
https://your-workspace--fin-r1-finr1service-gateway.modal.run
```

Your customer-facing **endpoint** is that URL **+ `/v1/chat/completions`**. It's
the same for every customer; only their key differs. First request cold-starts
the GPU and downloads weights (~1–2 min, then cached on a Volume); it scales to
zero ~5 min after the last request, so you pay only for use.

## Selling access: issue and manage keys

Keys live in a persistent `modal.Dict`; manage them with `modal run`:

```bash
# mint a key for a customer
modal run deploy/modal_finr1.py --action create --customer alice
#   → Issued key for 'alice':  sk-finr1-9f3c…c1ab

# see every key with its request/token usage (for billing)
modal run deploy/modal_finr1.py --action list

# revoke a key (immediate — the gateway rejects it on the next call)
modal run deploy/modal_finr1.py --action revoke --key sk-finr1-9f3c…c1ab
```

What you hand a paying customer is just two values:

```
FINGPT_ENDPOINT=https://your-workspace--fin-r1-finr1service-gateway.modal.run/v1/chat/completions
FINGPT_API_KEY=sk-finr1-9f3c…c1ab
```

## Customer setup (in their terminal)

They set the two env vars, or run `login` and paste them:

```bash
export FINGPT_ENDPOINT="https://your-workspace--fin-r1-finr1service-gateway.modal.run/v1/chat/completions"
export FINGPT_API_KEY="sk-finr1-9f3c…c1ab"
```

Then:

```
<FinGPT Terminal> NVDA
<FinGPT Terminal NVDA> financials ask "is the margin dip structural?"
```

If their key is revoked or wrong, `ask` shows an auth error and the rest of the
terminal keeps working (it never needs the model).

## Verify directly (optional)

```bash
curl "$FINGPT_ENDPOINT" \
  -H "Authorization: Bearer $FINGPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"SUFE-AIFLM-Lab/Fin-R1",
       "messages":[{"role":"user","content":"Say hello in one word."}],
       "max_tokens":16}'
```

A revoked/missing key returns `401`; a valid key returns the completion and
increments that key's usage counters.

## Notes & tuning

- **Billing:** `--action list` shows per-key `requests` and `tokens`. Counters
  are best-effort (concurrent requests can race); for exact billing, back the
  gateway with a real database instead of `modal.Dict`.
- **GPU:** `A10G` (24 GB) fits Fin-R1 in fp16. Bump `GPU` to `L40S`/`A100` in
  `modal_finr1.py` for more concurrency/headroom.
- **Context window:** deploy uses `--max-model-len 32768`. If you change it, tell
  customers to set `FINGPT_CONTEXT` to match (keeps their usage meter accurate).
- **Model id:** customers' `FINGPT_MODEL` defaults to `SUFE-AIFLM-Lab/Fin-R1` and
  must match `--served-model-name`.
- **Streaming:** the terminal uses non-streaming requests; the gateway proxies
  those. (Add a streaming branch if you expose `stream:true` to other clients.)
- **Modal API:** targets a recent Modal (`@app.cls`, `@modal.enter`,
  `@modal.asgi_app`, `@modal.concurrent`, `modal.Dict`). Decorator names have
  changed across versions — `pip install -U modal` and check the docs if a
  decorator errors.
