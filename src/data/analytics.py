"""Analytics — computed metrics over price history (returns, vol, corr, spread).

These power the utility verbs. Everything is derived from daily closes pulled via
yfinance; nothing here hits a new network source of its own.
"""

import math
import yfinance as yf

_PERIOD_FOR = {"returns": "3y", "stats": "1y", "corr": "1y", "spread": "2y", "seasonality": "max"}


def _closes(yf_symbol: str, period: str = "2y"):
    try:
        df = yf.Ticker(yf_symbol).history(period=period)
        s  = df["Close"].dropna()
        return s if len(s) else None
    except Exception:
        return None


def _pct(a, b):
    return (a / b - 1) * 100 if b else None


def returns_table(items: list[tuple[str, str]]) -> str:
    """items: [(label, yf_symbol)]. Trailing returns over standard windows."""
    import pandas as pd
    windows = [("1D", 1), ("1W", 5), ("1M", 21), ("3M", 63), ("YTD", None),
               ("1Y", 252), ("3Y", 756)]
    rows = {}
    for label, sym in items:
        s = _closes(sym, "3y")
        if s is None or len(s) < 2:
            rows[label] = None
            continue
        last = float(s.iloc[-1])
        vals = {}
        for name, n in windows:
            if name == "YTD":
                yr = s.index[-1].year
                ytd = s[s.index.year == yr]
                vals[name] = _pct(last, float(ytd.iloc[0])) if len(ytd) else None
            else:
                vals[name] = _pct(last, float(s.iloc[-1 - n])) if len(s) > n else None
        rows[label] = vals

    lw = max((len(l) for l, _ in items), default=6)
    head = f"  {'':<{lw}}" + "".join(f"{w:>8}" for w, _ in windows)
    out  = ["Trailing Returns", "", head, "  " + "─" * (lw + 8 * len(windows))]
    for label, _ in items:
        v = rows[label]
        if v is None:
            out.append(f"  {label:<{lw}}" + "       —" * len(windows))
            continue
        cells = "".join((f"{v[w]:>+7.1f}%" if v[w] is not None else f"{'—':>8}") for w, _ in windows)
        out.append(f"  {label:<{lw}}{cells}")
    return "\n".join(out)


def stats_table(items: list[tuple[str, str]], period: str = "1y") -> str:
    """Annualized vol, max drawdown, Sharpe (rf≈0), beta vs S&P 500."""
    spx = _closes("^GSPC", period)
    spx_ret = spx.pct_change().dropna() if spx is not None else None

    lw = max((len(l) for l, _ in items), default=6)
    head = f"  {'':<{lw}} {'Vol(ann)':>10} {'MaxDD':>9} {'Sharpe':>8} {'Beta':>7}"
    out  = [f"Risk & Return Stats  ({period})", "", head, "  " + "─" * (lw + 36)]
    for label, sym in items:
        s = _closes(sym, period)
        if s is None or len(s) < 20:
            out.append(f"  {label:<{lw}} {'—':>10} {'—':>9} {'—':>8} {'—':>7}"); continue
        ret = s.pct_change().dropna()
        vol = ret.std() * math.sqrt(252) * 100
        # max drawdown
        roll = s.cummax()
        dd   = ((s / roll - 1).min()) * 100
        sharpe = (ret.mean() / ret.std() * math.sqrt(252)) if ret.std() else 0
        beta = "—"
        if spx_ret is not None:
            j = ret.to_frame("a").join(spx_ret.to_frame("m"), how="inner").dropna()
            if len(j) > 10 and j["m"].var():
                beta = f"{j['a'].cov(j['m']) / j['m'].var():.2f}"
        out.append(f"  {label:<{lw}} {vol:>9.1f}% {dd:>8.1f}% {sharpe:>8.2f} {beta:>7}")
    return "\n".join(out)


def corr_matrix(items: list[tuple[str, str]], period: str = "1y") -> str:
    import pandas as pd
    series = {}
    for label, sym in items:
        s = _closes(sym, period)
        if s is not None and len(s) > 20:
            series[label] = s.pct_change()
    if len(series) < 2:
        return "Need at least two priced subjects with history for a correlation matrix."
    df = pd.DataFrame(series).dropna()
    corr = df.corr()
    labels = list(corr.columns)
    lw = max(len(l) for l in labels)
    head = f"  {'':<{lw}}" + "".join(f"{l:>8}" for l in labels)
    out  = [f"Return Correlation  ({period})", "", head, "  " + "─" * (lw + 8 * len(labels))]
    for r in labels:
        cells = "".join(f"{corr.loc[r, c]:>8.2f}" for c in labels)
        out.append(f"  {r:<{lw}}{cells}")
    return "\n".join(out)


def spread_series(a: tuple[str, str], b: tuple[str, str], period: str = "2y"):
    """Ratio series A/B aligned on dates → (label, values) for charting."""
    import pandas as pd
    sa, sb = _closes(a[1], period), _closes(b[1], period)
    if sa is None or sb is None:
        return None
    j = pd.DataFrame({"a": sa, "b": sb}).dropna()
    if j.empty:
        return None
    ratio = (j["a"] / j["b"]).tolist()
    return (f"{a[0]}/{b[0]}", ratio)


def seasonality(label: str, yf_symbol: str) -> str:
    """Average return by calendar month over all available history."""
    import pandas as pd
    s = _closes(yf_symbol, "max")
    if s is None or len(s) < 365:
        return f"Not enough history for {label} seasonality."
    monthly = s.resample("ME").last().pct_change().dropna() * 100
    by_month = monthly.groupby(monthly.index.month).mean()
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    out = [f"Seasonality — {label}", f"Average monthly return, {s.index[0].year}–{s.index[-1].year}", ""]
    for m in range(1, 13):
        v = by_month.get(m)
        if v is None:
            out.append(f"  {names[m-1]:<5} —"); continue
        bar = ("█" if v >= 0 else "▒") * min(int(abs(v) * 2), 28)
        out.append(f"  {names[m-1]:<5} {v:>+6.2f}%  {bar}")
    return "\n".join(out)
