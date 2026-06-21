"""Federal government spending — USAspending.gov (free, no key).

USAspending is the U.S. government's official open record of every federal
award. We surface the contracts a public company has won, which is a real,
hard-to-fudge demand signal for defense, healthcare, and infrastructure names."""

from datetime import date

from src.data.http import session

API = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

_SUFFIXES = (" corporation", " corp", " incorporated", " inc", " company",
             " co", " ltd", " plc", " holdings", " group", " the", ",", ".")


def _clean_name(name: str) -> str:
    n = (name or "").strip()
    low = n.lower()
    for s in _SUFFIXES:
        if low.endswith(s):
            n = n[: len(n) - len(s)].strip()
            low = n.lower()
    return n or name


def federal_contracts(company: str, n: int = 10) -> str:
    name = _clean_name(company)
    end = date.today().isoformat()
    start = f"{date.today().year - 4}-01-01"
    payload = {
        "filters": {
            "award_type_codes": ["A", "B", "C", "D"],   # contract awards
            "recipient_search_text": [name],
            "time_period": [{"start_date": start, "end_date": end}],
        },
        "fields": ["Award Amount", "Recipient Name", "Awarding Agency", "Description"],
        "sort": "Award Amount",
        "order": "desc",
        "limit": n,
        "page": 1,
    }
    try:
        r = session().post(API, json=payload, timeout=25)
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception as e:
        return f"Could not fetch federal contracts: {e}"

    if not results:
        return (f"No federal contract awards found for {name} in the last 4 years.\n"
                "  (Many companies sell nothing to the government — this is normal.)")

    def _amt(v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return "—"
        if abs(v) >= 1e9:
            return f"${v/1e9:.2f}B"
        if abs(v) >= 1e6:
            return f"${v/1e6:.1f}M"
        return f"${v:,.0f}"

    out = [
        f"Federal Contract Awards — {name}",
        "Source: USAspending.gov · contract awards, last 4 FY",
        "",
        f"  {'Amount':>10}  {'Agency':<26} Description",
        "  " + "─" * 64,
    ]
    for x in results:
        amt = _amt(x.get("Award Amount"))
        agency = (x.get("Awarding Agency") or "")[:25]
        desc = (x.get("Description") or "—").replace("\n", " ")[:30]
        out.append(f"  {amt:>10}  {agency:<26} {desc}")
    out += ["", "  Amount = total obligated award value (may span multiple years)."]
    return "\n".join(out)
