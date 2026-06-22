"""Router — the grammar engine.

One rule: a TARGET, then a pipeline of FUNCTIONS.

    NVDA                  load a target
    NVDA vs AMD           load a SET of targets ( vs / & / , combine )
    price chart 1y        run functions against whatever's loaded
    NVDA vs AMD chart 1y  set-aware functions (chart, compare, corr…) use all

A bare ticker mid-line switches the target; `vs`/`&`/`,` adds one. Per-target
functions (price, financials, news…) run once for each loaded target; set-aware
functions run once over the whole set.
"""

import shlex

from src.context import ctx
from src.display import print_error, print_help, console
from src.capabilities import _func_applies, functions_for
from src import verbs

CONNECTORS = {"vs", "versus", "&", "and"}

# Per-subject verbs: run once per loaded subject.
EACH = {
    "price":      verbs.v_price,
    "metrics":    verbs.v_metrics,
    "financials": verbs.v_financials,
    "earnings":   verbs.v_earnings,
    "filings":    verbs.v_filings,
    "news":       verbs.v_news,
    "calendar":   verbs.v_calendar,
    "profile":    verbs.v_profile,
    "dividends":  verbs.v_dividends,
    "holders":    verbs.v_holders,
    "analysts":   verbs.v_analysts,
    "insiders":   verbs.v_insiders,
    "short":      verbs.v_short,
    "options":    verbs.v_options,
    "ftd":        verbs.v_ftd,
    "cot":        verbs.v_cot,
    "contracts":  verbs.v_contracts,
    "buzz":       verbs.v_buzz,
    "fda":        verbs.v_fda,
    "regulations": verbs.v_regulations,
    "github":     verbs.v_github,
    "trials":     verbs.v_trials,
    "peers":      verbs.v_peers,
    "lobbying":   verbs.v_lobbying,
    "hiring":     verbs.v_hiring,
    "shortvol":   verbs.v_shortvol,
    "litigation": verbs.v_litigation,
    "campaigns":  verbs.v_campaigns,
    "epa":        verbs.v_epa,
    "mentions":   verbs.v_mentions,
    "adoption":   verbs.v_adoption,
    "players":    verbs.v_players,
    "archive":    verbs.v_archive,
    "stackoverflow": verbs.v_stackoverflow,
    "governance": verbs.v_governance,
    "funding":    verbs.v_funding,
    "cex":        verbs.v_cex,
    "dexpairs":   verbs.v_dexpairs,
    "cryptovol":  verbs.v_cryptovol,
    "cotfin":     verbs.v_cotfin,
    "constituents": verbs.v_constituents,
    "carry":      verbs.v_carry,
    "weather":    verbs.v_weather,
    "solar":      verbs.v_solar,
    "gtrends":    verbs.v_gtrends,
    "sentiment":  verbs.v_sentiment,
    "splits":     verbs.v_splits,
    "seasonality": verbs.v_seasonality,
    "holdings":   verbs.v_holdings,
    "gdp":        verbs.v_gdp,
    "inflation":  verbs.v_inflation,
    "trade":      verbs.v_trade,
    "debt":       verbs.v_debt,
    "unemployment": verbs.v_unemployment,
    "population":  verbs.v_population,
    "reserves":   verbs.v_reserves,
    "biodiversity": verbs.v_biodiversity,
    "co2":        verbs.v_co2,
    "military":   verbs.v_military,
    "health":     verbs.v_health,
    "corruption": verbs.v_corruption,
    "imf":        verbs.v_imf,
    "who":        verbs.v_who,
    "market":     verbs.v_market,
    "tvl":        verbs.v_tvl,
    "fees":       verbs.v_fees,
    "supply":     verbs.v_supply,
    "trends":     verbs.v_trends,
    "risk":       verbs.v_risk,
}

