"""Public holidays — Nager.Date (free, no key).

Per-country public-holiday calendars, handy for anticipating market closures and
low-liquidity sessions. Country codes are ISO-3166 alpha-2 (matching our country
subjects)."""

from datetime import date

from src.data.http import get_json

# Friendly exchange token → (ISO MIC for exchange_calendars, display name, tz).
EXCHANGES = {
    "NYSE": ("XNYS", "New York Stock Exchange", "America/New_York"),
    "NASDAQ": ("XNAS", "Nasdaq", "America/New_York"),
    "LSE": ("XLON", "London Stock Exchange", "Europe/London"),
    "JPX": ("XTKS", "Tokyo Stock Exchange", "Asia/Tokyo"),
    "TSE": ("XTKS", "Tokyo Stock Exchange", "Asia/Tokyo"),
    "HKEX": ("XHKG", "Hong Kong Exchange", "Asia/Hong_Kong"),
    "SSE": ("XSHG", "Shanghai Stock Exchange", "Asia/Shanghai"),
    "EURONEXT": ("XPAR", "Euronext Paris", "Europe/Paris"),
    "XETRA": ("XFRA", "Deutsche Börse (Xetra)", "Europe/Berlin"),
    "TSX": ("XTSE", "Toronto Stock Exchange", "America/Toronto"),
    "ASX": ("XASX", "Australian Securities Exchange", "Australia/Sydney"),
    "BSE": ("XBOM", "Bombay Stock Exchange", "Asia/Kolkata"),
    "SIX": ("XSWX", "SIX Swiss Exchange", "Europe/Zurich"),
    "KRX": ("XKRX", "Korea Exchange", "Asia/Seoul"),
}


def resolve_exchange(token: str):
    t = token.strip()
    if t.lower().startswith("exchange:"):
        t = t.split(":", 1)[1]
    return EXCHANGES.get(t.upper())


def exchange_status(mic: str, name: str, tz: str) -> str:
    """Whether an exchange is open right now, its next session, and upcoming holidays.
    Source: exchange_calendars (offline)."""
    try:
        import exchange_calendars as xcals
        import pandas as pd
        cal = xcals.get_calendar(mic)
        now = pd.Timestamp.now(tz="UTC")
    except Exception as e:
        return f"No trading calendar for {name} ({mic}): {e}"

    try:
        is_open = cal.is_open_on_minute(now)
    except Exception:
        is_open = False
    status = "● OPEN" if is_open else "CLOSED"

    try:
        next_open = cal.next_open(now)
        next_close = cal.next_close(now)
    except Exception:
        next_open = next_close = None

    def local(ts):
        try:
            return ts.tz_convert(tz).strftime("%a %b %d, %H:%M")
        except Exception:
            return "—"

    out = [
        f"{name}  ({mic})",
        f"Source: exchange_calendars · local time zone {tz}",
        "",
        f"  {'Status now':<16} {status}",
    ]
    if not is_open and next_open is not None:
        out.append(f"  {'Next open':<16} {local(next_open)}")
    if is_open and next_close is not None:
        out.append(f"  {'Closes':<16} {local(next_close)}")

    # Upcoming holiday closures.
    try:
        import pandas as pd
        sched = cal.schedule
        future_sessions = set(sched.index[sched.index >= now.normalize().tz_localize(None)][:40].date)
        hols = []
        d = now.tz_convert(tz).date()
        from datetime import timedelta as _td
        for i in range(1, 90):
            day = d + _td(days=i)
            if day.weekday() < 5 and day not in future_sessions:
                hols.append(day)
            if len(hols) >= 5:
                break
        if hols:
            out += ["", "  Upcoming weekday closures:"]
            for h in hols:
                out.append(f"    {h.strftime('%a %b %d, %Y')}")
    except Exception:
        pass
    return "\n".join(out)


def public_holidays(iso: str = "US", name: str = "United States", n: int = 12) -> str:
    iso = (iso or "US").upper()
    year = date.today().year
    today = date.today().isoformat()
    try:
        data = get_json(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{iso}", timeout=12)
        # roll into next year so the list is always forward-looking near year-end
        nxt = get_json(f"https://date.nager.at/api/v3/PublicHolidays/{year + 1}/{iso}", timeout=12)
        data = (data or []) + (nxt or [])
    except Exception as e:
        return (f"No public-holiday calendar for {name} ({iso}): {e}\n"
                "  Nager.Date covers most countries by ISO-2 code.")

    seen, upcoming = set(), []
    for h in data:
        if (h.get("date") or "") < today:
            continue
        key = (h.get("date"), (h.get("name") or h.get("localName") or "").lower())
        if key in seen:
            continue
        seen.add(key)
        upcoming.append(h)
    upcoming.sort(key=lambda h: h.get("date", ""))
    if not upcoming:
        return f"No upcoming public holidays found for {name}."

    out = [
        f"Public Holidays — {name}",
        "Source: Nager.Date",
        "",
        f"  {'Date':<14}{'Weekday':<11}Holiday",
        "  " + "─" * 50,
    ]
    from datetime import datetime
    for h in upcoming[:n]:
        d = h.get("date", "")
        try:
            wd = datetime.strptime(d, "%Y-%m-%d").strftime("%a")
        except ValueError:
            wd = ""
        nm = (h.get("name") or h.get("localName") or "")[:32]
        out.append(f"  {d:<14}{wd:<11}{nm}")
    return "\n".join(out)
