"""Tests for enhanced storage: error handling for corrupt/missing files."""
from datetime import datetime
from pathlib import Path

import pytest

from mdkv.core.model import MDKVDocument, Track
from mdkv.storage import save_mdkv, load_mdkv, MDKVFormatError


def _make_doc() -> MDKVDocument:
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# H"))
    return d


def test_load_missing_file_raises_filenotfound(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_mdkv(tmp_path / "nonexistent.mdkv")


def test_load_corrupt_zip_raises_format_error(tmp_path: Path):
    bad = tmp_path / "bad.mdkv"
    bad.write_bytes(b"PK\x03\x04bogus")
    with pytest.raises(MDKVFormatError):
        load_mdkv(bad)


def test_load_missing_manifest_raises_format_error(tmp_path: Path):
    import zipfile
    bad = tmp_path / "no_manifest.mdkv"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("tracks/primary.md", "# H")
    with pytest.raises(MDKVFormatError, match="manifest"):
        load_mdkv(bad)


def test_load_missing_track_file_raises_format_error(tmp_path: Path):
    import zipfile
    import yaml
    bad = tmp_path / "missing_track.mdkv"
    manifest = {
        "title": "T",
        "authors": ["A"],
        "created": "2025-01-01T00:00:00",
        "version": "0.1",
        "tracks": [{"track_id": "primary", "track_type": "primary", "language": "en", "path": "tracks/missing.md"}],
    }
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("manifest.yaml", yaml.safe_dump(manifest))
    with pytest.raises(MDKVFormatError, match="not found in container"):
        load_mdkv(bad)


def test_load_manifest_missing_title_key(tmp_path: Path):
    import zipfile
    import yaml
    bad = tmp_path / "no_title.mdkv"
    manifest = {"authors": ["A"], "created": "2025-01-01T00:00:00", "tracks": []}
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("manifest.yaml", yaml.safe_dump(manifest))
    with pytest.raises(MDKVFormatError, match="missing required key: title"):
        load_mdkv(bad)


def test_roundtrip_with_metadata(tmp_path: Path):
    doc = _make_doc()
    doc.set_metadata("project", "mdkv")
    doc.set_metadata("year", "2025")
    p = tmp_path / "doc.mdkv"
    save_mdkv(doc, p)
    loaded = load_mdkv(p)
    assert loaded.get_metadata("project") == "mdkv"
    assert loaded.get_metadata("year") == "2025"
