import asyncio
import json
from pathlib import Path

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

DEFAULT_CHATS_FILE = Path.home() / ".hum" / "telegram_chats.json"


class TelegramChannel:
    def __init__(self, config: dict) -> None:
        token = config.get("token")
        if not token:
            raise ValueError("telegram channel requires a 'token' field")
        self._token: str = token
        self._chats_file = Path(config.get("chats_file", DEFAULT_CHATS_FILE))
        self._queue: asyncio.Queue = asyncio.Queue()
        self._pending_update: Update | None = None
        self._known_chats: set[int] = self._load_chats()
        self._app: Application | None = None

    def _load_chats(self) -> set[int]:
        if not self._chats_file.exists():
            return set()
        return set(json.loads(self._chats_file.read_text()))

    def _save_chats(self) -> None:
        self._chats_file.parent.mkdir(parents=True, exist_ok=True)
        self._chats_file.write_text(json.dumps(list(self._known_chats)))

    async def connect(self) -> None:
        async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if update.message and update.message.text:
                chat_id = update.message.chat_id
                if chat_id not in self._known_chats:
                    self._known_chats.add(chat_id)
                    self._save_chats()
                await self._queue.put((update, update.message.text))

        self._app = Application.builder().token(self._token).build()
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()
        print(f"[hum] telegram channel ready ({len(self._known_chats)} known chats)")

    async def receive(self) -> str:
        update, message = await self._queue.get()
        self._pending_update = update
        return message

    async def send(self, reply: str) -> None:
        if self._pending_update is not None:
            await self._pending_update.message.reply_text(reply)
            self._pending_update = None
        else:
            for chat_id in self._known_chats:
                await self._app.bot.send_message(chat_id=chat_id, text=reply)

    async def close(self) -> None:
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
            self._app = None
