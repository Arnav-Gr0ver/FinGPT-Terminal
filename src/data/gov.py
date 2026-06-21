"""Gov & insider data — SEC EDGAR (Form 4 + FTD), congressional trade disclosures."""

import csv
import io
import requests
from datetime import datetime, timedelta
from urllib.parse import quote

HEADERS = {
    "User-Agent": "FinGPT Terminal research@fingpt.ai",
    "Accept-Encoding": "gzip, deflate",
}


# ---------------------------------------------------------------------------
# Insider trades — SEC EDGAR EFTS full-text search for Form 4 filings
# ---------------------------------------------------------------------------

def get_insider_trades(ticker: str) -> str:
    ticker = ticker.upper().strip()
    try:
        # Step 1: resolve CIK
        cik = _resolve_cik(ticker)
        if not cik:
            return f"Could not find SEC CIK for {ticker}."

        # Step 2: fetch recent Form 4 filings
        url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
        r   = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()

        filings = data.get("filings", {}).get("recent", {})
        forms   = filings.get("form", [])
        dates   = filings.get("filingDate", [])
        accns   = filings.get("accessionNumber", [])
        descriptions = filings.get("primaryDocument", [])

        # Filter to Form 4
        form4 = [
            (dates[i], accns[i])
            for i, f in enumerate(forms)
            if f == "4" and i < len(dates)
        ][:15]

        if not form4:
            return f"No recent Form 4 filings found for {ticker} on SEC EDGAR."

        # Step 3: parse each filing for transaction info
        lines = [
            f"Insider Trades — {ticker}  (SEC Form 4)",
            "Source: SEC EDGAR",
            "",
            f"  {'Date':<14} {'Insider':<26} {'Trans':<10} {'Shares':>12} {'Price':>10}",
            "  " + "─" * 76,
        ]

        for date_s, accn in form4[:12]:
            try:
                row = _parse_form4(cik, accn)
                if row:
                    name, ttype, shares, price = row
                    shares_s = f"{int(shares):,}" if shares else "N/A"
                    price_s  = f"${price:.2f}" if price else "N/A"
                    lines.append(
                        f"  {date_s:<14} {name[:25]:<26} {ttype:<10} {shares_s:>12} {price_s:>10}"
                    )
                else:
                    lines.append(f"  {date_s:<14} (filing parsed — see EDGAR for details)")
            except Exception:
                lines.append(f"  {date_s:<14} (could not parse filing)")

        lines += ["", f"  Full filings: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=4"]
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch insider trades for {ticker}: {e}"


def get_recent_filings(ticker: str) -> str:
    """Recent primary SEC filings (10-K, 10-Q, 8-K) for a ticker via EDGAR."""
    ticker = ticker.upper().strip()
    keep   = {"10-K", "10-Q", "8-K", "10-K/A", "10-Q/A", "8-K/A", "20-F", "S-1", "DEF 14A"}
    labels = {
        "10-K": "Annual report",  "10-Q": "Quarterly report",
        "8-K": "Material event",  "20-F": "Foreign annual",
        "S-1": "Registration",    "DEF 14A": "Proxy statement",
    }
    try:
        cik = _resolve_cik(ticker)
        if not cik:
            return f"Could not find SEC CIK for {ticker}."

        url  = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
        r    = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        recent = r.json().get("filings", {}).get("recent", {})

        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        docs  = recent.get("primaryDocument", [])
        accns = recent.get("accessionNumber", [])

        rows = []
        for i, f in enumerate(forms):
            if f in keep and i < len(dates):
                accn = accns[i].replace("-", "") if i < len(accns) else ""
                doc  = docs[i] if i < len(docs) else ""
                link = (f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn}/{doc}"
                        if accn and doc else "")
                rows.append((dates[i], f, labels.get(f.split("/")[0], ""), link))
            if len(rows) >= 12:
                break

        if not rows:
            return f"No recent 10-K / 10-Q / 8-K filings found for {ticker} on SEC EDGAR."

        lines = [
            f"Recent Filings — {ticker}  (SEC EDGAR)",
            "",
            f"  {'Filed':<14} {'Form':<10} {'Type'}",
            "  " + "─" * 48,
        ]
        for date_s, form, label, _ in rows:
            lines.append(f"  {date_s:<14} {form:<10} {label}")
        lines += ["", f"  Full index: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=include&count=40"]
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch filings for {ticker}: {e}"


