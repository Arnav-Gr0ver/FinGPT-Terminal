"""Display layer — all Rich UI for FinR1 Terminal."""

from datetime import datetime

from rich.console import Console, Group
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
  ███████╗██╗███╗   ██╗██████╗  ██╗
  ██╔════╝██║████╗  ██║██╔══██╗███║
  █████╗  ██║██╔██╗ ██║██████╔╝╚██║
  ██╔══╝  ██║██║╚██╗██║██╔══██╗ ██║
  ██║     ██║██║ ╚████║██║  ██║ ██║
  ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═╝
  ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗
     ██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║
     ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║
     ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║
     ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝\
"""

C = "#e05c4b"

# Each section: (group, [(command, description)])
_TARGETS = [
    ("NVDA · apple · SPY",        "equity · company name · ETF"),
    ("CPI · GDP · DGS10",         "FRED macro series"),
    ("SPX · VIX · GOLD · EURUSD · BTC", "index · commodity · FX · crypto"),
    ("US · CHINA · country:BR",   "country — World Bank macro"),
    ("ETHEREUM · chain:arbitrum", "crypto chain — DeFiLlama TVL"),
    ("NVDA vs AMD vs INTC",       "combine with vs / & / ,  →  a target set"),
]

_FUNCTIONS = [
    ("Price",    [("price · chart <range>",          "quote · price history"),
                  ("returns · stats · seasonality",  "trailing returns · risk · monthly")]),
    ("Compare",  [("compare · corr · spread",        "side-by-side · correlation · ratio")]),
    ("Company",  [("financials · earnings · profile","SEC 10-K figures · beat-miss · summary"),
                  ("dividends · holders · insiders",  "payouts · ownership · Form 4"),
                  ("analysts · filings · calendar",   "targets · filings · catalysts"),
                  ("short · options · sentiment · splits","short int · options+IV · tone · splits")]),
    ("Country",  [("gdp · inflation · trade · debt",  "World Bank macro"),
                  ("unemployment · population",       "labor force · population")]),
    ("Chain/ETF",[("tvl · holdings · supply",         "chain TVL · ETF holdings · inventories")]),
    ("Signals",  [("trends · risk",                   "Wikipedia attention · disruption")]),
    ("Markets",  [("yields · sectors · indices",      "Treasury curve · sectors · world indices"),
                  ("commodities · forex",             "commodity board · FX board"),
                  ("fear · dominance · coins",        "crypto F&G · dominance · top coins"),
                  ("protocols · stablecoins",         "top DeFi protocols · stablecoin caps")]),
    ("Find",     [("screen [name]",                   "gainers losers value tech… (bare = list)"),
                  ("watch · hours · export · convert","watchlist · hours · session→md · FX")]),
]


def print_banner():
    console.print()
    console.print(Text(BANNER, style=f"bold {C}"))
    console.print()
    console.print(
        f"  [#555555]v{__version__}[/]  [dim]•[/]  "
        f"[#555555]Type [/][white]/help[/][#555555] to see all commands[/]"
    )
    console.print()


def print_help():
    # Grammar reminder.
    header = Text.from_markup(
        f"  [#777777]TARGET ▸ FUNCTIONS[/]   [#444444]·[/]   "
        f"[white]NVDA price chart 1y[/]   [#444444]·[/]   "
        f"[white]NVDA vs AMD compare[/]"
    )

    targets = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    targets.add_column(style=f"bold {C}", no_wrap=True, width=10)
    targets.add_column(style="bold #e8e8e8", no_wrap=True, width=36)
    targets.add_column(style="#8a8a8a")
    for i, (cmd, desc) in enumerate(_TARGETS):
        targets.add_row("TARGETS" if i == 0 else "", cmd, desc)

    funcs = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    funcs.add_column(style=f"bold {C}", no_wrap=True, width=10)
    funcs.add_column(style="bold #e8e8e8", no_wrap=True, width=36)
    funcs.add_column(style="#8a8a8a")
    for group, rows in _FUNCTIONS:
        for i, (cmd, desc) in enumerate(rows):
            funcs.add_row(group if i == 0 else "", cmd, desc)

    ai = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    ai.add_column(style=f"bold {C}", no_wrap=True, width=10)
    ai.add_column(style="bold #e8e8e8", no_wrap=True, width=36)
    ai.add_column(style="#8a8a8a")
    ai.add_row("ai · paid", "/ask [N|all] \"<q>\"", "Fin-R1 reasons over the data on screen")
    ai.add_row("system", "/help · /clear · /login · /exit", "slash commands")

    body = Group(
        header, Text(""),
        targets, Text(""),
        Rule(style="#333333"),
        funcs, Text(""),
        Rule(style="#333333"),
        ai,
    )
    console.print()
    console.print(Panel(
        body,
        title=f"[bold {C}] FinR1 Terminal [/]",
        subtitle="[#444444] load a TARGET · run FUNCTIONS [/]",
        border_style=C, box=box.ROUNDED, padding=(1, 2),
    ))
    console.print(
        f"  [#555555]Functions run left-to-right against the loaded target(s); "
        f"as you type, the bar below shows what comes next.[/]\n"
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
