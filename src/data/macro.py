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
