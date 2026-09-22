"""Google Flights Benchmark Demo with ModelNorth HyperBrowser."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console

from modelnorth.agent import HyperAgent

console = Console(highlight=False)


async def main():
    goal = (
        "Find one-way flights from Dubai (DXB) to Lahore (LHE) on September 20, 2026, "
        "for one adult in economy. Stop when flight list is visible."
    )
    url = "https://www.google.com/travel/flights?hl=en"

    console.print("[bold cyan]🚀 Running ModelNorth HyperBrowser Benchmark[/bold cyan]")
    console.print(f"[dim]Goal: {goal}[/dim]\n")

    async with HyperAgent(url=url, goal=goal, headless=False, max_steps=15) as agent:
        async for step in agent.run():
            tier_str = f"Tier {step.tier}"
            color = "cyan" if step.tier == 0 else "green" if step.tier == 1 else "magenta"
            console.print(
                f"[{color}][{tier_str}][/{color}] {step.action} -> [bold]{step.target_name}[/bold] "
                f"([yellow]{step.elapsed_ms:.1f}ms[/yellow] | total: {step.total_elapsed_ms:.1f}ms)"
            )

    console.print(f"\n[bold green]✔ Benchmark Complete in {agent.state.steps[-1].total_elapsed_ms:.1f}ms[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
