"""News & sentiment — Yahoo Finance via yfinance, keyword-based scoring."""

import yfinance as yf
from datetime import datetime

_BULLISH = {
    "surge", "rally", "gain", "rise", "beat", "strong", "record", "high",
    "upgrade", "buy", "outperform", "growth", "profit", "positive",
    "bullish", "momentum", "breakout", "oversold", "opportunity", "upside",
    "accelerate", "expand", "recover", "rebound", "soar", "jump", "spike",
    "boost", "win", "lead", "innovate", "partnership", "deal", "acquisition",
}

_BEARISH = {
    "fall", "drop", "decline", "miss", "weak", "low", "downgrade", "sell",
    "crash", "warning", "risk", "concern", "loss", "negative", "bearish",
    "overbought", "correction", "headwind", "cut", "layoff", "lawsuit",
    "investigation", "fraud", "recall", "ban", "sanction", "debt",
    "default", "bankruptcy", "miss", "disappoint", "probe", "fine",
}


def _fmt_time(ts) -> str:
    """Accept Unix timestamp (int) or ISO-8601 string."""
    try:
        if isinstance(ts, str):
            # e.g. "2026-06-16T16:49:18Z"
            return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M").strftime("%b %d, %Y  %H:%M")
        return datetime.fromtimestamp(int(ts)).strftime("%b %d, %Y  %H:%M")
    except Exception:
        return str(ts)


def _normalize(item: dict) -> dict:
    """Normalize old and new yfinance news schemas to {title, publisher, time, link}."""
    # New schema: item['content']['title'], item['provider']['displayName'], item['content']['pubDate']
    content = item.get("content") or {}
    if content and content.get("title"):
        link = ((content.get("canonicalUrl") or {}).get("url")
                or (content.get("clickThroughUrl") or {}).get("url") or "")
        return {
            "title":     content.get("title", ""),
            "publisher": (item.get("provider") or {}).get("displayName", ""),
            "time":      content.get("pubDate") or content.get("displayTime") or "",
            "link":      link,
        }
    # Legacy schema: item['title'], item['publisher'], item['providerPublishTime']
    return {
        "title":     item.get("title") or item.get("headline") or "",
        "publisher": item.get("publisher") or "",
        "time":      item.get("providerPublishTime") or item.get("published") or "",
        "link":      item.get("link") or "",
    }


def get_news_feed(query: str, limit: int = 6) -> list[dict]:
    """A small, clean set of recent stories: [{title, publisher, ago, link}]."""
    items = _fetch_news(query, limit + 4)
    out = []
    seen = set()
    for item in items:
        n = _normalize(item)
        title = (n["title"] or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        out.append({
            "title":     title,
            "publisher": n["publisher"],
            "ago":       _rel_time(n["time"]) if n["time"] else "",
            "link":      n["link"],
        })
        if len(out) >= limit:
            break
    return out


def _score_headline(text: str) -> tuple[int, int]:
    words = set(text.lower().split())
    bull  = len(words & _BULLISH)
    bear  = len(words & _BEARISH)
    return bull, bear


def _fetch_news(query: str, limit: int) -> list[dict]:
    """Try yfinance Ticker.news; fall back to searching via SPY for general news."""
    try:
        t     = yf.Ticker(query.upper())
        items = t.news or []
        return items[:limit]
    except Exception:
        return []


def search_news(query: str, limit: int = 12) -> str:
    items = _fetch_news(query, limit)
    if not items:
        return f"No recent news found for '{query}'."
    return _format_news(items, f"News — {query.upper()}")


def _format_news(items: list, title: str) -> str:
    lines = [title, ""]
    for i, item in enumerate(items, 1):
        n         = _normalize(item)
        headline  = n["title"] or "(no title)"
        publisher = n["publisher"]
        time_s    = _fmt_time(n["time"]) if n["time"] else ""

        bull, bear = _score_headline(headline)
        if bull > bear:
            tag = " +"
        elif bear > bull:
            tag = " -"
        else:
            tag = "  "

        lines.append(f"  {i:>2}.{tag} {headline}")
        if publisher or time_s:
            meta = "  ".join(filter(None, [publisher, time_s]))
            lines.append(f"       [{meta}]")
        lines.append("")
    return "\n".join(lines).rstrip()


def _rel_time(ts) -> str:
    """Compact 'time ago' label (e.g. 2h, 3d) from a unix ts or ISO string."""
    try:
        if isinstance(ts, str):
            dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
        else:
            dt = datetime.utcfromtimestamp(int(ts))
        secs = (datetime.utcnow() - dt).total_seconds()
        if secs < 0:
            return ""
        if secs < 3600:
            return f"{int(secs // 60)}m"
        if secs < 86400:
            return f"{int(secs // 3600)}h"
        return f"{int(secs // 86400)}d"
    except Exception:
        return ""


def get_sentiment(query: str, limit: int = 20) -> str:
    items = _fetch_news(query, limit)
    if not items:
        return f"No headlines found for '{query}' to score."

    bull_total = bear_total = 0
    bull_items = []
    bear_items = []

    for item in items:
        headline = _normalize(item)["title"]
        b, be    = _score_headline(headline)
        bull_total += b
        bear_total += be
        if b > be:
            bull_items.append(headline)
        elif be > b:
            bear_items.append(headline)

    total = bull_total + bear_total
    if total == 0:
        verdict   = "NEUTRAL"
        bull_pct  = bear_pct = 50
    else:
        bull_pct  = int(bull_total / total * 100)
        bear_pct  = 100 - bull_pct
        if bull_pct >= 60:
            verdict = "BULLISH"
        elif bear_pct >= 60:
            verdict = "BEARISH"
        else:
            verdict = "MIXED"

    bar_w    = 30
    bull_bar = "█" * int(bull_pct / 100 * bar_w)
    bear_bar = "░" * int(bear_pct / 100 * bar_w)

    lines = [
        f"Sentiment Analysis — {query.upper()}",
        f"Based on {len(items)} recent headlines",
        "",
        f"  Verdict   {verdict}",
        "",
        f"  Bullish {bull_pct:>3}%  {bull_bar}",
        f"  Bearish {bear_pct:>3}%  {bear_bar}",
        "",
    ]

    if bull_items:
        lines.append("  Bullish signals:")
        for h in bull_items[:3]:
            lines.append(f"    + {h[:80]}")
        lines.append("")

    if bear_items:
        lines.append("  Bearish signals:")
        for h in bear_items[:3]:
            lines.append(f"    - {h[:80]}")

    lines.append("")
    lines.append("  Note: Keyword-based scoring only — no ML model.")
    return "\n".join(lines)
