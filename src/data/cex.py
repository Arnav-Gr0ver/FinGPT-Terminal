"""Cross-exchange crypto pricing (free, no key).

Queries the same asset's spot price across a wide set of public exchange APIs to
show where it trades and the venue spread, plus on-chain DEX pairs. Every venue
is a public, key-less endpoint; failures are skipped so the board still renders."""

import requests

H = {"User-Agent": "FinR1-Terminal/0.2", "Accept": "application/json"}


def _g(url, params=None):
    return requests.get(url, params=params, headers=H, timeout=8).json()

_PAPRIKA = {"BTC": "btc-bitcoin", "ETH": "eth-ethereum", "SOL": "sol-solana",
            "XRP": "xrp-xrp", "BNB": "bnb-binance-coin", "ADA": "ada-cardano",
            "DOGE": "doge-dogecoin", "AVAX": "avax-avalanche", "LINK": "link-chainlink",
            "MATIC": "matic-polygon", "DOT": "dot-polkadot", "LTC": "ltc-litecoin"}


# Each venue: name -> callable(sym) -> USD/USDT price.  Distinct public APIs.
_VENUES = {
    "Kraken": lambda s: float(next(iter(_g("https://api.kraken.com/0/public/Ticker", {"pair": f"{'XBT' if s=='BTC' else s}USD"})["result"].values()))["c"][0]),
    "Coinbase": lambda s: float(_g(f"https://api.exchange.coinbase.com/products/{s}-USD/ticker")["price"]),
    "OKX": lambda s: float(_g("https://www.okx.com/api/v5/market/ticker", {"instId": f"{s}-USDT"})["data"][0]["last"]),
    "KuCoin": lambda s: float(_g("https://api.kucoin.com/api/v1/market/stats", {"symbol": f"{s}-USDT"})["data"]["last"]),
    "Bitstamp": lambda s: float(_g(f"https://www.bitstamp.net/api/v2/ticker/{s.lower()}usd/")["last"]),
    "Bitfinex": lambda s: float(_g(f"https://api-pub.bitfinex.com/v2/ticker/t{s}USD")[6]),
    "MEXC": lambda s: float(_g("https://api.mexc.com/api/v3/ticker/price", {"symbol": f"{s}USDT"})["price"]),
    "HTX": lambda s: float(_g("https://api.huobi.pro/market/detail/merged", {"symbol": f"{s.lower()}usdt"})["tick"]["close"]),
    "Crypto.com": lambda s: float(_g("https://api.crypto.com/v2/public/get-ticker", {"instrument_name": f"{s}_USDT"})["result"]["data"][0]["a"]),
    "Gemini": lambda s: float(_g(f"https://api.gemini.com/v1/pubticker/{s.lower()}usd")["last"]),
    "Bitget": lambda s: float(_g("https://api.bitget.com/api/v2/spot/market/tickers", {"symbol": f"{s}USDT"})["data"][0]["lastPr"]),
    "Upbit": lambda s: float(_g("https://api.upbit.com/v1/ticker", {"markets": f"USDT-{s}"})[0]["trade_price"]),
    "bitFlyer": lambda s: float(_g("https://api.bitflyer.com/v1/ticker", {"product_code": f"{s}_USD"})["ltp"]),
    "WhiteBIT": lambda s: float(_g("https://whitebit.com/api/v4/public/ticker")[f"{s}_USDT"]["last_price"]),
    "CoinEx": lambda s: float(_g("https://api.coinex.com/v2/spot/ticker", {"market": f"{s}USDT"})["data"][0]["last"]),
    "BitMart": lambda s: float(_g("https://api-cloud.bitmart.com/spot/quotation/v3/ticker", {"symbol": f"{s}_USDT"})["data"]["last"]),
    "Gate.io": lambda s: float(_g("https://api.gateio.ws/api/v4/spot/tickers", {"currency_pair": f"{s}_USDT"})[0]["last"]),
    "HitBTC": lambda s: float(_g(f"https://api.hitbtc.com/api/3/public/ticker/{s}USDT")["last"]),
    "AscendEX": lambda s: float(_g("https://ascendex.com/api/pro/v1/spot/ticker", {"symbol": f"{s}/USDT"})["data"]["close"]),
    "BTSE": lambda s: float(_g("https://api.btse.com/spot/api/v3.2/price", {"symbol": f"{s}-USD"})[0]["indexPrice"]),
    "BingX": lambda s: float(_g("https://open-api.bingx.com/openApi/spot/v1/ticker/24hr", {"symbol": f"{s}-USDT"})["data"][0]["lastPrice"]),
    "DigiFinex": lambda s: float(_g("https://openapi.digifinex.com/v3/ticker", {"symbol": f"{s.lower()}_usdt"})["ticker"][0]["last"]),
    "Bitrue": lambda s: float(_g("https://openapi.bitrue.com/api/v1/ticker/price", {"symbol": f"{s}USDT"})["price"]),
    "Bitso": lambda s: float(_g(f"https://api.bitso.com/v3/ticker/", {"book": f"{s.lower()}_usd"})["payload"]["last"]),
    "BigONE": lambda s: float(_g(f"https://big.one/api/v3/asset_pairs/{s}-USDT/ticker")["data"]["close"]),
    "WazirX": lambda s: float(_g(f"https://api.wazirx.com/api/v2/tickers/{s.lower()}usdt")[f"{s.lower()}usdt"]["last"]),
    "XT": lambda s: float(_g("https://sapi.xt.com/v4/public/ticker", {"symbol": f"{s.lower()}_usdt"})["result"][0]["c"]),
    "WOO X": lambda s: float(_g("https://api.woox.io/v1/public/market_trades", {"symbol": f"SPOT_{s}_USDT", "limit": 1})["rows"][0]["executed_price"]),
    "CoinPaprika (avg)": lambda s: (_g(f"https://api.coinpaprika.com/v1/tickers/{_PAPRIKA[s]}").get("quotes", {}).get("USD", {}).get("price") if s in _PAPRIKA else None),
}

