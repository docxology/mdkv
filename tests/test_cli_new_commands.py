"""Tests for new CLI commands: remove-track, import, diff, stats, export --types, export --out-dir."""
import json
from datetime import datetime
from pathlib import Path

from click.testing import CliRunner

from mdkv.cli import main
from mdkv.core.model import MDKVDocument, Track
from mdkv.storage import save_mdkv


def _make_doc(tmp_path: Path) -> Path:
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Primary\n\nHello world"))
    d.add_track(Track("notes", "commentary", None, "tracks/notes.md", "# Notes\n\nSome note"))
    p = tmp_path / "doc.mdkv"
    save_mdkv(d, p)
    return p


def test_cli_remove_track(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["remove-track", str(p), "--id", "notes"])
    assert r.exit_code == 0
    # Verify the track is gone
    r2 = CliRunner().invoke(main, ["list-tracks", str(p)])
    assert r2.exit_code == 0
    ids = [t["id"] for t in json.loads(r2.output)]
    assert "notes" not in ids
    assert "primary" in ids


def test_cli_remove_track_missing(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["remove-track", str(p), "--id", "nonexistent"])
    assert r.exit_code != 0


def test_cli_import(tmp_path: Path):
    md_file = tmp_path / "input.md"
    md_file.write_text("# Imported\n\nThis is imported content.", encoding="utf-8")
    out = tmp_path / "imported.mdkv"
    r = CliRunner().invoke(main, [
        "import", str(md_file),
        "--out", str(out),
        "--title", "Imported Doc",
        "--author", "Tester",
    ])
    assert r.exit_code == 0
    assert out.exists()
    # Verify content
    r2 = CliRunner().invoke(main, ["info", str(out)])
    assert r2.exit_code == 0
    info = json.loads(r2.output)
    assert info["title"] == "Imported Doc"


def test_cli_diff_identical(tmp_path: Path):
    p1 = _make_doc(tmp_path)
    p2 = tmp_path / "copy.mdkv"
    import shutil
    shutil.copy2(p1, p2)
    r = CliRunner().invoke(main, ["diff", str(p1), str(p2)])
    assert r.exit_code == 0
    assert "No differences" in r.output


def test_cli_diff_with_changes(tmp_path: Path):
    p1 = _make_doc(tmp_path)
    p2 = tmp_path / "modified.mdkv"
    doc2 = MDKVDocument(title="T2", authors=["B"], created=datetime(2025, 1, 1))
    doc2.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Modified content"))
    doc2.add_track(Track("extra", "commentary", None, "tracks/extra.md", "new"))
    save_mdkv(doc2, p2)
    r = CliRunner().invoke(main, ["diff", str(p1), str(p2)])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert "title_changed" in data and len(data["title_changed"]) == 2
    assert "extra" in data["tracks_added"]
    assert "notes" in data["tracks_removed"]


def test_cli_stats(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["stats", str(p)])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert data["track_count"] == 2
    assert data["title"] == "T"
    assert "primary" in data["tracks_by_type"]
    assert data["total_characters"] > 0
    assert data["total_lines"] > 0


def test_cli_export_html_with_types(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["export", str(p), "--html", "--types", "primary,commentary"])
    assert r.exit_code == 0
    assert "Primary" in r.output
    assert "Notes" in r.output


def test_cli_export_out_dir(tmp_path: Path):
    p = _make_doc(tmp_path)
    out_dir = tmp_path / "exported"
    r = CliRunner().invoke(main, ["export", str(p), "--out-dir", str(out_dir)])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert len(data["files"]) == 2
    assert (out_dir / "primary.md").exists()
    assert (out_dir / "notes.md").exists()


def test_cli_validate_shows_warnings(tmp_path: Path):
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "content"))
    d.add_track(Track("notes", "commentary", None, "tracks/notes.md", "  "))  # empty → warn
    d.version = "bad"  # bad version → warn
    p = tmp_path / "warn.mdkv"
    save_mdkv(d, p)
    r = CliRunner().invoke(main, ["validate", str(p)])
    assert r.exit_code == 0  # warnings don't cause failure
    assert "WARN" in r.output
