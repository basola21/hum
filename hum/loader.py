from pathlib import Path

import yaml

from .registry import AgentConfig


def load_agent_yaml(path: Path) -> AgentConfig:
    """Load an AgentConfig from a YAML file.

    Raises ValueError with a clear message if required fields are missing.
    """
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"invalid YAML: expected a mapping in {path}")

    missing = [f for f in ("name", "system") if f not in raw]
    if missing:
        raise ValueError(f"missing required field(s) in {path}: {', '.join(missing)}")

    backend = raw.get("backend", {})
    if not isinstance(backend, dict) or not backend.get("command"):
        raise ValueError(f"missing required field 'backend.command' in {path}")

    command = backend["command"]
    if isinstance(command, str):
        command = command.split()

    heartbeat = raw.get("heartbeat", {}) or {}

    notes_path = raw.get("memory", "")
    if notes_path:
        notes_path = str(Path(notes_path).expanduser())

    return AgentConfig(
        name=raw["name"],
        system=raw["system"],
        command=command,
        notes_path=notes_path,
        port=raw.get("port"),
        description=raw.get("description", ""),
        heartbeat_every=heartbeat.get("every", ""),
        heartbeat_prompt=heartbeat.get("prompt", ""),
    )
