"""Metric layer — deep, consistent, per-target data fields.

Every equity exposes the same ~100 fundamental fields (Yahoo `info`); every
country exposes the same World-Bank indicator set. So `NVDA <metric>` works for
any stock and `INDIA <metric>` works for any country — same vocabulary, fully
consistent across targets. `<target> metrics` dumps the whole set at once.
"""

import time

# ── formatting ────────────────────────────────────────────────────────────────

def _money(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    a = abs(v)
    if a >= 1e12: return f"${v/1e12:.2f}T"
    if a >= 1e9:  return f"${v/1e9:.2f}B"
    if a >= 1e6:  return f"${v/1e6:.2f}M"
    return f"${v:,.0f}"

def _price(v):
    try: return f"${float(v):,.2f}"
    except (TypeError, ValueError): return None

def _pct(v):
    try: return f"{float(v)*100:.2f}%"
    except (TypeError, ValueError): return None

def _pct1(v):                       # value already in percent units
    try: return f"{float(v):.1f}%"
    except (TypeError, ValueError): return None

def _mult(v):
    try: return f"{float(v):.2f}x"
    except (TypeError, ValueError): return None

def _num(v):
    try: return f"{float(v):,.2f}"
    except (TypeError, ValueError): return None

def _int(v):
    try: return f"{int(float(v)):,}"
    except (TypeError, ValueError): return None

def _str(v):
    return str(v) if v not in (None, "") else None


# ── equity metrics (Yahoo `info`) ─────────────────────────────────────────────
# alias -> (info key OR callable(info), label, formatter, group)
EQUITY_METRICS = {
    # valuation
    "marketcap":   ("marketCap", "Market cap", _money, "Valuation"),
    "ev":          ("enterpriseValue", "Enterprise value", _money, "Valuation"),
    "pe":          ("trailingPE", "P/E (TTM)", _mult, "Valuation"),
    "forwardpe":   ("forwardPE", "Forward P/E", _mult, "Valuation"),
    "pb":          ("priceToBook", "Price / book", _mult, "Valuation"),
    "ps":          ("priceToSalesTrailing12Months", "Price / sales", _mult, "Valuation"),
    "peg":         ("trailingPegRatio", "PEG ratio", _num, "Valuation"),
    "evrevenue":   ("enterpriseToRevenue", "EV / revenue", _mult, "Valuation"),
    "evebitda":    ("enterpriseToEbitda", "EV / EBITDA", _mult, "Valuation"),
    # profitability
    "grossmargin": ("grossMargins", "Gross margin", _pct, "Profitability"),
    "operatingmargin": ("operatingMargins", "Operating margin", _pct, "Profitability"),
    "netmargin":   ("profitMargins", "Net margin", _pct, "Profitability"),
    "ebitdamargin": ("ebitdaMargins", "EBITDA margin", _pct, "Profitability"),
    "roe":         ("returnOnEquity", "Return on equity", _pct, "Profitability"),
    "roa":         ("returnOnAssets", "Return on assets", _pct, "Profitability"),
    # income statement
    "revenue":     ("totalRevenue", "Revenue (TTM)", _money, "Income"),
    "grossprofit": ("grossProfits", "Gross profit", _money, "Income"),
    "ebitda":      ("ebitda", "EBITDA", _money, "Income"),
    "netincome":   ("netIncomeToCommon", "Net income", _money, "Income"),
    "eps":         ("trailingEps", "EPS (TTM)", _price, "Income"),
    "forwardeps":  ("forwardEps", "Forward EPS", _price, "Income"),
    "revpershare": ("revenuePerShare", "Revenue / share", _price, "Income"),
    # growth
    "revgrowth":   ("revenueGrowth", "Revenue growth (YoY)", _pct, "Growth"),
    "earngrowth":  ("earningsGrowth", "Earnings growth (YoY)", _pct, "Growth"),
    "qtrgrowth":   ("earningsQuarterlyGrowth", "Quarterly earnings growth", _pct, "Growth"),
    # cash flow & balance sheet
    "fcf":         ("freeCashflow", "Free cash flow", _money, "Balance sheet"),
    "ocf":         ("operatingCashflow", "Operating cash flow", _money, "Balance sheet"),
    "cash":        ("totalCash", "Total cash", _money, "Balance sheet"),
    "debt":        ("totalDebt", "Total debt", _money, "Balance sheet"),
    "netdebt":     (lambda i: (i.get("totalDebt") or 0) - (i.get("totalCash") or 0), "Net debt", _money, "Balance sheet"),
    "debttoequity": ("debtToEquity", "Debt / equity", _num, "Balance sheet"),
    "currentratio": ("currentRatio", "Current ratio", _num, "Balance sheet"),
    "quickratio":  ("quickRatio", "Quick ratio", _num, "Balance sheet"),
    "bookvalue":   ("bookValue", "Book value / share", _price, "Balance sheet"),
    "cashpershare": ("totalCashPerShare", "Cash / share", _price, "Balance sheet"),
    "fcfyield":    (lambda i: (i.get("freeCashflow") / i["marketCap"]) if i.get("freeCashflow") and i.get("marketCap") else None, "FCF yield", _pct, "Balance sheet"),
    # dividends
    "divyield":    ("dividendYield", "Dividend yield", _pct1, "Dividends"),
    "divrate":     ("dividendRate", "Dividend rate", _price, "Dividends"),
    "payout":      ("payoutRatio", "Payout ratio", _pct, "Dividends"),
    "div5yr":      ("fiveYearAvgDividendYield", "5y avg div yield", _pct1, "Dividends"),
    # trading / risk
    "price":       ("currentPrice", "Price", _price, "Trading"),
    "beta":        ("beta", "Beta", _num, "Trading"),
    "high52":      ("fiftyTwoWeekHigh", "52-week high", _price, "Trading"),
    "low52":       ("fiftyTwoWeekLow", "52-week low", _price, "Trading"),
    "ma50":        ("fiftyDayAverage", "50-day average", _price, "Trading"),
    "ma200":       ("twoHundredDayAverage", "200-day average", _price, "Trading"),
    "avgvolume":   ("averageVolume", "Avg volume", _int, "Trading"),
    "shares":      ("sharesOutstanding", "Shares outstanding", _int, "Trading"),
    "float":       ("floatShares", "Float", _int, "Trading"),
    # short interest / ownership
    "shortpct":    ("shortPercentOfFloat", "Short % of float", _pct, "Ownership"),
    "shortratio":  ("shortRatio", "Short ratio (days)", _num, "Ownership"),
    "shares_short": ("sharesShort", "Shares short", _int, "Ownership"),
    "insiderown":  ("heldPercentInsiders", "Insider ownership", _pct, "Ownership"),
    "instown":     ("heldPercentInstitutions", "Institutional ownership", _pct, "Ownership"),
    # analyst
    "target":      ("targetMeanPrice", "Avg price target", _price, "Analyst"),
    "targethigh":  ("targetHighPrice", "High price target", _price, "Analyst"),
    "targetlow":   ("targetLowPrice", "Low price target", _price, "Analyst"),
    "rating":      ("recommendationMean", "Analyst rating (1=buy)", _num, "Analyst"),
    "analysts":    ("numberOfAnalystOpinions", "# analysts", _int, "Analyst"),
    # company
    "employees":   ("fullTimeEmployees", "Employees", _int, "Company"),
    "sector":      ("sector", "Sector", _str, "Company"),
    "industry":    ("industry", "Industry", _str, "Company"),
    "country":     ("country", "Country", _str, "Company"),
    "website":     ("website", "Website", _str, "Company"),
}

# friendly synonyms
EQUITY_METRICS["industrial"] = EQUITY_METRICS["sector"]  # avoid global-board confusion on a stock

_info_cache = {}


def _info(symbol):
    key = symbol.upper()
    hit = _info_cache.get(key)
    if hit and time.time() - hit[0] < 600:
        return hit[1]
    import yfinance as yf
    info = yf.Ticker(symbol).info or {}
    _info_cache[key] = (time.time(), info)
    return info


def _resolve_equity(info, spec):
    src = spec[0]
    raw = src(info) if callable(src) else info.get(src)
    return spec[2](raw)


def equity_metric(symbol, alias):
    spec = EQUITY_METRICS.get(alias)
    if not spec:
        return None
    val = _resolve_equity(_info(symbol), spec)
    return f"  {spec[1]:<26} {val if val is not None else '—'}"


def equity_groups(symbol):
    """{group: [(label, value), …]} for rendering a grouped table. Skips blanks."""
    info = _info(symbol)
    groups = {}
    for alias, spec in EQUITY_METRICS.items():
        if alias == "industrial":
            continue
        val = _resolve_equity(info, spec)
        if val is not None:
            groups.setdefault(spec[3], []).append((spec[1], val))
    ordered = {}
    for g in ("Valuation", "Profitability", "Income", "Growth", "Balance sheet",
              "Dividends", "Trading", "Ownership", "Analyst", "Company"):
        if groups.get(g):
            ordered[g] = groups[g]
    return ordered


_COUNTRY_CATS = ["Economy", "Sectors", "Prices & money", "Labor", "Trade",
                 "Fiscal", "Demographics", "Health", "Education",
                 "Energy & environment", "Infrastructure", "Society"]


def country_groups(iso):
    """{category: [(label, value, year), …]} — fetched concurrently for speed."""
    from concurrent.futures import ThreadPoolExecutor
    from src.data.worldbank import _series
    seen, specs = set(), []
    for alias, spec in COUNTRY_METRICS.items():
        if spec[0] in seen:
            continue
        seen.add(spec[0])
        specs.append(spec)

    def fetch(spec):
        s = _series(iso, spec[0], 1)
        if not s:
            return None
        yr, v = s[-1]
        val = spec[2](v)
        cat = spec[3] if len(spec) > 3 else "Other"
        return (cat, spec[1], val, str(yr)) if val is not None else None

    groups = {}
    with ThreadPoolExecutor(max_workers=16) as ex:
        for r in ex.map(fetch, specs):
            if r:
                groups.setdefault(r[0], []).append((r[1], r[2], r[3]))
    return {c: groups[c] for c in _COUNTRY_CATS if c in groups}


def country_rows(iso):
    """[(label, value, year), …] across the indicator set (flat)."""
    out = []
    for cat, rows in country_groups(iso).items():
        out.extend(rows)
    return out


def equity_all(symbol, name=""):
    info = _info(symbol)
    groups = {}
    for alias, spec in EQUITY_METRICS.items():
        if alias == "industrial":
            continue
        val = _resolve_equity(info, spec)
        if val is None:
            continue
        groups.setdefault(spec[3], []).append((spec[1], val))
    if not groups:
        return f"No fundamental data available for {symbol}."
    out = [f"{name or symbol} — Fundamentals  ({sum(len(v) for v in groups.values())} fields)",
           "Source: Yahoo Finance", ""]
    for g in ("Valuation", "Profitability", "Income", "Growth", "Balance sheet",
              "Dividends", "Trading", "Ownership", "Analyst", "Company"):
        rows = groups.get(g)
        if not rows:
            continue
        out.append(f"  [{g}]")
        for label, val in rows:
            out.append(f"    {label:<26} {val}")
        out.append("")
    return "\n".join(out).rstrip()


# ── country metrics (World Bank — the SAME indicators for every country) ──────
# alias -> (WB code, label, formatter, category).  Same firehose for all regions.
_CM = COUNTRY_METRICS = {
    # Economy
    "gdp":        ("NY.GDP.MKTP.CD", "GDP (current US$)", _money, "Economy"),
    "gdpppp":     ("NY.GDP.MKTP.PP.CD", "GDP (PPP)", _money, "Economy"),
    "gdppc":      ("NY.GDP.PCAP.CD", "GDP per capita", _money, "Economy"),
    "gdppcppp":   ("NY.GDP.PCAP.PP.CD", "GDP per capita (PPP)", _money, "Economy"),
    "growth":     ("NY.GDP.MKTP.KD.ZG", "Real GDP growth", _pct1, "Economy"),
    "gdppcgrowth": ("NY.GDP.PCAP.KD.ZG", "GDP per-capita growth", _pct1, "Economy"),
    "gni":        ("NY.GNP.MKTP.CD", "GNI (current US$)", _money, "Economy"),
    "gnipc":      ("NY.GNP.PCAP.CD", "GNI per capita", _money, "Economy"),
    "savings":    ("NY.GNS.ICTR.ZS", "Gross savings (%GDP)", _pct1, "Economy"),
    "investment": ("NE.GDI.TOTL.ZS", "Investment (%GDP)", _pct1, "Economy"),
    "capformation": ("NE.GDI.FTOT.ZS", "Gross capital formation (%GDP)", _pct1, "Economy"),
    "consumption": ("NE.CON.TOTL.ZS", "Final consumption (%GDP)", _pct1, "Economy"),
    "deflator":   ("NY.GDP.DEFL.KD.ZG", "GDP deflator", _pct1, "Economy"),
    # Sectors
    "agriculture": ("NV.AGR.TOTL.ZS", "Agriculture (%GDP)", _pct1, "Sectors"),
    "industry":   ("NV.IND.TOTL.ZS", "Industry (%GDP)", _pct1, "Sectors"),
    "industrial": ("NV.IND.TOTL.ZS", "Industry value added (%GDP)", _pct1, "Sectors"),
    "manufacturing": ("NV.IND.MANF.ZS", "Manufacturing (%GDP)", _pct1, "Sectors"),
    "services":   ("NV.SRV.TOTL.ZS", "Services (%GDP)", _pct1, "Sectors"),
    "naturalresources": ("NY.GDP.TOTL.RT.ZS", "Resource rents (%GDP)", _pct1, "Sectors"),
    # Prices & money
    "inflation":  ("FP.CPI.TOTL.ZG", "Inflation (CPI)", _pct1, "Prices & money"),
    "foodinflation": ("FP.FPI.TOTL", "Food price index", _num, "Prices & money"),
    "lending":    ("FR.INR.LEND", "Lending rate", _pct1, "Prices & money"),
    "deposit":    ("FR.INR.DPST", "Deposit rate", _pct1, "Prices & money"),
    "realrate":   ("FR.INR.RINR", "Real interest rate", _pct1, "Prices & money"),
    "broadmoney": ("FM.LBL.BMNY.GD.ZS", "Broad money (%GDP)", _pct1, "Prices & money"),
    "moneygrowth": ("FM.LBL.BMNY.ZG", "Money supply growth", _pct1, "Prices & money"),
    "domesticcredit": ("FS.AST.PRVT.GD.ZS", "Private credit (%GDP)", _pct1, "Prices & money"),
    "marketcap":  ("CM.MKT.LCAP.GD.ZS", "Stock mkt cap (%GDP)", _pct1, "Prices & money"),
    # Labor
    "unemployment": ("SL.UEM.TOTL.ZS", "Unemployment", _pct1, "Labor"),
    "youthunemployment": ("SL.UEM.1524.ZS", "Youth unemployment", _pct1, "Labor"),
    "laborforce": ("SL.TLF.TOTL.IN", "Labor force", _int, "Labor"),
    "participation": ("SL.TLF.CACT.ZS", "Labor participation", _pct1, "Labor"),
    "employment": ("SL.EMP.TOTL.SP.ZS", "Employment ratio", _pct1, "Labor"),
    "femalelabor": ("SL.TLF.CACT.FE.ZS", "Female participation", _pct1, "Labor"),
    "vulnerable": ("SL.EMP.VULN.ZS", "Vulnerable employment", _pct1, "Labor"),
    # Trade & external
    "exports":    ("NE.EXP.GNFS.ZS", "Exports (%GDP)", _pct1, "Trade"),
    "imports":    ("NE.IMP.GNFS.ZS", "Imports (%GDP)", _pct1, "Trade"),
    "trade":      ("NE.TRD.GNFS.ZS", "Trade (%GDP)", _pct1, "Trade"),
    "exportsusd": ("NE.EXP.GNFS.CD", "Exports (US$)", _money, "Trade"),
    "importsusd": ("NE.IMP.GNFS.CD", "Imports (US$)", _money, "Trade"),
    "currentaccount": ("BN.CAB.XOKA.GD.ZS", "Current account (%GDP)", _pct1, "Trade"),
    "fdi":        ("BX.KLT.DINV.WD.GD.ZS", "FDI inflows (%GDP)", _pct1, "Trade"),
    "fdiout":     ("BM.KLT.DINV.WD.GD.ZS", "FDI outflows (%GDP)", _pct1, "Trade"),
    "remittances": ("BX.TRF.PWKR.DT.GD.ZS", "Remittances (%GDP)", _pct1, "Trade"),
    "hightech":   ("TX.VAL.TECH.MF.ZS", "High-tech exports (%mfg)", _pct1, "Trade"),
    "reserves":   ("FI.RES.TOTL.CD", "Reserves (US$)", _money, "Trade"),
    "reservesmonths": ("FI.RES.TOTL.MO", "Reserves (months imports)", _num, "Trade"),
    "externaldebt": ("DT.DOD.DECT.CD", "External debt (US$)", _money, "Trade"),
    "debtservice": ("DT.TDS.DECT.EX.ZS", "Debt service (%exports)", _pct1, "Trade"),
    # Fiscal
    "debt":       ("GC.DOD.TOTL.GD.ZS", "Govt debt (%GDP)", _pct1, "Fiscal"),
    "tax":        ("GC.TAX.TOTL.GD.ZS", "Tax revenue (%GDP)", _pct1, "Fiscal"),
    "revenue":    ("GC.REV.XGRT.GD.ZS", "Govt revenue (%GDP)", _pct1, "Fiscal"),
    "expense":    ("GC.XPN.TOTL.GD.ZS", "Govt expense (%GDP)", _pct1, "Fiscal"),
    "deficit":    ("GC.NLD.TOTL.GD.ZS", "Fiscal balance (%GDP)", _pct1, "Fiscal"),
    "military":   ("MS.MIL.XPND.GD.ZS", "Military spend (%GDP)", _pct1, "Fiscal"),
    "militarypersonnel": ("MS.MIL.TOTL.P1", "Armed-forces personnel", _int, "Fiscal"),
    # Demographics
    "population": ("SP.POP.TOTL", "Population", _int, "Demographics"),
    "popgrowth":  ("SP.POP.GROW", "Population growth", _pct1, "Demographics"),
    "popdensity": ("EN.POP.DNST", "Population density (/km²)", _num, "Demographics"),
    "urban":      ("SP.URB.TOTL.IN.ZS", "Urban population", _pct1, "Demographics"),
    "rural":      ("SP.RUR.TOTL.ZS", "Rural population", _pct1, "Demographics"),
    "age014":     ("SP.POP.0014.TO.ZS", "Population 0-14", _pct1, "Demographics"),
    "age65":      ("SP.POP.65UP.TO.ZS", "Population 65+", _pct1, "Demographics"),
    "dependency": ("SP.POP.DPND", "Age dependency ratio", _num, "Demographics"),
    "fertility":  ("SP.DYN.TFRT.IN", "Fertility rate", _num, "Demographics"),
    "birthrate":  ("SP.DYN.CBRT.IN", "Birth rate (/1k)", _num, "Demographics"),
    "deathrate":  ("SP.DYN.CDRT.IN", "Death rate (/1k)", _num, "Demographics"),
    "migration":  ("SM.POP.NETM", "Net migration", _int, "Demographics"),
    # Health
    "lifeexp":    ("SP.DYN.LE00.IN", "Life expectancy", _num, "Health"),
    "lifeexpmale": ("SP.DYN.LE00.MA.IN", "Life expectancy (male)", _num, "Health"),
    "lifeexpfemale": ("SP.DYN.LE00.FE.IN", "Life expectancy (female)", _num, "Health"),
    "mortality":  ("SP.DYN.IMRT.IN", "Infant mortality (/1k)", _num, "Health"),
    "under5mortality": ("SH.DYN.MORT", "Under-5 mortality (/1k)", _num, "Health"),
    "maternalmortality": ("SH.STA.MMRT", "Maternal mortality", _int, "Health"),
    "health":     ("SH.XPD.CHEX.GD.ZS", "Health spend (%GDP)", _pct1, "Health"),
    "healthpc":   ("SH.XPD.CHEX.PC.CD", "Health spend / capita", _money, "Health"),
    "physicians": ("SH.MED.PHYS.ZS", "Physicians (/1k)", _num, "Health"),
    "hospitalbeds": ("SH.MED.BEDS.ZS", "Hospital beds (/1k)", _num, "Health"),
    "immunization": ("SH.IMM.IDPT", "DPT immunization", _pct1, "Health"),
    "undernourished": ("SN.ITK.DEFC.ZS", "Undernourishment", _pct1, "Health"),
    # Education
    "education":  ("SE.XPD.TOTL.GD.ZS", "Education spend (%GDP)", _pct1, "Education"),
    "literacy":   ("SE.ADT.LITR.ZS", "Adult literacy", _pct1, "Education"),
    "primary":    ("SE.PRM.ENRR", "Primary enrollment", _pct1, "Education"),
    "secondary":  ("SE.SEC.ENRR", "Secondary enrollment", _pct1, "Education"),
    "tertiary":   ("SE.TER.ENRR", "Tertiary enrollment", _pct1, "Education"),
    "pupilteacher": ("SE.PRM.ENRL.TC.ZS", "Pupil-teacher ratio", _num, "Education"),
    # Energy & environment
    "co2":        ("EN.GHG.CO2.PC.CE.AR5", "CO₂ per capita (t)", _num, "Energy & environment"),
    "co2total":   ("EN.GHG.CO2.MT.CE.AR5", "CO₂ total (Mt)", _num, "Energy & environment"),
    "energyuse":  ("EG.USE.PCAP.KG.OE", "Energy use / capita", _num, "Energy & environment"),
    "energyimports": ("EG.IMP.CONS.ZS", "Energy imports (%use)", _pct1, "Energy & environment"),
    "renewables": ("EG.FEC.RNEW.ZS", "Renewable energy share", _pct1, "Energy & environment"),
    "electricity": ("EG.ELC.ACCS.ZS", "Electricity access", _pct1, "Energy & environment"),
    "electricitypc": ("EG.USE.ELEC.KH.PC", "Electricity use / capita", _num, "Energy & environment"),
    "forest":     ("AG.LND.FRST.ZS", "Forest area", _pct1, "Energy & environment"),
    "agriland":   ("AG.LND.AGRI.ZS", "Agricultural land", _pct1, "Energy & environment"),
    "arable":     ("AG.LND.ARBL.ZS", "Arable land", _pct1, "Energy & environment"),
    "protected":  ("ER.LND.PTLD.ZS", "Protected areas", _pct1, "Energy & environment"),
    "pm25":       ("EN.ATM.PM25.MC.M3", "PM2.5 air pollution", _num, "Energy & environment"),
    "landarea":   ("AG.LND.TOTL.K2", "Land area (km²)", _int, "Energy & environment"),
    # Infrastructure & tech
    "internet":   ("IT.NET.USER.ZS", "Internet users", _pct1, "Infrastructure"),
    "mobile":     ("IT.CEL.SETS.P2", "Mobile / 100 people", _num, "Infrastructure"),
    "broadband":  ("IT.NET.BBND.P2", "Fixed broadband / 100", _num, "Infrastructure"),
    "airpassengers": ("IS.AIR.PSGR", "Air passengers", _int, "Infrastructure"),
    "airfreight": ("IS.AIR.GOOD.MT.K1", "Air freight (M ton-km)", _num, "Infrastructure"),
    "railways":   ("IS.RRS.TOTL.KM", "Rail lines (km)", _int, "Infrastructure"),
    "containers": ("IS.SHP.GOOD.TU", "Container port traffic", _int, "Infrastructure"),
    # Inequality & tourism & business
    "gini":       ("SI.POV.GINI", "Gini (inequality)", _num, "Society"),
    "poverty":    ("SI.POV.DDAY", "Poverty ($2.15/day)", _pct1, "Society"),
    "povertynat": ("SI.POV.NAHC", "Poverty (national)", _pct1, "Society"),
    "incometop10": ("SI.DST.10TH.10", "Income share top 10%", _pct1, "Society"),
    "tourism":    ("ST.INT.ARVL", "Tourist arrivals", _int, "Society"),
    "tourismreceipts": ("ST.INT.RCPT.CD", "Tourism receipts (US$)", _money, "Society"),
    "startbusiness": ("IC.REG.DURS", "Days to start a business", _num, "Society"),
}


def country_metric(iso, alias):
    spec = COUNTRY_METRICS.get(alias)
    if not spec:
        return None
    from src.data.worldbank import _series
    s = _series(iso, spec[0], 1)
    if not s:
        return f"  {spec[1]:<28} —"
    yr, v = s[-1]
    return f"  {spec[1]:<28} {spec[2](v) or '—'}  ({yr})"


def country_all(iso, name=""):
    from src.data.worldbank import _series
    out = [f"{name} — Country Indicators", "Source: World Bank", ""]
    seen = set()
    found = 0
    for alias, spec in COUNTRY_METRICS.items():
        if spec[0] in seen:                # skip duplicate codes (industry/industrial)
            continue
        seen.add(spec[0])
        s = _series(iso, spec[0], 1)
        if not s:
            continue
        yr, v = s[-1]
        val = spec[2](v)
        if val is not None:
            out.append(f"  {spec[1]:<30} {val:>16}  ({yr})")
            found += 1
    if not found:
        return f"No World Bank indicators available for {name}."
    out[0] = f"{name} — Country Indicators  ({found} fields)"
    return "\n".join(out)


# ── dispatch ──────────────────────────────────────────────────────────────────

def metric_aliases(kind):
    if kind in ("equity", "etf"):
        return list(EQUITY_METRICS)
    if kind == "country":
        return list(COUNTRY_METRICS)
    return []


def is_metric(kind, alias):
    return alias.lower() in metric_aliases(kind)


def card(subject, aliases):
    """(title, body) for a *set* of metrics on one subject — so chained fields
    render as a single card instead of one panel each. None if none apply."""
    rows = []
    if subject.kind in ("equity", "etf"):
        info = _info(subject.symbol)
        for a in aliases:
            spec = EQUITY_METRICS.get(a.lower())
            if spec:
                rows.append((spec[1], _resolve_equity(info, spec)))
    elif subject.kind == "country":
        from src.data.worldbank import _series
        for a in aliases:
            spec = COUNTRY_METRICS.get(a.lower())
            if not spec:
                continue
            s = _series(subject.ref, spec[0], 1)
            rows.append((spec[1], (f"{spec[2](s[-1][1])}  ({s[-1][0]})") if s else None))
    if not rows:
        return None
    w = max((len(l) for l, _ in rows), default=20) + 3
    body = "\n".join(f"  {l:<{w}} {v if v is not None else '—'}" for l, v in rows)
    title = (f"{subject.symbol}  ›  {rows[0][0]}" if len(rows) == 1
             else f"{subject.symbol}  ›  Metrics")
    return title, body
