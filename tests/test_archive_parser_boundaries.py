"""Real ZIP and YAML fixtures for the bounded archive reader profile."""

import io
import struct
import zipfile
import zlib
from datetime import datetime

import pytest

from mdkv.core.errors import ValidationError
from mdkv.core.model import MDKVDocument, Track
from mdkv.storage.io import (
    MAX_MEMBERS,
    MDKVFormatError,
    _preflight_directory,
    load_mdkv,
    save_mdkv,
    save_mdkv_incremental,
)


MANIFEST = (
    "title: Boundaries\n"
    "created: 2025-01-01T00:00:00\n"
    "tracks:\n"
    "- track_id: primary\n"
    "  track_type: primary\n"
    "  path: tracks/primary.md\n"
)


def _document():
    doc = MDKVDocument("Replacement", ["Author"], datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "Preserved output"))
    return doc


def _archive(path, *, manifest=MANIFEST, compression=zipfile.ZIP_STORED,
             comment=b"", extra=None, track_content=b"Original"):
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        archive.comment = comment
        archive.writestr("manifest.yaml", manifest)
        archive.writestr("tracks/primary.md", track_content)
        if extra is not None:
            archive.writestr("extra.bin", extra)
    return path


def _directory_fixture(actual, declared=None):
    """Handbuild central records without first allocating any ZipInfo objects."""
    local = struct.pack("<4s5H3I2H", b"PK\x03\x04", 20, 0, 0, 0, 0, 0, 0, 0, 1, 0) + b"x"
    records = []
    for index in range(actual):
        name = f"{index}.bin".encode()
        records.append(struct.pack(
            "<4s6H3I5H2I", b"PK\x01\x02", 20, 20, 0, 0, 0, 0,
            0, 0, 0, len(name), 0, 0, 0, 0, 0, 0,
        ) + name)
    directory = b"".join(records)
    count = actual if declared is None else declared
    end = struct.pack("<4s4H2IH", b"PK\x05\x06", 0, 0, count, count,
                      len(directory), len(local), 0)
    return local + directory + end


def _preflight(data):
    _preflight_directory(io.BytesIO(data), len(data))


@pytest.mark.parametrize("declared", [0, 1, MAX_MEMBERS, MAX_MEMBERS + 1])
def test_actual_directory_count_is_bounded_even_with_forged_eocd(tmp_path, declared):
    data = _directory_fixture(MAX_MEMBERS + 1, declared)
    with pytest.raises(MDKVFormatError, match="member count exceeds"):
        _preflight(data)
    path = tmp_path / "too-many.mdkv"
    path.write_bytes(data)
    with pytest.raises(MDKVFormatError, match="member count exceeds"):
        load_mdkv(path)


@pytest.mark.parametrize("declared", [0, 2, 60000])
def test_small_actual_directory_rejects_forged_declared_count(declared):
    with pytest.raises(MDKVFormatError, match="count mismatch"):
        _preflight(_directory_fixture(1, declared))


def test_exact_actual_member_limit_is_accepted_by_preflight():
    _preflight(_directory_fixture(MAX_MEMBERS))


@pytest.mark.parametrize("damage", ["length", "truncated", "signature", "disk", "zip64", "bounds"])
def test_malformed_central_records_are_rejected(damage):
    data = bytearray(_directory_fixture(1))
    central = data.index(b"PK\x01\x02")
    end = data.index(b"PK\x05\x06")
    if damage == "length":
        struct.pack_into("<H", data, central + 28, 65535)
    elif damage == "truncated":
        directory = data[central:central + 20]
        trailer = bytearray(data[end:])
        struct.pack_into("<I", trailer, 12, len(directory))
        data = data[:central] + directory + trailer
    elif damage == "signature":
        data[central:central + 4] = b"BAD!"
    elif damage == "disk":
        struct.pack_into("<H", data, central + 34, 1)
    elif damage == "zip64":
        struct.pack_into("<I", data, central + 24, 0xFFFFFFFF)
    else:
        struct.pack_into("<I", data, end + 16, central + 1)
    with pytest.raises(MDKVFormatError):
        _preflight(data)


