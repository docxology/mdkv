from datetime import datetime

from mdkv.core.model import MDKVDocument, Track
from mdkv.services.search import search_document


def test_search_with_filters_on_type_and_language():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("p", "primary", "en", "tracks/p.md", "alpha beta"))
    doc.add_track(Track("fr", "translation", "fr", "tracks/fr.md", "beta gamma"))

    # filter to only translation in fr
    matches = search_document(doc, pattern="beta", track_types=["translation"], languages=["fr"])
    assert {m.track_id for m in matches} == {"fr"}


