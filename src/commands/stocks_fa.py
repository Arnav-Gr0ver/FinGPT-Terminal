"""Stocks › Fundamental Analysis commands."""

from src.display import print_error, print_table, console


def handle(cmd: str, args: str):
    from src.commands.stocks import get_ticker
    ticker = get_ticker()
    if not ticker:
        print_error("No ticker loaded. Go back to stocks and run: load <ticker>")
        return

    if cmd == "income":
        _income(ticker)
    elif cmd == "balance":
        _balance(ticker)
    elif cmd == "ratios":
        _ratios(ticker)
    elif cmd == "earnings":
        _earnings(ticker)
    elif cmd in ("cash", "dcf"):
        raise NotImplementedError
    else:
        print_error(f"Unknown FA command '{cmd}'.")


def _income(ticker: str):
    try:
        import yfinance as yf
        df = yf.Ticker(ticker).financials
        if df is None or df.empty:
            print_error(f"No income data for {ticker}.")
            return

        metrics = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "EBITDA"]
        rows    = []
        for m in metrics:
            if m in df.index:
                row = [m] + [_fmt(df.loc[m, c]) for c in df.columns[:4]]
                rows.append(row)

        cols = ["Metric"] + [str(c.date()) for c in df.columns[:4]]
        print_table(f"FinGPT Terminal  ›  {ticker}  ›  Income Statement", cols, rows)

    except Exception as e:
        print_error(f"Could not fetch income statement: {e}")


def _balance(ticker: str):
    try:
        import yfinance as yf
        df = yf.Ticker(ticker).balance_sheet
        if df is None or df.empty:
            print_error(f"No balance sheet data for {ticker}.")
            return

        metrics = [
            "Total Assets",
            "Total Liabilities Net Minority Interest",
            "Stockholders Equity",
            "Cash And Cash Equivalents",
            "Total Debt",
            "Net Debt",
        ]
        rows = []
        for m in metrics:
            if m in df.index:
                row = [m] + [_fmt(df.loc[m, c]) for c in df.columns[:4]]
                rows.append(row)

        cols = ["Metric"] + [str(c.date()) for c in df.columns[:4]]
        print_table(f"FinGPT Terminal  ›  {ticker}  ›  Balance Sheet", cols, rows)

    except Exception as e:
        print_error(f"Could not fetch balance sheet: {e}")


def _ratios(ticker: str):
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info

        metrics = [
            ("P/E Ratio",        info.get("trailingPE")),
            ("Forward P/E",      info.get("forwardPE")),
            ("P/B Ratio",        info.get("priceToBook")),
            ("EV/EBITDA",        info.get("enterpriseToEbitda")),
            ("P/S Ratio",        info.get("priceToSalesTrailing12Months")),
            ("Gross Margin",     _pct(info.get("grossMargins"))),
            ("Operating Margin", _pct(info.get("operatingMargins"))),
            ("Net Margin",       _pct(info.get("profitMargins"))),
            ("ROE",              _pct(info.get("returnOnEquity"))),
            ("ROA",              _pct(info.get("returnOnAssets"))),
            ("Debt / Equity",    info.get("debtToEquity")),
            ("Current Ratio",    info.get("currentRatio")),
            ("Beta",             info.get("beta")),
        ]

        rows = [[k, str(v) if v is not None else "N/A"] for k, v in metrics]
        print_table(f"FinGPT Terminal  ›  {ticker}  ›  Key Ratios", ["Metric", "Value"], rows)

    except Exception as e:
        print_error(f"Could not fetch ratios: {e}")


def _earnings(ticker: str):
    try:
        import yfinance as yf
        df = yf.Ticker(ticker).earnings_dates
        if df is None or df.empty:
            print_error(f"No earnings data for {ticker}.")
            return

        rows = []
        for date, row in df.head(8).iterrows():
            rows.append([
                str(date.date()),
                str(row.get("EPS Estimate", "N/A")),
                str(row.get("Reported EPS", "N/A")),
                str(row.get("Surprise(%)", "N/A")),
            ])

        print_table(
            f"FinGPT Terminal  ›  {ticker}  ›  Earnings History",
            ["Date", "EPS Estimate", "EPS Reported", "Surprise %"],
            rows,
        )

    except Exception as e:
        print_error(f"Could not fetch earnings: {e}")


def _fmt(val) -> str:
    try:
        v = float(val)
        if abs(v) >= 1e9:
            return f"{v/1e9:.2f}B"
        if abs(v) >= 1e6:
            return f"{v/1e6:.2f}M"
        return f"{v:.2f}"
    except Exception:
        return "N/A"


def _pct(val) -> str:
    try:
        return f"{float(val) * 100:.2f}%"
    except Exception:
        return "N/A"