from datetime import datetime

from mdkv.core.model import MDKVDocument, Track
from mdkv.services.export import to_markdown


def test_to_markdown_include_filter():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "# P"))
    d.add_track(Track("n", "commentary", None, "tracks/n.md", "Note"))
    md = to_markdown(d, include_track_types=["commentary"])
    assert "Note" in md and "# P" not in md


