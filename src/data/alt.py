"""Alternative data — Fear & Greed (alternative.me), Polymarket prediction markets."""

import requests
from datetime import datetime

HEADERS = {"User-Agent": "FinGPT-Terminal/0.1.0"}


def get_fear_greed() -> str:
    """Crypto fear & greed index — last 7 days from alternative.me."""
    try:
        r    = requests.get("https://api.alternative.me/fng/?limit=7", headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])

        if not data:
            return "No fear & greed data available."

        def _bar(val: int) -> str:
            w   = 20
            bar = "█" * int(val / 100 * w)
            return f"{bar:<{w}}"

        def _label_color(classification: str) -> str:
            c = classification.lower()
            if "extreme fear" in c:
                return "⚡ Extreme Fear"
            if "fear" in c:
                return "▼ Fear"
            if "extreme greed" in c:
                return "🔥 Extreme Greed"
            if "greed" in c:
                return "▲ Greed"
            return "  Neutral"

        lines = [
            "Crypto Fear & Greed Index  (0 = Extreme Fear, 100 = Extreme Greed)",
            "Source: alternative.me",
            "",
            f"  {'Date':<14} {'Index':>6}   {'Bar':<22} Classification",
            "  " + "─" * 60,
        ]

        for entry in reversed(data):
            val   = int(entry.get("value", 0))
            ts    = int(entry.get("timestamp", 0))
            cls   = entry.get("value_classification", "")
            date  = datetime.fromtimestamp(ts).strftime("%b %d, %Y")
            bar   = _bar(val)
            label = _label_color(cls)
            lines.append(f"  {date:<14} {val:>6}   {bar}  {label}")

        # Highlight today
        today_val = int(data[0].get("value", 0))
        today_cls = data[0].get("value_classification", "")
        lines += [
            "",
            f"  Current reading: {today_val} — {today_cls}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch fear & greed data: {e}"


def get_prediction_markets(topic: str = "") -> str:
    """Polymarket — top active markets by volume via Gamma API."""
    try:
        params = {
            "active":    "true",
            "closed":    "false",
            "limit":     100,
            "order":     "volume",
            "ascending": "false",
        }
        r = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params=params,
            headers=HEADERS,
            timeout=12,
        )
        r.raise_for_status()
        markets = r.json()

        if not markets:
            return "No active prediction markets available."

        # Filter by topic keyword
        if topic:
            kw       = topic.lower()
            filtered = [m for m in markets if kw in (m.get("question") or "").lower()]
            if filtered:
                markets = filtered

        # Sort by volume and take top 15
        markets.sort(
            key=lambda m: float(m.get("volume") or m.get("volumeNum") or 0),
            reverse=True,
        )
        markets = markets[:15]

        lines = [
            f"Polymarket — Active Prediction Markets{' (' + topic.title() + ')' if topic else ''}",
            "Source: Polymarket Gamma API",
            "",
            f"  {'Question':<44} {'Yes':>5} {'No':>5} {'Volume':>10}",
            "  " + "─" * 70,
        ]

        for m in markets:
            question  = (m.get("question") or "")[:43]
            volume    = float(m.get("volume") or m.get("volumeNum") or 0)
            outcomes  = m.get("outcomes") or "[]"
            prices    = m.get("outcomePrices") or "[]"

            # Parse JSON strings if needed
            if isinstance(outcomes, str):
                import json
                try:
                    outcomes = json.loads(outcomes)
                    prices   = json.loads(prices) if isinstance(prices, str) else prices
                except Exception:
                    outcomes, prices = [], []

            yes_price = no_price = None
            for i, o in enumerate(outcomes):
                if isinstance(o, str) and o.lower() == "yes" and i < len(prices):
                    try:
                        yes_price = float(prices[i])
                    except Exception:
                        pass
                elif isinstance(o, str) and o.lower() == "no" and i < len(prices):
                    try:
                        no_price = float(prices[i])
                    except Exception:
                        pass

            yes_s = f"{yes_price*100:.0f}%" if yes_price is not None else "N/A"
            no_s  = f"{no_price*100:.0f}%"  if no_price  is not None else "N/A"
            vol_s = (f"${volume/1e6:.1f}M" if volume >= 1e6
                     else f"${volume/1e3:.0f}K" if volume >= 1000
                     else f"${volume:.0f}")

            lines.append(f"  {question:<44} {yes_s:>5} {no_s:>5} {vol_s:>10}")

        lines += ["", "  Yes/No prices = implied probability of each outcome."]
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch prediction markets: {e}"


