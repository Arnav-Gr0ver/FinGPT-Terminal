"""Auth — API key and endpoint management for the FinR1 Terminal AI layer."""

import os
import json
from pathlib import Path
from src.display import console, print_success, print_error, print_warning

CONFIG_DIR  = Path.home() / ".fingpt"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _read_config() -> dict:
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _write_config(updates: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = _read_config()
    data.update(updates)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_api_key() -> str:
    # Env var wins, so CI / power users don't have to run `login`.
    return os.environ.get("FINGPT_API_KEY", "").strip() or _read_config().get("api_key", "")


def get_endpoint() -> str:
    """AI endpoint URL, from FINGPT_ENDPOINT env var or saved config. Empty if unconfigured."""
    return os.environ.get("FINGPT_ENDPOINT", "").strip() or _read_config().get("endpoint", "").strip()


def save_api_key(key: str):
    _write_config({"api_key": key})


def save_endpoint(url: str):
    _write_config({"endpoint": url})


def run_login():
    console.print()
    console.print(f"  [bold #e05c4b]FinR1 Terminal — Login[/]")
    console.print("  [#555555]Get your API key at [/][white]fingpt.ai/dashboard[/]\n")
    key = console.input("  [bold #e8e8e8]API Key → [/]").strip()
    if not key:
        print_error("No key entered. Login cancelled.")
        return
    save_api_key(key)

    # Endpoint is optional — only prompt if not already set via env or config.
    if not get_endpoint():
        console.print(
            "\n  [#555555]Optional: AI endpoint URL (OpenAI-compatible). "
            "Leave blank to set later via [/][white]FINGPT_ENDPOINT[/][#555555].[/]"
        )
        endpoint = console.input("  [bold #e8e8e8]Endpoint → [/]").strip()
        if endpoint:
            save_endpoint(endpoint)

    print_success("Credentials saved. AI features are enabled once an endpoint is configured.")


def require_auth() -> str:
    key = get_api_key()
    if not key:
        print_warning("No API key found. Run 'login' to enable AI features.")
        run_login()
        key = get_api_key()
    if not key:
        raise RuntimeError("Authentication required to use AI features.")
    return key
