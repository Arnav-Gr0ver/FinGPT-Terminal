"""Menu tree — defines the full navigation structure and command registry."""

from src.display import print_error

MENU_TREE: dict = {
    "stocks": {
        "submenus": {
            "fa": {
                "desc": "Fundamental analysis — earnings, ratios, filings",
                "commands": {
                    "income":   "Income statement (annual & quarterly)",
                    "balance":  "Balance sheet",
                    "cash":     "Cash flow statement",
                    "ratios":   "Key financial ratios",
                    "earnings": "Earnings history and estimates",
                    "dcf":      "Discounted cash flow valuation",
                },
            },
            "ta": {
                "desc": "Technical analysis — indicators, patterns",
                "commands": {
                    "sma":      "Simple moving averages",
                    "ema":      "Exponential moving averages",
                    "rsi":      "Relative strength index",
                    "macd":     "MACD indicator",
                    "bb":       "Bollinger bands",
                    "patterns": "Candlestick pattern detection",
                },
            },
            "dps": {
                "desc": "Dark pool and short data",
                "commands": {
                    "short": "Short interest and days to cover",
                    "dp":    "Dark pool levels",
                    "ftd":   "Failure to deliver data",
                },
            },
            "gov": {
                "desc": "Government and insider data",
                "commands": {
                    "insider":  "Insider transactions",
                    "congress": "Congressional trading disclosures",
                    "lobbying": "Lobbying spend data",
                },
            },
        },
        "commands": {
            "load":    "Load a ticker  e.g. load AAPL",
            "quote":   "Live quote for loaded ticker",
            "chart":   "Price chart for loaded ticker",
            "news":    "Latest news for loaded ticker",
            "similar": "Find similar companies",
            "screen":  "Stock screener",
        },
    },
    "crypto": {
        "submenus": {
            "onchain": {
                "desc": "On-chain analytics — addresses, flows, whale activity",
                "commands": {
                    "whales": "Large wallet movements",
                    "flows":  "Exchange inflows and outflows",
                    "active": "Active address count",
                },
            },
            "defi": {
                "desc": "DeFi — protocols, TVL, yields",
                "commands": {
                    "tvl":    "Total value locked by protocol",
                    "yields": "Top yield opportunities",
                    "pools":  "Liquidity pool data",
                },
            },
        },
        "commands": {
            "load":  "Load a crypto symbol  e.g. load BTC",
            "quote": "Live price for loaded symbol",
            "chart": "Price chart",
            "news":  "Latest crypto news",
            "top":   "Top coins by market cap",
        },
    },
    "macro": {
        "submenus": {},
        "commands": {
            "rates":     "Central bank interest rates",
            "inflation": "CPI and inflation data by country",
            "gdp":       "GDP growth by country",
            "yield":     "Government bond yield curves",
            "calendar":  "Upcoming economic events",
            "fear":      "Fear and greed index",
        },
    },
    "forex": {
        "submenus": {},
        "commands": {
            "load":  "Load a pair  e.g. load EUR/USD",
            "quote": "Live rate for loaded pair",
            "chart": "Rate chart",
            "rates": "All major pair rates",
            "carry": "Carry trade data",
        },
    },
    "etf": {
        "submenus": {},
        "commands": {
            "load":     "Load an ETF  e.g. load SPY",
            "quote":    "Live quote",
            "holdings": "Top holdings",
            "flows":    "Fund flow data",
            "compare":  "Compare ETFs  e.g. compare SPY QQQ",
        },
    },
    "news": {
        "submenus": {},
        "commands": {
            "latest":    "Latest financial headlines",
            "search":    "Search news  e.g. search NVDA earnings",
            "sentiment": "Sentiment score for a ticker or topic",
        },
    },
    "portfolio": {
        "submenus": {},
        "commands": {
            "add":    "Add a position  e.g. add AAPL 10 150.00",
            "remove": "Remove a position  e.g. remove AAPL",
            "show":   "Show current portfolio",
            "pnl":    "P&L summary with live prices",
            "risk":   "Risk metrics — VaR, Sharpe, beta",
            "alloc":  "Allocation breakdown by weight",
        },
    },
}


def run_command(path: str, cmd: str, args: str):
    try:
        if path == "stocks":
            from src.commands.stocks import handle
        elif path == "stocks/fa":
            from src.commands.stocks_fa import handle
        elif path == "stocks/ta":
            from src.commands.stocks_ta import handle
        elif path == "stocks/dps":
            from src.commands.stocks_dps import handle
        elif path == "stocks/gov":
            from src.commands.stocks_gov import handle
        elif path == "crypto":
            from src.commands.crypto import handle
        elif path == "macro":
            from src.commands.macro import handle
        elif path == "forex":
            from src.commands.forex import handle
        elif path == "etf":
            from src.commands.etf import handle
        elif path == "news":
            from src.commands.news import handle
        elif path == "portfolio":
            from src.commands.portfolio import handle
        else:
            print_error(f"No handler registered for path '{path}'.")
            return
        handle(cmd, args)
    except NotImplementedError:
        from src.display import print_warning
        print_warning(f"'{cmd}' is not yet implemented.")