# Regional venues quoting in their home currency — shown separately (no FX guesswork).
_REGIONAL = {
    "Bithumb (KRW)": lambda s: float(_g(f"https://api.bithumb.com/public/ticker/{s}_KRW")["data"]["closing_price"]),
    "Coincheck (JPY)": lambda s: (float(_g("https://coincheck.com/api/ticker")["last"]) if s == "BTC" else None),
    "Indodax (IDR)": lambda s: float(_g(f"https://indodax.com/api/ticker/{s.lower()}idr")["ticker"]["last"]),
}


def price_board(symbol: str) -> str:
    sym = symbol.upper()
    rows = []
    for name, fn in _VENUES.items():
        try:
            p = fn(sym)
            if p and 0 < float(p) < 1e9:
                rows.append((name, float(p)))
        except Exception:
            continue
    if not rows:
        return f"No cross-exchange prices available for {sym}."
    # Drop any venue whose price is >25% off the median (mis-scaled / stale feed),
    # so a single bad quote can't distort the spread.
    med = sorted(p for _, p in rows)[len(rows) // 2]
    rows = [(n, p) for n, p in rows if med * 0.75 <= p <= med * 1.25] or rows
    prices = [p for _, p in rows]
    lo, hi = min(prices), max(prices)
    spread = (hi - lo) / lo * 100 if lo else 0
    rows.sort(key=lambda r: r[1])
    out = [f"Cross-Exchange Price — {sym}", f"Source: {len(rows)} public exchange APIs", "",
           f"  {'Venue':<22}{'Price (USD)':>16}", "  " + "─" * 40]
    for name, p in rows:
        mark = "  ▲" if p == hi else ("  ▼" if p == lo else "")
        out.append(f"  {name:<22}{p:>16,.2f}{mark}")
    out += ["", f"  Venue spread: {spread:.2f}%  (low {lo:,.2f} · high {hi:,.2f}) across {len(rows)} venues"]

    regional = []
    for name, fn in _REGIONAL.items():
        try:
            p = fn(sym)
            if p:
                regional.append((name, float(p)))
        except Exception:
            continue
    if regional:
        out += ["", "  Regional venues (home currency):"]
        for name, p in regional:
            out.append(f"  {name:<22}{p:>18,.0f}")
    return "\n".join(out)


def dex_pairs(query: str, n: int = 10) -> str:
    """Top decentralized-exchange pairs for a token. Sources: DEX Screener,
    with GeckoTerminal as a network/liquidity cross-check."""
    pairs = []
    try:
        pairs = _g("https://api.dexscreener.com/latest/dex/search", {"q": query}).get("pairs") or []
    except Exception:
        pairs = []
    if not pairs:
        try:                                           # fallback to GeckoTerminal search
            gt = _g("https://api.geckoterminal.com/api/v2/search/pools", {"query": query})
            for d in (gt.get("data") or [])[:n]:
                a = d.get("attributes", {})
                pairs.append({"baseToken": {"symbol": a.get("name", "").split("/")[0]},
                              "quoteToken": {"symbol": ""}, "chainId": "", "dexId": "gecko",
                              "priceUsd": a.get("base_token_price_usd"),
                              "liquidity": {"usd": float(a.get("reserve_in_usd") or 0)}})
        except Exception:
            pass
    if not pairs:
        return f"No DEX pairs found for '{query}'."
    pairs.sort(key=lambda p: (p.get("liquidity") or {}).get("usd") or 0, reverse=True)
    out = [f"DEX Pairs — {query.upper()}", "Source: DEX Screener / GeckoTerminal", "",
           f"  {'Pair':<16}{'Chain/DEX':<18}{'Price':>12}{'Liquidity':>13}", "  " + "─" * 60]
    for p in pairs[:n]:
        base = (p.get("baseToken") or {}).get("symbol", "")
        quote = (p.get("quoteToken") or {}).get("symbol", "")
        pair = f"{base}/{quote}".strip("/")[:15]
        venue = f"{p.get('chainId','')}/{p.get('dexId','')}".strip("/")[:17]
        price = p.get("priceUsd")
        liq = (p.get("liquidity") or {}).get("usd") or 0
        price_s = f"${float(price):,.4f}" if price else "—"
        liq_s = f"${liq/1e6:.1f}M" if liq >= 1e6 else f"${liq/1e3:.0f}k"
        out.append(f"  {pair:<16}{venue:<18}{price_s:>12}{liq_s:>13}")
    return "\n".join(out)
