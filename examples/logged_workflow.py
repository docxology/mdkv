from datetime import UTC, datetime
from pathlib import Path

from mdkv.common import configure_logging, get_logger
from mdkv.core.model import MDKVDocument, Track
from mdkv.core.validate import validate_document
from mdkv.services.export import export_to_files, to_html, to_markdown
from mdkv.services.search import search_document
from mdkv.storage import load_mdkv, save_mdkv


def main() -> None:
    configure_logging()
    log = get_logger(__name__)

    workdir = Path("workflow_out")
    workdir.mkdir(exist_ok=True)

    # create
    doc = MDKVDocument(title="Workflow", authors=["User"], created=datetime.now(UTC))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Title\n\nHello world"))
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "This is a note."))
    path = workdir / "workflow.mdkv"
    save_mdkv(doc, path)
    log.info("Saved MDKV to %s", path)

    # validate
    validate_document(doc)
    log.info("Validation passed")

    # export markdown and html
    md = to_markdown(doc)
    (workdir / "combined.md").write_text(md, encoding="utf-8")
    (workdir / "primary.html").write_text(to_html(doc), encoding="utf-8")
    log.info("Exported markdown and html")

    # export tracks to files
    export_to_files(doc, workdir / "tracks", include_track_types=["primary", "commentary"])
    log.info("Exported tracks to files")

    # search
    matches = search_document(doc, pattern="world|note")
    (workdir / "search.json").write_text(
        "\n".join(f"{m.track_id} {m.extract}" for m in matches), encoding="utf-8"
    )
    log.info("Saved search results (%d matches)", len(matches))

    # reload and show info
    loaded = load_mdkv(path)
    log.info("Reloaded document with %d tracks", len(loaded.tracks))


if __name__ == "__main__":
    main()
