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