# Set-aware verbs: run once over the whole active set.
SETV = {
    "returns": verbs.v_returns,
    "stats":   verbs.v_stats,
    "corr":    verbs.v_corr,
    "spread":  verbs.v_spread,
}

# Subject-independent verbs: run with nothing (or anything) loaded. Standalone
# market/economy "boards" were removed — the terminal is purely instrument →
# functions — so only session utilities and the two instrument-aware globals
# (holidays → country, bigmac → fx) remain here.
GLOBAL = {
    "watch":    verbs.v_watch,
    "hours":    verbs.v_hours,
    "export":   verbs.v_export,
    "holidays": verbs.v_holidays,
    "bigmac":   verbs.v_bigmac,
}

# Functions that take their own arguments (handled in _parse / _execute).
ARG_VERBS = {"chart", "compare", "screen", "convert", "find"}

VERBS = set(EACH) | set(SETV) | set(GLOBAL) | ARG_VERBS


def route(raw: str):
    raw = raw.strip()
    if not raw:
        return
    # System commands use a leading slash (/help, /ask, …) — but bare words still
    # work too, so a stray slash never breaks anything.
    low = raw.lower()
    # System commands REQUIRE a leading slash — bare `help`/`exit`/… do nothing special.
    if low in ("/exit", "/quit", "/q"):
        raise SystemExit(0)
    if low == "/clear":
        console.clear(); return
    if low in ("/help", "/h", "/?") or low.startswith(("/help ", "/h ")):
        parts = raw.split(None, 1)
        print_help(parts[1] if len(parts) > 1 else None); return
    try:
        tokens = shlex.split(raw)
    except ValueError:
        tokens = raw.split()
    tokens = _split_commas(tokens)

    steps = _parse(tokens)
    if steps is None:
        return
    _execute(steps)


def _split_commas(tokens: list[str]) -> list[str]:
    """Turn `SNDK,SPCX` into `SNDK vs SPCX` so commas compose a subject set."""
    out = []
    for t in tokens:
        if "," in t and t.lower() not in VERBS:
            parts = [p for p in t.split(",") if p]
            for j, p in enumerate(parts):
                if j:
                    out.append("vs")
                out.append(p)
        else:
            out.append(t)
    return out


# ── parse: tokens → ordered steps ─────────────────────────────────────────────

def _parse(tokens: list[str]):
    steps = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        low = tok.lower()

        if low in CONNECTORS:
            i += 1
            if i >= len(tokens):
                print_error("Add a subject after [white]vs[/] — e.g. [white]NVDA vs AMD[/].")
                return None
            steps.append(("__add", tokens[i]))
            i += 1
            continue

        if low not in VERBS:
            # Could be a new subject to load OR a metric on the current target —
            # resolved at execute time when we know what's loaded.
            steps.append(("__token", tok))
            i += 1
            continue

        i += 1
        if low == "chart":
            rng = None
            if i < len(tokens) and verbs.normalize_range(tokens[i]):
                rng = tokens[i]; i += 1
            steps.append(("chart", rng))
        elif low == "compare":
            peers = []
            while i < len(tokens) and tokens[i].lower() not in VERBS and tokens[i].lower() not in CONNECTORS:
                peers.append(tokens[i]); i += 1
            steps.append(("compare", peers))
        elif low == "screen":
            sname = None
            if i < len(tokens) and tokens[i].lower() not in VERBS:
                sname = tokens[i]; i += 1
            steps.append(("screen", sname))
        elif low == "convert":
            args = []
            while i < len(tokens) and tokens[i].lower() not in VERBS:
                args.append(tokens[i]); i += 1
            steps.append(("convert", args))
        elif low == "find":
            args = []
            while i < len(tokens) and tokens[i].lower() not in VERBS:
                args.append(tokens[i]); i += 1
            steps.append(("find", args))
        else:
            steps.append((low, None))
    return steps


# ── execute ───────────────────────────────────────────────────────────────────

