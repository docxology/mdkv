from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for autodoc
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

project = "MDKV"
author = "MDKV Authors"
current_year = datetime.utcnow().year
copyright = f"{current_year}, {author}"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx_autodoc_typehints",
]

myst_enable_extensions = ["colon_fence", "deflist"]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

html_theme = "alabaster"
html_static_path = ["_static"]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

autosectionlabel_prefix_document = True
