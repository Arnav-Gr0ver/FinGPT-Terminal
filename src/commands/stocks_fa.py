"""Stocks › Fundamentals command handler."""

from src.display import print_error, print_panel
from src.context import ctx


def _resolve(args: str) -> str | None:
    if args:
        sym = args.strip().upper().split()[0]
        ctx.set_ticker(sym)
        return sym
    return ctx.get_ticker()


def handle(cmd: str, args: str):
    ticker = _resolve(args)
    if not ticker:
        print_error(f"Usage: {cmd} <ticker>  e.g. {cmd} AAPL")
        return

    if cmd == "income":
        from src.data.equities import get_income
        print_panel(f"[white]{get_income(ticker)}[/]", title=f"{ticker}  ›  Income Statement")
    elif cmd == "balance":
        from src.data.equities import get_balance
        print_panel(f"[white]{get_balance(ticker)}[/]", title=f"{ticker}  ›  Balance Sheet")
    elif cmd == "ratios":
        from src.data.equities import get_ratios
        print_panel(f"[white]{get_ratios(ticker)}[/]", title=f"{ticker}  ›  Key Ratios")
    elif cmd == "earnings":
        from src.data.equities import get_earnings
        print_panel(f"[white]{get_earnings(ticker)}[/]", title=f"{ticker}  ›  Earnings History")
    elif cmd == "short":
        from src.data.equities import get_short_interest
        print_panel(f"[white]{get_short_interest(ticker)}[/]", title=f"{ticker}  ›  Short Interest")
    else:
        print_error(f"Unknown fundamentals command '{cmd}'.")
