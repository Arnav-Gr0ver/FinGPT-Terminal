"""Display layer — all Rich UI for FinR1 Terminal."""

from datetime import datetime

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.rule import Rule
from rich.markdown import Markdown
from rich.highlighter import RegexHighlighter
from rich import box

from src import __version__

THEME = Theme({
    "primary":   "bold #e05c4b",
    "secondary": "#e07060",
    "accent":    "#e08070",
    "muted":     "#6b7280",
    "success":   "#2ecc71",
    "warning":   "#ffab00",
    "danger":    "#ff5c6c",
    "white":     "#e8e8e8",
    "dim":       "#444444",
    # Auto-highlight styles applied to every panel body.
    "fin.money":  "#59b6ec",
    "fin.pos":    "bold #2ecc71",
    "fin.neg":    "bold #ff5c6c",
    "fin.header": "bold #d8b66a",
    "fin.source": "#6b7280",
    "fin.date":   "#6b7280",
    "fin.year":   "#6b7280",
})

console = Console(theme=THEME)


class _FinHighlighter(RegexHighlighter):
    """Auto-colors numbers/deltas/money/dates so every panel reads at a glance,
    without each verb having to style its own output."""
    base_style = "fin."
    highlights = [
        r"(?P<money>\$\d[\d,]*\.?\d*\s?[TBMk]?)",
        r"(?P<pos>[+▲][\s$]?\d[\d,]*\.?\d*%?)",
        r"(?P<neg>[-−▼][\s$]?\d[\d,]*\.?\d*%?)",
        r"(?P<header>\[[A-Za-z][\w &/.\-]*\])",
        r"(?P<source>Source:[^\n]*)",
        r"(?P<year>\(\d{4}\))",
        r"(?P<date>\d{4}-\d{2}-\d{2})",
    ]


_HL = _FinHighlighter()

# Per-target-kind accent colors — panels are tinted by what you've loaded.
C = "#e05c4b"
KIND_COLORS = {
    "equity": "#5aa7ff", "etf": "#5aa7ff",
    "crypto": "#f4a13c", "chain": "#f4a13c", "protocol": "#f4a13c", "stablecoin": "#f4a13c",
    "macro": "#46c890", "country": "#46c890",
    "index": "#b48ead", "commodity": "#d6b656", "fx": "#4fc1c4",
    "exchange": "#9aa0a6", "topic": "#9aa0a6",
}


def _active_accent():
    try:
        from src.context import ctx
        if ctx.subjects:
            return KIND_COLORS.get(ctx.subjects[0].kind)
    except Exception:
        pass
    return None

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
    ("AAVE · UNISWAP · USDT",     "DeFi protocol · stablecoin — DeFiLlama"),
    ("NYSE · LSE · topic:lithium","exchange calendar · any research topic"),
    ("NVDA vs AMD vs INTC",       "combine with vs / & / ,  →  a target set"),
]

