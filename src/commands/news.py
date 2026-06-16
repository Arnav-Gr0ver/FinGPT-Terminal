"""News section commands."""

from src.display import print_error, print_table, print_warning


def handle(cmd: str, args: str):
    if cmd == "latest":
        _latest()
    elif cmd == "search":
        if not args:
            print_error("Usage: search <query>  e.g. search NVDA earnings")
            return
        _search(args)
    elif cmd == "sentiment":
        raise NotImplementedError
    else:
        print_error(f"Unknown news command '{cmd}'.")


def _latest():
    try:
        import yfinance as yf
        news = yf.Ticker("^GSPC").news[:10]
        _print_news(news, "FinGPT Terminal  ›  News  ›  Latest Headlines")
    except Exception as e:
        print_error(f"Could not fetch news: {e}")


def _search(query: str):
    try:
        import yfinance as yf
        news = yf.Ticker(query.upper()).news[:10]
        if not news:
            print_warning(f"No news found for '{query}'.")
            return
        _print_news(news, f"FinGPT Terminal  ›  News  ›  {query.upper()}")
    except Exception as e:
        print_error(f"Could not fetch news for '{query}': {e}")


def _print_news(articles: list, title: str):
    if not articles:
        print_warning("No articles found.")
        return
    rows = [
        [a.get("publisher", "")[:20], a.get("title", "")[:72]]
        for a in articles
    ]
    print_table(title, ["Source", "Headline"], rows)