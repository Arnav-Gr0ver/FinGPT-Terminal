"""Shared HTTP — one pooled session with retries, so every connector gets the
same resilient behaviour (transient 5xx / rate-limit retries, keep-alive) and a
consistent User-Agent. New data modules should fetch through here."""

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except Exception:                       # pragma: no cover
    Retry = None

DEFAULT_HEADERS = {
    "User-Agent": "FinR1-Terminal/0.2 (+https://fingpt.ai research@fingpt.ai)",
    "Accept-Encoding": "gzip, deflate",
}

_session = None


def session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        if Retry is not None:
            retry = Retry(
                total=2, connect=2, read=2, backoff_factor=0.4,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset(["GET"]),
            )
            s.mount("https://", HTTPAdapter(max_retries=retry))
            s.mount("http://", HTTPAdapter(max_retries=retry))
        s.headers.update(DEFAULT_HEADERS)
        _session = s
    return _session


def get(url, params=None, timeout=15, headers=None):
    return session().get(url, params=params, timeout=timeout, headers=headers)


def get_json(url, params=None, timeout=15, headers=None):
    r = get(url, params=params, timeout=timeout, headers=headers)
    r.raise_for_status()
    return r.json()
