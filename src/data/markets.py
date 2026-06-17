"""Market snapshot — index/benchmark levels via yfinance fast_info."""

import yfinance as yf

# (label, yahoo symbol, kind) — kind drives formatting in the views.
INDICES = [
    ("S&P 500",    "^GSPC", "index"),
    ("Nasdaq",     "^IXIC", "index"),
    ("Dow",        "^DJI",  "index"),
    ("Russell 2K", "^RUT",  "index"),
    ("VIX",        "^VIX",  "level"),
    ("10Y",        "^TNX",  "rate"),
]

# Compact set for the home header.
HOME = [INDICES[0], INDICES[1], INDICES[2], INDICES[4], INDICES[5]]


def get_snapshot(rows=None) -> list[dict]:
    """Return [{label, kind, price, change_pct}] for a set of benchmarks."""
    out = []
    for label, sym, kind in (rows or INDICES):
        try:
            f      = yf.Ticker(sym).fast_info
            price  = f.last_price
            prev   = f.previous_close or price
            chg    = (price - prev) / prev * 100 if prev else 0.0
            out.append({"label": label, "kind": kind, "price": price, "change_pct": chg})
        except Exception:
            out.append({"label": label, "kind": kind, "price": None, "change_pct": None})
    return out
