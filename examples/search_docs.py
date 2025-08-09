from pathlib import Path

from mdkv.io import load_mdkv
from mdkv.search import search_document


def main() -> None:
    doc = load_mdkv(Path("example.mdkv"))
    matches = search_document(doc, pattern="Hello|Note")
    for m in matches:
        print(f"[{m.track_id}] {m.extract}")


if __name__ == "__main__":
    main()
