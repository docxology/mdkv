from pathlib import Path

from mdkv.io import load_mdkv
from mdkv.export import to_html


def main() -> None:
    path = Path("example.mdkv")
    doc = load_mdkv(path)
    html = to_html(doc)
    Path("example.html").write_text(html, encoding="utf-8")
    print("Wrote example.html")


if __name__ == "__main__":
    main()
