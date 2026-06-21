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
