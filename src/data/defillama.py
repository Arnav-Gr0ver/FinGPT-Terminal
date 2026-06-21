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


# Bare aliases for loadable DeFi-protocol subjects → DeFiLlama slug + display name.
PROTOCOLS = {
    "AAVE": ("aave", "Aave"), "UNISWAP": ("uniswap", "Uniswap"),
    "LIDO": ("lido", "Lido"), "CURVE": ("curve-dex", "Curve"),
    "MAKER": ("makerdao", "MakerDAO"), "MAKERDAO": ("makerdao", "MakerDAO"),
    "SKY": ("sky-lending", "Sky"), "COMPOUND": ("compound-finance", "Compound"),
    "PENDLE": ("pendle", "Pendle"), "GMX": ("gmx", "GMX"),
    "AERODROME": ("aerodrome-slipstream", "Aerodrome"), "RAYDIUM": ("raydium", "Raydium"),
    "JUPITER": ("jupiter-aggregator", "Jupiter"), "PANCAKESWAP": ("pancakeswap", "PancakeSwap"),
    "ETHENA": ("ethena", "Ethena"), "EIGENLAYER": ("eigenlayer", "EigenLayer"),
    "MORPHO": ("morpho", "Morpho"), "ROCKETPOOL": ("rocket-pool", "Rocket Pool"),
    "HYPERLIQUID": ("hyperliquid", "Hyperliquid"), "JITO": ("jito", "Jito"),
    "SPARK": ("spark", "Spark"), "DYDX": ("dydx", "dYdX"),
    "BALANCER": ("balancer", "Balancer"), "SUSHI": ("sushi", "SushiSwap"),
    "CONVEX": ("convex-finance", "Convex"),
}


def resolve_protocol(token: str):
    """Bare protocol alias or 'protocol:<slug>'."""
    t = token.strip()
    if t.lower().startswith("protocol:"):
        slug = t.split(":", 1)[1]
        return (slug, slug.replace("-", " ").title())
    return PROTOCOLS.get(t.upper())


# Major stablecoins → DeFiLlama pegged-asset id (stable across the API).
STABLECOINS = {
    "USDT": ("1", "Tether"), "USDC": ("2", "USD Coin"), "USDS": ("209", "Sky Dollar"),
    "DAI": ("5", "Dai"), "USDE": ("146", "Ethena USDe"), "FDUSD": ("128", "First Digital USD"),
    "PYUSD": ("130", "PayPal USD"), "TUSD": ("4", "TrueUSD"), "FRAX": ("6", "Frax"),
    "USDD": ("16", "USDD"), "BUSD": ("3", "Binance USD"), "GUSD": ("11", "Gemini Dollar"),
}


def resolve_stablecoin(token: str):
    """Bare symbol or 'stable:<symbol>'."""
    t = token.strip()
    if t.lower().startswith(("stable:", "stablecoin:")):
        t = t.split(":", 1)[1]
    return STABLECOINS.get(t.upper())


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


def top_pools(n: int = 14, stable_only: bool = False) -> str:
    """Highest-TVL DeFi yield pools with their current APY. Source: DeFiLlama
    yields. Defaults to the largest pools (deep liquidity); `stable_only` keeps
    just stablecoin pools (lower price risk)."""
    try:
        data = _get_yields("/pools").get("data", [])
    except Exception as e:
        return f"Could not fetch DeFi yield pools: {e}"

    pools = [p for p in data if (p.get("tvlUsd") or 0) > 1e7 and (p.get("apy") or 0) > 0.1]
    if stable_only:
        pools = [p for p in pools if p.get("stablecoin")]
    pools.sort(key=lambda p: p.get("tvlUsd") or 0, reverse=True)
    pools = pools[:n]
    if not pools:
        return "No DeFi pools matched right now."

    title = "Top DeFi Yield Pools" + (" — Stablecoins" if stable_only else " — by TVL")
    out = [
        title, "Source: DeFiLlama yields",
        "",
        f"  {'Project':<16}{'Symbol':<16}{'Chain':<11}{'TVL':>10}{'APY':>8}",
        "  " + "─" * 62,
    ]
    for p in pools:
        out.append(
            f"  {str(p.get('project',''))[:15]:<16}{str(p.get('symbol',''))[:15]:<16}"
            f"{str(p.get('chain',''))[:10]:<11}{_fmt(p.get('tvlUsd') or 0):>10}"
            f"{(p.get('apy') or 0):>7.1f}%"
        )
    out += ["", "  APY is variable and includes reward tokens; it is not guaranteed."]
    return "\n".join(out)


