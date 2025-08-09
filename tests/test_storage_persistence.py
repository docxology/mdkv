from datetime import datetime
from pathlib import Path

from mdkv.core.model import MDKVDocument, Track
from mdkv.storage import save_mdkv, load_mdkv


def test_metadata_persistence_roundtrip(tmp_path: Path):
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("p", "primary", "en", "tracks/p.md", "text"))
    doc.set_metadata("project", "mdkv")
    path = tmp_path / "doc.mdkv"
    save_mdkv(doc, path)
    loaded = load_mdkv(path)
    assert loaded.get_metadata("project") == "mdkv"


