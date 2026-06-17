"""Macro section command handler."""

from src.display import print_error, print_panel


def handle(cmd: str, args: str):
    if cmd == "rates":
        from src.data.macro import get_rates
        print_panel(f"[white]{get_rates()}[/]", title="Central Bank Interest Rates")
    elif cmd == "yield":
        from src.data.macro import get_yield_curve
        print_panel(f"[white]{get_yield_curve()}[/]", title="US Treasury Yield Curve")
    elif cmd == "inflation":
        from src.data.macro import get_inflation
        print_panel(f"[white]{get_inflation()}[/]", title="US CPI — Inflation Data")
    elif cmd == "gdp":
        from src.data.macro import get_gdp
        print_panel(f"[white]{get_gdp()}[/]", title="US Real GDP Growth")
    elif cmd == "calendar":
        raise NotImplementedError
    else:
        print_error(f"Unknown macro command '{cmd}'.")