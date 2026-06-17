"""Alternative data command handler."""

from src.display import print_error, print_panel
from src.context import ctx


def handle(cmd: str, args: str):
    if cmd == "fear":
        from src.data.alt import get_fear_greed
        print_panel(f"[white]{get_fear_greed()}[/]", title="Fear & Greed Index")

    elif cmd == "vix":
        from src.data.alt import get_vix
        print_panel(f"[white]{get_vix()}[/]", title="VIX — Equity Fear Gauge")

    elif cmd == "predict":
        topic = args or ctx.get_ticker() or ""
        from src.data.alt import get_prediction_markets
        print_panel(f"[white]{get_prediction_markets(topic)}[/]",
                    title=f"Prediction Markets{' — ' + topic if topic else ''}")

    else:
        print_error(f"Unknown alt command '{cmd}'.")
