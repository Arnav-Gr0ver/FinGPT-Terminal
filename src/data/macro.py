"""Macro data — FRED public CSV API + yfinance Treasury yields."""

import csv
import io
import requests
from datetime import datetime, timedelta

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
HEADERS  = {"User-Agent": "FinGPT-Terminal/0.1.0"}


def _fred(series: str, limit: int = 12) -> list[tuple[str, float]]:
    """Fetch the last `limit` observations from a FRED series as [(date, value)]."""
    r = requests.get(FRED_CSV, params={"id": series}, headers=HEADERS, timeout=10)
    r.raise_for_status()
    reader = csv.reader(io.StringIO(r.text))
    next(reader)  # skip header
    rows = []
    for date_s, val_s in reader:
        try:
            rows.append((date_s, float(val_s)))
        except ValueError:
            pass
    return rows[-limit:]


# Friendly macro subjects → (FRED id, display name, unit). These load as nouns:
# `CPI` then `chart 2y` works exactly like `NVDA chart 2y`.
MACRO_SERIES: dict[str, tuple[str, str, str]] = {
    "CPI":      ("CPIAUCSL",         "Consumer Price Index",        "index"),
    "CORECPI":  ("CPILFESL",         "Core CPI",                    "index"),
    "PCE":      ("PCEPI",            "PCE Price Index",             "index"),
    "GDP":      ("GDPC1",            "Real GDP",                    "$B"),
    "UNRATE":   ("UNRATE",           "Unemployment Rate",           "%"),
    "PAYROLLS": ("PAYEMS",           "Nonfarm Payrolls",            "thousands"),
    "FEDFUNDS": ("DFF",              "Federal Funds Rate",          "%"),
    "DGS2":     ("DGS2",             "2-Year Treasury Yield",       "%"),
    "DGS10":    ("DGS10",            "10-Year Treasury Yield",      "%"),
    "DGS30":    ("DGS30",            "30-Year Treasury Yield",      "%"),
    "M2":       ("M2SL",             "M2 Money Supply",             "$B"),
    "PPI":      ("PPIACO",           "Producer Price Index",        "index"),
    "RETAIL":   ("RSXFS",            "Retail Sales",                "$M"),
    "HOUSING":  ("HOUST",            "Housing Starts",              "thousands"),
    "SENTIMENT":("UMCSENT",          "U. Michigan Consumer Sentiment","index"),
    "CLAIMS":   ("ICSA",             "Initial Jobless Claims",      "claims"),
    "INDPRO":   ("INDPRO",           "Industrial Production",       "index"),
    "T10Y2Y":   ("T10Y2Y",           "10Y–2Y Treasury Spread",      "%"),
    "T10Y3M":   ("T10Y3M",           "10Y–3M Treasury Spread",      "%"),
    "REALRATE": ("DFII10",           "10Y Real Treasury Yield",     "%"),
    "MORTGAGE": ("MORTGAGE30US",     "30-Year Mortgage Rate",       "%"),
    "DXYIDX":   ("DTWEXBGS",         "Broad US Dollar Index",       "index"),
    "WTI":      ("DCOILWTICO",       "WTI Crude Oil Price",         "$"),
    "VIXLVL":   ("VIXCLS",           "CBOE VIX (FRED)",             "index"),
    "DEBT":     ("GFDEBTN",          "US Federal Debt",             "$M"),
}


def resolve_macro(token: str) -> tuple[str, str, str] | None:
    """Map a token to (fred_id, name, unit). Accepts a friendly alias or a raw
    FRED series id. Returns None if the token isn't a macro subject."""
    key = token.upper().strip()
    if key in MACRO_SERIES:
        return MACRO_SERIES[key]
    # Raw FRED id: validate by fetching one observation.
    if len(key) >= 5 and key.isalnum():
        try:
            if _fred(key, limit=1):
                return (key, key, "")
        except Exception:
            pass
    return None


# Range token → calendar days back. Frequency-agnostic: we filter FRED
# observations by date, so a quarterly series and a daily one both honor "5y".
_RANGE_DAYS = {
    "1d": 2, "5d": 7, "1mo": 31, "3mo": 93, "6mo": 186,
    "1y": 366, "2y": 731, "5y": 1827, "10y": 3653,
}


