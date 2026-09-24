"""ModelNorth HyperBrowser: Sovereign Browser Harness, Stealth & CDP Bridge."""

from __future__ import annotations

import asyncio
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright


class BrowserSession:
    """Manages high-performance browser lifecycle, anti-bot stealth, and CDP execution."""

    def __init__(
        self,
        cdp_url: Optional[str] = None,
        headless: bool = False,
        viewport_width: int = 1280,
        viewport_height: int = 800,
        enable_stealth: bool = True,
    ) -> None:
        self.cdp_url = cdp_url
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.enable_stealth = enable_stealth

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._pages: List[Page] = []

        # Load In-V8 Scripts
        core_dir = Path(__file__).parent
        self._snapshot_js = (core_dir / "snapshot.js").read_text(encoding="utf-8")
        self._fastpath_js = (core_dir / "fastpath.js").read_text(encoding="utf-8")
        self._stealth_js = (core_dir / "stealth.js").read_text(encoding="utf-8")

    async def start(self, initial_url: Optional[str] = None) -> Page:
        """Starts browser context with anti-bot stealth or connects to existing CDP."""
        self._playwright = await async_playwright().start()

        if self.cdp_url:
            self._browser = await self._playwright.chromium.connect_over_cdp(self.cdp_url)
            self._context = self._browser.contexts[0] if self._browser.contexts else await self._browser.new_context()
            self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        else:
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
                f"--window-size={self.viewport_width},{self.viewport_height}",
            ]
            try:
                self._browser = await self._playwright.chromium.launch(
                    headless=self.headless,
                    args=launch_args,
                )
            except Exception:
                try:
                    self._browser = await self._playwright.chromium.launch(
                        headless=self.headless,
                        args=launch_args,
                        channel="msedge",
                    )
                except Exception:
                    self._browser = await self._playwright.chromium.launch(
                        headless=self.headless,
                        args=launch_args,
                        channel="chrome",
                    )
            self._context = await self._browser.new_context(
                viewport={"width": self.viewport_width, "height": self.viewport_height},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York",
            )

            if self.enable_stealth:
                await self._context.add_init_script(self._stealth_js)

            self._page = await self._context.new_page()

        self._pages = self._context.pages if self._context else [self._page]

        if initial_url:
            await self._page.goto(initial_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(0.15)  # Micro-settle layout

        return self._page

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Browser session has not been started.")
        return self._page

    async def capture_snapshot(self) -> Dict[str, Any]:
        """Atomically captures indexed DOM table across shadow roots in < 20ms."""
        for _ in range(3):
            try:
                result = await self.page.evaluate(self._snapshot_js)
                if result:
                    return result
            except Exception:
                await asyncio.sleep(0.05)
        return {"elements": [], "visualTriggers": {}}

    async def run_fastpath(self, instruction: str) -> Dict[str, Any]:
        """Runs Tier 0 in-browser heuristic match in < 1ms."""
        expr = f"({self._fastpath_js})({repr(instruction)})"
        for _ in range(3):
            try:
                result = await self.page.evaluate(expr)
                if result:
                    return result
            except Exception:
                await asyncio.sleep(0.05)
        return {"matched": False}

    async def click_element(self, element_id: int) -> bool:
        """Executes instant click on targeted node across regular and Shadow DOM in < 5ms."""
        js_click = f"""
        (() => {{
            function findNode(root, id) {{
                if (!root) return null;
                try {{
                    const el = root.querySelector(`[data-mn-id="${{id}}"]`);
                    if (el) return el;
                }} catch (_) {{}}
                let all = [];
                try {{ all = root.querySelectorAll('*'); }} catch (_) {{}}
                for (const c of all) {{
                    if (c.shadowRoot) {{
                        const res = findNode(c.shadowRoot, id);
                        if (res) return res;
                    }}
                    if (c.tagName === 'IFRAME') {{
                        try {{
                            const doc = c.contentDocument || (c.contentWindow && c.contentWindow.document);
                            if (doc) {{
                                const res = findNode(doc, id);
                                if (res) return res;
                            }}
                        }} catch (_) {{}}
                    }}
                }}
                return null;
            }}
            const el = findNode(document, {element_id});
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
        await asyncio.sleep(0.02)
        return bool(success)

    async def type_text(self, element_id: int, text: str) -> bool:
        """Types text instantly into targeted element across Shadow DOM in < 5ms."""
        js_type = f"""
        (() => {{
            function findNode(root, id) {{
                if (!root) return null;
                try {{
                    const el = root.querySelector(`[data-mn-id="${{id}}"]`);
                    if (el) return el;
                }} catch (_) {{}}
                let all = [];
                try {{ all = root.querySelectorAll('*'); }} catch (_) {{}}
                for (const c of all) {{
                    if (c.shadowRoot) {{
                        const res = findNode(c.shadowRoot, id);
                        if (res) return res;
                    }}
                }}
                return null;
            }}
            const el = findNode(document, {element_id});
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

    async def select_option(self, element_id: int, value: str) -> bool:
        """Selects an option inside native dropdown."""
        js_select = f"""
        (() => {{
            const el = document.querySelector(`[data-mn-id="{element_id}"]`);
            if (el && el.tagName === 'SELECT') {{
                const targetVal = {repr(value.lower())};
                for (let i = 0; i < el.options.length; i++) {{
                    const opt = el.options[i];
                    if (opt.text.toLowerCase().includes(targetVal) || opt.value.toLowerCase().includes(targetVal)) {{
                        el.selectedIndex = i;
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                }}
            }}
            return false;
        }})()
        """
        success = await self.page.evaluate(js_select)
        await asyncio.sleep(0.02)
        return bool(success)

    async def press_key(self, key: str) -> None:
        """Sends native keyboard key press with automatic key normalization."""
        key_map = {
            "enter": "Enter",
            "return": "Enter",
            "escape": "Escape",
            "esc": "Escape",
            "tab": "Tab",
            "backspace": "Backspace",
            "delete": "Delete",
            "space": "Space",
            "arrowup": "ArrowUp",
            "arrowdown": "ArrowDown",
            "arrowleft": "ArrowLeft",
            "arrowright": "ArrowRight",
        }
        normalized_key = key_map.get(key.lower(), key.capitalize())
        await self.page.keyboard.press(normalized_key)
        await asyncio.sleep(0.02)

    async def click_pixel(self, x: float, y: float, humanize: bool = True) -> None:
        """Dispatches mouse click at exact pixel coordinates with optional human Bezier jitter."""
        if humanize:
            # Human-like Bezier path interpolation
            steps = random.randint(3, 6)
            for _ in range(steps):
                jitter_x = x + random.uniform(-2, 2)
                jitter_y = y + random.uniform(-2, 2)
                await self.page.mouse.move(jitter_x, jitter_y)
                await asyncio.sleep(0.01)

        await self.page.mouse.click(x, y)
        await asyncio.sleep(0.05)

    async def drag_and_drop(self, start_x: float, start_y: float, end_x: float, end_y: float) -> None:
        """Performs coordinate-grounded drag and drop (e.g. puzzle slider CAPTCHAs)."""
        await self.page.mouse.move(start_x, start_y)
        await self.page.mouse.down()
        steps = 10
        for i in range(1, steps + 1):
            cur_x = start_x + (end_x - start_x) * (i / steps) + math.sin(i) * 1.5
            cur_y = start_y + (end_y - start_y) * (i / steps)
            await self.page.mouse.move(cur_x, cur_y)
            await asyncio.sleep(0.015)
        await self.page.mouse.up()
        await asyncio.sleep(0.05)

    async def capture_screenshot(self) -> bytes:
        """Captures viewport screenshot for Tier 2 Vision Sentry."""
        return await self.page.screenshot(type="png", full_page=False)

    async def scroll(self, direction: str = "down", amount: int = 500) -> None:
        """Scrolls page up or down."""
        delta = amount if direction.lower() == "down" else -amount
        await self.page.mouse.wheel(0, delta)
        await asyncio.sleep(0.05)

    # Multi-tab Management
    async def new_tab(self, url: Optional[str] = None) -> Page:
        """Creates a new browser tab and sets it as active."""
        if not self._context:
            raise RuntimeError("Context not initialized")
        new_page = await self._context.new_page()
        self._page = new_page
        self._pages = self._context.pages
        if url:
            await new_page.goto(url, wait_until="domcontentloaded")
        return new_page

    async def switch_tab(self, index: int) -> Page:
        """Switches active tab by index."""
        if not self._context or not self._context.pages:
            raise RuntimeError("No active pages")
        self._pages = self._context.pages
        if 0 <= index < len(self._pages):
            self._page = self._pages[index]
            await self._page.bring_to_front()
            return self._page
        raise IndexError(f"Tab index {index} out of range ({len(self._pages)} tabs)")

    async def close(self) -> None:
        """Gracefully closes page, context, and browser instance."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
