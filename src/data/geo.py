"""Physical-economy sensors (free, no key).

  • NASA EONET     — open natural-hazard events (wildfires, storms, volcanoes) → hazards
  • OpenSky Network — live count of airborne aircraft (activity proxy)         → flights
"""

from src.data.http import get_json


def hazards(n: int = 14) -> str:
    """Open natural-hazard events worldwide — a supply-chain / insurance sensor.
    Source: NASA EONET."""
    try:
        j = get_json("https://eonet.gsfc.nasa.gov/api/v3/events",
                     params={"status": "open", "limit": 60}, timeout=15)
    except Exception as e:
        return f"Could not fetch hazard events: {e}"
    events = j.get("events") or []
    if not events:
        return "No open hazard events reported right now."
    by_cat = {}
    for e in events:
        cat = (e.get("categories") or [{}])[0].get("title", "Other")
        by_cat[cat] = by_cat.get(cat, 0) + 1

    out = ["Active Natural-Hazard Events", "Source: NASA EONET", "",
           "  By category:"]
    for cat, c in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True):
        out.append(f"  {cat[:24]:<26}{c:>4}")
    out += ["", "  Most recent:", "  " + "─" * 52]
    for e in events[:n]:
        cat = (e.get("categories") or [{}])[0].get("title", "")[:12]
        title = (e.get("title") or "").replace("\n", " ")[:36]
        out.append(f"  {cat:<14}{title}")
    return "\n".join(out)


def flights() -> str:
    """Live count of airborne aircraft worldwide — a real-time global-activity
    proxy. Source: OpenSky Network."""
    try:
        j = get_json("https://opensky-network.org/api/states/all", timeout=20)
    except Exception as e:
        return f"Could not fetch flight data: {e}"
    states = j.get("states") or []
    if not states:
        return "No live flight data available right now."
    airborne = [s for s in states if not s[8]]            # index 8 = on_ground
    by_country = {}
    for s in airborne:
        c = (s[2] or "Unknown").strip()
        by_country[c] = by_country.get(c, 0) + 1

    import datetime
    ts = datetime.datetime.utcfromtimestamp(j.get("time", 0)).strftime("%Y-%m-%d %H:%M UTC")
    out = ["Global Air Traffic — Live Snapshot",
           f"Source: OpenSky Network · {ts}", "",
           f"  {'Aircraft airborne':<22} {len(airborne):,}",
           f"  {'Total tracked':<22} {len(states):,}",
           "", "  By origin country:", "  " + "─" * 36]
    for c, n in sorted(by_country.items(), key=lambda kv: kv[1], reverse=True)[:10]:
        out.append(f"  {c[:24]:<26}{n:>6,}")
    return "\n".join(out)
