"""Municipal & health open data (Socrata / CMS, free, no key).

City building-permit feeds (a construction / real-estate activity sensor) plus
CDC respiratory surveillance and CMS Medicare data — each a distinct public
open-data host."""

from src.data.http import get_json

# City → (Socrata host, building-permit dataset id, date field).
_CITY_PERMITS = [
    ("New York",  "data.cityofnewyork.us", "ipu4-2q9a", "issuance_date"),
    ("San Francisco", "data.sfgov.org",     "i98e-djp9", "issued_date"),
    ("Chicago",   "data.cityofchicago.org", "ydr8-5enu", "issue_date"),
    ("Austin",    "data.austintexas.gov",   "3syk-w9eu", "issued_date"),
    ("Seattle",   "data.seattle.gov",       "76t5-zqzr", "issueddate"),
    ("Dallas",    "www.dallasopendata.com", "e7gq-4sah", "issued_date"),
]


def local_permits() -> str:
    """Recent building-permit volume across major US cities — a real-time
    construction / development sensor. Source: municipal Socrata open-data portals."""
    import datetime
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    out = ["City Building Permits — Last 30 Days", "Source: municipal open-data portals", "",
           f"  {'City':<18}{'Permits (30d)':>16}", "  " + "─" * 36]
    got = False
    for city, host, ds, datef in _CITY_PERMITS:
        try:
            j = get_json(f"https://{host}/resource/{ds}.json", params={
                "$select": "count(*)", "$where": f"{datef} > '{cutoff}T00:00:00'"}, timeout=12)
            cnt = int((j[0].get("count") or j[0].get("count_*") or list(j[0].values())[0]))
            got = True
            out.append(f"  {city:<18}{cnt:>16,}")
        except Exception:
            continue
    if not got:
        return "City permit data is unavailable right now."
    out += ["", "  Permit issuance leads construction starts and materials demand."]
    return "\n".join(out)


def respiratory_surveillance() -> str:
    """CDC respiratory-illness activity (emergency-dept visits). Source: CDC NSSP."""
    try:
        rows = get_json("https://data.cdc.gov/resource/rdmq-nq56.json",
                        params={"$limit": 200, "$order": "week_end DESC",
                                "$where": "county = 'All'"}, timeout=15)
    except Exception:
        rows = []
    if not rows:                                       # fall back without the county filter
        try:
            rows = get_json("https://data.cdc.gov/resource/rdmq-nq56.json",
                            params={"$limit": 50, "$order": "week_end DESC"}, timeout=15)
        except Exception as e:
            return f"Could not fetch CDC surveillance data: {e}"
    if not rows:
        return "CDC respiratory-surveillance data is unavailable right now."
    fields = [k for k in rows[0] if "percent" in k.lower() or "visit" in k.lower()]
    latest = rows[0]
    out = ["CDC Respiratory Illness — ED Visit Surveillance",
           f"Source: CDC NSSP · week ending {str(latest.get('week_end', ''))[:10]}", "", "  Recent readings:"]
    shown = 0
    for k in fields[:6]:
        v = latest.get(k)
        if v is not None:
            out.append(f"  {k.replace('_', ' ')[:34]:<36}{v}")
            shown += 1
    if not shown:
        out.append("  " + ", ".join(f"{k}={latest[k]}" for k in list(latest)[:4]))
    return "\n".join(out)


def medicare_overview() -> str:
    """CMS Medicare — sample of rated hospitals (name, location, star rating) from
    the public CMS provider-data API. Source: CMS."""
    try:
        rows = get_json("https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0",
                        params={"limit": 14}, timeout=15).get("results", [])
    except Exception as e:
        return f"Could not fetch CMS data: {e}"
    if not rows:
        return "CMS provider data is unavailable right now."

    def field(r, *names):
        for n in names:
            for k in r:
                if k.lower().replace(" ", "_") == n:
                    return r[k]
        return ""
    out = ["CMS Medicare — Rated Hospitals (sample)", "Source: CMS provider data", "",
           f"  {'Hospital':<34}{'State':<7}Rating", "  " + "─" * 50]
    for r in rows:
        nm = str(field(r, "facility_name", "hospital_name", "provider_name"))[:33]
        st = str(field(r, "state"))[:5]
        rt = str(field(r, "hospital_overall_rating", "overall_rating") or "—")
        out.append(f"  {nm:<34}{st:<7}{rt}")
    out += ["", "  Hospital quality & footprint underpin provider/device/insurer revenue."]
    return "\n".join(out)
