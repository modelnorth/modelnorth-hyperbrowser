import argparse
import asyncio
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table

from modelnorth.agent import HyperAgent

console = Console(highlight=False)


async def run_cli(url: str, goal: str, headless: bool = False, max_steps: int = 20) -> None:
    console.print(f"[bold cyan]⚡ ModelNorth HyperBrowser[/bold cyan] starting on [underline]{url}[/underline]")
    console.print(f"[dim]Goal: {goal}[/dim]\n")

    table = Table(title="Execution Telemetry Stream", show_header=True, header_style="bold magenta")
    table.add_column("Step", style="dim", width=6)
    table.add_column("Tier", justify="center", width=8)
    table.add_column("Action", style="green", width=14)
    table.add_column("Target / Value", width=32)
    table.add_column("Step (ms)", justify="right", width=10)
    table.add_column("Total (ms)", justify="right", width=10)

    async with HyperAgent(url=url, goal=goal, headless=headless, max_steps=max_steps) as agent:
        async for step in agent.run():
            tier_badge = (
                "[bold cyan]Tier 0[/bold cyan]"
                if step.tier == 0
                else "[bold green]Tier 1[/bold green]"
                if step.tier == 1
                else "[bold yellow]Tier 2[/bold yellow]"
            )
            target_display = f"{step.target_name or ''}"
            if step.text:
                target_display += f" = '{step.text}'"

            table.add_row(
                str(step.step_number),
                tier_badge,
                step.action,
                target_display,
                f"{step.elapsed_ms:.1f}",
                f"{step.total_elapsed_ms:.1f}",
            )

    console.print(table)
    console.print("\n[bold green]✔ Task Execution Completed.[/bold green]")


def main() -> None:
    parser = argparse.ArgumentParser(description="ModelNorth HyperBrowser CLI")
    parser.add_argument("--url", type=str, required=True, help="Target URL to automate")
    parser.add_argument("--goal", type=str, required=True, help="Natural language objective")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--max-steps", type=int, default=20, help="Maximum execution steps")

    args = parser.parse_args()
    asyncio.run(run_cli(args.url, args.goal, headless=args.headless, max_steps=args.max_steps))


if __name__ == "__main__":
    main()
