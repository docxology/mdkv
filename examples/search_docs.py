from pathlib import Path

from mdkv.services.search import search_document
from mdkv.storage import load_mdkv


def main() -> None:
    doc = load_mdkv(Path("example.mdkv"))
    matches = search_document(doc, pattern="Hello|Note")
    for m in matches:
        print(f"[{m.track_id}] {m.extract}")


if __name__ == "__main__":
    main()
