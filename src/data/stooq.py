"""Stooq CSV price data (free, no key) — a fallback when yfinance flakes."""

import csv
import io
import requests

HEAD = {"User-Agent": "FinGPT-Terminal/0.1"}


def _stooq_symbol(symbol: str) -> str:
    s = symbol.lower()
    # US equities/ETFs need a .us suffix on Stooq; indices/fx already carry theirs.
    if s.startswith("^") or "=" in s or "." in s:
        return s
    return f"{s}.us"


def get_closes(symbol: str, interval: str = "d") -> list[float]:
    """Daily closes (oldest→newest) for a symbol, or [] on failure."""
    try:
        url = "https://stooq.com/q/d/l/"
        r = requests.get(url, params={"s": _stooq_symbol(symbol), "i": interval},
                         headers=HEAD, timeout=12)
        r.raise_for_status()
        text = r.text.strip()
        if not text or text.lower().startswith("<"):
            return []
        reader = csv.DictReader(io.StringIO(text))
        closes = []
        for row in reader:
            try:
                closes.append(float(row["Close"]))
            except (KeyError, ValueError):
                pass
        return closes
    except Exception:
        return []
