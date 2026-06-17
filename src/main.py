"""fin — a financial terminal driven by one grammar: subject, then verbs."""

import sys
from datetime import datetime
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from rich.console import Console

from src.display import print_banner, print_error
from src.context import ctx
from src.router import route

# Nothing is persisted across sessions. Command history lives in memory only
# (up-arrow works this session, then it's gone). Remove any history file an
# earlier build left behind so old commands never resurface.
_old_history = Path.home() / ".fingpt" / "history"
try:
    _old_history.unlink(missing_ok=True)
except Exception:
    pass

console = Console()

PROMPT_STYLE = Style.from_dict({
    "prompt.time":    "#444444",
    "prompt.bracket": "#555555",
    "prompt.app":     "bold #e05c4b",
    "prompt.subject": "bold #e8e8e8",
    "prompt.arrow":   "#555555",
})


def _prompt_message():
    parts = [
        ("class:prompt.time",    datetime.now().strftime("%H:%M:%S") + " "),
        ("class:prompt.bracket", "<"),
        ("class:prompt.app",     "FinGPT Terminal"),
    ]
    if ctx.prompt_label:
        parts.append(("class:prompt.subject", f" {ctx.prompt_label}"))
    parts.append(("class:prompt.bracket", ">"))
    parts.append(("class:prompt.arrow", " "))
    return parts


def main():
    print_banner()
    # No tab-completion or ghost-text hinting — the grammar is small enough to
    # type. History is in-memory only (up-arrow within this session, never saved).
    session = PromptSession(
        history=InMemoryHistory(),
        style=PROMPT_STYLE,
    )
    while True:
        try:
            raw = session.prompt(_prompt_message).strip()
            if not raw:
                continue
            route(raw)
        except SystemExit:
            console.print("\n  [bold #e05c4b]Goodbye.[/]\n")
            sys.exit(0)
        except KeyboardInterrupt:
            console.print("\n  [#555555]Type 'exit' or Ctrl+D to quit.[/]")
            continue
        except EOFError:
            console.print("\n  [bold #e05c4b]Goodbye.[/]\n")
            sys.exit(0)
        except Exception as e:
            print_error(str(e))
            continue


if __name__ == "__main__":
    main()
