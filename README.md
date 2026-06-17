# FinGPT Terminal

> A financial terminal driven by one grammar: **subject, then verbs.**

```
NVDA price chart 1y
└─┬─┘ └──┬──┘ └─┬─┘
 noun  verb   verb
```

You load a subject once, then chain commands against it. No prefix on every
line, no flags soup. You're in a `<FinGPT Terminal>` session — the subject is
loaded, and you act on it. The grammar is the product.

```
$ fingpt
<FinGPT Terminal> NVDA
  NVDA loaded · NVIDIA Corp · NASDAQ

<FinGPT Terminal NVDA> price
<FinGPT Terminal NVDA> chart 1y
<FinGPT Terminal NVDA> earnings
```

The prompt shows what's loaded. Verbs run against it until you load something
else — just type a new ticker (or a macro series like `CPI`) to switch.

---

## Install

```bash
pip install fingpt-terminal
fingpt
```

**From source:**

```bash
git clone https://github.com/yourname/fingpt-terminal
cd fingpt-terminal
pip install -e ".[dev]"
python -m src.main
```

The free tier needs no API keys for data.

---

## The grammar

One rule: **subject, then verbs.** The subject is the noun; everything after it
acts on that noun.

### Subjects

All free, no keys:

- **Any equity ticker** — `NVDA`, `AAPL`, `BRK.B`. Names work too: `apple`, `nvidia`.
- **Any FRED macro series** — `CPI`, `GDP`, `UNRATE`, `DGS10`, `M2`, … Same grammar:
  `CPI chart 2y` works exactly like `NVDA chart 2y`.
- **Indices, commodities & FX** — `SPX`, `NDX`, `VIX`, `GOLD`, `OIL`, `BRENT`,
  `COPPER`, `EURUSD`, `USDJPY`, `DXY`.
- **Crypto** — `BTC`, `ETH`, `SOL`, …

### Verbs

Each verb answers a specific question a person actually asks.

| Verb | The question it answers |
|------|--------------------------|
| `price` | Where's it trading and how did it move? |
| `chart <range>` | What's the shape over time? (range required: `5d 1mo 3mo 6mo ytd 1y 2y 5y 10y max`) |
| `financials` | Is the business healthy? Revenue, margins, debt — trended. |
| `earnings` | What happened last print, and when's the next? |
| `profile` | What does this company actually do? Sector, industry, summary. |
| `dividends` | What does it pay, and what's the history? |
| `holders` · `insiders` | Who owns it · what are insiders doing (SEC Form 4)? |
| `analysts` | Where do the targets and consensus sit? |
| `filings` | What did they just file? Recent 10-K / 10-Q / 8-K. |
| `news` | What's the story right now? (latest few, with openable links) |
| `compare <peer> [peer]` | How does it stack against peers? (up to 4, side-by-side) |
| `calendar` | What's coming that moves this — earnings, ex-div, splits? |
| `screen [name]` | What's moving / cheap / hot? Find tickers, then load one. |
| `watch` | Your watchlist. With a subject loaded, adds/removes it; bare, it lists. |

Company-specific verbs (`financials`, `earnings`, `profile`, `dividends`,
`holders`, `insiders`, `analysts`, `filings`, `calendar`) apply to equities;
`price`, `chart`, `news`, and `compare` work across every subject type. `screen`
and `watch` need no subject — `screen` produces candidates you can load, `watch`
lists what you're tracking.

`screen` with no argument lists the available screens (`gainers`, `losers`,
`actives`, `shorted`, `smallcaps`, `tech`, `growth`, `value`); `screen value`
runs one.

### Chaining

Verbs compose left to right against the loaded subject:

```
<FinGPT Terminal NVDA> price compare AMD chart 1y
```

Reads as: for NVDA — show price, pull AMD alongside, chart both over 1 year. The
`compare AMD` injects a second subject into everything downstream, so `chart 1y`
now charts both. **Order is meaning.**

```
<FinGPT Terminal NVDA> earnings chart 2y
```

NVDA earnings history, then charted — beat/miss bars across eight quarters.
`chart` inherits whatever the prior verb produced; that's why the grammar is
subject-then-verbs and not flags — a flag can't inherit the previous verb's
output, a chained verb can.

