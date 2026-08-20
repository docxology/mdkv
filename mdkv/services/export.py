from __future__ import annotations

"""Export utilities for MDKV documents.

Compose multi-track Markdown or single-track HTML renderings for distribution.
"""

import re
from pathlib import Path

from markdown_it import MarkdownIt

from mdkv.core.model import MDKVDocument


def _safe_filename(track_id: str) -> str:
    """Sanitize a track_id for use as a filename, preventing path traversal.

    Strips directory separators and other dangerous characters.
    """
    # Remove any path components — keep only the basename
    safe = Path(track_id).name
    # Replace any remaining non-alphanumeric characters (except - and _) with _
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", safe)
    if not safe or safe.startswith("."):
        return f"_{safe}" if safe else "unnamed"
    return safe


def to_markdown(
    doc: MDKVDocument,
    include_track_types: list[str] | None = None,
    metadata_header: bool = False,
) -> str:
    """Render ``doc`` to Markdown.

    If ``include_track_types`` is provided, only those track types are exported.
    If ``metadata_header`` is True, prepend a YAML-style frontmatter block
    with document metadata (title, authors, version, created).
    Each track is prefixed with a lightweight HTML comment header encoding
    metadata for round-trip compatibility.
    """
    parts: list[str] = []
    if metadata_header:
        import yaml as _yaml
        frontmatter = {
            "title": doc.title,
            "authors": list(doc.authors),
            "version": doc.version,
            "created": doc.created.isoformat(),
        }
        if doc.metadata:
            frontmatter.update(doc.metadata)
        parts.append("---")
        parts.append(_yaml.safe_dump(frontmatter, sort_keys=False, default_flow_style=False).strip())
        parts.append("---")
        parts.append("")

    include = set(include_track_types) if include_track_types else None
    # Escape the title in the comment to prevent comment-injection (-->)
    safe_title = doc.title.replace("-->", "")
    parts.append(f"<!-- MDKV: {safe_title} -->")
    for track in doc.tracks.values():
        if include is not None and track.track_type not in include:
            continue
        # Escape track metadata in comment to prevent comment-injection (-->)
        safe_id = track.track_id.replace("-->", "")
        safe_type = track.track_type.replace("-->", "")
        safe_lang = str(track.language).replace("-->", "") if track.language else "None"
        header = f"\n\n<!-- track:{safe_id} type:{safe_type} lang:{safe_lang} -->\n\n"
        parts.append(header + track.content)
    return "".join(parts)


def to_html(
    doc: MDKVDocument,
    include_track_types: list[str] | None = None,
    metadata_header: bool = False,
) -> str:
    """Render HTML from ``doc``.

    By default renders only the ``primary`` track (backward-compatible).
    If ``include_track_types`` is provided, renders those track types instead.
    If ``metadata_header`` is True, includes YAML frontmatter in the source
    before rendering (useful for standalone HTML documents).
    """
    md = MarkdownIt()
    if include_track_types is None:
        include_track_types = ["primary"]
    rendered = md.render(to_markdown(doc, include_track_types=include_track_types, metadata_header=metadata_header))
    return str(rendered)


def export_to_files(
    doc: MDKVDocument,
    output_dir: Path,
    include_track_types: list[str] | None = None,
) -> list[Path]:
    """Write track contents to individual ``.md`` files in ``output_dir``.

    Filenames are derived from ``track_id``.  Returns the list of written paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    include = set(include_track_types) if include_track_types else None
    written: list[Path] = []
    for track in doc.tracks.values():
        if include is not None and track.track_type not in include:
            continue
        out = output_dir / f"{_safe_filename(track.track_id)}.md"
        out.write_text(track.content, encoding="utf-8")
        written.append(out)
    return written
