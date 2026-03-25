import asyncio
import sys
from pathlib import Path

import click

from .registry import AgentConfig, AgentStore

store = AgentStore()


@click.group()
def cli():
    """hum — a runtime for persistent agents."""


# ── hum new ───────────────────────────────────────────────────────────────────


@cli.command()
@click.option(
    "--file", "-f", "file_path", default=None, help="Path to agent YAML file."
)
def new(file_path: str | None):
    """Register a new agent from a YAML file."""
    if file_path:
        _new_from_file(Path(file_path))
        return

    click.echo("error: use --file <agent.yaml>", err=True)
    sys.exit(1)


def _new_from_file(path: Path) -> None:
    from .loader import load_agent_yaml

    if not path.exists():
        click.echo(f"error: file not found: {path}", err=True)
        sys.exit(1)

    try:
        config = load_agent_yaml(path)
    except ValueError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)

    try:
        store.add(config)
    except ValueError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Agent '{config.name}' registered.")
    click.echo(f"Run with: hum run {config.name}")


# ── hum list ──────────────────────────────────────────────────────────────────


@cli.command("list")
def list_agents():
    """List all registered agents."""
    agents = store.all()
    if not agents:
        click.echo("No agents registered. Use 'hum new --file agent.yaml'.")
        return

    click.echo(f"\n{'NAME':<20} {'COMMAND':<30} {'PORT':<8} NOTES")
    click.echo("─" * 72)
    for a in agents:
        port = str(a.port) if a.port else "stdin"
        cmd = " ".join(a.command)
        click.echo(f"{a.name:<20} {cmd:<30} {port:<8} {a.notes_path}")
    click.echo()


# ── hum remove ────────────────────────────────────────────────────────────────


@cli.command()
@click.argument("name")
def remove(name: str):
    """Remove a registered agent."""
    if not store.remove(name):
        click.echo(f"error: agent '{name}' not found", err=True)
        sys.exit(1)
    click.echo(f"Agent '{name}' removed.")


# ── hum run ───────────────────────────────────────────────────────────────────


@cli.command()
@click.argument("name")
def run(name: str):
    """Run a registered agent by name."""
    config = store.get(name)
    if not config:
        click.echo(
            f"error: agent '{name}' not found. Register it first with 'hum new'.",
            err=True,
        )
        sys.exit(1)

    from .acp.backend import ACPBackend
    from .runtime import Runtime

    backend = ACPBackend(config.command)
    asyncio.run(Runtime(config, backend).start())


def main():
    cli()
