from pathlib import Path

from mdkv.export import to_html
from mdkv.io import load_mdkv


def main() -> None:
    path = Path("example.mdkv")
    doc = load_mdkv(path)
    html = to_html(doc)
    Path("example.html").write_text(html, encoding="utf-8")
    print("Wrote example.html")


if __name__ == "__main__":
    main()
