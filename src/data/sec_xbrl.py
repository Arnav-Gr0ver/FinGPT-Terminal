"""Structured fundamentals from SEC XBRL (data.sec.gov, free, no key).

More authoritative than scraped fundamentals: these are the exact figures filed
in 10-Ks. Used as the primary source for `financials`, with yfinance as fallback.
"""

import requests
from src.data.gov import _resolve_cik, HEADERS

BASE = "https://data.sec.gov/api/xbrl/companyconcept"

# Each line: (label, [candidate us-gaap tags, first that exists wins]).
_LINES = [
    ("Revenue",          ["RevenueFromContractWithCustomerExcludingAssessedTax",
                          "RevenueFromContractWithCustomerIncludingAssessedTax",
                          "Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet"]),
    ("Gross Profit",     ["GrossProfit"]),
    ("Operating Income", ["OperatingIncomeLoss"]),
    ("Net Income",       ["NetIncomeLoss"]),
    ("Total Assets",     ["Assets"]),
    ("Total Liabilities",["Liabilities"]),
    ("Equity",           ["StockholdersEquity"]),
    ("Op Cash Flow",     ["NetCashProvidedByUsedInOperatingActivities"]),
]


def _annual(cik: int, tag: str) -> dict:
    """{fiscal_year: value} for annual (FY) figures of a us-gaap concept."""
    try:
        url = f"{BASE}/CIK{cik:010d}/us-gaap/{tag}.json"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return {}
        units = r.json().get("units", {})
        usd = units.get("USD") or next(iter(units.values()), [])
        out = {}
        for o in usd:
            if o.get("form", "").startswith("10-K") and o.get("fp") == "FY" and o.get("fy"):
                out[int(o["fy"])] = o["val"]
        return out
    except Exception:
        return {}


def get_xbrl_financials(ticker: str) -> str | None:
    """Trended income/balance/cash lines from filed 10-Ks, or None if unavailable."""
    cik = _resolve_cik(ticker.upper())
    if not cik:
        return None
    data, years = {}, set()
    for label, tags in _LINES:
        series = {}
        for tag in tags:
            series = _annual(cik, tag)
            if series:
                break
        if series:
            data[label] = series
            years |= set(series)
    if not data:
        return None
    yrs = sorted(years)[-4:]

    def fmt(v):
        if v is None:
            return "—"
        a = abs(v)
        if a >= 1e9: return f"{v/1e9:.1f}B"
        if a >= 1e6: return f"{v/1e6:.1f}M"
        return f"{v:,.0f}"

    head = f"  {'(USD)':<20}" + "".join(f"{y:>12}" for y in yrs)
    out  = [f"Financials — {ticker.upper()}  (SEC XBRL / filed 10-Ks)", "",
            head, "  " + "─" * (20 + 12 * len(yrs))]
    for label, _ in _LINES:
        if label not in data:
            continue
        cells = "".join(f"{fmt(data[label].get(y)):>12}" for y in yrs)
        out.append(f"  {label:<20}{cells}")
    return "\n".join(out)
