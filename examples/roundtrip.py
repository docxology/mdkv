from datetime import datetime
from pathlib import Path

from mdkv.model import MDKVDocument, Track
from mdkv.io import save_mdkv, load_mdkv


def main() -> None:
    path = Path("roundtrip.mdkv")
    doc = MDKVDocument(title="Roundtrip", authors=["A"], created=datetime.utcnow())
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "Roundtrip"))
    save_mdkv(doc, path)
    loaded = load_mdkv(path)
    print(f"Loaded title: {loaded.title}; tracks: {list(loaded.tracks)}")


if __name__ == "__main__":
    main()