Switch subjects anytime:

```
<FinGPT Terminal NVDA> SNDK
  SNDK loaded · Sandisk Corp
<FinGPT Terminal SNDK> price calendar
```

---

## The ai layer — `ask`, powered by Fin-R1

`ask` is a verb like any other, but it's the one that runs a model: the **ai**
layer, powered by **Fin-R1** (`SUFE-AIFLM-Lab/Fin-R1`, a financial-reasoning
LLM). It acts on the loaded subject and reasons over the same data the free verbs
pull — so it inherits context.

```
<FinGPT Terminal NVDA> financials ask "is the margin dip structural?"
<FinGPT Terminal NVDA> earnings compare AMD ask "who has better operating leverage?"
```

`ask` reasons over the data **already shown this session** — you choose how much
of it to hand the model:

```
ask "..."        # the most recent output only (default)
ask 5 "..."      # the last 5 outputs
ask all "..."    # the whole session so far
```

So `NVDA price financials ask all "is it cheap given the margins?"` hands Fin-R1
the price and financials panels it just printed. Every number comes from data the
terminal actually pulled — Fin-R1 reasons over it, it doesn't recall it — and
sources are cited. After each answer you get a usage line: tokens in/out and how
full the context window is.

Nothing is persisted across sessions: the transcript Fin-R1 can read, and your
up-arrow command history, both live **in memory only** and are wiped when you
quit.

### Setup

`ask` needs a Fin-R1 endpoint and an API key.

**If you were given a key** (Fin-R1 is hosted for you): just point the terminal at
the provided endpoint and key —

```bash
export FINGPT_ENDPOINT="https://<host>/v1/chat/completions"
export FINGPT_API_KEY="sk-finr1-..."
```

…or run `login` and paste them. Saved to `~/.fingpt/config.json`; env vars win.

**If you're hosting it yourself**, [`deploy/`](deploy/) has a one-command Modal
deployment that serves Fin-R1 as a multi-tenant API and lets you mint/revoke
per-customer keys — see [`deploy/README.md`](deploy/README.md).

Override the served model id with `FINGPT_MODEL` and the context window with
`FINGPT_CONTEXT`. **Everything except `ask` works with no AI configuration at all.**

---

## What ships in v1

- **Free verbs:** `price`, `chart`, `financials`, `earnings`, `profile`,
  `dividends`, `holders`, `insiders`, `analysts`, `filings`, `news`, `compare`,
  `calendar`, `screen`, `watch`.
- **Subjects:** equities, FRED macro series, indices, commodities, FX, crypto.
- **ai layer:** `ask` (Fin-R1).

The free tier needs no paid keys.

---

## System

```
help     The grammar and every verb
clear    Clear the screen
login    Save your Fin-R1 endpoint / key (for ask)
exit     Quit
```

The prompt is timestamped, so your scrollback is a dated research log. There's no
tab-completion or ghost-text — the grammar is small enough to just type.
Command history is in-memory only (up-arrow within the session) and is never
saved to disk.

---

## Data sources

All free. No API keys required for market data.

| Source | Data |
|--------|------|
| Yahoo Finance (`yfinance`) | Equity prices, financials, earnings, dividends, holders, analysts, calendar, news; indices, commodities & FX |
| FRED (St. Louis Fed) | Macro series — CPI, GDP, yields, rates, M2, … |
| SEC EDGAR | Recent 10-K / 10-Q / 8-K filings; Form 4 insider trades |
| CoinGecko | Crypto prices |

---

## Known limitations

- **Prices:** yfinance equity data is delayed ~15 minutes.
- **Macro:** FRED series publish on their own cadence; the latest reading may lag.
- **Calendar / earnings dates:** sourced from Yahoo; occasionally missing for
  smaller names.
- **`ask`:** requires an endpoint — set `FINGPT_ENDPOINT` (and `FINGPT_API_KEY`)
  or run `login`. Until then the rest of the terminal works normally.
- **Name resolution:** best-effort via Yahoo search. Mega-caps resolve reliably;
  ambiguous one-word names may pick a look-alike — use the exact symbol.
- **`ask` answers:** only as good as the connectors. Verify anything you'd trade
  on against the raw verb output.
