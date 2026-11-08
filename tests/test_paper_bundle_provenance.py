"""Bundle provenance records source custody, not its own generated outputs."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml


@pytest.mark.parametrize("custody,expected_dirty", [("clean", False), ("dirty", True), ("unavailable", None)])
def test_bundle_records_pre_generation_source_custody(tmp_path: Path, custody: str, expected_dirty: bool | None):
    source_root = Path(__file__).resolve().parents[1]
    project = tmp_path / "owned-source-fixture"
    paper = project / "paper"
    paper.mkdir(parents=True)
    hooks = project / "empty-hooks"
    hooks.mkdir()
    builder = paper / "build_paper_bundle.py"
    shutil.copyfile(source_root / "paper/build_paper_bundle.py", builder)
    shutil.copyfile(source_root / "uv.lock", project / "uv.lock")
    manuscript = paper / "mdkv_paper.md"
    manuscript.write_text(
        "---\ntitle: Synthetic provenance fixture\nauthors: [Synthetic Author]\n"
        "created: 2026-01-01T00:00:00Z\n---\n# Synthetic body\n\n"
        "![Synthetic figure](figures/graphic.png)\n", encoding="utf-8",
    )
    figures = paper / "figures"
    figures.mkdir()
    (figures / "graphic.png").write_bytes(b"synthetic-figure")

    def git(*arguments: str) -> str:
        result = subprocess.run(
            ["git", "-c", f"core.hooksPath={hooks}", "-c", "commit.gpgsign=false",
             "-c", "user.name=MDKV test fixture", "-c", "user.email=fixture@example.invalid",
             *arguments], cwd=project, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, check=True, timeout=30,
        )
        return result.stdout.strip()

    git("init", "--quiet", "--initial-branch=main", f"--template={hooks}")
    git("add", "paper", "uv.lock")
    git("commit", "--quiet", "-m", "Synthetic source fixture")
    commit = git("rev-parse", "HEAD")
    assert git("status", "--porcelain") == ""
    environment = dict(os.environ)
    if custody == "dirty":
        manuscript.write_text(manuscript.read_text(encoding="utf-8") + "Changed source.\n", encoding="utf-8")
    elif custody == "unavailable":
        environment["PATH"] = str(hooks)  # Real missing Git, not a mocked reader.
    result = subprocess.run(
        [sys.executable, str(builder), "--no-clone"], cwd=project, env=environment,
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    info = yaml.safe_load((paper / "_bundle/BUNDLE_INFO.yaml").read_text(encoding="utf-8"))
    assert info["builder_dirty"] is expected_dirty
    assert info["builder_commit"] == (None if custody == "unavailable" else commit)
    assert info["source_sha256"] == hashlib.sha256(manuscript.read_bytes()).hexdigest()
    assert (paper / "_bundle/figures/graphic.png").read_bytes() == b"synthetic-figure"
    checksums = yaml.safe_load((paper / "_bundle/CHECKSUMS.yaml").read_text(encoding="utf-8"))
    assert checksums["_bundle/figures/graphic.png"] == hashlib.sha256(b"synthetic-figure").hexdigest()
    assert git("status", "--porcelain") != ""  # Generated outputs exist only after the observation.
