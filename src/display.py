"""Display layer — all Rich UI for FinR1 Terminal."""

from datetime import datetime

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.rule import Rule
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

# Priority functions shown in the load panel — ordered by "most useful first" per kind.
_PRIORITY_FUNCS: dict[str, list[str]] = {
    "equity":     ["price", "chart", "financials", "earnings", "news", "sentiment", "pe", "revenue"],
    "etf":        ["price", "chart", "holdings", "holders", "returns", "sentiment", "news"],
    "crypto":     ["price", "chart", "cex", "funding", "governance", "dexpairs", "sentiment"],
    "index":      ["price", "chart", "returns", "cot", "constituents", "compare", "gtrends"],
    "commodity":  ["price", "chart", "cot", "supply", "weather", "solar", "returns"],
    "fx":         ["price", "chart", "carry", "cot", "bigmac", "returns", "gtrends"],
    "country":    ["gdp", "inflation", "trade", "debt", "co2", "unemployment", "market", "news"],
    "macro":      ["price", "chart", "gtrends", "trends", "risk"],
    "chain":      ["tvl", "price", "chart", "dexpairs", "governance", "gtrends"],
    "protocol":   ["fees", "price", "chart", "governance", "dexpairs", "gtrends"],
    "stablecoin": ["price", "gtrends", "trends", "risk"],
    "exchange":   ["hours", "holidays", "price", "gtrends", "trends"],
    "topic":      ["news", "gtrends", "trends", "risk", "stackoverflow"],
}

# Grouped functions per category for /help <category> — ordered by workflow.
_FUNC_GROUPS: dict[str, list[tuple[str, list[str]]]] = {
    "equity": [
        ("Price",        ["price", "chart", "returns", "stats", "seasonality"]),
        ("Compare",      ["compare", "corr", "spread"]),
        ("Fundamentals", ["financials", "earnings", "profile", "dividends", "holders", "insiders"]),
        ("Analysts",     ["analysts", "filings", "calendar", "mentions"]),
        ("Trading",      ["short", "options", "ftd", "splits", "shortvol"]),
        ("Sentiment",    ["sentiment", "buzz", "gtrends", "trends", "risk"]),
        ("Research",     ["trials", "fda", "regulations", "github", "contracts", "lobbying"]),
        ("Alternative",  ["hiring", "litigation", "campaigns", "epa", "adoption", "players"]),
        ("Reference",    ["peers", "archive", "stackoverflow", "news", "metrics"]),
        ("Session",      ["find", "hours", "watch", "export", "convert", "screen", "holidays"]),
    ],
    "etf": [
        ("Price",        ["price", "chart", "returns", "stats", "seasonality"]),
        ("Compare",      ["compare", "corr", "spread"]),
        ("Composition",  ["holdings", "holders"]),
        ("Sentiment",    ["sentiment", "buzz", "github", "shortvol", "gtrends", "trends", "risk"]),
        ("Reference",    ["peers", "news", "metrics", "stackoverflow"]),
        ("Session",      ["find", "hours", "watch", "export", "convert", "screen", "holidays"]),
    ],
    "crypto": [
        ("Market",        ["price", "chart", "returns", "stats", "seasonality"]),
        ("Compare",       ["compare", "corr", "spread"]),
        ("Cross-exchange",["cex"]),
        ("DeFi",          ["funding", "governance", "dexpairs"]),
        ("Sentiment",     ["sentiment", "buzz", "github", "cryptovol", "gtrends", "trends", "risk"]),
        ("Reference",     ["news"]),
        ("Session",       ["find", "hours", "watch", "export", "convert", "screen"]),
    ],
    "index": [
        ("Market",      ["price", "chart", "returns", "stats", "seasonality"]),
        ("Compare",     ["compare", "corr", "spread"]),
        ("Positioning", ["cot", "cotfin", "constituents"]),
        ("Signals",     ["gtrends", "trends", "risk", "news"]),
        ("Session",     ["find", "hours", "watch", "export", "convert", "screen", "holidays"]),
    ],
    "commodity": [
        ("Market",      ["price", "chart", "returns", "stats", "seasonality"]),
        ("Compare",     ["compare", "corr", "spread"]),
        ("Positioning", ["cot", "supply"]),
        ("Physical",    ["weather", "solar"]),
        ("Signals",     ["gtrends", "trends", "risk", "news"]),
        ("Session",     ["find", "hours", "watch", "export", "convert", "screen", "holidays"]),
    ],
    "fx": [
        ("Market",  ["price", "chart", "returns", "stats", "seasonality"]),
        ("Compare", ["compare", "corr", "spread"]),
        ("Macro",   ["cot", "cotfin", "carry", "bigmac"]),
        ("Signals", ["gtrends", "trends", "risk", "news"]),
        ("Session", ["find", "hours", "watch", "export", "convert", "screen", "holidays"]),
    ],
    "country": [
        ("Macro",         ["gdp", "inflation", "trade", "debt"]),
        ("Labor",         ["unemployment", "population"]),
        ("External",      ["reserves"]),
        ("Society",       ["co2", "military", "health", "corruption", "biodiversity"]),
        ("International", ["imf", "who", "profile", "market", "solar", "weather", "holidays"]),
        ("Attention",     ["gtrends", "trends", "risk", "news"]),
        ("Reference",     ["metrics"]),
        ("Session",       ["find", "hours", "watch", "export", "convert", "screen"]),
    ],
    "macro": [
        ("Data",    ["price", "chart"]),
        ("Signals", ["gtrends", "trends", "risk"]),
        ("Session", ["find", "hours", "watch", "export", "convert", "screen", "holidays"]),
    ],
    "chain": [
        ("DeFi",       ["tvl", "price", "chart", "dexpairs"]),
        ("Governance", ["governance"]),
        ("Signals",    ["gtrends", "trends", "risk"]),
        ("Session",    ["find", "hours", "watch", "export", "convert", "screen"]),
    ],
    "protocol": [
        ("DeFi",    ["fees", "price", "chart", "dexpairs", "governance"]),
        ("Signals", ["gtrends", "trends", "risk"]),
        ("Session", ["find", "hours", "watch", "export", "convert", "screen"]),
    ],
    "stablecoin": [
        ("Market",  ["price"]),
        ("Signals", ["gtrends", "trends", "risk"]),
        ("Session", ["find", "hours", "watch", "export", "convert", "screen"]),
    ],
    "exchange": [
        ("Calendar", ["price", "hours", "holidays"]),
        ("Signals",  ["gtrends", "trends", "risk"]),
        ("Session",  ["find", "watch", "export", "convert", "screen"]),
    ],
    "topic": [
        ("Research", ["price", "news", "gtrends", "trends", "risk", "stackoverflow"]),
        ("Session",  ["find", "hours", "watch", "export", "convert", "screen"]),
    ],
}

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

