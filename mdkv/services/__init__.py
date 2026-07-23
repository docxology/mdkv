from .search import search_document, SearchMatch
from .export import to_markdown, to_html, export_to_files
from .diff import diff_documents, DiffResult
from .stats import compute_stats, DocumentStats
from .pandoc_export import to_pdf, to_epub, to_docx

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
