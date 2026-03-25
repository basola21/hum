import asyncio
from pathlib import Path

from .channel import Channel
from .channels import build_channel
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

    async def _run_channel(self, channel: Channel) -> None:
        await channel.connect()
        try:
            while True:
                message = await channel.receive()
                reply = await self._handle_message(message)
                await channel.send(reply)
        finally:
            await channel.close()

    async def start(self):
        print("[hum] agent started")

        await self._backend.start()

        channels = [build_channel(entry) for entry in self._config.channels]
        if not channels:
            raise ValueError(
                "no channels configured — add a 'channels:' block or set 'port:' in your agent YAML"
            )

        tasks = [self._run_channel(c) for c in channels]

        if self._config.heartbeat_every:
            print(f"[hum] heartbeat: {self._config.heartbeat_every}")
            tasks.append(self._heartbeat_loop(channels))

        try:
            await asyncio.gather(*tasks)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n[hum] stopping")
        finally:
            await self._backend.stop()

    async def _heartbeat_loop(self, channels: list[Channel]) -> None:
        prompt_template = self._config.heartbeat_prompt or "Check in."
        seconds = parse_interval(self._config.heartbeat_every)

        while True:
            ctx = self._make_ctx()
            notes = ctx.notes or ""
            reply = await ctx.run(prompt_template.format(notes=notes))
            for channel in channels:
                await channel.send(reply)

            await asyncio.sleep(seconds)

    async def _handle_message(self, raw: str) -> str:
        ctx = self._make_ctx()
        return await ctx.run(raw)
