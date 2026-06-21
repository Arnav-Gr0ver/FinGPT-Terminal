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
    "price": "quote / latest", "metrics": "all fundamental fields",
    "chart": "price over a range", "financials": "filed fundamentals",
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
    "ftd": "fails-to-deliver (SEC)", "cot": "CFTC positioning",
    "contracts": "federal awards", "buzz": "Hacker News",
    "fda": "FDA recalls", "regulations": "Federal Register", "github": "dev activity",
    "sentiment": "news sentiment", "sectors": "sector performance",
    "splits": "split history", "unemployment": "country jobless",
    "population": "country population", "reserves": "FX reserves",
    "indices": "world indices",
    "commodities": "commodity board", "forex": "FX board",
    "protocols": "top DeFi protocols", "stablecoins": "stablecoin caps",
    "usdebt": "US national debt", "predictions": "Polymarket odds",
    "refrates": "SOFR / fed funds", "stress": "OFR stress index",
    "onchain": "Bitcoin network", "trending": "trending coins",
    "pools": "DeFi yield pools", "dexs": "DEX volumes",
    "fees": "protocol fees", "chains": "chains by TVL",
    "auctions": "Treasury auctions", "budget": "federal deficit",
    "hacks": "crypto exploits", "ipos": "S-1 pipeline",
    "holidays": "market holidays", "bigmac": "Big Mac index",
    "trials": "clinical trials", "peers": "co-watched names",
    "governance": "DAO votes", "funding": "perp funding",
    "constituents": "index members", "carry": "rate differential",
    "weather": "growing-region wx", "gtrends": "Google Trends",
    "recession": "yield-curve signal",
    "co2": "emissions", "military": "defense spend",
    "health": "life expectancy", "market": "benchmark index",
    "corruption": "governance index", "lobbying": "lobby spend (LDA)",
    "hiring": "open job roles", "shortvol": "FINRA short %",
    "cryptovol": "DVOL implied vol", "cotfin": "TFF positioning",
    "treasuries": "corp BTC/ETH", "congress": "congress trades",
    "disasters": "FEMA declarations", "politics": "PredictIt odds",
    "forecasts": "Manifold odds",
    "litigation": "court cases", "campaigns": "FEC donations",
    "epa": "EPA compliance", "mentions": "filing mentions", "adoption": "pkg downloads",
    "players": "Steam players", "imf": "IMF outlook",
    "credit": "bond spreads", "housing": "Case-Shiller",
    "soma": "Fed balance sheet", "hazards": "natural hazards",
    "flights": "air traffic", "exchanges": "crypto exchanges",
    "categories": "crypto sectors",
    "industrial": "factory output", "mining": "mining/extraction",
    "permits": "construction", "claims": "jobless claims",
    "confidence": "consumer demand", "freight": "freight/logistics",
    "shortages": "FDA drug shortages", "water": "river flows",
    "airports": "FAA delays", "alerts": "weather alerts",
    "travel": "TSA throughput",
    "cex": "cross-exchange price", "dexpairs": "DEX pairs",
    "who": "WHO health", "ecb": "ECB rates/FX",
    "spaceweather": "geomagnetic storm", "hurricanes": "tropical cyclones",
    "tides": "port water levels", "gridcarbon": "UK grid carbon",
    "archive": "Wayback snapshots", "stackoverflow": "dev mindshare",
    "eurostat": "euro-area stats", "volcanoes": "volcano alerts",
    "buoys": "offshore buoys", "neo": "near-earth objects",
    "biodiversity": "GBIF records", "citypermits": "city permits",
    "disease": "CDC surveillance", "medicare": "CMS Medicare",
    "sports": "sports leagues", "btcchain": "BTC explorers",
    "ethsupply": "ETH issuance", "kfutures": "Kraken futures OI",
}

# Which target kinds each function is relevant for (used to filter suggestions).
from src.capabilities import (_ALL, _PRICED, APPLIES, GLOBAL_APPLIES,
                              _APPLIES_ALL, _GLOBAL_FUNCS, _func_applies)


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
    if last in ("convert", "predictions", "forecasts"):
        return "none"
    return "verb"


