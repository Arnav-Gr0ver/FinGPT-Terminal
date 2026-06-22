# FinR1 Terminal

[![Join the Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/finr1)

> The analyst in your terminal.

FinR1 Terminal is a financial deep research terminal that connects 125+ public data sources through a single querying language. Every figure is traceable to a free, key-less source.

There are two ways to use it:

**1. Query public data** - load an instrument, chain functions, get structured output instantly.
```
NVDA price financials chart 1y
US gdp inflation corruption co2
BTC cex funding governance
GOLD vs OIL compare corr chart 1y
```

**2. AI mode** - `/ask` answers questions grounded in the terminal's data

## Install & run

```bash
pip install -e .
finr1
```

```
<FinR1 Terminal> NVDA
<FinR1 Terminal NVDA> price financials chart 1y
```

Arrow keys + Tab complete instruments and functions.

## Data sources

125 sources across 13 categories - all free, no API keys.

| Category | What's available |
|----------|-----------------|
| **Equity / ETF** | Prices, fundamentals, earnings, filings, sentiment, alt-data, options, short interest |
| **Crypto / DeFi** | Prices across 31 exchanges, DEX pairs, funding rates, governance, on-chain TVL/fees |
| **Macro / Country** | GDP, inflation, trade, debt, employment, CO₂, military, health, governance |
| **Commodities / FX** | Prices, CFTC positioning, supply, carry, weather |
| **Indices** | Prices, constituents, positioning |
| **Research** | Clinical trials, FDA, patents, academic papers, regulatory filings |
| **Climate** | NASA solar/weather, carbon emissions, NOAA, global power plant data |
| **Governance** | Open Sanctions, V-Dem, SIPRI, UN SDG, World Food Programme |

## Roadmap

| Version | Milestone |
|---------|-----------|
| **v0.1.0** | Public data terminal · data retrieval harness · financial reasoning model |
| **v0.2.0** | Agent mode - AI runs terminal commands to research and synthesize |
| **v0.3.0** | Data quality and depth expansion · 250 sources |
| **v0.4.0** | Benchmark terminal accuracy · public report |