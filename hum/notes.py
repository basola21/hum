from pathlib import Path

DEFAULT_PATH = Path("heartbeat.md")


class Notes:
    def __init__(self, path: Path = DEFAULT_PATH):
        self._path = path

    def read(self) -> str:
        if not self._path.exists():
            return ""
        return self._path.read_text()

    def write(self, content: str) -> None:
        self._path.write_text(content)

    @property
    def content(self) -> str:
        return self.read()

    @content.setter
    def content(self, value: str) -> None:
        self.write(value)
