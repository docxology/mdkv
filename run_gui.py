#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import importlib
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError


def ensure_module(mod: str, pip_name: str | None = None) -> None:
    try:
        importlib.import_module(mod)
        return
    except ImportError:
        pass
    # prefer uv, fallback to pip
    installer = None
    try:
        subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        installer = ["uv", "add"]
    except Exception:
        installer = [sys.executable, "-m", "pip", "install"]
    pkg = pip_name or mod
    subprocess.check_call([*installer, pkg])


def wait_for(url: str, timeout_seconds: int = 10) -> bool:
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
    parser = argparse.ArgumentParser(description="Launch MDKV GUI in your browser")
    parser.add_argument("--path", type=str, help="Optional path to .mdkv to open", default=None)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # ensure deps
    ensure_module("fastapi")
    ensure_module("uvicorn")

    # import after ensuring install
    from mdkv.gui import run as run_gui
    from mdkv.demo import write_demo_mdkv

    # start server in a background process using current interpreter
    env = dict(**os.environ)
    open_path = args.path
    if not open_path:
        demo_dir = Path("demo")
        demo_dir.mkdir(exist_ok=True)
        demo_file = demo_dir / "demo.mdkv"
        write_demo_mdkv(demo_file)
        open_path = str(demo_file)
    server_cmd = [
        sys.executable,
        "-c",
        (
            "from mdkv.gui import run;"
            f"run(host='{args.host}', port={args.port}, path={repr(open_path)})"
        ),
    ]
    proc = subprocess.Popen(server_cmd)  # noqa: S603

    url = f"http://{args.host}:{args.port}/"
    if wait_for(url, timeout_seconds=15):
        webbrowser.open(url)
    else:
        print(f"MDKV GUI server not responding at {url}")

    proc.wait()


if __name__ == "__main__":
    main()


