from .diff import DiffResult, diff_documents
from .export import export_to_files, to_html, to_markdown
from .pandoc_export import to_docx, to_epub, to_pdf
from .search import SearchMatch, search_document
from .stats import DocumentStats, compute_stats

__all__ = [
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
]
