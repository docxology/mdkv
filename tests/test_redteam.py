"""Red-team tests: security fixes, edge cases, and error handling."""
import json
import zipfile
from datetime import datetime

import pytest
import yaml
from click.testing import CliRunner

from mdkv import MDKVDocument, Track, save_mdkv, load_mdkv
from mdkv.core.model import MDKVDocument as Doc, Track as Tr
from mdkv.core.errors import ValidationError
from mdkv.storage import MDKVFormatError
from mdkv.services.export import to_markdown, to_html, export_to_files, _safe_filename
from mdkv.services.search import search_document
from mdkv.cli import main


# ============================================================
# SECURITY: Path traversal in export_to_files
# ============================================================

def test_safe_filename_strips_path_traversal():
    assert _safe_filename("../../etc/passwd") == "passwd"
    assert _safe_filename("../../../tmp/evil") == "evil"
    assert _safe_filename("normal_id") == "normal_id"


def test_safe_filename_strips_directory_components():
    assert _safe_filename("foo/bar") == "bar"
    assert _safe_filename("foo\\bar") == "foo_bar"


def test_export_to_files_prevents_path_traversal(tmp_path):
    """A track with a malicious track_id cannot escape output_dir."""
    doc = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    # Manually create a track with a path-traversal track_id
    # (Track.__post_init__ validates path starts with 'tracks/', so we set
    # track_id after construction)
    t = Tr("safe", "primary", "en", "tracks/safe.md", "content")
    t.track_id = "../../../evil"
    doc.add_track(t)
    out = tmp_path / "export"
    written = export_to_files(doc, out)
    # The file should be inside out/, not at tmp_path/evil
    written_path = written[0]
    assert out in written_path.parents or written_path == out / "evil.md"
    # Ensure no file was created outside out/
    assert not (tmp_path / "evil.md").exists()
    assert not (tmp_path / ".." / ".." / "evil.md").exists()


# ============================================================
# SECURITY: HTML comment injection in to_markdown
# ============================================================

def test_to_markdown_escapes_comment_injection():
    """A track_id containing '-->' should not break out of the HTML comment."""
    doc = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    t = Tr("safe", "primary", "en", "tracks/safe.md", "content")
    t.track_id = "evil-->injected"
    doc.add_track(t)
    md = to_markdown(doc)
    # The injected part should not appear as unescaped content
    assert "evil-->injected" not in md
    assert "evilinjected" in md  # --> stripped


# ============================================================
# SECURITY: YAML-safe metadata header
# ============================================================

def test_metadata_header_handles_special_chars():
    """Title with YAML special characters should be safely quoted."""
    doc = Doc(title="Title: with colon", authors=["A: B"], created=datetime(2025, 1, 1), version="1.0")
    doc.set_metadata("key", "value: with colon")
    md = to_markdown(doc, metadata_header=True)
    # Should be valid YAML — parse it back
    lines = md.split("---")
    frontmatter_yaml = lines[1].strip()
    parsed = yaml.safe_load(frontmatter_yaml)
    assert parsed["title"] == "Title: with colon"
    assert parsed["authors"] == ["A: B"]
    assert parsed["key"] == "value: with colon"


# ============================================================
# BUG: save_mdkv detects duplicate track paths
# ============================================================

def test_save_mdkv_rejects_duplicate_paths(tmp_path):
    """Two tracks with the same container path should raise ValidationError."""
    doc = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    t1 = Tr("a", "primary", "en", "tracks/dup.md", "content A")
    doc.add_track(t1)
    # Manually set same path on second track (bypassing __post_init__)
    t2 = Tr("b", "commentary", None, "tracks/dup.md", "content B")
    doc.add_track(t2)
    with pytest.raises(ValidationError, match="share path"):
        save_mdkv(doc, tmp_path / "out.mdkv")


# ============================================================
# BUG: _doc_from_manifest wraps Track ValueError in MDKVFormatError
# ============================================================

def test_load_mdkv_invalid_track_type_raises_format_error(tmp_path):
    """A manifest with an invalid track_type should raise MDKVFormatError, not ValueError."""
    manifest = {
        "title": "T",
        "authors": ["A"],
        "created": "2025-01-01T00:00:00",
        "version": "0.1",
        "tracks": [{"track_id": "primary", "track_type": "bogus_type", "language": "en", "path": "tracks/primary.md"}],
    }
    p = tmp_path / "bad.mdkv"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("manifest.yaml", yaml.safe_dump(manifest))
        zf.writestr("tracks/primary.md", "# H")
    with pytest.raises(MDKVFormatError, match="invalid track definition"):
        load_mdkv(p)


