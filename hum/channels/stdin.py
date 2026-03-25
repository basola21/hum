import asyncio
import sys


class StdinChannel:
    def __init__(self, config: dict) -> None:
        pass

    async def connect(self) -> None:
        print("[hum] stdin channel ready — type a message and press Enter")

    async def receive(self) -> str:
        loop = asyncio.get_event_loop()
        while True:
            line: str = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                raise EOFError("stdin closed")
            message = line.rstrip("\n")
            if message:
                return message

    async def send(self, reply: str) -> None:
        print(reply)

    async def close(self) -> None:
        pass
