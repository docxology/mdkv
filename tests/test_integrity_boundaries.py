"""Consumer-visible storage, mutable-model, registry, and history boundaries."""

import stat
import struct
import zipfile
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from mdkv.core.errors import ValidationError
from mdkv.core.history import TrackHistory, TrackVersion
from mdkv.core.model import MDKVDocument, Track, allowed_track_types
from mdkv.core.registry import TrackTypeRegistry, get_registry
from mdkv.core.validate import validate_document, validate_track
from mdkv.storage.io import MDKVFormatError, load_mdkv, save_mdkv, save_mdkv_incremental
from mdkv.storage.schema import MDKVManifestModel, TrackManifestModel


def _document() -> MDKVDocument:
    doc = MDKVDocument("Integrity", ["Author"], datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "Original"))
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "Notes"))
    return doc


def _manifest() -> dict:
    return {
        "title": "Integrity",
        "authors": ["Author"],
        "created": "2025-01-01T00:00:00",
        "tracks": [{"track_id": "primary", "track_type": "primary", "path": "tracks/primary.md"}],
    }


def _container(path: Path, manifest=None, members=None, compression=zipfile.ZIP_STORED) -> Path:
    if manifest is None:
        manifest = _manifest()
    if isinstance(manifest, dict):
        manifest = yaml.safe_dump(manifest, sort_keys=False)
    if members is None:
        members = [("tracks/primary.md", b"Original")]
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        archive.writestr("manifest.yaml", manifest)
        for name, content in members:
            archive.writestr(name, content)
    return path


def _patch_member(path: Path, name: str, *, size=None, flags=None, method=None) -> None:
    """Forge tiny ZIP headers, not large payloads or mocked readers."""
    data = bytearray(path.read_bytes())
    offset = data.find(b"PK\x01\x02")
    while offset != -1:
        name_size, extra_size, comment_size = struct.unpack_from("<HHH", data, offset + 28)
        member_name = bytes(data[offset + 46:offset + 46 + name_size]).decode("utf-8")
        if member_name == name:
            local = struct.unpack_from("<I", data, offset + 42)[0]
            if size is not None:
                struct.pack_into("<I", data, offset + 24, size)
                struct.pack_into("<I", data, local + 22, size)
            if flags is not None:
                struct.pack_into("<H", data, offset + 8, flags)
                struct.pack_into("<H", data, local + 6, flags)
            if method is not None:
                struct.pack_into("<H", data, offset + 10, method)
                struct.pack_into("<H", data, local + 8, method)
            path.write_bytes(data)
            return
        offset = data.find(b"PK\x01\x02", offset + 46 + name_size + extra_size + comment_size)
    raise AssertionError(f"fixture member missing: {name}")


def _corrupt_payload(path: Path, name: str) -> None:
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo(name)
        local = info.header_offset
        compressed_size = info.compress_size
    data = bytearray(path.read_bytes())
    name_size, extra_size = struct.unpack_from("<HH", data, local + 26)
    start = local + 30 + name_size + extra_size
    data[start:start + compressed_size] = b"\xff" * compressed_size
    path.write_bytes(data)


@pytest.mark.parametrize("manifest", [
    "title: [unterminated",
    "title: Bad\ncreated: 2025-01-01\ntitle: Duplicate\n",
    "title: Bad\ncreated: 2025-01-01\nmetadata: {key: first, key: second}\n",
    "title: &title Anchored\ncreated: 2025-01-01\n",
    "title: *unknown\ncreated: 2025-01-01\n",
    "title: Bad\ncreated: 2025-99-99\n",
    "title: !unknown Bad\ncreated: 2025-01-01\n",
    b"title: \xff\ncreated: 2025-01-01\n",
    "[]",
])
def test_malformed_yaml_is_a_format_error(tmp_path, manifest):
    path = _container(tmp_path / "bad.mdkv", manifest)
    with pytest.raises(MDKVFormatError):
        load_mdkv(path)


@pytest.mark.parametrize("extra, message", [
    ("[" * 33 + "0" + "]" * 33, "depth"),
    ("[" + ",".join("0" for _ in range(10001)) + "]", "node count"),
])
def test_yaml_complexity_is_bounded(tmp_path, extra, message):
    manifest = "title: Bounded\ncreated: 2025-01-01\nextra: " + extra + "\n"
    path = _container(tmp_path / "complex.mdkv", manifest)
    with pytest.raises(MDKVFormatError, match=message):
        load_mdkv(path)