def _execute(steps):
    active = list(ctx.subjects)
    prev_verb = None
    pending = []                                   # buffered consecutive metrics

    def flush():
        nonlocal pending
        if pending and active:
            _run_metrics(active, pending)
        pending = []

    for name, arg in steps:
        if name == "__load":
            flush()
            subj = verbs.load_subject(arg)
            if subj is None:
                return
            active = [subj]
            ctx.set_subjects(active)
            prev_verb = None
            continue
        if name == "__add":
            flush()
            subj = verbs.load_subject(arg)
            if subj is None:
                return
            if subj.symbol not in [s.symbol for s in active]:
                active.append(subj)
            ctx.set_subjects(active)
            prev_verb = None
            continue
        if name == "__token":
            # A bare token after a target: a metric on it if it fits, else a new subject.
            from src.data.metrics import is_metric
            if active and is_metric(active[0].kind, arg):
                pending.append(arg); prev_verb = "metric"; continue
            flush()
            subj = verbs.load_subject(arg)
            if subj is None:
                return
            active = [subj]; ctx.set_subjects(active); prev_verb = None
            continue

        flush()
        # subject-independent verbs run regardless of what's loaded
        if name == "screen":
            verbs.v_screen(arg); prev_verb = name; continue
        if name == "convert":
            verbs.v_convert(arg); prev_verb = name; continue
        if name == "find":
            verbs.v_find(arg); prev_verb = name; continue
        if name in GLOBAL:
            if active and not _func_applies(name, {s.kind for s in active}):
                _reject(name, active); prev_verb = name; continue
            GLOBAL[name](active); prev_verb = name; continue

        if not active:
            print_error("Load a subject first — type a ticker like [white]NVDA[/], "
                        "a series like [white]CPI[/], or a country like [white]US[/].")
            return

        # Enforce target-awareness: a function only runs if it fits the loaded kind,
        # so every target of a kind exposes exactly the same consistent set.
        if not _func_applies(name, {s.kind for s in active}):
            _reject(name, active); prev_verb = name; continue

        if name == "compare":
            for p in arg:
                s = verbs.peer_subject(p)
                if s and s.symbol not in [x.symbol for x in active]:
                    active.append(s)
            ctx.set_subjects(active)
            verbs.v_compare(active)
        elif name == "chart":
            verbs.v_chart(active, arg, prev_verb)
        elif name in SETV:
            SETV[name](active)
        else:                                   # per-subject verb
            fn = EACH[name]
            if len(active) == 1:
                fn(active)
            else:
                for s in active:
                    fn([s])

        prev_verb = name

    flush()


def _reject(name, active):
    """Explain that a function doesn't apply to the loaded target, and point to the
    consistent set that does — instead of silently running the wrong (US) data."""
    s = active[0]
    funcs = functions_for(s.kind)
    extra = ""
    if s.kind in ("equity", "etf", "country"):
        from src.data.metrics import metric_aliases
        ms = metric_aliases(s.kind)
        if ms:
            extra = f"\n  [#6b7280]+ {len(ms)} metric fields — e.g. {' · '.join(ms[:8])}[/]"
    sample = " · ".join(f"[white]{f}[/]" for f in funcs[:12])
    print_error(f"[white]{name}[/] doesn't apply to a {s.kind} target ([white]{s.symbol}[/]).\n"
                f"  Try: {sample}{' …' if len(funcs) > 12 else ''}{extra}\n"
                f"  [#6b7280]Same functions work for every {s.kind} — see /help {s.kind}.[/]")


def _run_metrics(active, aliases):
    """Render a combined metric card for each active subject that supports them."""
    from src.data.metrics import card
    from src.display import print_panel
    from src.context import ctx as _ctx
    from rich.markup import escape
    for s in active:
        res = card(s, aliases)
        if res is None:
            continue
        title, body = res
        _ctx.remember(title, body)
        print_panel(escape(body), title=title)