_FUNCTIONS = [
    ("Price",    [("price · chart <range>",          "quote · price history"),
                  ("returns · stats · seasonality",  "trailing returns · risk · monthly")]),
    ("Compare",  [("compare · corr · spread",        "side-by-side · correlation · ratio")]),
    ("Company",  [("financials · earnings · profile","SEC 10-K figures · beat-miss · summary"),
                  ("dividends · holders · insiders",  "payouts · ownership · Form 4"),
                  ("analysts · filings · calendar",   "targets · filings · catalysts"),
                  ("short · options · sentiment",     "short int · options+IV · news tone"),
                  ("ftd · splits · contracts · buzz", "fails-to-deliver · splits · federal awards · HN"),
                  ("fda · regulations · github",      "FDA recalls · Federal Register · dev activity"),
                  ("trials · peers · gtrends",        "clinical trials · co-watched names · Google Trends"),
                  ("lobbying · hiring · shortvol",    "LDA lobby spend · open roles · FINRA short %"),
                  ("litigation · campaigns · epa",    "court cases · FEC donations · EPA compliance"),
                  ("mentions · adoption · players",   "filing mentions · pkg downloads · Steam players"),
                  ("archive · stackoverflow",         "Wayback snapshots · dev mindshare")]),
    ("Country",  [("gdp · inflation · trade · debt",  "World Bank macro"),
                  ("unemployment · population · reserves","labor force · population · FX reserves"),
                  ("co2 · military · health · corruption","emissions · defense · life exp · governance"),
                  ("imf · who · market · profile · holidays","IMF · WHO health · index · snapshot · holidays")]),
    ("Crypto/DeFi",[("tvl · holdings · supply",       "chain TVL · ETF holdings · inventories"),
                  ("governance · funding · cryptovol · fees","DAO votes · perp funding · DVOL · protocol fees"),
                  ("cex · dexpairs · exchanges · categories","cross-exchange price · DEX pairs · venues · sectors"),
                  ("btcchain · ethsupply · kfutures","BTC explorers · ETH issuance · Kraken futures OI")]),
    ("Economy",  [("industrial · mining · permits","factory output · extraction · construction"),
                  ("claims · confidence · freight","jobless claims · consumer demand · logistics"),
                  ("travel · airports · water · alerts","TSA · FAA delays · river flows · weather alerts"),
                  ("spaceweather · hurricanes · tides · gridcarbon","geomagnetic storms · cyclones · port tides · UK grid"),
                  ("volcanoes · buoys · neo · biodiversity","USGS volcanoes · NOAA buoys · near-earth objects · GBIF"),
                  ("citypermits · disease · medicare · sports","city permits · CDC surveillance · CMS hospitals · leagues"),
                  ("shortages · ecb · eurostat",      "FDA drug shortages · ECB rates/FX · euro-area stats")]),
    ("Signals",  [("trends · risk · cot · cotfin · constituents","attention · disruption · CFTC legacy+financial · members")]),
    ("Markets",  [("yields · refrates · auctions · budget","Treasury curve · SOFR · auctions · deficit"),
                  ("usdebt · stress · recession · credit","US debt · OFR stress · curve signal · bond spreads"),
                  ("carry · housing · soma · ipos",   "FX carry · Case-Shiller · Fed B/S · IPO pipeline"),
                  ("bigmac · weather · hazards · flights","PPP · weather · natural hazards · air traffic"),
                  ("sectors · indices · commodities · forex","sectors · indices · commodity & FX boards"),
                  ("predictions · forecasts · politics","Polymarket · Manifold · PredictIt"),
                  ("congress · disasters · treasuries","congress trades · FEMA · corporate BTC/ETH"),
                  ("fear · dominance · coins · trending","crypto F&G · dominance · top · trending"),
                  ("onchain · pools · dexs · hacks","BTC net · yields · DEX vol · exploits"),
                  ("chains · protocols · stablecoins","chains by TVL · protocols · stablecoins")]),
    ("Find",     [("screen [name]",                   "gainers losers value tech… (bare = list)"),
                  ("watch · hours · export · convert","watchlist · hours · session→md · FX")]),
]


def print_banner():
    console.print()
    # Two-tone gradient down the wordmark.
    shades = ["#e05c4b", "#e06a4f", "#e57a52", "#ea8a56", "#ef9a5a", "#f0a85f"]
    lines = BANNER.split("\n")
    grad = Text()
    for i, ln in enumerate(lines):
        grad.append(ln + ("\n" if i < len(lines) - 1 else ""),
                    style=f"bold {shades[min(i, len(shades) - 1)]}")
    console.print(grad)
    console.print()
    console.print(
        f"  [bold #e8e8e8]An analyst in your terminal[/]   "
        f"[#3a3a3a]·[/]   [#6b7280]grounded, key-less financial deep research[/]"
    )
    console.print(
        f"  [#46c890]126[/][#6b7280] free no-key sources[/]   [#3a3a3a]·[/]   "
        f"[#5aa7ff]144[/][#6b7280] functions[/]   [#3a3a3a]·[/]   "
        f"[#6b7280]v{__version__}[/]   [#3a3a3a]·[/]   "
        f"[#6b7280]type [/][#e8e8e8]/help[/]"
    )
    console.print()


