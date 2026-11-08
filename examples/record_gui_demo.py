from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import URLError
from urllib.request import urlopen


def wait_for(url: str, timeout_seconds: int = 15) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=0.5) as r:  # noqa: S310
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

    target = out_dir / "gui_demo.webm"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")

    # This invocation owns the fixture and server lifetime, not demo/demo.mdkv.
    fixture_directory = TemporaryDirectory(prefix="mdkv-recording-fixture-", dir=out_dir)
    from mdkv.demo import write_demo_mdkv

    fixture = Path(fixture_directory.name) / "owned.mdkv"
    write_demo_mdkv(fixture)
    server_cmd = [sys.executable, "run_gui.py", "--path", str(fixture),
                  "--no-browser", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(server_cmd, stdin=subprocess.DEVNULL)  # noqa: S603
    try:
        if not wait_for(base + "/", timeout_seconds=20):
            raise RuntimeError("GUI did not start in time")

        # Record with Playwright
        from playwright.sync_api import sync_playwright  # type: ignore

        with TemporaryDirectory(prefix="mdkv-recording-") as recording_dir, sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                record_video_dir=recording_dir,
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

            # Only publish a recording produced by this invocation.
            videos = sorted(Path(recording_dir).glob("*.webm"))
            if len(videos) != 1:
                raise RuntimeError(f"Expected one recording, found {len(videos)}")
            with videos[0].open("rb") as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            print(f"Recorded: {target}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        fixture_directory.cleanup()


if __name__ == "__main__":
    main()


