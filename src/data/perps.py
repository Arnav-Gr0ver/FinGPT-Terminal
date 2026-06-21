"""Perpetual-futures funding — dYdX v4 public indexer (free, no key).

Funding rates and open interest on crypto perps. Persistently positive funding
means longs are crowded (paying shorts) — a sentiment/positioning gauge that spot
prices don't show."""

from src.data.http import get_json

API = "https://indexer.dydx.trade/v4/perpetualMarkets"

# Our crypto symbol → dYdX market ticker.
MARKETS = {
    "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD", "AVAX": "AVAX-USD",
    "LINK": "LINK-USD", "DOGE": "DOGE-USD", "ADA": "ADA-USD", "DOT": "DOT-USD",
    "ATOM": "ATOM-USD", "NEAR": "NEAR-USD", "ARB": "ARB-USD", "OP": "OP-USD",
    "SUI": "SUI-USD", "APT": "APT-USD", "LTC": "LTC-USD", "BCH": "BCH-USD",
    "UNI": "UNI-USD", "XRP": "XRP-USD", "TRX": "TRX-USD", "MATIC": "MATIC-USD",
}


def _row(m, label):
    try:
        fund = float(m.get("nextFundingRate") or 0) * 100      # → percent (8h)
        price = float(m.get("oraclePrice") or 0)
        oi = float(m.get("openInterest") or 0) * price
        chg_abs = float(m.get("priceChange24H") or 0)          # dYdX gives absolute $
        prev = price - chg_abs
        chg = (chg_abs / prev * 100) if prev else 0
    except (TypeError, ValueError):
        return None
    apr = fund * 3 * 365                                       # 8h funding → annualized
    return (label, price, chg, fund, apr, oi)


def funding(symbol: str = "") -> str:
    try:
        markets = get_json(API, timeout=15).get("markets", {})
    except Exception as e:
        return f"Could not fetch funding rates: {e}"
    if not markets:
        return "No perpetual-market data available."

    want = MARKETS.get((symbol or "").upper())
    rows = []
    if want and want in markets:
        r = _row(markets[want], want)
        if r:
            rows = [r]
        title = f"Perp Funding — {symbol.upper()}"
    else:
        for tk, m in markets.items():
            r = _row(m, tk)
            if r:
                rows.append(r)
        rows.sort(key=lambda x: abs(x[3]), reverse=True)        # most extreme funding
        rows = rows[:14]
        title = "Perp Funding — Most Extreme (dYdX)"

    if not rows:
        return "No funding data available right now."

    hl = _hyperliquid_funding(symbol.upper()) if want else None
    out = [
        title, "Source: dYdX v4 · funding per 8h, OI in USD",
        "",
        f"  {'Market':<10}{'Price':>11}{'24h':>8}{'Funding':>9}{'~APR':>9}{'OI':>11}",
        "  " + "─" * 60,
    ]
    for label, price, chg, fund, apr, oi in rows:
        p = f"${price:,.4f}" if price < 10 else f"${price:,.0f}"
        oi_s = f"${oi/1e9:.2f}B" if oi >= 1e9 else f"${oi/1e6:.0f}M"
        out.append(f"  {label:<10}{p:>11}{chg:>+7.1f}%{fund:>+8.3f}%{apr:>+8.1f}%{oi_s:>11}")
    if hl is not None:
        out += ["", f"  Hyperliquid {symbol.upper()} funding (1h): {hl:+.4f}%  (≈{hl*24*365:+.0f}% APR)"]
    out += ["", "  Positive funding = longs pay shorts (crowded longs)."]
    return "\n".join(out)


def _hyperliquid_funding(sym: str):
    """Current 1h funding for a coin on Hyperliquid (a 2nd venue). Source: Hyperliquid."""
    try:
        import requests
        r = requests.post("https://api.hyperliquid.xyz/info", json={"type": "metaAndAssetCtxs"},
                          headers={"User-Agent": "FinR1/0.2"}, timeout=12)
        meta, ctxs = r.json()
        names = [a["name"] for a in meta.get("universe", [])]
        if sym in names:
            return float(ctxs[names.index(sym)].get("funding") or 0) * 100
    except Exception:
        pass
    return None
