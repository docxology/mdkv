from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import click

from mdkv.storage import load_mdkv, save_mdkv
from mdkv.core.model import MDKVDocument, Track
from mdkv.core.validate import validate_document
from mdkv.core.errors import ValidationError
from mdkv.services.export import to_markdown, to_html
from mdkv.services.search import search_document
from mdkv.gui import run as run_gui
from mdkv import __version__, __license__


@click.group()
@click.version_option(version=__version__, prog_name="mdkv")
def main() -> None:
    """MDKV command-line interface."""


@main.command()
@click.option("--title", required=True)
@click.option("--author", multiple=True, required=True)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), required=True)
def init(title: str, author: list[str], out: Path) -> None:
    doc = MDKVDocument(title=title, authors=list(author), created=datetime.utcnow())
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# New Document\n\nStart here."))
    save_mdkv(doc, out)
    click.echo(f"Created {out}")


@main.command()
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
def info(path: Path) -> None:
    doc = load_mdkv(path)
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
@click.option("--content", required=True)
def add_track_cmd(path: Path, track_id: str, track_type: str, language: str | None, content: str) -> None:
    doc = load_mdkv(path)
    doc.add_track(Track(track_id, track_type, language if language else None, f"tracks/{track_id}.md", content))
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("export-tracks")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--types", required=True, help="Comma-separated track types to include")
def export_tracks(path: Path, types: str) -> None:
    doc = load_mdkv(path)
    include = [t.strip() for t in types.split(",") if t.strip()]
    click.echo(to_markdown(doc, include_track_types=include))


@main.command("rename-track")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--old-id", required=True)
@click.option("--new-id", required=True)
def rename_track_cmd(path: Path, old_id: str, new_id: str) -> None:
    doc = load_mdkv(path)
    doc.rename_track(old_id, new_id)
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("update-track")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--id", "track_id", required=True)
@click.option("--content", required=True)
def update_track_cmd(path: Path, track_id: str, content: str) -> None:
    doc = load_mdkv(path)
    doc.update_track_content(track_id, content)
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("set-meta")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.argument("key")
@click.argument("value")
def set_meta(path: Path, key: str, value: str) -> None:
    doc = load_mdkv(path)
    doc.set_metadata(key, value)
    save_mdkv(doc, path)
    click.echo("OK")


@main.command("get-meta")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.argument("key")
def get_meta(path: Path, key: str) -> None:
    doc = load_mdkv(path)
    val = doc.get_metadata(key)
    click.echo(val or "")


@main.command("search")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--pattern", required=True)
@click.option("--types", default="", help="comma-separated track types filter")
@click.option("--languages", default="", help="comma-separated languages filter")
def search_cmd(path: Path, pattern: str, types: str, languages: str) -> None:
    doc = load_mdkv(path)
    tt = [t.strip() for t in types.split(",") if t.strip()] if types else None
    ll = [l.strip() for l in languages.split(",") if l.strip()] if languages else None
    matches = search_document(doc, pattern=pattern, track_types=tt, languages=ll)
    click.echo(json.dumps([
        {"track_id": m.track_id, "start": m.start, "end": m.end, "extract": m.extract}
        for m in matches
    ], indent=2))


@main.command()
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
def validate(path: Path) -> None:  # type: ignore[override]
    doc = load_mdkv(path)
    try:
        validate_document(doc)
        click.echo("OK")
    except ValidationError as e:
        click.echo(f"ERROR: {e}")
        raise SystemExit(1)


@main.command()
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--html", "as_html", is_flag=True, help="Export HTML instead of Markdown")
def export(path: Path, as_html: bool) -> None:
    doc = load_mdkv(path)
    if as_html:
        click.echo(to_html(doc))
    else:
        click.echo(to_markdown(doc))


@main.command("gui")
@click.option("--path", type=click.Path(dir_okay=False, path_type=Path), required=False)
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000)
def gui_cmd(path: Path | None, host: str, port: int) -> None:
    """Launch local MDKV GUI web app."""
    run_gui(host=host, port=port, path=str(path) if path else None)


@main.command("license")
def license_cmd() -> None:
    """Show license information."""
    click.echo(
        "MDKV is licensed under the Apache License, Version 2.0 (Apache-2.0).\n"
        "See the LICENSE file in the repository or distribution for full text."
    )

