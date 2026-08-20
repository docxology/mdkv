"""Tests for case_insensitive search flag and metadata_header export."""
from datetime import datetime

from mdkv.core.model import MDKVDocument, Track
from mdkv.services.export import to_html, to_markdown
from mdkv.services.search import search_document


def _doc() -> MDKVDocument:
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1), version="1.0.0")
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "Hello World"))
    d.add_track(Track("fr", "translation", "fr", "tracks/fr.md", "HELLO world"))
    return d


def test_search_case_insensitive_flag():
    d = _doc()
    # case-sensitive: only "Hello World" matches "Hello"
    m_cs = search_document(d, pattern="Hello")
    assert {x.track_id for x in m_cs} == {"p"}
    # case-insensitive: both match
    m_ci = search_document(d, pattern="Hello", case_insensitive=True)
    assert {x.track_id for x in m_ci} == {"p", "fr"}


def test_search_case_insensitive_with_flags():
    d = _doc()
    # combining case_insensitive=True with other flags should work
    m = search_document(d, pattern="hello", case_insensitive=True)
    assert len(m) == 2


def test_to_markdown_metadata_header():
    d = _doc()
    md = to_markdown(d, metadata_header=True)
    assert md.startswith("---")
    assert "title: T" in md
    assert "authors:" in md
    assert "- A" in md
    assert "version: 1.0.0" in md
    assert "---" in md


def test_to_markdown_no_metadata_header_by_default():
    d = _doc()
    md = to_markdown(d)
    assert not md.startswith("---")


def test_to_html_with_metadata_header():
    d = _doc()
    html = to_html(d, include_track_types=["primary"], metadata_header=True)
    assert "<" in html  # valid HTML output


def test_to_markdown_metadata_header_includes_custom_metadata():
    d = _doc()
    d.set_metadata("project", "test")
    d.set_metadata("year", "2025")
    md = to_markdown(d, metadata_header=True)
    assert "project: test" in md or "project: 'test'" in md
    assert "year" in md and "2025" in md
