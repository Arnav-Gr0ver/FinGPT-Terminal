"""Symbol resolution — turn company / asset names into tickers (Yahoo search)."""

import re
import requests
from src.data.crypto import is_crypto, _SYMBOL_MAP

# Reverse of the CoinGecko map: the coin "id" is effectively its name, so
# "bitcoin" -> BTC, "ethereum" -> ETH. Lets us resolve coin names with no
# network call and without losing them to look-alike equities/trusts.
_CRYPTO_NAMES = {cg_id.replace("-", " "): sym for sym, cg_id in _SYMBOL_MAP.items()}

_SEARCH  = "https://query2.finance.yahoo.com/v1/finance/search"
HEADERS  = {"User-Agent": "Mozilla/5.0 (FinGPT-Terminal)"}

# Already a plausible ticker: 1–5 uppercase letters, optional .X suffix (BRK.B).
_TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")

_TYPE_MAP = {
    "equity":         "equity",
    "etf":            "etf",
    "cryptocurrency": "crypto",
    "index":          "index",
    "currency":       "fx",
    "mutualfund":     "fund",
}


def looks_like_ticker(token: str) -> bool:
    # A symbol the user typed *as* a symbol is already upper-case (AAPL, BRK.B).
    # A lower-case word like "apple" is a name to search, not a ticker.
    t = token.strip()
    return bool(_TICKER_RE.match(t)) or is_crypto(t)


def search_symbols(query: str, limit: int = 6) -> list[dict]:
    """Return candidate {symbol, name, type, exchange} dicts for a free-text query."""
    try:
        r = requests.get(
            _SEARCH,
            params={"q": query, "quotesCount": limit, "newsCount": 0},
            headers=HEADERS,
            timeout=8,
        )
        r.raise_for_status()
        quotes = r.json().get("quotes", [])
    except Exception:
        return []

    out = []
    for q in quotes:
        raw = q.get("symbol", "")
        if not raw:
            continue
        kind = _TYPE_MAP.get((q.get("quoteType") or "").lower(), "other")
        # CoinGecko/yfinance use the bare symbol for crypto (BTC, not BTC-USD).
        symbol = raw[:-4] if (kind == "crypto" and raw.endswith("-USD")) else raw
        name   = (q.get("shortname") or q.get("longname") or "").strip() or symbol
        out.append({
            "symbol":   symbol,
            "name":     name,
            "type":     kind,
            "exchange": q.get("exchange", ""),
        })
    return out


def resolve_symbol(query: str) -> str | None:
    """Best-effort single ticker for a name or symbol. Returns None if nothing fits.

    Fast path: anything already shaped like a ticker is returned untouched, so
    `AAPL` and `BTC` never hit the network.
    """
    q = query.strip()
    if not q:
        return None
    if looks_like_ticker(q):
        return q.upper()

    ql = q.lower()
    if ql in _CRYPTO_NAMES:          # "bitcoin", "ethereum", "solana", ...
        return _CRYPTO_NAMES[ql]

    candidates = search_symbols(q, limit=8)
    if not candidates:
        return None

    pref    = {"equity": 0, "etf": 1, "crypto": 2, "fund": 3, "index": 4, "fx": 5, "other": 6}
    us_exch = {"NMS", "NYQ", "NGM", "NCM", "PCX", "ASE", "BTS", "NYS", "NCM"}

    def score(c):
        exact = (c["symbol"].lower() == ql)       # "amd" -> AMD beats AUDAMD=X
        named = ql in c["name"].lower()           # query appears in the company name
        us    = c["exchange"] in us_exch          # prefer the US primary listing
        return (0 if exact else 1, pref.get(c["type"], 9), 0 if us else 1, 0 if named else 1)

    return min(candidates, key=score)["symbol"]
