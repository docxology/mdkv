from __future__ import annotations

"""Optional native conversion through Pandoc.

The default reader disables raw TeX/HTML, custom document metadata cannot become
converter configuration, and Pandoc uses its sandbox. PDF engines remain external
programs, not a security sandbox: convert only trusted documents to PDF. Extra
arguments, cover images and reference documents are trusted caller capabilities.
"""

import shutil
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

from mdkv.core.model import MDKVDocument
from mdkv.services.export import _frontmatter


def _check_pandoc() -> str:
    """Return the installed Pandoc executable or raise FileNotFoundError."""
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise FileNotFoundError("pandoc is not installed. Install it from https://pandoc.org/installing.html")
    return pandoc


def _write_temp_markdown(
    doc: MDKVDocument, include_track_types: list[str] | None,
    metadata_header: bool, tmpdir: Path,
) -> Path:
    include = set(include_track_types) if include_track_types is not None else None
    body = "\n\n".join(track.content for track in doc.tracks.values()
                       if include is None or track.track_type in include)
    if metadata_header:
        # Freeform fields such as header-includes are converter instructions.
        safe_doc = replace(doc, metadata={key: value for key, value in doc.metadata.items()
                                        if key in {"date", "lang"}})
        body = _frontmatter(safe_doc) + body
    md_path = tmpdir / "document.md"
    md_path.write_text(body, encoding="utf-8")
    return md_path


def _convert(
    doc: MDKVDocument, output_path: Path, include_track_types: list[str] | None,
    metadata_header: bool, pandoc_args: list[str] | None, resource_args: list[str],
) -> Path:
    pandoc = _check_pandoc()
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".mdkv-pandoc-", dir=out_path.parent) as temporary:
        tmpdir = Path(temporary).resolve()
        source = _write_temp_markdown(doc, include_track_types, metadata_header, tmpdir)
        rendered = tmpdir / ("rendered" + out_path.suffix)
        cmd = [
            pandoc, str(source), "-o", str(rendered), "--standalone", "--sandbox",
            "--from=markdown-raw_tex-raw_html-raw_attribute", *resource_args,
        ]
        if out_path.suffix.lower() == ".pdf":
            cmd.append("--pdf-engine-opt=-no-shell-escape")
        if pandoc_args:
            cmd.extend(pandoc_args)
        subprocess.run(cmd, cwd=tmpdir, stdin=subprocess.DEVNULL, capture_output=True,
                       text=True, timeout=120, check=True)
        rendered.replace(out_path)
    return out_path


def to_pdf(
    doc: MDKVDocument, output_path: Path, include_track_types: list[str] | None = None,
    metadata_header: bool = True, pandoc_args: list[str] | None = None,
) -> Path:
    """Convert a trusted document to PDF using installed Pandoc and a TeX engine.

    Raw TeX/HTML and converter-configuration metadata are disabled by default;
    Pandoc's sandbox does not isolate the PDF engine. Extra arguments are trusted.
    Failure preserves any existing destination. Errors propagate as
    ``FileNotFoundError``, ``CalledProcessError`` or ``TimeoutExpired``.
    """
    return _convert(doc, output_path, include_track_types, metadata_header, pandoc_args, [])


def to_epub(
    doc: MDKVDocument, output_path: Path, include_track_types: list[str] | None = None,
    metadata_header: bool = True, cover_image: Path | None = None,
    pandoc_args: list[str] | None = None,
) -> Path:
    """Convert to EPUB with sandboxed Pandoc; explicit resources/args are trusted.

    Failed conversion preserves any existing output. External resources may be
    unavailable under the sandbox; stage and authorize them explicitly.
    """
    resources = [f"--epub-cover-image={Path(cover_image).resolve()}"] if cover_image else []
    return _convert(doc, output_path, include_track_types, metadata_header, pandoc_args, resources)


def to_docx(
    doc: MDKVDocument, output_path: Path, include_track_types: list[str] | None = None,
    metadata_header: bool = True, reference_doc: Path | None = None,
    pandoc_args: list[str] | None = None,
) -> Path:
    """Convert to DOCX with sandboxed Pandoc and optional trusted reference document.

    Failed conversion preserves any existing output.
    """
    resources = [f"--reference-doc={Path(reference_doc).resolve()}"] if reference_doc else []
    return _convert(doc, output_path, include_track_types, metadata_header, pandoc_args, resources)