@pytest.mark.parametrize("damage", ["disk", "zip64", "comment", "trailing", "truncated"])
def test_malformed_end_records_are_rejected(damage):
    data = bytearray(_directory_fixture(1))
    end = data.index(b"PK\x05\x06")
    if damage == "disk":
        struct.pack_into("<H", data, end + 4, 1)
    elif damage == "zip64":
        struct.pack_into("<I", data, end + 12, 0xFFFFFFFF)
    elif damage == "comment":
        struct.pack_into("<H", data, end + 20, 5)
    elif damage == "trailing":
        data += b"trailing"
    else:
        del data[-3:]
    with pytest.raises(MDKVFormatError):
        _preflight(data)


def test_zip64_locator_before_eocd_cannot_select_another_directory(tmp_path):
    # A central-record comment can carry the 20-byte locator zipfile reads
    # immediately before the ordinary EOCD. Reject it before stdlib parses.
    data = bytearray(_directory_fixture(1))
    end = data.index(b"PK\x05\x06")
    central = data.index(b"PK\x01\x02")
    struct.pack_into("<H", data, central + 32, 20)
    data = data[:end] + b"PK\x06\x07" + struct.pack("<IQI", 0, 0, 1) + data[end:]
    shifted = data.index(b"PK\x05\x06")
    directory_size = struct.unpack_from("<I", data, shifted + 12)[0] + 20
    struct.pack_into("<I", data, shifted + 12, directory_size)
    with pytest.raises(MDKVFormatError, match="ZIP64"):
        _preflight(data)
    path = tmp_path / "locator.mdkv"
    path.write_bytes(data)
    with pytest.raises(MDKVFormatError, match="ZIP64"):
        load_mdkv(path)


