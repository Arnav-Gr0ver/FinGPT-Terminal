"""Crypto volatility — Deribit DVOL index (free, no key).

DVOL is Deribit's 30-day implied-volatility index for BTC and ETH — the crypto
analogue of the VIX, derived from the options book."""

from src.data.http import get_json

API = "https://www.deribit.com/api/v2/public/get_volatility_index_data"


def _series(currency: str):
    import time
    now = int(time.time() * 1000)
    start = now - 90 * 86400 * 1000
    try:
        j = get_json(API, params={"currency": currency, "start_timestamp": start,
                                  "end_timestamp": now, "resolution": "43200"}, timeout=15)
        return j.get("result", {}).get("data", [])
    except Exception:
        return []


_SPARK = "▁▂▃▄▅▆▇█"


def dvol(symbol: str = "") -> str:
    """Implied-volatility (DVOL) index for BTC/ETH — current level, regime, trend."""
    want = symbol.upper() if symbol.upper() in ("BTC", "ETH") else None
    currencies = [want] if want else ["BTC", "ETH"]

    blocks = []
    for ccy in currencies:
        data = _series(ccy)
        if not data:
            continue
        closes = [row[4] for row in data if len(row) >= 5]
        if not closes:
            continue
        cur = closes[-1]
        lo, hi = min(closes), max(closes)
        rng = (hi - lo) or 1
        spark = "".join(_SPARK[min(int((c - lo) / rng * 7), 7)] for c in closes[-40:])
        regime = ("low / complacent" if cur < 40 else "normal" if cur < 60
                  else "elevated" if cur < 90 else "extreme")
        blocks.append((ccy, cur, lo, hi, spark, regime))

    if not blocks:
        return "DVOL data is unavailable right now."
    out = ["Crypto Implied Volatility — DVOL Index",
           "Source: Deribit · 30-day implied vol (annualised %)", ""]
    for ccy, cur, lo, hi, spark, regime in blocks:
        out += [
            f"  {ccy}-DVOL        {cur:.1f}   ({regime})",
            f"    90d range     {lo:.0f} – {hi:.0f}",
            f"    90d trend     {spark}",
            "",
        ]
    out.append("  DVOL is the crypto VIX — higher = pricier options / more fear.")
    return "\n".join(out)