# Accent color per category kind.
_KIND_ACCENT = {
    "equity": "#5aa7ff", "etf": "#5aa7ff",
    "crypto": "#f4a13c", "chain": "#f4a13c", "protocol": "#f4a13c", "stablecoin": "#f4a13c",
    "macro": "#46c890", "country": "#46c890",
    "index": "#b48ead", "commodity": "#d6b656", "fx": "#4fc1c4",
    "exchange": "#9aa0a6", "topic": "#9aa0a6",
}

# Ordered list of all 13 categories for the overview panel.
_CATEGORIES = [
    ("equity",     "#5aa7ff", "∞",     "NVDA · AAPL · TSLA · GOOGL"),
    ("etf",        "#5aa7ff", "∞",     "SPY · QQQ · IWM · GLD · XLF"),
    ("crypto",     "#f4a13c", "∞",     "BTC · ETH · SOL · ADA · MATIC"),
    ("index",      "#b48ead", "21",    "SPX · NDX · VIX · FTSE · DAX · NIKKEI"),
    ("commodity",  "#d6b656", "20",    "GOLD · OIL · WHEAT · NATGAS · COPPER · BRENT"),
    ("fx",         "#4fc1c4", "16",    "EURUSD · USDJPY · DXY · GBPUSD · USDCAD"),
    ("country",    "#46c890", "50",    "US · CN · JP · DE · UK · IN · FR · BR"),
    ("macro",      "#46c890", "25",    "CPI · GDP · DGS10 · M2 · UNRATE · FEDFUNDS"),
    ("chain",      "#f4a13c", "23",    "ETHEREUM · ARBITRUM · SOLANA · BASE · OPTIMISM"),
    ("protocol",   "#f4a13c", "25",    "AAVE · UNISWAP · LIDO · CURVE · MAKER"),
    ("stablecoin", "#f4a13c", "12",    "USDT · USDC · DAI · USDS · USDE · PYUSD"),
    ("exchange",   "#9aa0a6", "14",    "NYSE · NASDAQ · LSE · JPX · TSE · HKEX"),
    ("topic",      "#9aa0a6", "∞",     "topic:lithium · topic:AI · topic:inflation"),
]


