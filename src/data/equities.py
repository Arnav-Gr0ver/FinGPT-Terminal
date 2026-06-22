"""Equities data — Yahoo Finance via yfinance."""

import yfinance as yf


def _large(n) -> str:
    if n is None:
        return "N/A"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "N/A"
    if n != n:
        return "N/A"
    if abs(n) >= 1e12:
        return f"${n/1e12:.2f}T"
    if abs(n) >= 1e9:
        return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"


def _pct(n) -> str:
    if n is None:
        return "N/A"
    try:
        f = float(n)
    except (TypeError, ValueError):
        return "N/A"
    if f != f:
        return "N/A"
    return f"{f * 100:.1f}%"


def _num(n, suffix="x", decimals=2) -> str:
    if n is None:
        return "N/A"
    try:
        f = float(n)
    except (TypeError, ValueError):
        return "N/A"
    if f != f:
        return "N/A"
    return f"{f:.{decimals}f}{suffix}"


def get_quote(ticker: str) -> str:
    try:
        t    = yf.Ticker(ticker)
        fast = t.fast_info
        info = t.info

        price  = fast.last_price
        prev   = fast.previous_close or price
        change = price - prev
        pct    = change / prev * 100 if prev else 0
        sign   = "+" if change >= 0 else ""
        arrow  = "▲" if change >= 0 else "▼"

        name     = info.get("longName") or info.get("shortName") or ticker.upper()
        exchange = info.get("exchangeAcronym") or info.get("exchange") or ""
        mktcap   = info.get("marketCap")
        vol      = fast.three_month_average_volume
        hi52     = fast.year_high
        lo52     = fast.year_low
        pe       = info.get("trailingPE")
        div      = info.get("trailingAnnualDividendYield")
        sector   = info.get("sector") or ""

        w = 16
        lines = [
            f"{name} ({ticker.upper()})   {exchange}",
        ]
        if sector:
            lines.append(f"{sector}")
        lines += [
            "",
            f"  {'Price':<{w}} ${price:,.2f}",
            f"  {'Change':<{w}} {sign}${abs(change):.2f}  ({sign}{pct:.2f}%)  {arrow}",
            "",
            f"  {'Market Cap':<{w}} {_large(mktcap)}",
            f"  {'Avg Volume':<{w}} {vol/1e6:.1f}M" if vol else f"  {'Avg Volume':<{w}} N/A",
            f"  {'52W High':<{w}} ${hi52:,.2f}",
            f"  {'52W Low':<{w}} ${lo52:,.2f}",
        ]
        if pe:
            lines.append(f"  {'P/E (TTM)':<{w}} {_num(pe)}")
        if div:
            lines.append(f"  {'Div Yield':<{w}} {_pct(div)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch quote for {ticker}: {e}"


def get_ratios(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
        w = 22

        sections = [
            ("Valuation", [
                ("P/E (TTM)",        _num(info.get("trailingPE"))),
                ("Forward P/E",      _num(info.get("forwardPE"))),
                ("P/B",              _num(info.get("priceToBook"))),
                ("EV / EBITDA",      _num(info.get("enterpriseToEbitda"))),
                ("EV / Revenue",     _num(info.get("enterpriseToRevenue"))),
                ("PEG Ratio",        _num(info.get("pegRatio"))),
            ]),
            ("Profitability", [
                ("Gross Margin",     _pct(info.get("grossMargins"))),
                ("Operating Margin", _pct(info.get("operatingMargins"))),
                ("Net Margin",       _pct(info.get("profitMargins"))),
                ("ROE",              _pct(info.get("returnOnEquity"))),
                ("ROA",              _pct(info.get("returnOnAssets"))),
            ]),
            ("Growth (YoY)", [
                ("Revenue Growth",   _pct(info.get("revenueGrowth"))),
                ("Earnings Growth",  _pct(info.get("earningsGrowth"))),
            ]),
            ("Risk & Capital", [
                ("Beta",             _num(info.get("beta"), suffix="")),
                ("Debt / Equity",    _num(info.get("debtToEquity"))),
                ("Current Ratio",    _num(info.get("currentRatio"), suffix="")),
                ("Quick Ratio",      _num(info.get("quickRatio"), suffix="")),
            ]),
        ]

        lines = []
        for header, rows in sections:
            lines.append(header)
            for label, val in rows:
                if val != "N/A":
                    lines.append(f"  {label:<{w}} {val}")
            lines.append("")
        return "\n".join(lines).rstrip()
    except Exception as e:
        return f"Could not fetch ratios for {ticker}: {e}"


def get_income(ticker: str) -> str:
    try:
        df = yf.Ticker(ticker).income_stmt
        if df is None or df.empty:
            return f"No income statement data for {ticker}."

        cols = df.columns[:4]
        years = [c.year for c in cols]

        want = {
            "Total Revenue":       "Revenue",
            "Gross Profit":        "Gross Profit",
            "Operating Income":    "Operating Income",
            "Net Income":          "Net Income",
            "EBITDA":              "EBITDA",
        }

        header = f"  {'(USD billions)':<22}" + "".join(f"{y:>10}" for y in years)
        lines  = ["Annual Income Statement", "", header, "  " + "─" * (22 + 10 * len(years))]

        for src_key, label in want.items():
            if src_key in df.index:
                row = df.loc[src_key, cols]
                vals = "".join(
                    f"{v/1e9:>9.1f}B" if v == v else f"{'N/A':>10}"
                    for v in row
                )
                lines.append(f"  {label:<22}{vals}")

        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch income statement for {ticker}: {e}"


def get_balance(ticker: str) -> str:
    try:
        df = yf.Ticker(ticker).balance_sheet
        if df is None or df.empty:
            return f"No balance sheet data for {ticker}."

        cols  = df.columns[:4]
        years = [c.year for c in cols]

        want = {
            "Total Assets":           "Total Assets",
            "Total Liabilities Net Minority Interest": "Total Liabilities",
            "Stockholders Equity":    "Shareholders Equity",
            "Cash And Cash Equivalents": "Cash & Equivalents",
            "Total Debt":             "Total Debt",
            "Net Debt":               "Net Debt",
        }

        header = f"  {'(USD billions)':<26}" + "".join(f"{y:>10}" for y in years)
        lines  = ["Annual Balance Sheet", "", header, "  " + "─" * (26 + 10 * len(years))]

        for src_key, label in want.items():
            if src_key in df.index:
                row = df.loc[src_key, cols]
                vals = "".join(
                    f"{v/1e9:>9.1f}B" if v == v else f"{'N/A':>10}"
                    for v in row
                )
                lines.append(f"  {label:<26}{vals}")

        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch balance sheet for {ticker}: {e}"


def get_earnings(ticker: str) -> str:
    try:
        t  = yf.Ticker(ticker)
        df = t.earnings_dates

        if df is None or df.empty:
            return f"No earnings data for {ticker}."

        df = df.dropna(subset=["EPS Estimate", "Reported EPS"], how="all")
        df = df[df["Reported EPS"].notna()].head(8)

        if df.empty:
            return f"No reported earnings found for {ticker}."

        lines = [
            "Earnings History  (last 8 quarters)",
            "",
            f"  {'Quarter':<14} {'Estimate':>10} {'Reported':>10} {'Surprise':>10}",
            "  " + "─" * 48,
        ]

        for date, row in df.iterrows():
            est      = row.get("EPS Estimate")
            reported = row.get("Reported EPS")
            surprise = row.get("Surprise(%)")

            est_s  = f"${est:.2f}"      if est == est      else "N/A"
            rep_s  = f"${reported:.2f}" if reported == reported else "N/A"
            sur_s  = f"{surprise:+.1f}%" if surprise == surprise else "N/A"

            quarter = date.strftime("%b %Y")
            lines.append(f"  {quarter:<14} {est_s:>10} {rep_s:>10} {sur_s:>10}")

        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch earnings for {ticker}: {e}"


def get_short_interest(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
        w    = 24

        short_pct   = info.get("shortPercentOfFloat")
        shares_short= info.get("sharesShort")
        days_cover  = info.get("shortRatio")
        shares_out  = info.get("sharesOutstanding")
        float_shares= info.get("floatShares")

        lines = [
            "Short Interest",
            "",
            f"  {'Short % of Float':<{w}} {_pct(short_pct)}",
            f"  {'Days to Cover':<{w}} {_num(days_cover, suffix=' days')}",
            f"  {'Shares Short':<{w}} {_large(shares_short).replace('$', '')}",
            f"  {'Float':<{w}} {_large(float_shares).replace('$', '')}",
            f"  {'Shares Outstanding':<{w}} {_large(shares_out).replace('$', '')}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch short interest for {ticker}: {e}"


def get_comparison(tickers: list) -> str:
    """Side-by-side fundamentals for 2–4 equities."""
    from src.data.crypto import is_crypto
    # Equities only — crypto has no comparable fundamentals here.
    tickers = [t.upper().strip() for t in tickers if t.strip() and not is_crypto(t)][:4]
    if len(tickers) < 2:
        return "Usage: compare <ticker> <ticker> [ticker ...]  (equities only)  e.g. compare AAPL MSFT NVDA"

    # Pull each ticker's data once.
    cols = {}
    for sym in tickers:
        try:
            t    = yf.Ticker(sym)
            info = t.info
            fast = t.fast_info
            price = fast.last_price
            prev  = fast.previous_close or price
            day   = (price - prev) / prev * 100 if prev else None
            cols[sym] = {"info": info, "price": price, "day": day}
        except Exception:
            cols[sym] = None

    def _day(c):
        if not c or c["day"] is None:
            return "N/A"
        return f"{c['day']:+.2f}%"

    def _price(c):
        if not c or c["price"] is None:
            return "N/A"
        return f"${c['price']:,.2f}"

    # (label, accessor) — accessor takes the per-ticker dict, returns a string.
    rows = [
        ("Price",          _price),
        ("1D Change",      _day),
        ("Market Cap",     lambda c: _large(c["info"].get("marketCap")) if c else "N/A"),
        ("P/E (TTM)",      lambda c: _num(c["info"].get("trailingPE")) if c else "N/A"),
        ("Forward P/E",    lambda c: _num(c["info"].get("forwardPE")) if c else "N/A"),
        ("P/B",            lambda c: _num(c["info"].get("priceToBook")) if c else "N/A"),
        ("EV / EBITDA",    lambda c: _num(c["info"].get("enterpriseToEbitda")) if c else "N/A"),
        ("Gross Margin",   lambda c: _pct(c["info"].get("grossMargins")) if c else "N/A"),
        ("Net Margin",     lambda c: _pct(c["info"].get("profitMargins")) if c else "N/A"),
        ("ROE",            lambda c: _pct(c["info"].get("returnOnEquity")) if c else "N/A"),
        ("Rev Growth",     lambda c: _pct(c["info"].get("revenueGrowth")) if c else "N/A"),
        ("Beta",           lambda c: _num(c["info"].get("beta"), suffix="") if c else "N/A"),
    ]

    lw = 16          # label column
    cw = 14          # per-ticker column
    header = f"  {'':<{lw}}" + "".join(f"{sym:>{cw}}" for sym in tickers)
    lines  = ["Side-by-Side Comparison", "", header, "  " + "─" * (lw + cw * len(tickers))]
    for label, fn in rows:
        cells = "".join(f"{fn(cols[sym]):>{cw}}" for sym in tickers)
        lines.append(f"  {label:<{lw}}{cells}")
    return "\n".join(lines)


def get_simple_quote(yf_symbol: str, name: str = "") -> str:
    """Lightweight quote for indices / commodities / FX (no fundamentals)."""
    try:
        fast = yf.Ticker(yf_symbol).fast_info
        price = fast.last_price
        prev  = fast.previous_close or price
        if price is None:
            return f"No price data for {name or yf_symbol}."
        change = price - prev
        pct    = change / prev * 100 if prev else 0
        arrow  = "▲" if change >= 0 else "▼"
        sign   = "+" if change >= 0 else "-"
        w = 16
        lines = [name or yf_symbol, ""]
        lines += [
            f"  {'Price':<{w}} {price:,.2f}",
            f"  {'Change':<{w}} {sign}{abs(change):,.2f}  ({sign}{abs(pct):.2f}%)  {arrow}",
        ]
        if fast.year_high:
            lines.append(f"  {'52W High':<{w}} {fast.year_high:,.2f}")
            lines.append(f"  {'52W Low':<{w}} {fast.year_low:,.2f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch quote for {name or yf_symbol}: {e}"


def get_profile(ticker: str) -> str:
    """Company profile — sector, industry, headcount, and business summary."""
    try:
        info = yf.Ticker(ticker).info
        name = info.get("longName") or info.get("shortName") or ticker.upper()
        w = 14
        rows = [
            ("Sector",    info.get("sector")),
            ("Industry",  info.get("industry")),
            ("Country",   info.get("country")),
            ("Employees", f"{info.get('fullTimeEmployees'):,}" if info.get("fullTimeEmployees") else None),
            ("Website",   info.get("website")),
        ]
        lines = [name, ""]
        for label, val in rows:
            if val:
                lines.append(f"  {label:<{w}} {val}")
        summary = info.get("longBusinessSummary")
        if summary:
            lines += ["", "  " + _wrap(summary, 88)]
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch profile for {ticker}: {e}"


def get_dividends(ticker: str) -> str:
    """Dividend history (last 10 payments) + current yield."""
    try:
        t   = yf.Ticker(ticker)
        div = t.dividends
        info = t.info or {}
        if div is None or div.empty:
            return f"{ticker.upper()} has paid no dividends on record."
        recent = div.tail(10)
        rate  = info.get("dividendRate")
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        lines = [f"Dividend History — {ticker.upper()}", ""]
        # Compute yield from rate/price — yfinance's dividendYield units are
        # inconsistent across versions, so don't trust it directly.
        if rate and price:
            lines.append(f"  Forward yield   {rate / price * 100:.2f}%")
        if rate:
            lines.append(f"  Annual rate     ${rate:.2f}")
        lines += ["", f"  {'Date':<14} {'Amount':>10}", "  " + "─" * 26]
        for date, amt in recent.items():
            lines.append(f"  {date.strftime('%b %d, %Y'):<14} {f'${amt:.4f}':>10}")
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch dividends for {ticker}: {e}"


def get_holders(ticker: str) -> str:
    """Ownership — insider/institutional split + top institutional holders."""
    try:
        t = yf.Ticker(ticker)
        lines = [f"Ownership — {ticker.upper()}", ""]
        labels = {
            "insidersPercentHeld":          ("Insiders held",        "pct"),
            "institutionsPercentHeld":      ("Institutions held",    "pct"),
            "institutionsFloatPercentHeld": ("Institutions (float)", "pct"),
            "institutionsCount":            ("# Institutions",       "int"),
        }
        mh = t.major_holders
        if mh is not None and not mh.empty:
            try:
                col = "Value" if "Value" in mh.columns else mh.columns[0]
                for key, val in mh[col].items():
                    label, fmt = labels.get(key, (key, "pct"))
                    if val != val:  # NaN
                        continue
                    if fmt == "pct":
                        lines.append(f"  {label:<22} {val*100:.1f}%")
                    else:
                        lines.append(f"  {label:<22} {int(val):,}")
            except Exception:
                pass
        inst = t.institutional_holders
        if inst is not None and not inst.empty:
            lines += ["", f"  {'Top Institutions':<30} {'Shares':>14} {'% Out':>8}", "  " + "─" * 56]
            for _, r in inst.head(8).iterrows():
                name   = str(r.get("Holder", ""))[:29]
                shares = r.get("Shares")
                pct    = r.get("pctHeld")
                sh_s   = f"{int(shares):,}" if shares == shares else "N/A"
                pc_s   = f"{pct*100:.1f}%" if pct == pct else "N/A"
                lines.append(f"  {name:<30} {sh_s:>14} {pc_s:>8}")
        if len(lines) <= 2:
            return f"No ownership data available for {ticker.upper()}."
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch ownership for {ticker}: {e}"


def get_analysts(ticker: str) -> str:
    """Analyst price targets + recommendation consensus."""
    try:
        info = yf.Ticker(ticker).info
        w = 20
        lines = [f"Analyst Coverage — {ticker.upper()}", ""]
        rec   = info.get("recommendationKey")
        n     = info.get("numberOfAnalystOpinions")
        if rec:
            lines.append(f"  {'Consensus':<{w}} {rec.replace('_', ' ').title()}"
                         + (f"  ({n} analysts)" if n else ""))
        cur   = info.get("currentPrice") or info.get("regularMarketPrice")
        for label, key in (("Target (low)", "targetLowPrice"),
                           ("Target (mean)", "targetMeanPrice"),
                           ("Target (high)", "targetHighPrice")):
            v = info.get(key)
            if v:
                up = f"  ({(v/cur-1)*100:+.1f}%)" if cur and key == "targetMeanPrice" else ""
                lines.append(f"  {label:<{w}} ${v:,.2f}{up}")
        if len(lines) <= 2:
            return f"No analyst coverage data for {ticker.upper()}."
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch analyst data for {ticker}: {e}"


def _wrap(text: str, width: int) -> str:
    import textwrap
    return "\n  ".join(textwrap.wrap(text, width)[:6])


def get_options(ticker: str) -> str:
    """Nearest-expiry option chain summary: ATM strikes, IV, and put/call ratio."""
    try:
        t = yf.Ticker(ticker)
        exps = t.options
        if not exps:
            return f"No options listed for {ticker.upper()}."
        spot = t.fast_info.last_price
        exp  = exps[0]
        chain = t.option_chain(exp)
        calls, puts = chain.calls, chain.puts

        def near(df):
            df = df.copy()
            df["d"] = (df["strike"] - spot).abs()
            return df.sort_values("d").head(5).sort_values("strike")

        lines = [f"Options — {ticker.upper()}   (expiry {exp}, spot ${spot:,.2f})", ""]
        lines.append(f"  {'Type':<5} {'Strike':>9} {'Last':>9} {'IV':>7} {'Vol':>8} {'OI':>9}")
        lines.append("  " + "─" * 50)
        for label, df in (("CALL", near(calls)), ("PUT", near(puts))):
            for _, r in df.iterrows():
                iv = f"{r['impliedVolatility']*100:.0f}%" if r.get("impliedVolatility") == r.get("impliedVolatility") else "—"
                lines.append(f"  {label:<5} {r['strike']:>9.2f} {r['lastPrice']:>9.2f} {iv:>7} "
                             f"{int(r.get('volume') or 0):>8,} {int(r.get('openInterest') or 0):>9,}")
        pcr = (puts["openInterest"].sum() / calls["openInterest"].sum()
               if calls["openInterest"].sum() else 0)
        lines += ["", f"  Put/Call OI ratio: {pcr:.2f}   ({len(exps)} expiries listed)"]
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch options for {ticker}: {e}"


def get_splits(ticker: str) -> str:
    """Stock split history."""
    try:
        s = yf.Ticker(ticker).splits
        if s is None or s.empty:
            return f"No stock splits on record for {ticker.upper()}."
        out = [f"Stock Splits — {ticker.upper()}", ""]
        for date, ratio in s.tail(12).items():
            r = f"{ratio:.0f}:1" if ratio >= 1 else f"1:{1/ratio:.0f}"
            out.append(f"  {date.strftime('%b %d, %Y'):<16} {r}")
        return "\n".join(out)
    except Exception as e:
        return f"Could not fetch splits for {ticker}: {e}"


def get_chart_data(ticker: str, period: str = "1mo") -> list:
    try:
        df = yf.Ticker(ticker).history(period=period)
        closes = df["Close"].dropna().tolist() if not df.empty else []
        if closes:
            return closes
    except Exception:
        pass
    # Fallback: Stooq (US equities/ETFs).
    try:
        from src.data.stooq import get_closes
        return get_closes(ticker)
    except Exception:
        return []


def get_etf_holdings(ticker: str) -> str:
    """Top holdings + sector weights for an ETF (yfinance funds data)."""
    try:
        fd = yf.Ticker(ticker).funds_data
        lines = [f"Holdings — {ticker.upper()}", ""]
        try:
            top = fd.top_holdings
            if top is not None and not top.empty:
                lines += [f"  {'Symbol':<8} {'% Assets':>9}  Name", "  " + "─" * 50]
                for sym, row in top.head(12).iterrows():
                    pct  = row.get("Holding Percent")
                    name = str(row.get("Name", ""))[:32]
                    lines.append(f"  {str(sym):<8} {pct*100:>8.2f}%  {name}")
        except Exception:
            pass
        try:
            sw = fd.sector_weightings
            if sw:
                lines += ["", "  Sector weights", "  " + "─" * 30]
                for sec, w in sorted(sw.items(), key=lambda x: -x[1])[:8]:
                    lines.append(f"  {sec.replace('_', ' ').title():<22} {w*100:>5.1f}%")
        except Exception:
            pass
        if len(lines) <= 2:
            return f"No holdings data available for {ticker.upper()} (is it an ETF?)."
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch holdings for {ticker}: {e}"


def get_next_earnings(ticker: str) -> str | None:
    """The next upcoming earnings date as 'Mon DD', or None if unknown."""
    try:
        from datetime import datetime
        df = yf.Ticker(ticker).earnings_dates
        if df is None or df.empty:
            return None
        # Future rows have no reported EPS yet; pick the soonest one ahead of now.
        now = datetime.now(df.index.tz) if df.index.tz else datetime.now()
        upcoming = [d for d in df.index if d > now]
        if not upcoming:
            return None
        return min(upcoming).strftime("%b %d")
    except Exception:
        return None


def get_calendar(ticker: str) -> str:
    """Forward-looking catalysts: next earnings, ex-dividend, splits."""
    try:
        from datetime import date
        t   = yf.Ticker(ticker)
        cal = t.calendar or {}
        info = t.info or {}

        def _d(v):
            if v is None:
                return None
            if isinstance(v, (list, tuple)):
                v = v[0] if v else None
            try:
                return v.strftime("%b %d, %Y")
            except Exception:
                return str(v) if v else None

        rows = []
        ed = cal.get("Earnings Date")
        if ed:
            rows.append(("Next Earnings", _d(ed)))
        exd = cal.get("Ex-Dividend Date") or info.get("exDividendDate")
        if isinstance(exd, (int, float)):
            try:
                from datetime import datetime
                exd = datetime.fromtimestamp(exd)
            except Exception:
                exd = None
        if exd:
            rows.append(("Ex-Dividend", _d(exd)))
        div = cal.get("Dividend Date")
        if div:
            rows.append(("Dividend Pay", _d(div)))
        ls = info.get("lastSplitDate")
        if ls and info.get("lastSplitFactor"):
            try:
                from datetime import datetime
                rows.append(("Last Split", f"{info['lastSplitFactor']} on "
                                            f"{datetime.fromtimestamp(ls).strftime('%b %d, %Y')}"))
            except Exception:
                pass

        rows = [(k, v) for k, v in rows if v]
        if not rows:
            return f"No upcoming calendar events found for {ticker.upper()}."

        w     = 18
        lines = [f"Calendar — {ticker.upper()}", "Forward-looking catalysts", ""]
        for label, val in rows:
            lines.append(f"  {label:<{w}} {val}")
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch calendar for {ticker}: {e}"
