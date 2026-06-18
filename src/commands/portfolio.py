"""Portfolio P&L — read-only helper used by the `/ask` agent's portfolio tool."""

import json
from pathlib import Path

PORTFOLIO_FILE = Path.home() / ".fingpt" / "portfolio.json"


def _load() -> list:
    if not PORTFOLIO_FILE.exists():
        return []
    try:
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def pnl_text() -> str:
    """Portfolio P&L as a plain-text block (consumed by the AI agent)."""
    pos = _load()
    if not pos:
        return "Portfolio is empty."
    import yfinance as yf
    lines = ["Portfolio P&L",
             f"  {'Ticker':<8} {'Shares':>8} {'Cost':>10} {'Price':>10} {'P&L':>12} {'Return':>8}"]
    total_cost = total_val = 0.0
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
            lines.append(f"  {p['ticker']:<8} {p['shares']:>8} ${p['cost']:>8.2f} "
                         f"${price:>8.2f} {sign}${pnl:>9.2f} {sign}{pct:.1f}%")
        except Exception:
            lines.append(f"  {p['ticker']:<8} {p['shares']:>8} ${p['cost']:>8.2f}  N/A")
    total_pnl = total_val - total_cost
    sign = "+" if total_pnl >= 0 else ""
    lines.append(f"\n  Total Cost: ${total_cost:,.2f}  Value: ${total_val:,.2f}  "
                 f"P&L: {sign}${total_pnl:,.2f}")
    return "\n".join(lines)