def print_banner():
    from src.data.sources import SOURCES
    from src.router import VERBS
    n_sources = len(SOURCES)
    n_funcs   = len(VERBS)
    console.print()
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
        f"[#3a3a3a]·[/]   [#6b7280]grounded, key-less financial research[/]"
    )
    console.print(
        f"  [#46c890]{n_sources}[/][#6b7280] free no-key sources[/]   [#3a3a3a]·[/]   "
        f"[#5aa7ff]{n_funcs}[/][#6b7280] functions[/]   [#3a3a3a]·[/]   "
        f"[#6b7280]v{__version__}[/]   [#3a3a3a]·[/]   "
        f"[#6b7280]type [/][#e8e8e8]/help[/]"
    )
    console.print()


def _help_all_funcs(kind: str) -> list[str]:
    """All functions for a kind: verbs + numeric field shortcuts merged."""
    from src.capabilities import functions_for
    from src.data.metrics import metric_aliases
    return sorted(set(functions_for(kind)) | set(metric_aliases(kind)))


def _help_instruments(kind: str) -> list[str]:
    """Canonical instrument tokens for a kind (empty for open-ended categories)."""
    if kind in ("equity", "etf", "crypto", "topic"):
        return []
    if kind in ("index", "commodity", "fx"):
        from src.verbs import SPECIAL_SUBJECTS
        return [s for s, v in SPECIAL_SUBJECTS.items() if v[2] == kind]
    if kind == "country":
        from src.data.worldbank import COUNTRIES
        seen, out = set(), []
        for tok, (iso, _) in COUNTRIES.items():
            if iso not in seen:
                seen.add(iso); out.append(tok)
        return out
    if kind == "chain":
        from src.data.defillama import CHAINS
        return list(CHAINS)
    if kind == "protocol":
        from src.data.defillama import PROTOCOLS
        return list(PROTOCOLS)
    if kind == "stablecoin":
        from src.data.defillama import STABLECOINS
        return list(STABLECOINS)
    if kind == "macro":
        from src.data.macro import MACRO_SERIES
        return list(MACRO_SERIES)
    if kind == "exchange":
        from src.data.calendars import EXCHANGES
        return list(EXCHANGES)
    return []


def print_load_panel(subj) -> None:
    """Compact passport card shown when any instrument is loaded."""
    accent = KIND_COLORS.get(subj.kind, C)
    priority = _PRIORITY_FUNCS.get(subj.kind, [])

    from src.capabilities import functions_for
    from src.data.metrics import metric_aliases
    valid = set(functions_for(subj.kind)) | set(metric_aliases(subj.kind))
    fns = [f for f in priority if f in valid][:8]
    total = len(valid)

    fn_line = "  ".join(f"[bold {accent}]{f}[/]" for f in fns)
    hint = f"  [#555555]→ /help {subj.kind}  ({total} total)[/]" if total > len(fns) else ""

    # Build label: name + exchange/kind tag
    name_part = f"[#9aa0a6]{subj.name}[/]  " if subj.name else ""
    tag = subj.exchange or subj.kind
    tag_line = f"{name_part}[{accent}]{tag}[/]"

    body = Text.from_markup(f"  {tag_line}\n\n  {fn_line}{hint}")
    console.print()
    console.print(Panel(
        body,
        title=f"[bold {accent}] ● {subj.symbol} [/]",
        title_align="left",
        border_style=accent,
        box=box.ROUNDED,
        padding=(0, 1),
        expand=False,
    ))
    console.print()


