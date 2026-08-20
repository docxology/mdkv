from .core import (
    MDKVDocument,
    Track,
    ValidationError,
    ValidationIssue,
    allowed_track_types,
    validate_document,
    validate_track,
)
from .core.history import TrackHistory, TrackVersion
from .core.registry import TrackTypeRegistry, get_registry, register_track_type
from .services import (
    DiffResult,
    DocumentStats,
    SearchMatch,
    compute_stats,
    diff_documents,
    export_to_files,
    search_document,
    to_docx,
    to_epub,
    to_html,
    to_markdown,
    to_pdf,
)
from .services.search import search_document_async
from .storage import MDKVFormatError, MDKVManifestModel, TrackManifestModel, load_mdkv, save_mdkv
from .storage.io import save_mdkv_incremental

__license__ = "Apache-2.0"
__version__ = "0.11.0"

__all__ = [
    "core",
    "services",
    "storage",
    "cli",
    # surfaced API — core
    "MDKVDocument",
    "Track",
    "allowed_track_types",
    "ValidationError",
    "validate_document",
    "validate_track",
    "ValidationIssue",
    # history
    "TrackHistory",
    "TrackVersion",
    # registry
    "TrackTypeRegistry",
    "register_track_type",
    "get_registry",
    # services
    "search_document",
    "search_document_async",
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
    # storage
    "save_mdkv",
    "save_mdkv_incremental",
    "load_mdkv",
    "MDKVFormatError",
    "MDKVManifestModel",
    "TrackManifestModel",
]
