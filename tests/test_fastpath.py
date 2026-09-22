"""Unit tests for Tier 0 Fast-Path Compiler."""

import pytest
from modelnorth.engine.text_engine import TextGenerationEngine
from modelnorth.engine.decision_local import LocalDecisionEngine


@pytest.mark.asyncio
async def test_text_engine_heuristics():
    engine = TextGenerationEngine()
    
    # Test Origin extraction
    origin = await engine.generate_text("Where from?", "Find flights from Zurich to London on Sept 20")
    assert origin == "Zurich"

    # Test Destination extraction
    destination = await engine.generate_text("Where to?", "Find flights from Zurich to London on Sept 20")
    assert destination == "London"

    # Test Date extraction
    date_val = await engine.generate_text("Departure date", "Find flights from Zurich to London on Sept 20, 2026")
    assert "Sept 20" in date_val


def test_decision_engine_local_ranking():
    engine = LocalDecisionEngine()
    
    elements = [
        {"id": 1, "name": "Google", "role": "link"},
        {"id": 2, "name": "Where from? Origin airport", "role": "combobox", "value": "New York"},
        {"id": 3, "name": "Where to? Destination airport", "role": "combobox", "value": ""},
        {"id": 4, "name": "Search Flights", "role": "button"},
    ]

    # Predict destination
    decision = engine.predict("Enter London into where to destination", elements)
    assert decision.operation == "TYPE_TEXT"
    assert decision.target_id == 3
    assert decision.elapsed_ms < 15.0  # Must be sub-15ms locally

    # Predict search click
    decision_click = engine.predict("Click Search Flights button", elements)
    assert decision_click.operation == "CLICK"
    assert decision_click.target_id == 4
    assert decision_click.elapsed_ms < 15.0
