from __future__ import annotations

"""Pandoc-based export services for MDKV documents.

Renders documents to PDF, EPUB, and DOCX formats using ``pandoc`` as a
subprocess.  This mirrors the approach used by the docxology/template
infrastructure's rendering module — pandoc is the single conversion engine,
no Python PDF/EPUB libraries are introduced.

If ``pandoc`` is not installed, a clear ``FileNotFoundError`` is raised
with installation instructions.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from mdkv.core.model import MDKVDocument
from mdkv.services.export import to_markdown


def _check_pandoc() -> str:
    """Return the path to pandoc or raise FileNotFoundError."""
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise FileNotFoundError(
            "pandoc is not installed. Install it from https://pandoc.org/installing.html"
        )
    return pandoc


def _write_temp_markdown(doc: MDKVDocument, include_track_types: list[str] | None,
                         metadata_header: bool, tmpdir: Path) -> Path:
    """Write the document as combined Markdown to a temp file and return the path."""
    md = to_markdown(doc, include_track_types=include_track_types, metadata_header=metadata_header)
    md_path = tmpdir / "document.md"
    md_path.write_text(md, encoding="utf-8")
    return md_path


def to_pdf(
    doc: MDKVDocument,
    output_path: Path,
    include_track_types: list[str] | None = None,
    metadata_header: bool = True,
    pandoc_args: list[str] | None = None,
) -> Path:
    """Render ``doc`` to a PDF file using pandoc.

    Requires ``pandoc`` and a LaTeX engine (e.g. ``pdflatex`` or ``xelatex``)
    to be installed.

    Args:
        doc: Document to render.
        output_path: Target .pdf path; parent created if missing.
        include_track_types: Optional track type filter.
        metadata_header: Include YAML frontmatter (recommended for PDF title/author).
        pandoc_args: Extra arguments passed to pandoc (e.g. ``["--pdf-engine=xelatex"]``).

    Returns:
        Path to the generated PDF file.

    Raises:
        FileNotFoundError: pandoc not installed.
        subprocess.CalledProcessError: pandoc conversion failed.
    """
    pandoc = _check_pandoc()
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir_path = Path(tmpdir)
        md_path = _write_temp_markdown(doc, include_track_types, metadata_header, tmp_dir_path)
        cmd = [pandoc, str(md_path), "-o", str(out_path), "--standalone"]
        if pandoc_args:
            cmd.extend(pandoc_args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
    return out_path


def to_epub(
    doc: MDKVDocument,
    output_path: Path,
    include_track_types: list[str] | None = None,
    metadata_header: bool = True,
    cover_image: Path | None = None,
    pandoc_args: list[str] | None = None,
) -> Path:
    """Render ``doc`` to an EPUB file using pandoc.

    Requires ``pandoc`` to be installed.

    Args:
        doc: Document to render.
        output_path: Target .epub path; parent created if missing.
        include_track_types: Optional track type filter.
        metadata_header: Include YAML frontmatter (recommended for EPUB metadata).
        cover_image: Optional path to a cover image.
        pandoc_args: Extra arguments passed to pandoc.

    Returns:
        Path to the generated EPUB file.

    Raises:
        FileNotFoundError: pandoc not installed.
        subprocess.CalledProcessError: pandoc conversion failed.
    """
    pandoc = _check_pandoc()
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir_path = Path(tmpdir)
        md_path = _write_temp_markdown(doc, include_track_types, metadata_header, tmp_dir_path)
        cmd = [pandoc, str(md_path), "-o", str(out_path), "--standalone"]
        if cover_image is not None:
            cmd.append(f"--epub-cover-image={cover_image}")
        if pandoc_args:
            cmd.extend(pandoc_args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
    return out_path


def to_docx(
    doc: MDKVDocument,
    output_path: Path,
    include_track_types: list[str] | None = None,
    metadata_header: bool = True,
    reference_doc: Path | None = None,
    pandoc_args: list[str] | None = None,
) -> Path:
    """Render ``doc`` to a DOCX file using pandoc.

    Requires ``pandoc`` to be installed.

    Args:
        doc: Document to render.
        output_path: Target .docx path; parent created if missing.
        include_track_types: Optional track type filter.
        metadata_header: Include YAML frontmatter (recommended for DOCX metadata).
        reference_doc: Optional .docx template for styling.
        pandoc_args: Extra arguments passed to pandoc.

    Returns:
        Path to the generated DOCX file.

    Raises:
        FileNotFoundError: pandoc not installed.
        subprocess.CalledProcessError: pandoc conversion failed.
    """
    pandoc = _check_pandoc()
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir_path = Path(tmpdir)
        md_path = _write_temp_markdown(doc, include_track_types, metadata_header, tmp_dir_path)
        cmd = [pandoc, str(md_path), "-o", str(out_path), "--standalone"]
        if reference_doc is not None:
            cmd.append(f"--reference-doc={reference_doc}")
        if pandoc_args:
            cmd.extend(pandoc_args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
    return out_path
