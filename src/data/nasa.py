"""NASA POWER — solar & wind resource climatology (free, no key).

NASA POWER (Prediction Of Worldwide Energy Resources) is a NASA Earth
science project providing global solar irradiance and meteorological
climatology data. The climatology endpoint returns 30-year monthly
averages for any lat/lon with zero authentication.

Endpoint: power.larc.nasa.gov/api/temporal/climatology/point
Community: RE (Renewable Energy)
"""

from src.data.http import get_json

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_KEYS   = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

_BASE = "https://power.larc.nasa.gov/api/temporal/climatology/point"


def solar_resource(lat: float, lon: float, name: str) -> str:
    """30-year solar & wind climatology for any lat/lon (NASA POWER, no key).

    Returns monthly averages of:
      ALLSKY_SFC_SW_DWN  Global Horizontal Irradiance (kWh/m²/day)
      CLRSKY_SFC_SW_DWN  Clear-sky GHI (kWh/m²/day)
      WS10M              Wind speed at 10 m (m/s)
      WS50M              Wind speed at 50 m (m/s) — turbine-relevant height
      T2M                Temperature at 2 m (°C)
    """
    try:
        j = get_json(_BASE, params={
            "parameters": "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,WS10M,WS50M,T2M",
            "community":  "RE",
            "longitude":  round(lon, 4),
            "latitude":   round(lat, 4),
            "format":     "JSON",
        }, timeout=20)
    except Exception as e:
        return f"Could not fetch NASA POWER data: {e}"

    props = (j or {}).get("properties", {}).get("parameter", {})
    ghi   = props.get("ALLSKY_SFC_SW_DWN") or {}
    csghi = props.get("CLRSKY_SFC_SW_DWN") or {}
    ws10  = props.get("WS10M") or {}
    ws50  = props.get("WS50M") or {}
    t2m   = props.get("T2M")   or {}

    if not ghi:
        return f"No NASA POWER climatology available for {name}."

    def mvals(d):
        return [d.get(k) for k in _KEYS]

    ann_ghi  = ghi.get("ANN")
    ann_csghi = csghi.get("ANN")
    ann_ws50 = ws50.get("ANN")
    ann_ws10 = ws10.get("ANN")
    ann_t2m  = t2m.get("ANN")

    ki = (ann_ghi / ann_csghi) if ann_csghi and ann_csghi > 0 and ann_ghi else None

    def _solar_class(ghi_ann):
        if ghi_ann >= 5.5: return "Excellent  ██████"
        if ghi_ann >= 4.5: return "Good       ████░░"
        if ghi_ann >= 3.5: return "Moderate   ██░░░░"
        return                     "Low        █░░░░░"

    def _wind_class(ws):
        if ws >= 7.0: return "Excellent  ██████"
        if ws >= 5.5: return "Good       ████░░"
        if ws >= 4.0: return "Moderate   ██░░░░"
        return                "Low        █░░░░░"

    out = [
        f"Solar & Wind Resource Climatology — {name}",
        "Source: NASA POWER (30-yr monthly avg)  ·  power.larc.nasa.gov",
        f"  Location: {abs(lat):.2f}°{'N' if lat >= 0 else 'S'}, "
        f"{abs(lon):.2f}°{'E' if lon >= 0 else 'W'}",
        "",
    ]

    if ann_ghi is not None:
        out.append(f"  {'Solar (GHI annual avg)':<28} {ann_ghi:.2f} kWh/m²/day  "
                   f"→ {_solar_class(ann_ghi)}")
    if ki is not None:
        out.append(f"  {'Clearness index':<28} {ki:.2f}  "
                   f"(fraction of clear-sky potential captured)")
    if ann_ws50 is not None:
        out.append(f"  {'Wind @ 50m (annual avg)':<28} {ann_ws50:.1f} m/s  "
                   f"→ {_wind_class(ann_ws50)}")
    if ann_ws10 is not None:
        out.append(f"  {'Wind @ 10m (annual avg)':<28} {ann_ws10:.1f} m/s")
    if ann_t2m is not None:
        out.append(f"  {'Mean annual temperature':<28} {ann_t2m:.1f} °C")

    # Monthly table
    ghi_m  = mvals(ghi)
    ws50_m = mvals(ws50)
    t2m_m  = mvals(t2m)

    def _spark(vals, vmin=None, vmax=None):
        _BAR = "▁▂▃▄▅▆▇█"
        clean = [v for v in vals if v is not None]
        lo = vmin if vmin is not None else (min(clean) if clean else 0)
        hi = vmax if vmax is not None else (max(clean) if clean else 1)
        rng = hi - lo or 1
        return "".join(
            _BAR[min(7, int((v - lo) / rng * 8))] if v is not None else "·"
            for v in vals
        )

    header = "  " + " " * 6 + "  ".join(f"{m:>4}" for m in _MONTHS)
    sep    = "  " + "─" * 66
    out += ["", header, sep]

    ghi_row  = "  GHI  " + "  ".join(
        f"{v:>4.1f}" if v is not None else "   —" for v in ghi_m)
    ws50_row = "  WS50 " + "  ".join(
        f"{v:>4.1f}" if v is not None else "   —" for v in ws50_m)
    t2m_row  = "  T2M  " + "  ".join(
        f"{v:>4.1f}" if v is not None else "   —" for v in t2m_m)

    out += [
        ghi_row,
        "         " + _spark(ghi_m),
        ws50_row,
        "         " + _spark(ws50_m),
        t2m_row,
        "         " + _spark(t2m_m),
        "",
        "  GHI = Global Horizontal Irradiance (kWh/m²/day) · "
        "WS50 = Wind Speed at 50m (m/s) · T2M = Temp (°C)",
    ]

    return "\n".join(out)
