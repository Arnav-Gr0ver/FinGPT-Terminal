"""
Agent — a grounded, tool-using financial analyst.

`run_agent(query)` drives a ReAct-style loop: the model is given the terminal's
data connectors as tools, decides which to call, sees the real output, and then
answers in plain language — citing the figures it actually pulled. Nothing is
invented; every number comes from a connector. This is the core difference from
a general chatbot: the answer is grounded in live, free public data and you can
see exactly which data was used.

Two entry depths share one engine:
    ask <question>       quick — a few tool calls, then answer
    research <goal>      deep  — more tool calls, more reasoning budget

The protocol is plain text (provider-agnostic — no native function-calling
required). Each turn the model returns either:
    ACTION: {"tool": "ratios", "args": {"ticker": "AAPL"}}
    ANSWER: <final plain-text answer>
"""

import io
import json
import re
import requests

from rich.console import Console as RichConsole

from src.display import console, print_error, print_warning, print_agent_step, print_agent_answer
from src.auth import require_auth, get_endpoint
from src.context import MODEL


# ── Tool registry ───────────────────────────────────────────────────────────
# name -> (signature_hint, human description). Dispatch lives in _run_tool.
TOOLS: dict[str, tuple[str, str]] = {
    "lookup":    ("query",  "Resolve a company or asset name to a ticker symbol"),
    "quote":     ("ticker", "Live price, market cap, 52w range, P/E, dividend"),
    "ratios":    ("ticker", "Valuation, profitability, growth, leverage ratios"),
    "income":    ("ticker", "Annual income statement (4 years)"),
    "balance":   ("ticker", "Annual balance sheet (4 years)"),
    "earnings":  ("ticker", "EPS history: estimate vs reported, surprise %"),
    "short":     ("ticker", "Short interest and days to cover"),
    "compare":   ("tickers","Side-by-side metrics for 2-4 tickers, space-separated"),
    "news":      ("ticker", "Recent headlines for a ticker"),
    "sentiment": ("ticker", "Bullish/bearish score from recent headlines"),
    "insider":   ("ticker", "SEC Form 4 insider buys/sells"),
    "congress":  ("ticker", "Congressional stock disclosures (optional ticker)"),
    "ftd":       ("ticker", "SEC failure-to-deliver data"),
    "rates":     ("",       "Central bank policy rates"),
    "yield":     ("",       "US Treasury yield curve + inversion signal"),
    "inflation": ("",       "US CPI, MoM and YoY"),
    "gdp":       ("",       "US real GDP growth, quarterly"),
    "vix":       ("",       "CBOE VIX equity fear gauge"),
    "fear":      ("",       "Crypto fear & greed index"),
    "top":       ("",       "Top crypto coins by market cap"),
    "dominance": ("",       "Crypto market dominance (BTC/ETH/alt)"),
    "predict":   ("topic",  "Polymarket prediction-market odds (optional topic)"),
    "portfolio": ("",       "The user's saved portfolio with live P&L"),
}


def run_agent(query: str, ctx=None, deep: bool = False):
    """Answer a natural-language question by pulling live data through the tools."""
    query = query.strip()
    if not query:
        print_error("Ask a question, e.g. ask is NVDA cheaper than AMD on forward P/E?")
        return

    endpoint = _require_endpoint()
    if not endpoint:
        return
    try:
        key = require_auth()
    except RuntimeError:
        return

    max_steps = 8 if deep else 5
    system    = _system_prompt(ctx, deep)
    messages  = [{"role": "system", "content": system},
                 {"role": "user",   "content": query}]

    for _ in range(max_steps):
        with console.status(f"  [#555555]{MODEL['label']} thinking…[/]", spinner="dots"):
            reply, usage = _chat(endpoint, key, messages)
        if reply is None:
            return  # network/auth error already reported
        _account(ctx, usage)

        action = _parse_action(reply)
        if not action:
            print_agent_answer(_parse_answer(reply))
            _print_usage(ctx)
            return

        tool, args = action
        print_agent_step(tool, args)
        observation = _run_tool(tool, args, ctx)
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"OBSERVATION ({tool}):\n{observation}"})

    # Step budget exhausted — force a final answer from what we have.
    messages.append({"role": "user", "content":
                     "You have gathered enough. Now give your ANSWER using the data above."})
    with console.status(f"  [#555555]{MODEL['label']} thinking…[/]", spinner="dots"):
        reply, usage = _chat(endpoint, key, messages)
    if reply is not None:
        _account(ctx, usage)
        print_agent_answer(_parse_answer(reply))
        _print_usage(ctx)


