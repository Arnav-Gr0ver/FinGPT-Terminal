"""Context — tracks navigation state and loaded instruments."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Context:
    path: list[str]      = field(default_factory=list)
    _ticker: str | None  = None

    def enter(self, name: str):
        self.path.append(name)

    def back(self):
        if self.path:
            self.path.pop()

    def home(self):
        self.path = []

    def set_ticker(self, ticker: str):
        self._ticker = ticker.upper().strip()

    def get_ticker(self) -> str | None:
        return self._ticker

    def clear_ticker(self):
        self._ticker = None

    @property
    def prompt_path(self) -> str:
        return "/".join(self.path) if self.path else ""

    @property
    def prompt_ticker(self) -> str | None:
        return self._ticker

    @property
    def current(self) -> Optional[str]:
        return self.path[-1] if self.path else None

    @property
    def depth(self) -> int:
        return len(self.path)


ctx = Context()