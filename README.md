# hum

Small agents that keep running.

## Install

```bash
pip install hum
```

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=sk-...
```

## Usage

```python
from hum import Agent

agent = Agent(
    system="You are a focused assistant.",
    model="claude-opus-4-6",
)

@agent.heartbeat(every="10m")
async def pulse(ctx):
    await ctx.run(f"Notes so far:\n{ctx.notes}\n\nAnything to do?")

@agent.on_message
async def respond(message, ctx):
    return await ctx.run(message)

agent.run()
```

```
$ python agent.py
[hum] agent started
[hum] heartbeat: 10m
[hum] listening on stdin
> hello
agent: Hi! How can I help?
```

## Core concepts

**Heartbeat** — the agent wakes up on a schedule and does work. Use `@agent.heartbeat(every="10m")`. Intervals: `s`, `m`, `h`, `d`.

**Messages** — the agent responds to input via stdin. Use `@agent.on_message`.

**Notes** — `ctx.notes` is a persistent markdown file (`heartbeat.md`) the agent can read and update between beats. The agent calls `update_notes` to write to it.

**ctx.run(prompt)** — invokes the LLM with the agent's system prompt. Returns the response text.

## Both at once

Heartbeat and message handling run concurrently. The agent does background work on its schedule and still responds when you talk to it.

```python
@agent.heartbeat(every="1h")
async def background(ctx):
    await ctx.run("Do your hourly check.")

@agent.on_message
async def respond(message, ctx):
    return await ctx.run(message)
```
