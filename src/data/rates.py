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


def soma_holdings() -> str:
    """The Fed's balance sheet — System Open Market Account (SOMA) holdings of
    Treasuries, agency debt, and MBS. Source: Federal Reserve Bank of New York."""
    try:
        j = get_json("https://markets.newyorkfed.org/api/soma/summary.json", timeout=15)
    except Exception as e:
        return f"Could not fetch SOMA holdings: {e}"
    summary = j.get("soma", {}).get("summary", [])
    if not summary:
        return "SOMA holdings data is unavailable right now."
    latest = summary[-1]
    prior = summary[-2] if len(summary) > 1 else latest

    def b(v):
        try:
            return float(v) / 1e9
        except (TypeError, ValueError):
            return 0.0
    total = b(latest.get("total"))
    tnotes = b(latest.get("notesbonds")) + b(latest.get("bills")) + b(latest.get("tips")) + b(latest.get("frn"))
    mbs = b(latest.get("mbs"))
    chg = total - b(prior.get("total"))
    return "\n".join([
        "Federal Reserve Balance Sheet — SOMA Holdings",
        f"Source: NY Fed · as of {latest.get('asOfDate','')[:10]}",
        "",
        f"  {'Total holdings':<20} ${total/1000:.2f}T",
        f"  {'  Treasuries':<20} ${tnotes/1000:.2f}T",
        f"  {'  Agency MBS':<20} ${mbs/1000:.2f}T",
        f"  {'Week-over-week':<20} {'+' if chg >= 0 else ''}{chg:.1f}B",
        "",
        "  Balance-sheet expansion = QE; contraction = QT.",
    ])
