#!/usr/bin/env python3
"""Stage the authored graphical abstract and its render metadata."""

import json
from pathlib import Path
import shutil


def main() -> None:
    """Copy the canonical figure and write the Template figure registry."""
    project = Path(__file__).resolve().parents[1]
    filename = "mdkv-graphical-abstract.png"
    figures = project / "output" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    source = project / "docs" / "manuscript" / "figures" / filename
    shutil.copyfile(source, figures / filename)
    registry = {
        "figures": [
            {
                "label": "fig:mdkv-graphical-abstract",
                "filename": filename,
                "caption": "One canonical manuscript packaged as an MDKV container and composed into audience views.",
                "alt_text": (
                    "One Markdown source flows through a multitrack ZIP and YAML container "
                    "into reader, reviewer, and archive views."
                ),
            },
        ],
    }
    (figures / "figure_registry.json").write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
