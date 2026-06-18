"""On-chain / DeFi data — DeFiLlama API (free, no key)."""

import requests

LLAMA = "https://api.llama.fi"
HEAD  = {"User-Agent": "FinGPT-Terminal/0.1"}

# Bare chain aliases → DeFiLlama chain slug + display name.
CHAINS = {
    "ETHEREUM": ("Ethereum", "Ethereum"), "ARBITRUM": ("Arbitrum", "Arbitrum"),
    "SOLANA": ("Solana", "Solana"), "BASE": ("Base", "Base"),
    "OPTIMISM": ("Optimism", "Optimism"), "POLYGON": ("Polygon", "Polygon"),
    "BSC": ("BSC", "BNB Chain"), "AVALANCHE": ("Avalanche", "Avalanche"),
    "TRON": ("Tron", "Tron"), "SUI": ("Sui", "Sui"),
    "APTOS": ("Aptos", "Aptos"), "TON": ("Ton", "TON"),
    "SEI": ("Sei", "Sei"), "BLAST": ("Blast", "Blast"),
    "MANTLE": ("Mantle", "Mantle"), "LINEA": ("Linea", "Linea"),
    "STARKNET": ("Starknet", "Starknet"), "ZKSYNC": ("zkSync Era", "zkSync Era"),
    "SCROLL": ("Scroll", "Scroll"), "GNOSIS": ("Gnosis", "Gnosis"),
    "CELO": ("Celo", "Celo"), "NEAR": ("Near", "Near"), "OSMOSIS": ("Osmosis", "Osmosis"),
}


def resolve_chain(token: str):
    """token may be a bare alias or a 'chain:<slug>' prefix."""
    t = token.strip()
    if t.lower().startswith("chain:"):
        slug = t.split(":", 1)[1]
        return (slug, slug.title())
    return CHAINS.get(t.upper())


def _get(path):
    r = requests.get(f"{LLAMA}{path}", headers=HEAD, timeout=15)
    r.raise_for_status()
    return r.json()


def _fmt(v):
    a = abs(v)
    if a >= 1e9: return f"${v/1e9:.2f}B"
    if a >= 1e6: return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"


def chain_tvl(slug: str, name: str) -> str:
    """Current TVL for a chain plus recent trend + top chains for context."""
    try:
        hist = _get(f"/v2/historicalChainTvl/{slug}")
    except Exception:
        hist = None
    out = [f"{name} — Total Value Locked", "Source: DeFiLlama", ""]
    if hist:
        cur = hist[-1]["tvl"]
        def back(days):
            if len(hist) > days:
                p = hist[-1 - days]["tvl"]
                return (cur / p - 1) * 100 if p else None
            return None
        out.append(f"  {'TVL':<14} {_fmt(cur)}")
        for lbl, d in (("7d", 7), ("30d", 30), ("90d", 90)):
            ch = back(d)
            if ch is not None:
                out.append(f"  {lbl + ' change':<14} {ch:+.1f}%")
    else:
        out.append("  (chain TVL history unavailable)")

    # Top chains for context.
    try:
        chains = _get("/v2/chains")
        top = sorted(chains, key=lambda c: c.get("tvl") or 0, reverse=True)[:8]
        out += ["", "  Top chains by TVL", "  " + "─" * 28]
        for c in top:
            mark = "›" if c.get("name", "").lower() == name.lower() else " "
            out.append(f"  {mark} {c.get('name', '')[:16]:<16} {_fmt(c.get('tvl') or 0):>12}")
    except Exception:
        pass
    return "\n".join(out)


def top_protocols(n: int = 12) -> str:
    """Largest DeFi protocols by TVL across all chains."""
    try:
        data = _get("/protocols")
        top = sorted(data, key=lambda p: p.get("tvl") or 0, reverse=True)[:n]
    except Exception as e:
        return f"Could not fetch protocols: {e}"
    out = ["Top DeFi Protocols by TVL", "Source: DeFiLlama", "",
           f"  {'Protocol':<22}{'Category':<16}{'TVL':>12}{'7d':>8}", "  " + "─" * 58]
    for p in top:
        ch7 = p.get("change_7d")
        c7  = f"{ch7:+.1f}%" if isinstance(ch7, (int, float)) else "—"
        out.append(f"  {str(p.get('name',''))[:21]:<22}{str(p.get('category') or '')[:15]:<16}"
                   f"{_fmt(p.get('tvl') or 0):>12}{c7:>8}")
    return "\n".join(out)


def stablecoins(n: int = 12) -> str:
    """Largest stablecoins by circulating supply + total market cap."""
    try:
        r = requests.get("https://stablecoins.llama.fi/stablecoins?includePrices=false",
                         headers=HEAD, timeout=15)
        r.raise_for_status()
        assets = r.json().get("peggedAssets", [])
    except Exception as e:
        return f"Could not fetch stablecoins: {e}"

    def circ(a):
        return (a.get("circulating") or {}).get("peggedUSD") or 0

    total = sum(circ(a) for a in assets)
    top = sorted(assets, key=circ, reverse=True)[:n]
    out = ["Stablecoins by Circulating Supply", "Source: DeFiLlama",
           f"Total stablecoin market cap: {_fmt(total)}", "",
           f"  {'Name':<22}{'Symbol':<8}{'Circulating':>14}{'Share':>8}", "  " + "─" * 54]
    for a in top:
        c = circ(a)
        share = f"{c/total*100:.1f}%" if total else "—"
        out.append(f"  {str(a.get('name',''))[:21]:<22}{str(a.get('symbol',''))[:7]:<8}"
                   f"{_fmt(c):>14}{share:>8}")
    return "\n".join(out)


def chain_tvl_series(slug: str, period_days: int = 365):
    """[(label, values)] of TVL for charting a chain subject."""
    try:
        hist = _get(f"/v2/historicalChainTvl/{slug}")
        vals = [h["tvl"] for h in hist][-period_days:]
        return vals or None
    except Exception:
        return None
