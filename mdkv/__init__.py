from .core import (
    MDKVDocument,
    Track,
    allowed_track_types,
    ValidationError,
    validate_document,
    ValidationIssue,
)
from .services import search_document, SearchMatch, to_markdown, to_html, export_to_files
from .storage import save_mdkv, load_mdkv

__license__ = "Apache-2.0"
__version__ = "0.1.0"

__all__ = [
    "core",
    "services",
    "storage",
    "cli",
    # surfaced API
    "MDKVDocument",
    "Track",
    "allowed_track_types",
    "ValidationError",
    "validate_document",
    "ValidationIssue",
    "search_document",
    "SearchMatch",
    "to_markdown",
    "to_html",
    "export_to_files",
    "save_mdkv",
    "load_mdkv",
]


