"""Crypto data — CoinGecko (market data) + yfinance (live price)."""

import requests

COINGECKO = "https://api.coingecko.com/api/v3"
HEADERS   = {"User-Agent": "FinGPT-Terminal/0.1.0"}

# Common symbol → CoinGecko id mappings
_SYMBOL_MAP = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "BNB": "binancecoin", "XRP": "ripple", "ADA": "cardano",
    "AVAX": "avalanche-2", "DOGE": "dogecoin", "TRX": "tron",
    "LINK": "chainlink", "DOT": "polkadot", "MATIC": "matic-network",
    "LTC": "litecoin", "UNI": "uniswap", "ATOM": "cosmos",
    "BCH": "bitcoin-cash", "XLM": "stellar", "NEAR": "near",
    "APT": "aptos", "ARB": "arbitrum", "OP": "optimism",
    "SHIB": "shiba-inu", "PEPE": "pepe", "SUI": "sui",
}

# Canonical set of symbols the terminal routes to CoinGecko instead of yfinance.
CRYPTO_SYMBOLS = set(_SYMBOL_MAP)


def is_crypto(symbol: str) -> bool:
    """True if `symbol` should be treated as a crypto asset."""
    return symbol.upper().strip() in CRYPTO_SYMBOLS


def _cg(path: str, params: dict = None):
    r = requests.get(f"{COINGECKO}{path}", params=params or {}, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()




def _large(n) -> str:
    if n is None:
        return "N/A"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "N/A"
    if abs(n) >= 1e12:
        return f"${n/1e12:.2f}T"
    if abs(n) >= 1e9:
        return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n/1e6:.2f}M"
    return f"${n:,.2f}"


def get_crypto_quote(symbol: str) -> str:
    sym = symbol.upper().strip()
    cg_id = _SYMBOL_MAP.get(sym)

    try:
        if cg_id:
            data = _cg(f"/coins/{cg_id}", params={"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"})
            mkt  = data.get("market_data", {})

            price      = mkt.get("current_price", {}).get("usd")
            change_24h = mkt.get("price_change_percentage_24h")
            change_7d  = mkt.get("price_change_percentage_7d")
            change_30d = mkt.get("price_change_percentage_30d")
            mktcap     = mkt.get("market_cap", {}).get("usd")
            vol        = mkt.get("total_volume", {}).get("usd")
            hi24       = mkt.get("high_24h", {}).get("usd")
            lo24       = mkt.get("low_24h", {}).get("usd")
            hi52       = mkt.get("ath", {}).get("usd")
            lo52       = mkt.get("atl", {}).get("usd")
            supply     = mkt.get("circulating_supply")
            rank       = data.get("market_cap_rank")
            name       = data.get("name", sym)

            def _chg(v):
                if v is None:
                    return "N/A"
                s = "+" if v >= 0 else ""
                return f"{s}{v:.2f}%"

            w = 18
            lines = [
                f"{name} ({sym})",
                f"Rank #{rank}" if rank else "",
                "",
                f"  {'Price':<{w}} ${price:,.4f}" if price and price < 1 else
                f"  {'Price':<{w}} ${price:,.2f}" if price else f"  {'Price':<{w}} N/A",
                f"  {'24h Change':<{w}} {_chg(change_24h)}",
                f"  {'7d Change':<{w}} {_chg(change_7d)}",
                f"  {'30d Change':<{w}} {_chg(change_30d)}",
                "",
                f"  {'24h High':<{w}} {_large(hi24)}",
                f"  {'24h Low':<{w}} {_large(lo24)}",
                f"  {'All-Time High':<{w}} {_large(hi52)}",
                "",
                f"  {'Market Cap':<{w}} {_large(mktcap)}",
                f"  {'24h Volume':<{w}} {_large(vol)}",
                f"  {'Circulating Supply':<{w}} {supply:,.0f} {sym}" if supply else f"  {'Circulating Supply':<{w}} N/A",
            ]
            return "\n".join(l for l in lines if l or l == "")
        else:
            # Fall back to yfinance for unknown symbols
            import yfinance as yf
            t    = yf.Ticker(f"{sym}-USD")
            fast = t.fast_info
            price  = fast.last_price
            prev   = fast.previous_close or price
            change = price - prev
            pct    = change / prev * 100 if prev else 0
            sign   = "+" if change >= 0 else ""
            w = 18
            lines = [
                f"{sym} / USD",
                "",
                f"  {'Price':<{w}} ${price:,.4f}" if price < 1 else f"  {'Price':<{w}} ${price:,.2f}",
                f"  {'24h Change':<{w}} {sign}{pct:.2f}%",
            ]
            return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch price for {sym}: {e}"


