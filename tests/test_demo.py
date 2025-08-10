from pathlib import Path

from mdkv.demo import build_multitrack_demo_document, write_demo_mdkv


def test_build_demo_document_and_write(tmp_path: Path):
    doc = build_multitrack_demo_document()
    assert "primary" in doc.tracks and "translation-fr" in doc.tracks
    out = tmp_path / "demo.mdkv"
    p = write_demo_mdkv(out)
    assert p.exists() and p.stat().st_size > 0


