"""ModelNorth HyperBrowser: Sovereign Model Context Protocol (MCP) Server.

Exposes sub-20ms web automation, zero-token DOM extraction, and session persistence
over standard JSON-RPC 2.0 stdio transport for Claude, Cursor, and autonomous AI agents.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from modelnorth.agent import HyperAgent
from modelnorth.core.browser import BrowserSession

MCP_PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "hyperbrowser_run",
        "description": "Executes ultrafast, sovereign web automation task using the Tri-Tier (Tier 0 V8 / Tier 1 ONNX / Tier 2 Vision) Reflex Engine.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Initial target URL to navigate to.",
                },
                "goal": {
                    "type": "string",
                    "description": "Natural language objective (e.g. 'Find one-way flights from Dubai to Lahore on Sept 20, 2026').",
                },
                "headless": {
                    "type": "boolean",
                    "description": "Whether to run browser in headless mode. Default is true.",
                    "default": True,
                },
                "max_steps": {
                    "type": "integer",
                    "description": "Maximum discrete micro-action steps to execute before stopping. Default is 15.",
                    "default": 15,
                },
                "storage_state_path": {
                    "type": "string",
                    "description": "Optional file path to saved browser storage state (cookies/tokens) for authenticated sessions.",
                },
            },
            "required": ["url", "goal"],
        },
    },
    {
        "name": "hyperbrowser_extract",
        "description": "Performs sub-30ms zero-token structured table and card extraction from target page DOM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Target webpage URL to extract data from.",
                },
                "target_entity": {
                    "type": "string",
                    "description": "Entity description to extract (e.g. 'flight', 'product', 'invoice'). Default is 'item'.",
                    "default": "item",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "hyperbrowser_snapshot",
        "description": "Atomically captures indexed DOM table across shadow roots and iframes in <20ms.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Webpage URL to inspect.",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "hyperbrowser_save_session",
        "description": "Navigates to URL, captures active cookies and session storage tokens, and saves them to a file for persistent reuse.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the site where session should be captured.",
                },
                "save_path": {
                    "type": "string",
                    "description": "Target JSON file path where storage state will be written.",
                },
            },
            "required": ["url", "save_path"],
        },
    },
]


async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatches tool execution to ModelNorth engine."""
    if name == "hyperbrowser_run":
        url = arguments["url"]
        goal = arguments["goal"]
        headless = arguments.get("headless", True)
        max_steps = arguments.get("max_steps", 15)
        storage_state_path = arguments.get("storage_state_path")

        steps_summary = []
        async with HyperAgent(
            url=url,
            goal=goal,
            headless=headless,
            max_steps=max_steps,
            storage_state_path=storage_state_path,
        ) as agent:
            async for step in agent.run():
                steps_summary.append({
                    "step": step.step_number,
                    "tier": f"Tier {step.tier}",
                    "action": step.action,
                    "target": step.target_name,
                    "elapsed_ms": round(step.elapsed_ms, 1),
                    "total_ms": round(step.total_elapsed_ms, 1),
                    "notes": step.notes,
                })
            final_snapshot = await agent.browser.capture_snapshot()

        return {
            "status": "success",
            "goal": goal,
            "final_url": final_snapshot.get("url"),
            "final_title": final_snapshot.get("title"),
            "steps_executed": len(steps_summary),
            "telemetry": steps_summary,
        }

    elif name == "hyperbrowser_extract":
        url = arguments["url"]
        target_entity = arguments.get("target_entity", "item")

        async with HyperAgent(url=url, goal="extract", headless=True) as agent:
            records = await agent.extract(target_entity=target_entity)

        return {
            "status": "success",
            "url": url,
            "count": len(records),
            "records": records,
        }

    elif name == "hyperbrowser_snapshot":
        url = arguments["url"]
        session = BrowserSession(headless=True)
        try:
            await session.start(url)
            snapshot = await session.capture_snapshot()
            return {
                "status": "success",
                "url": snapshot.get("url"),
                "title": snapshot.get("title"),
                "element_count": len(snapshot.get("elements", [])),
                "mutation_count": snapshot.get("mutationCount", 0),
                "visual_triggers": snapshot.get("visualTriggers", {}),
                "sample_elements": snapshot.get("elements", [])[:20],
            }
        finally:
            await session.close()

    elif name == "hyperbrowser_save_session":
        url = arguments["url"]
        save_path = arguments["save_path"]
        session = BrowserSession(headless=False, storage_state_path=save_path)
        try:
            await session.start(url)
            saved_to = await session.save_storage_state(save_path)
            return {
                "status": "success",
                "message": f"Storage state successfully persisted to {saved_to}",
                "save_path": saved_to,
            }
        finally:
            await session.close()

    raise ValueError(f"Unknown tool: {name}")


async def run_stdio_server() -> None:
    """Runs standard MCP stdio JSON-RPC server loop."""
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break

        line_str = line.decode("utf-8").strip()
        if not line_str:
            continue

        try:
            req = json.loads(line_str)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        response: Dict[str, Any] = {"jsonrpc": "2.0", "id": req_id}

        if method == "initialize":
            response["result"] = {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "modelnorth-hyperbrowser",
                    "version": "0.3.0",
                },
            }
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            response["result"] = {"tools": TOOLS}
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result = await handle_tool_call(tool_name, tool_args)
                response["result"] = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                    "isError": False,
                }
            except Exception as e:
                response["result"] = {
                    "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                    "isError": True,
                }
        elif method == "ping":
            response["result"] = {}
        else:
            response["error"] = {
                "code": -32601,
                "message": f"Method '{method}' not found",
            }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


def main() -> None:
    """CLI entry point for ModelNorth HyperBrowser MCP server."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