# ── Prompt construction ──────────────────────────────────────────────────────

def _system_prompt(ctx, deep: bool) -> str:
    tool_lines = "\n".join(
        f"  - {name}({sig}): {desc}" for name, (sig, desc) in TOOLS.items()
    )
    context_desc = ctx.summary() if ctx else "no ticker loaded"
    depth = (
        "Be thorough: gather data across several tools before concluding, and "
        "compare multiple angles (valuation, fundamentals, sentiment, macro)."
        if deep else
        "Be efficient: pull only the data you need, then answer."
    )
    return f"""You are Fin-R1, a sharp financial research analyst embedded in a terminal \
with live access to free public market data (Yahoo Finance, SEC EDGAR, FRED, \
CoinGecko).

Answer the user's question using REAL data you pull from the tools below. \
Never invent or recall numbers from memory — if you need a figure, fetch it. \
Use `lookup` to turn any company or asset name into a ticker before using \
ticker tools.

Each turn, reply with EXACTLY ONE of:
  ACTION: {{"tool": "<name>", "args": {{...}}}}   — to fetch data
  ANSWER: <your final answer>                      — when you have enough

Tools:
{tool_lines}

{depth}
Cite the specific figures you used. State clearly when data is missing or stale. \
Be direct and concise; this is research, not investment advice.

Current terminal context: {context_desc}."""


# ── Model I/O ────────────────────────────────────────────────────────────────

def _chat(endpoint: str, key: str, messages: list):
    """One non-streaming OpenAI-compatible chat completion.

    Returns (text, usage_dict) or (None, None) on error (already reported). The
    payload is standard `/v1/chat/completions` so it works against any
    OpenAI-compatible server hosting Fin-R1 (e.g. a vLLM server) unchanged.
    """
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        r = requests.post(
            endpoint,
            json={
                "model":       MODEL["name"],
                "messages":    messages,
                "max_tokens":  MODEL["max_tokens"],
                "temperature": 0.2,
                "stream":      False,
            },
            headers=headers,
            timeout=120,
        )
        r.raise_for_status()
        return _extract(r)
    except requests.exceptions.ConnectionError:
        print_error("Cannot reach the AI endpoint. Check FINGPT_ENDPOINT and your connection.")
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        hint = "Invalid API key — run login." if code in (401, 403) else \
               "Is the model id (FINGPT_MODEL) correct for your endpoint?" if code == 404 else ""
        print_error(f"AI endpoint error {code}. {hint}")
    except Exception as e:
        print_error(f"AI request failed: {e}")
    return None, None


def _extract(response):
    """Pull (text, usage) from an OpenAI-style chat-completions response."""
    ctype = response.headers.get("content-type", "")
    if "application/json" not in ctype:
        return response.text.strip(), None
    data = response.json()
    if isinstance(data, str):
        return data.strip(), None
    usage = data.get("usage")
    if "choices" in data and data["choices"]:
        msg = data["choices"][0].get("message", {})
        return (msg.get("content") or "").strip(), usage
    if "content" in data:                       # lenient fallback
        c = data["content"]
        return (c if isinstance(c, str) else str(c)).strip(), usage
    return str(data), usage


def _account(ctx, usage):
    if ctx and usage:
        ctx.record_usage(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))


def _print_usage(ctx):
    if not ctx:
        return
    from src.display import print_usage
    print_usage(ctx.stats)


# ── Protocol parsing ─────────────────────────────────────────────────────────

def _parse_action(reply: str):
    """Return (tool, args_dict) if the reply requests a tool, else None."""
    m = re.search(r"ACTION:\s*(\{.*\})", reply, re.S)
    if not m:
        return None
    blob = m.group(1)
    # Grab the first balanced-looking JSON object.
    try:
        obj = json.loads(blob)
    except Exception:
        inner = re.search(r"\{.*?\}", blob, re.S)
        if not inner:
            return None
        try:
            obj = json.loads(inner.group(0))
        except Exception:
            return None
    tool = (obj.get("tool") or "").strip()
    args = obj.get("args") or {}
    if tool not in TOOLS or not isinstance(args, dict):
        return None
    return tool, args


def _parse_answer(reply: str) -> str:
    m = re.search(r"ANSWER:\s*(.*)", reply, re.S)
    return (m.group(1) if m else reply).strip()


