from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from urllib.request import urlopen
from urllib.error import URLError


def wait_for(url: str, timeout_seconds: int = 15) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(url) as r:  # noqa: S310
                if r.status < 500:
                    return True
        except URLError:
            time.sleep(0.2)
    return False


def main() -> None:
    """Record a brief GUI demo and write video to docs/_static/gui_demo.webm.

    Requirements:
    - python -m pip install playwright
    - python -m playwright install chromium
    - Optional: ffmpeg available on PATH for GIF conversion (see README).
    """
    port = 8030
    base = f"http://127.0.0.1:{port}"
    out_dir = Path("docs/_static")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Start GUI server
    server_cmd = [sys.executable, "run_gui.py", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(server_cmd)  # noqa: S603
    try:
        if not wait_for(base + "/", timeout_seconds=20):
            raise RuntimeError("GUI did not start in time")

        # Record with Playwright
        from playwright.sync_api import sync_playwright  # type: ignore

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                record_video_dir=str(out_dir),
            )
            page = context.new_page()
            page.goto(base + "/")
            page.wait_for_selector("#trackFilters, iframe#right")

            # Interactions: toggle custom subset, then empty, then back to all
            # Uncheck "All"
            all_cb = page.locator("#track_all")
            all_cb.uncheck()
            time.sleep(0.4)

            # Click first 2 track checkboxes
            track_cbs = page.locator('input[type="checkbox"][data-track-id]')
            count = track_cbs.count()
            for i in range(min(2, count)):
                track_cbs.nth(i).check()
                time.sleep(0.3)

            # Show empty selection
            for i in range(min(2, count)):
                track_cbs.nth(i).uncheck()
                time.sleep(0.2)

            # Back to All
            all_cb.check()
            time.sleep(0.6)

            page.wait_for_timeout(500)
            context.close()
            browser.close()

        # Find the last recorded video and rename to gui_demo.webm
        videos = sorted(out_dir.glob("**/*.webm"), key=lambda p: p.stat().st_mtime)
        if videos:
            latest = videos[-1]
            target = out_dir / "gui_demo.webm"
            if target.exists():
                target.unlink()
            latest.rename(target)
            print(f"Recorded: {target}")
        else:
            print("No video was recorded.")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()


