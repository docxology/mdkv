"""Tests for enhanced export: HTML filtering and export_to_files return value."""
from datetime import datetime
from pathlib import Path

from mdkv.core.model import MDKVDocument, Track
from mdkv.services.export import to_html, to_markdown, export_to_files


def _doc() -> MDKVDocument:
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "# Primary\n\nHello"))
    d.add_track(Track("c", "commentary", None, "tracks/c.md", "# Commentary\n\nNote"))
    d.add_track(Track("t", "translation", "fr", "tracks/t.md", "# Traduction\n\nBonjour"))
    return d


def test_to_html_default_primary_only():
    d = _doc()
    html = to_html(d)
    assert "Primary" in html
    assert "Commentary" not in html


def test_to_html_with_include_types():
    d = _doc()
    html = to_html(d, include_track_types=["primary", "commentary"])
    assert "Primary" in html
    assert "Commentary" in html


def test_to_html_commentary_only():
    d = _doc()
    html = to_html(d, include_track_types=["commentary"])
    assert "Commentary" in html
    assert "Primary" not in html


def test_export_to_files_returns_written_paths(tmp_path: Path):
    d = _doc()
    out = tmp_path / "tracks_out"
    written = export_to_files(d, out, include_track_types=["primary", "commentary"])
    assert len(written) == 2
    assert all(p.exists() for p in written)
    assert (out / "p.md").exists()
    assert (out / "c.md").exists()
    assert not (out / "t.md").exists()


def test_export_to_files_all_when_no_filter(tmp_path: Path):
    d = _doc()
    out = tmp_path / "all"
    written = export_to_files(d, out)
    assert len(written) == 3
