"""Clinical-trial pipeline — ClinicalTrials.gov API v2 (free, no key).

The official US registry of clinical studies. Searching by sponsor surfaces a
drug/biotech company's active pipeline — a leading indicator that fundamentals
miss until much later."""

from src.data.http import get_json

API = "https://clinicaltrials.gov/api/v2/studies"

_SUFFIXES = (" corporation", " corp", " incorporated", " inc", " company", " co",
             " ltd", " plc", " holdings", " group", " pharmaceuticals", " pharmaceutical")

_STATUS = {"RECRUITING": "Recruiting", "ACTIVE_NOT_RECRUITING": "Active",
           "COMPLETED": "Completed", "NOT_YET_RECRUITING": "Not yet",
           "ENROLLING_BY_INVITATION": "Enrolling", "TERMINATED": "Terminated",
           "SUSPENDED": "Suspended", "WITHDRAWN": "Withdrawn"}


def _clean(name: str) -> str:
    n = (name or "").strip().rstrip(".,")
    low = n.lower()
    for s in _SUFFIXES:
        if low.endswith(s):
            return n[: len(n) - len(s)].strip()
    return n


def clinical_trials(company: str, n: int = 12) -> str:
    name = _clean(company)
    try:
        j = get_json(API, params={
            "query.spons": name, "pageSize": n, "countTotal": "true",
            "sort": "LastUpdatePostDate:desc",
            "fields": ("NCTId,BriefTitle,OverallStatus,Phase,Condition,"
                       "LeadSponsorName,LastUpdatePostDate"),
        }, timeout=15)
    except Exception as e:
        return f"Could not fetch clinical trials: {e}"

    studies = j.get("studies") or []
    if not studies:
        return (f"No clinical trials found with {name} as sponsor.\n"
                "  (Only companies running registered studies appear here.)")

    out = [
        f"Clinical Trials — {name}",
        f"Source: ClinicalTrials.gov · {j.get('totalCount', len(studies)):,} studies sponsored",
        "",
        f"  {'Updated':<12}{'Phase':<10}{'Status':<12}Study",
        "  " + "─" * 60,
    ]
    for s in studies[:n]:
        ps = s.get("protocolSection", {})
        ident = ps.get("identificationModule", {})
        status = ps.get("statusModule", {})
        design = ps.get("designModule", {})
        phases = design.get("phases") or []
        phase = "/".join(p.replace("PHASE", "Ph") for p in phases) if phases else "—"
        st = _STATUS.get(status.get("overallStatus", ""), (status.get("overallStatus") or "")[:11])
        upd = (status.get("lastUpdatePostDateStruct", {}) or {}).get("date", "")[:10]
        title = (ident.get("briefTitle") or "").replace("\n", " ")[:30]
        out.append(f"  {upd:<12}{phase:<10}{st:<12}{title}")
    return "\n".join(out)
