"""AI agent — chat mode connected to FinGPT Terminal Modal endpoint."""

import requests
from src.display import console, print_error
from src.auth import require_auth

_history: list[dict] = []
MODAL_ENDPOINT = "https://your-modal-endpoint.modal.run/v1/chat"  # TODO


def print_ai_welcome():
    console.print()
    console.print("  [bold #00d4aa]FinGPT Terminal — AI Mode[/]")
    console.print("  [#555555]Type naturally to chat with the AI analyst.[/]")
    console.print("  [#555555]Type [/][white]back[/][#555555] to return to the terminal.[/]")
    console.print()


def chat(message: str):
    try:
        key = require_auth()
    except RuntimeError:
        return

    _history.append({"role": "user", "content": message})
    console.print()
    console.print("  [bold #00d4aa]FinGPT Terminal[/] ", end="")

    try:
        response = requests.post(
            MODAL_ENDPOINT,
            json={"messages": _history},
            headers={"Authorization": f"Bearer {key}"},
            timeout=30,
            stream=True,
        )
        response.raise_for_status()

        full_reply = ""
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                text        = chunk.decode("utf-8")
                full_reply += text
                console.print(text, end="")

        console.print()
        console.print()
        _history.append({"role": "assistant", "content": full_reply})

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to FinGPT Terminal endpoint.")
        _history.pop()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print_error("Invalid API key. Run 'login' to update it.")
        else:
            print_error(f"API error: {e}")
        _history.pop()
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        _history.pop()


def clear_history():
    global _history
    _history = []