def _alias_subjects(prefix: str):
    from src.data.macro import MACRO_SERIES
    from src.verbs import SPECIAL_SUBJECTS
    from src.data.worldbank import COUNTRIES
    from src.data.defillama import CHAINS, PROTOCOLS, STABLECOINS
    from src.data.calendars import EXCHANGES
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
    for k in PROTOCOLS:
        if k.startswith(p): out.append((k, "protocol"))
    for k in STABLECOINS:
        if k.startswith(p): out.append((k, "stablecoin"))
    for k in EXCHANGES:
        if k.startswith(p): out.append((k, "exchange"))
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
            from src.data.metrics import EQUITY_METRICS, COUNTRY_METRICS, metric_aliases
            loaded_kinds = {s.kind for s in ctx.subjects}
            for v in sorted(VERBS):
                if v.startswith(wl) and _func_applies(v, loaded_kinds):
                    yield comp(v, VERB_META.get(v, "function"))
            # Deep metric fields for the loaded target (only once you've typed a
            # couple of letters, so the menu isn't flooded).
            if wl and len(wl) >= 2:
                reg = EQUITY_METRICS if loaded_kinds & {"equity", "etf"} else (
                    COUNTRY_METRICS if "country" in loaded_kinds else {})
                for alias in sorted(reg):
                    if alias.startswith(wl) and alias not in VERBS:
                        yield comp(alias, reg[alias][1])
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

# Priority order for the toolbar hint — most useful first, so the handful we show
# for a given target are the ones you'd actually reach for.
_VERB_ORDER = [
    "price", "metrics", "chart", "financials", "earnings", "compare", "returns", "stats", "corr",
    "spread", "profile", "dividends", "holders", "analysts", "insiders", "filings",
    "calendar", "short", "options", "ftd", "cot", "cotfin", "contracts", "fda",
    "regulations", "github", "trials", "peers", "lobbying", "hiring", "shortvol",
    "litigation", "campaigns", "epa", "mentions", "adoption", "players",
    "buzz", "sentiment", "splits", "seasonality", "holdings", "news",
    "archive", "stackoverflow",
    "governance", "funding", "cex", "dexpairs", "cryptovol", "constituents",
    "gdp", "inflation", "trade", "debt", "unemployment", "population", "reserves",
    "co2", "military", "health", "corruption", "imf", "who", "market",
    "usdebt", "budget", "recession", "credit", "housing", "soma", "carry",
    "industrial", "mining", "permits", "claims", "confidence", "freight",
    "tvl", "supply", "trends", "gtrends", "risk",
    "yields", "refrates", "auctions", "stress", "ipos", "bigmac", "holidays",
    "weather", "water", "alerts", "airports", "travel", "shortages",
    "spaceweather", "hurricanes", "tides", "gridcarbon", "ecb", "eurostat",
    "volcanoes", "buoys", "neo", "biodiversity", "citypermits", "disease", "medicare", "sports",
    "sectors", "indices", "commodities", "forex",
    "coins", "trending", "onchain", "pools", "dexs", "fees", "chains", "hacks",
    "treasuries", "exchanges", "categories", "btcchain", "ethsupply", "kfutures",
    "dominance", "fear", "protocols", "stablecoins",
    "congress", "disasters", "politics", "hazards", "flights", "predictions", "forecasts",
    "screen", "watch", "convert", "hours", "export",
]


def _verb_hint(loaded_kinds: set) -> str:
    """The functions that apply to what's loaded, in priority order — this is what
    makes the bar target-aware (no `financials` on a country, no `gdp` on a stock)."""
    applicable = [v for v in _VERB_ORDER if _func_applies(v, loaded_kinds)]
    shown = applicable[:6]
    tail = " …" if len(applicable) > len(shown) else ""
    return " · ".join(shown) + tail + "   or  vs <target>"


def toolbar_fragments(text: str):
    """Styled bottom-bar fragments: the loaded set, what's expected next, examples."""
    from src.context import ctx
    cat = _category(text)
    label, eg = _TB_SPECS.get(cat, ("", ""))
    # When a function is expected and a target is loaded, tailor the examples to
    # the functions that actually apply to that target.
    if cat == "verb" and ctx.loaded:
        eg = _verb_hint({s.kind for s in ctx.subjects})
    frags = [("class:tb.pad", " ")]
    if ctx.loaded:
        frags.append(("class:tb.loaded", f" {ctx.prompt_label} "))
        frags.append(("class:tb.pad", "  "))
    frags.append(("class:tb.key", f" next ▸ {label} "))
    frags.append(("class:tb.eg", f"  {eg} "))
    return frags
