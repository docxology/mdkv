"""Import a Markdown file as a new .mdkv document, then validate it."""
from datetime import UTC, datetime
from pathlib import Path

from mdkv import MDKVDocument, Track, save_mdkv, validate_document


def main() -> None:
    # write a sample markdown file
    md_path = Path("sample_input.md")
    md_path.write_text("# Sample\n\nThis is imported content.", encoding="utf-8")

    # create a new .mdkv with the imported content as primary track
    doc = MDKVDocument(
        title="Imported Sample",
        authors=["Import Script"],
        created=datetime.now(UTC),
    )
    doc.add_track(Track(
        track_id="primary",
        track_type="primary",
        language="en",
        path="tracks/primary.md",
        content=md_path.read_text(encoding="utf-8"),
    ))
    out = Path("imported.mdkv")
    save_mdkv(doc, out)
    print(f"Imported {md_path} → {out}")
    validate_document(doc)
    print("Validation: OK")
    md_path.unlink()


if __name__ == "__main__":
    main()
