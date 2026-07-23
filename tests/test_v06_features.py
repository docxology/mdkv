"""Tests for v0.6.0 features: Track.__eq__, track_ids, move_track, search limit,
validate_track, reserved IDs, CLI --format, GUI /api/document/json and /api/import."""
import json
from datetime import datetime
from pathlib import Path

from click.testing import CliRunner

from mdkv import MDKVDocument, Track, validate_track, search_document
from mdkv.core.validate import validate_document, ValidationIssue
from mdkv.cli import main


def _doc() -> MDKVDocument:
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# P"))
    d.add_track(Track("notes", "commentary", None, "tracks/notes.md", "note"))
    d.add_track(Track("fr", "translation", "fr", "tracks/fr.md", "salut"))
    return d


# === Track.__eq__ ===

def test_track_eq_same():
    t1 = Track("p", "primary", "en", "tracks/p.md", "hi")
    t2 = Track("p", "primary", "en", "tracks/p.md", "hi")
    assert t1 == t2


def test_track_eq_different_content():
    t1 = Track("p", "primary", "en", "tracks/p.md", "hi")
    t2 = Track("p", "primary", "en", "tracks/p.md", "bye")
    assert t1 != t2


def test_track_eq_different_id():
    t1 = Track("p", "primary", "en", "tracks/p.md", "hi")
    t2 = Track("q", "primary", "en", "tracks/q.md", "hi")
    assert t1 != t2


def test_track_eq_not_track():
    t = Track("p", "primary", "en", "tracks/p.md", "hi")
    assert t != "not a track"
    assert t != 42


def test_track_hash_consistent():
    t1 = Track("p", "primary", "en", "tracks/p.md", "hi")
    t2 = Track("p", "primary", "en", "tracks/p.md", "hi")
    assert hash(t1) == hash(t2)


def test_track_in_set():
    t1 = Track("p", "primary", "en", "tracks/p.md", "hi")
    t2 = Track("p", "primary", "en", "tracks/p.md", "hi")
    s = {t1}
    assert t2 in s


# === track_ids property ===

def test_track_ids_property():
    d = _doc()
    assert d.track_ids == ["primary", "notes", "fr"]


def test_track_ids_empty():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    assert d.track_ids == []


# === move_track ===

def test_move_track_to_first():
    d = _doc()
    d.move_track("fr", None)
    assert d.track_ids[0] == "fr"
    assert d.track_ids == ["fr", "primary", "notes"]


def test_move_track_after_another():
    d = _doc()
    d.move_track("fr", "primary")
    assert d.track_ids == ["primary", "fr", "notes"]


def test_move_track_to_end():
    d = _doc()
    d.move_track("primary", "fr")
    assert d.track_ids == ["notes", "fr", "primary"]


def test_move_track_missing():
    d = _doc()
    import pytest
    with pytest.raises(KeyError):
        d.move_track("nonexistent", None)


def test_move_track_missing_after():
    d = _doc()
    import pytest
    with pytest.raises(KeyError):
        d.move_track("primary", "nonexistent")


# === search limit ===

def test_search_limit():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "a a a a a"))
    matches = search_document(d, pattern="a", limit=3)
    assert len(matches) == 3


def test_search_limit_zero():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "a a a"))
    matches = search_document(d, pattern="a", limit=0)
    assert len(matches) == 0


def test_search_no_limit_returns_all():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "a a a"))
    matches = search_document(d, pattern="a")
    assert len(matches) == 3


# === validate_track ===

def test_validate_track_clean():
    t = Track("p", "primary", "en", "tracks/p.md", "content")
    issues = validate_track(t)
    assert issues == []


def test_validate_track_empty_content():
    t = Track("p", "primary", "en", "tracks/p.md", "  ")
    issues = validate_track(t)
    assert any("empty content" in i.message for i in issues)


def test_validate_track_code_without_fences():
    t = Track("c", "code", "python", "tracks/c.md", "print('hi')")
    issues = validate_track(t)
    assert any("fenced" in i.message for i in issues)


def test_validate_track_translation_no_language():
    t = Track("t", "translation", None, "tracks/t.md", "salut")
    issues = validate_track(t)
    assert any("language" in i.message for i in issues)


# === reserved track IDs ===

def test_validate_reserved_id_all():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("all", "primary", "en", "tracks/all.md", "content"))
    issues = validate_document(d)
    assert any("reserved" in i.message for i in issues)


def test_validate_reserved_id_none():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("none", "primary", "en", "tracks/none.md", "content"))
    issues = validate_document(d)
    assert any("reserved" in i.message for i in issues)


def test_validate_normal_id_no_reserved_warning():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "content"))
    issues = validate_document(d)
    assert not any("reserved" in i.message for i in issues)


# === CLI --format ===

def test_cli_info_table_format(tmp_path: Path):
    from mdkv.storage import save_mdkv
    d = _doc()
    p = tmp_path / "doc.mdkv"
    save_mdkv(d, p)
    r = CliRunner().invoke(main, ["info", str(p), "--format", "table"])
    assert r.exit_code == 0
    assert "Title:" in r.output
    assert "primary" in r.output
    assert "ID" in r.output  # table header


def test_cli_info_json_format_default(tmp_path: Path):
    from mdkv.storage import save_mdkv
    d = _doc()
    p = tmp_path / "doc.mdkv"
    save_mdkv(d, p)
    r = CliRunner().invoke(main, ["info", str(p)])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert data["title"] == "T"


def test_cli_export_json(tmp_path: Path):
    from mdkv.storage import save_mdkv
    d = _doc()
    p = tmp_path / "doc.mdkv"
    save_mdkv(d, p)
    r = CliRunner().invoke(main, ["export", str(p), "--format", "json"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert data["title"] == "T"
    assert len(data["tracks"]) == 3


# === GUI /api/document/json and /api/import ===

def test_gui_document_json(tmp_path: Path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/document/json")
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "MDKV Demo"
    assert "tracks" in data
    assert len(data["tracks"]) == 5


def test_gui_import_endpoint(tmp_path: Path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    # Create a markdown file to import
    md_file = tmp_path / "import.md"
    md_file.write_text("# Imported content", encoding="utf-8")
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/import", json={"path": str(md_file), "id": "imported", "type": "commentary"})
    assert r.status_code == 200
    assert r.json()["track_id"] == "imported"
    # Verify the track was added
    r2 = c.get("/api/tracks")
    assert any(t["id"] == "imported" for t in r2.json())


def test_gui_import_missing_file(tmp_path: Path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/import", json={"path": str(tmp_path / "missing.md"), "id": "x"})
    assert r.status_code == 404


def test_gui_import_missing_id(tmp_path: Path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    md_file = tmp_path / "import.md"
    md_file.write_text("content", encoding="utf-8")
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/import", json={"path": str(md_file)})
    assert r.status_code == 422