def get_series(fred_id: str, period: str = "1y") -> list[tuple[str, float]]:
    """Fetch (date, value) observations within `period` for charting a macro
    subject. `ytd` is year-to-date; `max` is the full series."""
    try:
        rows = _fred(fred_id, limit=10_000_000)  # all available observations
    except Exception:
        return []
    if period == "max":
        return rows
    if period == "ytd":
        cutoff = datetime(datetime.now().year, 1, 1)
    else:
        cutoff = datetime.now() - timedelta(days=_RANGE_DAYS.get(period, 366))
    out = []
    for d, v in rows:
        try:
            if datetime.strptime(d, "%Y-%m-%d") >= cutoff:
                out.append((d, v))
        except ValueError:
            pass
    return out or rows[-12:]


def get_macro_snapshot(fred_id: str, name: str, unit: str) -> str:
    """One-screen latest reading + recent trend for a macro subject's `price` verb."""
    rows = get_series(fred_id, "1y")
    if not rows:
        return f"No data available for {name} ({fred_id})."
    latest_d, latest_v = rows[-1]
    prev_v             = rows[-2][1] if len(rows) > 1 else None
    chg                = (latest_v - prev_v) if prev_v is not None else None

    def _fmt(v):
        if unit == "%":
            return f"{v:.2f}%"
        if unit in ("$B", "$M"):
            return f"{v:,.1f}{unit[-1]}"
        return f"{v:,.2f}"

    w     = 18
    lines = [f"{name}  ({fred_id})", "Source: FRED", "",
             f"  {'Latest':<{w}} {_fmt(latest_v)}",
             f"  {'As of':<{w}} {latest_d}"]
    if chg is not None:
        arrow = "▲" if chg >= 0 else "▼"
        lines.append(f"  {'Change':<{w}} {chg:+.2f}  {arrow}")
    # 12-period change
    if len(rows) >= 13:
        yago = rows[-13][1]
        if yago:
            yoy = (latest_v - yago) / yago * 100
            lines.append(f"  {'~1y change':<{w}} {yoy:+.1f}%")
    return "\n".join(lines)


def _yf_last(ticker: str) -> float | None:
    """Get the most recent closing price for a yfinance ticker."""
    import yfinance as yf
    try:
        df = yf.Ticker(ticker).history(period="5d")
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    except Exception:
        return None


def get_overview() -> dict:
    """Compact macro snapshot for the `macro` feed: fed funds, 2s10s, CPI YoY, GDP."""
    snap = {"fed": None, "y2": None, "y10": None, "spread": None,
            "cpi_yoy": None, "gdp": None, "gdp_q": None}
    try:
        rows = _fred("DFF", limit=1)
        snap["fed"] = rows[-1][1] if rows else None
    except Exception:
        pass
    try:
        y2  = _fred("DGS2", limit=5)
        y10 = _fred("DGS10", limit=5)
        v2  = next((v for _, v in reversed(y2) if v == v), None)
        v10 = next((v for _, v in reversed(y10) if v == v), None)
        snap["y2"], snap["y10"] = v2, v10
        if v2 is not None and v10 is not None:
            snap["spread"] = v10 - v2
    except Exception:
        pass
    try:
        cpi = _fred("CPIAUCSL", limit=13)
        if len(cpi) >= 13:
            snap["cpi_yoy"] = (cpi[-1][1] - cpi[-13][1]) / cpi[-13][1] * 100
    except Exception:
        pass
    try:
        g = _fred("A191RL1Q225SBEA", limit=1)
        if g:
            date_s, val = g[-1]
            dt = datetime.strptime(date_s, "%Y-%m-%d")
            snap["gdp"], snap["gdp_q"] = val, f"Q{(dt.month - 1)//3 + 1} {dt.year}"
    except Exception:
        pass
    return snap


