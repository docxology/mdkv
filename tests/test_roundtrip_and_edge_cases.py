from __future__ import annotations

"""Comprehensive roundtrip, schema validation, corruption, and edge case test suites."""

import zipfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mdkv import (
    MDKVDocument,
    MDKVFormatError,
    MDKVManifestModel,
    Track,
    TrackManifestModel,
    ValidationError,
    diff_documents,
    load_mdkv,
    save_mdkv_incremental,
    search_document_async,
    validate_document,
    validate_track,
)
from mdkv.demo import build_multitrack_demo_document
from mdkv.library import build_all_examples


def test_track_manifest_model_validation():
    """Test TrackManifestModel path and field constraints."""
    # Valid track
    tm = TrackManifestModel(track_id="t1", track_type="primary", path="tracks/t1.md", language="en")
    assert tm.track_id == "t1"
    assert tm.path == "tracks/t1.md"
    assert tm.language == "en"

    # MDKVManifestModel metadata coercion non-dict non-None
    m_other = MDKVManifestModel(title="T", created=datetime.now(UTC), metadata="not a dict")  # type: ignore[arg-type]
    assert m_other.metadata == {"not a dict": ""}

    # Invalid path
    with pytest.raises(Exception):
        TrackManifestModel(track_id="t1", track_type="primary", path="invalid_path.md")


def test_mdkv_manifest_model_validation():
    """Test MDKVManifestModel author and metadata coercions."""
    # Coerce single string author to list
    m1 = MDKVManifestModel(
        title="Doc",
        authors="Single Author",  # type: ignore[arg-type]
        created=datetime.now(UTC),
        metadata=None,  # type: ignore[arg-type]
    )
    assert m1.authors == ["Single Author"]
    assert m1.metadata == {}

    # None authors
    m2 = MDKVManifestModel(
        title="Doc",
        authors=None,  # type: ignore[arg-type]
        created=datetime.now(UTC),
        metadata={"k": "v"},
    )
    assert m2.authors == []
    assert m2.metadata == {"k": "v"}


def test_all_library_definitions_roundtrip(tmp_path: Path):
    """Test full load, build, save, load, diff, and validate on all library definitions."""
    repo_root = Path(__file__).resolve().parents[1]
    defs_dir = repo_root / "library" / "definitions"
    out_dir = tmp_path / "built"
    outputs = build_all_examples(defs_dir, out_dir)
    assert len(outputs) >= 7

    for out in outputs:
        doc = load_mdkv(out)
        assert doc.title
        assert len(doc.tracks) > 0
        issues = validate_document(doc)
        assert isinstance(issues, list)

        # Test incremental save on existing doc
        saved_inc = save_mdkv_incremental(doc, out)
        assert saved_inc is True

        # Re-load and verify identical diff
        doc_reloaded = load_mdkv(out)
        diff = diff_documents(doc, doc_reloaded)
        assert not diff.has_changes


def test_corrupted_container_variations(tmp_path: Path):
    """Test various corrupted ZIP structures and missing manifest entries."""
    # 1. Container missing manifest.yaml
    no_manifest = tmp_path / "no_manifest.mdkv"
    with zipfile.ZipFile(no_manifest, "w") as zf:
        zf.writestr("tracks/primary.md", "content")
    with pytest.raises(MDKVFormatError, match="manifest 'manifest.yaml' not found"):
        load_mdkv(no_manifest)

    # 2. Manifest is not a YAML mapping (e.g. list or scalar)
    scalar_manifest = tmp_path / "scalar_manifest.mdkv"
    with zipfile.ZipFile(scalar_manifest, "w") as zf:
        zf.writestr("manifest.yaml", "just a string, not a dict")
    with pytest.raises(MDKVFormatError, match="manifest is not a valid YAML mapping"):
        load_mdkv(scalar_manifest)

    # 3. Manifest missing created
    no_created = tmp_path / "no_created.mdkv"
    with zipfile.ZipFile(no_created, "w") as zf:
        zf.writestr("manifest.yaml", yaml.safe_dump({"title": "Test"}))
    with pytest.raises(MDKVFormatError, match="manifest missing required key: created"):
        load_mdkv(no_created)

    # 4. Manifest missing title
    no_title = tmp_path / "no_title.mdkv"
    with zipfile.ZipFile(no_title, "w") as zf:
        zf.writestr("manifest.yaml", yaml.safe_dump({"created": datetime.now(UTC).isoformat()}))
    with pytest.raises(MDKVFormatError, match="manifest missing required key: title"):
        load_mdkv(no_title)

    # 5. Track in manifest points outside tracks/ directory
    bad_track_path = tmp_path / "bad_track_path.mdkv"
    with zipfile.ZipFile(bad_track_path, "w") as zf:
        zf.writestr(
            "manifest.yaml",
            yaml.safe_dump({
                "title": "T",
                "created": datetime.now(UTC).isoformat(),
                "tracks": [{"track_id": "t1", "track_type": "primary", "path": "outside.md"}],
            }),
        )
        zf.writestr("outside.md", "content")
    with pytest.raises(MDKVFormatError, match="manifest schema validation failed"):
        load_mdkv(bad_track_path)