def _resolve_cik(ticker: str) -> int | None:
    """Map ticker → SEC CIK via the EDGAR company tickers JSON."""
    try:
        r = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                return int(entry["cik_str"])
        return None
    except Exception:
        return None


def _parse_form4(cik: int, accn: str) -> tuple | None:
    """Fetch and parse a Form 4 XML filing using ElementTree."""
    import xml.etree.ElementTree as ET

    codes = {
        "P": "Purchase", "S": "Sale", "A": "Award",
        "D": "Disposition", "F": "Tax withheld", "M": "Option exercise",
        "G": "Gift", "C": "Conversion", "X": "Option expiry",
    }

    try:
        # Build directory URL and fetch the filing index
        accn_nodash = accn.replace("-", "")
        idx_url     = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn_nodash}/"
        r_idx       = requests.get(idx_url, headers=HEADERS, timeout=8)
        if r_idx.status_code != 200:
            return None

        # Find the .xml file in the index listing
        import re
        xml_files = re.findall(r'href="([^"]*\.xml)"', r_idx.text)
        # Prefer the actual form4 xml (not the filing-summary)
        xml_file = next(
            (f for f in xml_files if "filing-summary" not in f and "primary_doc" not in f.lower()),
            xml_files[0] if xml_files else None,
        )
        if not xml_file:
            return None

        base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn_nodash}/"
        if xml_file.startswith("/"):
            xml_url = f"https://www.sec.gov{xml_file}"
        else:
            xml_url = base + xml_file

        r_xml = requests.get(xml_url, headers=HEADERS, timeout=8)
        if r_xml.status_code != 200:
            return None

        root = ET.fromstring(r_xml.content)

        def _txt(parent, *tags):
            for tag in tags:
                el = parent.find(f".//{tag}")
                if el is not None:
                    # value may be wrapped in <value>
                    v = el.find("value")
                    return (v.text if v is not None else el.text or "").strip()
            return ""

        name  = _txt(root, "rptOwnerName") or "Unknown"
        code  = _txt(root, "transactionCode") or "?"
        label = codes.get(code.upper(), code)

        # Try non-derivative transactions first, then derivative
        shares_s = _txt(root, "transactionShares")
        price_s  = _txt(root, "transactionPricePerShare")

        shares_f = float(shares_s) if shares_s and shares_s.replace(".", "").replace("-", "").isdigit() else None
        price_f  = float(price_s)  if price_s  and price_s.replace(".", "").replace("-", "").isdigit()  else None

        return (name[:25], label[:12], shares_f, price_f)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Congressional trades — Quiver Quant public CSV + EDGAR fallback
# ---------------------------------------------------------------------------

