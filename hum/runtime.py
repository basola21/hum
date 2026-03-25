import asyncio
import json
from pathlib import Path

from aiohttp import web

from .context import Context
from .heartbeat import parse_interval
from .notes import Notes
from .registry import AgentConfig


class Runtime:
    def __init__(self, config: AgentConfig, backend):
        self._config = config
        self._backend = backend
        self._notes = Notes(Path(config.notes_path))

    def _make_ctx(self) -> Context:
        return Context(self._config.system, self._notes, self._backend)

    async def start(self):
        print("[hum] agent started")

        await self._backend.start()

        tasks = []

        if self._config.heartbeat_every:
            print(f"[hum] heartbeat: {self._config.heartbeat_every}")
            tasks.append(self._heartbeat_loop())

        if not self._config.port:
            raise ValueError("port is required — set 'port' in your agent YAML")

        print(f"[hum] listening on http://localhost:{self._config.port}")
        tasks.append(self._http_server())

        try:
            await asyncio.gather(*tasks)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n[hum] stopping")
        finally:
            await self._backend.stop()

    async def _heartbeat_loop(self):
        prompt_template = self._config.heartbeat_prompt or "Check in."
        seconds = parse_interval(self._config.heartbeat_every)

        while True:
            ctx = self._make_ctx()
            notes = ctx.notes or ""
            await ctx.run(prompt_template.format(notes=notes))
            await asyncio.sleep(seconds)

    async def _handle_message(self, raw: str) -> str:
        ctx = self._make_ctx()
        return await ctx.run(raw)

    async def _http_server(self):
        async def handle(request: web.Request) -> web.Response:
            try:
                body = await request.json()
                message = body.get("message", "")
                if not message:
                    return web.Response(status=400, text="missing 'message' field")
                response = await self._handle_message(message)
                return web.Response(
                    content_type="application/json",
                    text=json.dumps({"response": response}),
                )
            except Exception as e:
                return web.Response(status=500, text=str(e))

        app = web.Application()
        app.router.add_post("/message", handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self._config.port, reuse_address=True)
        await site.start()
        try:
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()
