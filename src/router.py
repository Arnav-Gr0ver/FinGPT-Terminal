"""Router — the grammar engine.

One rule: subject, then verbs. The router loads a subject (an equity ticker, a
crypto symbol, or a FRED macro series) and runs a chain of verbs against it.
Verbs compose left to right against the loaded subject:

    NVDA                         load a subject
    price                        one verb
    price compare AMD chart 1y   a chain — compare injects a peer downstream

`ask` is the one paid verb; everything else is free.
"""

import shlex

from src.context import ctx
from src.display import print_error, print_help, console
from src import verbs

# Verb name → renderer. chart / compare / ai are special-cased (they take args).
ZERO_ARG = {
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
    "watch":      verbs.v_watch,
}
# chart / compare / ask / screen take arguments and are handled specially.
VERBS = set(ZERO_ARG) | {"chart", "compare", "ask", "screen"}


def route(raw: str):
    raw = raw.strip()
    if not raw:
        return

    low = raw.lower()
    if low in ("exit", "quit", "q"):
        raise SystemExit(0)
    if low == "clear":
        console.clear()
        return
    if low in ("help", "h", "?"):
        print_help()
        return
    if low == "login":
        from src.auth import run_login
        run_login()
        return

    try:
        tokens = shlex.split(raw)
    except ValueError:
        tokens = raw.split()

    steps = _parse(tokens)
    if steps is None:
        return
    _execute(steps)


# ── parse: tokens → ordered (verb, arg) steps ────────────────────────────────

def _parse(tokens: list[str]):
    steps = []
    i = 0
    # A leading non-verb token is a subject to load (or switch to).
    while i < len(tokens):
        tok = tokens[i]
        low = tok.lower()

        if low not in VERBS:
            # The leading token is always a subject to load (ticker, macro, or a
            # company/asset name). Mid-chain, only a ticker/macro shape switches
            # subjects — a stray word there is an error, not a name lookup.
            if i == 0 or verbs.is_subject_token(tok):
                steps.append(("__load", tok))
                i += 1
                continue
            from rich.markup import escape
            hint = "type a ticker (NVDA), a macro series (CPI), or a verb."
            print_error(f"Don't recognize '{escape(tok)}' — {hint}")
            return None

        i += 1
        if low == "chart":
            rng = None
            if i < len(tokens) and verbs.normalize_range(tokens[i]):
                rng = tokens[i]
                i += 1
            steps.append(("chart", rng))
        elif low == "compare":
            peers = []
            while i < len(tokens) and tokens[i].lower() not in VERBS:
                peers.append(tokens[i])
                i += 1
            steps.append(("compare", peers))
        elif low == "screen":
            sname = None
            if i < len(tokens) and tokens[i].lower() not in VERBS:
                sname = tokens[i]
                i += 1
            steps.append(("screen", sname))
        elif low == "ask":
            # Optional leading count controls how much session history Fin-R1
            # sees: `ask 5 "..."` = last 5 outputs, `ask all "..."` = everything,
            # bare `ask "..."` = the most recent output only.
            hist = "1"
            if i < len(tokens) and (tokens[i].isdigit() or tokens[i].lower() == "all"):
                hist = tokens[i].lower()
                i += 1
            question = " ".join(tokens[i:])
            i = len(tokens)
            steps.append(("ask", (hist, question)))
        else:
            steps.append((low, None))
    return steps


# ── execute: run the chain, mutating the active subject set ───────────────────

def _execute(steps):
    active = [ctx.subject] if ctx.loaded else []
    prev_verb = None

    for name, arg in steps:
        if name == "__load":
            subj = verbs.load_subject(arg)
            if subj is None:
                return
            active = [subj]
            prev_verb = None
            continue

        # `screen` finds subjects rather than acting on one — no load needed.
        if name == "screen":
            verbs.v_screen(arg)
            prev_verb = name
            continue
        # `watch` also works with nothing loaded (bare = list).
        if not active and name != "watch":
            print_error("Load a subject first — type a ticker like [white]NVDA[/] "
                        "or a series like [white]CPI[/].")
            return

        if name == "compare":
            peers = [verbs.peer_subject(p) for p in arg]
            peers = [p for p in peers if p]
            if not peers:
                print_error("compare needs a peer — e.g. [white]compare AMD[/].")
                return
            active = active + peers
            verbs.v_compare(active)
        elif name == "chart":
            verbs.v_chart(active, arg, prev_verb)
        elif name == "ask":
            _ask(arg, active)
        else:
            ZERO_ARG[name](active)

        prev_verb = name


def _ask(arg, active):
    """The `ask` verb (the ai layer, Fin-R1). Reasons over the data already shown
    this session — the user picks how much via the count: `ask`, `ask 5 …`,
    `ask all …`."""
    hist, question = arg
    if not question:
        print_error('ask needs a question — e.g. ask "is the margin dip structural?"\n'
                    '  Add session context: ask 5 "…" (last 5) or ask all "…".')
        return
    # Make sure the agent shares the active primary subject.
    if active:
        ctx.set_subject(active[0])
    context_block = ctx.history_context(hist)
    query = (context_block + "\n\nQUESTION: " + question) if context_block else question
    from src.agent import run_agent
    run_agent(query, ctx, deep=False)
