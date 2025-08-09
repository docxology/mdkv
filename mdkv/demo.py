from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .core.model import MDKVDocument, Track
from .storage import save_mdkv


def build_multitrack_demo_document(title: str = "MDKV Demo") -> MDKVDocument:
    doc = MDKVDocument(title=title, authors=["MDKV"], created=datetime.utcnow())

    primary_md = (
        "# MDKV Multitrack Demo\n\n"
        "This is a primary track in English. It shows headings, lists, and links.\n\n"
        "- Feature: multitrack content\n"
        "- Feature: metadata and validation\n"
        "- Feature: export and search\n\n"
        "See the [MDKV format overview](https://example.org/mdkv).\n"
    )
    fr_md = (
        "# Démonstration MDKV\n\n"
        "Piste principale traduite en français (exemple).\n\n"
        "- Fonctionnalité: contenu multi-pistes\n"
        "- Fonctionnalité: métadonnées et validation\n"
    )
    annotations_md = (
        "# Annotations\n\n"
        "- Note: Draft content.\n"
        "- Suggestion: Add more examples.\n"
    )
    refs_md = (
        "# References\n\n"
        "- RFC 9559 (Matroska)\n"
        "- CommonMark Spec\n"
    )
    media_md = (
        "# Media References\n\n"
        "- https://example.org/video.mp4\n"
        "- https://example.org/image.png\n"
    )

    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", primary_md))
    doc.add_track(Track("translation-fr", "translation", "fr", "tracks/translation-fr.md", fr_md))
    doc.add_track(Track("annotations", "commentary", None, "tracks/annotations.md", annotations_md))
    doc.add_track(Track("refs", "reference", None, "tracks/refs.md", refs_md))
    doc.add_track(Track("media", "media_ref", None, "tracks/media.md", media_md))

    doc.set_metadata("demo", "true")
    return doc


def write_demo_mdkv(output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = build_multitrack_demo_document()
    save_mdkv(doc, output_path)
    return output_path


