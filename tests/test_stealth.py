"""Unit tests for browser anti-bot stealth injection."""

import pytest
from modelnorth.core.browser import BrowserSession


@pytest.mark.asyncio
async def test_stealth_attributes():
    browser = BrowserSession(headless=True, enable_stealth=True)
    try:
        await browser.start("about:blank")
        # Check navigator.webdriver is undefined
        webdriver_val = await browser.page.evaluate("navigator.webdriver")
        assert webdriver_val is None or webdriver_val is False

        # Check chrome runtime mock
        has_chrome = await browser.page.evaluate("Boolean(window.chrome && window.chrome.runtime)")
        assert has_chrome is True

        # Check languages mock
        languages = await browser.page.evaluate("navigator.languages")
        assert "en-US" in languages
    finally:
        await browser.close()
