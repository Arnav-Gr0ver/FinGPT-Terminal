"""Crypto section commands."""

from src.display import print_error, print_table, console

_symbol: str | None = None


def handle(cmd: str, args: str):
    global _symbol

    if cmd == "load":
        if not args:
            print_error("Usage: load <symbol>  e.g. load BTC")
            return
        _symbol = args.upper().strip()
        console.print(f"\n  [bold #00d4aa]Loaded[/]  [white]{_symbol}[/]\n")

    elif cmd == "quote":
        if not _symbol:
            print_error("No symbol loaded. Run: load <symbol>  e.g. load BTC")
            return
        _quote(_symbol)

    elif cmd == "top":
        _top()

    elif cmd in ("chart", "news"):
        raise NotImplementedError

    else:
        print_error(f"Unknown crypto command '{cmd}'.")


def _quote(symbol: str):
    try:
        import yfinance as yf
        info  = yf.Ticker(f"{symbol}-USD").fast_info
        price = info.last_price
        prev  = info.previous_close
        chg   = price - prev
        pct   = (chg / prev) * 100 if prev else 0
        color = "#00c853" if chg >= 0 else "#ff1744"
        sign  = "+" if chg >= 0 else ""

        console.print()
        console.print(
            f"  [bold white]{symbol}/USD[/]  "
            f"[bold #e8e8e8]{price:,.2f}[/]  "
            f"[{color}]{sign}{chg:.2f}  ({sign}{pct:.2f}%)[/]"
        )
        console.print()

    except Exception as e:
        print_error(f"Could not fetch {symbol}: {e}")


def _top():
    try:
        import yfinance as yf
        symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE"]
        rows    = []
        for sym in symbols:
            try:
                info  = yf.Ticker(f"{sym}-USD").fast_info
                price = info.last_price
                prev  = info.previous_close
                pct   = ((price - prev) / prev * 100) if prev else 0
                sign  = "+" if pct >= 0 else ""
                rows.append([sym, f"{price:,.2f}", f"{sign}{pct:.2f}%"])
            except Exception:
                rows.append([sym, "N/A", "N/A"])

        print_table(
            "FinGPT Terminal  ›  Crypto  ›  Top by Market Cap",
            ["Symbol", "Price (USD)", "24h Change"],
            rows,
        )

    except Exception as e:
        print_error(f"Could not fetch crypto data: {e}")