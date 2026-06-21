"""CFTC Commitments of Traders — weekly futures positioning (free, no key).

The CFTC publishes, every Friday, how the major trader groups are positioned in
each futures market. The legacy report splits open interest into *non-commercial*
(large speculators — funds) and *commercial* (hedgers — producers/users). The
speculator net position (long − short) is a widely-watched sentiment gauge.

Data: CFTC Public Reporting Socrata API (publicreporting.cftc.gov)."""

from src.data.http import get_json

COT_API = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"

# Our subject symbols → a substring of the CFTC contract name. We pick the
# largest-open-interest contract matching the keyword, so these land on the
# benchmark contract (e.g. Chicago wheat, CME euro FX, E-mini S&P).
COT_MARKETS = {
    # metals & energy
    "GOLD": "GOLD", "SILVER": "SILVER", "COPPER": "COPPER",
    "PLATINUM": "PLATINUM", "PALLADIUM": "PALLADIUM",
    "OIL": "CRUDE OIL, LIGHT SWEET", "BRENT": "BRENT",
    "NATGAS": "NAT GAS", "GASOLINE": "GASOLINE RBOB", "HEATINGOIL": "NY HARBOR ULSD",
    # agriculture
    "WHEAT": "WHEAT-SRW", "CORN": "CORN", "SOYBEAN": "SOYBEANS",
    "COFFEE": "COFFEE", "SUGAR": "SUGAR NO. 11", "COCOA": "COCOA", "COTTON": "COTTON",
    # FX
    "EURUSD": "EURO FX", "GBPUSD": "BRITISH POUND", "USDJPY": "JAPANESE YEN",
    "AUDUSD": "AUSTRALIAN DOLLAR", "USDCAD": "CANADIAN DOLLAR", "USDCHF": "SWISS FRANC",
    "NZDUSD": "NEW ZEALAND DOLLAR", "USDMXN": "MEXICAN PESO", "USDBRL": "BRAZILIAN REAL",
    # equity index & crypto
    "SPX": "E-MINI S&P 500", "SP500": "E-MINI S&P 500", "NDX": "NASDAQ-100 STOCK INDEX (MINI)",
    "DJIA": "DJIA", "RUSSELL": "RUSSELL 2000", "VIX": "VIX", "BTC": "BITCOIN",
}


def cot_supported(symbol: str) -> bool:
    return symbol.upper() in COT_MARKETS


def _f(row, key):
    try:
        return float(row.get(key))
    except (TypeError, ValueError):
        return None


TFF_API = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"


def get_cotfin(symbol: str, label: str = "") -> str:
    """Traders-in-Financial-Futures positioning — splits open interest into
    dealers, asset managers, and leveraged funds (hedge funds). Best for index
    and FX futures. Source: CFTC TFF report."""
    keyword = COT_MARKETS.get(symbol.upper())
    if not keyword:
        return f"No CFTC financial-futures mapping for {symbol}."
    try:
        rows = get_json(TFF_API, params={
            "$where": f"upper(market_and_exchange_names) like '%{keyword.upper()}%'",
            "$order": "report_date_as_yyyy_mm_dd DESC", "$limit": 20,
        }, timeout=20)
    except Exception as e:
        return f"Could not fetch financial-futures positioning for {symbol}: {e}"
    if not rows:
        return f"No CFTC TFF data for {symbol} (try a major index or FX future)."

    latest = rows[0].get("report_date_as_yyyy_mm_dd", "")[:10]
    same = [r for r in rows if r.get("report_date_as_yyyy_mm_dd", "")[:10] == latest]
    row = max(same, key=lambda r: _f(r, "open_interest_all") or 0)

    def grp(longk, shortk):
        lng = _f(row, longk) or 0
        sh = _f(row, shortk) or 0
        return lng, sh, lng - sh

    oi = _f(row, "open_interest_all") or 0
    am = grp("asset_mgr_positions_long", "asset_mgr_positions_short")
    lf = grp("lev_money_positions_long", "lev_money_positions_short")
    dl = grp("dealer_positions_long", "dealer_positions_short")
    contract = (row.get("market_and_exchange_names") or keyword).strip()[:46]

    def line(nm, g):
        return f"  {nm:<18}{g[0]:>12,.0f}{g[1]:>12,.0f}{g[2]:>+13,.0f}"
    return "\n".join([
        f"CFTC Financial-Futures Positioning — {label or symbol}",
        f"Source: CFTC TFF · {contract} · week of {latest}",
        "",
        f"  {'Group':<18}{'Long':>12}{'Short':>12}{'Net':>13}",
        "  " + "─" * 56,
        line("Asset managers", am),
        line("Leveraged funds", lf),
        line("Dealers", dl),
        "",
        f"  Open interest     {oi:>12,.0f} contracts",
        "",
        "  Asset managers ≈ real money; leveraged funds ≈ hedge-fund/CTA flow.",
    ])


def get_cot(symbol: str, label: str = "") -> str:
    keyword = COT_MARKETS.get(symbol.upper())
    if not keyword:
        return (f"No CFTC positioning mapping for {symbol}. Supported: major "
                f"commodities, FX, and index futures.")
    try:
        rows = get_json(COT_API, params={
            "$where": f"upper(contract_market_name) like '%{keyword.upper()}%'",
            "$order": "report_date_as_yyyy_mm_dd DESC",
            "$limit": 30,
        }, timeout=20)
    except Exception as e:
        return f"Could not fetch CFTC positioning for {symbol}: {e}"
    if not rows:
        return f"No CFTC Commitments-of-Traders data found for {symbol}."

    latest_date = rows[0].get("report_date_as_yyyy_mm_dd", "")[:10]
    same = [r for r in rows if (r.get("report_date_as_yyyy_mm_dd", "")[:10] == latest_date)]
    row = max(same, key=lambda r: _f(r, "open_interest_all") or 0)

    oi      = _f(row, "open_interest_all") or 0
    nc_long = _f(row, "noncomm_positions_long_all") or 0
    nc_shrt = _f(row, "noncomm_positions_short_all") or 0
    c_long  = _f(row, "comm_positions_long_all") or 0
    c_shrt  = _f(row, "comm_positions_short_all") or 0
    d_long  = _f(row, "change_in_noncomm_long_all") or 0
    d_shrt  = _f(row, "change_in_noncomm_short_all") or 0

    net_spec  = nc_long - nc_shrt
    net_chg   = d_long - d_shrt
    net_pct   = (net_spec / oi * 100) if oi else 0
    stance    = ("net LONG — speculators bullish" if net_spec > 0
                 else "net SHORT — speculators bearish" if net_spec < 0 else "flat")
    contract  = (row.get("contract_market_name") or keyword).strip()[:48]

    def line(name, lng, shrt):
        net = lng - shrt
        return f"  {name:<16} {lng:>12,.0f} {shrt:>12,.0f} {net:>+13,.0f}"

    return "\n".join([
        f"CFTC Commitments of Traders — {label or symbol}",
        f"Source: CFTC · {contract} · week of {latest_date}",
        "",
        f"  {'Group':<16} {'Long':>12} {'Short':>12} {'Net':>13}",
        "  " + "─" * 56,
        line("Speculators", nc_long, nc_shrt),
        line("Hedgers", c_long, c_shrt),
        "",
        f"  Open interest        {oi:>12,.0f} contracts",
        f"  Speculator net       {net_spec:>+12,.0f}  ({net_pct:+.1f}% of OI)",
        f"  Week-over-week       {net_chg:>+12,.0f}  (change in spec net)",
        "",
        f"  Read: {stance}.",
    ])
