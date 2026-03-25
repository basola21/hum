"""Integration tests — spawn a real ACP agent and verify end-to-end communication.

Run with:
    hatch run pytest tests/test_acp_integration.py -v -s
"""

import shutil

import pytest

from hum.acp.backend import acp_backend


def agent_available(binary: str) -> bool:
    return shutil.which(binary) is not None


pytestmark = pytest.mark.skipif(
    not agent_available("claude-agent-acp"), reason="claude-agent-acp not found in PATH"
)


async def test_basic_response():
    async with acp_backend(["claude-agent-acp"]) as backend:
        result = await backend.run(
            system="You are a helpful assistant. Be extremely brief.",
            prompt="Reply with exactly the word: pong",
            notes="",
        )
    assert result.text.strip()
    print(f"\n[claude] → {result.text.strip()!r}")