@pytest.mark.parametrize("compression", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
@pytest.mark.parametrize("comment", [b"", b"ordinary ZIP comment", b"c" * 65535])
def test_standard_archives_comments_and_supported_compression_roundtrip(tmp_path, compression, comment):
    path = _archive(tmp_path / "ordinary.mdkv", compression=compression,
                    comment=comment, extra=b"\xff\x00binary extra")
    _preflight(path.read_bytes())
    doc = load_mdkv(path)
    assert doc.tracks["primary"].content == "Original"
    save_mdkv(doc, path, compression=compression)
    assert load_mdkv(path).tracks["primary"].content == "Original"


def _forge_small_size(path, name):
    """Keep a tiny genuine compressed stream but forge its size and prefix CRC."""
    data = bytearray(path.read_bytes())
    central = data.index(b"PK\x01\x02")
    while data[central:central + 4] == b"PK\x01\x02":
        name_size, extra_size, comment_size = struct.unpack_from("<HHH", data, central + 28)
        member_name = data[central + 46:central + 46 + name_size].decode()
        if member_name == name:
            local = struct.unpack_from("<I", data, central + 42)[0]
            struct.pack_into("<I", data, central + 16, zlib.crc32(b"A"))
            struct.pack_into("<I", data, central + 24, 1)
            struct.pack_into("<I", data, local + 14, zlib.crc32(b"A"))
            struct.pack_into("<I", data, local + 22, 1)
            path.write_bytes(data)
            return
        central += 46 + name_size + extra_size + comment_size
    raise AssertionError(f"missing fixture member: {name}")


@pytest.mark.parametrize("compression", [zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA])
@pytest.mark.parametrize("name", ["tracks/primary.md", "extra.bin"])
def test_unsafe_decoder_methods_rejected_in_preflight_with_forged_small_size(tmp_path, compression, name):
    path = _archive(tmp_path / "unsupported.mdkv", compression=compression,
                    extra=b"A" * 8192, track_content=b"A" * 8192)
    _forge_small_size(path, name)
    # This fixed-record pass runs without opening or decoding a ZIP member.
    with pytest.raises(MDKVFormatError, match="unsupported ZIP compression"):
        _preflight(path.read_bytes())
    with pytest.raises(MDKVFormatError, match="unsupported ZIP compression"):
        load_mdkv(path)
    before = path.read_bytes()
    with pytest.raises(ValueError, match="unsupported ZIP compression"):
        save_mdkv(_document(), path, compression=compression)
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("compression", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
@pytest.mark.parametrize("name", ["tracks/primary.md", "extra.bin"])
def test_actual_size_cannot_hide_behind_declared_size_and_prefix_crc(tmp_path, compression, name):
    path = _archive(tmp_path / "small-size.mdkv", compression=compression,
                    extra=b"A" * 200000, track_content=b"A" * 200000)
    _forge_small_size(path, name)
    with pytest.raises(MDKVFormatError, match="uncompressed size"):
        load_mdkv(path)


@pytest.mark.parametrize("tagged", [
    "created: !!timestamp nonsense\n",
    "metadata: {bad: !!int ''}\n",
    "metadata: {bad: !!bool nonsense}\n",
    "metadata: {bad: !!float ''}\n",
])
def test_bad_explicit_yaml_tags_normalize_and_incremental_fallback_preserves_document(tmp_path, tagged):
    manifest = "title: Broken\ntracks: []\n"
    if not tagged.startswith("created:"):
        manifest += "created: 2025-01-01T00:00:00\n"
    manifest += tagged
    path = _archive(tmp_path / "tagged.mdkv", manifest=manifest)
    with pytest.raises(MDKVFormatError):
        load_mdkv(path)
    original = path.read_bytes()
    invalid = _document()
    invalid.metadata["unserializable"] = object()
    with pytest.raises(ValidationError):
        save_mdkv_incremental(invalid, path)
    assert path.read_bytes() == original
    assert save_mdkv_incremental(_document(), path) is False
    loaded = load_mdkv(path)
    assert loaded.title == "Replacement"
    assert loaded.tracks["primary"].content == "Preserved output"


@pytest.mark.parametrize("created", ["!!timestamp 2025-01-01", "!!timestamp 2025-01-01T00:00:00"])
def test_legitimate_yaml_dates_remain_supported(tmp_path, created):
    manifest = MANIFEST.replace("created: 2025-01-01T00:00:00", f"created: {created}")
    path = _archive(tmp_path / "date.mdkv", manifest=manifest)
    assert load_mdkv(path).created == datetime(2025, 1, 1)


@pytest.mark.parametrize("compression", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
@pytest.mark.parametrize("name", ["tracks/primary.md", "extra.bin"])
def test_referenced_and_extra_members_require_actual_crc(tmp_path, compression, name):
    path = _archive(tmp_path / "bad-crc.mdkv", compression=compression, extra=b"Extra")
    with zipfile.ZipFile(path) as archive:
        local = archive.getinfo(name).header_offset
    data = bytearray(path.read_bytes())
    central = data.index(b"PK\x01\x02")
    while data[central:central + 4] == b"PK\x01\x02":
        name_size, extra_size, comment_size = struct.unpack_from("<HHH", data, central + 28)
        if data[central + 46:central + 46 + name_size].decode() == name:
            struct.pack_into("<I", data, central + 16, 0)
            break
        central += 46 + name_size + extra_size + comment_size
    else:
        raise AssertionError(f"missing fixture member: {name}")
    struct.pack_into("<I", data, local + 14, 0)
    path.write_bytes(data)
    with pytest.raises(MDKVFormatError, match="CRC"):
        load_mdkv(path)


def test_truncated_raw_deflate_rejected_for_unreferenced_extra(tmp_path):
    path = _archive(tmp_path / "truncated-stream.mdkv", compression=zipfile.ZIP_DEFLATED,
                    extra=b"A" * 8192)
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo("extra.bin")
        local, compressed_size = info.header_offset, info.compress_size
    data = bytearray(path.read_bytes())
    central = data.index(b"PK\x01\x02")
    while data[central:central + 4] == b"PK\x01\x02":
        name_size, extra_size, comment_size = struct.unpack_from("<HHH", data, central + 28)
        if data[central + 46:central + 46 + name_size] == b"extra.bin":
            struct.pack_into("<I", data, central + 20, compressed_size - 1)
            break
        central += 46 + name_size + extra_size + comment_size
    else:
        raise AssertionError("missing fixture extra")
    struct.pack_into("<I", data, local + 18, compressed_size - 1)
    path.write_bytes(data)
    with pytest.raises(MDKVFormatError):
        load_mdkv(path)
