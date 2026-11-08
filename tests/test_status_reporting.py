"""Exercise status reporting through the real interpreter and pytest process."""
import datetime as dt
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_status_without_tests() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts_status.py")],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    fields = dict(line.split(": ", 1) for line in result.stdout.splitlines())
    assert dt.date.fromisoformat(fields["date"]) == dt.date.today()
    with (ROOT / "pyproject.toml").open("rb") as source:
        expected_version = tomllib.load(source)["project"]["version"]
    assert fields["version"].split()[0] == expected_version


@pytest.mark.parametrize("passes", [True, False])
def test_status_propagates_pytest_outcome(tmp_path: Path, passes: bool) -> None:
    module = tmp_path / "test_owned_status_probe.py"
    module.write_text(
        f"def test_owned_probe():\n    assert {passes!r}\n", encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts_status.py"), "--tests",
         str(module), "-q", "--color=no"],
        cwd=ROOT, capture_output=True, text=True,
    )
    outcome = result.stdout + result.stderr
    assert result.returncode == (0 if passes else 1), outcome
    assert ("1 passed" if passes else "1 failed") in outcome
    if not passes:
        assert "test_owned_probe" in outcome
        assert "AssertionError" in outcome
