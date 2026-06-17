"""Attention signal — Wikipedia pageviews (free, no key).

A rough proxy for public/investor attention on a subject: daily views of its
Wikipedia article over the last 60 days, with a sparkline and trend.
"""

import requests
from datetime import datetime, timedelta

API  = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents"
HEAD = {"User-Agent": "FinGPT-Terminal/0.1 (research)"}
_SPARK = "▁▂▃▄▅▆▇█"


def pageviews(article: str, label: str = "") -> str:
    title = article.strip().replace(" ", "_")
    end   = datetime.utcnow()
    start = end - timedelta(days=60)
    url = f"{API}/{title}/daily/{start:%Y%m%d}/{end:%Y%m%d}"
    try:
        r = requests.get(url, headers=HEAD, timeout=12)
        if r.status_code == 404:
            return f"No Wikipedia article found for '{label or article}'."
        r.raise_for_status()
        items = r.json().get("items", [])
    except Exception as e:
        return f"Could not fetch attention data for '{label or article}': {e}"
    if not items:
        return f"No pageview data for '{label or article}'."

    views = [it["views"] for it in items]
    lo, hi = min(views), max(views)
    rng = (hi - lo) or 1
    spark = "".join(_SPARK[min(int((v - lo) / rng * 7), 7)] for v in views[-56:])
    recent = sum(views[-7:]) / min(7, len(views))
    base   = sum(views[:7]) / min(7, len(views)) or 1
    chg = (recent / base - 1) * 100

    return "\n".join([
        f"Attention — {label or article}  (Wikipedia pageviews)",
        "Source: Wikimedia REST API", "",
        f"  60-day trend   {spark}",
        f"  Latest day     {views[-1]:,} views",
        f"  7-day avg      {recent:,.0f}/day   ({chg:+.0f}% vs start of window)",
        f"  Peak           {hi:,} views",
    ])
