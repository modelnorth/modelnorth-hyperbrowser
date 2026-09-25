"""ModelNorth HyperBrowser: Automated Video Demo Recorder.

Records high-resolution browser interaction videos and converts to MP4 / WebM / GIF for documentation.
"""

import asyncio
import os
import shutil
import subprocess
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
    video_dir = Path("docs/videos")
    video_dir.mkdir(parents=True, exist_ok=True)

    console.print("[bold cyan]⚡ Recording ModelNorth HyperBrowser Benchmark Demo[/bold cyan]")
    console.print(f"[dim]Goal: {goal}[/dim]\n")

    # Run browser session with video recording enabled
    async with HyperAgent(
        url=url,
        goal=goal,
        headless=True,
        max_steps=15,
        record_video_dir=str(video_dir),
    ) as agent:
        async for step in agent.run():
            tier_str = f"Tier {step.tier}"
            color = "cyan" if step.tier == 0 else "green" if step.tier == 1 else "magenta"
            console.print(
                f"[{color}][{tier_str}][/{color}] {step.action} -> [bold]{step.target_name}[/bold] "
                f"([yellow]{step.elapsed_ms:.1f}ms[/yellow] | total: {step.total_elapsed_ms:.1f}ms)"
            )

    # Find the recorded video
    recorded_files = list(video_dir.glob("*.webm"))
    if recorded_files:
        latest_video = max(recorded_files, key=os.path.getctime)
        target_webm = Path("docs/demo.webm")
        target_mp4 = Path("docs/demo.mp4")
        target_gif = Path("docs/demo.gif")

        # 1. Copy webm
        shutil.copyfile(latest_video, target_webm)
        console.print(f"\n[bold green]✔ WebM Demo Saved: {target_webm}[/bold green]")

        # 2. Convert to MP4 using ffmpeg if available
        try:
            cmd_mp4 = [
                "ffmpeg", "-y", "-i", str(target_webm),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "faststart",
                str(target_mp4)
            ]
            subprocess.run(cmd_mp4, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            console.print(f"[bold green]✔ MP4 Demo Saved: {target_mp4}[/bold green]")
        except Exception as e:
            console.print(f"[yellow]MP4 conversion skipped: {e}[/yellow]")

        # 3. Generate preview GIF
        try:
            cmd_gif = [
                "ffmpeg", "-y", "-i", str(target_webm),
                "-vf", "fps=10,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                "-loop", "0",
                str(target_gif)
            ]
            subprocess.run(cmd_gif, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            console.print(f"[bold green]✔ Animated GIF Demo Saved: {target_gif}[/bold green]")
        except Exception as e:
            console.print(f"[yellow]GIF conversion skipped: {e}[/yellow]")


if __name__ == "__main__":
    asyncio.run(main())