def test_yaml_within_depth_limit_and_legacy_defaults_loads(tmp_path):
    manifest = "title: Bounded\ncreated: 2025-01-01\nextra: " + "[" * 30 + "0" + "]" * 30 + "\n"
    loaded = load_mdkv(_container(tmp_path / "within.mdkv", manifest))
    assert loaded.authors == []
    assert loaded.metadata == {}


@pytest.mark.parametrize("field", ["track_id", "path"])
def test_duplicate_manifest_track_ids_and_paths_are_rejected(tmp_path, field):
    manifest = _manifest()
    second = {"track_id": "notes", "track_type": "commentary", "path": "tracks/notes.md"}
    second[field] = manifest["tracks"][0][field]
    manifest["tracks"].append(second)
    path = _container(tmp_path / "duplicates.mdkv", manifest, [
        ("tracks/primary.md", "Original"), ("tracks/notes.md", "Notes"),
    ])
    with pytest.raises(MDKVFormatError, match="duplicate track_id|share path"):
        load_mdkv(path)


@pytest.mark.parametrize("name", ["manifest.yaml", "tracks/primary.md", "extra.bin"])
def test_duplicate_zip_members_are_rejected(tmp_path, name):
    with pytest.warns(UserWarning, match="Duplicate name"):
        path = _container(tmp_path / "duplicate-member.mdkv", members=[
            ("tracks/primary.md", "Original"), (name, "first"), (name, "second"),
        ])
    with pytest.raises(MDKVFormatError, match="duplicate archive member"):
        load_mdkv(path)


@pytest.mark.parametrize("name, size, message", [
    ("manifest.yaml", 1024 * 1024 + 1, "member 'manifest.yaml'.*size limit"),
    ("tracks/primary.md", 16 * 1024 * 1024 + 1, "member 'tracks/primary.md'.*size limit"),
    ("extra.bin", 64 * 1024 * 1024 + 1, "total declared uncompressed"),
])
def test_declared_member_and_total_bounds_use_tiny_fixtures(tmp_path, name, size, message):
    path = _container(tmp_path / "oversize.mdkv", members=[
        ("tracks/primary.md", "Original"), ("extra.bin", b"x"),
    ])
    _patch_member(path, name, size=size)
    assert path.stat().st_size < 1024
    with pytest.raises(MDKVFormatError, match=message):
        load_mdkv(path)


def test_compressed_archive_cap_rejects_sparse_file_before_zip_parsing(tmp_path):
    path = tmp_path / "oversize-sparse.mdkv"
    with path.open("wb") as stream:
        stream.truncate(128 * 1024 * 1024 + 1)
    with pytest.raises(MDKVFormatError, match="compressed archive size exceeds limit"):
        load_mdkv(path)


def test_member_count_bound_uses_empty_members(tmp_path):
    members = [(f"extras/{i}", b"") for i in range(4096)]
    path = _container(tmp_path / "many-members.mdkv", members=members)
    with pytest.raises(MDKVFormatError, match="member count"):
        load_mdkv(path)


def test_track_count_bound_precedes_entry_schema_validation(tmp_path):
    manifest = _manifest()
    manifest["tracks"] = [0] * 1025
    path = _container(tmp_path / "many-tracks.mdkv", manifest)
    with pytest.raises(MDKVFormatError, match="track count"):
        load_mdkv(path)


@pytest.mark.parametrize("change", [{"flags": 1}, {"method": 99}])
def test_encrypted_and_unsupported_members_are_format_errors(tmp_path, change):
    path = _container(tmp_path / "unsupported.mdkv")
    _patch_member(path, "tracks/primary.md", **change)
    with pytest.raises(MDKVFormatError, match="encrypted|unsupported"):
        load_mdkv(path)


