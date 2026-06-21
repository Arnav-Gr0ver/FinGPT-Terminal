"""Product recalls & enforcement — openFDA (FDA open data, free, no key).

Drug, device, and food recall/enforcement records, searchable by the recalling
firm. A concrete operational-risk signal for pharma, medtech, and food names."""

from src.data.http import get_json

_SUFFIXES = (" corporation", " corp", " incorporated", " inc", " company",
             " co", " ltd", " plc", " holdings", " group", " sa", " ag", " nv",
             " pharmaceuticals", " pharmaceutical")


def _clean(name: str) -> str:
    n = (name or "").strip().rstrip(".,")
    low = n.lower()
    for s in _SUFFIXES:
        if low.endswith(s):
            return n[: len(n) - len(s)].strip()
    return n


def _fmt_date(s):
    s = str(s or "")
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else (s or "—")


def _fda_date(s):
    s = str(s or "")
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else (s or "—")


def drug_shortages(company: str = "", n: int = 16) -> str:
    """Active FDA drug-shortage list — a supply-chain signal for pharma and
    hospital/distribution names. Filtered to a company if one is loaded.
    Source: openFDA drug shortages."""
    name = _clean(company) if company else ""
    params = {"sort": "update_date:desc", "limit": n}
    params["search"] = (f'company_name:"{name}"' if name else 'status:"Current"')
    try:
        j = get_json("https://api.fda.gov/drug/shortages.json", params=params, timeout=15)
    except Exception:
        if name:
            return f"No current FDA drug shortages listed for {name}."
        return "Could not fetch the FDA drug-shortage list."

    results = j.get("results", [])
    total = j.get("meta", {}).get("results", {}).get("total", len(results))
    if not results:
        return (f"No FDA drug-shortage records for {name}." if name
                else "No active drug shortages listed right now.")
    title = (f"FDA Drug Shortages — {name}" if name
             else "FDA Drug Shortages — Current")
    out = [title, f"Source: openFDA · {total:,} matching records", "",
           f"  {'Updated':<12}{'Status':<10}Drug", "  " + "─" * 58]
    for r in results[:n]:
        upd = _fda_date(r.get("update_date"))
        status = (r.get("status") or "")[:9]
        drug = (r.get("generic_name") or r.get("proprietary_name") or "")[:34]
        out.append(f"  {upd:<12}{status:<10}{drug}")
    if not name:
        out += ["", "  Load a pharma ticker then `shortages` to filter by company."]
    return "\n".join(out)


def fda_recalls(company: str, n: int = 12) -> str:
    name = _clean(company)
    results = []
    for kind in ("drug", "device", "food"):
        try:
            j = get_json(f"https://api.fda.gov/{kind}/enforcement.json", params={
                "search": f'recalling_firm:"{name}"',
                "sort": "report_date:desc", "limit": n,
            }, timeout=15)
            for r in j.get("results", []):
                r["_kind"] = kind
                results.append(r)
        except Exception:
            continue                       # openFDA 404s when nothing matches

    if not results:
        return (f"No FDA recall / enforcement records for {name}.\n"
                "  (Only drug, device, and food companies appear here.)")

    results.sort(key=lambda r: r.get("report_date", ""), reverse=True)
    out = [
        f"FDA Recalls & Enforcement — {name}",
        "Source: openFDA · drug / device / food enforcement",
        "",
        f"  {'Date':<12}{'Type':<8}{'Class':<10}Reason",
        "  " + "─" * 60,
    ]
    for r in results[:n]:
        date = _fmt_date(r.get("report_date"))
        kind = r.get("_kind", "")[:7]
        cls = (r.get("classification") or "").replace("Class ", "Cl ")[:9]
        reason = (r.get("reason_for_recall") or "").replace("\n", " ")[:30]
        out.append(f"  {date:<12}{kind:<8}{cls:<10}{reason}")
    out += ["", "  Class I = most serious (risk of death) · III = least."]
    return "\n".join(out)