def defi_hacks(n: int = 14) -> str:
    """Recent crypto exploits / hacks with amounts lost. Source: DeFiLlama."""
    import datetime as _dt
    try:
        data = _get("/hacks")
    except Exception as e:
        return f"Could not fetch hacks: {e}"
    data = sorted([h for h in data if h.get("date")], key=lambda h: h["date"], reverse=True)
    if not data:
        return "No hack data available."
    total = sum(h.get("amount") or 0 for h in data)
    out = [
        "Crypto Hacks & Exploits — Most Recent",
        f"Source: DeFiLlama · {len(data):,} events tracked · ${total/1e9:.1f}B total",
        "",
        f"  {'Date':<12}{'Protocol':<22}{'Lost':>10}  Technique",
        "  " + "─" * 60,
    ]
    for h in data[:n]:
        d = _dt.datetime.utcfromtimestamp(h["date"]).strftime("%Y-%m-%d")
        amt = h.get("amount") or 0
        amt_s = f"${amt/1e9:.2f}B" if amt >= 1e9 else f"${amt/1e6:.1f}M"
        out.append(f"  {d:<12}{str(h.get('name',''))[:21]:<22}{amt_s:>10}  "
                   f"{str(h.get('technique',''))[:22]}")
    return "\n".join(out)


def _get_yields(path):
    r = requests.get(f"https://yields.llama.fi{path}", headers=HEAD, timeout=20)
    r.raise_for_status()
    return r.json()


def dex_volumes(n: int = 12) -> str:
    """Largest decentralized exchanges by 24h spot volume. Source: DeFiLlama."""
    try:
        d = _get("/overview/dexs")
    except Exception as e:
        return f"Could not fetch DEX volumes: {e}"
    prot = sorted(d.get("protocols") or [], key=lambda p: p.get("total24h") or 0, reverse=True)
    if not prot:
        return "No DEX volume data available."
    total = d.get("total24h") or 0
    out = [
        "Decentralized Exchanges — 24h Spot Volume",
        f"Source: DeFiLlama · total 24h: {_fmt(total)}",
        "",
        f"  {'DEX':<26}{'24h Volume':>14}{'Share':>8}",
        "  " + "─" * 50,
    ]
    for p in prot[:n]:
        v = p.get("total24h") or 0
        share = f"{v/total*100:.1f}%" if total else "—"
        out.append(f"  {str(p.get('name',''))[:25]:<26}{_fmt(v):>14}{share:>8}")
    return "\n".join(out)


def protocol_fees(n: int = 12) -> str:
    """Protocols earning the most fees over the last 24h (a real-revenue proxy).
    Source: DeFiLlama."""
    try:
        d = _get("/overview/fees")
    except Exception as e:
        return f"Could not fetch protocol fees: {e}"
    prot = sorted(d.get("protocols") or [], key=lambda p: p.get("total24h") or 0, reverse=True)
    if not prot:
        return "No fee data available."
    out = [
        "Protocol Fees — Last 24h",
        f"Source: DeFiLlama · total 24h fees: {_fmt(d.get('total24h') or 0)}",
        "",
        f"  {'Protocol':<26}{'Fees 24h':>13}{'Revenue 24h':>14}",
        "  " + "─" * 54,
    ]
    for p in prot[:n]:
        fee = p.get("total24h") or 0
        rev = p.get("revenue24h")
        rev_s = _fmt(rev) if isinstance(rev, (int, float)) else "—"
        out.append(f"  {str(p.get('name',''))[:25]:<26}{_fmt(fee):>13}{rev_s:>14}")
    out += ["", "  Fees = paid by users; revenue = share kept by the protocol."]
    return "\n".join(out)


def top_chains(n: int = 15) -> str:
    """Blockchains ranked by total value locked. Source: DeFiLlama."""
    try:
        data = _get("/v2/chains")
    except Exception as e:
        return f"Could not fetch chains: {e}"
    chains = sorted([c for c in data if (c.get("tvl") or 0) > 0],
                    key=lambda c: c.get("tvl") or 0, reverse=True)
    if not chains:
        return "No chain TVL data available."
    total = sum(c.get("tvl") or 0 for c in chains)
    out = [
        "Blockchains by Total Value Locked",
        f"Source: DeFiLlama · total DeFi TVL: {_fmt(total)}",
        "",
        f"  {'#':<4}{'Chain':<22}{'TVL':>14}{'Share':>8}",
        "  " + "─" * 50,
    ]
    for i, c in enumerate(chains[:n], 1):
        v = c.get("tvl") or 0
        share = f"{v/total*100:.1f}%" if total else "—"
        out.append(f"  {i:<4}{str(c.get('name',''))[:21]:<22}{_fmt(v):>14}{share:>8}")
    return "\n".join(out)


