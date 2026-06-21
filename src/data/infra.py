"""Real-economy / infrastructure sensors (free, no key).

  • USGS streamflow      — major-river flow (drought, barge shipping, hydro)  → water
  • FAA NAS status       — airport ground delays / stops                      → airports
  • NOAA NWS             — active weather alerts by type                      → alerts
  • TSA                  — daily passenger throughput (air-travel demand)     → travel
"""

import re

from src.data.http import get, get_json

# Major river gauges: (USGS site, river/location).
_GAUGES = [
    ("07010000", "Mississippi @ St. Louis"),
    ("05587450", "Mississippi @ Grafton IL"),
    ("03612600", "Ohio @ Olmsted"),
    ("06934500", "Missouri @ Hermann"),
    ("09380000", "Colorado @ Lees Ferry"),
    ("14105700", "Columbia @ The Dalles"),
]


def river_flow() -> str:
    out = ["Major River Flows — Water & Logistics",
           "Source: USGS Water Services · discharge (cubic ft/s)", "",
           f"  {'River / gauge':<28}{'Flow (cfs)':>14}", "  " + "─" * 44]
    got = False
    for site, label in _GAUGES:
        try:
            j = get_json("https://waterservices.usgs.gov/nwis/iv/",
                         params={"format": "json", "sites": site, "parameterCd": "00060"}, timeout=12)
            ts = j["value"]["timeSeries"]
            val = ts[0]["values"][0]["value"][-1]["value"] if ts else None
            if val is not None:
                got = True
                out.append(f"  {label:<28}{float(val):>14,.0f}")
        except Exception:
            continue
    if not got:
        return "River-flow data is unavailable right now."
    out += ["", "  Low flow on the Mississippi/Ohio constrains barge grain & fuel shipping."]
    return "\n".join(out)


def airport_delays() -> str:
    """US airport ground-delay programs, ground stops, and closures. Source: FAA."""
    try:
        xml = get("https://nasstatus.faa.gov/api/airport-status-information", timeout=15).text
    except Exception as e:
        return f"Could not fetch FAA airport status: {e}"

    def block(tag):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", xml, re.S)
        return m.group(1) if m else ""

    out = ["US Airport Status — Delays & Disruptions", "Source: FAA NAS Status", ""]
    sections = [("Ground_Delay_Programs", "Ground delay programs"),
                ("Ground_Stop_Programs", "Ground stops"),
                ("Airport_Closures", "Closures"),
                ("Arrival_Departure_Delay_List", "Arrival/departure delays")]
    any_ = False
    for tag, label in sections:
        body = block(tag)
        arpts = re.findall(r"<ARPT>([^<]+)</ARPT>", body)
        if not arpts:
            continue
        any_ = True
        out.append(f"  {label}  ({len(arpts)}):")
        reasons = re.findall(r"<Reason>([^<]+)</Reason>", body)
        for i, a in enumerate(arpts[:8]):
            why = (reasons[i][:34] if i < len(reasons) else "")
            out.append(f"    {a:<6} {why}")
        out.append("")
    if not any_:
        return ("US Airport Status — Delays & Disruptions\nSource: FAA NAS Status\n\n"
                "  No ground delays, stops, or closures reported right now.")
    return "\n".join(out).rstrip()


_ALERT_WEIGHT = {"Warning": "█", "Watch": "▓", "Advisory": "▒", "Statement": "░"}


def weather_alerts() -> str:
    """Active US weather alerts grouped by event type — an insurance / agriculture /
    energy-demand sensor. Source: NOAA National Weather Service."""
    try:
        j = get_json("https://api.weather.gov/alerts/active",
                     params={"status": "actual", "message_type": "alert"}, timeout=15)
    except Exception as e:
        return f"Could not fetch weather alerts: {e}"
    feats = j.get("features", [])
    if not feats:
        return "No active US weather alerts right now."
    from collections import Counter
    events = Counter(f["properties"].get("event", "Other") for f in feats)
    severe = sum(1 for f in feats if f["properties"].get("severity") in ("Severe", "Extreme"))

    out = ["Active US Weather Alerts", f"Source: NOAA NWS · {len(feats):,} active · {severe} severe/extreme",
           "", f"  {'Event':<30}{'Count':>7}", "  " + "─" * 40]
    peak = events.most_common(1)[0][1] if events else 1
    for ev, c in events.most_common(14):
        bar = "█" * min(int(c / peak * 12), 12)
        out.append(f"  {ev[:29]:<30}{c:>7}  {bar}")
    return "\n".join(out)


def tsa_travel(n: int = 12) -> str:
    """TSA daily passenger throughput — a near-real-time air-travel demand proxy.
    Source: TSA."""
    try:
        import io
        import pandas as pd
        html = get("https://www.tsa.gov/travel/passenger-volumes", timeout=15).text
        df = pd.read_html(io.StringIO(html))[0]
    except Exception as e:
        return f"Could not fetch TSA passenger volumes: {e}"
    cols = list(df.columns)
    date_c = cols[0]
    num_c = next((c for c in cols[1:]), cols[-1])
    rows = df[[date_c, num_c]].dropna().values.tolist()[:n]
    if not rows:
        return "No TSA throughput data available right now."

    nums = []
    out = ["TSA Passenger Throughput — Air-Travel Demand",
           "Source: TSA", "", f"  {'Date':<14}{'Travelers':>14}", "  " + "─" * 32]
    for d, v in rows:
        try:
            v = int(v)
            nums.append(v)
            out.append(f"  {str(d):<14}{v:>14,}")
        except (TypeError, ValueError):
            continue
    if nums:
        avg = sum(nums) / len(nums)
        out += ["", f"  {len(nums)}-day average: {avg:,.0f}/day"]
    return "\n".join(out)