def _fuzzy_instrument_search(query: str) -> list[tuple[str, str, str]]:
    """Return (symbol, kind, name) for instruments whose symbol or name contains query."""
    from src.verbs import SPECIAL_SUBJECTS
    from src.data.worldbank import COUNTRIES
    from src.data.macro import MACRO_SERIES
    from src.data.defillama import CHAINS, PROTOCOLS, STABLECOINS
    from src.data.calendars import EXCHANGES

    q_up = query.upper()
    q_lo = query.lower()
    out, seen = [], set()

    def _check(sym, kind, name):
        if sym not in seen and (q_up in sym or q_lo in name.lower()):
            seen.add(sym)
            out.append((sym, kind, name))

    for sym, (_, name, kind) in SPECIAL_SUBJECTS.items():
        _check(sym, kind, name)
    for sym, (_, name) in COUNTRIES.items():
        _check(sym, "country", name)
    for sym, (_, name, _) in MACRO_SERIES.items():
        _check(sym, "macro", name)
    for sym, (_, name) in CHAINS.items():
        _check(sym, "chain", name)
    for sym, (_, name) in PROTOCOLS.items():
        _check(sym, "protocol", name)
    for sym, (_, name) in STABLECOINS.items():
        _check(sym, "stablecoin", name)
    for sym, (_, name, _) in EXCHANGES.items():
        _check(sym, "exchange", name)

    return out[:12]


def _resolve_help_kind(symbol: str) -> str | None:
    """Return the category kind for a symbol without a network call."""
    from src.verbs import SPECIAL_SUBJECTS
    from src.data.worldbank import COUNTRIES
    from src.data.defillama import CHAINS, PROTOCOLS, STABLECOINS
    from src.data.macro import MACRO_SERIES
    from src.data.calendars import EXCHANGES
    if symbol in SPECIAL_SUBJECTS:
        return SPECIAL_SUBJECTS[symbol][2]
    if symbol in COUNTRIES:
        return "country"
    if symbol in CHAINS:
        return "chain"
    if symbol in PROTOCOLS:
        return "protocol"
    if symbol in STABLECOINS:
        return "stablecoin"
    if symbol in MACRO_SERIES:
        return "macro"
    if symbol in EXCHANGES:
        return "exchange"
    from src.data.symbols import looks_like_ticker
    if looks_like_ticker(symbol):
        return "equity"
    return None



