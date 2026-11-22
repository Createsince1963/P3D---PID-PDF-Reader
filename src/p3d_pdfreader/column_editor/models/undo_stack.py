"""Small undo / redo stack (pure Python, no Qt): one command per user action (planning basis, section 15)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Command:
    text: str
    redo: Callable[[], None]
    undo: Callable[[], None]


class UndoStack:
    def __init__(self, limit: int = 200):
        self._done: list[Command] = []
        self._undone: list[Command] = []
        self._limit = limit

    def push(self, cmd: Command, *, execute: bool = True) -> None:
        if execute:
            cmd.redo()
        self._done.append(cmd)
        del self._done[: max(0, len(self._done) - self._limit)]
        self._undone.clear()

    def can_undo(self) -> bool:
        return bool(self._done)

    def can_redo(self) -> bool:
        return bool(self._undone)

    def undo_text(self) -> str:
        return self._done[-1].text if self._done else ""

    def redo_text(self) -> str:
        return self._undone[-1].text if self._undone else ""

    def undo(self) -> bool:
        if not self._done:
            return False
        cmd = self._done.pop()
        cmd.undo()
        self._undone.append(cmd)
        return True

    def redo(self) -> bool:
        if not self._undone:
            return False
        cmd = self._undone.pop()
        cmd.redo()
        self._done.append(cmd)
        return True

    def clear(self) -> None:
        self._done.clear()
        self._undone.clear()
