"""Tests for v0.9.0: CLI history/save-incremental commands, GUI /api/diff/view endpoint, coverage improvements."""
import json
from datetime import datetime
from pathlib import Path

from click.testing import CliRunner

from mdkv import load_mdkv
from mdkv.cli import main
from mdkv.core.history import TrackHistory
from mdkv.core.model import MDKVDocument as Doc
from mdkv.core.model import Track as Tr
from mdkv.core.registry import TrackTypeRegistry
from mdkv.storage import save_mdkv as sm
from mdkv.storage.io import save_mdkv_incremental


def _make_doc(tmp_path: Path) -> Path:
    d = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "# Primary\n\nHello"))
    d.add_track(Tr("rev1", "revision", None, "tracks/rev1.md", "# Revision 1\n\nUpdated content"))
    p = tmp_path / "doc.mdkv"
    sm(d, p)
    return p


# === CLI history ===

def test_cli_history_with_revisions(tmp_path: Path):
    """`--id` must filter; only the matching revision track is returned."""
    d = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "# P"))
    d.add_track(Tr("rev1", "revision", None, "tracks/rev1.md", "# Revision 1"))
    d.add_track(Tr("rev2", "revision", None, "tracks/rev2.md", "# Revision 2"))
    p = tmp_path / "doc.mdkv"
    sm(d, p)
    r = CliRunner().invoke(main, ["history", str(p), "--id", "rev1"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert [x["track_id"] for x in data] == ["rev1"]


def test_cli_history_filters_by_track_id(tmp_path: Path):
    """A track with no matching revision track reports none (regression for the
    prior behaviour that ignored --id and returned every revision)."""
    d = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "# P"))
    d.add_track(Tr("rev1", "revision", None, "tracks/rev1.md", "# Revision 1"))
    p = tmp_path / "doc.mdkv"
    sm(d, p)
    r = CliRunner().invoke(main, ["history", str(p), "--id", "primary"])
    assert r.exit_code == 0
    assert "No revision tracks" in r.output


def test_cli_history_no_revisions(tmp_path: Path):
    d = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "# P"))
    p = tmp_path / "no_revs.mdkv"
    sm(d, p)
    r = CliRunner().invoke(main, ["history", str(p), "--id", "primary"])
    assert r.exit_code == 0
    assert "No revision tracks" in r.output


# === CLI save-incremental ===

def test_cli_save_incremental_existing(tmp_path: Path):
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["save-incremental", str(p)])
    assert r.exit_code == 0
    assert "Saved" in r.output


def test_cli_save_incremental_new(tmp_path: Path):
    """Should fall back to full save for a nonexistent file — but CLI loads first."""
    p = _make_doc(tmp_path)
    r = CliRunner().invoke(main, ["save-incremental", str(p)])
    assert r.exit_code == 0


# === GUI /api/diff/view ===

def test_gui_diff_view(tmp_path: Path):
    from fastapi.testclient import TestClient

    from mdkv.demo import build_multitrack_demo_document
    from mdkv.gui.server import create_app, state
    from mdkv.storage import save_mdkv as sm

    state.path = tmp_path / "a.mdkv"
    state.doc = build_multitrack_demo_document()
    # Create a second doc
    other = tmp_path / "b.mdkv"
    other_doc = build_multitrack_demo_document()
    other_doc.title = "Different"
    sm(other_doc, other)

    app = create_app()
    c = TestClient(app)
    r = c.get("/api/diff/view", params={"other_path": str(other)})
    assert r.status_code == 200
    assert "<table" in r.text  # difflib.HtmlDiff outputs a table


def test_gui_diff_view_missing_file(tmp_path: Path):
    from fastapi.testclient import TestClient

    from mdkv.demo import build_multitrack_demo_document
    from mdkv.gui.server import create_app, state

    state.path = tmp_path / "a.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/diff/view", params={"other_path": str(tmp_path / "missing.mdkv")})
    assert r.status_code == 404


def test_gui_diff_view_no_doc():
    from fastapi.testclient import TestClient

    from mdkv.gui.server import create_app, state

    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/diff/view", params={"other_path": "/tmp/test.mdkv"})
    assert r.status_code == 400


# === Registry coverage improvements ===

def test_registry_heuristics():
    reg = TrackTypeRegistry()
    reg.register("custom", heuristics=lambda c: ["no code"] if "```" not in c else [])
    assert reg.check_heuristics("custom", "plain text") == ["no code"]
    assert reg.check_heuristics("custom", "```python\nx\n```") == []


def test_registry_check_heuristics_no_fn():
    reg = TrackTypeRegistry()
    reg.register("noheur")
    assert reg.check_heuristics("noheur", "content") == []


def test_registry_validate_no_fn():
    reg = TrackTypeRegistry()
    reg.register("novalid")
    assert reg.validate("novalid", "content") == []


def test_registry_unregister_missing():
    reg = TrackTypeRegistry()
    import pytest
    with pytest.raises(KeyError):
        reg.unregister("nonexistent")


# === History coverage improvements ===

def test_track_history_get_version_at_none():
    h = TrackHistory("test")
    assert h.get_version_at(datetime(2025, 1, 1)) is None


def test_track_history_restore_to_none():
    h = TrackHistory("test")
    assert h.restore_to(datetime(2025, 1, 1)) is None


# === Incremental save coverage ===

def test_incremental_save_corrupt_file(tmp_path: Path):
    """Should fall back to full save when file is corrupt."""
    doc = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "content"))
    p = tmp_path / "corrupt.mdkv"
    p.write_bytes(b"PK\x03\x04bogus")
    result = save_mdkv_incremental(doc, p)
    assert result is False  # fell back to full save
    assert load_mdkv(p).tracks["primary"].content == "content"


def test_incremental_save_no_manifest(tmp_path: Path):
    """Should fall back when manifest is missing."""
    import zipfile
    doc = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Tr("primary", "primary", "en", "tracks/primary.md", "content"))
    p = tmp_path / "no_manifest.mdkv"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("tracks/primary.md", "content")
    result = save_mdkv_incremental(doc, p)
    assert result is False  # fell back
    assert load_mdkv(p).tracks["primary"].content == "content"


# === Public API exports ===

def test_public_api_has_v08_exports():
    import mdkv
    assert hasattr(mdkv, "TrackHistory")
    assert hasattr(mdkv, "TrackVersion")
    assert hasattr(mdkv, "TrackTypeRegistry")
    assert hasattr(mdkv, "register_track_type")
    assert hasattr(mdkv, "get_registry")
    assert hasattr(mdkv, "search_document_async")
    assert hasattr(mdkv, "save_mdkv_incremental")
    assert "TrackHistory" in mdkv.__all__
    assert "search_document_async" in mdkv.__all__
    assert "save_mdkv_incremental" in mdkv.__all__
