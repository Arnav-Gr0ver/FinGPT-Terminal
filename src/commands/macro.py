"""Macro section commands."""

from src.display import print_error, print_table, console


def handle(cmd: str, args: str):
    if cmd == "rates":
        _rates()
    elif cmd == "yield":
        _yield()
    elif cmd in ("inflation", "gdp", "calendar", "fear"):
        raise NotImplementedError
    else:
        print_error(f"Unknown macro command '{cmd}'.")


def _rates():
    rows = [
        ["Federal Reserve",       "5.25–5.50%", "USD", "United States"],
        ["European Central Bank", "4.50%",       "EUR", "Eurozone"],
        ["Bank of England",       "5.25%",       "GBP", "United Kingdom"],
        ["Bank of Japan",         "0.10%",       "JPY", "Japan"],
        ["Swiss National Bank",   "1.75%",       "CHF", "Switzerland"],
        ["Bank of Canada",        "5.00%",       "CAD", "Canada"],
        ["Reserve Bank of Aus.",  "4.35%",       "AUD", "Australia"],
    ]
    print_table(
        "FinGPT Terminal  ›  Macro  ›  Central Bank Rates",
        ["Central Bank", "Rate", "Currency", "Region"],
        rows,
    )
    console.print("  [#555555]Rates are approximate. Source: public central bank data.[/]\n")


def _yield():
    try:
        import yfinance as yf
        tenors = {"3M": "^IRX", "5Y": "^FVX", "10Y": "^TNX", "30Y": "^TYX"}
        rows   = []
        for label, sym in tenors.items():
            try:
                price = yf.Ticker(sym).fast_info.last_price
                rows.append([label, f"{price:.2f}%"])
            except Exception:
                rows.append([label, "N/A"])

        print_table(
            "FinGPT Terminal  ›  Macro  ›  US Treasury Yield Curve",
            ["Tenor", "Yield"],
            rows,
        )

    except Exception as e:
        print_error(f"Could not fetch yield curve: {e}")