from datetime import datetime
from pathlib import Path

from mdkv.core.model import MDKVDocument, Track
from mdkv.services.export import export_to_files


def test_export_to_files(tmp_path: Path):
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("p", "primary", "en", "tracks/p.md", "# H"))
    doc.add_track(Track("n", "commentary", None, "tracks/n.md", "note"))
    outdir = tmp_path / "out"
    export_to_files(doc, outdir, include_track_types=["primary", "commentary"])
    assert (outdir / "p.md").exists()
    assert (outdir / "n.md").read_text(encoding="utf-8").strip() == "note"


