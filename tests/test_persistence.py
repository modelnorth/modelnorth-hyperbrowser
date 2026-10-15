"""Tests for ModelNorth HyperBrowser: Storage State & Session Persistence."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from modelnorth.agent import HyperAgent
from modelnorth.core.browser import BrowserSession


@pytest.mark.asyncio
async def test_browser_session_storage_state_save(tmp_path: Path):
    session = BrowserSession(storage_state_path=str(tmp_path / "test_session.json"))
    
    mock_context = AsyncMock()
    session._context = mock_context
    session._page = AsyncMock()

    save_target = tmp_path / "saved_state.json"
    result = await session.save_storage_state(str(save_target))

    assert result == str(save_target)
    mock_context.storage_state.assert_called_once_with(path=str(save_target))


@pytest.mark.asyncio
async def test_agent_storage_state_integration(tmp_path: Path):
    state_file = tmp_path / "auth_tokens.json"
    state_file.write_text(json.dumps({"cookies": [{"name": "auth_token", "value": "xyz123"}]}))

    agent = HyperAgent(
        url="https://example.com/dashboard",
        goal="check profile",
        storage_state_path=str(state_file),
    )
    assert agent.storage_state_path == str(state_file)
    assert agent.browser.storage_state_path == str(state_file)


@pytest.mark.asyncio
async def test_wait_for_download(tmp_path: Path):
    session = BrowserSession(download_dir=str(tmp_path))
    session._downloads.append({
        "filename": "report_march_2026.csv",
        "path": str(tmp_path / "report_march_2026.csv"),
        "url": "https://example.com/download/report.csv",
        "size_bytes": 1024,
    })

    download = await session.wait_for_download(timeout=0.1)
    assert download is not None
    assert download["filename"] == "report_march_2026.csv"
    assert download["size_bytes"] == 1024
