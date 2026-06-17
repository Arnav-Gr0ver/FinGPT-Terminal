"""Portfolio section command handler."""

import json
from pathlib import Path
from src.display import print_error, print_panel, print_warning, print_success

PORTFOLIO_FILE = Path.home() / ".fingpt" / "portfolio.json"


def _load() -> list:
    if not PORTFOLIO_FILE.exists():
        return []
    with open(PORTFOLIO_FILE) as f:
        return json.load(f)


def _save(positions: list):
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(positions, f, indent=2)


def handle(cmd: str, args: str):
    if cmd == "add":
        _add(args)
    elif cmd == "remove":
        _remove(args)
    elif cmd == "show":
        _show()
    elif cmd == "pnl":
        _pnl()
    elif cmd == "alloc":
        _alloc()
    elif cmd == "risk":
        raise NotImplementedError
    else:
        print_error(f"Unknown portfolio command '{cmd}'.")


def _add(args: str):
    parts = args.split()
    if len(parts) < 3:
        print_error("Usage: add <ticker> <shares> <cost_basis>  e.g. add AAPL 10 150.00")
        return
    ticker = parts[0].upper()
    try:
        shares = float(parts[1])
        cost   = float(parts[2])
    except ValueError:
        print_error("Shares and cost must be numbers.  e.g. add AAPL 10 150.00")
        return
    if shares <= 0 or cost < 0:
        print_error("Shares must be positive and cost cannot be negative.")
        return
    pos    = _load()
    pos.append({"ticker": ticker, "shares": shares, "cost": cost})
    _save(pos)
    print_success(f"Added {shares} shares of {ticker} at ${cost:.2f}")


def _remove(args: str):
    if not args:
        print_error("Usage: remove <ticker>  e.g. remove AAPL")
        return
    ticker = args.upper().strip()
    _save([p for p in _load() if p["ticker"] != ticker])
    print_success(f"Removed {ticker} from portfolio.")


def _show():
    pos = _load()
    if not pos:
        print_warning("Portfolio is empty. Use 'add' to add positions.")
        return
    lines = ["Portfolio Positions",
             f"  {'Ticker':<8} {'Shares':>10} {'Cost Basis':>12}"]
    for p in pos:
        lines.append(f"  {p['ticker']:<8} {p['shares']:>10} ${p['cost']:>10.2f}")
    print_panel("[white]" + "\n".join(lines) + "[/]", title="My Portfolio")


def pnl_text() -> str:
    """Portfolio P&L as a plain-text block (shared by the `pnl` command and the AI agent)."""
    pos = _load()
    if not pos:
        return "Portfolio is empty. Use 'add <ticker> <shares> <cost>' to add positions."
    import yfinance as yf
    lines      = ["Portfolio P&L",
                  f"  {'Ticker':<8} {'Shares':>8} {'Cost':>10} {'Price':>10} {'P&L':>12} {'Return':>8}"]
    total_cost = 0.0
    total_val  = 0.0
    for p in pos:
        try:
            price = yf.Ticker(p["ticker"]).fast_info.last_price
            cost  = p["cost"] * p["shares"]
            val   = price * p["shares"]
            pnl   = val - cost
            pct   = pnl / cost * 100 if cost else 0
            sign  = "+" if pnl >= 0 else ""
            total_cost += cost
            total_val  += val
            lines.append(
                f"  {p['ticker']:<8} {p['shares']:>8} "
                f"${p['cost']:>8.2f} ${price:>8.2f} "
                f"{sign}${pnl:>9.2f} {sign}{pct:.1f}%"
            )
        except Exception:
            lines.append(f"  {p['ticker']:<8} {p['shares']:>8} ${p['cost']:>8.2f}  N/A")
    total_pnl = total_val - total_cost
    sign      = "+" if total_pnl >= 0 else ""
    lines.append(f"\n  Total Cost: ${total_cost:,.2f}  Value: ${total_val:,.2f}  P&L: {sign}${total_pnl:,.2f}")
    return "\n".join(lines)


def _pnl():
    pos = _load()
    if not pos:
        print_warning("Portfolio is empty.")
        return
    try:
        print_panel("[white]" + pnl_text() + "[/]", title="Portfolio P&L")
    except Exception as e:
        print_error(f"Could not fetch prices: {e}")


def _alloc():
    pos = _load()
    if not pos:
        print_warning("Portfolio is empty.")
        return
    try:
        import yfinance as yf
        vals  = {}
        total = 0.0
        for p in pos:
            try:
                price             = yf.Ticker(p["ticker"]).fast_info.last_price
                val               = price * p["shares"]
                vals[p["ticker"]] = val
                total            += val
            except Exception:
                vals[p["ticker"]] = 0.0
        lines = ["Portfolio Allocation",
                 f"  {'Ticker':<8} {'Market Value':>14} {'Weight':>8}"]
        for t, v in sorted(vals.items(), key=lambda x: x[1], reverse=True):
            wt = f"{v/total*100:.1f}%" if total else "N/A"
            lines.append(f"  {t:<8} ${v:>12,.2f} {wt:>8}")
        lines.append(f"\n  Total: ${total:,.2f}")
        print_panel("[white]" + "\n".join(lines) + "[/]", title="Portfolio Allocation")
    except Exception as e:
        print_error(f"Could not compute allocation: {e}")