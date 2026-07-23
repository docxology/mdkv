"""Demonstrate diff_documents() and compute_stats() together."""
from datetime import datetime, timezone
from pathlib import Path

from mdkv import MDKVDocument, Track, save_mdkv, load_mdkv, diff_documents, compute_stats


def main() -> None:
    base = Path("v1.mdkv")
    other = Path("v2.mdkv")

    doc_a = MDKVDocument(title="V1", authors=["A"], created=datetime.now(timezone.utc), version="1.0.0")
    doc_a.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# V1\n\nOriginal"))
    doc_a.add_track(Track("notes", "commentary", None, "tracks/notes.md", "Note"))
    save_mdkv(doc_a, base)

    doc_b = MDKVDocument(title="V2", authors=["A"], created=datetime.now(timezone.utc), version="2.0.0")
    doc_b.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# V2\n\nModified"))
    doc_b.add_track(Track("extra", "commentary", None, "tracks/extra.md", "Extra"))
    save_mdkv(doc_b, other)

    a = load_mdkv(base)
    b = load_mdkv(other)

    # Diff
    result = diff_documents(a, b)
    print("=== Diff ===")
    if result.has_changes:
        print(f"  Title: {result.title_changed}")
        print(f"  Version: {result.version_changed}")
        print(f"  Added: {result.tracks_added}")
        print(f"  Removed: {result.tracks_removed}")
        print(f"  Modified: {result.tracks_modified}")
    else:
        print("  No differences.")

    # Stats
    print("\n=== Stats (V1) ===")
    stats = compute_stats(a)
    print(f"  Tracks: {stats.track_count}")
    print(f"  Types: {stats.tracks_by_type}")
    print(f"  Chars: {stats.total_characters}")
    print(f"  Lines: {stats.total_lines}")

    print("\n=== Stats (V2) ===")
    stats2 = compute_stats(b)
    print(f"  Tracks: {stats2.track_count}")
    print(f"  Types: {stats2.tracks_by_type}")
    print(f"  Chars: {stats2.total_characters}")
    print(f"  Lines: {stats2.total_lines}")

    base.unlink()
    other.unlink()


if __name__ == "__main__":
    main()
