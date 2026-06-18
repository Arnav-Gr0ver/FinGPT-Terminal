"""Verbs — the functions you run against a loaded subject.

The grammar is subject-then-verbs. A subject (equity, crypto, or FRED macro
series) is loaded into the context; each verb here answers one specific question
about it. Verbs compose left to right — the router walks a chained line like
`price compare AMD chart 1y` and calls these in order, mutating the active
subject set as it goes (so `compare` injects a peer into everything downstream).
"""

import json
from pathlib import Path

from rich.markup import escape
from rich.text import Text
from src.context import ctx, Subject
from src.display import console, print_panel as _panel, print_error, C

MUTE  = "#555555"
WHITE = "#e8e8e8"
GREEN = "#00c853"
RED   = "#ff1744"

WATCH_FILE = Path.home() / ".fingpt" / "watch.json"

# User range token → canonical (which is also the yfinance period and the macro
# key). `chart` requires one of these; range is meaning, not decoration.
RANGE_ALIASES = {
    "1d": "1d",
    "5d": "5d",   "1w": "5d",   "1wk": "5d",
    "1mo": "1mo", "1m": "1mo",  "30d": "1mo",
    "3mo": "3mo", "3m": "3mo",
    "6mo": "6mo", "6m": "6mo",
    "ytd": "ytd",
    "1y": "1y",   "12m": "1y",  "1yr": "1y",
    "2y": "2y",   "2yr": "2y",
    "5y": "5y",
    "10y": "10y",
    "max": "max", "all": "max",
}

_RANGE_LABEL = {
    "1d": "1 day", "5d": "5 days", "1mo": "1 month", "3mo": "3 months",
    "6mo": "6 months", "ytd": "year-to-date", "1y": "1 year", "2y": "2 years",
    "5y": "5 years", "10y": "10 years", "max": "all time",
}

_EXCHANGE = {
    "NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "NYQ": "NYSE",
    "NYS": "NYSE",   "PCX": "NYSE Arca", "ASE": "NYSE American",
    "BTS": "BATS",   "LSE": "LSE", "TOR": "TSX",
}

_SPARK = "▁▂▃▄▅▆▇█"

# Friendly aliases for non-fundamental market subjects — indices, commodities,
# and FX. They load via yfinance and support price / chart / news. token →
# (yfinance symbol, display name, kind).
SPECIAL_SUBJECTS = {
    "SPX":    ("^GSPC", "S&P 500",                 "index"),
    "SP500":  ("^GSPC", "S&P 500",                 "index"),
    "NDX":    ("^NDX",  "Nasdaq 100",              "index"),
    "NASDAQ": ("^IXIC", "Nasdaq Composite",        "index"),
    "DJIA":   ("^DJI",  "Dow Jones Industrial",    "index"),
    "RUSSELL":("^RUT",  "Russell 2000",            "index"),
    "VIX":    ("^VIX",  "CBOE Volatility Index",   "index"),
    "GOLD":   ("GC=F",  "Gold (front future)",     "commodity"),
    "SILVER": ("SI=F",  "Silver (front future)",   "commodity"),
    "OIL":    ("CL=F",  "WTI Crude Oil",           "commodity"),
    "BRENT":  ("BZ=F",  "Brent Crude Oil",         "commodity"),
    "NATGAS": ("NG=F",  "Natural Gas",             "commodity"),
    "COPPER": ("HG=F",  "Copper",                  "commodity"),
    "EURUSD": ("EURUSD=X", "Euro / US Dollar",     "fx"),
    "GBPUSD": ("GBPUSD=X", "Pound / US Dollar",    "fx"),
    "USDJPY": ("USDJPY=X", "US Dollar / Yen",      "fx"),
    "AUDUSD": ("AUDUSD=X", "Aussie / US Dollar",   "fx"),
    "USDCAD": ("USDCAD=X", "US Dollar / Canada",   "fx"),
    "USDCNY": ("USDCNY=X", "US Dollar / Yuan",     "fx"),
    "USDCHF": ("USDCHF=X", "US Dollar / Franc",    "fx"),
    "DXY":    ("DX-Y.NYB", "US Dollar Index",      "fx"),
    # More global indices
    "FTSE":     ("^FTSE",  "FTSE 100 (UK)",        "index"),
    "DAX":      ("^GDAXI", "DAX (Germany)",        "index"),
    "CAC":      ("^FCHI",  "CAC 40 (France)",      "index"),
    "NIKKEI":   ("^N225",  "Nikkei 225 (Japan)",   "index"),
    "HANGSENG": ("^HSI",   "Hang Seng (HK)",       "index"),
    "SENSEX":   ("^BSESN", "BSE Sensex (India)",   "index"),
    "STOXX":    ("^STOXX50E", "Euro Stoxx 50",     "index"),
    "KOSPI":    ("^KS11",  "KOSPI (Korea)",        "index"),
    "ASX":      ("^AXJO",  "ASX 200 (Australia)",  "index"),
    "TSX":      ("^GSPTSE","TSX (Canada)",         "index"),
    "IBOVESPA": ("^BVSP",  "Ibovespa (Brazil)",    "index"),
    "SMI":      ("^SSMI",  "SMI (Switzerland)",    "index"),
    "AEX":      ("^AEX",   "AEX (Netherlands)",    "index"),
    "IBEX":     ("^IBEX",  "IBEX 35 (Spain)",      "index"),
    # More commodities
    "WHEAT":    ("ZW=F",   "Wheat futures",        "commodity"),
    "CORN":     ("ZC=F",   "Corn futures",         "commodity"),
    "SOYBEAN":  ("ZS=F",   "Soybean futures",      "commodity"),
    "COFFEE":   ("KC=F",   "Coffee futures",       "commodity"),
    "SUGAR":    ("SB=F",   "Sugar futures",        "commodity"),
    "COCOA":    ("CC=F",   "Cocoa futures",        "commodity"),
    "COTTON":   ("CT=F",   "Cotton futures",       "commodity"),
    "OJ":       ("OJ=F",   "Orange Juice futures", "commodity"),
    "GASOLINE": ("RB=F",   "RBOB Gasoline",        "commodity"),
    "HEATINGOIL":("HO=F",  "Heating Oil",          "commodity"),
    "PLATINUM": ("PL=F",   "Platinum futures",     "commodity"),
    "PALLADIUM":("PA=F",   "Palladium futures",    "commodity"),
    "ALUMINUM": ("ALI=F",  "Aluminum futures",     "commodity"),
    "URANIUM":  ("URA",    "Uranium (URA ETF)",    "commodity"),
    # More FX
    "NZDUSD":   ("NZDUSD=X", "Kiwi / US Dollar",   "fx"),
    "USDMXN":   ("USDMXN=X", "US Dollar / Peso",   "fx"),
    "USDINR":   ("USDINR=X", "US Dollar / Rupee",  "fx"),
    "USDBRL":   ("USDBRL=X", "US Dollar / Real",   "fx"),
    "USDKRW":   ("USDKRW=X", "US Dollar / Won",    "fx"),
    "USDTRY":   ("USDTRY=X", "US Dollar / Lira",   "fx"),
    "USDSEK":   ("USDSEK=X", "US Dollar / Krona",  "fx"),
    "USDZAR":   ("USDZAR=X", "US Dollar / Rand",   "fx"),
}


