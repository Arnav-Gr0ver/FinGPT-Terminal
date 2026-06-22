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


