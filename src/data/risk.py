"""Risk / disruption signals — USGS earthquakes + GDELT news tone (free, no key).

A coarse 'what could disrupt this' read: recent major earthquakes worldwide (a
supply-chain / disaster sensor) plus the news tone for the subject from GDELT's
global news graph.
"""

import csv
import io
import requests
from datetime import datetime, timedelta

from src.data.http import get

HEAD = {"User-Agent": "FinGPT-Terminal/0.1"}
USGS = "https://earthquake.usgs.gov/fdsnws/event/1/query"
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
OFR_FSI = "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv"


def recent_quakes(min_mag: float = 6.0, days: int = 14) -> list[str]:
    try:
        start = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        r = requests.get(USGS, params={
            "format": "geojson", "starttime": start,
            "minmagnitude": min_mag, "orderby": "time", "limit": 8,
        }, headers=HEAD, timeout=12)
        r.raise_for_status()
        feats = r.json().get("features", [])
        lines = []
        for f in feats:
            p = f["properties"]
            t = datetime.utcfromtimestamp(p["time"] / 1000).strftime("%b %d")
            lines.append(f"  M{p['mag']:.1f}  {t}  {p.get('place', '')[:46]}")
        return lines
    except Exception:
        return []


def news_tone(query: str) -> str | None:
    """Average GDELT tone for a subject over the last week (− bearish, + bullish)."""
    try:
        r = requests.get(GDELT, params={
            "query": f'"{query}"', "mode": "timelinetone",
            "format": "json", "timespan": "1w",
        }, headers=HEAD, timeout=12)
        r.raise_for_status()
        series = r.json().get("timeline", [])
        vals = [pt["value"] for s in series for pt in s.get("data", [])]
        if not vals:
            return None
        avg = sum(vals) / len(vals)
        mood = "negative" if avg < -1 else "positive" if avg > 1 else "neutral"
        return f"{avg:+.2f} ({mood})"
    except Exception:
        return None


def risk_report(subject_label: str, query: str) -> str:
    out = [f"Risk & Disruption — {subject_label}", "Sources: USGS, GDELT", ""]
    tone = news_tone(query)
    out.append(f"  News tone (1w)   {tone if tone else '—'}   [GDELT global news]")
    out.append("")
    quakes = recent_quakes()
    if quakes:
        out.append("  Major earthquakes (M6+, 14d) — supply-chain / disaster sensor:")
        out += quakes
    else:
        out.append("  No major (M6+) earthquakes in the last 14 days.")
    return "\n".join(out)
