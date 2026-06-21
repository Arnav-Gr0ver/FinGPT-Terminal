"""Money-market reference rates — Federal Reserve Bank of New York.

Public, no-key JSON API (markets.newyorkfed.org). These are the administered and
benchmark overnight rates that anchor the front end of the curve: SOFR (the
Treasury-repo benchmark that replaced LIBOR), EFFR (fed funds), OBFR, and the
repo-rate family (TGCR/BGCR)."""

from src.data.http import get_json

NYFED = "https://markets.newyorkfed.org/api/rates/all/latest.json"

# Order + friendly labels for the rates we surface (kept short to fit the column).
_RATE_LABELS = [
    ("EFFR",   "Effective Fed Funds"),
    ("OBFR",   "Overnight Bank Funding"),
    ("SOFR",   "Secured Overnight (repo)"),
    ("BGCR",   "Broad Gen. Collateral"),
    ("TGCR",   "Tri-Party Gen. Collateral"),
]


def get_reference_rates() -> str:
    try:
        data = get_json(NYFED, timeout=15)
    except Exception as e:
        return f"Could not fetch reference rates: {e}"

    rows = {r.get("type", "").upper(): r for r in data.get("refRates", [])}
    if not rows:
        return "Reference-rate data is unavailable right now."

    eff = next((r.get("effectiveDate") for r in rows.values() if r.get("effectiveDate")), "")
    lines = [
        "US Money-Market Reference Rates  (overnight, %)",
        f"Source: Federal Reserve Bank of New York · effective {eff}",
        "",
        f"  {'Rate':<32} {'Rate %':>8} {'Volume $bn':>12}",
        "  " + "─" * 54,
    ]
    for key, label in _RATE_LABELS:
        r = rows.get(key)
        if not r:
            continue
        rate = r.get("percentRate")
        vol  = r.get("volumeInBillions")
        rate_s = f"{rate:.2f}" if isinstance(rate, (int, float)) else "—"
        vol_s  = f"{vol:,.0f}" if isinstance(vol, (int, float)) else "—"
        lines.append(f"  {key + ' · ' + label:<32} {rate_s:>8} {vol_s:>12}")

    lines += ["", "  SOFR is the primary USD benchmark; EFFR is the Fed's policy target."]
    return "\n".join(lines)
