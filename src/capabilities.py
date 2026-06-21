"""Capability map — which target kinds each function applies to.

Shared by the completer (to suggest) and the router (to *enforce*), so the menu
and what actually runs never drift. Country/global boards that are US-specific
are scoped out of `country` here, so e.g. `INDIA auctions` is rejected instead of
silently showing US data."""

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
    "tvl": {"chain"}, "supply": {"commodity"}, "trends": _ALL, "risk": _ALL,
    "cot": {"commodity", "fx", "index"},
    "contracts": {"equity"}, "buzz": {"equity", "etf", "crypto"},
    "fda": {"equity"}, "regulations": {"equity"}, "github": {"equity", "etf", "crypto"},
    "trials": {"equity"}, "peers": {"equity", "etf"},
    "governance": {"crypto", "chain", "protocol"}, "funding": {"crypto"},
    "constituents": {"index"}, "carry": {"fx"}, "weather": {"commodity", "country"},
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
# Functions that run with no target loaded; value = kinds they're *also* relevant
# to when something is loaded.
GLOBAL_APPLIES = {
    "hours": _ALL, "watch": _ALL, "export": _ALL, "convert": _ALL, "screen": _ALL,
    "predictions": _ALL, "ipos": {"equity", "etf"},
    "holidays": {"country", "macro", "equity", "etf", "index", "fx", "commodity", "exchange"},
    "bigmac": {"fx"},
    "yields": {"macro", "equity", "etf", "index", "fx"},
    "usdebt": {"macro"},
    "refrates": {"macro", "equity", "etf", "index", "fx"},
    "auctions": {"macro", "index", "fx"},
    "budget": {"macro"},
    "recession": {"macro", "equity", "etf", "index", "fx"},
    "stress": {"macro", "equity", "etf", "index"},
    "sectors": {"equity", "etf", "index"}, "indices": {"equity", "etf", "index"},
    "commodities": {"commodity"}, "forex": {"fx"},
    "coins": {"crypto", "chain"}, "dominance": {"crypto", "chain"},
    "fear": {"crypto", "chain"}, "protocols": {"crypto", "chain"},
    "stablecoins": {"crypto", "chain"},
    "trending": {"crypto", "chain"}, "onchain": {"crypto", "chain"},
    "pools": {"crypto", "chain"}, "dexs": {"crypto", "chain"},
    "fees": {"crypto", "chain", "protocol"}, "chains": {"crypto", "chain"},
    "hacks": {"crypto", "chain"}, "treasuries": {"crypto", "chain"},
    "congress": {"equity", "etf", "index"},
    "disasters": {"macro", "equity", "etf", "index", "commodity"},
    "politics": {"macro", "equity", "etf", "index", "fx"},
    "forecasts": _ALL,
    "credit": {"macro", "equity", "etf", "index"},
    "housing": {"macro"}, "soma": {"macro"},
    "hazards": {"macro", "equity", "etf", "index", "commodity"},
    "flights": {"macro", "equity", "etf", "index"},
    "exchanges": {"crypto", "chain"}, "categories": {"crypto", "chain"},
    "industrial": {"macro", "equity", "etf", "index", "commodity"},
    "mining": {"macro", "commodity", "equity", "etf", "index"},
    "permits": {"macro", "equity", "etf"},
    "claims": {"macro", "equity", "etf", "index"},
    "confidence": {"macro", "equity", "etf", "index"},
    "freight": {"macro", "equity", "etf", "commodity", "index"},
    "shortages": {"equity", "etf"},
    "water": {"commodity", "macro"},
    "airports": {"macro", "equity", "etf", "index"},
    "alerts": {"macro", "commodity"},
    "travel": {"macro", "equity", "etf", "index"},
    "ecb": {"macro", "fx", "index"},
    "spaceweather": {"macro", "equity", "etf", "index", "commodity"},
    "hurricanes": {"macro", "commodity", "equity", "etf", "index"},
    "tides": {"commodity", "macro"},
    "gridcarbon": {"commodity", "macro"},
    "eurostat": {"macro", "fx", "index"},
    "volcanoes": {"macro", "commodity", "equity", "etf", "index"},
    "buoys": {"commodity", "macro"},
    "neo": {"macro", "equity", "etf", "index"},
    "citypermits": {"macro", "equity", "etf"},
    "disease": {"macro", "equity", "etf"},
    "medicare": {"macro", "equity", "etf"},
    "sports": {"equity", "etf"},
    "btcchain": {"crypto", "chain"}, "ethsupply": {"crypto", "chain"},
    "kfutures": {"crypto", "chain"},
}

# ── Standalone boards ─────────────────────────────────────────────────────────
# Market/economy dashboards that take NO target. They don't act on a loaded
# instrument, so they never appear as an instrument function — every category's
# function set stays consistent (a function works for *all* members of its kind,
# or it's a standalone board here). Reached only with nothing loaded.
BOARDS = {
    # US macro / rates / fixed income
    "yields", "usdebt", "refrates", "auctions", "budget", "recession", "credit",
    "housing", "soma", "stress", "ipos", "industrial", "mining", "permits",
    "claims", "confidence", "freight",
    # real economy / weather / science
    "shortages", "water", "airports", "alerts", "travel", "spaceweather",
    "hurricanes", "tides", "gridcarbon", "volcanoes", "buoys", "neo",
    "citypermits", "disease", "medicare", "sports", "ecb", "eurostat",
    "congress", "disasters", "politics", "hazards", "flights",
    # market boards
    "sectors", "indices", "commodities", "forex",
    # crypto boards
    "fear", "dominance", "coins", "trending", "onchain", "pools", "dexs",
    "fees", "chains", "hacks", "treasuries", "exchanges", "categories",
    "btcchain", "ethsupply", "kfutures", "protocols", "stablecoins",
    # prediction-market boards
    "predictions", "forecasts",
}
for _b in BOARDS:
    GLOBAL_APPLIES[_b] = set()          # standalone-only: never an instrument function

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
