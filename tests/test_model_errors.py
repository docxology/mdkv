import pytest
from datetime import datetime

from mdkv.core.model import Track, MDKVDocument


def test_track_validation_errors():
    with pytest.raises(ValueError):
        Track("id", "unknown", None, "tracks/x.md", "")
    with pytest.raises(ValueError):
        Track("", "primary", None, "tracks/x.md", "")
    with pytest.raises(ValueError):
        Track("id", "primary", None, "other/x.md", "")


def test_document_error_branches():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    # remove_track missing
    with pytest.raises(KeyError):
        d.remove_track("missing")
    # update missing
    with pytest.raises(KeyError):
        d.update_track_content("missing", "x")
    # rename missing
    with pytest.raises(KeyError):
        d.rename_track("old", "new")
    # rename duplicate
    d.add_track(Track("a", "primary", "en", "tracks/a.md", ""))
    d.add_track(Track("b", "commentary", None, "tracks/b.md", ""))
    with pytest.raises(ValueError):
        d.rename_track("a", "b")


