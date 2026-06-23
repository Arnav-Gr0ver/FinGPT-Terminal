```
  ███████╗██╗███╗   ██╗██████╗  ██╗
  ██╔════╝██║████╗  ██║██╔══██╗███║
  █████╗  ██║██╔██╗ ██║██████╔╝╚██║
  ██╔══╝  ██║██║╚██╗██║██╔══██╗ ██║
  ██║     ██║██║ ╚████║██║  ██║ ██║
  ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═╝
  ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗
     ██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║
     ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║
     ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║
     ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝
```

[![Join the Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/finr1)
[![Early Preview Waitlist](https://img.shields.io/badge/Early%20Preview-Waitlist-e05c4b?logo=globe&logoColor=white)](https://finterminal.framer.website/)

> The analyst in your terminal.

FinR1 is a financial research terminal. Load an instrument, run functions — every figure pulled from a free, key-less public source.

## Install & run

Requires **Python 3.10+** and **pip** — [python.org/downloads](https://www.python.org/downloads/) if you don't have it.

```bash
pip install git+https://github.com/Arnav-Gr0ver/FinR1-Terminal.git
finr1
```

## Usage

```
<FinR1 Terminal>  ❯  NVDA
<FinR1 Terminal NVDA>  ❯  price financials chart 1y
```

Arrow keys + Tab complete instruments and functions. Chain any number of functions in one line.

---

**Equity — `NVDA price`**
```
╭─  NVDA  price  ───────────────────────────────────────╮
│                                                       │
│    NVIDIA Corporation   NASDAQ · equity               │
│                                                       │
│    Price     $202.17      Change    -5.66   (-2.72%)  │
│    Open      $202.16      Day       200.04 – 203.77   │
│    Volume    67.6M         Mkt Cap   $4.9T            │
│    52W       145.50 – 236.54                          │
│                                                       │
╰─────────────────────────────────────────────── 12:39 ─╯
```

**Macro — `US gdp inflation`**
```
╭─  US  gdp  inflation  ─────────────────────────╮
│                                                │
│    United States   country                     │
│                                                │
│    GDP          $27.4T     Growth     2.8%     │
│    Inflation    3.2%        Core CPI   3.5%    │
│    Unemployment 3.9%        Debt/GDP   122.3%  │
│    Trade Bal    -$773B      Reserves   $230B   │
│                                                │
╰──────────────────────────────────────── 12:39 ─╯
```

**Crypto — `BTC price`**
```
╭─  BTC  price  ────────────────────────────────────────╮
│                                                       │
│    Bitcoin   crypto                                   │
│                                                       │
│    Price     $62,496      Change    -1,455  (-2.27%)  │
│    Funding   +0.0082%/8h   Open Int  $18.4B           │
│    TVL       $87.2B        Dominance 52.1%            │
│                                                       │
╰─────────────────────────────────────────────── 12:39 ─╯
```

**`/help`**
```
╭─  FinR1 Terminal  ───────────────────────────────────────────────────╮
│                                                                      │
│  Markets    equity       52 fn  ∞    NVDA · AAPL · TSLA · GOOGL     │
│             etf          28 fn  ∞    SPY · QQQ · IWM · GLD · XLF    │
│             index        22 fn  21   SPX · NDX · VIX · FTSE · DAX   │
│             commodity    23 fn  20   GOLD · OIL · WHEAT · NATGAS     │
│             fx           23 fn  16   EURUSD · USDJPY · DXY           │
│                                                                      │
│  Economy    country      31 fn  50   US · CN · JP · DE · UK · IN    │
│             macro        12 fn  25   CPI · GDP · DGS10 · M2          │
│                                                                      │
│  Crypto     crypto       26 fn  ∞    BTC · ETH · SOL · ADA · MATIC  │
│             chain        14 fn  23   ETHEREUM · ARBITRUM · SOLANA    │
│             protocol     14 fn  25   AAVE · UNISWAP · LIDO · CURVE   │
│             stablecoin   10 fn  12   USDT · USDC · DAI · USDS        │
│                                                                      │
│  Other      exchange     11 fn  14   NYSE · NASDAQ · LSE · JPX       │
│             topic        12 fn  ∞    topic:lithium · topic:AI        │
│                                                                      │
│  ──────────────────────────────────────────────────────────────────  │
│    /help <category>  ·  /help <symbol>  ·  /help <function>  ·       │
│  /clear  /exit                                                       │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

## Data sources

125 sources across 13 categories — all free, no API keys.

**Markets**

| Category | What's available |
|----------|-----------------|
| **Equity / ETF** | Price, chart, financials, earnings, options, short interest, filings, sentiment, alt-data (trials, FDA, contracts, lobbying, hiring, litigation) |
| **Index** | Price, chart, constituents, CFTC positioning |
| **Commodity** | Price, chart, supply, CFTC positioning, weather, solar resource |
| **FX** | Price, chart, carry, CFTC positioning, Big Mac index |

**Economy**

| Category | What's available |
|----------|-----------------|
| **Country** | GDP, inflation, trade, debt, unemployment, CO₂, military spend, health, governance, IMF/WHO data |
| **Macro** | FRED series — CPI, DGS10, M2, UNRATE, FEDFUNDS, PCE and 20+ more |

**Crypto**

| Category | What's available |
|----------|-----------------|
| **Crypto** | Price across 31 exchanges, funding rates, implied vol, sentiment |
| **Chain** | TVL, DEX pairs, governance |
| **Protocol** | Fees, DEX pairs, governance |
| **Stablecoin** | Price, depeg monitoring |

**Other**

| Category | What's available |
|----------|-----------------|
| **Exchange** | Market hours, holidays |
| **Topic** | News, Google Trends, risk signal, Stack Overflow activity |

## Roadmap

| Version | Milestone |
|---------|-----------|
| **v0.1.0** | Public data terminal · data retrieval harness · financial reasoning model |
| **v0.2.0** | Agent mode — AI runs terminal commands to research and synthesize |
| **v0.3.0** | Data quality and depth expansion · 250 sources |
| **v0.4.0** | Benchmark terminal accuracy · public report |
