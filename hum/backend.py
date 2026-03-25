from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class BackendResponse:
    text: str
    notes: str | None = None


@runtime_checkable
class Backend(Protocol):
    async def run(self, system: str, prompt: str, notes: str) -> BackendResponse:
        ...
