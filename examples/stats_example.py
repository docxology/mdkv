"""Print statistics about an .mdkv document."""
from datetime import datetime, timezone
from pathlib import Path

from mdkv import MDKVDocument, Track, save_mdkv, load_mdkv


def main() -> None:
    # create a demo document
    doc = MDKVDocument(
        title="Stats Demo",
        authors=["DAF"],
        created=datetime.now(timezone.utc),
        version="1.0.0",
    )
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Stats\n\nSome content here.\nWith multiple lines."))
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "# Notes\n\nA note."))
    doc.add_track(Track("code1", "code", "python", "tracks/code1.md", "```python\nprint('hello')\n```"))
    doc.set_metadata("project", "demo")
    doc.set_metadata("year", "2025")

    out = Path("stats_demo.mdkv")
    save_mdkv(doc, out)
    loaded = load_mdkv(out)

    print(f"Title:    {loaded.title}")
    print(f"Version:  {loaded.version}")
    print(f"Tracks:   {len(loaded.tracks)}")
    print(f"By type:  {loaded.count_tracks_by_type()}")
    print(f"Languages: {loaded.list_languages()}")
    print(f"Metadata keys: {sorted(loaded.metadata)}")
    total_chars = sum(len(t.content) for t in loaded.tracks.values())
    total_lines = sum(t.content.count('\n') + 1 for t in loaded.tracks.values())
    print(f"Total chars: {total_chars}")
    print(f"Total lines: {total_lines}")

    # demonstrate to_dict / from_dict roundtrip
    d = loaded.to_dict()
    restored = MDKVDocument.from_dict(d)
    assert restored.title == loaded.title
    assert set(restored.tracks) == set(loaded.tracks)
    print("to_dict/from_dict roundtrip: OK")

    out.unlink()


if __name__ == "__main__":
    main()
