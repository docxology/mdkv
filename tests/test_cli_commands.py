import json
from datetime import datetime
from pathlib import Path

from click.testing import CliRunner

from mdkv.cli import main
from mdkv.core.model import MDKVDocument, Track
from mdkv.storage import save_mdkv


def make_doc(tmp_path: Path) -> Path:
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# P"))
    p = tmp_path / "doc.mdkv"
    save_mdkv(d, p)
    return p


def test_cli_info_list_tracks_export(tmp_path: Path):
    p = make_doc(tmp_path)
    r = CliRunner().invoke(main, ["info", str(p)])
    assert r.exit_code == 0 and json.loads(r.output)["title"] == "T"
    r2 = CliRunner().invoke(main, ["list-tracks", str(p)])
    assert r2.exit_code == 0 and any(t["id"] == "primary" for t in json.loads(r2.output))
    r3 = CliRunner().invoke(main, ["export-tracks", str(p), "--types", "primary"])
    assert r3.exit_code == 0 and "# P" in r3.output


def test_cli_add_rename_update_meta_validate_search(tmp_path: Path):
    p = make_doc(tmp_path)
    # add
    r = CliRunner().invoke(main, ["add-track", str(p), "--id", "n", "--type", "commentary", "--lang", "", "--content", "note"])
    assert r.exit_code == 0
    # rename
    r2 = CliRunner().invoke(main, ["rename-track", str(p), "--old-id", "n", "--new-id", "notes"])
    assert r2.exit_code == 0
    # update
    r3 = CliRunner().invoke(main, ["update-track", str(p), "--id", "notes", "--content", "updated"])
    assert r3.exit_code == 0
    # metadata
    r4 = CliRunner().invoke(main, ["set-meta", str(p), "author", "B"])
    assert r4.exit_code == 0
    r5 = CliRunner().invoke(main, ["get-meta", str(p), "author"])
    assert r5.exit_code == 0 and r5.output.strip() == "B"
    # validate
    r6 = CliRunner().invoke(main, ["validate", str(p)])
    assert r6.exit_code == 0 and r6.output.strip() == "OK"
    # search
    r7 = CliRunner().invoke(main, ["search", str(p), "--pattern", "P"]) 
    assert r7.exit_code == 0 and len(json.loads(r7.output)) >= 1


