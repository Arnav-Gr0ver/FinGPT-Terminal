"""FinGPT Terminal — main entry point."""

import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from rich.console import Console

from src.display import print_banner, print_home, print_error
from src.context import ctx
from src.router import route, TOP_LEVEL, GLOBAL_COMMANDS
from src.menus import MENU_TREE

HISTORY_FILE = ".fingpt_history"
console      = Console()

PROMPT_STYLE = Style.from_dict({
    "prompt.bracket": "#555555",
    "prompt.app":     "bold #00d4aa",
    "prompt.path":    "#0066ff",
    "prompt.arrow":   "#555555",
})


def _build_completer() -> WordCompleter:
    words = set(TOP_LEVEL) | set(GLOBAL_COMMANDS.keys())
    for section, tree in MENU_TREE.items():
        for sub in tree.get("submenus", {}).keys():
            words.add(sub)
        for cmd in tree.get("commands", {}).keys():
            words.add(cmd)
        for subtree in tree.get("submenus", {}).values():
            if isinstance(subtree, dict):
                for cmd in subtree.get("commands", {}).keys():
                    words.add(cmd)
    return WordCompleter(sorted(words), ignore_case=True)


def _prompt_message():
    path = ctx.prompt_path
    if path:
        return [
            ("class:prompt.bracket", "("),
            ("class:prompt.app",     "FinGPT Terminal"),
            ("class:prompt.bracket", ") ["),
            ("class:prompt.path",    path),
            ("class:prompt.bracket", "]"),
            ("class:prompt.arrow",   " > "),
        ]
    return [
        ("class:prompt.bracket", "("),
        ("class:prompt.app",     "FinGPT Terminal"),
        ("class:prompt.bracket", ")"),
        ("class:prompt.arrow",   " > "),
    ]


def main():
    print_banner()
    print_home()

    session = PromptSession(
        history=FileHistory(HISTORY_FILE),
        auto_suggest=AutoSuggestFromHistory(),
        completer=_build_completer(),
        complete_while_typing=False,
        style=PROMPT_STYLE,
    )

    while True:
        try:
            raw = session.prompt(_prompt_message).strip()
            if not raw:
                continue
            route(raw)
        except SystemExit:
            console.print("\n  [bold #00d4aa]FinGPT Terminal — Goodbye.[/]\n")
            sys.exit(0)
        except KeyboardInterrupt:
            console.print("\n  [#555555]Use 'exit' or Ctrl+D to quit.[/]")
            continue
        except EOFError:
            console.print("\n  [bold #00d4aa]FinGPT Terminal — Goodbye.[/]\n")
            sys.exit(0)
        except Exception as e:
            print_error(str(e))
            continue


if __name__ == "__main__":
    main()