from .core import (
    MDKVDocument,
    Track,
    allowed_track_types,
    ValidationError,
    validate_document,
    validate_track,
    ValidationIssue,
)
from .services import (
    search_document, SearchMatch,
    to_markdown, to_html, export_to_files,
    diff_documents, DiffResult,
    compute_stats, DocumentStats,
)
from .storage import save_mdkv, load_mdkv, MDKVFormatError

__license__ = "Apache-2.0"
__version__ = "0.6.0"

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
    "validate_track",
    "ValidationIssue",
    "search_document",
    "SearchMatch",
    "to_markdown",
    "to_html",
    "export_to_files",
    "diff_documents",
    "DiffResult",
    "compute_stats",
    "DocumentStats",
    "save_mdkv",
    "load_mdkv",
    "MDKVFormatError",
]
