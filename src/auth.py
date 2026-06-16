"""Auth — API key management for FinGPT Terminal Modal endpoint."""

import json
from pathlib import Path

from src.display import console, print_success, print_error, print_warning

CONFIG_DIR  = Path.home() / ".fingpt"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_api_key() -> str | None:
    try:
        if not CONFIG_FILE.exists():
            return None
        with open(CONFIG_FILE) as f:
            return json.load(f).get("api_key")
    except Exception:
        return None


def save_api_key(key: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    data["api_key"] = key
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def run_login():
    console.print()
    console.print("  [bold #00d4aa]FinGPT Terminal — Login[/]")
    console.print("  [#555555]Get your API key at [/][white]fingpt.ai/dashboard[/]\n")
    key = console.input("  [bold #e8e8e8]API Key → [/]").strip()
    if not key:
        print_error("No key entered. Login cancelled.")
        return
    save_api_key(key)
    print_success("API key saved. AI features are now enabled.")


def require_auth() -> str:
    key = get_api_key()
    if not key:
        print_warning("No API key found. Run 'login' to enable AI features.")
        run_login()
        key = get_api_key()
    if not key:
        raise RuntimeError("Authentication required to use AI features.")
    return key


def is_authenticated() -> bool:
    return bool(get_api_key())