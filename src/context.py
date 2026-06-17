"""Context — the loaded subject.

The grammar is subject-then-verbs: you load one subject (an equity ticker, a
crypto symbol, or a FRED macro series) and chain verbs against it. The prompt
shows what's loaded; verbs run against it until you load something else.

There is no user-facing model picker. A single model backs the `ask` verb and
scales its own effort, so users never reason about which model to choose.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

# The Fin-R1 model (SUFE-AIFLM-Lab/Fin-R1) backs the `ai` verb. The served model
# id and context window are overridable via env so you can point at your own
# deployment without code edits.
MODEL = {
    "name":       os.environ.get("FINGPT_MODEL", "SUFE-AIFLM-Lab/Fin-R1"),
    "label":      "Fin-R1",
    "max_tokens": 4000,
    "context":    int(os.environ.get("FINGPT_CONTEXT", "32768")),
}

_KIND_TAG = {"macro": "FRED", "crypto": "crypto", "index": "index",
             "commodity": "commodity", "fx": "FX"}


@dataclass
class Subject:
    """A loaded noun the verbs act on."""
    symbol: str                 # prompt label, e.g. "NVDA" or "CPI"
    kind: str = "equity"        # equity | crypto | macro | index | commodity | fx
    name: str = ""              # "NVIDIA Corp" / "Consumer Price Index"
    exchange: str = ""          # "NASDAQ" (equities only)
    fred_id: str = ""           # FRED series id (macro only)
    yf: str = ""                # yfinance symbol (markets/crypto/fx)

    def __post_init__(self):
        if not self.yf and self.kind != "macro":
            self.yf = self.symbol

    @property
    def is_company(self) -> bool:
        """Has fundamentals (financials/earnings/filings/calendar apply)."""
        return self.kind == "equity"

    def confirm_line(self) -> str:
        bits = [self.symbol, self.name]
        tag  = _KIND_TAG.get(self.kind) if self.kind != "equity" else self.exchange
        if tag:
            bits.append(tag)
        return " · ".join(b for b in bits if b)


@dataclass
class SessionStats:
    """Running counters surfaced in the status line."""
    subjects_loaded: int = 0
    ai_calls: int = 0
    last_prompt_tokens: int = 0
    last_completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def last_total(self) -> int:
        return self.last_prompt_tokens + self.last_completion_tokens

    @property
    def context_pct(self) -> float:
        return min(100.0, self.last_total / MODEL["context"] * 100) if MODEL["context"] else 0.0


@dataclass
class Context:
    subject: Optional[Subject] = None
    stats: "SessionStats" = field(default_factory=lambda: SessionStats())
    # In-memory transcript of what the terminal showed THIS session. Never
    # written to disk; gone when the process exits. `ask` can feed some or all
    # of it to Fin-R1 as context (the user chooses how much).
    history: list = field(default_factory=list)
    _MAX_ENTRIES = 80
    _MAX_CHARS   = 1600

    # ── subject management ────────────────────────────────────────────────────
    def set_subject(self, subject: Subject):
        if not self.subject or self.subject.symbol != subject.symbol:
            self.stats.subjects_loaded += 1
        self.subject = subject

    def record_usage(self, prompt_tokens: int, completion_tokens: int):
        self.stats.ai_calls += 1
        self.stats.last_prompt_tokens = prompt_tokens or 0
        self.stats.last_completion_tokens = completion_tokens or 0
        self.stats.total_tokens += (prompt_tokens or 0) + (completion_tokens or 0)

    # ── session transcript (in-memory only) ──────────────────────────────────
    def remember(self, label: str, text: str):
        """Record one verb's output for possible reuse as `ask` context."""
        text = (text or "").strip()
        if not text:
            return
        self.history.append({"label": label, "text": text})
        if len(self.history) > self._MAX_ENTRIES:
            self.history = self.history[-self._MAX_ENTRIES:]

    def history_context(self, n) -> str:
        """Format the last `n` transcript entries as a context block. `n` may be
        an int, the string 'all', or None (→ most recent only)."""
        if not self.history:
            return ""
        if n in (None, "", "1"):
            items = self.history[-1:]
        elif n == "all":
            items = self.history
        else:
            try:
                k = max(0, int(n))
            except (TypeError, ValueError):
                k = 1
            items = self.history[-k:] if k else []
        if not items:
            return ""
        blocks = []
        for e in items:
            body = e["text"]
            if len(body) > self._MAX_CHARS:
                body = body[: self._MAX_CHARS] + " …(truncated)"
            blocks.append(f"[{e['label']}]\n{body}")
        return ("SESSION CONTEXT — data the terminal already showed this session "
                "(use it; cite it):\n\n" + "\n\n".join(blocks))

    def clear(self):
        self.subject = None

    @property
    def loaded(self) -> bool:
        return self.subject is not None

    @property
    def prompt_label(self) -> Optional[str]:
        return self.subject.symbol if self.subject else None

    # ── backward-compatible helpers used by the AI agent ─────────────────────
    def set_ticker(self, ticker: str):
        sym = ticker.upper().strip()
        if not self.subject or self.subject.symbol != sym:
            self.subject = Subject(symbol=sym, kind="equity")

    def get_ticker(self) -> Optional[str]:
        return self.subject.symbol if self.subject else None

    def summary(self) -> str:
        if not self.subject:
            return "no subject loaded"
        s = self.subject
        return f"loaded subject: {s.symbol} ({s.kind}) — {s.name or 'unknown'}"


ctx = Context()
