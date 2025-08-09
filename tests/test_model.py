import io
from datetime import datetime

from mdkv.model import Track, MDKVDocument, allowed_track_types


def test_create_document_and_tracks():
    doc = MDKVDocument(
        title="Sample",
        authors=["Author"],
        created=datetime(2025, 1, 1),
    )
    primary = Track(track_id="primary", track_type="primary", language="en", path="tracks/primary.md", content="# Title\n\nHello")
    translation = Track(track_id="translation-en", track_type="translation", language="en", path="tracks/translation-en.md", content="Hello")

    doc.add_track(primary)
    doc.add_track(translation)

    assert doc.title == "Sample"
    assert set(doc.tracks.keys()) == {"primary", "translation-en"}
    assert "primary" in doc.tracks
    assert doc.tracks["primary"].content.startswith("# Title")
    # allowed types sanity
    assert "primary" in allowed_track_types()


