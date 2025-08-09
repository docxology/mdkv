import io
import tempfile
from datetime import datetime
from pathlib import Path

from mdkv.model import Track, MDKVDocument
from mdkv.io import save_mdkv, load_mdkv


def _sample_doc():
    doc = MDKVDocument(title="Doc", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# H\n\nHi"))
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "Note"))
    return doc


def test_roundtrip_zip_save_and_load(tmp_path: Path):
    doc = _sample_doc()
    out = tmp_path / "doc.mdkv"
    save_mdkv(doc, out)
    assert out.exists() and out.stat().st_size > 0

    loaded = load_mdkv(out)
    assert loaded.title == doc.title
    assert set(loaded.tracks.keys()) == set(doc.tracks.keys())
    assert loaded.tracks["primary"].content == doc.tracks["primary"].content


