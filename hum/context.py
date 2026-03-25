from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .backend import Backend
    from .notes import Notes


class Context:
    def __init__(self, system: str, notes: "Notes", backend: "Backend"):
        self._system = system
        self._notes = notes
        self._backend = backend

    @property
    def notes(self) -> str:
        return self._notes.content

    @notes.setter
    def notes(self, value: str) -> None:
        self._notes.content = value

    async def run(self, prompt: str) -> str:
        response = await self._backend.run(self._system, prompt, self._notes.content)
        if response.notes is not None:
            self._notes.content = response.notes
        return response.text
