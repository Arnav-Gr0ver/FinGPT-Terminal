"""Grammar-aware completion — suggests the right token *type* for where you are.

Position in the chain determines what's offered: a subject at the start or after
`vs`; a range after `chart`; a screen name after `screen`; verbs (and subject
switches) after a subject. Arrow keys move the menu, Tab accepts.
"""

from prompt_toolkit.completion import Completer, Completion

from src.router import VERBS, CONNECTORS, EACH, SETV, GLOBAL, ARG_VERBS
from src.data import symbol_index

RANGES = ["5d", "1mo", "3mo", "6mo", "ytd", "1y", "2y", "5y", "10y", "max"]

# System commands use a leading slash.
SYSTEM = [
    ("/ask",   'Fin-R1 — ask "question"'),
    ("/help",  "all commands"),
    ("/clear", "clear screen"),
    ("/login", "save Fin-R1 key/endpoint"),
    ("/exit",  "quit"),
]

# One-line meta shown beside each verb in the menu.
VERB_META = {
    "price": "quote / latest", "chart": "price over a range", "financials": "filed fundamentals",
    "earnings": "beat/miss + next", "profile": "what it does", "dividends": "payout history",
    "holders": "ownership", "insiders": "SEC Form 4", "analysts": "targets",
    "filings": "10-K/10-Q/8-K", "news": "headlines", "calendar": "catalysts ahead",
    "compare": "side-by-side", "returns": "trailing returns", "stats": "vol/beta/drawdown",
    "corr": "correlation", "spread": "ratio over time", "seasonality": "monthly pattern",
    "holdings": "ETF constituents", "gdp": "country GDP", "inflation": "country CPI",
    "trade": "exports/imports", "debt": "govt debt", "tvl": "chain TVL", "supply": "inventories",
    "trends": "search/attention", "risk": "news tone + quakes",
    "screen": "find tickers", "watch": "watchlist", "hours": "market hours",
    "export": "session → md", "convert": "currency",
    "yields": "Treasury curve", "fear": "crypto fear & greed",
    "dominance": "crypto dominance", "coins": "top crypto",
    "short": "short interest", "options": "option chain",
    "sentiment": "news sentiment", "sectors": "sector performance",
    "splits": "split history", "unemployment": "country jobless",
    "population": "country population", "indices": "world indices",
    "commodities": "commodity board", "forex": "FX board",
    "protocols": "top DeFi protocols", "stablecoins": "stablecoin caps",
}

# Which target kinds each function is relevant for (used to filter suggestions).
_ALL = {"equity", "etf", "crypto", "index", "commodity", "fx", "macro", "country", "chain"}
_PRICED = {"equity", "etf", "crypto", "index", "commodity", "fx"}
APPLIES = {
    "price": _ALL, "chart": _PRICED | {"macro", "chain"}, "news": _PRICED | {"country"},
    "returns": _PRICED, "stats": _PRICED, "seasonality": _PRICED,
    "compare": _PRICED, "corr": _PRICED, "spread": _PRICED,
    "financials": {"equity"}, "earnings": {"equity"}, "profile": {"equity"},
    "dividends": {"equity"}, "holders": {"equity", "etf"}, "insiders": {"equity"},
    "analysts": {"equity"}, "filings": {"equity"}, "calendar": {"equity"},
    "short": {"equity"}, "options": {"equity"}, "splits": {"equity"},
    "sentiment": {"equity", "etf", "crypto"}, "holdings": {"etf"},
    "gdp": {"country"}, "inflation": {"country"}, "trade": {"country"},
    "debt": {"country"}, "unemployment": {"country"}, "population": {"country"},
    "tvl": {"chain"}, "supply": {"commodity"}, "trends": _ALL, "risk": _ALL,
}
# Functions that run with no target loaded; value = kinds they're *also* relevant
# to when something is loaded.
GLOBAL_APPLIES = {
    "hours": _ALL, "watch": _ALL, "export": _ALL, "convert": _ALL, "screen": _ALL,
    "yields": {"macro", "equity", "etf", "index", "fx"},
    "sectors": {"equity", "etf", "index"}, "indices": {"equity", "etf", "index"},
    "commodities": {"commodity"}, "forex": {"fx"},
    "coins": {"crypto", "chain"}, "dominance": {"crypto", "chain"},
    "fear": {"crypto", "chain"}, "protocols": {"crypto", "chain"},
    "stablecoins": {"crypto", "chain"},
}
_APPLIES_ALL = {**APPLIES, **GLOBAL_APPLIES}
_GLOBAL_FUNCS = set(GLOBAL_APPLIES)


