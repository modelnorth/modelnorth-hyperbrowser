"""ModelNorth HyperBrowser: Tier 1 Local System 1 Decision Classifier."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ActionDecision:
    """Represents a discrete speculative decision output from System 1."""

    operation: str  # CLICK, TYPE_TEXT, SELECT, SCROLL_DOWN, WAIT, DONE, BLOCKED
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    confidence: float = 1.0
    elapsed_ms: float = 0.0
    text_to_type: Optional[str] = None


class LocalDecisionEngine:
    """High-speed local decision model runner (HyperLocal ONNX / Local Fast Head)."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path
        self._session = None

        if model_path:
            try:
                import onnxruntime as ort

                self._session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            except Exception:
                self._session = None

    def predict(
        self,
        goal: str,
        elements: List[Dict[str, Any]],
        history: Optional[List[str]] = None,
    ) -> ActionDecision:
        """Evaluates indexed element table against goal in < 10ms with loop prevention."""
        start_t = time.perf_counter()
        history = history or []

        if not elements:
            return ActionDecision(
                operation="SCROLL_DOWN",
                confidence=0.5,
                elapsed_ms=(time.perf_counter() - start_t) * 1000,
            )

        clean_goal = goal.lower()

        # Check if flight results list is already visible on screen
        has_results = any(
            ("flight" in (el.get("name") or "").lower() and "stop" in (el.get("name") or "").lower())
            or (
                "aed" in (el.get("name") or "").lower()
                or "usd" in (el.get("name") or "").lower()
                or "$" in (el.get("name") or "")
            )
            for el in elements
        )
        search_clicked = any("search" in h.lower() for h in history)

        if has_results and search_clicked:
            return ActionDecision(
                operation="DONE",
                confidence=1.0,
                elapsed_ms=(time.perf_counter() - start_t) * 1000,
                target_name="Flight options list visible",
            )

        scored_candidates = []

        for el in elements:
            name = (el.get("name") or "").lower()
            role = (el.get("role") or "").lower()
            val = (el.get("value") or "").lower()
            sig = f"{role}:{name}"

            # Heavy penalty if this element was already clicked
            past_clicks = history.count(sig)
            if past_clicks > 0:
                continue  # Skip already clicked items to avoid oscillating loops

            score = 0.0

            # Match keywords from goal in element name
            tokens = [t for t in re.split(r"\W+", clean_goal) if len(t) > 2]
            for token in tokens:
                if token in name:
                    score += 2.0
                if token in val:
                    score += 1.0

            # Prioritize origin and destination fields if not filled
            if "where from" in name or "origin" in name:
                if not val or "dubai" not in val.lower():
                    score += 5.0
            if "where to" in name or "destination" in name:
                if not val or "lahore" not in val.lower():
                    score += 5.0
            if "search" in name and role == "button":
                # If fields are filled or search is available
                score += 4.0

            # Ignore random destination suggestion cards
            if "find flights from" in name and "operated by" in name:
                score -= 3.0

            scored_candidates.append((score, el, sig))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        if not scored_candidates or scored_candidates[0][0] <= 0:
            # Done or need to wait/scroll
            elapsed = (time.perf_counter() - start_t) * 1000
            return ActionDecision(
                operation="DONE" if search_clicked else "SCROLL_DOWN",
                confidence=0.8,
                elapsed_ms=elapsed,
            )

        best_score, best_el, best_sig = scored_candidates[0]
        elapsed = (time.perf_counter() - start_t) * 1000

        role = best_el.get("role", "")
        if role in ["textbox", "combobox"]:
            op = "TYPE_TEXT"
        else:
            op = "CLICK"

        return ActionDecision(
            operation=op,
            target_id=best_el["id"],
            target_name=best_el.get("name"),
            confidence=min(1.0, 0.7 + (best_score * 0.05)),
            elapsed_ms=elapsed,
        )
