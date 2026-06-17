"""Display layer — all Rich UI for FinGPT Terminal."""

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.rule import Rule
from rich.markdown import Markdown
from rich import box

from src import __version__

THEME = Theme({
    "primary":   "bold #e05c4b",
    "secondary": "#e07060",
    "accent":    "#e08070",
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

C = "#e05c4b"

_HELP_ROWS = [
    # (group, cmd, desc)
    ("Subjects", "NVDA · apple",            "Equity ticker or company name"),
    ("Subjects", "CPI · GDP · DGS10",       "FRED macro series"),
    ("Subjects", "SPX · VIX · GOLD · OIL",  "Index, commodity & FX"),
    ("Subjects", "BTC · ETH · EURUSD",      "Crypto & currency pairs"),
    ("Verbs",    "price",                   "Quote, day's move, range"),
    ("Verbs",    "chart <range>",           "5d 1mo 3mo 6mo ytd 1y 2y 5y 10y max"),
    ("Verbs",    "financials",              "Revenue, margins, debt — trended"),
    ("Verbs",    "earnings",                "Beat/miss history + next date"),
    ("Verbs",    "profile",                 "Sector, industry, business summary"),
    ("Verbs",    "dividends",               "Dividend history + yield"),
    ("Verbs",    "holders · insiders",      "Ownership · SEC Form 4 trades"),
    ("Verbs",    "analysts",                "Price targets + consensus"),
    ("Verbs",    "filings",                 "Recent 10-K / 10-Q / 8-K"),
    ("Verbs",    "news",                    "Latest headlines (openable links)"),
    ("Verbs",    "calendar",                "Earnings, ex-div, splits ahead"),
    ("Verbs",    "compare <peer> [peer]",   "Side-by-side, up to 4 subjects"),
    ("Verbs",    "screen [name]",           "Find tickers — gainers, value, tech… (bare = list)"),
    ("Verbs",    "watch",                   "Your watchlist; with a subject, add/remove it"),
    ("Chaining", "price compare AMD chart 1y","Verbs compose left to right"),
    ("ai",       "ask [N|all] \"<q>\"",      "Fin-R1 over session data (N outputs back)"),
    ("System",   "help · clear · login · exit","Menu · clear · keys · quit"),
]


def print_banner():
    console.print()
    console.print(Text(BANNER, style=f"bold {C}"))
    console.print()
    console.print(
        f"  [#555555]v{__version__}[/]  [dim]•[/]  "
        f"[#555555]Type [/][white]help[/][#555555] to see all commands[/]"
    )
    console.print()


def print_help():
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), show_edge=False)
    table.add_column(style="#555555",    width=16)
    table.add_column(style=f"bold {C}", width=28)
    table.add_column(style="#e8e8e8")

    current_group = None
    for group, cmd, desc in _HELP_ROWS:
        if group != current_group:
            if current_group is not None:
                table.add_row("", "", "")
            table.add_row(f"[bold #e8e8e8]{group}[/]", "", "")
            current_group = group
        table.add_row("", cmd, desc)

    console.print()
    console.print(Panel(
        table,
        title=f"[bold {C}] FinGPT Terminal — subject, then verbs [/]",
        border_style=C,
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print(
        f"  [#555555]Load a subject, then act on it. Type a new ticker anytime to "
        f"switch. Names work too — [/][white]apple[/][#555555], [/][white]nvidia[/][#555555].[/]\n"
    )


def print_agent_step(tool: str, args: dict):
    """Dim, transparent line showing exactly which connector the agent is pulling."""
    detail = " ".join(f"{v}" for v in args.values() if str(v).strip())
    label  = f"{tool} {detail}".strip()
    console.print(f"  [#555555]↳ pulling[/] [#e07060]{label}[/]")


def print_agent_answer(text: str):
    """Render the agent's grounded answer as timestamped markdown."""
    ts = datetime.now().strftime("%H:%M:%S")
    console.print(Panel(
        Markdown(text or "(no answer)"),
        title=f"[bold {C}] Fin-R1 [/]",
        subtitle=f"[#333333] {ts} [/]",
        border_style=C,
        box=box.ROUNDED,
        padding=(1, 2),
    ))


def print_usage(stats):
    """Compact status line after an `ai` call: tokens used + context window fill."""
    from src.context import MODEL
    last  = stats.last_total
    pct   = stats.context_pct
    win_k = MODEL["context"] / 1000
    bar_w = 16
    fill  = int(pct / 100 * bar_w)
    bar   = "█" * fill + "░" * (bar_w - fill)
    color = "#00c853" if pct < 60 else "#ffab00" if pct < 85 else "#ff1744"
    console.print(
        f"  [#555555]Fin-R1[/] [#777777]·[/] "
        f"[#555555]{stats.last_prompt_tokens:,} in + {stats.last_completion_tokens:,} out "
        f"= {last:,} tok[/]  [{color}]{bar}[/] [#555555]{pct:.0f}% of {win_k:.0f}k ctx[/]  "
        f"[#777777]·[/] [#555555]{stats.ai_calls} call(s), {stats.total_tokens:,} tok this session[/]\n"
    )


def print_panel(content, title: str = "", border: str = C):
    ts = datetime.now().strftime("%H:%M:%S")
    console.print(Panel(
        content,
        title=f"[bold {C}] {title} [/]" if title else "",
        subtitle=f"[#333333] {ts} [/]",
        border_style=border,
        box=box.ROUNDED,
        padding=(1, 2),
    ))


def print_table(title: str, columns: list, rows: list):
    table = Table(
        title=f" {title} ",
        box=box.SIMPLE_HEAD,
        border_style=C,
        header_style=f"bold {C}",
        title_style=f"bold {C}",
        show_lines=False,
        padding=(0, 2),
    )
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