# Per-function help: (description, source)
_FUNC_HELP: dict[str, tuple[str, str]] = {
    "price":       ("Latest quote — price, change, % change, volume, day range.",
                    "Yahoo Finance · CoinGecko · Stooq"),
    "chart":       ("Price chart over a time range. Append range: chart 1y · chart 6mo · chart 5d.",
                    "Yahoo Finance · CoinGecko"),
    "metrics":     ("All available fundamental metric fields in one table.",
                    "Yahoo Finance · World Bank"),
    "financials":  ("Income statement, balance sheet, cash flow — filed with the SEC.",
                    "SEC EDGAR via Yahoo Finance"),
    "earnings":    ("Historical EPS beat/miss and next earnings date.",
                    "Yahoo Finance"),
    "profile":     ("Business description, sector, employee count, website.",
                    "Yahoo Finance · World Bank"),
    "dividends":   ("Dividend payment history and current yield.",
                    "Yahoo Finance"),
    "holders":     ("Institutional and mutual fund ownership breakdown.",
                    "Yahoo Finance"),
    "insiders":    ("Recent insider buy/sell transactions from SEC Form 4.",
                    "SEC EDGAR via Yahoo Finance"),
    "analysts":    ("Analyst price targets and buy/sell/hold consensus.",
                    "Yahoo Finance"),
    "filings":     ("Recent SEC filings — 10-K, 10-Q, 8-K with links.",
                    "SEC EDGAR"),
    "news":        ("Recent news headlines.",
                    "Google News · GDELT"),
    "calendar":    ("Upcoming earnings dates, dividend ex-dates, and analyst events.",
                    "Yahoo Finance"),
    "compare":     ("Side-by-side price comparison. Load a set first: NVDA vs AMD compare.",
                    "Yahoo Finance · CoinGecko"),
    "returns":     ("Trailing returns — 1d, 1w, 1mo, 3mo, 1y, 3y, 5y.",
                    "Yahoo Finance"),
    "stats":       ("Volatility, beta, Sharpe ratio, max drawdown.",
                    "Yahoo Finance"),
    "corr":        ("Correlation matrix across a loaded set: NVDA vs AMD corr.",
                    "Yahoo Finance"),
    "spread":      ("Price ratio of two instruments over time: NVDA vs AMD spread.",
                    "Yahoo Finance"),
    "seasonality": ("Average return by calendar month — seasonal pattern.",
                    "Yahoo Finance"),
    "holdings":    ("ETF constituents — top positions and sector weights.",
                    "Yahoo Finance"),
    "short":       ("Short interest — shares short, days-to-cover, short float %.",
                    "Yahoo Finance · FINRA"),
    "options":     ("Options chain — calls and puts with strike, expiry, IV, volume.",
                    "Yahoo Finance"),
    "ftd":         ("Fails-to-deliver — shares that failed to settle (SEC).",
                    "SEC"),
    "cot":         ("CFTC Commitment of Traders — speculative positioning.",
                    "CFTC"),
    "cotfin":      ("CFTC Traders in Financial Futures (TFF) — positioning in financial instruments.",
                    "CFTC"),
    "sentiment":   ("News sentiment score — positive/negative ratio from recent headlines.",
                    "GDELT"),
    "buzz":        ("Hacker News mentions — developer and tech community attention.",
                    "Hacker News"),
    "gtrends":     ("Google search interest over time — retail attention proxy.",
                    "Google Trends"),
    "trends":      ("Combined attention signal: Google Trends + Reddit + Hacker News.",
                    "Google Trends · Reddit"),
    "risk":        ("News risk score — geopolitical, financial, and natural disaster signals.",
                    "GDELT · USGS"),
    "governance":  ("DAO governance — active proposals and recent votes.",
                    "Snapshot.org"),
    "funding":     ("Perpetual futures funding rate — long/short positioning signal.",
                    "Hyperliquid · Deribit"),
    "cex":         ("Cross-exchange spot price comparison across major centralized exchanges.",
                    "CoinGecko"),
    "dexpairs":    ("DEX trading pairs — liquidity and volume on decentralized exchanges.",
                    "GeckoTerminal · DEX Screener"),
    "cryptovol":   ("Implied volatility (DVOL) from crypto options markets.",
                    "Deribit"),
    "tvl":         ("Total value locked — DeFi chain TVL over time.",
                    "DeFiLlama"),
    "fees":        ("Protocol revenue and fees — annualized run rate.",
                    "DeFiLlama"),
    "constituents":("Index constituent members and weights.",
                    "Wikipedia · index providers"),
    "gdp":         ("GDP level and annual growth rate.",
                    "World Bank · FRED"),
    "inflation":   ("CPI inflation — headline and core, year-over-year.",
                    "World Bank · FRED"),
    "trade":       ("Exports, imports, and trade balance.",
                    "World Bank · UN Comtrade"),
    "debt":        ("Government debt as % of GDP.",
                    "World Bank · IMF"),
    "unemployment":("Unemployment rate over time.",
                    "World Bank · ILO"),
    "population":  ("Population level, growth rate, urban/rural split.",
                    "World Bank"),
    "reserves":    ("Foreign exchange reserve levels.",
                    "World Bank"),
    "co2":         ("CO₂ emissions — total and per capita.",
                    "World Bank · Carbon Monitor"),
    "military":    ("Military expenditure as % of GDP.",
                    "SIPRI · World Bank"),
    "health":      ("Life expectancy, infant mortality, healthcare spend.",
                    "World Bank · WHO"),
    "corruption":  ("Corruption Perceptions Index and World Bank governance indicators.",
                    "Transparency International · World Bank"),
    "biodiversity":("Species occurrence records.",
                    "GBIF"),
    "imf":         ("IMF World Economic Outlook projections — GDP and inflation forecasts.",
                    "IMF"),
    "who":         ("WHO health statistics — disease burden, vaccination rates, mortality.",
                    "WHO"),
    "market":      ("Country benchmark equity index performance.",
                    "Yahoo Finance · Stooq"),
    "carry":       ("FX carry signal — interest rate differential between two currencies.",
                    "FRED · central banks"),
    "bigmac":      ("The Economist Big Mac Index — currency over/undervaluation.",
                    "The Economist"),
    "supply":      ("Commodity supply — inventories, production, stockpiles.",
                    "EIA · USDA"),
    "weather":     ("Growing-region weather — temperature and precipitation for commodity areas.",
                    "Open-Meteo · NOAA"),
    "solar":       ("NASA solar and wind resource data by region.",
                    "NASA POWER"),
    "contracts":   ("Federal government contract awards.",
                    "USAspending.gov"),
    "fda":         ("FDA recalls and enforcement actions linked to the company.",
                    "openFDA"),
    "regulations": ("Federal Register rule-making activity linked to the company.",
                    "Federal Register"),
    "github":      ("GitHub repository activity — stars, commits, contributors.",
                    "GitHub"),
    "trials":      ("Clinical trials — active studies by sponsor.",
                    "ClinicalTrials.gov"),
    "lobbying":    ("Lobbying spend and issues from Senate LDA filings.",
                    "Senate LDA"),
    "hiring":      ("Open job roles — hiring trends by department.",
                    "Greenhouse · Lever"),
    "shortvol":    ("FINRA short volume as % of total volume.",
                    "FINRA"),
    "litigation":  ("Federal court cases from CourtListener.",
                    "CourtListener"),
    "campaigns":   ("Political donation history from FEC filings.",
                    "OpenFEC"),
    "epa":         ("EPA compliance and enforcement actions.",
                    "EPA ECHO"),
    "mentions":    ("Mentions of the ticker in SEC filings.",
                    "SEC EDGAR"),
    "adoption":    ("Package download counts — developer adoption signal.",
                    "npm · PyPI · crates.io"),
    "players":     ("Steam concurrent player counts.",
                    "SteamSpy"),
    "peers":       ("Co-viewed tickers — instruments frequently viewed alongside this one.",
                    "Yahoo Finance"),
    "archive":     ("Wayback Machine snapshots — historical web presence.",
                    "Internet Archive"),
    "stackoverflow":("Stack Overflow tag activity — developer mindshare.",
                    "Stack Exchange API"),
    "splits":      ("Stock split history.",
                    "Yahoo Finance"),
    "screen":      ("Screener — find tickers by preset: screen gainers · screen value · screen tech.",
                    "Yahoo Finance"),
    "find":        ("Search instruments by name or symbol across all categories.",
                    "local index"),
    "watch":       ("Add the loaded instrument to your session watchlist, or view it.",
                    "session"),
    "hours":       ("Current market trading hours and open/closed status.",
                    "exchange calendars"),
    "holidays":    ("Market holiday calendar for the exchange.",
                    "exchange calendars"),
    "export":      ("Export session history to a Markdown file.",
                    "local"),
    "convert":     ("Currency conversion. Usage: convert 100 USD EUR.",
                    "Frankfurter"),
}

