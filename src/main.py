"""fin — a financial terminal driven by one grammar: subject, then verbs."""

import sys
import threading
from datetime import datetime
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console

from src.display import print_banner, print_error
from src.context import ctx
from src.router import route
from src.completion import GrammarCompleter, toolbar_fragments
from src.data import symbol_index

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
    "bottom-toolbar": "bg:#262626",
    "tb.pad":    "bg:#262626",
    "tb.loaded": "bold #141414 bg:#9aa0a6",
    "tb.key":    "bold #141414 bg:#e05c4b",
    "tb.eg":     "#cfcfcf bg:#262626",
    # Completion menu — high-contrast, no hard-to-read blue.
    "completion-menu":                       "bg:#1c1c1c",
    "completion-menu.completion":            "bg:#1c1c1c #d0d0d0",
    "completion-menu.completion.current":    "bg:#e05c4b #141414",
    "completion-menu.meta.completion":         "bg:#1c1c1c #6f6f6f",
    "completion-menu.meta.completion.current": "bg:#c0463a #141414",
    "scrollbar.background": "bg:#303030",
    "scrollbar.button":     "bg:#666666",
})


_kb = KeyBindings()


@_kb.add("enter")
def _(event):
    """Enter accepts a highlighted completion (if any) and runs the line. Submitting
    tears down the menu, so the dropdown always closes. Use Tab to accept a
    completion *without* running, to keep typing the chain."""
    buff = event.current_buffer
    state = buff.complete_state
    if state is not None and state.current_completion is not None:
        buff.apply_completion(state.current_completion)
    buff.complete_state = None
    buff.validate_and_handle()


def _toolbar():
    try:
        text = get_app().current_buffer.document.text_before_cursor
    except Exception:
        text = ""
    return toolbar_fragments(text)


def _prompt_message():
    from src.display import KIND_COLORS
    parts = [("fg:#555555", "<"), ("fg:#e05c4b bold", "FinR1 Terminal")]
    if ctx.subjects:
        color = KIND_COLORS.get(ctx.subjects[0].kind, "#e8e8e8")
        parts.append(("fg:#6b7280", " "))
        parts.append((f"fg:{color} bold", ctx.prompt_label or ""))
    parts.append(("fg:#555555", ">"))
    parts.append(("fg:#6b7280", "  ❯ "))
    return parts


def _rprompt():
    from datetime import time as _time
    try:
        from zoneinfo import ZoneInfo
        et = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        et = datetime.now()
    is_open = et.weekday() < 5 and _time(9, 30) <= et.time() < _time(16, 0)
    dot = "fg:#2ecc71" if is_open else "fg:#6b7280"
    label = "NYSE open" if is_open else "NYSE closed"
    return [(dot, "● "), ("fg:#6b7280", f"{label}   {datetime.now().strftime('%H:%M')}")]


def main():
    print_banner()
    # Build the symbol index in the background so completion is ready quickly
    # without blocking startup.
    threading.Thread(target=symbol_index.ensure_index, daemon=True).start()
    # Grammar-aware completion: as you type, it suggests the right token type
    # (subject / verb / range / screen). History is in-memory only.
    session = PromptSession(
        history=InMemoryHistory(),
        completer=GrammarCompleter(),
        complete_while_typing=True,
        key_bindings=_kb,
        style=PROMPT_STYLE,
    )
    while True:
        try:
            raw = session.prompt(_prompt_message, rprompt=_rprompt).strip()
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
