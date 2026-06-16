"""Router — dispatches input based on current navigation context."""

from src.context import ctx
from src.display import print_error, print_home, console

GLOBAL_COMMANDS = {
    "home":  "Return to the main menu",
    "menu":  "Show the current menu",
    "..":    "Go up one level",
    "back":  "Go up one level",
    "login": "Set your FinGPT Terminal API key",
    "help":  "Show available global commands",
    "clear": "Clear the screen",
    "exit":  "Quit FinGPT Terminal",
    "quit":  "Quit FinGPT Terminal",
}

TOP_LEVEL = {"stocks", "crypto", "macro", "forex", "etf", "news", "portfolio", "ai"}


def route(raw: str):
    parts = raw.strip().split(maxsplit=1)
    cmd   = parts[0].lower()
    args  = parts[1] if len(parts) > 1 else ""

    if cmd in ("exit", "quit"):
        raise SystemExit(0)

    if cmd == "clear":
        console.clear()
        return

    if cmd == "home":
        ctx.home()
        print_home()
        return

    if cmd in ("..", "back"):
        if ctx.ai_mode:
            ctx.exit_ai()
        elif ctx.depth > 0:
            ctx.back()
        _show_current_menu()
        return

    if cmd == "menu":
        _show_current_menu()
        return

    if cmd == "help":
        _print_help()
        return

    if cmd == "login":
        from src.auth import run_login
        run_login()
        return

    if cmd == "ai" and not ctx.ai_mode:
        ctx.enter_ai()
        from src.agent import print_ai_welcome
        print_ai_welcome()
        return

    if ctx.ai_mode:
        if cmd in ("exit", "back"):
            ctx.exit_ai()
            _show_current_menu()
            return
        from src.agent import chat
        chat(raw)
        return

    if ctx.depth == 0:
        _route_home(cmd, args)
    elif ctx.depth == 1:
        _route_section(ctx.current, cmd, args)
    else:
        _route_deep(ctx.path, cmd, args)


def _route_home(cmd: str, args: str):
    if cmd in TOP_LEVEL:
        ctx.enter(cmd)
        _show_current_menu()
    else:
        print_error(f"Unknown command '{cmd}'. Type 'menu' to see options.")


def _route_section(section: str, cmd: str, args: str):
    from src.menus import MENU_TREE, run_command
    tree = MENU_TREE.get(section, {})
    if cmd in tree.get("submenus", {}):
        ctx.enter(cmd)
        _show_current_menu()
        return
    if cmd in tree.get("commands", {}):
        run_command(section, cmd, args)
        return
    print_error(f"Unknown command '{cmd}' in {section}. Type 'menu' to see options.")


def _route_deep(path: list, cmd: str, args: str):
    from src.menus import MENU_TREE, run_command
    section = path[0]
    subsect = path[1]
    subtree = MENU_TREE.get(section, {}).get("submenus", {}).get(subsect, {})
    if cmd in subtree.get("commands", {}):
        run_command(f"{section}/{subsect}", cmd, args)
        return
    print_error(f"Unknown command '{cmd}'. Type 'menu' to see options.")


def _show_current_menu():
    if ctx.ai_mode:
        return
    if ctx.depth == 0:
        print_home()
        return
    from src.menus import MENU_TREE
    from src.display import print_menu
    section = ctx.path[0]
    tree    = MENU_TREE.get(section, {})
    if ctx.depth == 1:
        items = []
        for name, meta in tree.get("submenus", {}).items():
            items.append((name, meta.get("desc", "") if isinstance(meta, dict) else meta))
        for name, desc in tree.get("commands", {}).items():
            items.append((name, desc))
        print_menu(f"FinGPT Terminal  ›  {section.upper()}", items)
    elif ctx.depth == 2:
        subsect = ctx.path[1]
        subtree = tree.get("submenus", {}).get(subsect, {})
        items   = list(subtree.get("commands", {}).items())
        print_menu(f"FinGPT Terminal  ›  {section.upper()}  ›  {subsect.upper()}", items)


def _print_help():
    from src.display import print_menu
    print_menu("FinGPT Terminal  —  Global Commands", list(GLOBAL_COMMANDS.items()))