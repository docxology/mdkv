"""Diff two .mdkv documents and print the changes."""
from pathlib import Path

from mdkv import MDKVDocument, Track, save_mdkv, load_mdkv


def main() -> None:
    from datetime import datetime, timezone
    # create two documents
    base = Path("v1.mdkv")
    other = Path("v2.mdkv")

    doc_a = MDKVDocument(title="Version 1", authors=["A"], created=datetime.now(timezone.utc))
    doc_a.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# V1\n\nOriginal content"))
    save_mdkv(doc_a, base)

    doc_b = MDKVDocument(title="Version 2", authors=["A"], created=datetime.now(timezone.utc))
    doc_b.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# V2\n\nModified content"))
    doc_b.add_track(Track("notes", "commentary", None, "tracks/notes.md", "# Notes"))
    save_mdkv(doc_b, other)

    # load and diff
    a = load_mdkv(base)
    b = load_mdkv(other)

    print(f"Diff: {base} vs {other}")
    print(f"  title:    {'CHANGED' if a.title != b.title else 'same'}  ({a.title!r} → {b.title!r})")
    print(f"  tracks:   added={sorted(set(b.tracks) - set(a.tracks))}, removed={sorted(set(a.tracks) - set(b.tracks))}")
    for tid in sorted(set(a.tracks) & set(b.tracks)):
        if a.tracks[tid].content != b.tracks[tid].content:
            print(f"  modified: {tid}")

    base.unlink()
    other.unlink()


if __name__ == "__main__":
    main()
