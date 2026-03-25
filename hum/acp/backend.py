import os
from contextlib import asynccontextmanager

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.core import ClientSideConnection

from ..backend import BackendResponse
from .client import HumACPClient, _CLIENT_CAPABILITIES, _CLIENT_INFO


class ACPBackend:
    """Backend that keeps a single ACP agent process alive for its lifetime."""

    def __init__(self, command: list[str]):
        self._command = command
        self._client: HumACPClient | None = None
        self._conn: ClientSideConnection | None = None
        self._session_id: str | None = None
        self._exit_stack = None

    async def start(self) -> None:
        """Spawn the agent process and open a session. Call once before run()."""
        self._client = HumACPClient()
        self._exit_stack = spawn_agent_process(self._client, *self._command)
        conn, _proc = await self._exit_stack.__aenter__()
        self._conn = conn

        await conn.initialize(
            protocol_version=PROTOCOL_VERSION,
            client_capabilities=_CLIENT_CAPABILITIES,
            client_info=_CLIENT_INFO,
        )
        session = await conn.new_session(cwd=os.getcwd(), mcp_servers=[])
        self._session_id = session.session_id

    async def stop(self) -> None:
        """Terminate the agent process."""
        if self._exit_stack is not None:
            await self._exit_stack.__aexit__(None, None, None)
            self._exit_stack = None
            self._conn = None
            self._session_id = None

    async def run(self, system: str, prompt: str, notes: str) -> BackendResponse:
        if self._conn is None or self._session_id is None:
            raise RuntimeError("ACPBackend not started — call start() first")

        full_prompt = f"[context]\n{notes}\n\n{prompt}" if notes.strip() else prompt

        self._client._chunks.clear()
        await self._conn.prompt(
            session_id=self._session_id,
            prompt=[text_block(full_prompt)],
        )

        return BackendResponse(text=self._client.get_text(), notes=None)


@asynccontextmanager
async def acp_backend(command: list[str]):
    """Async context manager that starts and stops an ACPBackend."""
    backend = ACPBackend(command)
    await backend.start()
    try:
        yield backend
    finally:
        await backend.stop()