def _func_applies(name: str, loaded_kinds: set) -> bool:
    if not loaded_kinds:                       # nothing loaded → only global functions
        return name in _GLOBAL_FUNCS
    return bool(_APPLIES_ALL.get(name, _ALL) & loaded_kinds)


def _category(text: str) -> str:
    from src.context import ctx
    parts = text.split()
    ends_space = (text == "") or text[-1].isspace()
    prior = parts if ends_space else parts[:-1]
    if not prior:
        # First token: load a TARGET — but if one's already loaded, you'll more
        # likely run a FUNCTION (or type a new ticker to switch), so rank those first.
        return "verb" if ctx.loaded else "start"
    last = prior[-1].lower()
    if last == "chart":
        return "range"
    if last == "screen":
        return "screen"
    if last in CONNECTORS:
        return "subject"
    if last == "convert":
        return "none"
    return "verb"


def _alias_subjects(prefix: str):
    from src.data.macro import MACRO_SERIES
    from src.verbs import SPECIAL_SUBJECTS
    from src.data.worldbank import COUNTRIES
    from src.data.defillama import CHAINS
    p = prefix.upper()
    out = []
    for k in MACRO_SERIES:
        if k.startswith(p): out.append((k, "macro"))
    for k in SPECIAL_SUBJECTS:
        if k.startswith(p): out.append((k, SPECIAL_SUBJECTS[k][2]))
    for k in COUNTRIES:
        if k.startswith(p): out.append((k, "country"))
    for k in CHAINS:
        if k.startswith(p): out.append((k, "chain"))
    seen, uniq = set(), []
    for sym, kind in out:
        if sym not in seen:
            seen.add(sym); uniq.append((sym, kind))
    return uniq[:6]


class GrammarCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        ends_space = (text == "") or text[-1].isspace()
        parts = text.split()
        word = "" if ends_space else (parts[-1] if parts else "")
        start = -len(word)
        cat = _category(text)
        wl = word.lower()

        def comp(t, meta):
            # No per-item colours (the menu style handles contrast); the meta
            # text on the right tells you what kind of token it is.
            return Completion(t, start_position=start, display=t, display_meta=meta)

        # Slash → system commands, anywhere.
        if word.startswith("/"):
            for cmd, meta in SYSTEM:
                if cmd.startswith(wl):
                    yield comp(cmd, meta)
            return

        if cat == "range":
            for r in RANGES:
                if r.startswith(wl):
                    yield comp(r, "range")
            return
        if cat == "screen":
            from src.data.screener import SCREENS
            for k, (_id, desc) in SCREENS.items():
                if k.startswith(wl):
                    yield comp(k, desc)
            return
        if cat == "none":
            return

        def subjects():
            for sym, kind in _alias_subjects(word):
                yield comp(sym, kind)
            if word:
                for sym, name in symbol_index.search(word, limit=8):
                    yield comp(sym, name[:34])

        def verbs_():
            from src.context import ctx
            loaded_kinds = {s.kind for s in ctx.subjects}
            for v in sorted(VERBS):
                if v.startswith(wl) and _func_applies(v, loaded_kinds):
                    yield comp(v, VERB_META.get(v, "function"))
            for c in ("vs", "&"):
                if c.startswith(wl):
                    yield comp(c, "add a target")

        # Order by what's most likely next: subjects when loading, verbs after one.
        if cat == "subject":
            yield from subjects()
        elif cat == "start":
            yield from subjects(); yield from verbs_()
        else:  # "verb" — after a subject; a verb is most likely, then a switch
            yield from verbs_(); yield from subjects()


_TB_SPECS = {
    "start":   ("TARGET",   "NVDA · CPI · US · BTC · SPX · ETHEREUM   — or a function"),
    "subject": ("TARGET",   "another name to add to the set (after vs)"),
    "range":   ("RANGE",    "5d · 1mo · 3mo · 6mo · ytd · 1y · 2y · 5y · 10y · max"),
    "screen":  ("SCREEN",   "gainers · losers · actives · value · tech · growth"),
    "verb":    ("FUNCTION", "price · chart · compare · returns · financials …   or  vs <target>"),
    "none":    ("ARGS",     "100 USD EUR"),
}


def toolbar_fragments(text: str):
    """Styled bottom-bar fragments: the loaded set, what's expected next, examples."""
    from src.context import ctx
    label, eg = _TB_SPECS.get(_category(text), ("", ""))
    frags = [("class:tb.pad", " ")]
    if ctx.loaded:
        frags.append(("class:tb.loaded", f" {ctx.prompt_label} "))
        frags.append(("class:tb.pad", "  "))
    frags.append(("class:tb.key", f" next ▸ {label} "))
    frags.append(("class:tb.eg", f"  {eg} "))
    return frags
