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

_PREFIXES = {"chain", "country", "fred", "protocol", "stable", "stablecoin",
             "exchange", "topic"}


def is_subject_token(token: str) -> bool:
    """True if `token` could name a subject (not a bare verb)."""
    from src.data.macro import MACRO_SERIES
    from src.data.symbols import looks_like_ticker
    from src.data.worldbank import COUNTRIES
    from src.data.defillama import CHAINS, PROTOCOLS, STABLECOINS
    from src.data.calendars import EXCHANGES
    if ":" in token and token.split(":", 1)[0].lower() in _PREFIXES:
        return True
    up = token.upper()
    if (up in MACRO_SERIES or up in SPECIAL_SUBJECTS or up in COUNTRIES or up in CHAINS
            or up in PROTOCOLS or up in STABLECOINS or up in EXCHANGES):
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
        if pre == "protocol":
            from src.data.defillama import resolve_protocol
            p = resolve_protocol(token)
            if p:
                return Subject(symbol=p[1], kind="protocol", name=p[1], ref=p[0])
        if pre in ("stable", "stablecoin"):
            from src.data.defillama import resolve_stablecoin
            sc = resolve_stablecoin(token)
            if sc:
                return Subject(symbol=val.upper(), kind="stablecoin", name=sc[1], ref=sc[0])
        if pre == "exchange":
            from src.data.calendars import resolve_exchange
            ex = resolve_exchange(token)
            if ex:
                return Subject(symbol=val.upper(), kind="exchange", name=ex[1], ref=ex[0])
        if pre == "topic":
            phrase = val.strip()
            phrase = phrase[:1].upper() + phrase[1:]      # Wikipedia titles are case-sensitive
            return Subject(symbol=phrase[:24], kind="topic", name=phrase)

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

    # Loadable DeFi protocols, stablecoins, and exchanges (checked after the
    # market/index aliases above, so e.g. NASDAQ stays the index).
    from src.data.defillama import PROTOCOLS, STABLECOINS
    from src.data.calendars import EXCHANGES
    if up in EXCHANGES:
        mic, name, _tz = EXCHANGES[up]
        return Subject(symbol=up, kind="exchange", name=name, ref=mic)
    if up in STABLECOINS:
        sid, name = STABLECOINS[up]
        return Subject(symbol=up, kind="stablecoin", name=name, ref=sid)
    if up in PROTOCOLS:
        slug, name = PROTOCOLS[up]
        return Subject(symbol=up, kind="protocol", name=name, ref=slug)

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
    from src.display import KIND_COLORS
    accent = KIND_COLORS.get(subj.kind, C)
    bits = subj.confirm_line().split(" · ")
    name = escape(bits[1]) if len(bits) > 1 else ""
    tag = escape(bits[2]) if len(bits) > 2 else escape(subj.kind)
    console.print(
        f"  [bold {accent}]●[/] [bold {WHITE}]{escape(subj.symbol)}[/]"
        f"  [{MUTE}]{name}[/]   [{accent}]{tag}[/]"
    )


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
    transcript, so `ask` can feed it back to Fin-R1 as context. `body` may be a
    markup string or any Rich renderable (e.g. a table)."""
    if isinstance(body, str):
        try:
            plain = Text.from_markup(body).plain
        except Exception:
            plain = body
    else:
        with console.capture() as cap:        # render the table to text for /ask
            console.print(body)
        plain = cap.get()
    ctx.remember(title, plain)
    _panel(body, title=title)


# ── verbs ─────────────────────────────────────────────────────────────────────

def v_price(subjects: list[Subject]):
    s = subjects[0]
    with _loading(f"{s.symbol} price"):
        if s.kind == "protocol":
            from src.data.defillama import protocol_overview
            _show(f"[{WHITE}]{escape(protocol_overview(s.ref, s.name))}[/]", title=f"{s.symbol}  ›  Protocol")
            return
        if s.kind == "stablecoin":
            from src.data.defillama import stablecoin_overview
            _show(f"[{WHITE}]{escape(stablecoin_overview(s.ref, s.name))}[/]", title=f"{s.symbol}  ›  Stablecoin")
            return
        if s.kind == "exchange":
            from src.data.calendars import EXCHANGES, exchange_status
            _, _, tz = EXCHANGES.get(s.symbol, (s.ref, s.name, "UTC"))
            _show(f"[{WHITE}]{escape(exchange_status(s.ref, s.name, tz))}[/]", title=f"{s.symbol}  ›  Exchange")
            return
        if s.kind == "topic":
            from src.data.trends import pageviews
            _show(f"[{WHITE}]{escape(pageviews(s.name, s.name))}[/]", title=f"{s.symbol}  ›  Attention")
            return
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


def v_metrics(subjects: list[Subject]):
    """The deep fundamental / indicator dump — rendered as grouped tables. Works
    for any equity or any country."""
    s = subjects[0]
    from rich.console import Group
    from rich.text import Text as _T
    from src.data.metrics import equity_groups, country_rows
    from src.display import make_table, delta

    if s.kind in ("equity", "etf"):
        with _loading(f"{s.symbol} fundamentals"):
            groups = equity_groups(s.symbol)
        if not groups:
            print_error(f"No fundamental data available for {s.symbol}.")
            return
        n = sum(len(v) for v in groups.values())
        blocks = [_T.from_markup(f"  [#9aa0a6]{escape(s.name)} · {n} fields · Yahoo Finance[/]"), _T("")]
        for g, rows in groups.items():
            blocks.append(_T.from_markup(f"  [bold #d8b66a]{g}[/]"))
            blocks.append(make_table(["Field", "Value"],
                                     [(f"  {lbl}", delta(val)) for lbl, val in rows],
                                     justify=["left", "right"], show_header=False))
            blocks.append(_T(""))
        _show(Group(*blocks), title=f"{s.symbol}  ›  Metrics")
    elif s.kind == "country":
        from src.data.metrics import country_groups
        with _loading(f"{s.symbol} indicators"):
            groups = country_groups(s.ref)
        if not groups:
            print_error(f"No World Bank indicators available for {s.name}.")
            return
        n = sum(len(v) for v in groups.values())
        blocks = [_T.from_markup(f"  [#b4b4b4]{escape(s.name)} · {n} indicators · World Bank[/]"), _T("")]
        for g, rows in groups.items():
            blocks.append(_T.from_markup(f"  [bold #d8b66a]{g}[/]"))
            blocks.append(make_table(["Indicator", "Value", "Year"],
                                     [(f"  {lbl}", delta(val), f"[#7a7a7a]{yr}[/]") for lbl, val, yr in rows],
                                     justify=["left", "right", "right"], show_header=False))
            blocks.append(_T(""))
        _show(Group(*blocks), title=f"{s.symbol}  ›  Metrics")
    else:
        print_error(f"metrics covers equities and countries (this is a {s.kind} subject). "
                    f"Try [white]price[/] or [white]chart[/].")


def v_profile(subjects: list[Subject]):
    s = subjects[0]
    if s.kind == "country":
        from src.data.worldbank import overview
        with _loading(f"{s.symbol} profile"):
            body = overview(s.ref, s.name)
        _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Profile")
        return
    if not s.is_company:
        print_error(f"profile needs a company or country (this is a {s.kind} subject).")
        return
    from src.data.equities import get_profile
    from src.data.dev import wikipedia_summary, wikidata_facts
    with _loading(f"{s.symbol} profile"):
        body = get_profile(s.symbol)
        facts = wikidata_facts(s.name)
        wiki = wikipedia_summary(s.name)
    if facts:
        body += "\n\n  Wikidata:\n" + facts
    if wiki:
        from textwrap import fill
        body += "\n\n" + fill(wiki, width=72, initial_indent="  ", subsequent_indent="  ")
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Profile")


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
    from src.data.news import get_news_feed, google_news
    with _loading(f"{s.symbol} news"):
        feed = get_news_feed(query, limit=6)
        if not feed:                       # Yahoo is thin for macro/FX/country —
            feed = google_news(s.name or query, limit=6)   # fall back to Google News
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
        elif s.kind in ("chain", "protocol"):
            days = {"5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "ytd": 250,
                    "1y": 365, "2y": 730, "5y": 1825, "10y": 3650, "max": 100000}.get(canon, 365)
            if s.kind == "chain":
                from src.data.defillama import chain_tvl_series
                vals = chain_tvl_series(s.ref, days) or []
            else:
                from src.data.defillama import protocol_tvl_series
                vals = protocol_tvl_series(s.ref, days) or []
        elif s.kind == "stablecoin":
            from src.data.defillama import stablecoin_supply_series
            days = {"5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "ytd": 250,
                    "1y": 365, "2y": 730, "5y": 1825, "10y": 3650, "max": 100000}.get(canon, 365)
            vals = stablecoin_supply_series(s.ref, days) or []
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


def v_ftd(subjects):
    from src.data.gov import get_ftd
    _company_verb(subjects, get_ftd, "Fails-to-Deliver")


def v_fda(subjects):
    s = subjects[0]
    if not s.is_company:
        print_error(f"fda recalls search by company name (this is a {s.kind} subject).")
        return
    from src.data.openfda import fda_recalls
    with _loading(f"{s.symbol} fda recalls"):
        body = fda_recalls(s.name or s.symbol)        # openFDA matches the firm name
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  FDA Recalls")


def v_regulations(subjects):
    s = subjects[0]
    if not s.is_company:
        print_error(f"regulations searches the Federal Register by company name "
                    f"(this is a {s.kind} subject).")
        return
    from src.data.fedreg import company_regulations
    with _loading(f"{s.symbol} regulations"):
        body = company_regulations(s.name or s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Regulatory")


def v_github(subjects):
    s = subjects[0]
    if s.kind not in ("equity", "etf", "crypto"):
        print_error("github (dev activity) works on companies and crypto.")
        return
    from src.data.dev import github_activity
    with _loading(f"{s.symbol} github"):
        body = github_activity(s.name or s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  GitHub")


def v_contracts(subjects):
    s = subjects[0]
    if not s.is_company:
        print_error("contracts needs a company ticker — federal awards are by "
                    f"recipient (this is a {s.kind} subject).")
        return
    from src.data.spending import federal_contracts
    with _loading(f"{s.symbol} federal contracts"):
        body = federal_contracts(s.name or s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Federal Contracts")


def v_buzz(subjects):
    s = subjects[0]
    if s.kind not in ("equity", "etf", "crypto"):
        print_error("buzz (Hacker News) works on stocks, ETFs, and crypto.")
        return
    from src.data.news import hacker_news_buzz
    query = s.name or s.symbol
    with _loading(f"{s.symbol} hacker news"):
        body = hacker_news_buzz(query)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  HN Buzz")


def v_lobbying(subjects):
    s = subjects[0]
    if not s.is_company:
        print_error(f"lobbying searches Senate LDA filings by company (this is a {s.kind} subject).")
        return
    from src.data.govalt import lobbying
    with _loading(f"{s.symbol} lobbying"):
        body = lobbying(s.name or s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Lobbying")


def v_hiring(subjects):
    s = subjects[0]
    if not s.is_company:
        print_error(f"hiring reads a company's public job board (this is a {s.kind} subject).")
        return
    from src.data.hiring import hiring
    with _loading(f"{s.symbol} hiring"):
        body = hiring(s.symbol, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Hiring")


def v_shortvol(subjects):
    s = subjects[0]
    if not s.is_company and s.kind != "etf":
        print_error(f"shortvol needs a stock or ETF ticker (this is a {s.kind} subject).")
        return
    from src.data.govalt import short_volume
    with _loading(f"{s.symbol} short volume"):
        body = short_volume(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Short Volume")


def _equity_name_verb(subjects, fn, title, etf_ok=False):
    """Shared shape for equity verbs that search by company NAME."""
    s = subjects[0]
    if not (s.is_company or (etf_ok and s.kind == "etf")):
        print_error(f"{title.lower()} needs a company ticker (this is a {s.kind} subject).")
        return
    with _loading(f"{s.symbol} {title.lower()}"):
        body = fn(s.name or s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  {title}")


def v_litigation(subjects):
    from src.data.legal import litigation
    _equity_name_verb(subjects, litigation, "Litigation")


def v_campaigns(subjects):
    from src.data.legal import campaigns
    _equity_name_verb(subjects, campaigns, "Campaign Finance")


def v_epa(subjects):
    from src.data.legal import epa_compliance
    _equity_name_verb(subjects, epa_compliance, "EPA Compliance")


def v_mentions(subjects):
    from src.data.gov import sec_mentions
    _equity_name_verb(subjects, sec_mentions, "Filing Mentions")


def v_adoption(subjects):
    s = subjects[0]
    if not s.is_company:
        print_error(f"adoption tracks developer-package usage (this is a {s.kind} subject).")
        return
    from src.data.devdata import adoption
    with _loading(f"{s.symbol} adoption"):
        body = adoption(s.symbol, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Adoption")


def v_players(subjects):
    s = subjects[0]
    if not s.is_company:
        print_error(f"players tracks Steam concurrent players (this is a {s.kind} subject).")
        return
    from src.data.devdata import players
    with _loading(f"{s.symbol} players"):
        body = players(s.symbol, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Players")


def v_trials(subjects):
    s = subjects[0]
    if not s.is_company:
        print_error(f"trials searches ClinicalTrials.gov by sponsor (this is a {s.kind} subject).")
        return
    from src.data.clinicaltrials import clinical_trials
    with _loading(f"{s.symbol} clinical trials"):
        body = clinical_trials(s.name or s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Clinical Trials")


def v_peers(subjects):
    s = subjects[0]
    if s.kind not in ("equity", "etf"):
        print_error("peers works on stocks and ETFs.")
        return
    from src.data.markets_ref import peers
    with _loading(f"{s.symbol} peers"):
        body = peers(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Peers")


def v_governance(subjects):
    s = subjects[0]
    if s.kind not in ("crypto", "chain", "protocol"):
        print_error("governance (Snapshot DAO votes) works on crypto, chains, and protocols.")
        return
    from src.data.snapshot import governance
    token = s.ref if s.kind in ("chain", "protocol") else s.symbol
    with _loading(f"{s.symbol} governance"):
        body = governance(token, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Governance")


def v_funding(subjects):
    s = subjects[0]
    if s.kind != "crypto":
        print_error("funding (perp funding rates) works on crypto subjects.")
        return
    from src.data.perps import funding
    with _loading(f"{s.symbol} funding"):
        body = funding(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Funding")


def v_cex(subjects):
    s = subjects[0]
    if s.kind != "crypto":
        print_error("cex (cross-exchange price) works on crypto subjects.")
        return
    from src.data.cex import price_board
    with _loading(f"{s.symbol} cross-exchange"):
        body = price_board(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Cross-Exchange")


def v_dexpairs(subjects):
    s = subjects[0]
    if s.kind not in ("crypto", "chain", "protocol"):
        print_error("dexpairs (DEX trading pairs) works on crypto, chains, and protocols.")
        return
    from src.data.cex import dex_pairs
    with _loading(f"{s.symbol} dex pairs"):
        body = dex_pairs(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  DEX Pairs")


def v_archive(subjects):
    s = subjects[0]
    if not s.is_company:
        print_error(f"archive looks up a company website (this is a {s.kind} subject).")
        return
    from src.data.equities import get_profile
    from src.data.dev import web_archive
    import re
    with _loading(f"{s.symbol} web archive"):
        prof = get_profile(s.symbol)
        m = re.search(r"(https?://[^\s]+)", prof or "")
        domain = m.group(1) if m else (s.name or s.symbol)
        body = web_archive(domain)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Web Archive")


def v_stackoverflow(subjects):
    s = subjects[0]
    if s.kind not in ("equity", "etf", "topic"):
        print_error("stackoverflow (dev mindshare) works on companies and topics.")
        return
    from src.data.dev import stack_overflow
    with _loading(f"{s.symbol} stack overflow"):
        body = stack_overflow(s.name or s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Stack Overflow")


def v_cryptovol(subjects):
    s = subjects[0]
    if s.kind != "crypto":
        print_error("cryptovol (DVOL implied vol) works on crypto subjects.")
        return
    from src.data.deribit import dvol
    with _loading(f"{s.symbol} implied vol"):
        body = dvol(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Implied Vol")


def v_cotfin(subjects):
    s = subjects[0]
    from src.data.cftc import cot_supported, get_cotfin
    if s.kind not in ("index", "fx") or not cot_supported(s.symbol):
        print_error("cotfin (financial-futures positioning) covers major index "
                    "and FX futures — e.g. SPX, NDX, EURUSD, USDJPY.")
        return
    with _loading(f"{s.symbol} fin positioning"):
        body = get_cotfin(s.symbol, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  TFF Positioning")


def v_constituents(subjects):
    s = subjects[0]
    if s.kind != "index":
        print_error("constituents lists members of an equity index (S&P 500, Nasdaq-100, Dow).")
        return
    from src.data.markets_ref import constituents
    with _loading(f"{s.symbol} constituents"):
        body = constituents(s.symbol, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Constituents")


def v_carry(subjects):
    s = subjects[0]
    if s.kind != "fx":
        print_error("carry needs an FX pair (e.g. EURUSD).")
        return
    from src.data.macro import carry
    with _loading(f"{s.symbol} carry"):
        body = carry(s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Carry")


def v_recession(subjects):
    from src.data.macro import recession_signal
    with _loading("recession signal"):
        body = recession_signal()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Recession Signal")


_WEATHER_REGIONS = {
    "WHEAT": (39.0, -98.0, "US Plains"), "CORN": (41.5, -93.5, "US Corn Belt"),
    "SOYBEAN": (40.0, -89.0, "US Midwest"), "COFFEE": (-21.0, -47.0, "Brazil (Minas)"),
    "SUGAR": (-21.0, -48.0, "Brazil (São Paulo)"), "COCOA": (6.8, -5.3, "Côte d'Ivoire"),
    "COTTON": (33.0, -101.0, "US Cotton Belt"), "NATGAS": (40.0, -90.0, "US Midwest (HDD)"),
    "OJ": (28.0, -81.5, "Florida"),
}


def v_weather(subjects):
    s = subjects[0]
    from src.data.weather import region_forecast, geocode
    # Commodity → its key growing/demand region; country → its capital/centroid.
    if s.kind == "commodity":
        spec = _WEATHER_REGIONS.get(s.symbol)
        if not spec:
            print_error("weather covers key growing/demand regions for: " +
                        ", ".join(_WEATHER_REGIONS) + " — or load a country.")
            return
        lat, lon, region = spec
    elif s.kind == "country":
        loc = geocode(s.name)
        if not loc:
            print_error(f"Couldn't locate {s.name} for a forecast.")
            return
        lat, lon, region = loc[0], loc[1], loc[2]
    else:
        print_error(f"weather works on commodities and countries (this is a {s.kind} subject).")
        return
    with _loading(f"{s.symbol} weather"):
        body = region_forecast(lat, lon, region, "" if s.kind == "country" else s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Weather")


def v_gtrends(subjects):
    s = subjects[0]
    from src.data.trends import google_trends
    with _loading(f"{s.symbol} search interest"):
        body = google_trends(s.name or s.symbol, s.name or s.symbol)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Search Interest")


def v_cot(subjects):
    s = subjects[0]
    from src.data.cftc import cot_supported, get_cot
    if not cot_supported(s.symbol):
        print_error("cot (CFTC positioning) covers major futures — commodities "
                    "(GOLD, OIL, CORN…), FX (EURUSD…), and index (SPX, VIX). "
                    f"No mapping for {s.symbol}.")
        return
    with _loading(f"{s.symbol} positioning"):
        body = get_cot(s.symbol, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  CoT Positioning")


def v_unemployment(subjects):
    from src.data.worldbank import unemployment
    _country_verb(subjects, unemployment, "Unemployment")


def v_population(subjects):
    from src.data.worldbank import population
    _country_verb(subjects, population, "Population")


def v_reserves(subjects):
    from src.data.worldbank import reserves
    _country_verb(subjects, reserves, "Reserves")


def v_co2(subjects):
    from src.data.worldbank import co2
    _country_verb(subjects, co2, "Emissions")


def v_military(subjects):
    from src.data.worldbank import military
    _country_verb(subjects, military, "Military")


def v_health(subjects):
    from src.data.worldbank import health
    _country_verb(subjects, health, "Health")


def v_imf(subjects):
    s = subjects[0]
    if s.kind != "country":
        print_error("imf (World Economic Outlook) needs a country.")
        return
    from src.data.intl import imf_outlook
    with _loading(f"{s.symbol} imf outlook"):
        body = imf_outlook(s.ref, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  IMF Outlook")


def v_who(subjects):
    s = subjects[0]
    if s.kind != "country":
        print_error("who (WHO health indicators) needs a country.")
        return
    from src.data.intl import who_health
    with _loading(f"{s.symbol} who health"):
        body = who_health(s.ref, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  WHO Health")


def v_corruption(subjects):
    s = subjects[0]
    if s.kind != "country":
        print_error("corruption (governance index) needs a country.")
        return
    from src.data.owid import corruption
    with _loading(f"{s.symbol} corruption"):
        body = corruption(s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Corruption")


def v_market(subjects):
    s = subjects[0]
    if s.kind != "country":
        print_error("market shows a country's benchmark equity index — load a country.")
        return
    from src.data.worldbank import COUNTRY_INDEX
    from src.data.equities import get_simple_quote
    spec = COUNTRY_INDEX.get(s.ref)
    if not spec:
        print_error(f"No benchmark index mapped for {s.name}.")
        return
    yf_sym, idx_name = spec
    with _loading(f"{s.symbol} market"):
        body = get_simple_quote(yf_sym, idx_name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  {idx_name}")


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
            r = requests.get("https://api.frankfurter.dev/v1/latest",
                             params={"amount": amt, "from": frm, "to": to}, timeout=10)
            r.raise_for_status()
            data = r.json()
        rate = (data.get("rates") or {}).get(to)
        src = "ECB"
        date = data.get("date", "")
        if rate is None:
            # Fallback chain across independent no-key FX providers.
            for url, extract, label in (
                (f"https://open.er-api.com/v6/latest/{frm}", lambda j: (j.get("rates") or {}).get(to), "exchangerate-api"),
                (f"https://api.fxratesapi.com/latest?base={frm}", lambda j: (j.get("rates") or {}).get(to), "fxratesapi"),
                (f"https://api.vatcomply.com/rates?base={frm}", lambda j: (j.get("rates") or {}).get(to), "vatcomply"),
                (f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{frm.lower()}.json",
                 lambda j: (j.get(frm.lower()) or {}).get(to.lower()), "currency-api"),
            ):
                try:
                    unit = extract(requests.get(url, timeout=10).json())
                    if unit:
                        rate, src, date = unit * amt, label, "live"
                        break
                except Exception:
                    continue
        if rate is None:
            print_error(f"Couldn't convert {frm}→{to}. Use ISO currency codes (USD, EUR, JPY…).")
            return
        body = (f"  {amt:,.2f} {frm}  =  {rate:,.2f} {to}\n\n"
                f"  [{MUTE}]rate 1 {frm} = {rate/amt:.4f} {to}   ·   "
                f"{escape(str(date))}   ·   {src}[/]")
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


def v_usdebt(subjects):
    from src.data.macro import get_national_debt
    with _loading("us national debt"):
        body = get_national_debt()
    _show(f"[{WHITE}]{escape(body)}[/]", title="US National Debt")


def v_refrates(subjects):
    from src.data.rates import get_reference_rates
    with _loading("reference rates"):
        body = get_reference_rates()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Money-Market Reference Rates")


def v_stress(subjects):
    from src.data.risk import financial_stress
    with _loading("financial stress index"):
        body = financial_stress()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Financial Stress Index")


def v_onchain(subjects):
    from src.data.crypto import get_btc_network
    with _loading("bitcoin network"):
        body = get_btc_network()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Bitcoin Network")


def v_trending(subjects):
    from src.data.crypto import get_trending
    with _loading("trending coins"):
        body = get_trending()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Trending Coins")


def v_pools(subjects):
    from src.data.defillama import top_pools
    with _loading("defi yield pools"):
        body = top_pools()
    _show(f"[{WHITE}]{escape(body)}[/]", title="DeFi Yield Pools")


def v_dexs(subjects):
    from src.data.defillama import dex_volumes
    with _loading("dex volumes"):
        body = dex_volumes()
    _show(f"[{WHITE}]{escape(body)}[/]", title="DEX Volumes")


def v_fees(subjects):
    # Target-aware: a loaded protocol → that protocol's fees; else the top board.
    proto = next((s for s in subjects if s.kind == "protocol"), None)
    if proto:
        from src.data.defillama import protocol_fee_detail
        with _loading(f"{proto.symbol} fees"):
            body = protocol_fee_detail(proto.ref, proto.name)
        _show(f"[{WHITE}]{escape(body)}[/]", title=f"{proto.symbol}  ›  Fees")
        return
    from src.data.defillama import protocol_fees
    with _loading("protocol fees"):
        body = protocol_fees()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Protocol Fees")


def v_chains(subjects):
    from src.data.defillama import top_chains
    with _loading("chains by tvl"):
        body = top_chains()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Chains by TVL")


def v_auctions(subjects):
    from src.data.macro import treasury_auctions
    with _loading("treasury auctions"):
        body = treasury_auctions()
    _show(f"[{WHITE}]{escape(body)}[/]", title="US Treasury Auctions")


def v_budget(subjects):
    from src.data.macro import federal_budget
    with _loading("federal budget"):
        body = federal_budget()
    _show(f"[{WHITE}]{escape(body)}[/]", title="US Federal Budget")


def v_hacks(subjects):
    from src.data.defillama import defi_hacks
    with _loading("crypto hacks"):
        body = defi_hacks()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Crypto Hacks")


def v_treasuries(subjects):
    """Public-company crypto treasuries — ETH if an ETH subject is loaded, else BTC."""
    coin = "ethereum" if any(s.symbol == "ETH" for s in subjects) else "bitcoin"
    from src.data.crypto import get_treasuries
    with _loading("corporate treasuries"):
        body = get_treasuries(coin)
    _show(f"[{WHITE}]{escape(body)}[/]", title="Corporate Crypto Treasuries")


def v_congress(subjects):
    from src.data.govalt import congress_trades
    with _loading("congressional trades"):
        body = congress_trades()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Congressional Trades")


def v_disasters(subjects):
    from src.data.risk import disaster_declarations
    with _loading("disaster declarations"):
        body = disaster_declarations()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Disaster Declarations")


def v_politics(subjects):
    from src.data.alt import get_politics
    with _loading("political markets"):
        body = get_politics()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Political Markets")


def v_exchanges(subjects):
    from src.data.crypto import get_exchanges
    with _loading("crypto exchanges"):
        body = get_exchanges()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Crypto Exchanges")


def v_categories(subjects):
    from src.data.crypto import get_categories
    with _loading("crypto sectors"):
        body = get_categories()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Crypto Sectors")


def v_credit(subjects):
    from src.data.macro import credit_spreads
    with _loading("credit spreads"):
        body = credit_spreads()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Credit Spreads")


def v_housing(subjects):
    from src.data.macro import home_prices
    with _loading("home prices"):
        body = home_prices()
    _show(f"[{WHITE}]{escape(body)}[/]", title="US Home Prices")


def v_soma(subjects):
    from src.data.rates import soma_holdings
    with _loading("fed balance sheet"):
        body = soma_holdings()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Fed Balance Sheet")


def v_hazards(subjects):
    from src.data.geo import hazards
    with _loading("natural hazards"):
        body = hazards()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Natural Hazards")


def v_flights(subjects):
    from src.data.geo import flights
    with _loading("global air traffic"):
        body = flights()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Global Air Traffic")


def _fred_dashboard(fn, label, title):
    with _loading(label):
        body = fn()
    _show(f"[{WHITE}]{escape(body)}[/]", title=title)


def v_industrial(subjects):
    from src.data.macro import industrial_production
    _fred_dashboard(industrial_production, "industrial activity", "Industrial Activity")


def v_mining(subjects):
    from src.data.macro import mining_activity
    _fred_dashboard(mining_activity, "mining activity", "Mining & Extraction")


def v_permits(subjects):
    from src.data.macro import building_permits
    _fred_dashboard(building_permits, "construction activity", "Construction Activity")


def v_claims(subjects):
    from src.data.macro import jobless_claims
    _fred_dashboard(jobless_claims, "jobless claims", "Jobless Claims")


def v_confidence(subjects):
    from src.data.macro import consumer_confidence
    _fred_dashboard(consumer_confidence, "consumer demand", "Consumer Demand")


def v_freight(subjects):
    from src.data.macro import freight_activity
    _fred_dashboard(freight_activity, "freight activity", "Freight & Logistics")


def v_shortages(subjects):
    """FDA drug shortages — filtered to a loaded pharma company, else the current list."""
    company = next((s.name for s in subjects if s.is_company), "")
    from src.data.openfda import drug_shortages
    with _loading("drug shortages"):
        body = drug_shortages(company)
    _show(f"[{WHITE}]{escape(body)}[/]", title="FDA Drug Shortages")


def v_water(subjects):
    from src.data.infra import river_flow
    with _loading("river flows"):
        body = river_flow()
    _show(f"[{WHITE}]{escape(body)}[/]", title="River Flows")


def v_airports(subjects):
    from src.data.infra import airport_delays
    with _loading("airport status"):
        body = airport_delays()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Airport Status")


def v_alerts(subjects):
    from src.data.infra import weather_alerts
    with _loading("weather alerts"):
        body = weather_alerts()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Weather Alerts")


def v_travel(subjects):
    from src.data.infra import tsa_travel
    with _loading("tsa throughput"):
        body = tsa_travel()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Air-Travel Demand")


def v_ecb(subjects):
    from src.data.intl import ecb_rates
    with _loading("ecb rates"):
        body = ecb_rates()
    _show(f"[{WHITE}]{escape(body)}[/]", title="ECB Rates & FX")


def v_spaceweather(subjects):
    from src.data.science import space_weather
    with _loading("space weather"):
        body = space_weather()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Space Weather")


def v_hurricanes(subjects):
    from src.data.science import hurricanes
    with _loading("tropical cyclones"):
        body = hurricanes()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Tropical Cyclones")


def v_tides(subjects):
    from src.data.science import port_tides
    with _loading("port tides"):
        body = port_tides()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Port Water Levels")


def v_gridcarbon(subjects):
    from src.data.science import grid_carbon
    with _loading("grid carbon"):
        body = grid_carbon()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Grid Carbon Intensity")


def _global_verb(fn_path, label, title):
    mod, fn = fn_path
    with _loading(label):
        body = getattr(__import__("src.data." + mod, fromlist=[fn]), fn)()
    _show(f"[{WHITE}]{escape(body)}[/]", title=title)


def v_btcchain(subjects):
    _global_verb(("cryptox", "btc_chain"), "bitcoin chain", "Bitcoin Chain")


def v_ethsupply(subjects):
    _global_verb(("cryptox", "eth_issuance"), "eth supply", "Ethereum Supply")


def v_kfutures(subjects):
    _global_verb(("cryptox", "kraken_futures_oi"), "kraken futures", "Kraken Futures OI")


def v_citypermits(subjects):
    _global_verb(("citydata", "local_permits"), "city permits", "City Building Permits")


def v_disease(subjects):
    _global_verb(("citydata", "respiratory_surveillance"), "disease surveillance", "Respiratory Surveillance")


def v_medicare(subjects):
    _global_verb(("citydata", "medicare_overview"), "medicare data", "CMS Medicare")


def v_eurostat(subjects):
    _global_verb(("intl", "eurostat_indicators"), "eurostat", "Euro-Area Indicators")


def v_volcanoes(subjects):
    _global_verb(("science", "volcanoes"), "volcano alerts", "Volcanic Activity")


def v_buoys(subjects):
    _global_verb(("science", "ocean_buoys"), "ocean buoys", "Offshore Conditions")


def v_neo(subjects):
    _global_verb(("science", "near_earth_objects"), "near-earth objects", "Near-Earth Objects")


def v_biodiversity(subjects):
    s = subjects[0]
    if s.kind != "country":
        print_error("biodiversity works on a country (GBIF per-country records).")
        return
    from src.data.science import biodiversity
    with _loading(f"{s.symbol} biodiversity"):
        body = biodiversity(s.ref, s.name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"{s.symbol}  ›  Biodiversity")


def v_sports(subjects):
    _global_verb(("dev", "sports_leagues"), "sports leagues", "Sports Leagues")


def v_forecasts(args):
    """Manifold community forecasts (no target needed); an optional word filters
    by topic — e.g. [white]forecasts recession[/]."""
    topic = " ".join(args).strip() if args else ""
    from src.data.alt import get_forecasts
    with _loading("community forecasts"):
        body = get_forecasts(topic)
    title = "Forecasts" + (f"  ›  {topic.title()}" if topic else "")
    _show(f"[{WHITE}]{escape(body)}[/]", title=title)


def v_ipos(subjects):
    from src.data.gov import recent_ipos
    with _loading("ipo pipeline"):
        body = recent_ipos()
    _show(f"[{WHITE}]{escape(body)}[/]", title="IPO Pipeline")


def v_holidays(subjects):
    """Public-holiday calendar — for a loaded country, else the US."""
    iso, name = "US", "United States"
    for s in subjects:
        if s.kind == "country":
            iso, name = s.ref, s.name
            break
    from src.data.calendars import public_holidays
    with _loading(f"{name} holidays"):
        body = public_holidays(iso, name)
    _show(f"[{WHITE}]{escape(body)}[/]", title=f"Holidays  ›  {name}")


def v_bigmac(subjects):
    """Big Mac Index — for a loaded FX pair, else the global table."""
    fx = next((s.symbol for s in subjects if s.kind == "fx"), "")
    from src.data.macro import big_mac
    with _loading("big mac index"):
        body = big_mac(fx)
    _show(f"[{WHITE}]{escape(body)}[/]", title="Big Mac Index")


def v_predictions(args):
    """Polymarket prediction markets (no target needed). An optional word filters
    by topic — e.g. [white]predictions election[/]."""
    topic = " ".join(args).strip() if args else ""
    from src.data.alt import get_prediction_markets
    with _loading("prediction markets"):
        body = get_prediction_markets(topic)
    title = "Prediction Markets" + (f"  ›  {topic.title()}" if topic else "")
    _show(f"[{WHITE}]{escape(body)}[/]", title=title)


def v_dominance(subjects):
    from src.data.crypto import get_global_dominance
    with _loading("market dominance"):
        body = get_global_dominance()
    _show(f"[{WHITE}]{escape(body)}[/]", title="Crypto Market Dominance")


def v_coins(subjects):
    from src.data.crypto import top_coins_rows
    from src.display import make_table, delta
    with _loading("top coins"):
        rows = top_coins_rows(15)
    if not rows:
        print_error("Couldn't fetch top coins right now.")
        return
    tbl = make_table(
        ["#", "Coin", "Price", "24h", "7d", "Market Cap", "Volume"],
        [(f"[#6b7280]{r}[/]", f"[bold]{sym}[/]", price, delta(c24), delta(c7), mc, vol)
         for r, sym, price, c24, c7, mc, vol in rows],
        justify=["right", "left", "right", "right", "right", "right", "right"])
    _show(tbl, title="Top Coins  ·  CoinGecko")


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


# Braille dot bit values — [sub-row 0=top..3][sub-col 0=left,1=right].
_BRAILLE = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]


def _braille_chart(label: str, closes: list, range_label: str):
    """A smooth line chart at 2×4 braille resolution, with a y-axis and trend color."""
    first, last = closes[0], closes[-1]
    chg   = (last / first - 1) * 100 if first else 0
    color = GREEN if last >= first else RED
    cells_w = _chart_cols(11)
    sub_w   = cells_w * 2
    vals    = _fit(closes, sub_w)
    H       = 9                                   # character rows
    sub_h   = H * 4
    lo, hi  = min(vals), max(vals)
    rng     = (hi - lo) or 1

    grid = [[0] * cells_w for _ in range(H)]
    prev = None
    for x, v in enumerate(vals):
        y = int((v - lo) / rng * (sub_h - 1))     # 0 = bottom
        span = (y,) if prev is None else range(min(prev, y), max(prev, y) + 1)
        for yy in span:
            row_top = (sub_h - 1 - yy) // 4
            col     = x // 2
            if 0 <= row_top < H and 0 <= col < cells_w:
                grid[row_top][col] |= _BRAILLE[(sub_h - 1 - yy) % 4][x % 2]
        prev = y

    def axis(r):                                  # value at the top of character row r
        return lo + (1 - r / H) * rng
    rows = []
    for r in range(H):
        glyphs = "".join(chr(0x2800 + grid[r][c]) for c in range(cells_w))
        lbl = f"{axis(r):>9,.2f}" if r in (0, H // 2, H - 1) else " " * 9
        rows.append(f"[{MUTE}]{lbl}[/] [{MUTE}]│[/][{color}]{glyphs}[/]")
    foot = (f"{'':>10}[{MUTE}]└{'─' * cells_w}[/]\n"
            f"{'':>11}[{MUTE}]◄ {range_label}[/]"
            f"{'':>{max(1, cells_w - len(range_label) - len(f'{chg:+.1f}%') - 2)}}"
            f"[{color}]{chg:+.1f}%[/]")
    _show("\n".join(rows) + "\n" + foot, title=f"{label}  ›  Chart  ({range_label})")


# kept name for callers
def _single_chart(label: str, closes: list, range_label: str):
    _braille_chart(label, closes, range_label)


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
