from .core import (
    MDKVDocument,
    Track,
    allowed_track_types,
    ValidationError,
    validate_document,
    validate_track,
    ValidationIssue,
)
from .core.history import TrackHistory, TrackVersion
from .core.registry import TrackTypeRegistry, register_track_type, get_registry
from .services import (
    search_document, SearchMatch,
    to_markdown, to_html, export_to_files,
    diff_documents, DiffResult,
    compute_stats, DocumentStats,
    to_pdf, to_epub, to_docx,
)
from .services.search import search_document_async
from .storage import save_mdkv, load_mdkv, MDKVFormatError
from .storage.io import save_mdkv_incremental

__license__ = "Apache-2.0"
__version__ = "0.8.0"

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
    "to_pdf",
    "to_epub",
    "to_docx",
    "save_mdkv",
    "load_mdkv",
    "MDKVFormatError",
]
