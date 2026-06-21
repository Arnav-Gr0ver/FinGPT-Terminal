"""Hiring velocity — public ATS job boards (Greenhouse & Lever, free, no key).

Open-role count by department is a real-time demand signal that fundamentals lag.
Coverage is limited to companies whose board is public on a supported ATS."""

from src.data.http import get_json

# Ticker → (ATS, board token). Public companies known to run a public board.
BOARDS = {
    "COIN": ("greenhouse", "coinbase"), "DDOG": ("greenhouse", "datadog"),
    "NET": ("greenhouse", "cloudflare"), "HOOD": ("greenhouse", "robinhood"),
    "SNOW": ("greenhouse", "snowflakecomputing"), "PLTR": ("lever", "palantir"),
    "PINS": ("greenhouse", "pinterest"), "DOCN": ("greenhouse", "digitalocean"),
    "SHOP": ("greenhouse", "shopify"), "TWLO": ("greenhouse", "twilio"),
    "ZM": ("greenhouse", "zoom"), "DASH": ("greenhouse", "doordash"),
    "ABNB": ("greenhouse", "airbnb"), "RBLX": ("greenhouse", "roblox"),
    "U": ("greenhouse", "unity"), "PATH": ("greenhouse", "uipath"),
    "GTLB": ("greenhouse", "gitlab"), "S": ("greenhouse", "sentinelone"),
    "CRWD": ("greenhouse", "crowdstrike"), "MDB": ("greenhouse", "mongodb"),
    "OKTA": ("greenhouse", "okta"), "TEAM": ("greenhouse", "atlassian"),
    "AFRM": ("greenhouse", "affirm"), "BILL": ("greenhouse", "bill"),
    "ROKU": ("greenhouse", "roku"), "LYFT": ("greenhouse", "lyft"),
    "SQ": ("greenhouse", "block"), "XYZ": ("greenhouse", "block"),
}


def hiring(ticker: str, company: str = "") -> str:
    spec = BOARDS.get(ticker.upper())
    if not spec:
        return (f"No public job board mapped for {ticker}.\n"
                "  Covered: many tech names (COIN, DDOG, NET, SHOP, CRWD, MDB …).")
    ats, token = spec
    try:
        if ats == "greenhouse":
            j = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/departments",
                         timeout=15)
            depts, total_jobs = {}, []
            for d in j.get("departments", []):
                jl = d.get("jobs") or []
                if jl:
                    depts[d.get("name") or "Other"] = len(jl)
                    total_jobs += jl
            jobs = total_jobs
        else:
            jobs = get_json(f"https://api.lever.co/v0/postings/{token}",
                            params={"mode": "json"}, timeout=15)
            depts = {}
            for jb in jobs:
                nm = (jb.get("categories") or {}).get("team") or "Other"
                depts[nm] = depts.get(nm, 0) + 1
    except Exception as e:
        return f"Could not fetch job board for {ticker}: {e}"

    total = len(jobs)
    if not total:
        return f"No open roles listed on {company or ticker}'s public board right now."
    out = [
        f"Hiring — {company or ticker}",
        f"Source: {ats.title()} public board · {total} open roles",
        "",
        f"  {'Department':<28}{'Roles':>8}",
        "  " + "─" * 38,
    ]
    for nm, c in sorted(depts.items(), key=lambda kv: kv[1], reverse=True)[:12]:
        bar = "█" * min(int(c / max(depts.values()) * 16), 16)
        out.append(f"  {nm[:27]:<28}{c:>8}  {bar}")
    out += ["", "  Open-role count is a coincident demand / expansion signal."]
    return "\n".join(out)
