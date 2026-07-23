"""Tests for enhanced search with track_type and language in SearchMatch."""
from datetime import datetime

from mdkv.core.model import MDKVDocument, Track
from mdkv.services.search import search_document


def _doc() -> MDKVDocument:
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "alpha beta gamma"))
    d.add_track(Track("fr", "translation", "fr", "tracks/fr.md", "beta gamma delta"))
    d.add_track(Track("notes", "commentary", None, "tracks/notes.md", "beta is here"))
    return d


def test_search_match_has_track_type_and_language():
    d = _doc()
    matches = search_document(d, pattern="beta")
    by_id = {m.track_id: m for m in matches}
    assert by_id["p"].track_type == "primary"
    assert by_id["p"].language == "en"
    assert by_id["fr"].track_type == "translation"
    assert by_id["fr"].language == "fr"
    assert by_id["notes"].track_type == "commentary"
    assert by_id["notes"].language is None


def test_search_no_matches_returns_empty():
    d = _doc()
    matches = search_document(d, pattern="zzzznotfound")
    assert matches == []


def test_search_regex_pattern():
    d = _doc()
    matches = search_document(d, pattern=r"beta.*gamma")
    assert len(matches) >= 1
    assert all("beta" in m.extract for m in matches)
