"""International macro — IMF DataMapper (free, no key).

The IMF's World Economic Outlook database, including forward projections, exposed
through the simple DataMapper REST API (ISO-3 country codes)."""

from src.data.http import get, get_json

DM = "https://www.imf.org/external/datamapper/api/v1"

_INDICATORS = [
    ("NGDP_RPCH", "Real GDP growth", "%"),
    ("PCPIPCH",   "Inflation (avg)", "%"),
    ("LUR",       "Unemployment",    "%"),
    ("GGXWDG_NGDP", "Govt debt/GDP", "%"),
    ("BCA_NGDPD", "Current acct/GDP", "%"),
]


def _iso3(iso2: str) -> str | None:
    try:
        import pycountry
        c = pycountry.countries.get(alpha_2=iso2.upper())
        return c.alpha_3 if c else None
    except Exception:
        return None


def who_health(iso2: str, name: str) -> str:
    """WHO Global Health Observatory — life expectancy by sex (latest). Source: WHO GHO."""
    iso3 = _iso3(iso2)
    if not iso3:
        return f"No WHO country code for {name}."
    try:
        vals = get_json("https://ghoapi.azureedge.net/api/WHOSIS_000001",
                        params={"$filter": f"SpatialDim eq '{iso3}'"}, timeout=15).get("value", [])
    except Exception as e:
        return f"Could not fetch WHO data for {name}: {e}"
    if not vals:
        return f"No WHO health data for {name}."
    latest = max(v.get("TimeDim", 0) for v in vals)
    by_sex = {v.get("Dim1"): v.get("NumericValue") for v in vals if v.get("TimeDim") == latest}
    label = {"SEX_BTSX": "Both sexes", "SEX_MLE": "Male", "SEX_FMLE": "Female"}
    out = [f"WHO Health — {name}", f"Source: WHO Global Health Observatory · {latest}", "",
           "  Life expectancy at birth (years):"]
    for k in ("SEX_BTSX", "SEX_FMLE", "SEX_MLE"):
        if k in by_sex and by_sex[k] is not None:
            out.append(f"  {label[k]:<14}{by_sex[k]:>6.1f}")
    return "\n".join(out)


def imf_outlook(iso2: str, name: str) -> str:
    """IMF World Economic Outlook snapshot — latest reading + next-year projection."""
    iso3 = _iso3(iso2)
    if not iso3:
        return f"No IMF country code for {name}."
    import datetime
    this_year = datetime.date.today().year

    rows = []
    for code, label, unit in _INDICATORS:
        try:
            vals = get_json(f"{DM}/{code}/{iso3}", timeout=12) \
                .get("values", {}).get(code, {}).get(iso3, {})
        except Exception:
            vals = {}
        if not vals:
            continue
        years = sorted(int(y) for y in vals)
        cur = next((y for y in reversed(years) if y <= this_year), years[-1])
        nxt = next((y for y in years if y > cur), None)
        rows.append((label, vals.get(str(cur)), cur, vals.get(str(nxt)) if nxt else None, nxt, unit))

    if not rows:
        return f"No IMF outlook data for {name}."
    out = [f"IMF World Economic Outlook — {name}",
           "Source: IMF DataMapper (incl. projections)", "",
           f"  {'Indicator':<18}{'Latest':>15}{'Projection':>15}", "  " + "─" * 50]
    for label, cv, cy, nv, ny, unit in rows:
        cur_s = f"{cv:.1f}{unit} ({cy})" if isinstance(cv, (int, float)) else "—"
        nxt_s = f"{nv:.1f}{unit} ({ny})" if isinstance(nv, (int, float)) else "—"
        out.append(f"  {label:<18}{cur_s:>15}{nxt_s:>15}")
    return "\n".join(out)
