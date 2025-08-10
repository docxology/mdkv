from __future__ import annotations

"""Export utilities for MDKV documents.

Compose multi-track Markdown or single-track HTML renderings for distribution.
"""

from pathlib import Path
from typing import List

from markdown_it import MarkdownIt

from mdkv.core.model import MDKVDocument


def to_markdown(doc: MDKVDocument, include_track_types: List[str] | None = None) -> str:
    """Render `doc` to Markdown.

    If `include_track_types` is provided, only those track types are exported.
    Each track is prefixed with a lightweight HTML comment header encoding
    metadata for round-trip compatibility.
    """
    include = set(include_track_types) if include_track_types else None
    parts: List[str] = [f"<!-- MDKV: {doc.title} -->"]
    for track in doc.tracks.values():
        if include is not None and track.track_type not in include:
            continue
        header = f"\n\n<!-- track:{track.track_id} type:{track.track_type} lang:{track.language} -->\n\n"
        parts.append(header + track.content)
    return "".join(parts)


def to_html(doc: MDKVDocument) -> str:
    """Render HTML for the primary track of `doc`."""
    md = MarkdownIt()
    return md.render(to_markdown(doc, include_track_types=["primary"]))


def export_to_files(doc: MDKVDocument, output_dir: Path, include_track_types: List[str] | None = None) -> None:
    """Write track contents to individual `.md` files in `output_dir`.

    Filenames are derived from `track_id`.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    include = set(include_track_types) if include_track_types else None
    for track in doc.tracks.values():
        if include is not None and track.track_type not in include:
            continue
        # write each track content to a file named after track_id with .md extension
        out = output_dir / f"{track.track_id}.md"
        out.write_text(track.content, encoding="utf-8")


