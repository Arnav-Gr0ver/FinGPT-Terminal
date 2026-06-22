# FinR1 Terminal

[![Join the Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/K9qDtng3hQ)

> An analyst in your terminal.

FinR1 is a financial research terminal. Load an instrument, run functions — every figure pulled from a free, key-less public source.

```
NVDA price financials chart 1y
US gdp inflation corruption co2
BTC cex funding governance
GOLD vs OIL compare corr chart 1y
```

**AI mode** — coming in v0.1.0. `/ask` answers questions grounded in live terminal data; `/agent` runs the terminal autonomously to research and synthesize across sources.

---

## Install

```bash
pip install -e .
finr1
```

```
<FinR1 Terminal> NVDA
<FinR1 Terminal NVDA> price financials chart 1y
```

Tab autocompletes instruments and functions. `/help` for the full reference.

---

## Query language

One rule: **instrument first, then functions**.

```
NVDA                         # load any equity
price financials pe revenue  # chain functions left to right
chart 1y                     # some functions take an argument
NVDA vs AMD vs SMH           # load a set
compare corr spread          # set-aware functions run across all
find india                   # search instruments by name
/help equity                 # browse a category
/help calendar               # explain a function
```

The terminal enforces which functions apply to which category, so the same function always works the same way — `gdp` for `US`, `IN`, `CN`, `DE`.

---

## Data sources

125 sources — all free, no API keys.

**Markets** — equity, etf, index, commodity, fx
Prices · fundamentals · earnings · SEC filings · options · short interest · CFTC positioning · analyst targets · insider trades · carry · supply · weather

**Economy** — country, macro
GDP · inflation · trade · debt · unemployment · CO₂ · military spend · health · corruption · IMF · WHO · FRED

**Crypto** — crypto, chain, protocol, stablecoin
Cross-exchange prices · DEX pairs · funding rates · governance votes · TVL · protocol fees · implied vol

**Other** — exchange, topic
Market hours · holidays · Google Trends · news sentiment · Stack Overflow

**Alt-data** (equity)
Clinical trials · FDA recalls · Federal Register · lobbying · contracts · hiring · litigation · FEC donations · EPA · GitHub · package downloads · Steam players

---

## Roadmap

| Version | Milestone |
|---------|-----------|
| **v0.1.0** | Public data terminal · data retrieval harness · financial reasoning model |
| **v0.2.0** | Agent mode — AI runs the terminal to research and synthesize |
| **v0.3.0** | Data quality and depth expansion · 250 sources |
| **v0.4.0** | Benchmark terminal accuracy · public report |
