"""Router — the grammar engine.

One rule: a TARGET, then a pipeline of FUNCTIONS.

    NVDA                  load a target
    NVDA vs AMD           load a SET of targets ( vs / & / , combine )
    price chart 1y        run functions against whatever's loaded
    NVDA vs AMD chart 1y  set-aware functions (chart, compare, corr…) use all

A bare ticker mid-line switches the target; `vs`/`&`/`,` adds one. Per-target
functions (price, financials, news…) run once for each loaded target; set-aware
functions run once over the whole set. `/ask` is the one paid function.
"""

import shlex

from src.context import ctx
from src.display import print_error, print_help, console
from src import verbs

CONNECTORS = {"vs", "versus", "&", "and"}

# Per-subject verbs: run once per loaded subject.
EACH = {
    "price":      verbs.v_price,
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
    "sentiment":  verbs.v_sentiment,
    "seasonality": verbs.v_seasonality,
    "holdings":   verbs.v_holdings,
    "gdp":        verbs.v_gdp,
    "inflation":  verbs.v_inflation,
    "trade":      verbs.v_trade,
    "debt":       verbs.v_debt,
    "tvl":        verbs.v_tvl,
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

# Subject-independent verbs: run with nothing (or anything) loaded.
GLOBAL = {
    "watch":     verbs.v_watch,
    "hours":     verbs.v_hours,
    "export":    verbs.v_export,
    "yields":    verbs.v_yields,
    "fear":      verbs.v_fear,
    "dominance": verbs.v_dominance,
    "coins":     verbs.v_coins,
    "sectors":   verbs.v_sectors,
}

# Functions that take their own arguments (handled in _parse / _execute).
ARG_VERBS = {"chart", "compare", "screen", "convert"}

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
    if low in ("/help", "/h", "/?"):
        print_help(); return
    if low == "/login":
        from src.auth import run_login; run_login(); return

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

        # `/ask` — the one in-chain system command (slash required).
        if low in ("/ask", "/ai"):
            i += 1
            hist = "1"
            if i < len(tokens) and (tokens[i].isdigit() or tokens[i].lower() == "all"):
                hist = tokens[i].lower(); i += 1
            question = " ".join(tokens[i:]); i = len(tokens)
            steps.append(("ask", (hist, question)))
            continue

        if low in CONNECTORS:
            i += 1
            if i >= len(tokens):
                print_error("Add a subject after [white]vs[/] — e.g. [white]NVDA vs AMD[/].")
                return None
            steps.append(("__add", tokens[i]))
            i += 1
            continue

        if low not in VERBS:
            if i == 0 or verbs.is_subject_token(tok):
                steps.append(("__load", tok))
                i += 1
                continue
            from rich.markup import escape
            print_error(f"Don't recognize '{escape(tok)}' — type a ticker (NVDA), a "
                        f"macro series (CPI), a country (US), or a function.")
            return None

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
        else:
            steps.append((low, None))
    return steps


# ── execute ───────────────────────────────────────────────────────────────────

def _execute(steps):
    active = list(ctx.subjects)
    prev_verb = None

    for name, arg in steps:
        if name == "__load":
            subj = verbs.load_subject(arg)
            if subj is None:
                return
            active = [subj]
            ctx.set_subjects(active)
            prev_verb = None
            continue
        if name == "__add":
            subj = verbs.load_subject(arg)
            if subj is None:
                return
            if subj.symbol not in [s.symbol for s in active]:
                active.append(subj)
            ctx.set_subjects(active)
            prev_verb = None
            continue

        # subject-independent verbs run regardless of what's loaded
        if name == "screen":
            verbs.v_screen(arg); prev_verb = name; continue
        if name == "convert":
            verbs.v_convert(arg); prev_verb = name; continue
        if name in GLOBAL:
            GLOBAL[name](active); prev_verb = name; continue

        if not active:
            print_error("Load a subject first — type a ticker like [white]NVDA[/], "
                        "a series like [white]CPI[/], or a country like [white]US[/].")
            return

        if name == "compare":
            for p in arg:
                s = verbs.peer_subject(p)
                if s and s.symbol not in [x.symbol for x in active]:
                    active.append(s)
            ctx.set_subjects(active)
            verbs.v_compare(active)
        elif name == "chart":
            verbs.v_chart(active, arg, prev_verb)
        elif name == "ask":
            _ask(arg, active)
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


def _ask(arg, active):
    """The `/ask` function (the ai layer, Fin-R1). Reasons over the data already shown
    this session — the user picks how much via the count: `ask`, `ask 5 …`,
    `ask all …`."""
    hist, question = arg
    if not question:
        print_error('/ask needs a question — e.g. /ask "is the margin dip structural?"\n'
                    '  Add session context: /ask 5 "…" (last 5) or /ask all "…".')
        return
    if active:
        ctx.set_subjects(active)        # the model shares the whole loaded set
    context_block = ctx.history_context(hist)
    query = (context_block + "\n\nQUESTION: " + question) if context_block else question
    from src.agent import run_agent
    run_agent(query, ctx, deep=False)
