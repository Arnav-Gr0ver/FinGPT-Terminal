"""Adoption / usage signals (free, no key).

  • Package-download counts (npm / PyPI / crates) for companies whose product is a
    developer package → adoption
  • SteamSpy player estimates for game publishers           → players
Both use small curated ticker maps and degrade gracefully when unmapped."""

from src.data.http import get_json

# Ticker → (ecosystem, package) for companies whose core product is a dev package.
PACKAGES = {
    "MDB": ("pypi", "pymongo"), "DDOG": ("pypi", "datadog"),
    "ESTC": ("pypi", "elasticsearch"), "CFLT": ("pypi", "confluent-kafka"),
    "GTLB": ("pypi", "python-gitlab"), "HCP": ("pypi", "hvac"),
    "NET": ("npm", "cloudflare"), "TWLO": ("pypi", "twilio"),
    "OKTA": ("npm", "@okta/okta-auth-js"), "SNOW": ("pypi", "snowflake-connector-python"),
    "S": ("pypi", "sentinelone"), "FROG": ("npm", "jfrog-client-js"),
    "VRCL": ("npm", "vercel"),
    "DOCN": ("docker", "library/ubuntu"), "IBM": ("docker", "ibmcom/db2"),
    "RHT": ("brew", "podman"), "HASH": ("brew", "vault"),
}

# Ticker → representative Steam appids for game publishers.
STEAM = {
    "EA": [1237970, 1506830], "TTWO": [271590, 1174180], "RBLX": [],
    "U": [], "TCEHY": [], "NTES": [], "SE": [],
}


def adoption(ticker: str, company: str = "") -> str:
    spec = PACKAGES.get(ticker.upper())
    if not spec:
        return (f"No tracked developer package for {ticker}.\n"
                "  Covered: dev-tool names (MDB, DDOG, ESTC, NET, TWLO, SNOW …).")
    eco, pkg = spec
    try:
        if eco == "npm":
            wk = get_json(f"https://api.npmjs.org/downloads/point/last-week/{pkg}", timeout=12).get("downloads")
            mo = get_json(f"https://api.npmjs.org/downloads/point/last-month/{pkg}", timeout=12).get("downloads")
            unit = "npm downloads"
        elif eco == "crates":
            j = get_json(f"https://crates.io/api/v1/crates/{pkg}", timeout=12).get("crate", {})
            wk, mo = None, j.get("recent_downloads")
            unit = "crates.io downloads"
        elif eco == "docker":
            j = get_json(f"https://hub.docker.com/v2/repositories/{pkg}", timeout=12)
            wk, mo = None, j.get("pull_count")
            unit = "Docker Hub pulls (total)"
        elif eco == "brew":
            j = get_json(f"https://formulae.brew.sh/api/formula/{pkg}.json", timeout=12)
            mo = ((j.get("analytics") or {}).get("install") or {}).get("30d", {}).get(pkg)
            wk = None
            unit = "Homebrew installs (30d)"
        else:
            j = get_json(f"https://pypistats.org/api/packages/{pkg.lower()}/recent", timeout=12).get("data", {})
            wk, mo = j.get("last_week"), j.get("last_month")
            unit = "PyPI downloads"
    except Exception as e:
        return f"Could not fetch package downloads for {ticker}: {e}"

    out = [f"Developer Adoption — {company or ticker}",
           f"Source: {eco} · package '{pkg}'", "",
           f"  {'Last week':<14}{(f'{wk:,}' if isinstance(wk,int) else '—'):>16}",
           f"  {'Last month':<14}{(f'{mo:,}' if isinstance(mo,int) else '—'):>16}",
           "", f"  {unit} — a proxy for product usage / mindshare."]
    return "\n".join(out)


def players(ticker: str, company: str = "") -> str:
    appids = STEAM.get(ticker.upper())
    if not appids:
        return (f"No tracked Steam titles for {ticker}.\n"
                "  Covered: a few large publishers (EA, TTWO).")
    rows = []
    for appid in appids:
        try:
            j = get_json("https://steamspy.com/api.php",
                         params={"request": "appdetails", "appid": appid}, timeout=12)
            rows.append((j.get("name", str(appid)), j.get("owners", "—"), j.get("ccu", 0)))
        except Exception:
            continue
    if not rows:
        return f"No Steam data available for {company or ticker} right now."
    out = [f"Steam Players — {company or ticker}",
           "Source: SteamSpy", "",
           f"  {'Title':<30}{'Concurrent':>12}", "  " + "─" * 44]
    for name, owners, ccu in rows:
        out.append(f"  {str(name)[:29]:<30}{ccu:>12,}")
        out.append(f"    [dim]owners {owners}[/dim]".replace("[dim]", "").replace("[/dim]", ""))
    return "\n".join(out)
