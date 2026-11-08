#!/usr/bin/env python3
"""Print source version and date; optionally run pytest in the current environment.

    python scripts_status.py
    python scripts_status.py --tests
    python scripts_status.py --tests path/to/test_module.py -q
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as source:
        return tomllib.load(source)["project"]["version"]


def tests(pytest_args: list[str]) -> int:
    args = pytest_args or ["-q", "--cov=mdkv", "--cov-report=term"]
    return subprocess.run([sys.executable, "-m", "pytest", *args], cwd=ROOT).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tests", nargs=argparse.REMAINDER, metavar="PYTEST_ARG",
                    help="run pytest, optionally with explicit pytest arguments")
    args = ap.parse_args()
    print(f"date: {dt.date.today().isoformat()}", flush=True)
    print(f"version: {version()}   (source: pyproject.toml)", flush=True)
    if args.tests is not None:
        return tests(args.tests)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
