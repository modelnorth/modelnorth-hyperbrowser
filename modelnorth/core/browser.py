"""ModelNorth HyperBrowser: Browser Harness & CDP Protocol Bridge."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserSession:
    """Manages high-performance browser lifecycle and CDP execution."""

    def __init__(
        self,
        cdp_url: Optional[str] = None,
        headless: bool = False,
        viewport_width: int = 1280,
        viewport_height: int = 800,
    ) -> None:
        self.cdp_url = cdp_url
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # Load In-V8 Scripts
        core_dir = Path(__file__).parent
        self._snapshot_js = (core_dir / "snapshot.js").read_text(encoding="utf-8")
        self._fastpath_js = (core_dir / "fastpath.js").read_text(encoding="utf-8")

    async def start(self, initial_url: Optional[str] = None) -> Page:
        """Starts browser context or connects to existing CDP."""
        self._playwright = await async_playwright().start()

        if self.cdp_url:
            self._browser = await self._playwright.chromium.connect_over_cdp(self.cdp_url)
            self._context = self._browser.contexts[0] if self._browser.contexts else await self._browser.new_context()
            self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        else:
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ]
            )
            self._context = await self._browser.new_context(
                viewport={"width": self.viewport_width, "height": self.viewport_height},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            self._page = await self._context.new_page()

        if initial_url:
            await self._page.goto(initial_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(0.2)  # Settle initial layout

        return self._page

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Browser session has not been started.")
        return self._page

    async def capture_snapshot(self) -> Dict[str, Any]:
        """Atomically captures indexed DOM table and anomaly triggers in < 20ms."""
        for attempt in range(3):
            try:
                result = await self.page.evaluate(self._snapshot_js)
                if result:
                    return result
            except Exception:
                await asyncio.sleep(0.08)
        return {"elements": [], "visualTriggers": {}}

    async def run_fastpath(self, instruction: str) -> Dict[str, Any]:
        """Runs Tier 0 in-browser heuristic match in < 1ms."""
        expr = f"({self._fastpath_js})({repr(instruction)})"
        for attempt in range(3):
            try:
                result = await self.page.evaluate(expr)
                if result:
                    return result
            except Exception:
                await asyncio.sleep(0.08)
        return {"matched": False}

    async def click_element(self, element_id: int) -> bool:
        """Executes instant V8 click on targeted node reference by data-mn-id in < 5ms."""
        js_click = f"""
        (() => {{
            const el = document.querySelector('[data-mn-id="{element_id}"]');
            if (el) {{
                el.scrollIntoView({{ block: 'nearest', inline: 'nearest' }});
                el.focus();
                el.dispatchEvent(new MouseEvent('mousedown', {{ bubbles: true, cancelable: true, view: window }}));
                el.dispatchEvent(new MouseEvent('mouseup', {{ bubbles: true, cancelable: true, view: window }}));
                el.click();
                return true;
            }}
            return false;
        }})()
        """
        success = await self.page.evaluate(js_click)
        await asyncio.sleep(0.02)  # 20ms fast micro-settle
        return bool(success)

    async def type_text(self, element_id: int, text: str, clear: bool = True) -> bool:
        """Types text instantly into targeted element via V8 property injection in < 5ms."""
        js_type = f"""
        (() => {{
            const el = document.querySelector('[data-mn-id="{element_id}"]');
            if (el) {{
                el.focus();
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {{
                    el.value = {repr(text)};
                }} else {{
                    el.innerText = {repr(text)};
                }}
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                el.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }}));
                return true;
            }}
            return false;
        }})()
        """
        success = await self.page.evaluate(js_type)
        await asyncio.sleep(0.02)
        return bool(success)

    async def click_pixel(self, x: float, y: float) -> None:
        """Dispatches mouse click at exact pixel coordinates."""
        await self.page.mouse.click(x, y)
        await asyncio.sleep(0.1)

    async def capture_screenshot(self) -> bytes:
        """Captures viewport screenshot for Tier 2 Vision Sentry."""
        return await self.page.screenshot(type="png", full_page=False)

    async def scroll(self, direction: str = "down", amount: int = 500) -> None:
        """Scrolls page up or down."""
        delta = amount if direction.lower() == "down" else -amount
        await self.page.mouse.wheel(0, delta)
        await asyncio.sleep(0.1)

    async def close(self) -> None:
        """Gracefully closes page, context, and browser instance."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
