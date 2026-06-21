# FinR1 Terminal

> An analyst in your terminal.

A financial **deep-research terminal** that connects public market data through a
single querying language and lets you reason over it with grounded AI. Load a
target, run a pipeline of functions, then ask Fin-R1 questions about exactly
what you pulled — every figure traceable to a panel the terminal actually
fetched. Everything is live, free, and needs no API keys (except the optional AI
endpoint).

```
NVDA price chart 1y
└─┬┘ └─────┬─────┘
TARGET   FUNCTIONS
```

### Run it

```bash
pip install -e .       # from this repo (or: pip install -r requirements.txt)
finr1                  # launch the terminal
```

Without installing: `python -m src.main`. Published builds: `pip install finr1-terminal && finr1`.

```
$ finr1
<FinR1 Terminal> NVDA
<FinR1 Terminal NVDA> price financials chart 1y
```

The bottom bar always shows what's expected next (a target, a function, a
range); arrow keys + Tab complete it. Slash commands: `/help` · `/clear` ·
`/login` · `/ask` · `/exit`. The prompt is timestamped; command history is
in-memory only and never written to disk.

---

# Query language

One grammar for all of public market data: **load a TARGET, run FUNCTIONS.** You
load a target once, then run a pipeline of functions against it — no flags, no
menus. Combine targets with `vs` and set-aware functions act on all of them.

```
<FinR1 Terminal> NVDA
<FinR1 Terminal NVDA> price financials chart 1y

<FinR1 Terminal NVDA> NVDA vs AMD vs SMH
<FinR1 Terminal NVDA·AMD·SMH> compare corr chart 1y
```

### Targets — what you can load

| Target | Examples | Source |
|--------|----------|--------|
| Equity / ETF / name | `NVDA` · `SPY` · `apple` | Yahoo Finance |
| FRED macro series | `CPI` · `GDP` · `DGS10` · `M2` | FRED |
| Index / commodity / FX | `SPX` · `VIX` · `GOLD` · `OIL` · `EURUSD` · `DXY` | Yahoo Finance |
| Crypto | `BTC` · `ETH` · `SOL` | CoinGecko |
| Country | `US` · `CHINA` · `country:BR` | World Bank |
| Crypto chain | `ETHEREUM` · `chain:arbitrum` | DeFiLlama |
| DeFi protocol | `AAVE` · `UNISWAP` · `protocol:lido` | DeFiLlama |
| Stablecoin | `USDT` · `USDC` · `DAI` | DeFiLlama |
| Exchange | `NYSE` · `LSE` · `JPX` | exchange_calendars |
| Research topic | `topic:lithium` · `topic:"AI"` | Wikipedia · GDELT · Trends |

Combine into a **set** with `vs` / `&` / `,` — e.g. `NVDA vs AMD vs INTC`. Type a
new ticker any time to switch targets; the prompt shows what's loaded.

### Functions — what you can run

A query is a target followed by a **pipeline of functions**, run left to right.
Set-aware functions (`compare`, `corr`, `spread`, `returns`, `stats`, `chart`)
use the whole set; the rest run once per target. Some need no target at all.

| Group | Functions | |
|-------|-----------|--|
| **Price** | `price` `chart <range>` `returns` `stats` `seasonality` | quote · history · returns · risk · monthly pattern |
| **Compare** *(set)* | `compare` `corr` `spread` | side-by-side · correlation matrix · ratio over time |
| **Company** | `financials` `earnings` `profile` `dividends` | 10-K figures · beat/miss · summary (+Wikipedia) · payouts |
| | `holders` `insiders` `analysts` `filings` `calendar` | ownership · Form 4 · targets · filings · catalysts |
| | `short` `options` `ftd` `sentiment` `splits` | short interest · option chain+IV · SEC fails-to-deliver · news tone · splits |
| | `contracts` `buzz` `fda` `regulations` `github` | federal awards · Hacker News · FDA recalls · Federal Register · dev activity |
| | `trials` `peers` `gtrends` `lobbying` `hiring` `shortvol` | clinical trials · co-watched peers · Google Trends · lobbying spend · open roles · FINRA short % |
| **Country** | `gdp` `inflation` `trade` `debt` `unemployment` `population` `reserves` | World Bank macro · FX reserves |
| | `co2` `military` `health` `corruption` `market` `profile` `holidays` | emissions · defense spend · life expectancy · governance index · benchmark index · snapshot · holidays |
| **Crypto / DeFi** | `tvl` `holdings` `supply` `governance` `funding` `cryptovol` `fees` | chain/protocol TVL · ETF holdings · inventories · DAO votes · perp funding · DVOL implied vol · protocol fees |
| **Signals** | `trends` `risk` `cot` `cotfin` `constituents` | Wikipedia attention · news tone + major-quake risk · CFTC positioning (legacy + financial) · index members |
| **Markets** *(no target)* | `yields` `refrates` `auctions` `usdebt` `budget` `recession` `carry` `stress` `ipos` `bigmac` `weather` `sectors` `indices` `commodities` `forex` | Treasury curve · SOFR · auctions · US debt · deficit · yield-curve signal · FX carry · OFR stress · IPO pipeline · Big Mac PPP · growing-region weather · sectors · indices · commodity & FX boards |
| | `fear` `dominance` `coins` `trending` `onchain` `pools` `dexs` `fees` `chains` `hacks` `treasuries` `protocols` `stablecoins` | crypto fear&greed · dominance · top coins · trending · BTC on-chain · DeFi yields · DEX volume · protocol fees · chains by TVL · exploits · corporate BTC/ETH · DeFi protocols · stablecoins |
| | `predictions` `forecasts` `politics` `congress` `disasters` | Polymarket odds · Manifold forecasts · PredictIt politics · congressional trade filings · FEMA disasters |
| **Find / utility** | `screen [name]` `watch` `hours` `export` `convert` | screener · watchlist · hours · session→md · FX |
| **Ranges** | for `chart` | `5d 1mo 3mo 6mo ytd 1y 2y 5y 10y max` |

