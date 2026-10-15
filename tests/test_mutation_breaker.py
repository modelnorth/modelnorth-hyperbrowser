"""Tests for ModelNorth HyperBrowser: DOM Mutation Verification & Overlay Dismissal."""

import pytest
from modelnorth.engine.decision_local import LocalDecisionEngine


def test_overlay_dismissal_priority():
    engine = LocalDecisionEngine()
    elements = [
        {"id": 1, "name": "Accept all cookies", "role": "button", "value": None},
        {"id": 2, "name": "Flight search form", "role": "button", "value": None},
    ]
    decision = engine.predict("Find flights from Dubai to Lahore", elements)
    # The overlay dismissal button should be prioritized to unblock the screen
    assert decision.target_id == 1
    assert "accept all cookies" in (decision.target_name or "").lower()


def test_circuit_breaker_mutation_state_tracking():
    elements = [
        {"id": 1, "name": "Submit", "role": "button", "value": None},
    ]
    engine = LocalDecisionEngine()
    # First action
    decision1 = engine.predict("Submit form", elements, history=[])
    assert decision1.operation == "CLICK"

    # Repeated action without state change is avoided via history
    decision2 = engine.predict("Submit form", elements, history=["click:submit", "submit"])
    assert decision2.operation in ["DONE", "SCROLL_DOWN"]
