# hum

Small agents that keep running.

An agent runs on a schedule, persists notes between sessions, and accepts messages over HTTP. You define it in YAML and manage it with the `hum` CLI.

## Install

```bash
pip install hum
```

You also need a running ACP-compatible agent binary on your PATH. For Claude:

```bash
pip install claude-agent-acp
export ANTHROPIC_API_KEY=sk-...
```

## Define an agent

Create a YAML file:

```yaml
# assistant.yaml
name: my-assistant
description: A focused personal assistant
system: You are a focused personal assistant. Keep responses short and useful.
backend:
  command: [claude-agent-acp]
port: 8000
heartbeat:
  every: 10m
  prompt: |
    Your current notes:
    {notes}

    Do a brief check-in. Note anything worth remembering.
memory: ./notes.md
```

### Fields

| Field | Required | Description |
|---|---|---|
| `name` | yes | Unique agent name |
| `system` | yes | System prompt |
| `backend.command` | yes | Command to launch the ACP agent process |
| `port` | yes | HTTP port the agent listens on |
| `heartbeat.every` | no | How often the agent wakes up (`s`, `m`, `h`, `d`) |
| `heartbeat.prompt` | no | Prompt sent on each heartbeat. `{notes}` is replaced with current notes |
| `memory` | no | Path to the notes file (default: `~/.hum/agents/<name>/notes.md`) |
| `description` | no | Human-readable description |

## Manage agents

```bash
# Register
hum new --file assistant.yaml

# List registered agents
hum list

# Run
hum run my-assistant

# Remove
hum remove my-assistant
```

## Send messages

While the agent is running, send messages via HTTP:

```bash
curl -X POST http://localhost:8000/message \
  -H 'Content-Type: application/json' \
  -d '{"message": "What should I focus on today?"}'
```

Response:

```json
{"response": "Based on your notes, you mentioned the report is due Friday..."}
```

## How it works

**Heartbeat** — on each tick the agent receives the heartbeat prompt (with `{notes}` filled in) and runs it through the LLM. Use this for background work: summarising, checking in, updating notes.

**Messages** — incoming HTTP requests hit `POST /message` and are sent to the LLM with the same system prompt. The response is returned synchronously.

**Notes** — a persistent markdown file the agent can read and update between beats via the `update_notes` tool. The current content is injected into heartbeat prompts via `{notes}`.

**Concurrency** — heartbeat and HTTP handling run concurrently in the same process. The agent does background work on schedule and still responds to messages.

**Backend** — agents run as ACP (Agent Client Protocol) subprocesses. `hum` spawns the process, holds a session open for the agent's lifetime, and routes prompts through it.

## Examples

See the [`examples/`](examples/) directory:

| File | Description |
|---|---|
| `basic.yaml` | Personal assistant, checks in every 10 minutes |
| `journal.yaml` | Journaling companion, prompts reflection twice a day |
| `standup.yaml` | Work standup bot, daily done/next/blockers log |
| `habit-tracker.yaml` | Habit tracker with streak awareness |
| `research-digest.yaml` | Research synthesis assistant, surfaces gaps every 6 hours |
| `focus-timer.yaml` | Pomodoro coach, checks in every 25 minutes |
