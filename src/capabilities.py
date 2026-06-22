"""Capability map — which target kinds each function applies to.

Shared by the completer (to suggest) and the router (to *enforce*), so the menu
and what actually runs never drift. A function applies to a *kind*, and works for
every member of that kind — there are no target-less dashboards."""

_ALL = {"equity", "etf", "crypto", "index", "commodity", "fx", "macro", "country",
        "chain", "protocol", "stablecoin", "exchange", "topic"}
_PRICED = {"equity", "etf", "crypto", "index", "commodity", "fx"}
APPLIES = {
    "price": _ALL, "metrics": {"equity", "etf", "country"},
    "chart": _PRICED | {"macro", "chain", "protocol"},
    "news": _PRICED | {"country", "topic"},
    "returns": _PRICED, "stats": _PRICED, "seasonality": _PRICED,
    "compare": _PRICED, "corr": _PRICED, "spread": _PRICED,
    "financials": {"equity"}, "earnings": {"equity"}, "profile": {"equity", "country"},
    "dividends": {"equity"}, "holders": {"equity", "etf"}, "insiders": {"equity"},
    "analysts": {"equity"}, "filings": {"equity"}, "calendar": {"equity"},
    "short": {"equity"}, "options": {"equity"}, "splits": {"equity"},
    "ftd": {"equity"},
    "sentiment": {"equity", "etf", "crypto"}, "holdings": {"etf"},
    "gdp": {"country"}, "inflation": {"country"}, "trade": {"country"},
    "debt": {"country"}, "unemployment": {"country"}, "population": {"country"},
    "reserves": {"country"}, "biodiversity": {"country"},
    "tvl": {"chain"}, "fees": {"protocol"},
    "supply": {"commodity"}, "trends": _ALL, "risk": _ALL,
    "cot": {"commodity", "fx", "index"},
    "contracts": {"equity"}, "buzz": {"equity", "etf", "crypto"},
    "fda": {"equity"}, "regulations": {"equity"}, "github": {"equity", "etf", "crypto"},
    "trials": {"equity"}, "peers": {"equity", "etf"},
    "governance": {"crypto", "chain", "protocol"}, "funding": {"crypto"},
    "constituents": {"index"}, "carry": {"fx"}, "weather": {"commodity", "country"},
    "solar":   {"commodity", "country"},
    "gtrends": _ALL,
    "co2": {"country"}, "military": {"country"}, "health": {"country"},
    "market": {"country"}, "corruption": {"country"},
    "lobbying": {"equity"}, "hiring": {"equity"}, "shortvol": {"equity", "etf"},
    "cryptovol": {"crypto"}, "cotfin": {"index", "fx"},
    "litigation": {"equity"}, "campaigns": {"equity"}, "epa": {"equity"},
    "mentions": {"equity"},
    "adoption": {"equity"}, "players": {"equity"}, "imf": {"country"},
    "who": {"country"},
    "cex": {"crypto"}, "dexpairs": {"crypto", "chain", "protocol"},
    "archive": {"equity"}, "stackoverflow": {"equity", "etf", "topic"},
    "trends": _ALL, "risk": _ALL,
}
# Session utilities + the two instrument-aware globals. `holidays` resolves to a
# loaded country (every country), `bigmac` to a loaded FX pair — both consistent
# across their category. Everything here also runs with nothing loaded.
GLOBAL_APPLIES = {
    "hours": _ALL, "watch": _ALL, "export": _ALL, "convert": _ALL, "screen": _ALL,
    "find": _ALL,
    "holidays": {"country", "macro", "equity", "etf", "index", "fx", "commodity", "exchange"},
    "bigmac": {"fx"},
}

_APPLIES_ALL = {**APPLIES, **GLOBAL_APPLIES}
_GLOBAL_FUNCS = set(GLOBAL_APPLIES)


def _func_applies(name: str, loaded_kinds: set) -> bool:
    if not loaded_kinds:                       # nothing loaded → only global functions
        return name in _GLOBAL_FUNCS
    return bool(_APPLIES_ALL.get(name, _ALL) & loaded_kinds)


def functions_for(kind: str):
    """Sorted function names that apply to a single target kind."""
    out = [n for n, ks in _APPLIES_ALL.items() if kind in (ks or set())]
    return sorted(set(out))
