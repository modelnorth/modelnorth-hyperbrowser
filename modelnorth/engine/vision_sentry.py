"""ModelNorth HyperBrowser: Tier 2 Multimodal Vision Sentry for Canvas & CAPTCHAs."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class VisionAction:
    """Represents a coordinate-grounded visual action."""
    action: str  # CLICK, DRAG, SOLVE_CAPTCHA
    point_x_ratio: float  # 0.0 to 1.0
    point_y_ratio: float  # 0.0 to 1.0
    explanation: str
    elapsed_ms: float = 0.0


class VisionSentry:
    """Multimodal Vision Circuit Breaker using Gemini 2.5 Flash."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    async def analyze_and_ground(
        self,
        screenshot_bytes: bytes,
        goal: str,
        viewport_width: int = 1280,
        viewport_height: int = 800,
    ) -> Optional[VisionAction]:
        """Sends screenshot to Gemini 2.5 Flash and returns normalized pixel coordinates."""
        start_t = time.perf_counter()

        if not self.api_key:
            # Synthetic / fallback visual centering if no API key provided
            return VisionAction(
                action="CLICK",
                point_x_ratio=0.5,
                point_y_ratio=0.5,
                explanation="No Gemini API Key provided. Defaulting to center canvas target.",
                elapsed_ms=(time.perf_counter() - start_t) * 1000,
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            prompt = (
                f"You are the Sovereign Vision Sentry for a browser automation agent.\n"
                f"Current Goal: {goal}\n\n"
                f"Inspect the screenshot carefully. Look for:\n"
                f"1. Canvas elements, sliders, puzzle pieces, or interactive graphic controls.\n"
                f"2. CAPTCHA verification buttons (e.g., 'Verify you are human', Turnstile, hCaptcha checkbox).\n\n"
                f"Return JSON with the exact target coordinates on a 0-1000 scale:\n"
                f"{{\n"
                f'  "action": "CLICK",\n'
                f'  "point": [y_coord_0_to_1000, x_coord_0_to_1000],\n'
                f'  "explanation": "why clicking this location achieves the sub-goal"\n'
                f"}}"
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            data = json.loads(response.text)
            point = data.get("point", [500, 500])
            y_ratio = point[0] / 1000.0
            x_ratio = point[1] / 1000.0

            elapsed = (time.perf_counter() - start_t) * 1000

            return VisionAction(
                action=data.get("action", "CLICK"),
                point_x_ratio=x_ratio,
                point_y_ratio=y_ratio,
                explanation=data.get("explanation", "Grounded by Gemini Vision"),
                elapsed_ms=elapsed,
            )
        except Exception as err:
            elapsed = (time.perf_counter() - start_t) * 1000
            return VisionAction(
                action="CLICK",
                point_x_ratio=0.5,
                point_y_ratio=0.5,
                explanation=f"Vision query encountered error: {err}. Fallback center click.",
                elapsed_ms=elapsed,
            )
