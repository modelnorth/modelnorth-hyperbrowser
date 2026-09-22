"""ModelNorth HyperBrowser: Tri-Tier Master Agent Orchestrator."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional

from modelnorth.core.browser import BrowserSession
from modelnorth.engine.decision_local import LocalDecisionEngine, ActionDecision
from modelnorth.engine.text_engine import TextGenerationEngine
from modelnorth.engine.vision_sentry import VisionSentry, VisionAction


@dataclass
class AgentStep:
    """Telemetry report for each executed micro-action."""
    step_number: int
    tier: int  # 0: In-Browser, 1: Local System 1, 2: Vision Sentry
    action: str
    target_name: Optional[str] = None
    target_id: Optional[int] = None
    text: Optional[str] = None
    elapsed_ms: float = 0.0
    total_elapsed_ms: float = 0.0
    confidence: float = 1.0
    notes: str = ""


@dataclass
class AgentState:
    """Cumulative state of the active HyperAgent run."""
    url: str
    goal: str
    status: str = "running"  # running, completed, blocked, error
    steps: List[AgentStep] = field(default_factory=list)
    start_time: float = field(default_factory=time.perf_counter)


class HyperAgent:
    """The High-Speed Sovereign Web Automation Agent."""

    def __init__(
        self,
        url: str,
        goal: str,
        max_steps: int = 25,
        cdp_url: Optional[str] = None,
        headless: bool = False,
        gemini_api_key: Optional[str] = None,
    ) -> None:
        self.url = url
        self.goal = goal
        self.max_steps = max_steps
        self.cdp_url = cdp_url
        self.headless = headless

        self.browser = BrowserSession(cdp_url=cdp_url, headless=headless)
        self.decision_engine = LocalDecisionEngine()
        self.text_engine = TextGenerationEngine()
        self.vision_sentry = VisionSentry(api_key=gemini_api_key)

        self.state = AgentState(url=url, goal=goal)

    async def __aenter__(self) -> "HyperAgent":
        await self.browser.start(self.url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.browser.close()

    async def run(self) -> AsyncGenerator[AgentStep, None]:
        """Main execution loop streaming steps as they execute."""
        step_idx = 1

        while step_idx <= self.max_steps:
            t0 = time.perf_counter()

            # 1. Capture atomic DOM snapshot
            snapshot = await self.browser.capture_snapshot()
            elements = snapshot.get("elements", [])
            visual_triggers = snapshot.get("visualTriggers", {})

            # 2. Check Tier 0 Fast-Path Compiler (< 1 ms)
            fastpath_res = await self.browser.run_fastpath(self.goal)
            
            if fastpath_res and fastpath_res.get("matched"):
                action = fastpath_res["action"]
                target_id = fastpath_res["targetId"]
                target_name = fastpath_res.get("targetName")
                text_to_type = fastpath_res.get("text")

                if action == "CLICK":
                    await self.browser.click_element(target_id)
                elif action == "TYPE_TEXT" and text_to_type:
                    await self.browser.type_text(target_id, text_to_type)

                step_elapsed = (time.perf_counter() - t0) * 1000
                total_elapsed = (time.perf_counter() - self.state.start_time) * 1000

                step = AgentStep(
                    step_number=step_idx,
                    tier=0,
                    action=action,
                    target_id=target_id,
                    target_name=target_name,
                    text=text_to_type,
                    elapsed_ms=step_elapsed,
                    total_elapsed_ms=total_elapsed,
                    confidence=fastpath_res.get("confidence", 1.0),
                    notes="Direct In-Browser V8 Fast-Path Match"
                )
                self.state.steps.append(step)
                yield step
                step_idx += 1
                continue

            # 3. Check Tier 2 Vision Sentry Trigger (Canvas / CAPTCHA / Empty DOM)
            if visual_triggers.get("hasCanvas") or visual_triggers.get("hasCaptcha") or len(elements) == 0:
                screenshot = await self.browser.capture_screenshot()
                vision_action = await self.vision_sentry.analyze_and_ground(
                    screenshot, self.goal
                )

                if vision_action:
                    w = visual_triggers.get("viewport", {}).get("width", 1280)
                    h = visual_triggers.get("viewport", {}).get("height", 800)
                    abs_x = w * vision_action.point_x_ratio
                    abs_y = h * vision_action.point_y_ratio

                    await self.browser.click_pixel(abs_x, abs_y)

                    step_elapsed = (time.perf_counter() - t0) * 1000
                    total_elapsed = (time.perf_counter() - self.state.start_time) * 1000

                    step = AgentStep(
                        step_number=step_idx,
                        tier=2,
                        action=f"PIXEL_{vision_action.action}",
                        target_name=f"({int(abs_x)}, {int(abs_y)})",
                        elapsed_ms=step_elapsed,
                        total_elapsed_ms=total_elapsed,
                        confidence=0.92,
                        notes=f"Tier 2 Vision: {vision_action.explanation}"
                    )
                    self.state.steps.append(step)
                    yield step
                    step_idx += 1
                    continue

            # 4. Standard Tier 1 Local System 1 Decision (< 15 ms)
            history_sigs = [f"{s.action}:{s.target_name}" for s in self.state.steps]
            decision = self.decision_engine.predict(self.goal, elements, history=history_sigs)

            if decision.operation == "DONE":
                step_elapsed = (time.perf_counter() - t0) * 1000
                total_elapsed = (time.perf_counter() - self.state.start_time) * 1000
                step = AgentStep(
                    step_number=step_idx,
                    tier=1,
                    action="DONE",
                    target_name=decision.target_name or "Goal Satisfied",
                    elapsed_ms=step_elapsed,
                    total_elapsed_ms=total_elapsed,
                    confidence=1.0,
                    notes="Verified Goal Reached"
                )
                self.state.steps.append(step)
                yield step
                self.state.status = "completed"
                break
            elif decision.operation == "SCROLL_DOWN":
                await self.browser.scroll("down", 500)
            elif decision.operation == "CLICK" and decision.target_id:
                await self.browser.click_element(decision.target_id)
            elif decision.operation == "TYPE_TEXT" and decision.target_id:
                # Generate text payload
                field_name = decision.target_name or "field"
                val = await self.text_engine.generate_text(field_name, self.goal)
                await self.browser.type_text(decision.target_id, val)
                decision.text_to_type = val

            step_elapsed = (time.perf_counter() - t0) * 1000
            total_elapsed = (time.perf_counter() - self.state.start_time) * 1000

            step = AgentStep(
                step_number=step_idx,
                tier=1,
                action=decision.operation,
                target_id=decision.target_id,
                target_name=decision.target_name,
                text=decision.text_to_type,
                elapsed_ms=step_elapsed,
                total_elapsed_ms=total_elapsed,
                confidence=decision.confidence,
                notes="Local System 1 Speculative Decision"
            )
            self.state.steps.append(step)
            yield step

            step_idx += 1

        self.state.status = "completed" if step_idx <= self.max_steps else "stopped"