_KIND_ORDER = ["equity", "etf", "crypto", "index", "commodity", "fx",
               "country", "macro", "chain", "protocol", "stablecoin", "exchange", "topic"]


def print_help(topic: str = None):
    """
    /help                → overview (or loaded instrument's functions if one is active)
    /help <category>     → instruments in that category
    /help <function>     → what a function does and what it applies to
    /help <symbol>       → all functions for that instrument
    """
    topic = (topic or "").strip()
    if topic.lower().startswith("topic:"):
        topic = "topic"

    top_up  = topic.upper()
    top_low = topic.lower()

    _KIND_ALIAS = {
        "equity": "equity", "stock": "equity", "stocks": "equity", "equities": "equity",
        "etf": "etf", "etfs": "etf",
        "country": "country", "countries": "country",
        "crypto": "crypto", "cryptocurrency": "crypto",
        "chain": "chain", "chains": "chain",
        "protocol": "protocol", "protocols": "protocol",
        "stablecoin": "stablecoin", "stablecoins": "stablecoin",
        "index": "index", "indices": "index", "indexes": "index",
        "commodity": "commodity", "commodities": "commodity",
        "fx": "fx", "forex": "fx",
        "macro": "macro", "fred": "macro",
        "exchange": "exchange", "exchanges": "exchange",
        "topic": "topic", "topics": "topic",
    }

    # ── /help <category> → instruments in that category ─────────────────────
    if top_low in _KIND_ALIAS:
        kind        = _KIND_ALIAS[top_low]
        accent      = _KIND_ACCENT.get(kind, C)
        instruments = _help_instruments(kind)
        _OPEN = {
            "equity": ("∞",  "NVDA · AAPL · TSLA · GOOGL · MSFT · AMZN · META · JPM"),
            "etf":    ("∞",  "SPY · QQQ · IWM · GLD · XLF · ARKK · VTI · AGG"),
            "crypto": ("∞",  "BTC · ETH · SOL · ADA · MATIC · AVAX · DOT · LINK"),
            "topic":  ("∞",  'topic:lithium · topic:AI · topic:inflation · topic:"rate cuts"'),
        }
        parts: list = []
        if instruments:
            n = len(instruments)
            title_str = f"[bold {accent}] {kind}  —  {n} [/]"
            for i in range(0, len(instruments), 10):
                row = instruments[i:i+10]
                parts.append(Text.from_markup(
                    "  " + "  ·  ".join(f"[bold {accent}]{t}[/]" for t in row)))
        else:
            count, ex = _OPEN.get(kind, ("", ""))
            title_str = f"[bold {accent}] {kind}  —  {count} [/]"
            parts.append(Text.from_markup(f"  [#c0c4cc]{ex}[/]"))
        parts.append(Text(""))
        parts.append(Text.from_markup(f"  [#808080]/help <symbol>  to see functions[/]"))
        console.print()
        console.print(Panel(Group(*parts), title=title_str, title_align="left",
                            border_style=accent, box=box.ROUNDED, padding=(1, 2), expand=False))
        console.print()
        return

    # ── /help <function> → what it does, what it applies to ─────────────────
    if topic:
        from src.router import VERBS
        if top_low in VERBS or top_low in _FUNC_HELP:
            desc, source = _FUNC_HELP.get(top_low, (f"{top_low} function", ""))
            from src.capabilities import _APPLIES_ALL
            raw_kinds = _APPLIES_ALL.get(top_low, set())
            kinds = [k for k in _KIND_ORDER if k in raw_kinds]
            parts: list = [Text.from_markup(f"  [#c0c4cc]{desc}[/]")]
            if kinds:
                parts.append(Text(""))
                kind_str = "  ".join(
                    f"[bold {_KIND_ACCENT.get(k, '#9aa0a6')}]{k}[/]" for k in kinds
                )
                parts.append(Text.from_markup(f"  [#9aa0a6]applies to[/]   {kind_str}"))
            if source:
                parts.append(Text.from_markup(f"  [#9aa0a6]source    [/]   [#c0c4cc]{source}[/]"))
            console.print()
            console.print(Panel(
                Group(*parts),
                title=f"[bold {C}] {top_low} [/]",
                title_align="left", border_style=C,
                box=box.ROUNDED, padding=(1, 2), expand=False,
            ))
            console.print()
            return

    # ── /help <symbol> or context-aware (/help with instrument loaded) ────────
    if topic:
        kind = _resolve_help_kind(top_up)
        sym  = top_up
        if not kind:
            if len(topic) >= 2:
                matches = _fuzzy_instrument_search(topic)
                if matches:
                    rows_markup = []
                    for s, mtype, name in matches:
                        a = _KIND_ACCENT.get(mtype, "#9aa0a6")
                        rows_markup.append(
                            f"  [bold {a}]{s:<14}[/]  [{a}]{mtype:<12}[/]  [#c0c4cc]{name}[/]"
                        )
                    body = Text.from_markup(
                        f"  [#9aa0a6]Matching [/][white]{topic}[/]\n\n"
                        + "\n".join(rows_markup)
                        + "\n\n  [#808080]/help <symbol>  for functions  ·  /help <category>  for list[/]"
                    )
                    console.print()
                    console.print(Panel(body, title=f"[bold {C}] find: {topic} [/]",
                                        title_align="left", border_style=C,
                                        box=box.ROUNDED, padding=(1, 2), expand=False))
                    console.print()
            return
    else:
        from src.context import ctx
        if ctx.subjects:
            kind = ctx.subjects[0].kind
            sym  = ctx.subjects[0].symbol
        else:
            kind = None
            sym  = ""

    if kind:
        accent = _KIND_ACCENT.get(kind, C)
        from src.capabilities import functions_for as _ffor
        valid_set = set(_ffor(kind))
        n_fn = len(valid_set)

        desc = ""
        from src.verbs import SPECIAL_SUBJECTS
        from src.data.worldbank import COUNTRIES
        from src.data.macro import MACRO_SERIES
        if sym in SPECIAL_SUBJECTS:
            desc = SPECIAL_SUBJECTS[sym][1]
        elif sym in COUNTRIES:
            desc = COUNTRIES[sym][1]
        elif sym in MACRO_SERIES:
            desc = MACRO_SERIES[sym][1]

        parts: list = []
        if desc:
            parts.append(Text.from_markup(f"  [#c0c4cc]{desc}[/]"))
            parts.append(Text(""))

        groups = _FUNC_GROUPS.get(kind)
        if groups:
            for group_name, group_fns in groups:
                valid_fns = [f for f in group_fns if f in valid_set]
                if not valid_fns:
                    continue
                fn_str = "  ".join(f"[bold {accent}]{f}[/]" for f in valid_fns)
                parts.append(Text.from_markup(f"  [#9aa0a6]{group_name:<14}[/]  {fn_str}"))
        else:
            funcs = sorted(valid_set)
            for i in range(0, len(funcs), 8):
                row = funcs[i:i+8]
                parts.append(Text.from_markup(
                    "  " + "  ".join(f"[bold {accent}]{f}[/]" for f in row)))

        console.print()
        console.print(Panel(
            Group(*parts),
            title=f"[bold {accent}] {sym}  —  {n_fn} functions [/]",
            title_align="left", border_style=accent,
            box=box.ROUNDED, padding=(1, 2), expand=False,
        ))
        console.print()
        return

    # ── Overview (/help with nothing loaded) ─────────────────────────────────
    from src.capabilities import functions_for

    _GROUPS = [
        ("Markets",  "#5aa7ff", ["equity", "etf", "index", "commodity", "fx"]),
        ("Economy",  "#46c890", ["country", "macro"]),
        ("Crypto",   "#f4a13c", ["crypto", "chain", "protocol", "stablecoin"]),
        ("Other",    "#c0c4cc", ["exchange", "topic"]),
    ]
    cat_lookup = {c[0]: c for c in _CATEGORIES}

    cat_table = Table(box=None, show_header=False, padding=(0, 1, 0, 0))
    cat_table.add_column(no_wrap=True, min_width=10)  # group label
    cat_table.add_column(no_wrap=True, min_width=12)  # category
    cat_table.add_column(no_wrap=True, min_width=6)   # fn count
    cat_table.add_column(no_wrap=True, min_width=4)   # sym count
    cat_table.add_column(style="#9aa0a6")              # examples

    for g_idx, (group_name, group_accent, group_cats) in enumerate(_GROUPS):
        if g_idx > 0:
            cat_table.add_row("", "", "", "", "")
        for c_idx, cat_name in enumerate(group_cats):
            if cat_name not in cat_lookup:
                continue
            _, accent, sym_count, examples = cat_lookup[cat_name]
            n_fn = len(functions_for(cat_name))
            label = f"[bold {group_accent}]{group_name}[/]" if c_idx == 0 else ""
            cat_table.add_row(
                label,
                f"[bold {accent}]{cat_name}[/]",
                f"[#c0c4cc]{n_fn} fn[/]",
                f"[#9aa0a6]{sym_count}[/]",
                examples,
            )

    body = Group(
        cat_table,
        Text(""),
        Rule(style="#3a3a3a"),
        Text.from_markup(
            "  [#c0c4cc]/help <category>[/]  [#6b7280]·[/]  "
            "[#c0c4cc]/help <symbol>[/]  [#6b7280]·[/]  "
            "[#c0c4cc]/help <function>[/]  [#6b7280]·[/]  "
            "[#c0c4cc]/clear  /exit[/]"),
    )
    console.print()
    console.print(Panel(body, title=f"[bold {C}] FinR1 Terminal [/]", title_align="left",
                        border_style=C, box=box.ROUNDED, padding=(1, 2), expand=False))
    console.print()


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
