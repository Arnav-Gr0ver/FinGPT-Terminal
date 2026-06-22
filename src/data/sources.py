"""All free, no-key data sources used by FinR1 Terminal.

Add an entry here when a new provider is wired in; the count in the
startup banner and /help panels updates automatically.
"""

SOURCES: tuple[str, ...] = (
    # Prices / market data
    "Yahoo Finance",
    "CoinGecko",
    "Stooq",
    # Fundamentals / filings
    "SEC EDGAR",
    "FRED",
    # DeFi / on-chain
    "DeFiLlama",
    "DEX Screener",
    "GeckoTerminal",
    "Hyperliquid",
    "Snapshot.org",
    "Deribit",
    # Cross-exchange crypto pricing (31 venues)
    "Kraken", "Coinbase", "OKX", "KuCoin", "Bitstamp", "Bitfinex",
    "MEXC", "HTX", "Crypto.com", "Gemini", "Bitget", "Upbit",
    "bitFlyer", "WhiteBIT", "CoinEx", "BitMart", "Gate.io", "HitBTC",
    "AscendEX", "BTSE", "BingX", "DigiFinex", "Bitrue", "Bitso",
    "BigONE", "WazirX", "XT", "WOO", "Bithumb", "Coincheck", "Indodax",
    # Additional crypto data
    "CoinPaprika",
    "Alternative.me",
    "Blockchain.com",
    # Country / macro / international
    "World Bank",
    "IMF",
    "WHO",
    "Our World in Data",
    # International statistical bodies
    "ECB (European Central Bank)",
    "Eurostat",
    "OECD.Stat",
    "ILO (ILOSTAT)",
    "BIS Statistics",
    "UN FAO (FAOSTAT)",
    "ONS (UK Statistics)",
    "Statistics Canada",
    "Destatis (Germany)",
    "INSEE (France)",
    "ABS (Australia)",
    # US government data
    "BLS (Bureau of Labor Statistics)",
    "FDIC",
    "TreasuryDirect",
    "PatentsView (USPTO)",
    "Federal Reserve H.8",
    "ProPublica Nonprofit Explorer",
    # Government / regulatory
    "CFTC",
    "openFDA",
    "USAspending.gov",
    "Federal Register",
    "ClinicalTrials.gov",
    "Senate LDA",
    "FINRA",
    "CMS Open Payments",
    # Company-level data
    "Greenhouse",
    "Lever",
    "CourtListener",
    "OpenFEC",
    "EPA ECHO",
    "GitHub API",
    "npm Registry",
    "PyPI",
    "crates.io",
    "SteamSpy",
    "OpenCorporates",
    # Nature / climate / physical world
    "GBIF",
    "NASA POWER",
    "NASA EONET",
    "Open-Meteo",
    "Open-Meteo Air Quality",
    "USGS",
    "Carbon Monitor",
    "NOAA (api.weather.gov)",
    "Global Power Plant Database (WRI)",
    # Calendars / sessions
    "Nager.Date",
    "exchange_calendars",
    # Research & academic
    "arXiv",
    "CrossRef",
    "Semantic Scholar",
    "PubMed / NCBI",
    # News / attention / signals
    "GDELT",
    "Hacker News",
    "Google Trends",
    "Google News",
    "Stack Exchange",
    "Reddit",
    "Dev.to",
    "Lobste.rs",
    # Reference / encyclopedic
    "Wikipedia",
    "Wikidata",
    "Internet Archive",
    "The Economist",
    "RestCountries",
    # Governance & geopolitical
    "Open Sanctions",
    "V-Dem (Varieties of Democracy)",
    "SIPRI",
    "UN SDG Indicators",
    "World Food Programme (VAM)",
    # Trade & agriculture
    "UN Comtrade",
    "USDA ERS",
    # FX conversion (5 fallback providers)
    "Frankfurter",
    "open.er-api",
    "fxratesapi",
    "vatcomply",
    "currency-api",
)
