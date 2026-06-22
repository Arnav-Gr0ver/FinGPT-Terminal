# FinR1 Terminal

> An analyst in your terminal.

FinR1 is a financial research terminal that connects 125 public data sources through a single querying language. Every figure is traceable to a free, key-less source — no hallucinations, no paywalls.

There are two ways to use it:

**1. Query public data** — load an instrument, chain functions, get structured output instantly.
```
NVDA price financials chart 1y
US gdp inflation corruption co2
BTC cex funding governance
GOLD vs OIL compare corr chart 1y
```

**2. AI mode** — `/ask` answers questions grounded in the terminal's data; `/agent` lets an AI run the terminal autonomously to research and synthesize across sources.

[![Join the Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/finr1)

---

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

```
/help                   overview (or loaded instrument's functions)
/help <category>        instruments in that category  →  /help equity
/help <symbol>          all functions for that instrument  →  /help NVDA
/help india             fuzzy search — shows IN, SENSEX, NIFTY
```

---

## Query language

One rule: **load an INSTRUMENT, run FUNCTIONS**.

```
NVDA                              # load any equity
price financials pe revenue       # chain functions
chart 1y                          # function with argument
NVDA vs AMD vs SMH                # load a set
compare corr spread               # set-aware functions
find india                        # search instruments
/help equity                      # browse functions by category
```

**Why this beats a chat interface:**

- **Grounded**: every number is fetched from a traceable source, not generated. No hallucinations.
- **Composable**: `NVDA vs AMD corr returns chart 1y` is one line, not five back-and-forths.
- **Consistent**: `corruption` works the same for `US`, `INDIA`, and `CN`. Same schema, every time.
- **Fast**: no tokens to generate — data is fetched and rendered directly.

The grammar is intentionally minimal. You don't describe what you want in prose; you name the instrument and the analysis. The terminal knows which functions apply to which category and enforces it.

---

## AI

*(coming in v0.1.0)*

- `/ask <question>` — answers grounded in live terminal data, not training-time knowledge
- `/agent` — autonomous agent that runs terminal commands, synthesizes across sources, and returns a structured report

The agent uses the same query language under the hood, so its outputs are source-traceable and reproducible.

---

## Data sources

125 sources across 13 categories — all free, no API keys.

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

---

## Roadmap

| Version | Milestone |
|---------|-----------|
| **v0.1.0** | Public data terminal · data retrieval harness · financial reasoning model |
| **v0.2.0** | Agent mode — AI runs terminal commands to research and synthesize |
| **v0.3.0** | Data quality and depth expansion · 250 sources |
| **v0.4.0** | Benchmark terminal accuracy · public report |
