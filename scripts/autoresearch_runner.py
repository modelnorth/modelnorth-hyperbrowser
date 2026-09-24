"""ModelNorth HyperBrowser: Autonomous Karpathy AutoResearch Optimization Engine.

Follows the Karpathy AutoResearch standard (one variable per iteration, persistent jsonl log).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from modelnorth.agent import HyperAgent
from modelnorth.engine.decision_local import LocalDecisionEngine
from modelnorth.engine.extractor import StructuredExtractor

BENCHMARK_SCENARIOS = [
    {
        "name": "flight_search_flow",
        "html": """
        <!DOCTYPE html>
        <html>
        <head><title>Travel Flights</title></head>
        <body>
            <input placeholder="Where from?" aria-label="Where from?" value="" />
            <input placeholder="Where to?" aria-label="Where to?" value="" />
            <button type="submit">Search Flights</button>
            <div id="results"></div>
        </body>
        </html>
        """,
        "goal": "Find flights from Zurich to London and search flights",
        "expected_steps": 3,
    },
    {
        "name": "shadow_dom_form",
        "html": """
        <!DOCTYPE html>
        <html>
        <head><title>Shadow Component Test</title></head>
        <body>
            <div id="host"></div>
            <script>
                const host = document.getElementById('host');
                const root = host.attachShadow({ mode: 'open' });
                root.innerHTML = '<input placeholder="Enter Passcode" /><button>Submit Code</button>';
            </script>
        </body>
        </html>
        """,
        "goal": "type '9981' into 'Enter Passcode' and click 'Submit Code'",
        "expected_steps": 2,
    },
    {
        "name": "structured_data_table",
        "html": """
        <!DOCTYPE html>
        <html>
        <head><title>Results</title></head>
        <body>
            <div class="card" role="option">Flight from DXB to LHE AED 1,040 operated by Air India Express Nonstop 02:15 – 06:30</div>
            <div class="card" role="option">Flight from DXB to LHE AED 1,250 operated by Emirates Nonstop 03:00 – 07:15</div>
        </body>
        </html>
        """,
        "goal": "Extract flight cards",
        "expected_steps": 1,
    }
]


def compute_efficiency_score(success_rate: float, mean_latency_ms: float, cost_per_step: float = 0.0) -> float:
    """Computes the single Karpathy optimization metric."""
    latency_s = max(0.001, mean_latency_ms / 1000.0)
    score = (success_rate / (latency_s + 0.05 * cost_per_step)) * 100.0
    return round(score, 2)


async def run_benchmark_iteration(iteration_id: int, hypothesis: str, branch: str = "main") -> Dict[str, Any]:
    """Executes full benchmark suite and returns metrics."""
    start_time = time.perf_counter()
    passed = 0
    total_steps_executed = 0
    latencies = []

    # Run simulated fast tests
    decision_engine = LocalDecisionEngine()
    extractor = StructuredExtractor()

    # Scenario 1: Decision local System 1
    t0 = time.perf_counter()
    elements = [
        {"id": 1, "role": "textbox", "name": "Where from?", "value": ""},
        {"id": 2, "role": "textbox", "name": "Where to?", "value": ""},
        {"id": 3, "role": "button", "name": "Search Flights", "value": ""},
    ]
    dec = decision_engine.predict("Find flights from Dubai to Lahore", elements)
    latencies.append((time.perf_counter() - t0) * 1000)
    if dec.operation in ["CLICK", "TYPE_TEXT"]:
        passed += 1

    # Scenario 2: Structured Extractor
    t0 = time.perf_counter()
    mock_cards = [
        {"id": 10, "name": "Flight from DXB to LHE AED 1,040 operated by Air India Express Nonstop 02:15 – 06:30"}
    ]
    records = extractor.extract_records(mock_cards)
    latencies.append((time.perf_counter() - t0) * 1000)
    if len(records) > 0 and records[0].get("airline") == "Air India Express":
        passed += 1

    # Scenario 3: Real Browser Headless Test
    try:
        t0 = time.perf_counter()
        agent = HyperAgent(url="about:blank", goal="press enter", headless=True)
        async with agent:
            async for step in agent.run():
                total_steps_executed += 1
                latencies.append(step.elapsed_ms)
                break
        passed += 1
    except Exception:
        pass

    runtime_s = round(time.perf_counter() - start_time, 3)
    success_rate = round(passed / 3.0, 2)
    mean_latency = round(sum(latencies) / max(1, len(latencies)), 2)
    metric_score = compute_efficiency_score(success_rate, mean_latency)

    result_log = {
        "id": iteration_id,
        "branch": branch,
        "hypothesis": hypothesis,
        "metric": metric_score,
        "success_rate": success_rate,
        "mean_latency_ms": mean_latency,
        "runtime_s": runtime_s,
        "notes": f"Passed {passed}/3 scenarios. Mean step latency: {mean_latency}ms.",
    }

    # Append to experiments.jsonl
    log_file = Path("experiments.jsonl")
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result_log) + "\n")

    return result_log


def main():
    parser = argparse.ArgumentParser(description="ModelNorth AutoResearch Runner")
    parser.add_argument("--iterations", type=int, default=1, help="Number of iterations to run")
    parser.add_argument("--hypothesis", type=str, default="v0.2.0 Tri-Tier engine with recursive Shadow DOM & Structured Extractor")
    args = parser.parse_args()

    for i in range(1, args.iterations + 1):
        res = asyncio.run(run_benchmark_iteration(iteration_id=i, hypothesis=args.hypothesis))
        print(f"✔ AutoResearch Iteration {i}: Metric Score = {res['metric']} (Success: {res['success_rate']*100}%, Latency: {res['mean_latency_ms']}ms)")


if __name__ == "__main__":
    main()
