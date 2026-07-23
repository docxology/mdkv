"""Test that __main__.py allows `python -m mdkv` execution."""
import subprocess
import sys


def test_python_m_mdkv_help():
    result = subprocess.run(
        [sys.executable, "-m", "mdkv", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "MDKV command-line interface" in result.stdout
    assert "init" in result.stdout
    assert "stats" in result.stdout
    assert "diff" in result.stdout


def test_python_m_mdkv_version():
    result = subprocess.run(
        [sys.executable, "-m", "mdkv", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "0.10" in result.stdout
