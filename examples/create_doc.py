from datetime import datetime
from pathlib import Path

from mdkv.model import MDKVDocument, Track
from mdkv.io import save_mdkv


def main() -> None:
    out = Path("example.mdkv")
    doc = MDKVDocument(title="Example", authors=["Author"], created=datetime.utcnow())
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Example\n\nHello, see [link](https://example.org)."))
    doc.add_track(Track("translation-fr", "translation", "fr", "tracks/translation-fr.md", "Bonjour"))
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "Note."))
    doc.add_track(Track("refs", "reference", None, "tracks/refs.md", "- https://example.org"))
    save_mdkv(doc, out)
    print(f"Wrote {out.resolve()}")


if __name__ == "__main__":
    main()
