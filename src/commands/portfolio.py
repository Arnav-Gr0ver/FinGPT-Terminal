"""Portfolio section commands."""

import json
from pathlib import Path
from src.display import print_error, print_table, print_warning, print_success, console

PORTFOLIO_FILE = Path.home() / ".fingpt" / "portfolio.json"


def _load() -> list[dict]:
    if not PORTFOLIO_FILE.exists():
        return []
    with open(PORTFOLIO_FILE) as f:
        return json.load(f)


def _save(positions: list[dict]):
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(positions, f, indent=2)


def handle(cmd: str, args: str):
    if cmd == "show":
        _show()
    elif cmd == "add":
        _add(args)
    elif cmd == "remove":
        _remove(args)
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
    ticker, shares, cost = parts[0].upper(), float(parts[1]), float(parts[2])
    positions = _load()
    positions.append({"ticker": ticker, "shares": shares, "cost": cost})
    _save(positions)
    print_success(f"Added {shares} shares of {ticker} at ${cost:.2f}")


def _remove(args: str):
    if not args:
        print_error("Usage: remove <ticker>")
        return
    ticker    = args.upper().strip()
    positions = [p for p in _load() if p["ticker"] != ticker]
    _save(positions)
    print_success(f"Removed {ticker} from portfolio.")


def _show():
    positions = _load()
    if not positions:
        print_warning("Portfolio is empty. Use 'add' to add positions.")
        return
    rows = [[p["ticker"], str(p["shares"]), f"${p['cost']:.2f}"] for p in positions]
    print_table(
        "FinGPT Terminal  >  Portfolio  >  Positions",
        ["Ticker", "Shares", "Cost Basis"],
        rows,
    )


def _pnl():
    positions = _load()
    if not positions:
        print_warning("Portfolio is empty.")
        return
    try:
        import yfinance as yf
        rows       = []
        total_cost = 0.0
        total_val  = 0.0

        for p in positions:
            try:
                price = yf.Ticker(p["ticker"]).fast_info.last_price
                cost  = p["cost"] * p["shares"]
                val   = price     * p["shares"]
                pnl   = val - cost
                pct   = (pnl / cost) * 100
                sign  = "+" if pnl >= 0 else ""
                total_cost += cost
                total_val  += val
                rows.append([
                    p["ticker"],
                    str(p["shares"]),
                    f"${p['cost']:.2f}",
                    f"${price:.2f}",
                    f"{sign}${pnl:.2f}",
                    f"{sign}{pct:.2f}%",
                ])
            except Exception:
                rows.append([p["ticker"], str(p["shares"]),
                             f"${p['cost']:.2f}", "N/A", "N/A", "N/A"])

        print_table(
            "FinGPT Terminal  >  Portfolio  >  P&L",
            ["Ticker", "Shares", "Cost", "Price", "P&L", "Return"],
            rows,
        )

        total_pnl = total_val - total_cost
        sign      = "+" if total_pnl >= 0 else ""
        color     = "#00c853" if total_pnl >= 0 else "#ff1744"
        console.print(
            f"  [bold]Total[/]  "
            f"Cost [white]${total_cost:,.2f}[/]  "
            f"Value [white]${total_val:,.2f}[/]  "
            f"P&L [{color}]{sign}${total_pnl:,.2f}[/]\n"
        )

    except Exception as e:
        print_error(f"Could not fetch prices: {e}")


def _alloc():
    positions = _load()
    if not positions:
        print_warning("Portfolio is empty.")
        return
    try:
        import yfinance as yf
        vals  = {}
        total = 0.0
        for p in positions:
            try:
                price             = yf.Ticker(p["ticker"]).fast_info.last_price
                val               = price * p["shares"]
                vals[p["ticker"]] = val
                total            += val
            except Exception:
                vals[p["ticker"]] = 0.0

        rows = [
            [t, f"${v:,.2f}", f"{(v / total * 100):.1f}%" if total else "N/A"]
            for t, v in sorted(vals.items(), key=lambda x: x[1], reverse=True)
        ]
        print_table(
            "FinGPT Terminal  >  Portfolio  >  Allocation",
            ["Ticker", "Market Value", "Weight"],
            rows,
        )

    except Exception as e:
        print_error(f"Could not compute allocation: {e}")