def get_top_coins(limit: int = 20) -> str:
    try:
        coins = _cg("/coins/markets", params={
            "vs_currency": "usd",
            "order":       "market_cap_desc",
            "per_page":    limit,
            "page":        1,
            "sparkline":   "false",
        })

        lines = [
            f"Top {limit} Coins by Market Cap",
            "",
            f"  {'#':<4} {'Coin':<14} {'Price':>12} {'24h':>8} {'7d':>8} {'Market Cap':>14} {'Volume':>12}",
            "  " + "─" * 74,
        ]

        for c in coins:
            rank   = c.get("market_cap_rank") or "?"
            name   = (c.get("symbol") or "?").upper()
            price  = c.get("current_price") or 0
            chg24  = c.get("price_change_percentage_24h") or 0
            chg7   = c.get("price_change_percentage_7d_in_currency") or 0
            mktcap = c.get("market_cap") or 0
            vol    = c.get("total_volume") or 0

            price_s = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
            chg24_s = f"{chg24:+.2f}%"
            chg7_s  = f"{chg7:+.2f}%"
            mkt_s   = _large(mktcap)
            vol_s   = _large(vol)

            lines.append(
                f"  {rank:<4} {name:<14} {price_s:>12} {chg24_s:>8} {chg7_s:>8} {mkt_s:>14} {vol_s:>12}"
            )

        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch top coins: {e}"


def get_global_dominance() -> str:
    try:
        data   = _cg("/global")
        global_ = data.get("data", {})

        total_mktcap = global_.get("total_market_cap", {}).get("usd")
        total_vol    = global_.get("total_volume", {}).get("usd")
        dom          = global_.get("market_cap_percentage", {})
        btc_dom      = dom.get("btc")
        eth_dom      = dom.get("eth")
        others       = 100 - (btc_dom or 0) - (eth_dom or 0)
        n_coins      = global_.get("active_cryptocurrencies")
        defi_pct     = global_.get("defi_market_cap")

        w = 26
        lines = [
            "Crypto Market Overview",
            "",
            f"  {'Total Market Cap':<{w}} {_large(total_mktcap)}",
            f"  {'24h Volume':<{w}} {_large(total_vol)}",
            f"  {'Active Coins':<{w}} {n_coins:,}" if n_coins else "",
            "",
            "Market Dominance",
            "",
        ]

        bar_w = 40
        if btc_dom:
            btc_bar = "█" * int(btc_dom / 100 * bar_w)
            lines.append(f"  BTC  {btc_dom:.1f}%  {btc_bar}")
        if eth_dom:
            eth_bar = "░" * int(eth_dom / 100 * bar_w)
            lines.append(f"  ETH  {eth_dom:.1f}%  {eth_bar}")
        if btc_dom and eth_dom:
            oth_bar = "·" * int(others / 100 * bar_w)
            lines.append(f"  ALT  {others:.1f}%  {oth_bar}")

        return "\n".join(l for l in lines if l is not None)
    except Exception as e:
        return f"Could not fetch global crypto data: {e}"


def get_trending() -> str:
    """CoinGecko trending search — the coins users are looking up most right now."""
    try:
        data = _cg("/search/trending")
    except Exception as e:
        return f"Could not fetch trending coins: {e}"
    coins = data.get("coins", [])
    if not coins:
        return "No trending data available."

    lines = [
        "Trending Coins  (most-searched on CoinGecko, last 24h)",
        "Source: CoinGecko",
        "",
        f"  {'#':<3} {'Coin':<10} {'Name':<22} {'Price':>12} {'24h':>8} {'Rank':>6}",
        "  " + "─" * 66,
    ]
    for i, c in enumerate(coins[:15], 1):
        it    = c.get("item", {}) or {}
        d     = it.get("data", {}) or {}
        sym   = (it.get("symbol") or "?").upper()[:9]
        name  = (it.get("name") or "")[:21]
        price = d.get("price")
        chg   = (d.get("price_change_percentage_24h") or {}).get("usd") if isinstance(d.get("price_change_percentage_24h"), dict) else None
        rank  = it.get("market_cap_rank")
        try:
            price_s = (f"${float(price):,.4f}" if float(price) < 1 else f"${float(price):,.2f}") if price is not None else "—"
        except (TypeError, ValueError):
            price_s = "—"
        chg_s  = f"{chg:+.1f}%" if isinstance(chg, (int, float)) else "—"
        rank_s = f"#{rank}" if rank else "—"
        lines.append(f"  {i:<3} {sym:<10} {name:<22} {price_s:>12} {chg_s:>8} {rank_s:>6}")
    return "\n".join(lines)


