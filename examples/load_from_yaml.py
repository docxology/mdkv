from __future__ import annotations

from pathlib import Path

import yaml

from mdkv.library import build_document_from_definition
from mdkv.storage import save_mdkv


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Build .mdkv from YAML definition")
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()

    data = yaml.safe_load(Path(args.input).read_text(encoding="utf-8"))
    doc = build_document_from_definition(data)
    save_mdkv(doc, args.output)
    print(f"Wrote {args.output}")


