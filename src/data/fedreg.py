"""Regulatory exposure — the Federal Register API (free, no key).

Every rule, proposed rule, notice, and presidential document published by US
federal agencies. Searching a company name surfaces the regulatory actions that
mention it (tariffs, investigations, approvals, rulemakings)."""

from src.data.http import get_json

API = "https://www.federalregister.gov/api/v1/documents.json"

_TYPE = {"Rule": "Rule", "Proposed Rule": "Proposed", "Notice": "Notice",
         "Presidential Document": "Exec"}


def company_regulations(name: str, n: int = 10) -> str:
    try:
        j = get_json(API, params={
            "conditions[term]": f'"{name}"', "per_page": n, "order": "newest",
            "fields[]": ["publication_date", "type", "title", "agencies", "html_url"],
        }, timeout=15)
    except Exception as e:
        return f"Could not fetch Federal Register entries: {e}"

    results = j.get("results") or []
    if not results:
        return f"No recent Federal Register documents mention {name}."

    out = [
        f"Federal Register — Documents mentioning {name}",
        f"Source: FederalRegister.gov · {j.get('count', 0):,} total matches",
        "",
        f"  {'Date':<12}{'Type':<10}Title",
        "  " + "─" * 62,
    ]
    for r in results[:n]:
        date = (r.get("publication_date") or "")[:10]
        typ = _TYPE.get(r.get("type"), (r.get("type") or "")[:9])
        title = (r.get("title") or "").replace("\n", " ")[:46]
        out.append(f"  {date:<12}{typ:<10}{title}")
    return "\n".join(out)