def get_treasuries(coin: str = "bitcoin") -> str:
    """Public companies holding BTC/ETH on their balance sheet. Source: CoinGecko."""
    coin = "ethereum" if coin.lower() in ("eth", "ethereum") else "bitcoin"
    try:
        j = _cg(f"/companies/public_treasury/{coin}")
    except Exception as e:
        return f"Could not fetch corporate treasuries: {e}"
    companies = j.get("companies") or []
    if not companies:
        return "No corporate-treasury data available."
    sym = "BTC" if coin == "bitcoin" else "ETH"
    total = j.get("total_holdings") or 0
    val = j.get("total_value_usd") or 0
    out = [
        f"Corporate {sym} Treasuries",
        f"Source: CoinGecko · {total:,.0f} {sym} held · {_large(val)} total",
        "",
        f"  {'Company':<26}{'Holdings':>14}{'Value':>12}",
        "  " + "─" * 54,
    ]
    for c in companies[:15]:
        h = c.get("total_holdings") or 0
        v = c.get("total_current_value_usd") or 0
        out.append(f"  {str(c.get('name',''))[:25]:<26}{h:>12,.0f} {sym}{_large(v):>12}")
    return "\n".join(out)


def get_btc_network() -> str:
    """Bitcoin network health — hashrate, difficulty, throughput, and current fee
    market. Sources: blockchain.info (network stats) + mempool.space (fees)."""
    from src.data.http import get_json
    try:
        s = get_json("https://api.blockchain.info/stats", timeout=15)
    except Exception as e:
        return f"Could not fetch Bitcoin network stats: {e}"

    price   = s.get("market_price_usd")
    hr_ghs  = s.get("hash_rate")            # GH/s
    diff    = s.get("difficulty")
    n_tx    = s.get("n_tx")                 # tx in last 24h
    blk_min = s.get("minutes_between_blocks")
    vol_usd = s.get("trade_volume_usd")
    mined   = s.get("n_btc_mined")
    hr_ehs  = (hr_ghs / 1e9) if isinstance(hr_ghs, (int, float)) else None

    fees = None
    try:
        fees = get_json("https://mempool.space/api/v1/fees/recommended", timeout=10)
    except Exception:
        fees = None

    w = 26
    lines = [
        "Bitcoin Network — On-Chain Health",
        "Sources: blockchain.info · mempool.space",
        "",
    ]
    if isinstance(price, (int, float)):
        lines.append(f"  {'Price':<{w}} ${price:,.0f}")
    if hr_ehs:
        lines.append(f"  {'Hash rate':<{w}} {hr_ehs:,.0f} EH/s")
    if isinstance(diff, (int, float)):
        lines.append(f"  {'Difficulty':<{w}} {diff/1e12:,.1f} T")
    if isinstance(blk_min, (int, float)):
        lines.append(f"  {'Avg block time':<{w}} {blk_min:.1f} min")
    if isinstance(n_tx, (int, float)):
        lines.append(f"  {'Transactions (24h)':<{w}} {n_tx:,}")
    if vol_usd:
        lines.append(f"  {'Est. exchange volume':<{w}} {_large(vol_usd)}")
    if fees:
        lines += [
            "",
            "  Fee market (sat/vB):",
            f"  {'Next block (fastest)':<{w}} {fees.get('fastestFee', '—')}",
            f"  {'~30 min':<{w}} {fees.get('halfHourFee', '—')}",
            f"  {'~1 hour':<{w}} {fees.get('hourFee', '—')}",
            f"  {'Economy':<{w}} {fees.get('economyFee', '—')}",
        ]
    return "\n".join(lines)
