from datetime import datetime

from mdkv.model import MDKVDocument, Track
from mdkv.search import search_document


def test_search_across_tracks():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "alpha beta gamma"))
    doc.add_track(Track("notes", "commentary", "fr", "tracks/notes.md", "beta is here"))

    matches = search_document(doc, pattern="beta")
    assert {m.track_id for m in matches} == {"primary", "notes"}
    assert all("beta" in m.extract for m in matches)

    # Filtering by type
    m_types = search_document(doc, pattern="beta", track_types=["commentary"])
    assert len(m_types) == 1
    assert m_types[0].track_id == "notes"

    # Filtering by language
    m_lang = search_document(doc, pattern="beta", languages=["en"])
    assert len(m_lang) == 1
    assert m_lang[0].track_id == "primary"


