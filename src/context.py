"""Context — tracks the user's current position in the menu tree."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Context:
    path: list[str]            = field(default_factory=list)
    ai_mode: bool              = False
    _ai_return_path: list[str] = field(default_factory=list)

    def enter(self, name: str):
        self.path.append(name)

    def back(self):
        if self.path:
            self.path.pop()

    def home(self):
        self.path    = []
        self.ai_mode = False

    def enter_ai(self):
        self._ai_return_path = list(self.path)
        self.ai_mode         = True

    def exit_ai(self):
        self.path    = list(self._ai_return_path)
        self.ai_mode = False

    @property
    def prompt_path(self) -> str:
        if self.ai_mode:
            return "ai"
        return "/".join(self.path) if self.path else ""

    @property
    def current(self) -> Optional[str]:
        return self.path[-1] if self.path else None

    @property
    def depth(self) -> int:
        return len(self.path)

    def __repr__(self):
        return f"Context(path={self.path}, ai_mode={self.ai_mode})"


ctx = Context()