Functions are **target-aware**: both the completion menu and the bottom hint bar
only surface functions that fit what's loaded (no `coins` when you're on
equities, no `financials` on a country, no `gdp` on a stock), and the terminal
says so if you run one that doesn't apply.

---

# Data sources

All free, no keys. The querying language above maps onto these providers
transparently — you ask for `financials` or `tvl`, the terminal picks the source.

| Source | Data |
|--------|------|
| Yahoo Finance | Prices, fundamentals, earnings, dividends, holders, analysts, options, ETF holdings; indices, commodities, FX |
| SEC EDGAR / XBRL | 10-K financials, filings, Form 4 insiders, fails-to-deliver, **S-1 IPO pipeline** |
| FRED | Macro series, Treasury yields, inventories, federal budget, **yield-curve & FX-carry signals** |
| U.S. Treasury (FiscalData) | National debt, average interest rate, auction results |
| NY Fed | Money-market reference rates — SOFR, EFFR, OBFR, repo (TGCR/BGCR) |
| Office of Financial Research | OFR Financial Stress Index (by category & region) |
| CFTC | Commitments of Traders — weekly futures positioning (specs vs hedgers) |
| USAspending.gov | Federal contract awards by company |
| openFDA | Drug / device / food recalls & enforcement by firm |
| Federal Register | Rules, notices & actions mentioning a company |
| ClinicalTrials.gov | Clinical-trial pipeline by sponsor (pharma / biotech) |
| Senate LDA · House Clerk | Lobbying spend · congressional trade-report filings |
| FINRA | Daily off-exchange short-sale volume by ticker |
| Greenhouse · Lever | Open job roles by department (hiring velocity) |
| GitHub | Public-repo / open-source dev activity for a name |
| World Bank · Our World in Data | Country GDP, inflation, trade, debt, reserves, CO₂, military, health, **corruption** |
| Nager.Date · exchange_calendars | Public-holiday calendars · real exchange trading sessions |
| Open-Meteo | Weather for key commodity growing / demand regions |
| The Economist | Big Mac Index (burgernomics PPP) |
| DeFiLlama | Chain & protocol TVL, stablecoins, protocols, fees/revenue, DEX volume, yield pools, hacks |
| Snapshot.org · dYdX · Deribit | DAO votes · perp funding · DVOL implied-vol index |
| CFTC | Commitments of Traders — legacy **and** financial-futures (TFF) positioning |
| CoinGecko · alternative.me | Crypto prices, dominance, trending, **corporate treasuries** · fear & greed |
| blockchain.info · mempool.space | Bitcoin on-chain stats — hashrate, throughput, fee market |
| Polymarket · Manifold · PredictIt | Prediction-market & community-forecast odds |
| FEMA | US federal disaster declarations |
| Hacker News (Algolia) · Google Trends | Tech-community attention · search interest |
| Wikipedia / Wikimedia | Page-view attention · profiles · index constituents |
| USGS · GDELT | Earthquakes · global news tone |
| Google News · Stooq · Frankfurter (ECB) | Headline fallback · price fallback · FX conversion |

Every source above is **public and key-less** — no signup, no tokens. Requests go
through one pooled HTTP session with automatic retries, so a transient hiccup
re-tries rather than failing the panel.

**Limitations.** Yahoo prices are delayed ~15 min; FRED/World Bank series publish
on their own lag; CFTC positioning is weekly (released each Friday for the prior
Tuesday). Name resolution is best-effort — use the exact symbol when ambiguous.

---

# AI mode

`/ask`, powered by **Fin-R1**, reasons over the data you've **already pulled this
session** — you choose how much to hand the model:

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
it, never recalls it — and the answer cites the panels it used. It's only as
good as its endpoint and the data behind it, so verify anything you'd trade on.

### Setup

`/ask` needs an OpenAI-compatible Fin-R1 endpoint. Point it at any server
running the model (e.g. `vllm serve SUFE-AIFLM-Lab/Fin-R1`):

```bash
export FINGPT_ENDPOINT="https://<host>/v1/chat/completions"
export FINGPT_API_KEY="..."
```

…or `/login` and paste them (saved to `~/.fingpt/config.json`; env wins).
Override the served id with `FINGPT_MODEL`, the context window with
`FINGPT_CONTEXT`. **Everything except `/ask` works with no AI configured.**
