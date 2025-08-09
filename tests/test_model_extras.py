from datetime import datetime

from mdkv.model import MDKVDocument, Track


def _doc():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "hi"))
    d.add_track(Track("trans-fr", "translation", "fr", "tracks/trans-fr.md", "salut"))
    d.add_track(Track("notes", "commentary", None, "tracks/notes.md", "n"))
    return d


def test_get_and_remove_track():
    d = _doc()
    t = d.get_track("primary")
    assert t is not None and t.track_type == "primary"
    removed = d.remove_track("primary")
    assert removed.track_id == "primary"
    assert d.get_track("primary") is None


def test_list_languages_unique_sorted():
    d = _doc()
    langs = d.list_languages()
    assert langs == ["en", "fr"]