_GROUP_COLOR = {
    "Price": "#5aa7ff", "Compare": "#5aa7ff", "Company": "#5aa7ff",
    "Country": "#46c890", "Crypto/DeFi": "#f4a13c", "Economy": "#d6b656",
    "Signals": "#b48ead", "Markets": "#46c890", "Find": "#9aa0a6",
}


def print_help(topic: str = None):
    topic = (topic or "").strip().lower()
    groups = {g.lower(): (g, rows) for g, rows in _FUNCTIONS}

    # Per-instrument help takes precedence over a same-named category (so `/help
    # country` shows the full consistent function+metric set, not the short list).
    _kinds = {"equity", "stock", "stocks", "etf", "country", "countries", "crypto",
              "chain", "protocol", "stablecoin", "index", "commodity", "fx", "forex",
              "macro", "exchange", "topic"}

    # Drill-down: `/help company`, `/help markets`, `/help targets`, `/help metrics`.
    if topic in groups and topic not in _kinds:
        g, rows = groups[topic]
        accent = _GROUP_COLOR.get(g, C)
        t = Table(box=None, show_header=False, padding=(0, 3, 0, 0))
        t.add_column(style=f"bold {accent}", no_wrap=True)
        t.add_column(style="#b4b4b4")
        for cmd, desc in rows:
            t.add_row(cmd, desc)
        console.print()
        console.print(Panel(t, title=f"[bold {accent}] {g} [/]", title_align="left",
                            border_style=accent, box=box.ROUNDED, padding=(1, 2), expand=False))
        console.print()
        return
    if topic in ("target", "targets"):
        t = Table(box=None, show_header=False, padding=(0, 3, 0, 0))
        t.add_column(style="bold #e8e8e8", no_wrap=True)
        t.add_column(style="#b4b4b4")
        for cmd, desc in _TARGETS:
            t.add_row(cmd, desc)
        console.print()
        console.print(Panel(t, title="[bold #e8e8e8] Targets — what you can load [/]",
                            title_align="left", border_style="#5aa7ff", box=box.ROUNDED,
                            padding=(1, 2), expand=False))
        console.print()
        return
    # Per-instrument help: `/help equity`, `/help country`, `/help crypto`, …
    _KIND_ALIAS = {"equity": "equity", "stock": "equity", "stocks": "equity", "etf": "etf",
                   "country": "country", "countries": "country", "crypto": "crypto",
                   "chain": "chain", "protocol": "protocol", "stablecoin": "stablecoin",
                   "index": "index", "commodity": "commodity", "fx": "fx", "forex": "fx",
                   "macro": "macro", "exchange": "exchange", "topic": "topic"}
    if topic in _KIND_ALIAS:
        from src.capabilities import functions_for
        from src.data.metrics import metric_aliases
        kind = _KIND_ALIAS[topic]
        funcs = functions_for(kind)
        ms = metric_aliases(kind)
        accent = {"equity": "#5aa7ff", "etf": "#5aa7ff", "country": "#46c890",
                  "crypto": "#f4a13c", "chain": "#f4a13c", "protocol": "#f4a13c",
                  "stablecoin": "#f4a13c", "index": "#b48ead", "commodity": "#d6b656",
                  "fx": "#4fc1c4"}.get(kind, C)
        lines = [f"  [#b4b4b4]Functions that work on every {kind} target:[/]\n",
                 "  " + "  ".join(f"[white]{f}[/]" for f in funcs)]
        if ms:
            lines += [f"\n  [#b4b4b4]Plus {len(ms)} metric fields (type any after the target):[/]\n",
                      "  " + "  ".join(f"[#9aa0a6]{m}[/]" for m in ms[:40]) + (" …" if len(ms) > 40 else "")]
        console.print()
        console.print(Panel(Text.from_markup("\n".join(lines)),
                            title=f"[bold {accent}] {kind.title()} — what you can run [/]",
                            title_align="left", border_style=accent, box=box.ROUNDED,
                            padding=(1, 2), expand=False))
        console.print()
        return
    if topic in ("board", "boards", "global"):
        from src.capabilities import BOARDS
        from src.completion import VERB_META
        t = Table(box=None, show_header=False, padding=(0, 3, 0, 0))
        t.add_column(style="bold #e8e8e8", no_wrap=True)
        t.add_column(style="#b4b4b4")
        for b in sorted(BOARDS):
            t.add_row(b, VERB_META.get(b, ""))
        console.print()
        console.print(Panel(t, title="[bold #e07060] Boards — standalone dashboards (no target) [/]",
                            title_align="left", border_style="#e07060", box=box.ROUNDED,
                            padding=(1, 2), expand=False))
        console.print()
        return
    if topic in ("metric", "metrics"):
        console.print(Panel(Text.from_markup(
            "  Every [bold #5aa7ff]equity[/] exposes ~65 fields; every [bold #46c890]country[/] ~40 indicators —\n"
            "  the same vocabulary on any target of that kind.\n\n"
            "  [white]NVDA pe revenue netmargin fcf roe[/]   [#9aa0a6]→ one combined card[/]\n"
            "  [white]NVDA metrics[/]                        [#9aa0a6]→ the full dump[/]\n"
            "  [white]INDIA growth gdppc inflation[/]        [#9aa0a6]→ same idea, any country[/]\n"
            "  [white]NVDA vs AMD pe[/]                       [#9aa0a6]→ a field across the set[/]"),
            title="[bold #d8b66a] Metrics — deep, consistent fields [/]", title_align="left",
            border_style="#d8b66a", box=box.ROUNDED, padding=(1, 2), expand=False))
        return

    # Overview.
    from src.capabilities import functions_for
    from src.data.metrics import metric_aliases
    grammar = Text.from_markup(
        "  [#9aa0a6]Load an[/] [bold #e8e8e8]INSTRUMENT[/][#9aa0a6], run[/] [bold #e8e8e8]FUNCTIONS[/] "
        "[#9aa0a6]& metric fields, left to right. Every function works[/]\n"
        "  [#9aa0a6]for[/] [bold #e8e8e8]every[/] [#9aa0a6]instrument in its category — so it's the same on[/] "
        "[white]NVDA[/] [#9aa0a6]as[/] [white]AAPL[/][#9aa0a6], [/][white]US[/] [#9aa0a6]as[/] [white]INDIA[/][#9aa0a6].[/]\n\n"
        "    [white]NVDA[/] [#9aa0a6]price financials pe revenue roe[/]     [#b4b4b4]a stock + fields[/]\n"
        "    [white]NVDA vs AMD[/] [#9aa0a6]compare corr[/]                 [#b4b4b4]a set[/]\n"
        "    [white]INDIA[/] [#9aa0a6]gdp inflation corruption metrics[/]   [#b4b4b4]any country[/]\n"
        "    [white]BTC[/] [#9aa0a6]price cex funding governance[/]         [#b4b4b4]crypto[/]\n"
        "    [white]coins[/][#9aa0a6] · [/][white]yields[/][#9aa0a6] · [/][white]auctions[/]               [#b4b4b4]standalone boards (no target)[/]"
    )
    _INSTR = [("Equity", "equity", "#5aa7ff"), ("Country", "country", "#46c890"),
              ("Crypto", "crypto", "#f4a13c"), ("Index", "index", "#b48ead"),
              ("Commodity", "commodity", "#d6b656"), ("FX", "fx", "#4fc1c4")]
    cat = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    cat.add_column(no_wrap=True)
    cat.add_column(style="#b4b4b4")
    for label, kind, color in _INSTR:
        nf = len(functions_for(kind))
        nm = len(metric_aliases(kind))
        extra = f" + {nm} fields" if nm else ""
        cat.add_row(f"[bold {color}]{label}[/]",
                    f"{nf} functions{extra}  ·  /help {kind}")

    body = Group(
        grammar, Text(""),
        Rule("[#5a5a5a]instruments — type /help <instrument> for its full, consistent set[/]", style="#5a5a5a"),
        Text(""), cat, Text(""),
        Rule(style="#5a5a5a"),
        Text.from_markup(
            "  [bold #e07060]boards[/]    [#b4b4b4]/help boards — standalone dashboards (coins, yields, auctions …)[/]\n"
            "  [bold #d8b66a]metrics[/]   [#b4b4b4]/help metrics — deep per-instrument fields[/]\n"
            "  [bold #e07060]/ask[/]      [#b4b4b4]\"question\" — Fin-R1 reasons over the panels on screen[/]\n"
            "  [#9aa0a6]system[/]    [#b4b4b4]/help targets · /clear · /login · /exit[/]"),
    )
    console.print()
    console.print(Panel(body, title=f"[bold {C}] FinR1 Terminal [/]", title_align="left",
                        subtitle="[#7a7a7a] load a TARGET · run FUNCTIONS [/]",
                        border_style=C, box=box.ROUNDED, padding=(1, 2), expand=False))
    console.print()


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


