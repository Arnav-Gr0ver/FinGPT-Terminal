"""Extra crypto data sources (free, no key) — independent of CoinGecko/DeFiLlama.

Blockstream + Blockchair (Bitcoin chain), ultrasound.money (ETH issuance),
CoinLore (global stats), Kraken Futures (perp open interest)."""

import requests

H = {"User-Agent": "FinR1-Terminal/0.2", "Accept": "application/json"}


def _g(url, params=None):
    return requests.get(url, params=params, headers=H, timeout=12).json()


def btc_chain() -> str:
    """Bitcoin chain status from two independent explorers. Sources: Blockstream, Blockchair."""
    out = ["Bitcoin Chain — Independent Explorers", "Source: Blockstream · Blockchair", ""]
    try:
        h = requests.get("https://blockstream.info/api/blocks/tip/height", headers=H, timeout=10).text
        out.append(f"  {'Tip height (Blockstream)':<28} {int(h):,}")
    except Exception:
        pass
    try:
        d = _g("https://api.blockchair.com/bitcoin/stats").get("data", {})
        out += [
            f"  {'Difficulty (Blockchair)':<28} {d.get('difficulty',0)/1e12:,.1f} T",
            f"  {'Mempool txs':<28} {d.get('mempool_transactions',0):,}",
            f"  {'24h transactions':<28} {d.get('transactions_24h',0):,}",
            f"  {'Market price':<28} ${d.get('market_price_usd',0):,.0f}",
            f"  {'Hashrate (24h)':<28} {d.get('hashrate_24h','—')}",
        ]
    except Exception:
        pass
    if len(out) <= 3:
        return "Bitcoin chain data is unavailable right now."
    return "\n".join(out)


def _supply_val(point):
    """Pull a supply number out of a point that may be a dict, list, or scalar."""
    if isinstance(point, dict):
        for k in ("supply", "value", "v"):
            if k in point:
                return point[k]
    if isinstance(point, (list, tuple)) and point:
        return point[-1]
    if isinstance(point, (int, float)):
        return point
    return None


def eth_issuance() -> str:
    """Ethereum net issuance / burn over recent windows. Source: ultrasound.money."""
    try:
        j = _g("https://ultrasound.money/api/v2/fees/supply-over-time")
    except Exception as e:
        return f"Could not fetch ETH issuance: {e}"

    out = ["Ethereum Supply & Issuance", "Source: ultrasound.money", ""]
    for win, label in (("d1", "1-day"), ("d7", "7-day"), ("d30", "30-day")):
        try:
            series = j.get(win)
            pts = series if isinstance(series, list) else (series.get("data") if isinstance(series, dict) else None)
            if not pts or len(pts) < 2:
                continue
            first, last = _supply_val(pts[0]), _supply_val(pts[-1])
            d = float(last) - float(first)
            out.append(f"  {label + ' net supply':<22} {d:+,.0f} ETH  ({'inflationary' if d > 0 else 'deflationary'})")
        except Exception:
            continue
    if len(out) <= 3:
        return ("Ethereum Supply & Issuance\nSource: ultrasound.money\n\n"
                "  Live ETH net-issuance series is momentarily unavailable.")
    return "\n".join(out)


def coinlore_global() -> str:
    """Independent global crypto snapshot (cross-check vs CoinGecko). Source: CoinLore."""
    try:
        g = _g("https://api.coinlore.net/api/global/")[0]
    except Exception as e:
        return f"Could not fetch CoinLore global data: {e}"
    return "\n".join([
        "Global Crypto — Independent Read", "Source: CoinLore", "",
        f"  {'Total market cap':<24} ${g.get('total_mcap',0)/1e12:.2f}T",
        f"  {'24h volume':<24} ${g.get('total_volume',0)/1e9:.1f}B",
        f"  {'BTC dominance':<24} {g.get('btc_d','—')}%",
        f"  {'ETH dominance':<24} {g.get('eth_d','—')}%",
        f"  {'Active coins':<24} {g.get('coins_count','—'):,}" if isinstance(g.get('coins_count'), int) else f"  Active coins            {g.get('coins_count','—')}",
        f"  {'24h market-cap change':<24} {g.get('mcap_change','—')}%",
    ])


def kraken_futures_oi(n: int = 12) -> str:
    """Perpetual-futures open interest & funding on Kraken Futures. Source: Kraken."""
    try:
        tickers = _g("https://futures.kraken.com/derivatives/api/v3/tickers").get("tickers", [])
    except Exception as e:
        return f"Could not fetch Kraken Futures data: {e}"
    perps = [t for t in tickers if (t.get("symbol", "").startswith("pf_") or t.get("tag") == "perpetual")
             and t.get("openInterest")]
    perps.sort(key=lambda t: float(t.get("openInterest") or 0) * float(t.get("markPrice") or 0), reverse=True)
    if not perps:
        return "No Kraken Futures perp data available."
    out = ["Kraken Futures — Perp Open Interest", "Source: Kraken Futures", "",
           f"  {'Contract':<16}{'Mark':>12}{'Funding':>11}{'OI ($)':>14}", "  " + "─" * 56]
    for t in perps[:n]:
        sym = t.get("symbol", "").replace("pf_", "").upper()[:15]
        mark = float(t.get("markPrice") or 0)
        fr = float(t.get("fundingRate") or 0) * 100
        oi = float(t.get("openInterest") or 0) * mark
        oi_s = f"${oi/1e9:.2f}B" if oi >= 1e9 else f"${oi/1e6:.0f}M"
        out.append(f"  {sym:<16}{mark:>12,.2f}{fr:>+10.4f}%{oi_s:>14}")
    return "\n".join(out)
