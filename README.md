# FinR1 Terminal

> One grammar for public market data: **load a TARGET, run FUNCTIONS.**

```
NVDA price chart 1y
└─┬┘ └─────┬─────┘
TARGET   FUNCTIONS
```

You load a target once, then run a pipeline of functions against it — no flags,
no menus. Combine targets with `vs` and set-aware functions act on all of them.

```
$ finr1
<FinR1 Terminal> NVDA
<FinR1 Terminal NVDA> price financials chart 1y

<FinR1 Terminal NVDA> NVDA vs AMD vs SMH
<FinR1 Terminal NVDA·AMD·SMH> compare corr chart 1y
```

The bottom bar always shows what's expected next (a target, a function, a range);
arrow keys + Tab complete it. Everything is live, free, and needs no API keys.

---

## Install

```bash
pip install finr1-terminal
finr1
```

From source: `pip install -e ".[dev]"` then `python -m src.main`.

---

## Targets — what you can load

| Target | Examples | Source |
|--------|----------|--------|
| Equity / ETF / name | `NVDA` · `SPY` · `apple` | Yahoo Finance |
| FRED macro series | `CPI` · `GDP` · `DGS10` · `M2` | FRED |
| Index / commodity / FX | `SPX` · `VIX` · `GOLD` · `OIL` · `EURUSD` · `DXY` | Yahoo Finance |
| Crypto | `BTC` · `ETH` · `SOL` | CoinGecko |
| Country | `US` · `CHINA` · `country:BR` | World Bank |
| Crypto chain | `ETHEREUM` · `chain:arbitrum` | DeFiLlama |

Combine into a **set** with `vs` / `&` / `,` — e.g. `NVDA vs AMD vs INTC`. Type a
new ticker any time to switch targets; the prompt shows what's loaded.

---

## Functions — what you can run

A query is a target followed by a **pipeline of functions**, run left to right.
Set-aware functions (`compare`, `corr`, `spread`, `returns`, `stats`, `chart`)
use the whole set; the rest run once per target. Some need no target at all.

| Group | Functions | |
|-------|-----------|--|
| **Price** | `price` `chart <range>` | quote · price history |
| | `returns` `stats` `seasonality` | trailing returns · vol/beta/drawdown · monthly pattern |
| **Compare** *(set)* | `compare` `corr` `spread` | side-by-side · correlation matrix · ratio over time |
| **Company** | `financials` `earnings` `profile` | SEC-filed 10-K figures · beat/miss + next · summary |
| | `dividends` `holders` `insiders` | payout history · ownership · SEC Form 4 |
| | `analysts` `filings` `calendar` | price targets · 10-K/Q/8-K · catalysts |
| | `short` `options` `sentiment` | short interest · option chain + IV · news tone |
| **Macro / chain** | `gdp` `inflation` `trade` `debt` | country macro (World Bank) |
| | `tvl` `holdings` `supply` | chain TVL · ETF constituents · oil/gas inventories |
| **Signals** | `trends` `risk` | Wikipedia attention · news tone + major-quake risk |
| **Markets** *(no target)* | `yields` `sectors` `fear` `dominance` `coins` | Treasury curve · sector perf · crypto fear&greed · dominance · top coins |
| **Find / utility** | `screen [name]` | gainers · losers · value · tech … (bare = list) |
| | `watch` `hours` `export` `convert` | watchlist · market hours · session→markdown · FX convert |
| **Ranges** | for `chart` | `5d 1mo 3mo 6mo ytd 1y 2y 5y 10y max` |

The terminal tells you when a function doesn't fit a target (`gdp` needs a
country, `financials` needs a company).

---

## The ai layer — `/ask`, powered by Fin-R1

`/ask` reasons over the data you've **already pulled this session** — you choose
how much to hand the model:

```
/ask "..."        # the most recent panel
/ask 5 "..."      # the last 5
/ask all "..."    # the whole session
```

```
<FinR1 Terminal NVDA·AMD> compare returns
<FinR1 Terminal NVDA·AMD> /ask all "who's the better risk-adjusted buy?"
```

Every figure comes from data the terminal actually pulled — Fin-R1 reasons over
it, never recalls it — and the answer cites the panels it used.

**Setup.** `/ask` needs an OpenAI-compatible Fin-R1 endpoint. Point it at any
server running the model (e.g. `vllm serve SUFE-AIFLM-Lab/Fin-R1`):

```bash
export FINGPT_ENDPOINT="https://<host>/v1/chat/completions"
export FINGPT_API_KEY="..."
```

…or `/login` and paste them (saved to `~/.fingpt/config.json`; env wins).
Override the served id with `FINGPT_MODEL`, the context window with
`FINGPT_CONTEXT`. **Everything except `/ask` works with no AI configured.**

---

## Data sources — all free, no keys

| Source | Data |
|--------|------|
| Yahoo Finance | Prices, fundamentals, earnings, dividends, holders, analysts, options, ETF holdings; indices, commodities, FX |
| SEC EDGAR / XBRL | Filed 10-K financials, recent filings, Form 4 insiders |
| FRED | Macro series, Treasury yields, oil & gas inventories |
| World Bank | Country GDP, inflation, trade, debt |
| DeFiLlama | Crypto-chain TVL |
| CoinGecko · alternative.me | Crypto prices · fear & greed |
| Wikimedia · USGS · GDELT | Attention · earthquakes · global news tone |
| Stooq · Frankfurter (ECB) | Price fallback · FX conversion |

---

## System

Slash commands: `/help` · `/clear` · `/login` · `/exit` (and `/ask`). The prompt
is timestamped; command history is in-memory only and never written to disk.

## Limitations

- Yahoo prices are delayed ~15 min; FRED/World Bank series publish on their own lag.
- `/ask` is only as good as its endpoint and the data it pulls — verify anything
  you'd trade on.
- Name resolution is best-effort; use the exact symbol when ambiguous.