def get_congress_trades(ticker: str = "") -> str:
    """Congressional trading disclosures via QuiverQuant public data."""
    ticker = ticker.upper().strip()
    trades = []

    # QuiverQuant hosts cleaned congressional trade data as a public CSV
    # endpoint (no key required for the bulk CSV download)
    try:
        url = "https://api.quiverquant.com/beta/bulk/congresstrading"
        r   = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=12)
        if r.status_code == 200:
            data = r.json()
            for t in data:
                sym = (t.get("Ticker") or "").upper().strip()
                if ticker and sym != ticker:
                    continue
                trades.append({
                    "date":   (t.get("Date") or "")[:10],
                    "who":    (t.get("Name") or t.get("Representative") or "Unknown")[:22],
                    "ticker": sym[:8],
                    "type":   (t.get("Transaction") or "?")[:12],
                    "amount": (t.get("Range") or t.get("Amount") or "")[:14],
                    "party":  (t.get("Party") or "")[:3],
                })
    except Exception:
        pass

    if not trades:
        # Fall back: inform user where to find the data
        msg = f" for {ticker}" if ticker else ""
        return (
            f"Congressional trade data{msg} is not available from free APIs at this time.\n"
            "\n"
            "  Check these official and community sources:\n"
            "    House disclosures:  https://disclosures.house.gov\n"
            "    Senate disclosures: https://efts.sec.gov\n"
            "    Capitol Trades:     https://www.capitoltrades.com\n"
            "    Quiver Quant:       https://www.quiverquant.com/congresstrading\n"
            "\n"
            "  Note: Congressional stock trades must be reported within 45 days.\n"
            "  Delayed reporting is common and data may lag real transactions."
        )

    trades.sort(key=lambda x: x["date"], reverse=True)
    trades = trades[:25]

    header = f"Congressional Trades{' — ' + ticker if ticker else '  (Recent)'}"
    lines  = [
        header,
        "Source: QuiverQuant congressional disclosure data",
        "",
        f"  {'Date':<12} {'Member':<24} {'Ticker':<10} {'Type':<14} {'Amount'}",
        "  " + "─" * 76,
    ]
    for t in trades:
        party = f"({t['party']})" if t["party"] else ""
        lines.append(
            f"  {t['date']:<12} {t['who']:<24} {t['ticker']:<10} {t['type']:<14} {t['amount']}"
        )

    lines += ["", "  Full data: https://www.quiverquant.com/congresstrading"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Failure to Deliver — SEC published CSV files
# ---------------------------------------------------------------------------

def _efts(params: dict):
    r = requests.get("https://efts.sec.gov/LATEST/search-index",
                     params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json().get("hits", {}).get("hits", [])


def sec_activists(company: str, n: int = 12) -> str:
    """Recent activist / large-stake filings (SC 13D / 13G) naming the company.
    Source: SEC EDGAR full-text search."""
    import re
    try:
        hits = _efts({"q": f'"{company}"', "forms": "SC 13D,SC 13G,SC 13D/A,SC 13G/A"})
    except Exception as e:
        return f"Could not fetch 13D/G filings: {e}"
    core = company.lower().split()[0]                 # e.g. "apple"
    rows = []
    for h in hits:
        s = h.get("_source", {})
        filer = re.sub(r"\s*\(.*", "", (s.get("display_names") or ["?"])[0]).strip()
        if core in filer.lower():                      # drop the company's own filings
            continue
        rows.append((s.get("file_date", "")[:10], s.get("file_type", "")[:9], filer[:34]))
        if len(rows) >= n:
            break
    if not rows:
        return (f"No third-party 13D/13G stake filings found naming {company}.\n"
                "  (Holders' filings index the subject by name; coverage varies.)")
    out = [f"Activist & >5% Stake Filings — {company}",
           "Source: SEC EDGAR · Schedule 13D / 13G (filed by holders)", "",
           f"  {'Filed':<12}{'Form':<10}Filer", "  " + "─" * 56]
    for date, form, filer in rows:
        out.append(f"  {date:<12}{form:<10}{filer}")
    out += ["", "  13D = activist intent · 13G = passive >5% holder."]
    return "\n".join(out)


def sec_mentions(company: str, n: int = 12) -> str:
    """Most recent SEC filings (any form) that mention the company in full text.
    Source: SEC EDGAR full-text search."""
    import re
    try:
        hits = _efts({"q": f'"{company}"'})
    except Exception as e:
        return f"Could not fetch filings: {e}"
    if not hits:
        return f"No recent filings mention {company}."
    out = [f"SEC Filing Mentions — {company}",
           "Source: SEC EDGAR full-text search", "",
           f"  {'Filed':<12}{'Form':<10}Filer", "  " + "─" * 56]
    for h in hits[:n]:
        s = h.get("_source", {})
        filer = re.sub(r"\s*\(.*", "", (s.get("display_names") or ["?"])[0]).strip()[:34]
        out.append(f"  {s.get('file_date','')[:10]:<12}{s.get('file_type','')[:9]:<10}{filer}")
    return "\n".join(out)


def recent_ipos(n: int = 15) -> str:
    """The IPO pipeline — most recent S-1 registration statements filed with the
    SEC (companies preparing to go public). Source: SEC EDGAR full-text search."""
    import re
    try:
        r = requests.get("https://efts.sec.gov/LATEST/search-index",
                         params={"forms": "S-1", "dateRange": "custom",
                                 "startdt": (datetime.utcnow() - timedelta(days=120)).strftime("%Y-%m-%d"),
                                 "enddt": datetime.utcnow().strftime("%Y-%m-%d")},
                         headers=HEADERS, timeout=15)
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])
    except Exception as e:
        return f"Could not fetch the IPO pipeline: {e}"
    if not hits:
        return "No recent S-1 filings found."

    seen, rows = set(), []
    for h in hits:
        s = h.get("_source", {})
        names = s.get("display_names") or []
        if not names:
            continue
        raw = names[0]
        ticker = ""
        m = re.search(r"\(([A-Z]{1,6})\)", raw)
        if m:
            ticker = m.group(1)
        company = re.sub(r"\s*\(.*", "", raw).strip()[:34]
        key = company.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append((s.get("file_date", "")[:10], company, ticker, s.get("file_type", "S-1")))
        if len(rows) >= n:
            break

    out = [
        "IPO Pipeline — Recent S-1 Registrations",
        "Source: SEC EDGAR · companies filing to go public",
        "",
        f"  {'Filed':<12}{'Company':<36}{'Ticker':<8}Form",
        "  " + "─" * 64,
    ]
    for date, company, ticker, form in rows:
        out.append(f"  {date:<12}{company:<36}{ticker or '—':<8}{form}")
    out += ["", "  S-1/A = amended registration.  Load any ticker to research it."]
    return "\n".join(out)


