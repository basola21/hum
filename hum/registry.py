import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HUM_DIR = Path.home() / ".hum"
AGENTS_FILE = HUM_DIR / "agents.json"


@dataclass
class AgentConfig:
    name: str
    system: str
    command: list[str]
    notes_path: str = ""
    port: int | None = None
    channels: list[dict] = field(default_factory=list)
    description: str = ""
    heartbeat_every: str = ""
    heartbeat_prompt: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.notes_path:
            self.notes_path = str(HUM_DIR / "agents" / self.name / "notes.md")
        if not self.channels and self.port:
            self.channels = [{"type": "http", "port": self.port}]


# ── persistence ──────────────────────────────────────────────────────────────

class AgentStore:
    def _load(self) -> list[AgentConfig]:
        if not AGENTS_FILE.exists():
            return []
        raw = json.loads(AGENTS_FILE.read_text())
        return [AgentConfig(**a) for a in raw.get("agents", [])]

    def _save(self, agents: list[AgentConfig]) -> None:
        HUM_DIR.mkdir(parents=True, exist_ok=True)
        AGENTS_FILE.write_text(json.dumps({"agents": [asdict(a) for a in agents]}, indent=2))

    def all(self) -> list[AgentConfig]:
        return self._load()

    def get(self, name: str) -> AgentConfig | None:
        return next((a for a in self._load() if a.name == name), None)

    def add(self, config: AgentConfig) -> None:
        agents = self._load()
        if any(a.name == config.name for a in agents):
            raise ValueError(f"agent '{config.name}' already exists")
        self._save([*agents, config])

    def remove(self, name: str) -> bool:
        agents = self._load()
        filtered = [a for a in agents if a.name != name]
        if len(filtered) == len(agents):
            return False
        self._save(filtered)
        return True


__all__ = ["AgentConfig", "AgentStore"]
