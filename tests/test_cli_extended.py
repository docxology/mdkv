import json
from datetime import datetime
from pathlib import Path

from click.testing import CliRunner

from mdkv.cli import main
from mdkv.core.model import MDKVDocument, Track
from mdkv.storage import save_mdkv


def _make_doc(tmp_path: Path) -> Path:
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "alpha beta"))
    p = tmp_path / "doc.mdkv"
    save_mdkv(d, p)
    return p


def test_cli_rename_and_update_track(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["rename-track", str(p), "--old-id", "p", "--new-id", "primary"])
    assert r.exit_code == 0
    r2 = CliRunner().invoke(main, ["update-track", str(p), "--id", "primary", "--content", "alpha beta gamma"])
    assert r2.exit_code == 0


def test_cli_metadata_and_search(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["set-meta", str(p), "author", "B"])
    assert r.exit_code == 0
    r2 = CliRunner().invoke(main, ["get-meta", str(p), "author"])
    assert r2.exit_code == 0 and r2.output.strip() == "B"
    r3 = CliRunner().invoke(main, ["search", str(p), "--pattern", "beta", "--types", "primary"]) 
    assert r3.exit_code == 0
    data = json.loads(r3.output)
    assert any(m["track_id"] == "p" or m["track_id"] == "primary" for m in data)


