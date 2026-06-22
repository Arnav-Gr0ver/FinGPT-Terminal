"""Context — the loaded subject.

The grammar is subject-then-verbs: you load one subject (an equity ticker, a
crypto symbol, or a FRED macro series) and chain verbs against it. The prompt
shows what's loaded; verbs run against it until you load something else.
"""

from dataclasses import dataclass, field
from typing import Optional

_KIND_TAG = {"macro": "FRED", "crypto": "crypto", "index": "index",
             "commodity": "commodity", "fx": "FX", "country": "country",
             "etf": "ETF", "chain": "chain", "protocol": "DeFi protocol",
             "stablecoin": "stablecoin", "exchange": "exchange", "topic": "topic"}

# Kinds that have price/chart history through a yfinance-style symbol.
_PRICED = {"equity", "etf", "crypto", "index", "commodity", "fx"}


@dataclass
class Subject:
    """A loaded noun the verbs act on."""
    symbol: str                 # prompt label, e.g. "NVDA" or "CPI"
    kind: str = "equity"        # equity|etf|crypto|macro|index|commodity|fx|country|chain
    name: str = ""              # "NVIDIA Corp" / "Consumer Price Index"
    exchange: str = ""          # "NASDAQ" (equities only)
    fred_id: str = ""           # FRED series id (macro only)
    yf: str = ""                # yfinance symbol (markets/crypto/fx)
    ref: str = ""               # extra handle: country code, lat,lon, chain slug…

    def __post_init__(self):
        if not self.yf and self.kind in _PRICED:
            self.yf = self.symbol

    @property
    def is_company(self) -> bool:
        """Has SEC/issuer fundamentals (financials/earnings/filings/etc.)."""
        return self.kind == "equity"

    @property
    def is_priced(self) -> bool:
        """Has price/chart history."""
        return self.kind in _PRICED

    def confirm_line(self) -> str:
        bits = [self.symbol, self.name]
        tag  = _KIND_TAG.get(self.kind) if self.kind != "equity" else self.exchange
        if tag:
            bits.append(tag)
        return " · ".join(b for b in bits if b)


@dataclass
class Context:
    # The active subject SET. One subject is the common case; `vs`/`&`/`,`
    # compose several (e.g. NVDA vs AMD), and set-aware verbs (compare, chart,
    # corr, spread, returns) act on all of them.
    subjects: list = field(default_factory=list)
    # In-memory transcript of what the terminal showed THIS session. Never
    # written to disk; gone when the process exits. `export` writes it to md.
    history: list = field(default_factory=list)
    _MAX_ENTRIES = 80
    _MAX_CHARS   = 1600

    @property
    def subject(self) -> Optional[Subject]:
        return self.subjects[0] if self.subjects else None

    # ── subject management ────────────────────────────────────────────────────
    def set_subject(self, subject: Subject):
        if not self.subject or self.subject.symbol != subject.symbol:
            self.stats.subjects_loaded += 1
        self.subjects = [subject]

    def set_subjects(self, subjects: list):
        self.subjects = list(subjects)

    def add_subject(self, subject: Subject):
        if subject.symbol not in [s.symbol for s in self.subjects]:
            self.stats.subjects_loaded += 1
            self.subjects.append(subject)

    # ── session transcript (in-memory only) ──────────────────────────────────
    def remember(self, label: str, text: str):
        """Record one verb's output for possible reuse as `ask` context."""
        text = (text or "").strip()
        if not text:
            return
        self.history.append({"label": label, "text": text})
        if len(self.history) > self._MAX_ENTRIES:
            self.history = self.history[-self._MAX_ENTRIES:]

    def clear(self):
        self.subjects = []

    @property
    def loaded(self) -> bool:
        return bool(self.subjects)

    @property
    def prompt_label(self) -> Optional[str]:
        if not self.subjects:
            return None
        return "·".join(s.symbol for s in self.subjects)

ctx = Context()
