"""Legal / regulatory / campaign-finance signals (free, no key).

  • CourtListener  — recent court opinions naming the company  → litigation
  • OpenFEC        — political contributions by company employees → campaigns
  • EPA ECHO       — environmental compliance / violations        → epa
"""

from src.data.http import get_json

_SUFFIXES = (" corporation", " corp", " incorporated", " inc", " company", " co",
             " ltd", " plc", " holdings", " group")


def _clean(name: str) -> str:
    n = (name or "").strip().rstrip(".,")
    low = n.lower()
    for s in _SUFFIXES:
        if low.endswith(s):
            n = n[: len(n) - len(s)].strip()
            break
    return n.rstrip(" .,&")


def litigation(company: str, n: int = 10) -> str:
    name = _clean(company)
    try:
        j = get_json("https://www.courtlistener.com/api/rest/v4/search/", params={
            "q": f'"{name}"', "type": "o", "order_by": "dateFiled desc",
        }, timeout=20)
    except Exception as e:
        return f"Could not fetch court records: {e}"
    res = j.get("results") or []
    if not res:
        return f"No recent court opinions naming {name}."
    out = [f"Litigation — opinions naming {name}",
           f"Source: CourtListener · {j.get('count', 0):,} matches", "",
           f"  {'Filed':<12}{'Court':<26}Case", "  " + "─" * 60]
    for r in res[:n]:
        date = (r.get("dateFiled") or "")[:10] or "—"
        court = (r.get("court") or "")[:25]
        case = (r.get("caseName") or "").replace("\n", " ")[:30]
        out.append(f"  {date:<12}{court:<26}{case}")
    return "\n".join(out)


def campaigns(company: str, n: int = 10) -> str:
    name = _clean(company)
    import datetime
    yr = datetime.date.today().year
    period = yr if yr % 2 == 0 else yr + 1
    try:
        j = get_json("https://api.open.fec.gov/v1/schedules/schedule_a/", params={
            "api_key": "DEMO_KEY", "contributor_employer": name,
            "two_year_transaction_period": period, "per_page": 30,
            "sort": "-contribution_receipt_amount",
        }, timeout=20)
    except Exception as e:
        return f"Could not fetch FEC contributions: {e}"
    res = j.get("results") or []
    if not res:
        return (f"No FEC contributions found listing {name} as employer "
                f"(cycle {period}).")
    agg = {}
    for r in res:
        cm = (r.get("committee") or {}).get("name") or "—"
        agg[cm] = agg.get(cm, 0) + (r.get("contribution_receipt_amount") or 0)
    out = [f"Political Contributions — {name} employees",
           f"Source: OpenFEC · itemized, {period} cycle", "",
           f"  {'Amount':>12}  Recipient committee", "  " + "─" * 54]
    for cm, amt in sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:n]:
        amt_s = f"${amt/1e3:.0f}k" if amt >= 1000 else f"${amt:,.0f}"
        out.append(f"  {amt_s:>12}  {cm[:38]}")
    out += ["", "  Based on the largest itemized donations citing this employer."]
    return "\n".join(out)


def epa_compliance(company: str) -> str:
    name = _clean(company)
    try:
        j = get_json("https://echodata.epa.gov/echo/echo_rest_services.get_facility_info",
                     params={"output": "JSON", "p_fn": name, "responseset": "5"}, timeout=20)
    except Exception as e:
        return f"Could not fetch EPA ECHO data: {e}"
    r = j.get("Results") or {}
    rows = r.get("QueryRows")
    if not rows or str(rows) == "0":
        return f"No EPA-regulated facilities found for {name}."
    return "\n".join([
        f"EPA Compliance — {name}",
        "Source: EPA ECHO (Enforcement & Compliance History)",
        "",
        f"  {'Regulated facilities':<28} {rows}",
        f"  {'With significant violations':<28} {r.get('SVRows', '—')}",
        f"  {'With current violations':<28} {r.get('CVRows', '—')}",
        "",
        "  Significant/current violations flag active environmental noncompliance.",
    ])
