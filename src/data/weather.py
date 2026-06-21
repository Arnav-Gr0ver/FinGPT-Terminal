"""Weather for commodity-relevant regions — Open-Meteo (free, no key).

A coarse fundamental input for agriculture and energy: temperature and
precipitation outlook over a key growing or demand region."""

from src.data.http import get_json


def region_forecast(lat: float, lon: float, region: str, commodity: str = "") -> str:
    try:
        j = get_json("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto", "forecast_days": 7,
        }, timeout=15)
    except Exception as e:
        return f"Could not fetch weather for {region}: {e}"

    daily = j.get("daily") or {}
    dates = daily.get("time") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    prcp = daily.get("precipitation_sum") or []
    if not dates:
        return f"No forecast available for {region}."

    units = j.get("daily_units") or {}
    tu = units.get("temperature_2m_max", "°C")
    pu = units.get("precipitation_sum", "mm")
    total_rain = sum(p for p in prcp if isinstance(p, (int, float)))

    out = [
        f"Weather — {region}" + (f"  ({commodity})" if commodity else ""),
        f"Source: Open-Meteo · 7-day outlook · {round(lat,1)},{round(lon,1)}",
        "",
        f"  {'Date':<12}{'High':>7}{'Low':>7}{'Precip':>10}",
        "  " + "─" * 38,
    ]
    from datetime import datetime
    for i, d in enumerate(dates):
        hi = tmax[i] if i < len(tmax) else None
        lo = tmin[i] if i < len(tmin) else None
        pr = prcp[i] if i < len(prcp) else None
        try:
            wd = datetime.strptime(d, "%Y-%m-%d").strftime("%a %m-%d")
        except ValueError:
            wd = d
        hi_s = f"{hi:.0f}{tu}" if isinstance(hi, (int, float)) else "—"
        lo_s = f"{lo:.0f}{tu}" if isinstance(lo, (int, float)) else "—"
        pr_s = f"{pr:.1f}{pu}" if isinstance(pr, (int, float)) else "—"
        bar = "▮" * min(int((pr or 0) / 5), 8)
        out.append(f"  {wd:<12}{hi_s:>7}{lo_s:>7}{pr_s:>10} {bar}")
    out += ["", f"  7-day precipitation total: {total_rain:.1f}{pu}"]
    return "\n".join(out)
