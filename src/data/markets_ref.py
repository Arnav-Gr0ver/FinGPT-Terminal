"""Reference market structure — peers and index constituents (free, no key).

Peer companies come from Yahoo's "people also watch" recommendation graph
(via yahooquery); index membership is read from the maintained Wikipedia tables
(via pandas.read_html)."""


def peers(symbol: str) -> str:
    """Companies most co-watched with this one, with a live quote for each."""
    try:
        from yahooquery import Ticker
        rec = Ticker(symbol).recommendations
        block = rec.get(symbol) if isinstance(rec, dict) else None
        syms = [r["symbol"] for r in (block or {}).get("recommendedSymbols", [])] if block else []
    except Exception as e:
        return f"Could not fetch peers for {symbol}: {e}"
    if not syms:
        return f"No peer companies found for {symbol}."

    quotes = {}
    try:
        from yahooquery import Ticker
        p = Ticker(syms).price
        if isinstance(p, dict):
            quotes = p
    except Exception:
        quotes = {}

    out = [
        f"Peers — companies co-watched with {symbol}",
        "Source: Yahoo Finance recommendation graph",
        "",
        f"  {'Ticker':<8}{'Price':>12}{'24h':>9}  Name",
        "  " + "─" * 54,
    ]
    for s in syms:
        q = quotes.get(s, {}) if isinstance(quotes.get(s), dict) else {}
        price = q.get("regularMarketPrice")
        chg = q.get("regularMarketChangePercent")
        name = (q.get("shortName") or "")[:26]
        price_s = f"${price:,.2f}" if isinstance(price, (int, float)) else "—"
        chg_s = f"{chg*100:+.2f}%" if isinstance(chg, (int, float)) else "—"
        out.append(f"  {s:<8}{price_s:>12}{chg_s:>9}  {name}")
    return "\n".join(out)


# Index subject symbol → (Wikipedia page, ticker column, name column).
_INDEX_WIKI = {
    "SPX": ("List_of_S%26P_500_companies", "Symbol", "Security"),
    "SP500": ("List_of_S%26P_500_companies", "Symbol", "Security"),
    "NDX": ("Nasdaq-100", "Ticker", "Company"),
    "NASDAQ": ("Nasdaq-100", "Ticker", "Company"),
    "DJIA": ("Dow_Jones_Industrial_Average", "Symbol", "Company"),
}


def constituents(index_symbol: str, name: str = "") -> str:
    """Members of a major equity index, read from Wikipedia's maintained table."""
    spec = _INDEX_WIKI.get(index_symbol.upper())
    if not spec:
        return (f"Constituent lists are available for the S&P 500, Nasdaq-100, "
                f"and Dow ({name or index_symbol} not covered).")
    page, tcol, ncol = spec
    try:
        import io
        import pandas as pd
        from src.data.http import get
        html = get(f"https://en.wikipedia.org/wiki/{page}", timeout=20).text
        tables = pd.read_html(io.StringIO(html))
    except Exception as e:
        return f"Could not fetch constituents: {e}"

    df = None
    for t in tables:
        cols = [str(c) for c in t.columns]
        if tcol in cols and ncol in cols:
            df = t
            break
    if df is None:
        return f"Couldn't parse the constituent table for {name or index_symbol}."

    rows = df[[tcol, ncol]].dropna().values.tolist()
    out = [
        f"{name or index_symbol} — Constituents ({len(rows)} members)",
        "Source: Wikipedia",
        "",
    ]
    line = "  "
    for tkr, _nm in rows:
        cell = f"{str(tkr).replace('.', '-'):<7}"
        if len(line) + len(cell) > 70:
            out.append(line.rstrip())
            line = "  "
        line += cell
    if line.strip():
        out.append(line.rstrip())
    out += ["", "  Load any ticker above to research it."]
    return "\n".join(out)
