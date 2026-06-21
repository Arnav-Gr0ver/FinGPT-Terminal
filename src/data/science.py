"""Science / weather / energy sensors (free, no key).

  • NOAA SWPC  — geomagnetic storm (Kp) level → satellites, GPS, power-grid risk → spaceweather
  • NOAA NHC   — active tropical cyclones → insurance, energy, agriculture        → hurricanes
  • NOAA Tides — water level at major ports → shipping / draft conditions          → tides
  • UK Carbon Intensity — grid carbon (gCO2/kWh) → energy transition               → gridcarbon
"""

from src.data.http import get, get_json


def biodiversity(iso2: str = "US", name: str = "United States") -> str:
    """Biodiversity occurrence records for a country (works for every country).
    Source: GBIF (Global Biodiversity Information Facility)."""
    iso2 = (iso2 or "US").upper()
    try:
        total = get_json("https://api.gbif.org/v1/occurrence/count", params={"country": iso2}, timeout=12)
        recent = get_json("https://api.gbif.org/v1/occurrence/search",
                          params={"country": iso2, "year": __import__("datetime").date.today().year, "limit": 0}, timeout=12)
    except Exception as e:
        return f"Could not fetch GBIF data: {e}"
    if not isinstance(total, int) or total == 0:
        return f"No GBIF biodiversity records for {name}."
    out = [f"Biodiversity Records — {name}", "Source: GBIF", "",
           f"  {'Total occurrence records':<30} {total:,}",
           f"  {'Recorded this year':<30} {recent.get('count', 0):,}",
           "", "  An open index of species observations — research & ESG adjacent."]
    return "\n".join(out)


