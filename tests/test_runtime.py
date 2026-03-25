"""Runtime integration tests — HTTP port messaging.

Run with:
    hatch run pytest tests/test_runtime.py -v -s
"""

import asyncio
import contextlib
import shutil

import aiohttp
import pytest

from hum.acp.backend import ACPBackend
from hum.backend import BackendResponse
from hum.registry import AgentConfig
from hum.runtime import Runtime

SYSTEM = "You are a helpful assistant. Be extremely brief."
COMMAND = ["claude-agent-acp"]
HTTP_PORT = 18_765

pytestmark = pytest.mark.skipif(
    not shutil.which("claude-agent-acp"), reason="claude-agent-acp not found in PATH"
)


# ── helpers ───────────────────────────────────────────────────────────────────


class StubBackend:
    """Fake backend that returns a fixed response without spawning a process."""

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def run(self, system: str, prompt: str, notes: str) -> BackendResponse:
        return BackendResponse(text="stub response")


async def wait_for_port(port: int, retries: int = 20, delay: float = 0.5) -> None:
    for _ in range(retries):
        try:
            reader, writer = await asyncio.open_connection("localhost", port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError:
            await asyncio.sleep(delay)
    raise TimeoutError(f"port {port} did not open after {retries * delay}s")


def make_config(tmp_path) -> AgentConfig:
    return AgentConfig(
        name="test-runtime",
        system=SYSTEM,
        command=COMMAND,
        notes_path=str(tmp_path / "notes.md"),
        port=HTTP_PORT,
    )


async def start_runtime(config, backend):
    task = asyncio.create_task(Runtime(config, backend).start())
    await wait_for_port(HTTP_PORT)
    return task


async def stop_runtime(task):
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


# ── tests ─────────────────────────────────────────────────────────────────────


async def test_runtime_http(tmp_path):
    """Full round-trip through the real ACP backend."""
    config = make_config(tmp_path)
    task = await start_runtime(config, ACPBackend(config.command))
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"http://localhost:{HTTP_PORT}/message",
                json={"message": "Reply with exactly the word: pong"},
            )
            assert resp.status == 200
            data = await resp.json()
        print(f"\n[http] → {data['response']!r}")
        assert data["response"].strip()
    finally:
        await stop_runtime(task)


async def test_runtime_http_missing_message(tmp_path):
    """400 is returned by the runtime before the backend is called."""
    config = make_config(tmp_path)
    task = await start_runtime(config, StubBackend())
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"http://localhost:{HTTP_PORT}/message",
                json={},
            )
            assert resp.status == 400
    finally:
        await stop_runtime(task)
