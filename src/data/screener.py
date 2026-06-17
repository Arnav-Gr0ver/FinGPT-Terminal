"""Stock screens — Yahoo's predefined screeners via yfinance (free, no key)."""

import yfinance as yf
from src.data.equities import _large

# Friendly alias → (Yahoo predefined screen id, description).
SCREENS = {
    "gainers":   ("day_gainers",               "Biggest % gainers today"),
    "losers":    ("day_losers",                "Biggest % losers today"),
    "actives":   ("most_actives",              "Most actively traded"),
    "shorted":   ("most_shorted_stocks",       "Most heavily shorted"),
    "smallcaps": ("aggressive_small_caps",     "Aggressive small caps"),
    "tech":      ("growth_technology_stocks",  "Growth technology stocks"),
    "growth":    ("undervalued_growth_stocks", "Undervalued growth stocks"),
    "value":     ("undervalued_large_caps",    "Undervalued large caps"),
}


def list_screens() -> str:
    w = max(len(a) for a in SCREENS)
    lines = ["Stock Screens", "", "  Run one:  screen <name>", ""]
    for alias, (_id, desc) in SCREENS.items():
        lines.append(f"  {alias:<{w}}   {desc}")
    return "\n".join(lines)


def get_screen_rows(alias: str, count: int = 20) -> list[dict]:
    """Return [{symbol, name, price, chg, mktcap, pe}] for a screen."""
    key = alias.lower().strip()
    if key not in SCREENS:
        return []
    yahoo_id = SCREENS[key][0]
    try:
        res    = yf.screen(yahoo_id, count=count)
        quotes = (res or {}).get("quotes", [])
    except Exception:
        return []

    rows = []
    for q in quotes:
        sym = q.get("symbol")
        if not sym:
            continue
        rows.append({
            "symbol": sym,
            "name":   q.get("shortName") or q.get("displayName") or "",
            "price":  q.get("regularMarketPrice"),
            "chg":    q.get("regularMarketChangePercent"),
            "mktcap": _large(q.get("marketCap")).replace("$", "") if q.get("marketCap") else "—",
            "pe":     q.get("trailingPE"),
        })
    return rows
