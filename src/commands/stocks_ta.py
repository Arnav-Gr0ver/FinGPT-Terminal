"""Stocks › Technicals command handler."""

from src.display import print_error, print_panel
from src.context import ctx


def _resolve(args: str) -> str | None:
    if args:
        sym = args.strip().upper().split()[0]
        ctx.set_ticker(sym)
        return sym
    return ctx.get_ticker()


def handle(cmd: str, args: str):
    if cmd == "chart":
        ticker = _resolve(args)
        if not ticker:
            print_error("Usage: chart <ticker>  e.g. chart AAPL")
            return
        _chart(ticker)
    elif cmd in ("sma", "ema", "rsi", "macd"):
        raise NotImplementedError
    else:
        print_error(f"Unknown technicals command '{cmd}'.")


def _chart(ticker: str):
    from src.data.equities import get_chart_data
    from src.data.crypto import is_crypto
    # yfinance needs the -USD suffix for crypto price history.
    yf_symbol = f"{ticker}-USD" if is_crypto(ticker) else ticker
    closes = get_chart_data(yf_symbol, period="1mo")
    if not closes:
        print_error(f"No price data for {ticker}.")
        return
    hi  = max(closes)
    lo  = min(closes)
    rng = hi - lo or 1
    h   = 12
    rows = []
    for row in range(h, -1, -1):
        threshold = lo + (row / h) * rng
        line      = "".join("█" if p >= threshold else " " for p in closes)
        rows.append(f"{threshold:>9.2f} │{line}")
    w      = len(closes)
    chart  = "\n".join(rows)
    chart += f"\n{'':>10}└{'─' * w}"
    chart += f"\n{'':>11}{'◄ 1 month ago':<{w//2}}{'today ►':>{w//2}}"
    print_panel(f"[white]{chart}[/]", title=f"{ticker}  ›  Price Chart  (1 Month)")