def test_incremental_save_corrupt_fallback(tmp_path: Path):
    """Test incremental save fallbacks when existing archive is corrupted or missing manifest."""
    doc = build_multitrack_demo_document()
    p = tmp_path / "corrupt_inc.mdkv"

    # Existing archive has no manifest
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("tracks/foo.md", "foo")
    res1 = save_mdkv_incremental(doc, p)
    assert res1 is False
    assert load_mdkv(p).title == doc.title

    # Existing archive has non-dict manifest
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("manifest.yaml", "scalar string")
    res2 = save_mdkv_incremental(doc, p)
    assert res2 is False
    assert load_mdkv(p).title == doc.title

    # Existing archive is unparseable zip
    p_bad = tmp_path / "bad_zip.mdkv"
    p_bad.write_bytes(b"not a real zip")
    res_bad = save_mdkv_incremental(doc, p_bad)
    assert res_bad is False
    assert load_mdkv(p_bad).title == doc.title

    # Existing archive has track missing from zip
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr(
            "manifest.yaml",
            yaml.safe_dump({
                "title": "T",
                "created": datetime.now(UTC).isoformat(),
                "tracks": [{"track_id": "missing_file", "track_type": "primary", "path": "tracks/missing.md"}],
            }),
        )
    # Incremental save will skip the missing track and save cleanly
    res3 = save_mdkv_incremental(doc, p)
    assert res3 is True
    assert load_mdkv(p).title == doc.title


def test_validate_track_errors_direct():
    """Directly test ValidationError in validate_track and validate_document."""
    doc = MDKVDocument(title="Doc", authors=["A"], created=datetime.now(UTC))
    t1 = Track("primary", "primary", "en", "tracks/primary.md", "content 1")
    t2 = Track("t2", "commentary", None, "tracks/primary.md", "content 2")
    doc.add_track(t1)
    doc.tracks["t2"] = t2  # bypass add_track duplicate path check to test validate_document

    with pytest.raises(ValidationError, match="shares path"):
        validate_document(doc)

    # Empty content error condition if forced
    t_bad = Track("t_bad", "primary", "en", "tracks/t_bad.md", "content")
    with patch.object(t_bad, "track_id", ""):
        # validate_track checking invalid track_id
        pass
    # Non-Track instance passed to validate_track
    with pytest.raises(ValidationError, match="must be an instance of Track"):
        validate_track("not a track")  # type: ignore[arg-type]


def test_validation_edge_cases():
    doc = MDKVDocument(title="Valid", authors=["A"], created=datetime.now(UTC))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Primary"))

    # Add track with reserved id
    doc.add_track(Track("null", "commentary", None, "tracks/null.md", "notes"))
    issues = validate_document(doc)
    assert any(i.level == "WARN" and "reserved word" in i.message for i in issues)

    # Test single validate_track with reserved id
    t_null = doc.get_track("null")
    assert t_null is not None
    t_issues = validate_track(t_null)
    assert any(i.level == "WARN" and "reserved word" in i.message for i in t_issues)


def test_search_async_type_and_lang_filter():
    import asyncio
    doc = MDKVDocument(title="Doc", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "hello world"))
    doc.add_track(Track("notes", "commentary", "es", "tracks/notes.md", "hello notes"))

    async def _run_filter():
        m_type = []
        async for m in search_document_async(doc, "hello", track_types=["commentary"]):
            m_type.append(m)
        m_lang = []
        async for m in search_document_async(doc, "hello", languages=["es"]):
            m_lang.append(m)
        return m_type, m_lang

    t_res, l_res = asyncio.run(_run_filter())
    assert len(t_res) == 1
    assert t_res[0].track_id == "notes"
    assert len(l_res) == 1
    assert l_res[0].track_id == "notes"


def test_search_async_yield_control():
    """Test search_document_async sleep yield when more than 100 matches."""
    import asyncio
    doc = MDKVDocument(title="Big Search", authors=["A"], created=datetime.now(UTC))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "match " * 150))

    async def _run():
        matches = []
        async for m in search_document_async(doc, pattern=r"match"):
            matches.append(m)
        return matches

    res = asyncio.run(_run())
    assert len(res) == 150
