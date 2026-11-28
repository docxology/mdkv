from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

from sphinx import version_info as sphinx_version_info

# Add project root to path for autodoc
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

project = "MDKV"
author = "MDKV Authors"
current_year = datetime.now(UTC).year
copyright = f"{current_year}, {author}"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
]

myst_enable_extensions = ["colon_fence", "deflist"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "README.md", "AGENTS.md", "manuscript/**", "early_design.md", "TODO.md"]

html_theme = "alabaster"
html_static_path = ["_static"]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

autosectionlabel_prefix_document = True

# Native annotations are complete. Sphinx 9.0 still mutates inherited
# Pydantic annotations with type-comment enrichment disabled. Use its
# supported class-based loader to keep later FastAPI imports working.
autodoc_use_type_comments = False
if sphinx_version_info[:2] == (9, 0):
    autodoc_use_legacy_class_based = True
autodoc_typehints = "description"
