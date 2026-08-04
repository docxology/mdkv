from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import click

from mdkv.storage import load_mdkv, save_mdkv, MDKVFormatError
from mdkv.core.model import MDKVDocument, Track
from mdkv.core.validate import validate_document
from mdkv.core.errors import ValidationError
from mdkv.services.export import to_markdown, to_html, export_to_files
from mdkv.services.search import search_document
from mdkv.services.diff import diff_documents
from mdkv.services.stats import compute_stats
from mdkv.gui import run as run_gui
from mdkv import __version__


def _handle_load_errors(fn):
    """Decorator that catches FileNotFoundError and MDKVFormatError from load_mdkv."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except FileNotFoundError as e:
            click.echo(f"ERROR: {e}", err=True)
            raise SystemExit(1)
        except MDKVFormatError as e:
            click.echo(f"ERROR: {e}", err=True)
            raise SystemExit(1)
    return wrapper


@click.group()
@click.version_option(version=__version__, prog_name="mdkv")
def main() -> None:
    """MDKV command-line interface."""


@main.command()
@click.option("--title", required=True)
@click.option("--author", multiple=True, required=True)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), required=True)
def init(title: str, author: list[str], out: Path) -> None:
    doc = MDKVDocument(title=title, authors=list(author), created=datetime.now(timezone.utc))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# New Document\n\nStart here."))
    save_mdkv(doc, out)
    click.echo(f"Created {out}")


@main.command()
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--format", "fmt", type=click.Choice(["json", "table"]), default="json",
              help="Output format (json or table)")
@_handle_load_errors
def info(path: Path, fmt: str) -> None:
    """Show document metadata and track index."""
    doc = load_mdkv(path)
    if fmt == "table":
        click.echo(f"Title:   {doc.title}")
        click.echo(f"Authors: {', '.join(doc.authors)}")
        click.echo(f"Version: {doc.version}")
        click.echo(f"Created: {doc.created.isoformat()}")
        click.echo(f"Tracks:  {len(doc.tracks)}")
        click.echo("")
        click.echo(f"{'ID':<20} {'Type':<15} {'Language':<10} {'Path'}")
        click.echo(f"{'--':<20} {'----':<15} {'--------':<10} {'----'}")
        for t in doc.tracks.values():
            lang = t.language or "-"
            click.echo(f"{t.track_id:<20} {t.track_type:<15} {lang:<10} {t.path}")
    else:
        click.echo(json.dumps({
            "title": doc.title,
            "authors": doc.authors,
            "version": doc.version,
            "tracks": [{
                "id": t.track_id,
                "type": t.track_type,
                "language": t.language,
                "path": t.path,
            } for t in doc.tracks.values()],
        }, indent=2))


@main.command("list-tracks")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@_handle_load_errors
def list_tracks(path: Path) -> None:
    doc = load_mdkv(path)
    rows = [
        {"id": t.track_id, "type": t.track_type, "language": t.language, "path": t.path}
        for t in doc.tracks.values()
    ]
    click.echo(json.dumps(rows, indent=2))


@main.command("add-track")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--id", "track_id", required=True)
@click.option("--type", "track_type", required=True)
@click.option("--lang", "language", required=False, default=None)
@click.option("--content", default=None, help="Track content as a string")
@click.option("--file", "content_file", type=click.Path(dir_okay=False, path_type=Path), default=None,
              help="Read track content from this file (overrides --content)")
@_handle_load_errors
def add_track_cmd(path: Path, track_id: str, track_type: str, language: str | None,
                  content: str | None, content_file: Path | None) -> None:
    """Add a new track to the document."""
    if content_file is not None:
        content = Path(content_file).read_text(encoding="utf-8")
    elif content is None:
        click.echo("ERROR: --content or --file is required", err=True)
        raise SystemExit(1)
    doc = load_mdkv(path)
    doc.add_track(Track(track_id, track_type, language if language else None,
                        f"tracks/{track_id}.md", content))
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("remove-track")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--id", "track_id", required=True)
@_handle_load_errors
def remove_track_cmd(path: Path, track_id: str) -> None:
    """Remove a track from the document."""
    doc = load_mdkv(path)
    try:
        doc.remove_track(track_id)
    except KeyError:
        click.echo(f"ERROR: track '{track_id}' not found", err=True)
        raise SystemExit(1)
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("export-tracks")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--types", required=True, help="Comma-separated track types to include")
@_handle_load_errors
def export_tracks(path: Path, types: str) -> None:
    doc = load_mdkv(path)
    include = [t.strip() for t in types.split(",") if t.strip()]
    click.echo(to_markdown(doc, include_track_types=include))


@main.command("rename-track")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--old-id", required=True)
@click.option("--new-id", required=True)
@_handle_load_errors
def rename_track_cmd(path: Path, old_id: str, new_id: str) -> None:
    doc = load_mdkv(path)
    doc.rename_track(old_id, new_id)
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("move-track")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--id", "track_id", required=True)
@click.option("--after-id", default=None, help="Track ID to insert after (omit for first position)")
@_handle_load_errors
def move_track_cmd(path: Path, track_id: str, after_id: str | None) -> None:
    """Reorder a track within the document."""
    doc = load_mdkv(path)
    try:
        doc.move_track(track_id, after_id)
    except KeyError:
        click.echo(f"ERROR: track '{track_id}' not found", err=True)
        raise SystemExit(1)
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("update-track")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--id", "track_id", required=True)
@click.option("--content", default=None, help="New content as a string")
@click.option("--file", "content_file", type=click.Path(dir_okay=False, path_type=Path), default=None,
              help="Read new content from this file (overrides --content)")
@_handle_load_errors
def update_track_cmd(path: Path, track_id: str, content: str | None,
                     content_file: Path | None) -> None:
    """Update the content of an existing track."""
    if content_file is not None:
        content = Path(content_file).read_text(encoding="utf-8")
    elif content is None:
        click.echo("ERROR: --content or --file is required", err=True)
        raise SystemExit(1)
    doc = load_mdkv(path)
    doc.update_track_content(track_id, content)
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("set-meta")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.argument("key")
@click.argument("value")
@_handle_load_errors
def set_meta(path: Path, key: str, value: str) -> None:
    doc = load_mdkv(path)
    doc.set_metadata(key, value)
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("get-meta")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.argument("key")
@_handle_load_errors
def get_meta(path: Path, key: str) -> None:
    doc = load_mdkv(path)
    val = doc.get_metadata(key)
    click.echo(val or "")


@main.command("search")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--pattern", required=True)
@click.option("--types", default="", help="comma-separated track types filter")
@click.option("--languages", default="", help="comma-separated languages filter")
@click.option("--case-insensitive", "-i", is_flag=True, help="case-insensitive search")
@click.option("--limit", type=int, default=None, help="Maximum number of matches to return")
@_handle_load_errors
def search_cmd(path: Path, pattern: str, types: str, languages: str, case_insensitive: bool,
               limit: int | None) -> None:
    """Search across tracks for a regex pattern."""
    doc = load_mdkv(path)
    tt = [t.strip() for t in types.split(",") if t.strip()] if types else None
    ll = [l.strip() for l in languages.split(",") if l.strip()] if languages else None
    try:
        matches = search_document(
            doc, pattern=pattern, track_types=tt, languages=ll,
            case_insensitive=case_insensitive, limit=limit,
        )
    except re.error as e:
        click.echo(f"ERROR: invalid regex pattern: {e}", err=True)
        raise SystemExit(1)
    click.echo(json.dumps([
        {
            "track_id": m.track_id,
            "track_type": m.track_type,
            "language": m.language,
            "start": m.start,
            "end": m.end,
            "extract": m.extract,
        }
        for m in matches
    ], indent=2))


@main.command()
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Output validation result as JSON")
@_handle_load_errors
def validate(path: Path, as_json: bool) -> None:  # type: ignore[override]
    """Validate the document and report issues."""
    doc = load_mdkv(path)
    try:
        issues = validate_document(doc)
        if as_json:
            click.echo(json.dumps({
                "ok": True,
                "issues": [
                    {"level": i.level, "message": i.message, "track_id": i.track_id}
                    for i in issues
                ],
            }, indent=2))
        else:
            for issue in issues:
                level_tag = "WARN" if issue.level == "WARN" else "ERROR"
                track_tag = f" [{issue.track_id}]" if issue.track_id else ""
                click.echo(f"{level_tag}{track_tag}: {issue.message}")
            if not issues:
                click.echo("OK")
    except ValidationError as e:
        if as_json:
            click.echo(json.dumps({"ok": False, "error": str(e)}, indent=2))
        else:
            click.echo(f"ERROR: {e}")
        raise SystemExit(1)


@main.command()
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--html", "as_html", is_flag=True, help="Export HTML instead of Markdown")
@click.option("--types", default=None, help="Comma-separated track types to include (HTML and Markdown)")
@click.option("--out-dir", type=click.Path(file_okay=False, path_type=Path), default=None,
              help="Export tracks as individual files to this directory")
@click.option("--metadata-header", is_flag=True, default=False, help="Include YAML frontmatter in Markdown output")
@click.option("--format", "fmt", type=click.Choice(["markdown", "html", "json", "pdf", "epub", "docx"]), default=None,
              help="Output format (overrides --html; 'json' exports full document as JSON; pdf/epub/docx require pandoc)")
@_handle_load_errors
def export(path: Path, as_html: bool, types: str | None, out_dir: Path | None,
           metadata_header: bool, fmt: str | None) -> None:
    """Export document to Markdown, HTML, JSON, PDF, EPUB, DOCX, or individual files."""
    doc = load_mdkv(path)
    include = [t.strip() for t in types.split(",") if t.strip()] if types else None
    if out_dir:
        written = export_to_files(doc, out_dir, include_track_types=include)
        click.echo(json.dumps({"files": [str(p) for p in written]}, indent=2))
    elif fmt == "json":
        data = doc.to_dict()
        if include is not None:
            data["tracks"] = [t for t in data["tracks"] if t["track_type"] in include]
        click.echo(json.dumps(data, indent=2))
    elif fmt in ("pdf", "epub", "docx"):
        from mdkv.services.pandoc_export import to_pdf, to_epub, to_docx
        out = path.with_suffix(f".{fmt}")
        try:
            if fmt == "pdf":
                to_pdf(doc, out, include_track_types=include, metadata_header=True)
            elif fmt == "epub":
                to_epub(doc, out, include_track_types=include, metadata_header=True)
            else:
                to_docx(doc, out, include_track_types=include, metadata_header=True)
        except FileNotFoundError as e:
            click.echo(f"ERROR: {e}", err=True)
            raise SystemExit(1)
        except Exception as e:
            click.echo(f"ERROR: pandoc conversion failed: {e}", err=True)
            raise SystemExit(1)
        click.echo(str(out))
    elif fmt == "html" or (fmt is None and as_html):
        click.echo(to_html(doc, include_track_types=include, metadata_header=metadata_header))
    else:
        click.echo(to_markdown(doc, include_track_types=include, metadata_header=metadata_header))


@main.command("import")
@click.argument("input_file", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), required=True)
@click.option("--title", required=True)
@click.option("--author", multiple=True, required=True)
@click.option("--track-id", default="primary")
@click.option("--track-type", default="primary")
@click.option("--language", default="en")
@_handle_load_errors
def import_cmd(
    input_file: Path,
    out: Path,
    title: str,
    author: list[str],
    track_id: str,
    track_type: str,
    language: str,
) -> None:
    """Import a Markdown file into a new .mdkv document."""
    content = Path(input_file).read_text(encoding="utf-8")
    doc = MDKVDocument(
        title=title,
        authors=list(author),
        created=datetime.now(timezone.utc),
    )
    doc.add_track(Track(
        track_id=track_id,
        track_type=track_type,
        language=language,
        path=f"tracks/{track_id}.md",
        content=content,
    ))
    save_mdkv(doc, out)
    click.echo(f"Imported {input_file} → {out}")


@main.command("diff")
@click.argument("path_a", type=click.Path(dir_okay=False, path_type=Path))
@click.argument("path_b", type=click.Path(dir_okay=False, path_type=Path))
@_handle_load_errors
def diff_cmd(path_a: Path, path_b: Path) -> None:
    """Compare two .mdkv documents and report differences."""
    doc_a = load_mdkv(path_a)
    doc_b = load_mdkv(path_b)
    result = diff_documents(doc_a, doc_b)
    if not result.has_changes:
        click.echo("No differences found.")
    else:
        click.echo(json.dumps(result.to_dict(), indent=2))


@main.command("stats")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@_handle_load_errors
def stats_cmd(path: Path) -> None:
    """Show statistics about an .mdkv document."""
    doc = load_mdkv(path)
    stats = compute_stats(doc)
    click.echo(json.dumps(stats.to_dict(), indent=2))


@main.command("history")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--id", "track_id", required=True, help="Track ID to show history for")
@_handle_load_errors
def history_cmd(path: Path, track_id: str) -> None:
    """Show revision history for a track (from revision tracks)."""
    doc = load_mdkv(path)
    # History for a track is the set of revision tracks whose track_id matches.
    revisions = [
        t for t in doc.tracks.values()
        if t.track_type == "revision" and t.track_id == track_id
    ]
    if not revisions:
        click.echo(f"No revision tracks found for '{track_id}'.")
        return
    # Output revision contents as JSON
    click.echo(json.dumps([
        {"track_id": t.track_id, "content_preview": t.content[:200]}
        for t in revisions
    ], indent=2))


@main.command("save-incremental")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@_handle_load_errors
def save_incremental_cmd(path: Path) -> None:
    """Save only changed tracks (incremental mode)."""
    from mdkv.storage.io import save_mdkv_incremental
    doc = load_mdkv(path)
    result = save_mdkv_incremental(doc, path)
    if result:
        click.echo("Saved (incremental)")
    else:
        click.echo("Saved (full fallback)")


@main.command("gui")
@click.option("--path", type=click.Path(dir_okay=False, path_type=Path), required=False)
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000)
def gui_cmd(path: Path | None, host: str, port: int) -> None:
    """Launch local MDKV GUI web app."""
    run_gui(host=host, port=port, path=str(path) if path else None)


@main.command("completions")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completions_cmd(shell: str) -> None:
    """Generate shell completion scripts."""
    env_var = "_MDKV_COMPLETE"
    click.echo(f"# Add this to your shell config (e.g. ~/.{shell}rc):")
    click.echo(f'# eval "$(_MDKV_COMPLETE={shell}_source mdkv)"')
    click.echo(f"# Or save this script and source it:")
    click.echo("")
    # Use click's built-in shell completion
    import click.shell_completion as cs
    # Click generates completions dynamically; we output the instruction
    click.echo(f'export _MDKV_COMPLETE={shell}_source')
    click.echo(f'eval "$(mdkv --generate-completions {shell} 2>/dev/null || true)"')


@main.group("batch")
def batch_group() -> None:
    """Run operations across multiple .mdkv files."""


@batch_group.command("validate")
@click.argument("paths", nargs=-1, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_load_errors
def batch_validate(paths: tuple[Path, ...], as_json: bool) -> None:
    """Validate multiple documents."""
    results = []
    for p in paths:
        try:
            doc = load_mdkv(p)
            issues = validate_document(doc)
            results.append({"path": str(p), "ok": True, "issues": len(issues)})
        except Exception as e:
            results.append({"path": str(p), "ok": False, "error": str(e)})
    if as_json:
        click.echo(json.dumps(results, indent=2))
    else:
        for r in results:
            status = "OK" if r["ok"] else "FAIL"
            click.echo(f"{status}  {r['path']}")


@batch_group.command("stats")
@click.argument("paths", nargs=-1, type=click.Path(dir_okay=False, path_type=Path))
@_handle_load_errors
def batch_stats(paths: tuple[Path, ...]) -> None:
    """Show stats for multiple documents."""
    results = []
    for p in paths:
        try:
            doc = load_mdkv(p)
            stats = compute_stats(doc)
            results.append(stats.to_dict())
        except Exception as e:
            results.append({"path": str(p), "error": str(e)})
    click.echo(json.dumps(results, indent=2))


@main.command("license")
def license_cmd() -> None:
    """Show license information."""
    click.echo(
        "MDKV is licensed under the Apache License, Version 2.0 (Apache-2.0).\n"
        "See the LICENSE file in the repository or distribution for full text."
    )
