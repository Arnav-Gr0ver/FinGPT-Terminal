"""Our World in Data — country indicators via grapher CSV exports (free, no key).

OWID republishes V-Dem, World Bank, and other datasets as clean, current CSVs.
We use it for governance/corruption, which the World Bank's WGI API no longer
serves."""

import csv
import io

from src.data.http import get

_CPI_CSV = "https://ourworldindata.org/grapher/political-corruption-index.csv"

# OWID entity names differ slightly from our display names in a few cases.
_ENTITY_FIX = {"United States": "United States", "South Korea": "South Korea",
               "UAE": "United Arab Emirates", "Russia": "Russia",
               "Czechia": "Czechia", "Turkey": "Turkey"}


def corruption(name: str) -> str:
    """V-Dem Political Corruption Index (0 = least corrupt … 1 = most corrupt),
    last several years. Source: Our World in Data / V-Dem."""
    entity = _ENTITY_FIX.get(name, name)
    try:
        text = get(_CPI_CSV, params={"v": "1", "csvType": "full"}, timeout=20).text
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception as e:
        return f"Could not fetch the corruption index: {e}"
    if not rows:
        return "Corruption-index data is unavailable right now."

    col = next((c for c in rows[0] if "orrupt" in c), None)
    if not col:
        return "Corruption-index column not found."
    series = []
    for r in rows:
        if r.get("Entity") == entity and r.get(col) not in (None, ""):
            try:
                series.append((int(r["Year"]), float(r[col])))
            except (ValueError, TypeError):
                continue
    if not series:
        return f"No corruption-index data for {name}."
    series = sorted(series)[-8:]

    out = [f"Political Corruption Index — {name}",
           "Source: Our World in Data / V-Dem · 0 = clean … 1 = corrupt", "",
           f"  {'Year':<8}{'Index':>8}", "  " + "─" * 30]
    for yr, v in series:
        bar = "█" * min(int(v * 28), 28)
        out.append(f"  {yr:<8}{v:>8.2f}  {bar}")
    latest = series[-1][1]
    verdict = ("high corruption" if latest > 0.6 else
               "moderate" if latest > 0.3 else "low corruption")
    out += ["", f"  Latest: {latest:.2f} — {verdict}."]
    return "\n".join(out)
