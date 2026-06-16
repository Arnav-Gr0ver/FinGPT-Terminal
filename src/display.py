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
    "primary":   "bold #00d4aa",
    "secondary": "#0066ff",
    "accent":    "#ff6b35",
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
    console.print(Text(BANNER, style="bold #00d4aa"))
    console.print()
    console.print(
        f"  [#555555]FinGPT Terminal[/]  [dim]•[/]  [#555555]v{__version__}[/]  "
        f"[dim]•[/]  [#555555]Type [/][white]menu[/][#555555] to explore or [/][white]help[/][#555555] for commands[/]"
    )
    console.print()


def print_home():
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), show_edge=False)
    table.add_column(style="bold #00d4aa", width=14)
    table.add_column(style="#555555")
    for cmd, desc in [
        ("stocks",    "Equities — prices, fundamentals, technicals, screener"),
        ("crypto",    "Cryptocurrency — prices, on-chain, DeFi"),
        ("macro",     "Macroeconomics — rates, inflation, GDP, central banks"),
        ("forex",     "Foreign exchange — pairs, rates, carry"),
        ("etf",       "ETFs — flows, holdings, performance"),
        ("news",      "News and sentiment across all asset classes"),
        ("portfolio", "Portfolio tracking, P&L, risk metrics"),
        ("ai",        "AI analyst — ask questions, get analysis"),
    ]:
        table.add_row(cmd, desc)
    console.print(Panel(table, title="[bold #00d4aa] FinGPT Terminal [/]",
                        border_style="#0066ff", box=box.ROUNDED, padding=(1, 1)))


def print_menu(title: str, items: list[tuple[str, str]]):
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), show_edge=False)
    table.add_column(style="bold #00d4aa", width=18)
    table.add_column(style="#555555")
    for cmd, desc in items:
        table.add_row(cmd, desc)
    console.print(Panel(table, title=f"[bold #00d4aa] {title} [/]",
                        border_style="#0066ff", box=box.ROUNDED, padding=(1, 1)))


def print_panel(content, title: str = "", border: str = "#0066ff"):
    console.print(Panel(content, title=f"[bold #00d4aa] {title} [/]" if title else "",
                        border_style=border, box=box.ROUNDED, padding=(1, 2)))


def print_table(title: str, columns: list[str], rows: list[list]):
    table = Table(title=f" {title} ", box=box.SIMPLE_HEAD, border_style="#0066ff",
                  header_style="bold #00d4aa", title_style="bold #00d4aa",
                  show_lines=False, padding=(0, 1))
    for col in columns:
        table.add_column(col, style="#e8e8e8")
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def print_rule(label: str = ""):
    console.print(Rule(label, style="#333333"))


def print_error(message: str):
    console.print(f"\n  [bold #ff1744]error[/]  [#555555]{message}[/]\n")


def print_success(message: str):
    console.print(f"\n  [bold #00c853]✓[/]  [#e8e8e8]{message}[/]\n")


def print_warning(message: str):
    console.print(f"\n  [bold #ffab00]![/]  [#e8e8e8]{message}[/]\n")


def print_info(message: str):
    console.print(f"  [#555555]{message}[/]")