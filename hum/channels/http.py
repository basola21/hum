import asyncio
import json

from aiohttp import web


class HttpChannel:
    def __init__(self, config: dict) -> None:
        port = config.get("port")
        if not port:
            raise ValueError("http channel requires a 'port' field")
        self._port: int = port
        self._queue: asyncio.Queue = asyncio.Queue()
        self._pending: tuple[str, asyncio.Future] | None = None
        self._runner: web.AppRunner | None = None

    async def connect(self) -> None:
        async def handle(request: web.Request) -> web.Response:
            try:
                body = await request.json()
            except Exception:
                return web.Response(status=400, text="invalid JSON body")
            message = body.get("message", "")
            if not message:
                return web.Response(status=400, text="missing 'message' field")
            future: asyncio.Future = asyncio.get_event_loop().create_future()
            await self._queue.put((message, future))
            reply = await future
            return web.Response(
                content_type="application/json",
                text=json.dumps({"response": reply}),
            )

        app = web.Application()
        app.router.add_post("/message", handle)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "localhost", self._port, reuse_address=True)
        await site.start()
        print(f"[hum] listening on http://localhost:{self._port}")

    async def receive(self) -> str:
        self._pending = await self._queue.get()
        return self._pending[0]

    async def send(self, reply: str) -> None:
        if self._pending is None:
            return  # no active request — heartbeat push not supported over HTTP
        self._pending[1].set_result(reply)
        self._pending = None

    async def close(self) -> None:
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
