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


def disaster_declarations(n: int = 12) -> str:
    """Recent US federal disaster declarations — a supply-chain / insurance /
    regional-economy risk sensor. Source: FEMA OpenFEMA (no key)."""
    try:
        j = get("https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries",
                params={"$orderby": "declarationDate desc", "$top": 200,
                        "$select": "declarationDate,state,incidentType,declarationTitle,fyDeclared"},
                timeout=15)
        j.raise_for_status()
        data = j.json().get("DisasterDeclarationsSummaries", [])
    except Exception as e:
        return f"Could not fetch FEMA disaster declarations: {e}"
    if not data:
        return "No recent disaster-declaration data available."

    seen, rows = set(), []
    for d in data:
        key = (d.get("declarationTitle"), d.get("state"))
        if key in seen:
            continue
        seen.add(key)
        rows.append(d)
        if len(rows) >= n:
            break

    out = [
        "US Federal Disaster Declarations — Recent",
        "Source: FEMA OpenFEMA",
        "",
        f"  {'Declared':<12}{'State':<7}{'Type':<14}Title",
        "  " + "─" * 58,
    ]
    for d in rows:
        date = (d.get("declarationDate") or "")[:10]
        st = (d.get("state") or "")[:5]
        typ = (d.get("incidentType") or "")[:13]
        title = (d.get("declarationTitle") or "").title()[:26]
        out.append(f"  {date:<12}{st:<7}{typ:<14}{title}")
    return "\n".join(out)


def financial_stress() -> str:
    """OFR Financial Stress Index — a daily, market-based gauge of system-wide
    stress. Zero is the long-run average; positive = stress above normal,
    negative = calmer than normal. Built from five categories across regions."""
    try:
        r = get(OFR_FSI, timeout=15)
        r.raise_for_status()
        rows = list(csv.reader(io.StringIO(r.text)))
    except Exception as e:
        return f"Could not fetch the OFR Financial Stress Index: {e}"

    if len(rows) < 2:
        return "Financial Stress Index data is unavailable right now."
    header = rows[0]
    data = [row for row in rows[1:] if row and row[0]]
    if not data:
        return "Financial Stress Index data is unavailable right now."

    def val(row, i):
        try:
            return float(row[i])
        except (ValueError, IndexError):
            return None

    latest = data[-1]
    date = latest[0]
    fsi = val(latest, 1)

    def ago(days):
        target = datetime.strptime(date, "%Y-%m-%d") - timedelta(days=days)
        for row in reversed(data):
            try:
                if datetime.strptime(row[0], "%Y-%m-%d") <= target:
                    return val(row, 1)
            except ValueError:
                continue
        return None

    def trend(old):
        if fsi is None or old is None:
            return "—"
        d = fsi - old
        return f"{d:+.2f}  ({'tighter' if d > 0 else 'easier'})"

    regime = ("elevated stress" if (fsi or 0) > 1 else
              "above-average stress" if (fsi or 0) > 0 else
              "below-average / calm" if (fsi or 0) > -2 else "very calm")

    out = [
        "OFR Financial Stress Index  (0 = long-run average)",
        f"Source: U.S. Office of Financial Research · {date}",
        "",
        f"  Index            {fsi:+.2f}   ({regime})" if fsi is not None else "  Index            —",
        f"  1-month          {trend(ago(30))}",
        f"  1-year           {trend(ago(365))}",
        "",
        "  Category contributions (latest):",
    ]
    # Columns 2.. are the category/region breakdowns from the CSV header.
    for i in range(2, min(len(header), len(latest))):
        v = val(latest, i)
        if v is None:
            continue
        bar_n = min(int(abs(v) * 4), 16)
        bar = ("█" if v >= 0 else "▒") * bar_n
        out.append(f"  {header[i][:22]:<22} {v:>+6.2f}  {bar}")
    return "\n".join(out)


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
