"""Local symbol index for instant completion (SEC ticker list, cached to disk).

Live Yahoo search is too slow to run on every keystroke, so we cache the SEC's
public company_tickers.json (~10k US tickers + names) and prefix-search it
locally. Built once in the background at startup; refreshed if the cache is gone.
"""

import json
import threading
from pathlib import Path

import requests

CACHE   = Path.home() / ".fingpt" / "symbols.json"
SEC_URL = "https://www.sec.gov/files/company_tickers.json"
HEAD    = {"User-Agent": "FinGPT Terminal research@fingpt.ai"}

_index: list = []          # [(SYMBOL, name)]
_loaded = False
_lock = threading.Lock()


def _build_from_sec() -> list:
    r = requests.get(SEC_URL, headers=HEAD, timeout=20)
    r.raise_for_status()
    out = []
    for e in r.json().values():
        t = (e.get("ticker") or "").upper()
        if t:
            out.append([t, e.get("title") or t])
    return out


def ensure_index():
    """Load the index from cache, or build it from SEC. Safe to call repeatedly."""
    global _index, _loaded
    with _lock:
        if _loaded:
            return
    idx = []
    try:
        if CACHE.exists():
            idx = json.loads(CACHE.read_text())
    except Exception:
        idx = []
    if not idx:
        try:
            idx = _build_from_sec()
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(json.dumps(idx))
        except Exception:
            idx = []
    with _lock:
        _index = idx
        _loaded = True


def ready() -> bool:
    return _loaded and bool(_index)


def search(prefix: str, limit: int = 8) -> list[tuple[str, str]]:
    """Tickers whose symbol starts with `prefix`, then symbol/name contains it."""
    p = prefix.upper()
    if not p or not _index:
        return []
    starts, contains = [], []
    for sym, name in _index:
        if sym.startswith(p):
            starts.append((sym, name))
            if len(starts) >= limit:
                break
        elif len(contains) < limit and (p in sym or p in name.upper()):
            contains.append((sym, name))
    res = starts[:limit]
    if len(res) < limit:
        res += [c for c in contains if c not in res][: limit - len(res)]
    return res