# ============================================================
# BUG: CLI error handling for missing/corrupt files
# ============================================================

def test_cli_info_missing_file_exit_code():
    r = CliRunner().invoke(main, ["info", "/nonexistent/path.mdkv"])
    assert r.exit_code != 0
    assert "ERROR" in r.output


def test_cli_info_corrupt_file_exit_code(tmp_path):
    bad = tmp_path / "bad.mdkv"
    bad.write_bytes(b"PK\x03\x04bogus")
    r = CliRunner().invoke(main, ["info", str(bad)])
    assert r.exit_code != 0
    assert "ERROR" in r.output


def test_cli_stats_missing_file_exit_code():
    r = CliRunner().invoke(main, ["stats", "/nonexistent/path.mdkv"])
    assert r.exit_code != 0


def test_cli_validate_missing_file_exit_code():
    r = CliRunner().invoke(main, ["validate", "/nonexistent/path.mdkv"])
    assert r.exit_code != 0


def test_cli_export_missing_file_exit_code():
    r = CliRunner().invoke(main, ["export", "/nonexistent/path.mdkv"])
    assert r.exit_code != 0


def test_cli_search_invalid_regex(tmp_path):
    """Invalid regex pattern should exit with error, not crash."""
    from mdkv.storage import save_mdkv as sm
    doc = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Tr("p", "primary", "en", "tracks/p.md", "content"))
    p = tmp_path / "doc.mdkv"
    sm(doc, p)
    r = CliRunner().invoke(main, ["search", str(p), "--pattern", "[invalid"])
    assert r.exit_code != 0
    assert "invalid regex" in r.output.lower()


# ============================================================
# BUG: GUI /api/track upsert validates track_type on mutation
# ============================================================

def test_gui_upsert_invalid_track_type_on_update(tmp_path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    # Try to update an existing track with an invalid type
    r = c.post("/api/track", json={"id": "primary", "type": "bogus_type"})
    assert r.status_code == 400
    assert "Unsupported track_type" in r.json()["detail"]


# ============================================================
# BUG: GUI /api/search handles invalid regex
# ============================================================

def test_gui_search_invalid_regex(tmp_path):
    from fastapi.testclient import TestClient
    from mdkv.gui.server import create_app, state
    from mdkv.demo import build_multitrack_demo_document

    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/search", params={"pattern": "[invalid"})
    assert r.status_code == 400
    assert "invalid regex" in r.json()["detail"].lower()


# ============================================================
# BUG: diff detects track_type/language/path changes
# ============================================================

def test_diff_detects_track_type_change(tmp_path):
    """diff should report a track as modified if its type changed even if content is the same."""
    from mdkv.storage import save_mdkv as sm
    doc_a = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc_a.add_track(Tr("p", "primary", "en", "tracks/p.md", "same content"))
    pa = tmp_path / "a.mdkv"
    sm(doc_a, pa)

    doc_b = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc_b.add_track(Tr("p", "commentary", "en", "tracks/p.md", "same content"))
    pb = tmp_path / "b.mdkv"
    sm(doc_b, pb)

    r = CliRunner().invoke(main, ["diff", str(pa), str(pb)])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert "p" in data["tracks_modified"]


def test_diff_detects_language_change(tmp_path):
    from mdkv.storage import save_mdkv as sm
    doc_a = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc_a.add_track(Tr("p", "primary", "en", "tracks/p.md", "same"))
    pa = tmp_path / "a.mdkv"
    sm(doc_a, pa)

    doc_b = Doc(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc_b.add_track(Tr("p", "primary", "fr", "tracks/p.md", "same"))
    pb = tmp_path / "b.mdkv"
    sm(doc_b, pb)

    r = CliRunner().invoke(main, ["diff", str(pa), str(pb)])
    data = json.loads(r.output)
    assert "p" in data["tracks_modified"]


# ============================================================
# BUG: MDKVDocument.from_dict handles missing keys
# ============================================================

def test_from_dict_missing_title_raises_key_error():
    with pytest.raises(KeyError):
        Doc.from_dict({"authors": ["A"], "created": "2025-01-01T00:00:00"})


def test_from_dict_missing_created_raises_key_error():
    with pytest.raises(KeyError):
        Doc.from_dict({"title": "T", "authors": ["A"]})
