"""Tests for v0.7.0 features: CLI search --limit, move-track, export --format json/pdf/epub/docx,
batch commands, completions, GUI move-track/validate-track/search-limit, save_mdkv compression."""
import json
import zipfile
from datetime import datetime
from pathlib import Path

from click.testing import CliRunner

from mdkv import MDKVDocument, Track, save_mdkv, load_mdkv
from mdkv.cli import main
from mdkv.core.model import MDKVDocument as Doc, Track as Tr
from mdkv.storage import save_mdkv as sm
from mdkv.services.pandoc_export import _check_pandoc, to_pdf, to_epub, to_docx
import pytest


def _make_doc(tmp_path: Path) -> Path:
    d = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "# Primary\n\nHello world"))
    d.add_track(Tr("notes", "commentary", None, "tracks/notes.md", "# Notes\n\nSome note"))
    p = tmp_path / "doc.mdkv"
    sm(d, p)
    return p


# === CLI search --limit ===

def test_cli_search_limit(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["search", str(p), "--pattern", ".", "--limit", "1"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert len(data) == 1


# === CLI move-track ===

def test_cli_move_track(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["move-track", str(p), "--id", "notes", "--after-id", "primary"])
    assert r.exit_code == 0
    # Verify order: primary, notes (notes was already after primary, but test the command works)
    r2 = CliRunner().invoke(main, ["list-tracks", str(p)])
    ids = [t["id"] for t in json.loads(r2.output)]
    assert "notes" in ids


def test_cli_move_track_to_first(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["move-track", str(p), "--id", "notes"])
    assert r.exit_code == 0
    r2 = CliRunner().invoke(main, ["list-tracks", str(p)])
    ids = [t["id"] for t in json.loads(r2.output)]
    assert ids[0] == "notes"


def test_cli_move_track_missing(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["move-track", str(p), "--id", "nonexistent"])
    assert r.exit_code != 0


# === CLI export --format json with --types ===

def test_cli_export_json_with_types(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["export", str(p), "--format", "json", "--types", "primary"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert len(data["tracks"]) == 1
    assert data["tracks"][0]["track_type"] == "primary"


# === CLI batch ===

def test_cli_batch_validate(tmp_path: Path):
    p1 = _make_doc(tmp_path)
    p2 = tmp_path / "doc2.mdkv"
    sm(Doc(title="T2", authors=["B"], created=datetime(2025, 1, 1)), p2) if False else None
    import shutil
    shutil.copy2(p1, p2)
    r = CliRunner().invoke(main, ["batch", "validate", str(p1), str(p2)])
    assert r.exit_code == 0
    assert "OK" in r.output


def test_cli_batch_validate_json(tmp_path: Path):
    p1 = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["batch", "validate", str(p1), "--json"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert len(data) == 1
    assert data[0]["ok"] is True


def test_cli_batch_stats(tmp_path: Path):
    p1 = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["batch", "stats", str(p1)])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert len(data) == 1
    assert data[0]["title"] == "T"


# === CLI completions ===

def test_cli_completions_bash():
    r = CliRunner().invoke(main, ["completions", "bash"])
    assert r.exit_code == 0
    assert "bash" in r.output


def test_cli_completions_zsh():
    r = CliRunner().invoke(main, ["completions", "zsh"])
    assert r.exit_code == 0
    assert "zsh" in r.output


# === save_mdkv compression ===

def test_save_mdkv_compression_levels(tmp_path: Path):
    doc = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "x" * 10000))
    p1 = tmp_path / "level1.mdkv"
    p9 = tmp_path / "level9.mdkv"
    save_mdkv(doc, p1, compresslevel=1)
    save_mdkv(doc, p9, compresslevel=9)
    # Both should load correctly
    assert load_mdkv(p1).tracks["primary"].content == "x" * 10000
    assert load_mdkv(p9).tracks["primary"].content == "x" * 10000


def test_save_mdkv_stored_no_compression(tmp_path: Path):
    doc = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "content"))
    p = tmp_path / "stored.mdkv"
    save_mdkv(doc, p, compression=zipfile.ZIP_STORED)
    loaded = load_mdkv(p)
    assert loaded.tracks["primary"].content == "content"


# === Pandoc export (skip if pandoc not installed) ===


def _check_pandoc_safe():
    try:
        _check_pandoc()
        return True
    except FileNotFoundError:
        return False


_has_pandoc = _check_pandoc_safe()


@pytest.mark.skipif(not _check_pandoc_safe(), reason="pandoc not installed")
def test_to_pdf(tmp_path: Path):
    doc = Doc(title="Test PDF", authors=["Author"], created=datetime(2025, 1, 1))
    doc.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "# Hello PDF\n\nThis is a test."))
    out = tmp_path / "output.pdf"
    result = to_pdf(doc, out, metadata_header=True)
    assert result.exists()
    assert result.stat().st_size > 0


@pytest.mark.skipif(not _check_pandoc_safe(), reason="pandoc not installed")
def test_to_epub(tmp_path: Path):
    doc = Doc(title="Test EPUB", authors=["Author"], created=datetime(2025, 1, 1))
    doc.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "# Hello EPUB\n\nThis is a test."))
    out = tmp_path / "output.epub"
    result = to_epub(doc, out, metadata_header=True)
    assert result.exists()
    assert result.stat().st_size > 0


@pytest.mark.skipif(not _check_pandoc_safe(), reason="pandoc not installed")
def test_to_docx(tmp_path: Path):
    doc = Doc(title="Test DOCX", authors=["Author"], created=datetime(2025, 1, 1))
    doc.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "# Hello DOCX\n\nThis is a test."))
    out = tmp_path / "output.docx"
    result = to_docx(doc, out, metadata_header=True)
    assert result.exists()
    assert result.stat().st_size > 0


def test_pandoc_export_without_pandoc(tmp_path: Path, monkeypatch):
    """If pandoc is not installed, should raise FileNotFoundError."""
    import mdkv.services.pandoc_export as pe
    monkeypatch.setattr(pe.shutil, "which", lambda x: None)
    doc = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "# Hi"))
    with pytest.raises(FileNotFoundError, match="pandoc"):
        to_pdf(doc, tmp_path / "out.pdf")


# === GUI new endpoints ===

def test_gui_move_track(tmp_path: Path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    # Move primary to first position
    r = c.post("/api/move-track", json={"track_id": "primary", "after_id": None})
    assert r.status_code == 200
    assert r.json()["track_ids"][0] == "primary"


def test_gui_move_track_missing(tmp_path: Path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/move-track", json={"track_id": "nonexistent"})
    assert r.status_code == 404


def test_gui_validate_track(tmp_path: Path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/validate-track", params={"track_id": "primary"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True


def test_gui_validate_track_missing(tmp_path: Path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/validate-track", params={"track_id": "nonexistent"})
    assert r.status_code == 404


def test_gui_search_limit(tmp_path: Path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/search", params={"pattern": ".", "limit": 2})
    assert r.status_code == 200
    assert len(r.json()["matches"]) <= 2
