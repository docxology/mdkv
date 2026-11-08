from pathlib import Path

from mdkv.services.export import to_html
from mdkv.storage import load_mdkv


def main() -> None:
    path = Path("example.mdkv")
    doc = load_mdkv(path)
    html = to_html(doc)
    with Path("example.html").open("x", encoding="utf-8") as output:
        output.write(html)
    print("Wrote example.html")


if __name__ == "__main__":
    main()