def protocol_overview(slug: str, name: str) -> str:
    """A loadable DeFi protocol's snapshot — current TVL, category, and the chains
    it spans. Source: DeFiLlama."""
    try:
        info = _get(f"/protocol/{slug}")
    except Exception as e:
        return f"Could not load protocol {name}: {e}"
    tvl = 0
    try:
        tvl = float(requests.get(f"{LLAMA}/tvl/{slug}", headers=HEAD, timeout=12).text)
    except Exception:
        hist = info.get("tvl") or []
        tvl = hist[-1].get("totalLiquidityUSD", 0) if hist else 0

    # currentChainTvls mixes real chains with pseudo-buckets (borrowed, staking,
    # pool2, …) and "Chain-borrowed" variants — keep only plain chain names.
    _PSEUDO = {"borrowed", "staking", "pool2", "vesting", "treasury", "offers",
               "masterchef", "polynetwork"}
    chains = {}
    for k, v in (info.get("currentChainTvls") or {}).items():
        if "-" in k or k.lower() in _PSEUDO:
            continue
        chains[k] = chains.get(k, 0) + (v or 0)
    top = sorted(chains.items(), key=lambda kv: kv[1], reverse=True)[:8]

    out = [
        f"{info.get('name', name)} — DeFi Protocol",
        f"Source: DeFiLlama · {info.get('category', '—')}",
        "",
        f"  {'Total Value Locked':<22} {_fmt(tvl)}",
        f"  {'Token':<22} {info.get('symbol') or '—'}",
        "",
        "  TVL by chain:",
    ]
    for ch, v in top:
        share = f"{v/tvl*100:.0f}%" if tvl else "—"
        out.append(f"  {ch[:18]:<20}{_fmt(v):>14}  {share:>5}")
    desc = (info.get("description") or "").strip()
    if desc:
        from textwrap import fill
        out += ["", fill(desc[:240], width=66, initial_indent="  ", subsequent_indent="  ")]
    return "\n".join(out)


def protocol_tvl_series(slug: str, period_days: int = 365):
    """[(values)] of a protocol's TVL for charting."""
    try:
        info = _get(f"/protocol/{slug}")
        vals = [h["totalLiquidityUSD"] for h in (info.get("tvl") or [])][-period_days:]
        return vals or None
    except Exception:
        return None


def protocol_fee_detail(slug: str, name: str) -> str:
    """Fees & protocol revenue for a single DeFi protocol. Source: DeFiLlama."""
    def grab(dtype):
        try:
            j = _get(f"/summary/fees/{slug}?dataType={dtype}")
            return j.get("total24h"), j.get("total7d"), j.get("total30d"), j.get("totalAllTime")
        except Exception:
            return (None, None, None, None)
    f24, f7, f30, fall = grab("dailyFees")
    r24, _, _, _ = grab("dailyRevenue")
    if f24 is None and fall is None:
        return f"No fee data tracked for {name}."

    def fm(v):
        return _fmt(v) if isinstance(v, (int, float)) else "—"
    return "\n".join([
        f"{name} — Fees & Revenue",
        "Source: DeFiLlama",
        "",
        f"  {'Fees (24h)':<20} {fm(f24)}",
        f"  {'Fees (7d)':<20} {fm(f7)}",
        f"  {'Fees (30d)':<20} {fm(f30)}",
        f"  {'Revenue (24h)':<20} {fm(r24)}",
        f"  {'Fees (all-time)':<20} {fm(fall)}",
        "",
        "  Fees = paid by users · revenue = kept by the protocol/holders.",
    ])


def stablecoin_overview(sid: str, name: str) -> str:
    """A stablecoin's circulating supply, peg, and chain distribution. Source: DeFiLlama."""
    try:
        info = requests.get(f"https://stablecoins.llama.fi/stablecoin/{sid}",
                            headers=HEAD, timeout=15).json()
    except Exception as e:
        return f"Could not load stablecoin {name}: {e}"

    def circ(d):
        return (d or {}).get("peggedUSD") or 0
    chain_circ = info.get("chainBalances") or {}
    totals = {ch: circ((d.get("tokens") or [{}])[-1].get("circulating"))
              for ch, d in chain_circ.items()}
    total = sum(totals.values())
    price = info.get("price")
    peg = f"${price:.4f}" if isinstance(price, (int, float)) else "—"
    dev = f"{(price-1)*10000:+.0f} bps" if isinstance(price, (int, float)) else ""

    out = [
        f"{info.get('name', name)} ({info.get('symbol','')}) — Stablecoin",
        f"Source: DeFiLlama · pegged to {info.get('pegType','USD').replace('peggedUSD','USD')}",
        "",
        f"  {'Circulating':<18} {_fmt(total)}",
        f"  {'Price / peg':<18} {peg}   {dev}",
        "",
        "  By chain:",
    ]
    for ch, v in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:8]:
        if v <= 0:
            continue
        share = f"{v/total*100:.0f}%" if total else "—"
        out.append(f"  {ch[:18]:<20}{_fmt(v):>14}  {share:>5}")
    return "\n".join(out)


def stablecoin_supply_series(sid: str, period_days: int = 365):
    """[(values)] of a stablecoin's circulating supply for charting."""
    try:
        data = requests.get(f"https://stablecoins.llama.fi/stablecoincharts/all",
                            params={"stablecoin": sid}, headers=HEAD, timeout=20).json()
        vals = [(d.get("totalCirculating") or {}).get("peggedUSD") for d in data]
        vals = [v for v in vals if v is not None][-period_days:]
        return vals or None
    except Exception:
        return None


def chain_tvl_series(slug: str, period_days: int = 365):
    """[(label, values)] of TVL for charting a chain subject."""
    try:
        hist = _get(f"/v2/historicalChainTvl/{slug}")
        vals = [h["tvl"] for h in hist][-period_days:]
        return vals or None
    except Exception:
        return None
