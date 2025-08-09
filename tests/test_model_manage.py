from datetime import datetime

import pytest

from mdkv.core.model import MDKVDocument, Track


def _doc():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "hi"))
    d.add_track(Track("trans-fr", "translation", "fr", "tracks/trans-fr.md", "salut"))
    d.add_track(Track("notes", "commentary", None, "tracks/notes.md", "n"))
    return d


def test_find_tracks_by_type_and_update_content():
    d = _doc()
    ts = d.find_tracks_by_type("translation")
    assert len(ts) == 1 and ts[0].track_id == "trans-fr"
    d.update_track_content("trans-fr", "bonjour")
    assert d.get_track("trans-fr").content == "bonjour"


def test_rename_track_and_collision():
    d = _doc()
    d.rename_track("notes", "commentary")
    assert d.get_track("commentary") is not None and d.get_track("notes") is None
    with pytest.raises(ValueError):
        d.rename_track("primary", "commentary")


def test_metadata_ops():
    d = _doc()
    d.set_metadata("k", "v")
    assert d.get_metadata("k") == "v"
    assert d.get_metadata("missing", default="x") == "x"
    d.remove_metadata("k")
    assert d.get_metadata("k") is None