def get_rates() -> str:
    """Central bank policy rates from FRED public series."""
    sources = [
        ("US Fed Funds",    "DFF"),
        ("ECB Deposit",     "ECBDFR"),
        ("Bank of England", "IRSTCB01GBM156N"),
        ("Bank of Japan",   "IRSTJPM193N"),
        ("Bank of Canada",  "IRSTCB01CAM156N"),
        ("RBA Australia",   "IRSTCB01AUM156N"),
        ("SNB Switzerland", "IRSTCB01CHM156N"),
    ]

    cutoff = datetime.utcnow() - timedelta(days=180)
    w      = 22
    lines  = [
        "Central Bank Policy Rates",
        "Source: FRED (Federal Reserve Economic Data)",
        "",
        f"  {'Central Bank':<{w}} {'Rate':>6}   Last Updated",
        "  " + "─" * 52,
    ]

    for label, series in sources:
        try:
            rows = _fred(series, limit=3)
            if not rows:
                lines.append(f"  {label:<{w}} {'N/A':>6}")
                continue
            date_s, val = rows[-1]
            dt    = datetime.strptime(date_s, "%Y-%m-%d")
            stale = "  ⚠ stale" if dt < cutoff else ""
            lines.append(f"  {label:<{w}} {val:>5.2f}%   {date_s}{stale}")
        except Exception:
            lines.append(f"  {label:<{w}} {'N/A':>6}")

    lines += [
        "",
        "  ⚠ = data older than 6 months — check central bank website for current rate.",
    ]
    return "\n".join(lines)


def get_yield_curve() -> str:
    """US Treasury yield curve from FRED daily series."""
    maturities = [
        ("1 Month",  "DGS1MO"),
        ("3 Month",  "DGS3MO"),
        ("6 Month",  "DGS6MO"),
        ("1 Year",   "DGS1"),
        ("2 Year",   "DGS2"),
        ("5 Year",   "DGS5"),
        ("10 Year",  "DGS10"),
        ("30 Year",  "DGS30"),
    ]

    yields = {}
    latest_date = ""
    for label, series in maturities:
        try:
            rows = _fred(series, limit=5)
            # find the most recent non-null value
            for date_s, val in reversed(rows):
                if val and val == val:
                    yields[label] = val
                    if not latest_date:
                        latest_date = date_s
                    break
        except Exception:
            pass

    if not yields:
        return "Could not fetch yield curve data."

    # Inversion check: 10Y vs 2Y and 10Y vs 3M
    y10  = yields.get("10 Year")
    y2   = yields.get("2 Year")
    y3m  = yields.get("3 Month")
    inv_2_10  = (y2 and y10 and y2 > y10)
    inv_3m_10 = (y3m and y10 and y3m > y10)

    bar_max = max(yields.values()) if yields else 5.0
    bar_w   = 30

    lines = [
        f"US Treasury Yield Curve  [{latest_date}]",
        "",
        f"  {'Maturity':<12} {'Yield':>7}   Chart",
        "  " + "─" * 55,
    ]

    for label, _ in maturities:
        if label not in yields:
            continue
        y   = yields[label]
        bar = "█" * int(y / bar_max * bar_w)
        lines.append(f"  {label:<12} {y:>6.2f}%   {bar}")

    lines.append("")
    if inv_3m_10 and inv_2_10:
        lines.append("  ⚠  INVERTED: 3M > 10Y and 2Y > 10Y — historically a recession signal")
    elif inv_3m_10:
        lines.append("  ⚠  INVERTED: 3-Month yield above 10-Year")
    elif inv_2_10:
        lines.append("  ⚠  INVERTED: 2-Year yield above 10-Year")
    else:
        spread = (y10 - y3m) if (y10 and y3m) else None
        if spread:
            lines.append(f"  Normal curve  |  10Y-3M spread: {spread:+.2f}%")

    return "\n".join(lines)


def get_inflation() -> str:
    """US CPI (All Urban Consumers) — last 12 months from FRED."""
    try:
        rows = _fred("CPIAUCSL", limit=25)
        if not rows:
            return "Could not fetch CPI data."

        lines = [
            "US CPI — Consumer Price Index  (All Urban Consumers, SA)",
            "Source: FRED / BLS",
            "",
            f"  {'Month':<14} {'CPI Level':>10} {'MoM':>8} {'YoY':>8}",
            "  " + "─" * 44,
        ]

        # Show last 12 months with YoY computed from -12 months back
        display = rows[-13:]  # 13 so we always have a prev_month for row 0
        for i in range(1, len(display)):
            date_s, val    = display[i]
            _, prev_month  = display[i - 1]
            mom = (val - prev_month) / prev_month * 100

            # YoY from the full rows array
            yoy_s = "N/A"
            # find the same month 12 entries earlier in the full dataset
            full_i = rows.index(display[i])
            if full_i >= 12:
                _, val_12m_ago = rows[full_i - 12]
                yoy = (val - val_12m_ago) / val_12m_ago * 100
                yoy_s = f"{yoy:+.2f}%"

            dt    = datetime.strptime(date_s, "%Y-%m-%d")
            month = dt.strftime("%b %Y")
            mom_s = f"{mom:+.2f}%"
            lines.append(f"  {month:<14} {val:>10.1f} {mom_s:>8} {yoy_s:>8}")

        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch inflation data: {e}"


