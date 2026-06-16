"""Display layer — all Rich UI for FinGPT Terminal."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.rule import Rule
from rich import box

from src import __version__

THEME = Theme({
    "primary":   "bold #ff6b00",
    "secondary": "#ff8c00",
    "accent":    "#ffaa33",
    "muted":     "#555555",
    "success":   "#00c853",
    "warning":   "#ffab00",
    "danger":    "#ff1744",
    "white":     "#e8e8e8",
    "dim":       "#444444",
})

console = Console(theme=THEME)

BANNER = """\
  ███████╗██╗███╗   ██╗ ██████╗ ██████╗ ████████╗
  ██╔════╝██║████╗  ██║██╔════╝ ██╔══██╗╚══██╔══╝
  █████╗  ██║██╔██╗ ██║██║  ███╗██████╔╝   ██║
  ██╔══╝  ██║██║╚██╗██║██║   ██║██╔═══╝    ██║
  ██║     ██║██║ ╚████║╚██████╔╝██║        ██║
  ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝        ╚═╝
  ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗
     ██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║
     ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║
     ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║
     ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝\
"""


def print_banner():
    console.print()
    console.print(Text(BANNER, style="bold #ff6b00"))
    console.print()
    console.print(
        f"  [#555555]v{__version__}[/]  [dim]•[/]  "
        f"[#555555]Type [/][white]help[/][#555555] to see all commands  [/]"
        f"[dim]•[/]  [#555555]Type [/][white]/ask <question>[/][#555555] to talk to the AI[/]"
    )
    console.print()


def print_home():
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), show_edge=False)
    table.add_column(style="bold #ff6b00", width=14)
    table.add_column(style="#e8e8e8",      width=24)
    table.add_column(style="#555555")
    for cmd, label, desc in [
        ("stocks",    "Stocks & Equities",  "prices, fundamentals, charts, news"),
        ("crypto",    "Cryptocurrency",     "prices, on-chain data, DeFi"),
        ("macro",     "Macro & Economy",    "interest rates, inflation, yield curve"),
        ("forex",     "Foreign Exchange",   "currency pairs and rates"),
        ("etf",       "ETFs & Funds",       "holdings, flows, performance"),
        ("news",      "News & Sentiment",   "headlines across all markets"),
        ("portfolio", "My Portfolio",       "track positions, P&L, allocation"),
    ]:
        table.add_row(cmd, label, desc)

    console.print()
    console.print(Panel(table, title="[bold #ff6b00] FinGPT Terminal [/]",
                        border_style="#ff6b00", box=box.ROUNDED, padding=(1, 2)))
    console.print(
        "  [#555555]Type a section name to enter it  [dim]•[/]  "
        "[white]/ask <question>[/][#555555] to ask the AI  [dim]•[/]  "
        "[white]help[/][#555555] for all commands[/]\n"
    )


def print_menu(title: str, items: list[tuple[str, str, str]], tip: str = ""):
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), show_edge=False)
    table.add_column(style="bold #ff6b00", width=16)
    table.add_column(style="#e8e8e8",      width=26)
    table.add_column(style="#555555")
    for cmd, label, desc in items:
        table.add_row(cmd, label, desc)

    if tip:
        from rich.console import Group
        body = Group(table, Text(f"\n  {tip}", style="#555555"))
    else:
        body = table

    console.print()
    console.print(Panel(body, title=f"[bold #ff6b00] {title} [/]",
                        border_style="#ff6b00", box=box.ROUNDED, padding=(1, 2)))
    console.print(
        "  [#555555][white]..[/] to go back  [dim]•[/]  "
        "[white]home[/] to return to main menu  [dim]•[/]  "
        "[white]/ask <question>[/] to ask the AI[/]\n"
    )


def print_panel(content, title: str = "", border: str = "#ff6b00"):
    console.print(Panel(content, title=f"[bold #ff6b00] {title} [/]" if title else "",
                        border_style=border, box=box.ROUNDED, padding=(1, 2)))


def print_table(title: str, columns: list[str], rows: list[list]):
    table = Table(title=f" {title} ", box=box.SIMPLE_HEAD, border_style="#ff6b00",
                  header_style="bold #ff6b00", title_style="bold #ff6b00",
                  show_lines=False, padding=(0, 2))
    for col in columns:
        table.add_column(col, style="#e8e8e8")
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print()
    console.print(table)
    console.print()


def print_rule(label: str = ""):
    console.print(Rule(label, style="#333333"))


def print_error(message: str):
    console.print(f"\n  [bold #ff1744]✗[/]  [#e8e8e8]{message}[/]\n")


def print_success(message: str):
    console.print(f"\n  [bold #00c853]✓[/]  [#e8e8e8]{message}[/]\n")


def print_warning(message: str):
    console.print(f"\n  [bold #ffab00]![/]  [#e8e8e8]{message}[/]\n")


def print_info(message: str):
    console.print(f"  [#555555]{message}[/]")