def normalize_range(token: str) -> str | None:
    return RANGE_ALIASES.get((token or "").lower())


# ── subject loading ───────────────────────────────────────────────────────────

_PREFIXES = {"chain", "country", "fred"}


def is_subject_token(token: str) -> bool:
    """True if `token` could name a subject (not a bare verb)."""
    from src.data.macro import MACRO_SERIES
    from src.data.symbols import looks_like_ticker
    from src.data.worldbank import COUNTRIES
    from src.data.defillama import CHAINS
    if ":" in token and token.split(":", 1)[0].lower() in _PREFIXES:
        return True
    up = token.upper()
    if up in MACRO_SERIES or up in SPECIAL_SUBJECTS or up in COUNTRIES or up in CHAINS:
        return True
    return looks_like_ticker(token)


def resolve_subject(token: str) -> Subject | None:
    """Resolve any token to a Subject (no printing, no ctx mutation)."""
    token = token.strip()
    if not token:
        return None
    up = token.upper()

    # Namespaced subjects: chain:… country:… fred:…
    if ":" in token and token.split(":", 1)[0].lower() in _PREFIXES:
        pre, val = token.split(":", 1)
        pre = pre.lower()
        if pre == "chain":
            from src.data.defillama import resolve_chain
            c = resolve_chain(token)
            if c:
                return Subject(symbol=c[1], kind="chain", name=c[1], ref=c[0])
        if pre == "country":
            from src.data.worldbank import resolve_country
            c = resolve_country(val) or (val.upper()[:2], val.title())
            return Subject(symbol=c[1], kind="country", name=c[1], ref=c[0])
        if pre == "fred":
            from src.data.macro import resolve_macro
            m = resolve_macro(val)
            if m:
                return Subject(symbol=val.upper(), kind="macro", name=m[1], fred_id=m[0])

    from src.data.macro import MACRO_SERIES, resolve_macro
    from src.data.symbols import looks_like_ticker
    from src.data.worldbank import COUNTRIES
    from src.data.defillama import CHAINS

    if up in MACRO_SERIES:
        fred_id, name, _ = MACRO_SERIES[up]
        return Subject(symbol=up, kind="macro", name=name, fred_id=fred_id)
    if up in SPECIAL_SUBJECTS:
        yf_sym, name, kind = SPECIAL_SUBJECTS[up]
        return Subject(symbol=up, kind=kind, name=name, yf=yf_sym)
    if up in COUNTRIES:
        iso, name = COUNTRIES[up]
        return Subject(symbol=up, kind="country", name=name, ref=iso)
    if up in CHAINS:
        slug, name = CHAINS[up]
        return Subject(symbol=up, kind="chain", name=name, ref=slug)
    if not looks_like_ticker(token) and token.isupper():
        m = resolve_macro(token)
        if m:
            return Subject(symbol=up, kind="macro", name=m[1], fred_id=m[0])

    # Equity / ETF / crypto.
    from src.data.symbols import resolve_symbol
    from src.data.crypto import is_crypto
    sym = (resolve_symbol(token) or up).strip()
    if is_crypto(sym):
        return Subject(symbol=sym, kind="crypto", name=_crypto_name(sym), yf=f"{sym}-USD")
    name, exch, qtype = _equity_meta(sym)
    if not name:
        return None
    kind = "etf" if qtype == "ETF" else "equity"
    return Subject(symbol=sym, kind=kind, name=name, exchange=exch)


