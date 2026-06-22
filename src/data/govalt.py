"""More government data — lobbying, congressional trade filings, short volume.

All public, key-less:
  • Senate LDA (lobbying disclosures)            → lobbying spend by company
  • House Clerk financial disclosures (PTR ZIP)  → recent congressional trade reports
  • FINRA Reg-SHO daily files                    → short-sale volume by ticker
"""

import csv
import io
from datetime import datetime, timedelta

from src.data.http import get, get_json

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


# ── lobbying (Senate LDA) ─────────────────────────────────────────────────────

def lobbying(company: str) -> str:
    name = _clean(company)
    year = datetime.utcnow().year
    by_year = {}
    try:
        for yr in range(year, year - 4, -1):
            j = get_json("https://lda.senate.gov/api/v1/filings/", params={
                "client_name": name, "filing_year": yr, "page_size": 100,
            }, timeout=20)
            tot = 0.0
            n = 0
            for f in j.get("results", []):
                amt = f.get("income") or f.get("expenses")
                try:
                    tot += float(amt)
                except (TypeError, ValueError):
                    pass
                n += 1
            if n:
                by_year[yr] = (tot, n)
    except Exception as e:
        return f"Could not fetch lobbying data: {e}"

    if not by_year:
        return (f"No federal lobbying disclosures found for {name}.\n"
                "  (Senate LDA matches by client name — try the parent company.)")
    out = [
        f"Federal Lobbying — {name}",
        "Source: U.S. Senate · Lobbying Disclosure Act filings",
        "",
        f"  {'Year':<8}{'Reported spend':>18}{'Filings':>10}",
        "  " + "─" * 38,
    ]
    for yr in sorted(by_year, reverse=True):
        tot, n = by_year[yr]
        amt = f"${tot/1e6:.2f}M" if tot >= 1e6 else f"${tot:,.0f}"
        out.append(f"  {yr:<8}{amt:>18}{n:>10}")
    out += ["", "  Sum of reported income/expenses across all LDA filings that quarter."]
    return "\n".join(out)


# ── congressional trade filings (House Clerk PTR) ─────────────────────────────

def short_volume(ticker: str) -> str:
    """Daily short-sale volume as a share of total volume — FINRA consolidated
    Reg-SHO files (off-exchange). A high, persistent ratio signals short pressure."""
    ticker = ticker.upper().strip()
    out_rows = []
    day = datetime.utcnow()
    tries = 0
    while len(out_rows) < 10 and tries < 20:
        tries += 1
        day -= timedelta(days=1)
        if day.weekday() >= 5:
            continue
        url = f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{day:%Y%m%d}.txt"
        try:
            text = get(url, timeout=15).text
        except Exception:
            continue
        for line in text.splitlines():
            parts = line.split("|")
            if len(parts) >= 5 and parts[1] == ticker:
                try:
                    short = float(parts[2]); total = float(parts[4])
                    out_rows.append((parts[0], short, total))
                except ValueError:
                    pass
                break
    if not out_rows:
        return (f"No recent FINRA short-volume rows for {ticker}.\n"
                "  (Reg-SHO covers off-exchange consolidated volume; data lags ~1 day.)")

    out = [
        f"Short-Sale Volume — {ticker}",
        "Source: FINRA Reg-SHO daily (off-exchange, consolidated)",
        "",
        f"  {'Date':<12}{'Short %':>9}{'Short vol':>14}{'Total vol':>14}",
        "  " + "─" * 50,
    ]
    for date, short, total in out_rows:
        pct = short / total * 100 if total else 0
        d = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        bar = "█" * min(int(pct / 5), 12)
        out.append(f"  {d:<12}{pct:>8.1f}%{short:>14,.0f}{total:>14,.0f}  {bar}")
    return "\n".join(out)
