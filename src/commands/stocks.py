"""Stocks section commands."""

from src.display import print_error, print_panel, console

_ticker: str | None = None


def handle(cmd: str, args: str):
    global _ticker

    if cmd == "load":
        if not args:
            print_error("Usage: load <ticker>  e.g. load AAPL")
            return
        _ticker = args.upper().strip()
        console.print(f"\n  [bold #00d4aa]Loaded[/]  [white]{_ticker}[/]\n")

    elif cmd == "quote":
        if not _require_ticker():
            return
        _quote(_ticker)

    elif cmd == "chart":
        if not _require_ticker():
            return
        _chart(_ticker)

    elif cmd == "news":
        if not _require_ticker():
            return
        from src.commands.news import handle as news_handle
        news_handle("search", _ticker)

    elif cmd == "screen":
        raise NotImplementedError

    elif cmd == "similar":
        raise NotImplementedError

    else:
        print_error(f"Unknown stocks command '{cmd}'.")


def _require_ticker() -> bool:
    if not _ticker:
        print_error("No ticker loaded. Run: load <ticker>  e.g. load AAPL")
        return False
    return True


def get_ticker() -> str | None:
    """Expose loaded ticker to other command modules."""
    return _ticker


def _quote(ticker: str):
    try:
        import yfinance as yf
        info  = yf.Ticker(ticker).fast_info
        price = info.last_price
        prev  = info.previous_close
        chg   = price - prev
        pct   = (chg / prev) * 100 if prev else 0
        color = "#00c853" if chg >= 0 else "#ff1744"
        sign  = "+" if chg >= 0 else ""

        console.print()
        console.print(
            f"  [bold white]{ticker}[/]  "
            f"[bold #e8e8e8]{price:.2f}[/]  "
            f"[{color}]{sign}{chg:.2f}  ({sign}{pct:.2f}%)[/]"
        )
        console.print()

    except Exception as e:
        print_error(f"Could not fetch quote for {ticker}: {e}")


def _chart(ticker: str):
    try:
        import yfinance as yf
        hist   = yf.Ticker(ticker).history(period="1mo")
        closes = hist["Close"].tolist()

        if not closes:
            print_error(f"No price data for {ticker}.")
            return

        hi  = max(closes)
        lo  = min(closes)
        rng = hi - lo or 1
        h   = 10

        rows = []
        for row in range(h, -1, -1):
            threshold = lo + (row / h) * rng
            line      = "".join("█" if p >= threshold else " " for p in closes)
            label     = f"{threshold:>8.2f} │"
            rows.append(label + line)

        w      = len(closes)
        chart  = "\n".join(rows)
        chart += f"\n{'':>9}└{'─' * w}"
        chart += f"\n{'':>10}{'1 month':^{w}}"

        print_panel(f"[white]{chart}[/]", title=f"FinGPT Terminal  ›  {ticker}  ›  1 Month Chart")

    except Exception as e:
        print_error(f"Could not render chart: {e}")