def get_ftd(ticker: str) -> str:
    ticker = ticker.upper().strip()
    try:
        # SEC publishes FTD files semi-monthly. Try last few months.
        now    = datetime.utcnow()
        months = [now - timedelta(days=30 * i) for i in range(3)]
        data   = []

        for dt in months:
            for half in ("b", "a"):
                ym  = dt.strftime("%Y%m")
                url = f"https://www.sec.gov/files/data/fails-deliver-data/cnsfails{ym}{half}.zip"
                try:
                    r = requests.get(url, headers=HEADERS, timeout=15)
                    if r.status_code != 200:
                        continue
                    import zipfile
                    import io as _io
                    zf    = zipfile.ZipFile(_io.BytesIO(r.content))
                    fname = zf.namelist()[0]
                    text  = zf.read(fname).decode("utf-8", errors="replace")
                    reader = csv.DictReader(io.StringIO(text), delimiter="|")
                    for row in reader:
                        sym = (row.get("SYMBOL") or row.get("Symbol") or "").upper().strip()
                        if sym == ticker:
                            data.append(row)
                    if data:
                        break
                except Exception:
                    continue
            if data:
                break

        if not data:
            return (
                f"No FTD data found for {ticker} in recent SEC files.\n"
                "\n"
                "  SEC FTD files are published bi-monthly with a ~2 week delay.\n"
                "  Full data: https://www.sec.gov/data/foiadocuments/data.htm"
            )

        # Sort by date desc
        data.sort(key=lambda r: r.get("SETTLEMENT DATE") or r.get("Date") or "", reverse=True)
        data = data[:20]

        lines = [
            f"Failure to Deliver — {ticker}",
            "Source: SEC EDGAR FTD Data",
            "",
            f"  {'Settlement Date':<18} {'FTD Shares':>14} {'Price':>10} {'Value':>14}",
            "  " + "─" * 60,
        ]

        for row in data:
            date_s  = row.get("SETTLEMENT DATE") or row.get("Date") or "?"
            shares  = row.get("QUANTITY (FAILS)") or row.get("Quantity") or "0"
            price   = row.get("PRICE") or row.get("Price") or "0"
            try:
                shares_f = int(shares.replace(",", ""))
                price_f  = float(price)
                value    = shares_f * price_f
                val_s    = f"${value/1e6:.2f}M" if value >= 1e6 else f"${value:,.0f}"
                lines.append(
                    f"  {date_s:<18} {shares_f:>14,} {price_f:>9.2f} {val_s:>14}"
                )
            except Exception:
                lines.append(f"  {date_s:<18} {shares:<14} {price:>10}")

        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch FTD data for {ticker}: {e}"
