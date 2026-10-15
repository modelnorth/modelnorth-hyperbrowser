"""Tests for ModelNorth HyperBrowser: MCP Server Protocol & Tool Dispatch."""

import pytest
from modelnorth.mcp_server import TOOLS, handle_tool_call


def test_mcp_tool_definitions():
    tool_names = [t["name"] for t in TOOLS]
    assert "hyperbrowser_run" in tool_names
    assert "hyperbrowser_extract" in tool_names
    assert "hyperbrowser_snapshot" in tool_names
    assert "hyperbrowser_save_session" in tool_names

    run_tool = next(t for t in TOOLS if t["name"] == "hyperbrowser_run")
    assert "url" in run_tool["inputSchema"]["required"]
    assert "goal" in run_tool["inputSchema"]["required"]


@pytest.mark.asyncio
async def test_handle_tool_call_invalid_tool():
    with pytest.raises(ValueError, match="Unknown tool: non_existent"):
        await handle_tool_call("non_existent", {})