# ── Tool execution ───────────────────────────────────────────────────────────

def _resolve(arg: str) -> str:
    """Resolve a possibly-name argument to a ticker, falling back to the raw arg."""
    from src.data.symbols import resolve_symbol
    return (resolve_symbol(arg) or arg).upper().strip()


def _run_tool(tool: str, args: dict, ctx) -> str:
    """Execute a tool and return its text output (no Rich markup)."""
    buf     = io.StringIO()
    capture = RichConsole(file=buf, highlight=False, no_color=True, width=110)

    def out(text):
        capture.print(text)
        return buf.getvalue().strip()

    try:
        ticker = (args.get("ticker") or args.get("symbol") or "").strip()
        if ticker and ctx and tool in ("quote", "ratios", "income", "balance",
                                       "earnings", "short", "news", "sentiment",
                                       "insider", "ftd"):
            ticker = _resolve(ticker)
            ctx.set_ticker(ticker)

        if tool == "lookup":
            from src.data.symbols import search_symbols
            q = (args.get("query") or args.get("name") or args.get("ticker") or "").strip()
            hits = search_symbols(q, limit=5)
            if not hits:
                return f"No symbol found for '{q}'."
            return "\n".join(f"{h['symbol']:<10} {h['name']} ({h['type']})" for h in hits)

        if tool == "quote":
            from src.data.crypto import is_crypto, get_crypto_quote
            if is_crypto(ticker):
                return out(get_crypto_quote(ticker))
            from src.data.equities import get_quote
            return out(get_quote(ticker))
        if tool == "ratios":
            from src.data.equities import get_ratios;  return out(get_ratios(ticker))
        if tool == "income":
            from src.data.equities import get_income;   return out(get_income(ticker))
        if tool == "balance":
            from src.data.equities import get_balance;  return out(get_balance(ticker))
        if tool == "earnings":
            from src.data.equities import get_earnings; return out(get_earnings(ticker))
        if tool == "short":
            from src.data.equities import get_short_interest; return out(get_short_interest(ticker))
        if tool == "compare":
            from src.data.equities import get_comparison
            syms = args.get("tickers") or args.get("symbols") or ""
            syms = syms.split() if isinstance(syms, str) else list(syms)
            syms = [_resolve(s) for s in syms]
            return out(get_comparison(syms))
        if tool == "news":
            from src.data.news import search_news;   return out(search_news(ticker or args.get("query", "")))
        if tool == "sentiment":
            from src.data.news import get_sentiment;  return out(get_sentiment(ticker))
        if tool == "insider":
            from src.data.gov import get_insider_trades; return out(get_insider_trades(ticker))
        if tool == "congress":
            from src.data.gov import get_congress_trades; return out(get_congress_trades(ticker))
        if tool == "ftd":
            from src.data.gov import get_ftd;         return out(get_ftd(ticker))
        if tool == "rates":
            from src.data.macro import get_rates;     return out(get_rates())
        if tool == "yield":
            from src.data.macro import get_yield_curve; return out(get_yield_curve())
        if tool == "inflation":
            from src.data.macro import get_inflation; return out(get_inflation())
        if tool == "gdp":
            from src.data.macro import get_gdp;       return out(get_gdp())
        if tool == "vix":
            from src.data.alt import get_vix;         return out(get_vix())
        if tool == "fear":
            from src.data.alt import get_fear_greed;  return out(get_fear_greed())
        if tool == "top":
            from src.data.crypto import get_top_coins; return out(get_top_coins())
        if tool == "dominance":
            from src.data.crypto import get_global_dominance; return out(get_global_dominance())
        if tool == "predict":
            from src.data.alt import get_prediction_markets
            return out(get_prediction_markets(args.get("topic", "")))
        if tool == "portfolio":
            from src.commands.portfolio import pnl_text; return out(pnl_text())
        return f"Unknown tool '{tool}'."
    except Exception as e:
        return f"Error running {tool}: {e}"


# ── Endpoint guard ───────────────────────────────────────────────────────────

def _require_endpoint() -> str:
    endpoint = get_endpoint()
    if not endpoint:
        print_warning(
            "AI endpoint not configured. Set it with one of:\n"
            "    • export FINGPT_ENDPOINT=https://your-endpoint/v1/chat\n"
            "    • run 'login' and enter an endpoint URL\n"
            "  The endpoint should accept OpenAI-style chat-completion POSTs."
        )
    return endpoint

