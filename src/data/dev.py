"""Developer-activity & reference data (free, no key).

GitHub public search (no key, 60 req/hr) as a software-momentum signal, and the
Wikipedia REST summary used to enrich company/asset profiles."""

from src.data.http import get_json

_SUFFIXES = (" corporation", " corp", " incorporated", " inc", " company",
             " co", " ltd", " plc", " holdings", " group", " sa", " ag")


def _clean(name: str) -> str:
    n = (name or "").strip().rstrip(".,")
    low = n.lower()
    for s in _SUFFIXES:
        if low.endswith(s):
            return n[: len(n) - len(s)].strip()
    return n


def github_activity(name: str, n: int = 10) -> str:
    """Most-starred public repositories matching the subject — open-source
    footprint and how actively it's maintained. Source: GitHub Search API."""
    q = _clean(name)
    try:
        j = get_json("https://api.github.com/search/repositories", params={
            "q": q, "sort": "stars", "order": "desc", "per_page": n,
        }, timeout=15, headers={"Accept": "application/vnd.github+json"})
    except Exception as e:
        return f"Could not fetch GitHub activity: {e}"

    items = j.get("items") or []
    if not items:
        return f"No public GitHub repositories found for '{q}'."

    out = [
        f"GitHub — Top Repositories for '{q}'",
        f"Source: GitHub · {j.get('total_count', 0):,} repos match",
        "",
        f"  {'Stars':>8}  {'Lang':<12}{'Updated':<11}Repository",
        "  " + "─" * 60,
    ]
    for r in items[:n]:
        stars = r.get("stargazers_count") or 0
        star_s = f"{stars/1000:.1f}k" if stars >= 1000 else str(stars)
        lang = (r.get("language") or "—")[:11]
        pushed = (r.get("pushed_at") or "")[:10]
        repo = (r.get("full_name") or "")[:30]
        out.append(f"  {star_s:>8}  {lang:<12}{pushed:<11}{repo}")
    out += ["", "  'Updated' is the last push — stale dates mean low activity."]
    return "\n".join(out)


def stack_overflow(name: str) -> str:
    """Stack Overflow tag activity for a technology/company — a developer-mindshare
    proxy. Source: Stack Exchange API."""
    tag = _clean(name).lower().split()[0]
    try:
        info = get_json("https://api.stackexchange.com/2.3/tags/{}/info".format(tag),
                        params={"site": "stackoverflow"}, timeout=12)
        items = info.get("items") or []
    except Exception as e:
        return f"Could not fetch Stack Overflow data: {e}"
    if not items:
        return f"No Stack Overflow tag '{tag}' found."
    t = items[0]
    try:
        recent = get_json(
            f"https://api.stackexchange.com/2.3/questions",
            params={"site": "stackoverflow", "tagged": tag, "sort": "creation",
                    "order": "desc", "pagesize": 1, "filter": "total"}, timeout=12)
        # 'total' filter returns {'total': N}
    except Exception:
        recent = {}
    return "\n".join([
        f"Stack Overflow — '{tag}'",
        "Source: Stack Exchange API",
        "",
        f"  {'Tagged questions':<22} {t.get('count', 0):,}",
        f"  {'Recently active':<22} {'yes' if t.get('count') else '—'}",
        "",
        "  Tag question volume is a rough developer-mindshare gauge.",
    ])


def web_archive(domain: str) -> str:
    """Wayback Machine coverage for a company's website — first and latest captured
    snapshots. Source: Internet Archive."""
    domain = (domain or "").replace("https://", "").replace("http://", "").strip("/").split("/")[0]
    if not domain:
        return "No website to look up."
    try:
        first = get_json("http://archive.org/wayback/available",
                         params={"url": domain, "timestamp": "19960101"}, timeout=12)
        last = get_json("http://archive.org/wayback/available",
                        params={"url": domain}, timeout=12)
    except Exception as e:
        return f"Could not fetch web archive: {e}"

    def snap(j):
        s = (j.get("archived_snapshots") or {}).get("closest") or {}
        return s.get("timestamp"), s.get("url")

    ft, fu = snap(first)
    lt, lu = snap(last)
    if not lt:
        return f"No Wayback Machine snapshots found for {domain}."

    def fmt(ts):
        return f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if ts and len(ts) >= 8 else "—"
    return "\n".join([
        f"Web Archive — {domain}",
        "Source: Internet Archive (Wayback Machine)",
        "",
        f"  {'First captured':<18} {fmt(ft)}",
        f"  {'Latest capture':<18} {fmt(lt)}",
        f"  {'Snapshot':<18} {lu or '—'}",
    ])


def wikidata_facts(name: str) -> str | None:
    """Structured company facts (inception, employees, CEO, HQ) from Wikidata.
    Returns a formatted block or None. Source: Wikidata."""
    try:
        search = get_json("https://www.wikidata.org/w/api.php", params={
            "action": "wbsearchentities", "search": name, "language": "en",
            "type": "item", "limit": 1, "format": "json"}, timeout=10)
        hits = search.get("search") or []
        if not hits:
            return None
        qid = hits[0]["id"]
        ent = get_json("https://www.wikidata.org/w/api.php", params={
            "action": "wbgetentities", "ids": qid, "props": "claims", "format": "json"}, timeout=10)
        claims = ent.get("entities", {}).get(qid, {}).get("claims", {})
    except Exception:
        return None

    def amount(pid):
        try:
            v = claims[pid][0]["mainsnak"]["datavalue"]["value"]
            return v.get("amount", "").lstrip("+") if isinstance(v, dict) else v
        except Exception:
            return None

    def year(pid):
        try:
            t = claims[pid][0]["mainsnak"]["datavalue"]["value"]["time"]
            return t[1:5]
        except Exception:
            return None
    rows = []
    if year("P571"):
        rows.append(f"  {'Founded':<14} {year('P571')}")
    if amount("P1128"):
        try:
            rows.append(f"  {'Employees':<14} {int(float(amount('P1128'))):,}")
        except (TypeError, ValueError):
            pass
    if amount("P2139"):
        try:
            rows.append(f"  {'Revenue':<14} ${float(amount('P2139'))/1e9:,.1f}B")
        except (TypeError, ValueError):
            pass
    return "\n".join(rows) if rows else None


def wikipedia_summary(title: str) -> str | None:
    """One-paragraph plain-text summary from Wikipedia, or None."""
    if not title:
        return None
    try:
        j = get_json(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
            timeout=10)
    except Exception:
        return None
    extract = (j.get("extract") or "").strip()
    if not extract or j.get("type") == "disambiguation":
        return None
    return extract