def get_politics() -> str:
    """PredictIt — live odds on US political markets (elections, nominations, control
    of Congress). Source: PredictIt public market data (no key)."""
    try:
        markets = requests.get("https://www.predictit.org/api/marketdata/all/",
                               headers=HEADERS, timeout=15).json().get("markets", [])
    except Exception as e:
        return f"Could not fetch PredictIt markets: {e}"
    if not markets:
        return "No PredictIt markets available."

    out = [
        "PredictIt — US Political Markets",
        "Source: PredictIt · price = implied probability (¢ = %)",
        "",
    ]
    shown = 0
    for m in markets[:14]:
        contracts = m.get("contracts") or []
        if not contracts:
            continue
        top = max(contracts, key=lambda c: c.get("lastTradePrice") or 0)
        price = top.get("lastTradePrice")
        if price is None:
            continue
        q = (m.get("name") or "")[:50]
        lead = (top.get("name") or "Yes")[:18]
        out.append(f"  {q}")
        out.append(f"      ↳ {lead:<18} {price*100:.0f}%")
        shown += 1
        if shown >= 10:
            break
    if shown == 0:
        return "No priced PredictIt markets right now."
    return "\n".join(out)


def get_forecasts(topic: str = "") -> str:
    """Manifold — community probability forecasts on any question. Source: Manifold
    Markets (no key). An optional topic filters by keyword."""
    try:
        if topic:
            # No sort override → Manifold ranks by relevance to the term.
            markets = requests.get("https://api.manifold.markets/v0/search-markets",
                                   params={"term": topic, "filter": "open", "limit": 15},
                                   headers=HEADERS, timeout=15).json()
        else:
            markets = requests.get("https://api.manifold.markets/v0/markets",
                                   params={"limit": 60}, headers=HEADERS, timeout=15).json()
            markets = [m for m in markets if not m.get("isResolved")]
            markets.sort(key=lambda m: m.get("volume") or 0, reverse=True)
    except Exception as e:
        return f"Could not fetch forecasts: {e}"
    if not markets:
        return f"No Manifold markets found{' for ' + topic if topic else ''}."

    out = [
        "Manifold — Community Forecasts" + (f"  ›  {topic.title()}" if topic else ""),
        "Source: Manifold Markets · probability + volume",
        "",
        f"  {'Prob':>5}  {'Volume':>9}  Question",
        "  " + "─" * 60,
    ]
    for m in markets[:14]:
        prob = m.get("probability")
        if prob is None:
            continue
        vol = m.get("volume") or 0
        vol_s = f"M${vol/1000:.0f}k" if vol >= 1000 else f"M${vol:.0f}"
        q = (m.get("question") or "").replace("\n", " ")[:46]
        out.append(f"  {prob*100:>4.0f}%  {vol_s:>9}  {q}")
    return "\n".join(out)


def get_vix() -> str:
    """CBOE VIX — equity fear gauge via yfinance."""
    try:
        import yfinance as yf
        from datetime import datetime, timedelta

        t    = yf.Ticker("^VIX")
        fi   = t.fast_info
        vix  = round(fi.last_price, 2)
        hi52 = round(fi.year_high, 2)
        lo52 = round(fi.year_low,  2)

        hist    = t.history(period="1mo")
        vix_30d = round(float(hist["Close"].iloc[0]),  2) if len(hist) >= 20 else None
        trend   = round(vix - vix_30d, 2)              if vix_30d else None
        trend_s = (f"+{trend}" if trend >= 0 else str(trend)) if trend is not None else "N/A"
        arrow   = "▲" if (trend or 0) >= 0 else "▼"

        if vix < 15:
            regime, signal = "Low Volatility", "Markets are calm. Complacency risk."
        elif vix < 20:
            regime, signal = "Normal",         "Typical market conditions."
        elif vix < 30:
            regime, signal = "Elevated",       "Uncertainty rising. Caution warranted."
        elif vix < 40:
            regime, signal = "High",           "Fear dominant. Historically near-term opportunity."
        else:
            regime, signal = "Extreme Fear",   "Panic conditions. Major dislocation."

        pct52 = int((vix - lo52) / max(hi52 - lo52, 0.01) * 20)
        bar   = "█" * pct52 + "░" * (20 - pct52)

        lines = [
            "CBOE VIX — Equity Volatility / Fear Gauge",
            "Source: CBOE via Yahoo Finance",
            "",
            f"  Current VIX      {vix:.2f}",
            f"  30-Day Change    {trend_s}  {arrow}",
            f"  52W Range        {lo52:.2f} – {hi52:.2f}",
            f"  [{bar}]  {int(pct52 / 20 * 100)}th pct of 52W range",
            "",
            f"  Regime    {regime}",
            f"  Signal    {signal}",
            "",
            "  VIX interpretation:",
            "    < 15   Low volatility / complacency",
            "    15–20  Normal / orderly markets",
            "    20–30  Elevated uncertainty",
            "    30–40  High fear",
            "    > 40   Extreme dislocation (2008, Mar 2020)",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch VIX data: {e}"
