from datetime import datetime

from mdkv.model import Track, MDKVDocument
from mdkv.search import search_document


def test_search_across_tracks():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "alpha beta gamma"))
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "beta is here"))

    matches = search_document(doc, pattern="beta")
    assert {m.track_id for m in matches} == {"primary", "notes"}
    assert all("beta" in m.extract for m in matches)


