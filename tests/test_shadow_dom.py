"""Unit tests for recursive Shadow DOM crawling."""

import pytest
from modelnorth.core.browser import BrowserSession


@pytest.mark.asyncio
async def test_shadow_dom_element_extraction():
    browser = BrowserSession(headless=True)
    try:
        await browser.start("about:blank")
        html = """
        <html>
        <body>
            <div id="host"></div>
            <script>
                const host = document.getElementById('host');
                const root = host.attachShadow({ mode: 'open' });
                root.innerHTML = `
                    <input id="shadow-in" placeholder="Enter Shadow Code" value="" />
                    <button id="shadow-btn">Unlock Gate</button>
                `;
            </script>
        </body>
        </html>
        """
        await browser.page.set_content(html)
        snapshot = await browser.capture_snapshot()
        elements = snapshot.get("elements", [])

        # Find shadow input and button
        shadow_inputs = [el for el in elements if "Shadow Code" in (el.get("name") or "")]
        shadow_buttons = [el for el in elements if "Unlock Gate" in (el.get("name") or "")]

        assert len(shadow_inputs) == 1
        assert len(shadow_buttons) == 1
        assert shadow_inputs[0]["id"] is not None
        assert shadow_buttons[0]["id"] is not None
    finally:
        await browser.close()
