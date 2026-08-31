#!/usr/bin/env python3
"""Print current project status: version, test count, coverage, date.

Executable truth for the status claims in TODO.md / README.md. Run:

    uv run python scripts_status.py            # version + date (fast)
    uv run python scripts_status.py --tests    # + test/coverage (runs the suite, slow)

Verified 2026-08-31 on this host: `uv sync -p 3.12` first (see AGENTS.md gotcha).
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else "unknown"


def tests() -> tuple[str, str]:
    cmd = [sys.executable, "-m", "pytest", "-q", "--cov=mdkv", "--cov-report=term"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = proc.stdout
    m_count = re.search(r"(\d+) passed", out)
    m_cov = re.search(r"^TOTAL.*?(\d+)%", out, re.M)
    count = m_count.group(1) if m_count else "unknown"
    cov = f"{m_cov.group(1)}%" if m_cov else "unknown"
    return count, cov


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tests", action="store_true", help="also run the test suite")
    args = ap.parse_args()
    today = dt.date.today().isoformat()
    print(f"date: {today}")
    print(f"version: {version()}   (source: pyproject.toml)")
    if args.tests:
        count, cov = tests()
        print(f"tests: {count} passed   coverage: {cov}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
