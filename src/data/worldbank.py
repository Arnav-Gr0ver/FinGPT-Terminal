"""Country macro — World Bank Open Data API (free, no key)."""

import requests

WB   = "https://api.worldbank.org/v2"
HEAD = {"User-Agent": "FinGPT-Terminal/0.1"}

# Friendly token → (ISO-2 code, display name). Bare country subjects.
COUNTRIES = {
    "US": ("US", "United States"), "USA": ("US", "United States"),
    "CN": ("CN", "China"), "CHINA": ("CN", "China"),
    "JP": ("JP", "Japan"), "JAPAN": ("JP", "Japan"),
    "DE": ("DE", "Germany"), "GERMANY": ("DE", "Germany"),
    "UK": ("GB", "United Kingdom"), "GB": ("GB", "United Kingdom"),
    "IN": ("IN", "India"), "INDIA": ("IN", "India"),
    "FR": ("FR", "France"), "FRANCE": ("FR", "France"),
    "BR": ("BR", "Brazil"), "BRAZIL": ("BR", "Brazil"),
    "CA": ("CA", "Canada"), "CANADA": ("CA", "Canada"),
    "KR": ("KR", "South Korea"), "KOREA": ("KR", "South Korea"),
    "MX": ("MX", "Mexico"), "MEXICO": ("MX", "Mexico"),
    "RU": ("RU", "Russia"), "RUSSIA": ("RU", "Russia"),
    "AU": ("AU", "Australia"), "AUSTRALIA": ("AU", "Australia"),
    "ID": ("ID", "Indonesia"), "SA": ("SA", "Saudi Arabia"),
    "TR": ("TR", "Turkey"), "CH": ("CH", "Switzerland"),
    "IT": ("IT", "Italy"), "ES": ("ES", "Spain"), "NL": ("NL", "Netherlands"),
    "SE": ("SE", "Sweden"), "NO": ("NO", "Norway"), "PL": ("PL", "Poland"),
    "SG": ("SG", "Singapore"), "ZA": ("ZA", "South Africa"),
    "NG": ("NG", "Nigeria"), "EG": ("EG", "Egypt"), "AR": ("AR", "Argentina"),
    "AE": ("AE", "UAE"), "TH": ("TH", "Thailand"), "VN": ("VN", "Vietnam"),
    "IL": ("IL", "Israel"), "IE": ("IE", "Ireland"),
}


def resolve_country(token: str):
    return COUNTRIES.get(token.upper())


def _series(iso: str, indicator: str, n: int = 8):
    """Return [(year, value)] newest-last, dropping nulls."""
    try:
        r = requests.get(f"{WB}/country/{iso}/indicator/{indicator}",
                         params={"format": "json", "per_page": n + 4, "mrv": n + 4},
                         headers=HEAD, timeout=12)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or len(data) < 2 or not data[1]:
            return []
        rows = [(int(o["date"]), o["value"]) for o in data[1] if o.get("value") is not None]
        return sorted(rows)[-n:]
    except Exception:
        return []


def _fmt_usd(v):
    a = abs(v)
    if a >= 1e12: return f"${v/1e12:.2f}T"
    if a >= 1e9:  return f"${v/1e9:.1f}B"
    if a >= 1e6:  return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"


def _block(title: str, rows: list[tuple[str, str]]) -> str:
    out = [title, ""]
    for k, v in rows:
        out.append(f"  {k:<22} {v}")
    return "\n".join(out)


def gdp(iso: str, name: str) -> str:
    lvl = _series(iso, "NY.GDP.MKTP.CD", 6)
    grw = dict(_series(iso, "NY.GDP.MKTP.KD.ZG", 6))
    if not lvl:
        return f"No GDP data for {name}."
    out = [f"GDP — {name}", "Source: World Bank", "",
           f"  {'Year':<8} {'GDP':>14} {'Growth':>10}", "  " + "─" * 34]
    for yr, v in lvl:
        g = grw.get(yr)
        out.append(f"  {yr:<8} {_fmt_usd(v):>14} {(f'{g:+.1f}%' if g is not None else '—'):>10}")
    return "\n".join(out)


def inflation(iso: str, name: str) -> str:
    cpi = _series(iso, "FP.CPI.TOTL.ZG", 8)
    if not cpi:
        return f"No inflation data for {name}."
    out = [f"Inflation (CPI, annual %) — {name}", "Source: World Bank", ""]
    for yr, v in cpi:
        bar = ("█" if v >= 0 else "▒") * min(int(abs(v)), 30)
        out.append(f"  {yr:<6} {v:>+6.1f}%  {bar}")
    return "\n".join(out)


def trade(iso: str, name: str) -> str:
    exp = dict(_series(iso, "NE.EXP.GNFS.ZS", 4))
    imp = dict(_series(iso, "NE.IMP.GNFS.ZS", 4))
    cab = dict(_series(iso, "BN.CAB.XOKA.GD.ZS", 4))
    years = sorted(set(exp) | set(imp) | set(cab))[-4:]
    if not years:
        return f"No trade data for {name}."
    out = [f"Trade & External Balance (% of GDP) — {name}", "Source: World Bank", "",
           f"  {'Year':<8} {'Exports':>10} {'Imports':>10} {'Curr Acct':>11}", "  " + "─" * 41]
    for yr in years:
        def c(d): return f"{d[yr]:.1f}%" if yr in d else "—"
        out.append(f"  {yr:<8} {c(exp):>10} {c(imp):>10} {c(cab):>11}")
    return "\n".join(out)


def debt(iso: str, name: str) -> str:
    d = _series(iso, "GC.DOD.TOTL.GD.ZS", 8)
    if not d:
        return f"No government-debt data for {name} (often unreported)."
    out = [f"Central Government Debt (% of GDP) — {name}", "Source: World Bank", ""]
    for yr, v in d:
        bar = "█" * min(int(v / 5), 30)
        out.append(f"  {yr:<6} {v:>6.1f}%  {bar}")
    return "\n".join(out)


def overview(iso: str, name: str) -> str:
    """The country `price` analogue — latest headline readings."""
    def latest(ind):
        s = _series(iso, ind, 2)
        return s[-1] if s else None
    g  = latest("NY.GDP.MKTP.CD")
    gr = latest("NY.GDP.MKTP.KD.ZG")
    cpi = latest("FP.CPI.TOTL.ZG")
    un = latest("SL.UEM.TOTL.ZS")
    pop = latest("SP.POP.TOTL")
    rows = []
    if g:   rows.append(("GDP", f"{_fmt_usd(g[1])}  ({g[0]})"))
    if gr:  rows.append(("GDP growth", f"{gr[1]:+.1f}%  ({gr[0]})"))
    if cpi: rows.append(("Inflation", f"{cpi[1]:.1f}%  ({cpi[0]})"))
    if un:  rows.append(("Unemployment", f"{un[1]:.1f}%  ({un[0]})"))
    if pop: rows.append(("Population", f"{pop[1]/1e6:,.1f}M  ({pop[0]})"))
    if not rows:
        return f"No data available for {name}."
    return _block(f"{name} — macro snapshot  (World Bank)", rows)
