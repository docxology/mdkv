#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def wait_for(url: str, timeout_seconds: int = 10) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=0.5) as response:  # noqa: S310
                if response.status < 500:
                    return True
        except (URLError, OSError):
            time.sleep(0.2)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch MDKV GUI using installed dependencies")
    parser.add_argument("--path", type=Path, required=True, help="Existing .mdkv fixture to open (saving modifies this file)")
    parser.add_argument("--host", choices=("127.0.0.1", "localhost", "::1"), default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="Run without opening a browser")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    path = args.path.expanduser().resolve()
    if not path.is_file():
        parser.error("--path must name an existing .mdkv file")
    missing = [name for name in ("fastapi", "uvicorn", "markdown_it") if importlib.util.find_spec(name) is None]
    if missing:
        parser.error("missing installed GUI dependencies: " + ", ".join(missing) + "; run uv sync --extra dev first")
    # Arguments remain data: no generated Python or shell interpolation.
    command = [sys.executable, "-m", "mdkv", "gui", "--host", args.host,
               "--port", str(args.port), "--path", str(path)]
    proc = subprocess.Popen(command)  # noqa: S603
    import signal

    def stop_server(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop_server)
    try:
        if not args.no_browser:
            host = f"[{args.host}]" if ":" in args.host else args.host
            url = f"http://{host}:{args.port}/"
            if wait_for(url, timeout_seconds=15):
                webbrowser.open(url)
            else:
                print(f"MDKV GUI server not responding at {url}", file=sys.stderr)
        returncode = proc.wait()
    except KeyboardInterrupt:
        returncode = 130
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
    raise SystemExit(returncode)


if __name__ == "__main__":
    main()
