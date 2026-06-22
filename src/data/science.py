"""Per-country science sensors (free, no key).

  • GBIF — biodiversity occurrence records by country → biodiversity
"""

from src.data.http import get_json


def biodiversity(iso2: str = "US", name: str = "United States") -> str:
    """Biodiversity occurrence records for a country (works for every country).
    Source: GBIF (Global Biodiversity Information Facility)."""
    iso2 = (iso2 or "US").upper()
    try:
        total = get_json("https://api.gbif.org/v1/occurrence/count", params={"country": iso2}, timeout=12)
        recent = get_json("https://api.gbif.org/v1/occurrence/search",
                          params={"country": iso2, "year": __import__("datetime").date.today().year, "limit": 0}, timeout=12)
    except Exception as e:
        return f"Could not fetch GBIF data: {e}"
    if not isinstance(total, int) or total == 0:
        return f"No GBIF biodiversity records for {name}."
    out = [f"Biodiversity Records — {name}", "Source: GBIF", "",
           f"  {'Total occurrence records':<30} {total:,}",
           f"  {'Recorded this year':<30} {recent.get('count', 0):,}",
           "", "  An open index of species observations — research & ESG adjacent."]
    return "\n".join(out)