def space_weather() -> str:
    try:
        data = get_json("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=15)
    except Exception as e:
        return f"Could not fetch space-weather data: {e}"
    pts = []
    for r in data:
        try:
            if isinstance(r, dict):
                kp = r.get("Kp", r.get("kp_index", r.get("estimated_kp", r.get("kp"))))
                t = r.get("time_tag", "")
            else:                                      # list-of-lists with a header row
                if str(r[1]).lower() in ("kp", "kp_index"):
                    continue
                kp, t = r[1], r[0]
            pts.append((str(t), float(kp)))
        except (ValueError, TypeError, IndexError, KeyError):
            continue
    pts = pts[-24:]
    if not pts:
        return "Space-weather data is unavailable right now."
    t, kp = pts[-1]
    peak = max(p[1] for p in pts)
    scale = ("G1 minor" if peak >= 5 else "quiet") if peak < 6 else \
            ("G2 moderate" if peak < 7 else "G3+ strong — grid/sat risk")
    spark = "".join("▁▂▃▄▅▆▇█"[min(int(p[1]), 7)] for p in pts)
    return "\n".join([
        "Space Weather — Geomagnetic Activity",
        f"Source: NOAA SWPC · {t[:16]} UTC",
        "",
        f"  Current Kp index    {kp:.1f}",
        f"  24h peak Kp         {peak:.1f}   ({scale})",
        f"  24h trend           {spark}",
        "",
        "  Kp ≥ 5 = geomagnetic storm — can disrupt satellites, GPS, and grids.",
    ])


def hurricanes() -> str:
    try:
        j = get_json("https://www.nhc.noaa.gov/CurrentStorms.json", timeout=15)
    except Exception as e:
        return f"Could not fetch hurricane data: {e}"
    storms = j.get("activeStorms") or []
    if not storms:
        return ("Tropical Cyclones — Active Systems\nSource: NOAA NHC\n\n"
                "  No active named storms right now.")
    out = ["Tropical Cyclones — Active Systems", "Source: NOAA National Hurricane Center", "",
           f"  {'Name':<16}{'Class':<14}{'Winds':>8}  Basin", "  " + "─" * 50]
    for s in storms:
        name = (s.get("name") or "")[:15]
        cls = (s.get("classification") or s.get("tcType") or "")[:13]
        wind = s.get("intensity") or s.get("maxSustainedWind") or "—"
        basin = s.get("binNumber", "")[:4] or s.get("basin", "")
        out.append(f"  {name:<16}{cls:<14}{str(wind)+' kt':>8}  {basin}")
    return "\n".join(out)


# A few major US port tide stations (NOAA CO-OPS).
_PORTS = [("9410660", "Los Angeles"), ("8518750", "New York (Battery)"),
          ("8443970", "Boston"), ("8771450", "Galveston"), ("9414290", "San Francisco"),
          ("8594900", "Washington DC")]


def port_tides() -> str:
    out = ["Port Water Levels — Tides", "Source: NOAA CO-OPS · feet rel. MLLW", "",
           f"  {'Port':<22}{'Water level':>14}", "  " + "─" * 40]
    got = False
    for station, label in _PORTS:
        try:
            j = get_json("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter", params={
                "product": "water_level", "date": "latest", "station": station,
                "datum": "MLLW", "time_zone": "gmt", "units": "english", "format": "json"}, timeout=10)
            v = (j.get("data") or [{}])[0].get("v")
            if v is not None:
                got = True
                out.append(f"  {label:<22}{float(v):>11.2f} ft")
        except Exception:
            continue
    if not got:
        return "Port tide data is unavailable right now."
    return "\n".join(out)


def volcanoes() -> str:
    """Volcanoes at elevated alert level (US + global). Source: USGS Volcano Hazards."""
    try:
        data = get_json("https://volcanoes.usgs.gov/hans-public/api/volcano/getElevatedVolcanoes", timeout=15)
    except Exception as e:
        return f"Could not fetch volcano alerts: {e}"
    rows = data if isinstance(data, list) else data.get("items", [])
    if not rows:
        return ("Volcanic Activity — Elevated Alerts\nSource: USGS\n\n"
                "  No US volcanoes above normal alert level right now.")
    out = ["Volcanic Activity — Elevated Alert Levels", "Source: USGS Volcano Hazards Program", "",
           f"  {'Volcano':<24}{'Alert':<12}Aviation", "  " + "─" * 48]
    for v in rows[:14]:
        nm = (v.get("volcano_name") or v.get("vName") or "")[:23]
        alert = (v.get("alert_level") or v.get("alertLevel") or "")[:11]
        color = v.get("color_code") or v.get("colorCode") or ""
        out.append(f"  {nm:<24}{alert:<12}{color}")
    return "\n".join(out)


def ocean_buoys(n: int = 12) -> str:
    """Latest offshore conditions from NOAA marine buoys (waves, wind) — a shipping
    and offshore-energy sensor. Source: NOAA NDBC."""
    try:
        text = get("https://www.ndbc.noaa.gov/data/latest_obs/latest_obs.txt", timeout=15).text
    except Exception as e:
        return f"Could not fetch buoy data: {e}"
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    out = ["Offshore Conditions — NOAA Buoys", "Source: NOAA NDBC", "",
           f"  {'Buoy':<8}{'Lat':>7}{'Lon':>9}{'Wind kt':>9}{'Wave m':>8}", "  " + "─" * 44]
    shown = 0
    for ln in lines:
        p = ln.split()
        if len(p) < 12:
            continue
        try:
            stn, lat, lon = p[0], float(p[1]), float(p[2])
            wspd = p[8] if p[8] != "MM" else "—"
            wvht = p[10] if p[10] != "MM" else "—"
            out.append(f"  {stn:<8}{lat:>7.1f}{lon:>9.1f}{str(wspd):>9}{str(wvht):>8}")
            shown += 1
        except (ValueError, IndexError):
            continue
        if shown >= n:
            break
    if not shown:
        return "Buoy observation data is unavailable right now."
    return "\n".join(out)


def near_earth_objects() -> str:
    """Near-Earth objects passing close today — a tail-risk / space-economy curio.
    Source: NASA NeoWs (public DEMO_KEY)."""
    import datetime
    today = datetime.date.today().isoformat()
    try:
        j = get_json("https://api.nasa.gov/neo/rest/v1/feed",
                     params={"start_date": today, "end_date": today, "api_key": "DEMO_KEY"}, timeout=15)
    except Exception as e:
        return f"Could not fetch NEO data: {e}"
    neos = (j.get("near_earth_objects") or {}).get(today, [])
    if not neos:
        return f"No near-Earth objects catalogued for {today}."
    neos.sort(key=lambda o: (o.get("close_approach_data") or [{}])[0].get("miss_distance", {}).get("kilometers", 9e9) and
              float((o.get("close_approach_data") or [{}])[0].get("miss_distance", {}).get("kilometers", 9e9)))
    out = [f"Near-Earth Objects — {today}", f"Source: NASA NeoWs · {len(neos)} tracked", "",
           f"  {'Object':<20}{'Ø (m)':>9}{'Miss (km)':>14}{'Hazard':>8}", "  " + "─" * 52]
    for o in neos[:12]:
        nm = (o.get("name") or "").strip("()")[:19]
        dia = (o.get("estimated_diameter", {}).get("meters", {}) or {}).get("estimated_diameter_max", 0)
        cad = (o.get("close_approach_data") or [{}])[0]
        miss = float(cad.get("miss_distance", {}).get("kilometers", 0))
        haz = "⚠ yes" if o.get("is_potentially_hazardous_asteroid") else "no"
        out.append(f"  {nm:<20}{dia:>9.0f}{miss:>14,.0f}{haz:>8}")
    return "\n".join(out)


def grid_carbon() -> str:
    """Great Britain electricity-grid carbon intensity (gCO₂/kWh). A clean read on
    the renewable/fossil mix powering the grid right now. Source: UK Carbon Intensity API."""
    try:
        j = get_json("https://api.carbonintensity.org.uk/intensity", timeout=12)
        cur = (j.get("data") or [{}])[0].get("intensity", {})
        mix = get_json("https://api.carbonintensity.org.uk/generation", timeout=12)
        gen = (mix.get("data") or {}).get("generationmix", [])
    except Exception as e:
        return f"Could not fetch grid carbon intensity: {e}"
    out = ["UK Grid Carbon Intensity", "Source: National Grid ESO · Carbon Intensity API", "",
           f"  Intensity (now)     {cur.get('actual') or cur.get('forecast','—')} gCO₂/kWh  ({cur.get('index','')})",
           ""]
    if gen:
        out.append("  Generation mix:")
        for g in sorted(gen, key=lambda x: x.get("perc") or 0, reverse=True)[:8]:
            bar = "█" * min(int((g.get("perc") or 0) / 4), 16)
            out.append(f"  {g.get('fuel','')[:12]:<14}{g.get('perc',0):>5.1f}%  {bar}")
    return "\n".join(out)