@pytest.mark.parametrize("name", ["tracks/primary.md", "extra.bin"])
@pytest.mark.parametrize("compression", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
def test_crc_and_decompression_failures_are_format_errors(tmp_path, name, compression):
    path = _container(tmp_path / "corrupt-payload.mdkv", members=[
        ("tracks/primary.md", "Original content"), ("extra.bin", b"Extra content"),
    ], compression=compression)
    _corrupt_payload(path, name)
    with pytest.raises(MDKVFormatError):
        load_mdkv(path)


def test_invalid_track_utf8_is_a_format_error(tmp_path):
    path = _container(tmp_path / "bad-utf8.mdkv", members=[("tracks/primary.md", b"\xff")])
    with pytest.raises(MDKVFormatError):
        load_mdkv(path)


def test_invalid_zip_is_a_format_error_and_missing_file_remains_distinct(tmp_path):
    path = tmp_path / "not-zip.mdkv"
    path.write_bytes(b"PK\x03\x04broken")
    with pytest.raises(MDKVFormatError):
        load_mdkv(path)
    with pytest.raises(FileNotFoundError):
        load_mdkv(tmp_path / "missing.mdkv")


@pytest.mark.parametrize("path", [
    "tracks/../escape.md", "tracks/./file.md", "tracks//file.md", "tracks/",
    "tracks/nested/", "tracks\\file.md", "tracks/file\x00.md", "/tracks/file.md", "other/file.md",
])
def test_model_schema_reader_and_mutable_save_share_safe_paths(tmp_path, path):
    with pytest.raises(ValueError):
        Track("primary", "primary", None, path, "Content")
    with pytest.raises(ValueError):
        TrackManifestModel(track_id="primary", track_type="primary", path=path)
    manifest = _manifest()
    manifest["tracks"][0]["path"] = path
    with pytest.raises(MDKVFormatError):
        load_mdkv(_container(tmp_path / "unsafe.mdkv", manifest))
    doc = _document()
    doc.tracks["primary"].path = path
    with pytest.raises((ValidationError, ValueError)):
        save_mdkv(doc, tmp_path / "save.mdkv")


@pytest.mark.parametrize("track_id", ["", "   ", "a\x00b", 42])
def test_invalid_ids_are_rejected_at_construction_and_after_mutation(tmp_path, track_id):
    with pytest.raises(ValueError):
        Track(track_id, "primary", None, "tracks/primary.md", "Content")
    doc = _document()
    doc.tracks["primary"].track_id = track_id
    with pytest.raises((ValidationError, ValueError)):
        save_mdkv(doc, tmp_path / "bad-id.mdkv")


@pytest.mark.parametrize("save", [save_mdkv, save_mdkv_incremental])
@pytest.mark.parametrize("mutation", ["duplicate_path", "duplicate_id", "mapping_key", "type", "content"])
def test_mutated_invalid_documents_preserve_destination(tmp_path, save, mutation):
    path = tmp_path / "document.mdkv"
    doc = _document()
    save_mdkv(doc, path)
    before = path.read_bytes()
    if mutation == "duplicate_path":
        doc.tracks["notes"].path = doc.tracks["primary"].path
    elif mutation == "duplicate_id":
        doc.tracks["notes"].track_id = "primary"
    elif mutation == "mapping_key":
        doc.tracks["notes"].track_id = "different"
    elif mutation == "type":
        doc.tracks["notes"].track_type = "unregistered-integrity-type"
    else:
        doc.tracks["notes"].content = b"not Markdown text"
    with pytest.raises((ValidationError, ValueError)):
        save(doc, path)
    assert path.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [path.name]


@pytest.mark.parametrize("save", [save_mdkv, save_mdkv_incremental])
def test_unserializable_metadata_preserves_bytes_mode_and_cleans_temporary(tmp_path, save):
    path = tmp_path / "document.mdkv"
    doc = _document()
    save_mdkv(doc, path)
    path.chmod(0o640)
    before = path.read_bytes()
    doc.metadata["unserializable"] = object()
    with pytest.raises((ValidationError, ValueError)):
        save(doc, path)
    assert path.read_bytes() == before
    assert stat.S_IMODE(path.stat().st_mode) == 0o640
    assert sorted(p.name for p in tmp_path.iterdir()) == [path.name]


@pytest.mark.parametrize("options", [{"compression": 999}, {"compresslevel": -2}])
def test_real_compression_failure_preserves_destination_and_cleans_temporary(tmp_path, options):
    path = tmp_path / "document.mdkv"
    doc = _document()
    save_mdkv(doc, path)
    path.chmod(0o604)
    before = path.read_bytes()
    with pytest.raises(ValueError):
        save_mdkv(doc, path, **options)
    assert path.read_bytes() == before
    assert stat.S_IMODE(path.stat().st_mode) == 0o604
    assert sorted(p.name for p in tmp_path.iterdir()) == [path.name]


@pytest.mark.parametrize("save", [save_mdkv, save_mdkv_incremental])
def test_unique_temporary_does_not_clobber_preexisting_sentinel(tmp_path, save):
    path = tmp_path / "document.mdkv"
    doc = _document()
    save_mdkv(doc, path)
    path.chmod(0o640)
    sentinels = [tmp_path / "document.mdkv.tmp", tmp_path / ".document.mdkv.sentinel.tmp"]
    for sentinel in sentinels:
        sentinel.write_bytes(b"Do not touch")
    doc.update_track_content("primary", "Updated")
    save(doc, path)
    assert load_mdkv(path).tracks["primary"].content == "Updated"
    assert stat.S_IMODE(path.stat().st_mode) == 0o640
    for sentinel in sentinels:
        assert sentinel.read_bytes() == b"Do not touch"
    assert set(tmp_path.iterdir()) == {path, *sentinels}


def test_incremental_roundtrip_rewrites_changes_additions_removals_and_metadata(tmp_path):
    path = tmp_path / "document.mdkv"
    doc = _document()
    doc.metadata["remove"] = "old"
    assert save_mdkv_incremental(doc, path) is False
    doc.update_track_content("primary", "Changed")
    doc.remove_track("notes")
    doc.add_track(Track("reference", "reference", None, "tracks/reference.md", "New"))
    doc.title = "Changed title"
    doc.authors.append("Second author")
    doc.metadata = {"new": "metadata"}
    assert save_mdkv_incremental(doc, path) is True
    assert load_mdkv(path).to_dict() == doc.to_dict()
    with zipfile.ZipFile(path) as archive:
        assert set(archive.namelist()) == {"manifest.yaml", "tracks/primary.md", "tracks/reference.md"}


@pytest.mark.parametrize("original", [b"not ZIP", b"title: [malformed"])
def test_incremental_false_for_invalid_existing_container(tmp_path, original):
    path = tmp_path / "invalid.mdkv"
    if original.startswith(b"title"):
        _container(path, original)
    else:
        path.write_bytes(original)
    doc = _document()
    assert save_mdkv_incremental(doc, path) is False
    assert load_mdkv(path).to_dict() == doc.to_dict()


def test_incremental_false_for_structurally_invalid_existing_manifest(tmp_path):
    path = _container(tmp_path / "invalid-schema.mdkv", {"title": "Missing created"})
    assert save_mdkv_incremental(_document(), path) is False
    assert load_mdkv(path).title == "Integrity"


def test_self_move_and_rename_preserve_track_and_insertion_order():
    doc = _document()
    primary = doc.tracks["primary"]
    original = doc.to_dict()
    doc.move_track("primary", "primary")
    assert doc.to_dict() == original
    assert doc.tracks["primary"] is primary
    doc.rename_track("primary", "renamed")
    assert doc.track_ids == ["renamed", "notes"]
    assert doc.tracks["renamed"] is primary
    assert primary.path == "tracks/renamed.md"
    doc.rename_track("renamed", "renamed")
    assert doc.track_ids == ["renamed", "notes"]


@pytest.mark.parametrize("new_id", ["", "../escape", "bad\\id", "bad\x00id", "notes"])
def test_invalid_rename_preserves_order_content_and_identity(new_id):
    doc = _document()
    primary = doc.tracks["primary"]
    before = doc.to_dict()
    with pytest.raises(ValueError):
        doc.rename_track("primary", new_id)
    assert doc.to_dict() == before
    assert doc.tracks["primary"] is primary


def test_rename_path_collision_is_atomic():
    doc = _document()
    doc.tracks["notes"].path = "tracks/new.md"
    before = doc.to_dict()
    with pytest.raises(ValueError, match="path exists"):
        doc.rename_track("primary", "new")
    assert doc.to_dict() == before


def test_safe_nested_path_and_legitimate_metadata_normalization_roundtrip(tmp_path):
    doc = _document()
    doc.tracks["notes"].path = "tracks/nested/notes.md"
    doc.metadata = {"count": 2, "enabled": True}
    path = tmp_path / "normalized.mdkv"
    save_mdkv(doc, path)
    loaded = load_mdkv(path)
    assert loaded.tracks["notes"].path == "tracks/nested/notes.md"
    assert loaded.metadata == {"count": "2", "enabled": "True"}
    legacy = MDKVManifestModel(created=datetime(2025, 1, 1), authors="Author", metadata="legacy")
    assert legacy.authors == ["Author"]
    assert legacy.metadata == {"legacy": ""}
    with pytest.raises(ValueError):
        MDKVManifestModel(created=datetime(2025, 1, 1), metadata={1: "number", "1": "string"})
    with pytest.raises(ValueError):
        MDKVManifestModel(created=datetime(2025, 1, 1), metadata={"nested": ["not scalar"]})


@pytest.mark.parametrize("name", ["", "  ", None, 42, []])
def test_registry_rejects_empty_or_nonstring_names_without_registration(name):
    registry = TrackTypeRegistry()
    before = registry.all_types()
    with pytest.raises(ValueError):
        registry.register(name)
    assert registry.all_types() == before


def test_registered_custom_type_roundtrips_and_uses_both_validation_callbacks(tmp_path):
    registry = get_registry()
    name = "integrity-custom-type"
    registry.register(
        name,
        validator=lambda content: ["custom validator warning"] if "Custom" in content else [],
        heuristics=lambda content: ["custom heuristics warning"] if "Custom" in content else [],
    )
    try:
        assert name in allowed_track_types()
        doc = _document()
        doc.add_track(Track("custom", name, None, "tracks/custom.md", "Custom content"))
        path = tmp_path / "custom.mdkv"
        save_mdkv(doc, path)
        loaded = load_mdkv(path)
        assert loaded.tracks["custom"].track_type == name
        individual = validate_track(loaded.tracks["custom"])
        document_issues = validate_document(loaded)
        assert [issue.message for issue in individual] == [
            "custom validator warning", "custom heuristics warning",
        ]
        assert [issue.message for issue in document_issues if issue.track_id == "custom"] == [
            issue.message for issue in individual
        ]
        assert all(issue.level == "WARN" for issue in individual)
    finally:
        registry.unregister(name)


def _version(day: int, *, aware: bool = False) -> TrackVersion:
    return TrackVersion(datetime(2025, 1, day, tzinfo=UTC if aware else None), f"v{day}", "primary", "en", "primary")


def test_history_constructor_ingestion_queries_and_restore_are_chronological():
    supplied = [_version(3), _version(1)]
    history = TrackHistory("primary", supplied)
    assert [version.content for version in history.versions] == ["v1", "v3"]
    assert [version.content for version in supplied] == ["v3", "v1"]
    history.add_version("v2", "primary", "en", datetime(2025, 1, 2))
    assert history.get_current().content == "v3"
    assert history.get_version_at(datetime(2025, 1, 2, 12)).content == "v2"
    history.versions.reverse()
    assert [version.content for version in history.list_versions()] == ["v1", "v2", "v3"]
    assert history.get_current().content == "v3"
    assert [item["content"] for item in history.to_dict()["versions"]] == ["v1", "v2", "v3"]
    assert history.restore_to(datetime(2025, 1, 2)).content == "v2"
    assert [version.content for version in history.versions] == ["v1", "v2"]


def test_history_timezone_rejection_never_partially_mutates():
    supplied = [_version(1), _version(2, aware=True)]
    with pytest.raises(ValueError, match="comparable timezones"):
        TrackHistory("primary", supplied)
    assert supplied == [_version(1), _version(2, aware=True)]
    history = TrackHistory("primary", [_version(1)])
    before = history.to_dict()
    with pytest.raises(ValueError, match="comparable timezones"):
        history.add_version("aware", "primary", "en", datetime(2025, 1, 2, tzinfo=UTC))
    with pytest.raises(ValueError, match="comparable timezones"):
        history.get_version_at(datetime(2025, 1, 2, tzinfo=UTC))
    with pytest.raises(ValueError, match="comparable timezones"):
        history.restore_to(datetime(2025, 1, 2, tzinfo=UTC))
    assert history.to_dict() == before


def test_history_aware_offsets_and_equal_timestamp_ingestion_order():
    history = TrackHistory("primary")
    later = datetime(2025, 1, 1, 12, tzinfo=UTC)
    earlier = datetime(2025, 1, 1, 12, tzinfo=timezone(timedelta(hours=2)))
    history.add_version("later", "primary", None, later)
    history.add_version("earlier", "primary", None, earlier)
    history.add_version("latest-equal", "primary", None, later)
    assert [version.content for version in history.list_versions()] == ["earlier", "later", "latest-equal"]
    assert history.get_current().content == "latest-equal"
    assert history.get_version_at(later).content == "latest-equal"


def test_history_default_timestamp_matches_existing_naive_convention():
    history = TrackHistory("primary", [_version(1)])
    history.add_version("now", "primary", None)
    assert history.get_current().content == "now"
    assert history.get_current().timestamp.utcoffset() is None


def test_history_restore_keeps_equal_timestamp_snapshots():
    first = _version(1)
    second = _version(2)
    history = TrackHistory("primary", [second, first, first, _version(3)])
    assert history.restore_to(first.timestamp) is first
    assert history.versions == [first, first]