def get_gdp() -> str:
    """US Real GDP — quarterly growth rate (annualized) from FRED."""
    try:
        # A191RL1Q225SBEA = Real GDP % change from preceding period, seasonally adjusted, annualized rate
        rows = _fred("A191RL1Q225SBEA", limit=10)
        if not rows:
            return "Could not fetch GDP data."

        # Also get level for context
        level_rows = _fred("GDPC1", limit=10)
        level_map  = {d: v for d, v in level_rows}

        lines = [
            "US Real GDP Growth  (Quarterly, Annualized % Change)",
            "Source: FRED / BEA",
            "",
            f"  {'Quarter':<14} {'Growth Rate':>12} {'GDP Level (B)':>16}",
            "  " + "─" * 46,
        ]

        bar_max = max(abs(v) for _, v in rows) or 1

        for date_s, rate in rows:
            dt      = datetime.strptime(date_s, "%Y-%m-%d")
            quarter = f"Q{(dt.month - 1)//3 + 1} {dt.year}"
            sign    = "+" if rate >= 0 else ""
            rate_s  = f"{sign}{rate:.1f}%"
            bar     = ("▲" if rate >= 0 else "▼") * min(int(abs(rate) / bar_max * 8), 8)
            level   = level_map.get(date_s)
            lev_s   = f"${level:,.1f}B" if level else "N/A"
            lines.append(f"  {quarter:<14} {rate_s:>12}   {bar:<10} {lev_s:>14}")

        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch GDP data: {e}"


# U.S. Treasury — "debt to the penny" via the FiscalData API (no key required).
FISCALDATA = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"