def print_panel(content, title: str = "", border: str = None, kind: str = None):
    ts = datetime.now().strftime("%H:%M")
    accent = border or KIND_COLORS.get(kind) or _active_accent() or C
    # Render markup → Text, then auto-highlight numbers/deltas/money/dates.
    if isinstance(content, str):
        body = Text.from_markup(content)
        _HL.highlight(body)
    else:
        body = content
    console.print(Panel(
        body,
        title=f"[bold {accent}] {title} [/]" if title else "",
        title_align="left",
        subtitle=f"[#3a3a3a]{ts}[/]",
        subtitle_align="right",
        border_style=accent,
        box=box.ROUNDED,
        padding=(1, 2),
        expand=False,           # size the card to its content, not the full width
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


def make_table(columns, rows, justify=None, header="#9aa0a6", show_header=True):
    """A clean, zebra-striped Rich table for boards. `columns` are (label) strings;
    `justify` an optional list of 'left'/'right' per column. Cell strings may carry
    markup (so callers can pre-color deltas)."""
    t = Table(box=box.SIMPLE_HEAD if show_header else None, show_header=show_header,
              show_edge=False, pad_edge=False, expand=False,
              header_style=f"bold {header}", border_style="#2a2a2a",
              row_styles=["", "on #161616"], padding=(0, 2, 0, 0))
    for i, col in enumerate(columns):
        t.add_column(col, justify=(justify[i] if justify else "left"), no_wrap=True)
    for row in rows:
        t.add_row(*[str(c) for c in row])
    return t


def delta(s):
    """Color a signed string/number green (+) or red (−) for a table cell."""
    txt = str(s)
    if txt.startswith(("-", "−", "▼")):
        return f"[#ff5c6c]{txt}[/]"
    if txt.startswith(("+", "▲")):
        return f"[#2ecc71]{txt}[/]"
    return txt


def print_rule(label: str = ""):
    console.print(Rule(label, style="#333333"))


def print_error(message: str):
    console.print(f"\n  [bold #ff1744]✗[/]  [#e8e8e8]{message}[/]\n")


def print_success(message: str):
    console.print(f"\n  [bold #00c853]✓[/]  [#e8e8e8]{message}[/]\n")


def print_warning(message: str):
    console.print(f"\n  [bold #ffab00]![/]  [#e8e8e8]{message}[/]\n")
