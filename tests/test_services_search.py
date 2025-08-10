from datetime import datetime

from mdkv.core.model import MDKVDocument, Track
from mdkv.services.search import search_document


def test_search_flags_and_filters():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "Alpha beta"))
    d.add_track(Track("fr", "translation", "fr", "tracks/fr.md", "BETA"))
    # case-insensitive across selected language
    m = search_document(d, pattern="beta", flags=0, languages=["fr"])
    assert {x.track_id for x in m} == set()
    m2 = search_document(d, pattern="beta", flags=0)
    assert {x.track_id for x in m2} == {"p"}
    m3 = search_document(d, pattern="beta", flags=2)  # re.IGNORECASE value is 2
    assert {x.track_id for x in m3} == {"p", "fr"}