def get_national_debt() -> str:
    """US total public debt outstanding — latest level, 1M/1Y change, monthly trend.
    Source: U.S. Treasury FiscalData (open data, no API key)."""
    try:
        r = requests.get(
            f"{FISCALDATA}/v2/accounting/od/debt_to_penny",
            params={"sort": "-record_date", "page[size]": 400,
                    "fields": "record_date,tot_pub_debt_out_amt"},
            headers=HEADERS, timeout=15,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception as e:
        return f"Could not fetch national debt data: {e}"

    rows = []
    for d in data:
        try:
            rows.append((d["record_date"], float(d["tot_pub_debt_out_amt"])))
        except (KeyError, TypeError, ValueError):
            continue
    if not rows:
        return "National debt data is unavailable right now."

    def _t(v):
        return f"${v/1e12:.2f}T"

    latest_date, latest = rows[0]

    def _change(days):
        target = datetime.strptime(latest_date, "%Y-%m-%d") - timedelta(days=days)
        for dt, val in rows:                       # rows are newest-first
            if datetime.strptime(dt, "%Y-%m-%d") <= target:
                delta = latest - val
                pct   = (delta / val * 100) if val else 0
                return f"{'+' if delta >= 0 else '−'}{_t(abs(delta))}  ({pct:+.1f}%)"
        return "—"

    # One sample per calendar month, newest first.
    monthly, seen = [], set()
    for dt, val in rows:
        ym = dt[:7]
        if ym not in seen:
            seen.add(ym)
            monthly.append((dt, val))
        if len(monthly) >= 8:
            break

    avg_rate = _avg_interest_rate()

    lines = [
        "US National Debt — Total Public Debt Outstanding",
        "Source: U.S. Treasury · FiscalData (debt to the penny)",
        "",
        f"  {'Current':<12} {_t(latest):>10}   ({latest_date})",
        f"  {'1-month':<12} {_change(30):>10}",
        f"  {'1-year':<12} {_change(365):>10}",
    ]
    if avg_rate:
        rate, rate_date = avg_rate
        lines.append(f"  {'Avg rate':<12} {rate:>9.2f}%   (marketable debt, {rate_date})")
    lines += [
        "",
        "  Recent (month-end snapshots):",
        f"  {'Date':<14} {'Total Debt':>12}",
        "  " + "─" * 28,
    ]
    for dt, val in monthly:
        lines.append(f"  {dt:<14} {_t(val):>12}")
    return "\n".join(lines)


def _indicator_panel(title: str, source: str, specs: list) -> str:
    """Render a small dashboard of FRED series — latest reading vs a year ago.
    specs: [(label, fred_id, unit)]."""
    def yr_ago(rows):
        target = datetime.strptime(rows[-1][0], "%Y-%m-%d") - timedelta(days=365)
        for d, v in reversed(rows):
            if datetime.strptime(d, "%Y-%m-%d") <= target:
                return v
        return None

    lines = [title, f"Source: {source}", "",
             f"  {'Indicator':<26}{'Latest':>13}{'Year ago':>13}", "  " + "─" * 54]
    asof = ""
    found = False
    for label, fid, unit in specs:
        rows = _fred(fid, limit=420)
        if not rows:
            continue
        found = True
        d, v = rows[-1]
        asof = max(asof, d)
        ya = yr_ago(rows)

        def fmt(x):
            if x is None:
                return "—"
            return (f"{x:,.0f}{unit}" if abs(x) >= 1000 else f"{x:,.1f}{unit}")
        lines.append(f"  {label[:25]:<26}{fmt(v):>13}{fmt(ya):>13}")
    if not found:
        return f"{title} data is unavailable right now."
    lines[1] = f"Source: {source} · latest {asof}"
    return "\n".join(lines)


def industrial_production() -> str:
    return _indicator_panel(
        "US Industrial Activity", "FRED / Federal Reserve",
        [("Industrial production", "INDPRO", ""), ("Capacity utilization", "TCU", "%"),
         ("Manufacturing output", "IPMAN", ""), ("Business inventories", "ISRATIO", "x")])


def mining_activity() -> str:
    return _indicator_panel(
        "US Mining & Extraction", "FRED / Federal Reserve",
        [("Mining production", "IPMINE", ""), ("Oil & gas extraction", "IPG211S", ""),
         ("Oil & gas drilling", "IPN213111N", ""), ("Coal mining", "IPN2121S", "")])


def building_permits() -> str:
    return _indicator_panel(
        "US Construction Activity", "FRED / Census Bureau",
        [("Building permits", "PERMIT", "k"), ("Housing starts", "HOUST", "k"),
         ("Construction spend ($M)", "TTLCONS", ""), ("New home sales", "HSN1F", "k")])


def jobless_claims() -> str:
    return _indicator_panel(
        "US Labor — Jobless Claims", "FRED / Dept. of Labor",
        [("Initial claims", "ICSA", ""), ("Continued claims", "CCSA", ""),
         ("Unemployment rate", "UNRATE", "%"), ("Job openings (JOLTS)", "JTSJOL", "k")])


def consumer_confidence() -> str:
    return _indicator_panel(
        "US Consumer Demand", "FRED / U.Michigan / Census",
        [("U.Mich sentiment", "UMCSENT", ""), ("Retail sales ($M)", "RSAFS", ""),
         ("Real disposable income", "DSPIC96", ""), ("Personal saving rate", "PSAVERT", "%")])


def freight_activity() -> str:
    return _indicator_panel(
        "US Freight & Logistics", "FRED",
        [("Truck tonnage index", "TRUCKD11", ""), ("Durable-goods orders ($M)", "DGORDER", ""),
         ("Rail intermodal traffic", "RAILFRTINTERMODAL", ""), ("Wholesale inventories", "WHLSLRIRSA", "x")])


def credit_spreads() -> str:
    """Corporate-bond option-adjusted spreads (ICE BofA, via FRED) — investment-
    grade and high-yield. Widening spreads = rising credit stress."""
    ig = _fred("BAMLC0A0CM", limit=260)
    hy = _fred("BAMLH0A0HYM2", limit=260)
    if not ig:
        return "Credit-spread data is unavailable right now."

    def at(s, days):
        if not s:
            return None
        target = datetime.strptime(s[-1][0], "%Y-%m-%d") - timedelta(days=days)
        for d, v in reversed(s):
            if datetime.strptime(d, "%Y-%m-%d") <= target:
                return v
        return None

    out = ["US Corporate Credit Spreads  (option-adjusted, %)",
           f"Source: FRED · ICE BofA · {ig[-1][0]}", "",
           f"  {'':<16}{'Now':>8}{'1mo':>8}{'1yr':>8}", "  " + "─" * 40]
    for label, s in (("Investment grade", ig), ("High yield", hy)):
        if not s:
            continue
        m, y = at(s, 30), at(s, 365)
        out.append(f"  {label:<16}{s[-1][1]:>7.2f}%{(f'{m:.2f}' if m else '—'):>8}{(f'{y:.2f}' if y else '—'):>8}")
    out += ["", "  Wider = more credit stress; HY leads risk-off moves."]
    return "\n".join(out)


def home_prices() -> str:
    """US home-price trend — S&P CoreLogic Case-Shiller National Index (FRED)."""
    rows = _fred("CSUSHPINSA", limit=64)
    if not rows:
        return "Home-price data is unavailable right now."
    latest_d, latest = rows[-1]

    def chg(months):
        if len(rows) > months:
            old = rows[-1 - months][1]
            return (latest / old - 1) * 100 if old else None
        return None

    out = ["US Home Prices — Case-Shiller National Index",
           f"Source: FRED · S&P CoreLogic · index {latest:.1f} ({latest_d})", "",
           f"  {'1-month':<12}{(f'{chg(1):+.1f}%' if chg(1) is not None else '—'):>8}",
           f"  {'1-year':<12}{(f'{chg(12):+.1f}%' if chg(12) is not None else '—'):>8}",
           f"  {'5-year':<12}{(f'{chg(60):+.1f}%' if chg(60) is not None else '—'):>8}",
           "", "  Recent (index, seasonally-unadjusted):",
           f"  {'Month':<10}{'Index':>10}", "  " + "─" * 24]
    for d, v in rows[-8:][::-1]:
        out.append(f"  {d:<10}{v:>10.1f}")
    return "\n".join(out)


def recession_signal() -> str:
    """Yield-curve recession signal — the 10y–2y and 10y–3m Treasury spreads.
    A sustained inversion (negative) has preceded every recent US recession.
    Source: FRED."""
    s102 = _fred("T10Y2Y", limit=380)
    s103 = _fred("T10Y3M", limit=380)
    if not s102:
        return "Yield-curve data is unavailable right now."

    def at(series, days):
        if not series:
            return None
        target = datetime.strptime(series[-1][0], "%Y-%m-%d") - timedelta(days=days)
        for d, v in reversed(series):
            if datetime.strptime(d, "%Y-%m-%d") <= target:
                return v
        return None

    cur2, cur3 = s102[-1][1], (s103[-1][1] if s103 else None)
    inverted = cur2 < 0
    status = ("INVERTED — historically a recession warning" if inverted
              else "normal (positive slope)")
    out = [
        "Yield-Curve Recession Signal",
        f"Source: FRED · {s102[-1][0]}",
        "",
        f"  {'10y − 2y spread':<20} {cur2:>+6.2f}%   ({'inverted' if cur2 < 0 else 'normal'})",
    ]
    if cur3 is not None:
        out.append(f"  {'10y − 3m spread':<20} {cur3:>+6.2f}%   ({'inverted' if cur3 < 0 else 'normal'})")
    m1, y1 = at(s102, 30), at(s102, 365)
    out += [
        "",
        f"  {'1 month ago':<20} {(f'{m1:+.2f}%' if m1 is not None else '—'):>7}",
        f"  {'1 year ago':<20} {(f'{y1:+.2f}%' if y1 is not None else '—'):>7}",
        "",
        f"  Read: {status}.",
    ]
    return "\n".join(out)


# Currency → FRED long-term (10y) government bond yield series.
_CCY_RATE = {
    "USD": "IRLTLT01USM156N", "EUR": "IRLTLT01DEM156N", "JPY": "IRLTLT01JPM156N",
    "GBP": "IRLTLT01GBM156N", "CAD": "IRLTLT01CAM156N", "AUD": "IRLTLT01AUM156N",
    "CHF": "IRLTLT01CHM156N", "NZD": "IRLTLT01NZM156N", "SEK": "IRLTLT01SEM156N",
    "NOK": "IRLTLT01NOM156N", "KR": "IRLTLT01KRM156N", "MX": "IRLTLT01MXM156N",
}


def carry(fx_symbol: str) -> str:
    """Interest-rate (carry) differential between the two legs of an FX pair, using
    10-year government bond yields. Positive = the base currency out-yields the
    quote currency. Source: FRED."""
    sym = (fx_symbol or "").upper().replace("=X", "")
    if len(sym) != 6:
        return "carry needs a 6-letter FX pair (e.g. EURUSD)."
    base, quote = sym[:3], sym[3:]
    bs, qs = _CCY_RATE.get(base), _CCY_RATE.get(quote)
    if not bs or not qs:
        return f"No long-yield series for {base}/{quote}. Covered: " + ", ".join(_CCY_RATE)

    br = _fred(bs, limit=3)
    qr = _fred(qs, limit=3)
    if not br or not qr:
        return f"Yield data unavailable for {base} or {quote} right now."
    bv, qv = br[-1][1], qr[-1][1]
    diff = bv - qv
    lean = (f"positive carry — holding {base} earns ~{diff:.2f}% over {quote}" if diff > 0
            else f"negative carry — holding {base} costs ~{abs(diff):.2f}% vs {quote}")
    return "\n".join([
        f"Carry — {base}/{quote}  (10-year yield differential)",
        f"Source: FRED · {br[-1][0]}",
        "",
        f"  {base} 10y yield      {bv:>6.2f}%",
        f"  {quote} 10y yield      {qv:>6.2f}%",
        f"  {'Differential':<18} {diff:>+6.2f}%",
        "",
        f"  Read: {lean}.",
    ])


def federal_budget() -> str:
    """US federal budget balance — monthly surplus/deficit and the trailing
    12-month total. Source: FRED / U.S. Treasury (Monthly Treasury Statement)."""
    rows = _fred("MTSDS133FMS", limit=14)          # millions USD, monthly, deficit < 0
    if not rows:
        return "Federal budget data is unavailable right now."

    def _b(v):                                     # millions → $B / $T
        a = abs(v) / 1000
        return (f"-${a/1000:.2f}T" if v < 0 else f"+${a/1000:.2f}T") if a >= 1000 \
            else (f"-${a:.1f}B" if v < 0 else f"+${a:.1f}B")

    last12 = rows[-12:]
    rolling = sum(v for _, v in last12)
    latest_d, latest_v = rows[-1]
    out = [
        "US Federal Budget Balance  (surplus +, deficit −)",
        "Source: FRED · U.S. Treasury Monthly Treasury Statement",
        "",
        f"  {'Latest month':<18} {_b(latest_v):>10}   ({latest_d})",
        f"  {'Trailing 12-month':<18} {_b(rolling):>10}",
        "",
        "  Recent months:",
        f"  {'Month':<10} {'Balance':>12}",
        "  " + "─" * 26,
    ]
    for d, v in reversed(last12):
        out.append(f"  {d:<10} {_b(v):>12}")
    return "\n".join(out)


# Foreign currency of each FX pair → Big Mac currency_code.
_BIGMAC_CCY = {
    "EURUSD": "EUR", "GBPUSD": "GBP", "USDJPY": "JPY", "AUDUSD": "AUD",
    "USDCAD": "CAD", "USDCHF": "CHF", "USDCNY": "CNY", "NZDUSD": "NZD",
    "USDMXN": "MXN", "USDINR": "INR", "USDBRL": "BRL", "USDKRW": "KRW",
    "USDTRY": "TRY", "USDSEK": "SEK", "USDZAR": "ZAR",
}

_BIGMAC_CSV = ("https://raw.githubusercontent.com/TheEconomist/big-mac-data/"
               "master/output-data/big-mac-full-index.csv")


def big_mac(fx_symbol: str = "") -> str:
    """The Economist's Big Mac Index — burgernomics PPP. Positive = the currency
    looks over-valued vs the USD (GDP-adjusted), negative = under-valued."""
    try:
        text = requests.get(_BIGMAC_CSV, headers=HEADERS, timeout=15).text
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception as e:
        return f"Could not fetch the Big Mac Index: {e}"
    if not rows:
        return "Big Mac Index data is unavailable right now."

    latest_date = max(r["date"] for r in rows)
    latest = [r for r in rows if r["date"] == latest_date]

    def adj(r):
        try:
            return float(r.get("USD_adjusted")) * 100
        except (TypeError, ValueError):
            return None

    target = _BIGMAC_CCY.get((fx_symbol or "").upper())
    if target:
        row = next((r for r in latest if r.get("currency_code") == target), None)
        if not row:
            return f"No Big Mac data for {target}."
        v = adj(row)
        verdict = "over-valued" if (v or 0) > 0 else "under-valued"
        return "\n".join([
            f"Big Mac Index — {row.get('name','')} ({target})",
            f"Source: The Economist · {latest_date}",
            "",
            f"  Local price (USD)     ${float(row.get('dollar_price',0)):.2f}",
            f"  vs US Dollar          {v:+.1f}%  ({verdict}, GDP-adjusted)",
            "",
            "  Positive = currency looks expensive vs the dollar.",
        ])

    ranked = sorted(((r.get("name", ""), r.get("currency_code", ""), adj(r))
                     for r in latest if adj(r) is not None),
                    key=lambda x: x[2], reverse=True)
    out = [
        "Big Mac Index — Currency Valuation vs USD",
        f"Source: The Economist · {latest_date} · GDP-adjusted",
        "",
        f"  {'Country':<20}{'Ccy':<6}{'vs USD':>9}",
        "  " + "─" * 38,
    ]
    for nm, ccy, v in ranked[:8] + [("…", "", None)] + ranked[-8:]:
        if v is None:
            out.append("  " + "·" * 34)
            continue
        bar = ("▲" if v >= 0 else "▼") * min(int(abs(v) / 5), 10)
        out.append(f"  {nm[:19]:<20}{ccy:<6}{v:>+8.1f}%  {bar}")
    return "\n".join(out)


def treasury_auctions(n: int = 12) -> str:
    """Recent U.S. Treasury auction results — term, high yield, and bid-to-cover
    (demand). Source: Treasury FiscalData (no key)."""
    try:
        data = requests.get(
            f"{FISCALDATA}/v1/accounting/od/auctions_query",
            params={"sort": "-auction_date", "page[size]": 120,
                    "fields": ("auction_date,security_type,security_term,high_yield,"
                               "high_investment_rate,int_rate,bid_to_cover_ratio,offering_amt")},
            headers=HEADERS, timeout=15,
        ).json().get("data", [])
    except Exception as e:
        return f"Could not fetch Treasury auctions: {e}"

    def clean(v):
        return None if v in (None, "null", "") else v

    rows = []
    for d in data:
        btc = clean(d.get("bid_to_cover_ratio"))
        yld = clean(d.get("high_yield")) or clean(d.get("high_investment_rate")) or clean(d.get("int_rate"))
        if btc is None and yld is None:
            continue                      # auction not settled / no results yet
        rows.append((d.get("auction_date", "")[:10],
                     f"{d.get('security_type','')} {d.get('security_term','')}".strip(),
                     yld, btc, clean(d.get("offering_amt"))))
        if len(rows) >= n:
            break
    if not rows:
        return "No recent settled Treasury auctions found."

    out = [
        "US Treasury Auctions — Recent Results",
        "Source: U.S. Treasury · FiscalData",
        "",
        f"  {'Auction':<12}{'Security':<22}{'High Yield':>11}{'Bid/Cover':>11}",
        "  " + "─" * 56,
    ]
    for date, sec, yld, btc, _amt in rows:
        try:
            yld_s = f"{float(yld):.3f}%"
        except (TypeError, ValueError):
            yld_s = "—"
        try:
            btc_s = f"{float(btc):.2f}x"
        except (TypeError, ValueError):
            btc_s = "—"
        out.append(f"  {date:<12}{sec[:21]:<22}{yld_s:>11}{btc_s:>11}")
    out += ["", "  Bid-to-cover = total bids ÷ amount sold; higher = stronger demand."]
    return "\n".join(out)


def _avg_interest_rate():
    """Weighted-average interest rate on total marketable Treasury debt (latest).
    Returns (rate_pct, record_date) or None. Source: Treasury FiscalData."""
    try:
        data = requests.get(
            f"{FISCALDATA}/v2/accounting/od/avg_interest_rates",
            params={"sort": "-record_date",
                    "filter": "security_desc:eq:Total Marketable",
                    "page[size]": 1,
                    "fields": "record_date,avg_interest_rate_amt"},
            headers=HEADERS, timeout=12,
        ).json().get("data", [])
        if data:
            return float(data[0]["avg_interest_rate_amt"]), data[0]["record_date"]
    except Exception:
        pass
    return None