def load_subject(token: str) -> Subject | None:
    """Resolve a subject and print the one-line confirmation (router owns the set)."""
    with _loading(f"loading {token.strip().upper()}"):
        subj = resolve_subject(token)
    if subj is None:
        print_error(f"Couldn't load '{escape(token)}'. Check the symbol, name, "
                    f"or prefix (chain: / country:).")
        return None
    _confirm(subj)
    return subj


# `compare` peers resolve the same way, just without the confirmation print.
peer_subject = resolve_subject


def _confirm(subj: Subject):
    rest = subj.confirm_line().split(" · ", 1)
    tail = f" [{MUTE}]· {escape(rest[1])}[/]" if len(rest) > 1 else ""
    console.print(f"  [bold {C}]{escape(subj.symbol)}[/] [{MUTE}]loaded[/]{tail}")


def _equity_meta(sym: str) -> tuple[str, str, str]:
    try:
        import yfinance as yf
        info = yf.Ticker(sym).info or {}
        name = info.get("longName") or info.get("shortName") or ""
        exch = _EXCHANGE.get(info.get("exchange", ""),
                             info.get("exchangeAcronym") or info.get("exchange") or "")
        return name, exch, (info.get("quoteType") or "").upper()
    except Exception:
        return "", "", ""


def _crypto_name(sym: str) -> str:
    from src.data.crypto import _SYMBOL_MAP
    cg = _SYMBOL_MAP.get(sym.upper(), "")
    return cg.replace("-", " ").title() if cg else sym


def _yf_symbol(subj: Subject) -> str:
    return subj.yf or subj.symbol


def _loading(msg: str):
    """A spinner shown while a verb fetches data."""
    return console.status(f"[{MUTE}]{escape(msg)}…[/]", spinner="dots")


def _show(body, title: str = ""):
    """Render a panel AND record its plain text in the in-memory session
    transcript, so `ask` can feed it back to Fin-R1 as context."""
    try:
        plain = Text.from_markup(body).plain if isinstance(body, str) else str(body)
    except Exception:
        plain = body if isinstance(body, str) else str(body)
    ctx.remember(title, plain)
    _panel(body, title=title)


# ── verbs ─────────────────────────────────────────────────────────────────────

def v_price(subjects: list[Subject]):
    s = subjects[0]
    with _loading(f"{s.symbol} price"):
        if s.kind == "macro":
            from src.data.macro import MACRO_SERIES, get_macro_snapshot
            _, _, unit = MACRO_SERIES.get(s.symbol, (s.fred_id, s.name, ""))
            body = get_macro_snapshot(s.fred_id, s.name, unit)
            _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Latest")
            return
        if s.kind == "crypto":
            from src.data.crypto import get_crypto_quote
            _show(f"[{WHITE}]{escape(get_crypto_quote(s.symbol))}[/]", title=f"{s.symbol}  ›  Price")
            return
        if s.kind == "country":
            from src.data.worldbank import overview
            _show(f"[{WHITE}]{escape(overview(s.ref, s.name))}[/]", title=f"{s.symbol}  ›  Macro")
            return
        if s.kind == "chain":
            from src.data.defillama import chain_tvl
            _show(f"[{WHITE}]{escape(chain_tvl(s.ref, s.name))}[/]", title=f"{s.symbol}  ›  TVL")
            return
        if s.kind in ("index", "commodity", "fx"):
            from src.data.equities import get_simple_quote
            _show(f"[{WHITE}]{escape(get_simple_quote(s.yf, s.name))}[/]", title=f"{s.symbol}  ›  Price")
            return
        from src.data.equities import get_quote
        _show(f"[{WHITE}]{escape(get_quote(s.symbol))}[/]", title=f"{s.symbol}  ›  Price")


