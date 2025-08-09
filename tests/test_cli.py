import json
from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from mdkv.cli import main
from mdkv.model import MDKVDocument, Track
from mdkv.io import save_mdkv


def _make_doc(tmp_path: Path) -> Path:
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# T"))
    path = tmp_path / "doc.mdkv"
    save_mdkv(doc, path)
    return path


def test_cli_list_tracks(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["list-tracks", str(p)])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert any(t["id"] == "primary" for t in data)


def test_cli_add_track_and_export_tracks(tmp_path: Path):
    p = _make_doc(tmp_path)
    # add a commentary track
    r = CliRunner().invoke(
        main,
        [
            "add-track",
            str(p),
            "--id",
            "notes",
            "--type",
            "commentary",
            "--lang",
            "",
            "--content",
            "Note",
        ],
    )
    assert r.exit_code == 0

    # export only primary and commentary tracks as markdown
    r2 = CliRunner().invoke(
        main,
        [
            "export-tracks",
            str(p),
            "--types",
            "primary,commentary",
        ],
    )
    assert r2.exit_code == 0
    out = r2.output
    assert "Note" in out and "# T" in out


