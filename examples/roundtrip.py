from datetime import UTC, datetime
from pathlib import Path

from mdkv.io import load_mdkv, save_mdkv
from mdkv.model import MDKVDocument, Track


def main() -> None:
    path = Path("roundtrip.mdkv")
    doc = MDKVDocument(title="Roundtrip", authors=["A"], created=datetime.now(UTC))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "Roundtrip"))
    save_mdkv(doc, path)
    loaded = load_mdkv(path)
    print(f"Loaded title: {loaded.title}; tracks: {list(loaded.tracks)}")


if __name__ == "__main__":
    main()
