from datetime import datetime

from mdkv.model import Track, MDKVDocument
from mdkv.export import to_markdown, to_html


def test_export_markdown_combines_tracks():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# A\n\nHi"))
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "Note"))

    md = to_markdown(doc)
    assert "# A" in md and "Note" in md


def test_export_html_basic():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# A\n\nHi"))
    html = to_html(doc)
    assert "<h1>A</h1>" in html or "<h1> A </h1>" in html


