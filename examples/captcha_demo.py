"""Canvas & CAPTCHA Sentry Demo with ModelNorth HyperBrowser."""

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
    goal = "Verify human check on Cloudflare challenge by clicking the turnstile verification checkbox."
    url = "https://2captcha.com/demo/cloudflare-turnstile"

    console.print("[bold magenta]👁️ Running ModelNorth Vision Sentry (Tier 2 Fallback)[/bold magenta]")
    console.print(f"[dim]Goal: {goal}[/dim]\n")

    async with HyperAgent(url=url, goal=goal, headless=False, max_steps=10) as agent:
        async for step in agent.run():
            console.print(
                f"[bold magenta][Tier {step.tier}][/bold magenta] {step.action} -> {step.target_name} "
                f"([yellow]{step.elapsed_ms:.1f}ms[/yellow]) | {step.notes}"
            )


if __name__ == "__main__":
    asyncio.run(main())
