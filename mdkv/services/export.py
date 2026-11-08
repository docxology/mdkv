from __future__ import annotations

"""Export utilities for MDKV documents.

Compose multi-track Markdown or single-track HTML renderings for distribution.
"""

import os
import re
import tempfile
from html import escape
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


def _frontmatter(doc: MDKVDocument) -> str:
    """Serialize canonical fields once for Markdown and native exporters."""
    import yaml

    fields = {
        "title": doc.title,
        "author": list(doc.authors),
        "authors": list(doc.authors),
        "version": doc.version,
        "created": doc.created.isoformat(),
    }
    fields.update({key: value for key, value in doc.metadata.items() if key not in fields})
    return "---\n" + yaml.safe_dump(fields, sort_keys=False, default_flow_style=False) + "---\n\n"


def to_markdown(
    doc: MDKVDocument,
    include_track_types: list[str] | None = None,
    metadata_header: bool = False,
) -> str:
    """Render ``doc`` to Markdown.

    If ``include_track_types`` is provided, only those track types are exported.
    If ``metadata_header`` is True, prepend a YAML-style frontmatter block
    with document metadata (title, authors, version, created).
    Each track has an informational attribution comment. These hints do not
    define a lossless combined-Markdown import format.
    """
    parts: list[str] = []
    if metadata_header:
        parts.append(_frontmatter(doc))

    include = set(include_track_types) if include_track_types is not None else None
    safe_title = escape(doc.title, quote=True)
    parts.append(f"<!-- MDKV: {safe_title} -->")
    for track in doc.tracks.values():
        if include is not None and track.track_type not in include:
            continue
        safe_id = escape(track.track_id, quote=True)
        safe_type = escape(track.track_type, quote=True)
        safe_lang = escape(str(track.language), quote=True) if track.language else "None"
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
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    include = set(include_track_types) if include_track_types is not None else {"primary"}
    source = "\n\n".join(t.content for t in doc.tracks.values() if t.track_type in include)
    if metadata_header:
        source = to_markdown(doc, include_track_types=list(include), metadata_header=True)
    return str(md.render(source))


def export_to_files(
    doc: MDKVDocument,
    output_dir: Path,
    include_track_types: list[str] | None = None,
) -> list[Path]:
    """Write track contents to individual ``.md`` files in ``output_dir``.

    Filenames are derived from ``track_id``. Case-insensitive filename collisions
    raise ``ValueError`` before writing anything. Existing symlink destinations
    are refused; regular files are replaced atomically without following links.
    This is not a transactional multi-file export or a same-user sandbox.
    """
    output_dir = Path(output_dir)
    include = set(include_track_types) if include_track_types is not None else None
    planned: list[tuple[Path, str]] = []
    names: set[str] = set()
    for track in doc.tracks.values():
        if include is not None and track.track_type not in include:
            continue
        out = output_dir / f"{_safe_filename(track.track_id)}.md"
        if out.name.casefold() in names:
            raise ValueError(f"track export filename collision: {out.name}")
        names.add(out.name.casefold())
        if out.is_symlink():
            raise ValueError(f"refusing symlink export destination: {out}")
        planned.append((out, track.content))
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for out, content in planned:
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", dir=output_dir,
                prefix=".mdkv-export-", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(out)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        written.append(out)
    return written