def _company_verb(subjects, fn, title: str):
    """Shared shape for verbs that need company fundamentals."""
    s = subjects[0]
    if not s.is_company:
        print_error(f"{title.lower()} needs a company ticker — load a stock first "
                    f"(this is a {s.kind} subject).")
        return
    with _loading(f"{s.symbol} {title.lower()}"):
        body = fn(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  {title}")


def v_financials(subjects: list[Subject]):
    from src.data.sec_xbrl import get_xbrl_financials
    from src.data.equities import get_income, get_ratios
    def _fn(t):
        xbrl = get_xbrl_financials(t)               # authoritative, from filed 10-Ks
        ratios = get_ratios(t)
        return (xbrl + "\n\n" + ratios) if xbrl else (get_income(t) + "\n\n" + ratios)
    _company_verb(subjects, _fn, "Financials")


def v_earnings(subjects: list[Subject]):
    from src.data.equities import get_earnings, get_next_earnings
    def _fn(t):
        body = get_earnings(t)
        nxt  = get_next_earnings(t)
        return body + (f"\n\n  Next report: {nxt}" if nxt else "")
    _company_verb(subjects, _fn, "Earnings")


def v_filings(subjects: list[Subject]):
    from src.data.gov import get_recent_filings
    _company_verb(subjects, get_recent_filings, "Filings")


def v_calendar(subjects: list[Subject]):
    from src.data.equities import get_calendar
    _company_verb(subjects, get_calendar, "Calendar")


def v_profile(subjects: list[Subject]):
    from src.data.equities import get_profile
    _company_verb(subjects, get_profile, "Profile")


def v_dividends(subjects: list[Subject]):
    from src.data.equities import get_dividends
    _company_verb(subjects, get_dividends, "Dividends")


def v_holders(subjects: list[Subject]):
    from src.data.equities import get_holders
    _company_verb(subjects, get_holders, "Ownership")


def v_analysts(subjects: list[Subject]):
    from src.data.equities import get_analysts
    _company_verb(subjects, get_analysts, "Analysts")


def v_insiders(subjects: list[Subject]):
    from src.data.gov import get_insider_trades
    _company_verb(subjects, get_insider_trades, "Insiders")


def v_news(subjects: list[Subject]):
    s = subjects[0]
    query = s.symbol if s.kind in ("equity", "crypto") else (s.yf or s.symbol)
    from src.data.news import get_news_feed
    with _loading(f"{s.symbol} news"):
        feed = get_news_feed(query, limit=6)
    if not feed:
        print_error(f"No recent headlines for {s.symbol}.")
        return
    lines = []
    for i, a in enumerate(feed, 1):
        title = escape(a["title"])
        head  = f"[link={a['link']}]{title}[/link]" if a["link"] else title
        meta  = "  ·  ".join(x for x in (a["publisher"], a["ago"]) if x)
        lines.append(f"  [bold {C}]{i:>2}[/]  [{WHITE}]{head}[/]")
        if meta:
            lines.append(f"      [{MUTE}]{escape(meta)}[/]")
        lines.append("")
    lines.append(f"  [{MUTE}]Ctrl/⌘-click a headline to open it.[/]")
    _show("\n".join(lines).rstrip(), title=f"{s.symbol}  ›  News  ({len(feed)} latest)")


def v_compare(subjects: list[Subject]):
    syms = [s.symbol for s in subjects]
    if len(syms) < 2:
        print_error("compare needs a peer — e.g. [white]compare AMD[/] "
                    "(chain more for 3-way: [white]compare AMD INTC[/]).")
        return
    with _loading("comparing " + ", ".join(syms)):
        from src.data.equities import get_comparison
        body = get_comparison(syms)
    _show(f"[{WHITE}]{escape(body)}[/]",
                title="Compare  ›  " + "  vs  ".join(syms[:4]))


def v_chart(subjects: list[Subject], rng: str | None, prev_verb: str | None):
    canon = normalize_range(rng) if rng else None
    if not canon:
        print_error("chart needs a range — e.g. [white]chart 1y[/] · "
                    "5d 1mo 3mo 6mo ytd 1y 2y 5y 10y max")
        return

    # `chart` inherits the prior verb's output: after `earnings`, chart the
    # beat/miss history rather than price.
    if prev_verb == "earnings" and subjects[0].kind == "equity":
        _earnings_chart(subjects[0], canon)
        return

    series = []
    for s in subjects:
        if s.kind == "macro":
            from src.data.macro import get_series
            vals = [v for _, v in get_series(s.fred_id, canon)]
        elif s.kind == "chain":
            from src.data.defillama import chain_tvl_series
            days = {"5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "ytd": 250,
                    "1y": 365, "2y": 730, "5y": 1825, "10y": 3650, "max": 100000}.get(canon, 365)
            vals = chain_tvl_series(s.ref, days) or []
        elif s.is_priced:
            from src.data.equities import get_chart_data
            vals = get_chart_data(_yf_symbol(s), canon)
        else:
            vals = []
        if vals:
            series.append((s.symbol, vals))

    if not series:
        print_error(f"No chartable history for {', '.join(s.symbol for s in subjects)} "
                    f"(this subject type has no price series).")
        return

    label = _RANGE_LABEL.get(canon, canon)
    if len(series) == 1:
        _single_chart(series[0][0], series[0][1], label)
    else:
        _multi_chart(series, label)


# ── utility & data verbs ──────────────────────────────────────────────────────

def _priced_items(subjects):
    return [(s.symbol, _yf_symbol(s)) for s in subjects if s.is_priced]


def _country_verb(subjects, fn, title):
    s = subjects[0]
    if s.kind != "country":
        print_error(f"{title.lower()} needs a country — e.g. [white]US[/], [white]CHINA[/], "
                    f"or [white]country:BR[/].")
        return
    with _loading(f"{s.symbol} {title.lower()}"):
        body = fn(s.ref, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  {title}")


def v_gdp(subjects):
    from src.data.worldbank import gdp;        _country_verb(subjects, gdp, "GDP")


def v_inflation(subjects):
    from src.data.worldbank import inflation;  _country_verb(subjects, inflation, "Inflation")


def v_trade(subjects):
    from src.data.worldbank import trade;      _country_verb(subjects, trade, "Trade")


def v_debt(subjects):
    from src.data.worldbank import debt;       _country_verb(subjects, debt, "Debt")


def v_tvl(subjects):
    s = subjects[0]
    if s.kind != "chain":
        print_error("tvl needs a chain — e.g. [white]ETHEREUM[/] or [white]chain:arbitrum[/].")
        return
    from src.data.defillama import chain_tvl
    with _loading(f"{s.symbol} tvl"):
        body = chain_tvl(s.ref, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  TVL")


def v_holdings(subjects):
    from src.data.equities import get_etf_holdings
    _company_or(subjects, get_etf_holdings, "Holdings")


def v_short(subjects):
    from src.data.equities import get_short_interest
    _company_verb(subjects, get_short_interest, "Short Interest")


def v_options(subjects):
    from src.data.equities import get_options
    _company_verb(subjects, get_options, "Options")


def v_splits(subjects):
    from src.data.equities import get_splits
    _company_verb(subjects, get_splits, "Splits")


def v_unemployment(subjects):
    from src.data.worldbank import unemployment
    _country_verb(subjects, unemployment, "Unemployment")


def v_population(subjects):
    from src.data.worldbank import population
    _country_verb(subjects, population, "Population")


def v_sentiment(subjects):
    s = subjects[0]
    if s.kind not in ("equity", "etf", "crypto"):
        print_error("sentiment needs a stock or crypto subject.")
        return
    from src.data.news import get_sentiment
    with _loading(f"{s.symbol} sentiment"):
        body = get_sentiment(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Sentiment")


def v_seasonality(subjects):
    s = subjects[0]
    if not s.is_priced:
        print_error("seasonality needs a priced subject (equity/ETF/index/FX/crypto).")
        return
    from src.data.analytics import seasonality
    with _loading(f"{s.symbol} seasonality"):
        body = seasonality(s.symbol, _yf_symbol(s))
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Seasonality")


def v_trends(subjects):
    s = subjects[0]
    from src.data.trends import pageviews
    with _loading(f"{s.symbol} attention"):
        body = pageviews(s.name or s.symbol, s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Attention")


def v_risk(subjects):
    s = subjects[0]
    from src.data.risk import risk_report
    with _loading(f"{s.symbol} risk"):
        body = risk_report(s.symbol, s.name or s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Risk")


_SUPPLY_FRED = {
    "OIL":    ("WCESTUS1", "U.S. Crude Oil Ending Stocks (thousand barrels)"),
    "NATGAS": ("NGSTUS",   "U.S. Natural Gas in Underground Storage (Bcf)"),
}


def v_supply(subjects):
    s = subjects[0]
    spec = _SUPPLY_FRED.get(s.symbol)
    if s.kind != "commodity" or not spec:
        print_error("supply has inventory data for [white]OIL[/] and [white]NATGAS[/].")
        return
    fred_id, label = spec
    from src.data.macro import get_series
    with _loading(f"{s.symbol} supply"):
        rows = get_series(fred_id, "2y")
    if not rows:
        print_error(f"Inventory series for {s.symbol} is unavailable right now.")
        return
    out = [label, "Source: FRED / EIA", "", f"  {'Date':<14} {'Level':>14}", "  " + "─" * 30]
    for d, v in rows[-14:]:
        out.append(f"  {d:<14} {v:>14,.0f}")
    _show(f"[{WHITE}]" + "\n".join(out) + "[/]", title=f"{s.symbol}  ›  Supply")


# ── set-aware analytics verbs ─────────────────────────────────────────────────

def v_returns(subjects):
    items = _priced_items(subjects)
    if not items:
        print_error("returns needs priced subjects (equity/ETF/index/FX/crypto).")
        return
    from src.data.analytics import returns_table
    with _loading("computing returns"):
        body = returns_table(items)
    _show(f"[{WHITE}]{escape(body)}[/]", title="Returns")


def v_stats(subjects):
    items = _priced_items(subjects)
    if not items:
        print_error("stats needs priced subjects (equity/ETF/index/FX/crypto).")
        return
    from src.data.analytics import stats_table
    with _loading("computing stats"):
        body = stats_table(items)
    _show(f"[{WHITE}]{escape(body)}[/]", title="Risk & Return")


def v_corr(subjects):
    items = _priced_items(subjects)
    if len(items) < 2:
        print_error("corr needs ≥2 priced subjects — e.g. [white]NVDA vs AMD vs SMH corr[/].")
        return
    from src.data.analytics import corr_matrix
    with _loading("computing correlations"):
        body = corr_matrix(items)
    _show(f"[{WHITE}]{escape(body)}[/]", title="Correlation")


def v_spread(subjects):
    items = _priced_items(subjects)
    if len(items) != 2:
        print_error("spread needs exactly two priced subjects — e.g. [white]NVDA vs SMH spread[/].")
        return
    from src.data.analytics import spread_series
    with _loading("computing spread"):
        res = spread_series(items[0], items[1])
    if not res:
        print_error("Couldn't build that spread.")
        return
    label, vals = res
    _single_chart(label, vals, "2 years")


# ── global verbs (no subject needed) ──────────────────────────────────────────

def v_hours(subjects):
    from datetime import datetime, time
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        now = datetime.now()
    weekday = now.weekday() < 5
    open_t, close_t = time(9, 30), time(16, 0)
    is_open = weekday and open_t <= now.time() < close_t
    status = "[#00c853]OPEN[/]" if is_open else "[#ff1744]CLOSED[/]"
    if weekday and now.time() < open_t:
        nxt = f"opens {open_t.strftime('%H:%M')} ET today"
    elif is_open:
        nxt = f"closes {close_t.strftime('%H:%M')} ET"
    else:
        nxt = "opens 09:30 ET next trading day"
    rows = [
        f"  US (NYSE / Nasdaq)   {status}   [{MUTE}]{escape(nxt)}[/]",
        f"  [{MUTE}]Now {now.strftime('%a %H:%M')} ET[/]", "",
        f"  [{MUTE}]Regular sessions (local):[/]",
        f"  [{MUTE}]  London   08:00–16:30   ·   Tokyo 09:00–15:00   ·   "
        f"Frankfurt 09:00–17:30[/]",
    ]
    _show("\n".join(rows), title="Market Hours")


def v_export(subjects):
    from pathlib import Path
    from datetime import datetime
    if not ctx.history:
        print_error("Nothing to export yet — run some verbs first.")
        return
    d = Path.home() / ".fingpt" / "exports"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"session-{datetime.now():%Y%m%d-%H%M%S}.md"
    lines = [f"# FinR1 Terminal — session export", f"_{datetime.now():%Y-%m-%d %H:%M}_", ""]
    for e in ctx.history:
        lines.append(f"## {e['label']}\n\n```\n{e['text']}\n```\n")
    path.write_text("\n".join(lines))
    console.print(f"  [bold #00c853]✓[/] exported {len(ctx.history)} panels → "
                  f"[white]{escape(str(path))}[/]\n")


def v_convert(args):
    import requests
    toks = [a for a in args if a.lower() != "to"]
    if len(toks) < 3:
        print_error('Usage: [white]convert 100 USD EUR[/]')
        return
    try:
        amt = float(toks[0].replace(",", ""))
    except ValueError:
        print_error("First argument must be a number — [white]convert 100 USD EUR[/].")
        return
    frm, to = toks[1].upper(), toks[2].upper()
    try:
        with _loading(f"{frm}→{to}"):
            r = requests.get("https://api.frankfurter.app/latest",
                             params={"amount": amt, "from": frm, "to": to}, timeout=10)
            r.raise_for_status()
            data = r.json()
        rate = (data.get("rates") or {}).get(to)
        if rate is None:
            print_error(f"Couldn't convert {frm}→{to}. Use ISO currency codes (USD, EUR, JPY…).")
            return
        body = (f"  {amt:,.2f} {frm}  =  {rate:,.2f} {to}\n\n"
                f"  [{MUTE}]rate 1 {frm} = {rate/amt:.4f} {to}   ·   "
                f"{escape(data.get('date',''))}   ·   ECB[/]")
        _show(body, title=f"Convert  ›  {frm} → {to}")
    except Exception as e:
        print_error(f"Conversion failed: {e}")


def _company_or(subjects, fn, title):
    """Like _company_verb but tolerant — for verbs (holdings) that also apply to ETFs."""
    s = subjects[0]
    with _loading(f"{s.symbol} {title.lower()}"):
        body = fn(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  {title}")


def v_yields(subjects):
    from src.data.macro import get_yield_curve
    with _loading("treasury yields"):
        body = get_yield_curve()
    _show(f"[{WHITE}]{escape(body)}[/]", title="US Treasury Yields")


def v_fear(subjects):
    from src.data.alt import get_fear_greed
    with _loading("fear & greed"):
        body = get_fear_greed()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Crypto Fear & Greed")


def v_dominance(subjects):
    from src.data.crypto import get_global_dominance
    with _loading("market dominance"):
        body = get_global_dominance()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Crypto Market Dominance")


def v_coins(subjects):
    from src.data.crypto import get_top_coins
    with _loading("top coins"):
        body = get_top_coins(15)
    _show(f"[{WHITE}]{escape(body)}[/]", title="Top Coins by Market Cap")


def v_sectors(subjects):
    from src.data.equities import get_sectors
    with _loading("sector performance"):
        body = get_sectors()
    _show(f"[{WHITE}]{escape(body)}[/]", title="US Sectors")


def _market_table(kind: str, title: str):
    from src.data.equities import perf_table
    items = [(name, yf) for (yf, name, k) in SPECIAL_SUBJECTS.values() if k == kind]
    # de-dup by yf symbol (some aliases share a symbol)
    seen, uniq = set(), []
    for name, yf in items:
        if yf not in seen:
            seen.add(yf); uniq.append((name, yf))
    with _loading(title.lower()):
        body = perf_table(title, uniq, "Yahoo Finance · 1-day / 1-month")
    _show(f"[{WHITE}]{escape(body)}[/]", title=title)


def v_indices(subjects):
    _market_table("index", "World Indices")


def v_commodities(subjects):
    _market_table("commodity", "Commodities")


def v_forex(subjects):
    _market_table("fx", "Foreign Exchange")


def v_protocols(subjects):
    from src.data.defillama import top_protocols
    with _loading("defi protocols"):
        body = top_protocols()
    _show(f"[{WHITE}]{escape(body)}[/]", title="DeFi Protocols")


def v_stablecoins(subjects):
    from src.data.defillama import stablecoins
    with _loading("stablecoins"):
        body = stablecoins()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Stablecoins")


# ── chart renderers ───────────────────────────────────────────────────────────

def _chart_cols(prefix: int) -> int:
    """Plot width that fits the current terminal, leaving room for axis + border."""
    try:
        cw = console.width or 100
    except Exception:
        cw = 100
    return max(20, min(160, cw - prefix - 6))


def _fit(values: list, width: int) -> list:
    """Downsample a series to `width` columns by bucket-averaging (charts plot
    one column per point, so a 252-day series must be compressed to fit)."""
    n = len(values)
    if n <= width:
        return values
    out = []
    for i in range(width):
        lo = i * n // width
        hi = max(lo + 1, (i + 1) * n // width)
        chunk = values[lo:hi]
        out.append(sum(chunk) / len(chunk))
    return out


def _single_chart(label: str, closes: list, range_label: str):
    first, last = closes[0], closes[-1]
    chg    = (last / first - 1) * 100 if first else 0
    color  = GREEN if last >= first else RED
    closes = _fit(closes, _chart_cols(14))
    hi, lo = max(closes), min(closes)
    rng    = (hi - lo) or 1
    h      = 12
    w      = len(closes)
    rows   = []
    for row in range(h, -1, -1):
        threshold = lo + (row / h) * rng
        line      = "".join("█" if p >= threshold else " " for p in closes)
        rows.append(f"{threshold:>11.2f} │[{color}]{line}[/]")
    chart  = "\n".join(rows)
    chart += f"\n{'':>12}└{'─' * w}"
    chart += (f"\n{'':>13}[{MUTE}]◄ {range_label}[/]"
              f"{'':>{max(1, w - len(range_label) - 14)}}"
              f"[{color}]{chg:+.1f}%[/]")
    _show(f"[{WHITE}]{chart}[/]", title=f"{label}  ›  Chart  ({range_label})")


def _multi_chart(series: list, range_label: str):
    """Compare chart: one shared-scale sparkline per subject, so relative
    performance reads at a glance and it stays clean for 2, 3, or 4 names.
    Overlaying ASCII lines turns to noise — stacked rows on one scale don't."""
    cols = _chart_cols(28)
    norm = []
    for label, vals in series:
        base = vals[0] or 1
        norm.append((label, _fit([(v / base - 1) * 100 for v in vals], cols)))
    allv   = [x for _, p in norm for x in p]
    lo, hi = min(allv), max(allv)
    span   = (hi - lo) or 1
    colors = [C, GREEN, "#4a9eff", "#ffab00", "#c77dff"]

    lab_w = max(len(l) for l, _ in norm)
    rows = []
    for si, (label, p) in enumerate(norm):
        spark = "".join(_SPARK[min(int((x - lo) / span * 7), 7)] for x in p)
        ret   = p[-1]
        col   = colors[si % len(colors)]
        retc  = GREEN if ret >= 0 else RED
        rows.append(f"  [{col}]{label:<{lab_w}}[/]  [{col}]{spark}[/]  [{retc}]{ret:+6.1f}%[/]")

    header = (f"  [{MUTE}]return over {range_label}, shared scale[/] "
              f"[{RED}]{lo:+.0f}%[/] [{MUTE}]…[/] [{GREEN}]{hi:+.0f}%[/]")
    body  = header + "\n\n" + "\n".join(rows)
    title = "Compare  ›  " + " vs ".join(l for l, _ in series)
    _show(body, title=f"{title}  ({range_label})")


def _earnings_chart(subj: Subject, canon: str):
    import yfinance as yf
    quarters = {"1y": 4, "2y": 8, "5y": 20, "max": 40}.get(canon, 8)
    try:
        df = yf.Ticker(subj.symbol).earnings_dates
        df = df[df["Reported EPS"].notna()].head(quarters)
    except Exception:
        df = None
    if df is None or df.empty:
        print_error(f"No earnings history to chart for {subj.symbol}.")
        return

    lines = [f"Earnings surprise — last {len(df)} quarters", ""]
    for date, row in df.iloc[::-1].iterrows():
        sur = row.get("Surprise(%)")
        q   = date.strftime("%b %Y")
        if sur != sur or sur is None:
            lines.append(f"  {q:<10} —")
            continue
        beat  = sur >= 0
        color = GREEN if beat else RED
        bar   = ("█" if beat else "▒") * min(int(abs(sur)), 30)
        lines.append(f"  {q:<10} [{color}]{bar} {sur:+.1f}%[/]")
    _show(f"[{WHITE}]" + "\n".join(lines) + "[/]",
                title=f"{subj.symbol}  ›  Earnings Chart  ({_RANGE_LABEL.get(canon, canon)})")


# ── watchlist ─────────────────────────────────────────────────────────────────

def v_watch(subjects: list[Subject]):
    """Personal watchlist. A loaded subject + `watch` toggles it on the list;
    bare `watch` just lists what you're tracking with live quotes."""
    wl = _watch_load()
    if subjects:
        sym = subjects[0].symbol
        if sym in wl:
            wl.remove(sym)
            console.print(f"  [{MUTE}]removed[/] [bold {C}]{escape(sym)}[/] [{MUTE}]from watchlist[/]")
        else:
            wl.append(sym)
            console.print(f"  [bold {C}]{escape(sym)}[/] [{MUTE}]added to watchlist[/]")
        _watch_save(wl)
    _render_watch(wl)


def _watch_load() -> list:
    try:
        if WATCH_FILE.exists():
            return json.loads(WATCH_FILE.read_text())
    except Exception:
        pass
    return []


def _watch_save(wl: list):
    WATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCH_FILE.write_text(json.dumps(wl, indent=2))


def _render_watch(wl: list):
    if not wl:
        _show(
            f"[{MUTE}]Watchlist is empty. Load a ticker and type [/][white]watch[/]"
            f"[{MUTE}] to add it — e.g. [/][white]NVDA[/][{MUTE}] then [/][white]watch[/][{MUTE}].[/]",
            title="Watchlist")
        return
    import yfinance as yf
    from src.data.equities import get_next_earnings
    rows = [f"  {'TICKER':<8} {'PRICE':>12} {'CHG':>10}   NEXT EVENT"]
    for sym in wl:
        try:
            fast  = yf.Ticker(sym).fast_info
            price = fast.last_price
            prev  = fast.previous_close or price
            chg   = (price - prev) / prev * 100 if prev else 0
            color = GREEN if chg >= 0 else RED
            arrow = "▲" if chg >= 0 else "▼"
            nxt   = get_next_earnings(sym) or "—"
            rows.append(
                f"  {sym:<8} [{WHITE}]${price:>10,.2f}[/] "
                f"[{color}]{arrow} {chg:>6.2f}%[/]   [{MUTE}]Earnings {escape(nxt)}[/]"
            )
        except Exception:
            rows.append(f"  {sym:<8} {'—':>12} {'—':>10}")
    _show("\n".join(rows), title="Watchlist")


# ── screener ──────────────────────────────────────────────────────────────────

def v_screen(name: str | None):
    """Run a stock screen, or list the available ones. Needs no loaded subject —
    it produces candidates you can then load by typing one's ticker."""
    from src.data.screener import SCREENS, list_screens, get_screen_rows
    if not name:
        _show(f"[{WHITE}]{escape(list_screens())}[/]", title="Screens")
        return
    key = name.lower().strip()
    if key not in SCREENS:
        print_error(f"Unknown screen '{escape(name)}'. Type [white]screen[/] to list them.")
        return
    with _loading(f"screening {key}"):
        rows = get_screen_rows(key, count=20)
    if not rows:
        print_error(f"No results for screen '{escape(name)}' right now.")
        return

    out = [f"  {'TICKER':<8} {'PRICE':>11} {'CHG':>9}  {'MKT CAP':>10}  {'P/E':>7}  COMPANY"]
    for r in rows:
        chg   = r["chg"]
        color = GREEN if (chg or 0) >= 0 else RED
        arrow = "▲" if (chg or 0) >= 0 else "▼"
        price = f"${r['price']:,.2f}" if r["price"] is not None else "—"
        chg_s = f"{arrow} {chg:>5.1f}%" if chg is not None else "—"
        pe    = f"{r['pe']:.1f}" if r["pe"] is not None else "—"
        out.append(
            f"  [bold {C}]{r['symbol']:<8}[/] [{WHITE}]{price:>11}[/] "
            f"[{color}]{chg_s:>9}[/]  [{WHITE}]{r['mktcap']:>10}[/]  [{MUTE}]{pe:>7}[/]  "
            f"[{MUTE}]{escape(r['name'][:30])}[/]"
        )
    out.append(f"\n  [{MUTE}]Load any of these — just type its ticker.[/]")
    _show("\n".join(out), title=f"Screen  ›  {escape(SCREENS[key][1])}")
