"""Gov & Insider section command handler."""

from src.display import print_error, print_panel
from src.context import ctx


def _resolve(args: str) -> str | None:
    if args:
        sym = args.strip().upper().split()[0]
        ctx.set_ticker(sym)
        return sym
    return ctx.get_ticker()


def handle(cmd: str, args: str):
    if cmd == "insider":
        ticker = _resolve(args)
        if not ticker:
            print_error("Usage: insider <ticker>  e.g. insider AAPL")
            return
        from src.data.gov import get_insider_trades
        print_panel(f"[white]{get_insider_trades(ticker)}[/]",
                    title=f"{ticker}  ›  Insider Trades (SEC Form 4)")

    elif cmd == "congress":
        ticker = _resolve(args) or ""
        from src.data.gov import get_congress_trades
        print_panel(f"[white]{get_congress_trades(ticker)}[/]",
                    title=f"Congressional Trades{' — ' + ticker if ticker else ''}")

    elif cmd == "ftd":
        ticker = _resolve(args)
        if not ticker:
            print_error("Usage: ftd <ticker>  e.g. ftd GME")
            return
        from src.data.gov import get_ftd
        print_panel(f"[white]{get_ftd(ticker)}[/]",
                    title=f"{ticker}  ›  Failure to Deliver (SEC)")

    elif cmd == "lobbying":
        raise NotImplementedError

    else:
        print_error(f"Unknown gov command '{cmd}'.")
