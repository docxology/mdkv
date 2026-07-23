"""Tests for v0.8.0: TrackHistory, plugin registry, incremental save, async search,
benchmarks, i18n, GUI theme/drag-drop/diff."""
import asyncio
import zipfile
from datetime import datetime, timezone

import pytest

from mdkv import MDKVDocument, Track, save_mdkv, load_mdkv
from mdkv.core.history import TrackHistory, TrackVersion
from mdkv.core.registry import TrackTypeRegistry, register_track_type, get_registry
from mdkv.services.search import search_document_async
from mdkv.storage.io import save_mdkv_incremental
from mdkv.i18n import set_language, gettext, _


# === TrackHistory ===

def test_track_history_add_and_get():
    h = TrackHistory("primary")
    h.add_version("v1", "primary", "en", datetime(2025, 1, 1))
    h.add_version("v2", "primary", "en", datetime(2025, 1, 2))
    assert len(h.versions) == 2
    assert h.get_current().content == "v2"


def test_track_history_get_version_at():
    h = TrackHistory("primary")
    h.add_version("v1", "primary", "en", datetime(2025, 1, 1))
    h.add_version("v2", "primary", "en", datetime(2025, 1, 2))
    v = h.get_version_at(datetime(2025, 1, 1, 12))
    assert v.content == "v1"


def test_track_history_restore_to():
    h = TrackHistory("primary")
    h.add_version("v1", "primary", "en", datetime(2025, 1, 1))
    h.add_version("v2", "primary", "en", datetime(2025, 1, 2))
    h.add_version("v3", "primary", "en", datetime(2025, 1, 3))
    restored = h.restore_to(datetime(2025, 1, 2))
    assert restored.content == "v2"
    assert len(h.versions) == 2  # v3 was truncated


def test_track_history_empty():
    h = TrackHistory("empty")
    assert h.get_current() is None
    assert h.list_versions() == []


def test_track_history_to_dict():
    h = TrackHistory("primary")
    h.add_version("v1", "primary", "en", datetime(2025, 1, 1))
    d = h.to_dict()
    assert d["track_id"] == "primary"
    assert len(d["versions"]) == 1
    assert d["versions"][0]["content"] == "v1"


# === Plugin Registry ===

def test_registry_builtin_types():
    reg = TrackTypeRegistry()
    assert reg.is_registered("primary")
    assert reg.is_registered("translation")
    assert reg.is_registered("code")
    assert "primary" in reg.all_types()


def test_registry_register_custom():
    reg = TrackTypeRegistry()
    reg.register("custom_type", description="My custom type")
    assert reg.is_registered("custom_type")
    assert "custom_type" in reg.custom_types()
    assert "primary" not in reg.custom_types()


def test_registry_register_duplicate():
    reg = TrackTypeRegistry()
    with pytest.raises(ValueError, match="already registered"):
        reg.register("primary")


def test_registry_unregister():
    reg = TrackTypeRegistry()
    reg.register("temp_type")
    reg.unregister("temp_type")
    assert not reg.is_registered("temp_type")


def test_registry_unregister_builtin():
    reg = TrackTypeRegistry()
    with pytest.raises(ValueError, match="built-in"):
        reg.unregister("primary")


def test_registry_validate():
    reg = TrackTypeRegistry()
    reg.register("custom", validator=lambda c: ["warning"] if "bad" in c else [])
    assert reg.validate("custom", "bad content") == ["warning"]
    assert reg.validate("custom", "good content") == []


def test_global_register_track_type():
    register_track_type("global_custom", description="Test")
    reg = get_registry()
    assert reg.is_registered("global_custom")
    # Clean up
    reg.unregister("global_custom")


# === Incremental Save ===

def test_incremental_save_new_file(tmp_path):
    """Should fall back to full save if file doesn't exist."""
    from pathlib import Path
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "content"))
    p = tmp_path / "new.mdkv"
    result = save_mdkv_incremental(doc, p)
    assert result is False  # full save was used
    assert p.exists()
    assert load_mdkv(p).tracks["primary"].content == "content"


def test_incremental_save_existing_file(tmp_path):
    """Should use incremental save when file exists."""
    from pathlib import Path
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "original"))
    p = tmp_path / "existing.mdkv"
    save_mdkv(doc, p)
    # Modify content
    doc.update_track_content("primary", "updated")
    result = save_mdkv_incremental(doc, p)
    assert result is True
    assert load_mdkv(p).tracks["primary"].content == "updated"


# === Async Search ===

def test_async_search_basic():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("p", "primary", "en", "tracks/p.md", "alpha beta gamma"))
    doc.add_track(Track("n", "commentary", None, "tracks/n.md", "beta delta"))

    async def run():
        matches = []
        async for m in search_document_async(doc, pattern="beta"):
            matches.append(m)
        return matches

    matches = asyncio.run(run())
    assert len(matches) == 2
    assert {m.track_id for m in matches} == {"p", "n"}


def test_async_search_limit():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("p", "primary", "en", "tracks/p.md", "a a a a a"))

    async def run():
        matches = []
        async for m in search_document_async(doc, pattern="a", limit=3):
            matches.append(m)
        return matches

    matches = asyncio.run(run())
    assert len(matches) == 3


def test_async_search_offset():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("p", "primary", "en", "tracks/p.md", "a a a a a"))

    async def run():
        matches = []
        async for m in search_document_async(doc, pattern="a", offset=2, limit=2):
            matches.append(m)
        return matches

    matches = asyncio.run(run())
    assert len(matches) == 2


# === i18n ===

def test_i18n_default_english():
    set_language("en")
    assert gettext("test") == "test"
    assert _("test") == "test"


def test_i18n_unknown_language_fallback():
    set_language("xx")  # not translated
    assert gettext("test") == "test"  # falls back to English
