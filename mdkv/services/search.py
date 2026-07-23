from __future__ import annotations

"""Search utilities for MDKV documents.

Provides regex-based search across tracks with optional filtering by
track type and language.  Each ``SearchMatch`` carries enough context
to identify the hit without re-reading the document.
"""

import re
from dataclasses import dataclass
from typing import List, Iterable, Optional

from mdkv.core.model import MDKVDocument


@dataclass
class SearchMatch:
    """A single regex match within a track.

    Fields:
    - ``track_id``: the track containing the match
    - ``track_type``: type of the track (primary, commentary, ...)
    - ``language``: language code of the track, or ``None``
    - ``start``: character offset of the match start
    - ``end``: character offset of the match end
    - ``extract``: a small window of surrounding text for context
    """

    track_id: str
    track_type: str
    language: Optional[str]
    start: int
    end: int
    extract: str


def search_document(
    doc: MDKVDocument,
    pattern: str,
    flags: int = 0,
    track_types: Optional[Iterable[str]] = None,
    languages: Optional[Iterable[str]] = None,
    case_insensitive: bool = False,
) -> List[SearchMatch]:
    """Search ``doc`` for ``pattern``.

    - ``track_types``: optional subset filter (e.g. ``["primary", "commentary"]``)
    - ``languages``: optional subset filter (e.g. ``["en", "es"]``)
    - ``case_insensitive``: if ``True``, adds ``re.IGNORECASE`` to flags
    Returns a list of ``SearchMatch`` with small surrounding extracts.
    """
    if case_insensitive:
        flags |= re.IGNORECASE
    regex = re.compile(pattern, flags)
    results: List[SearchMatch] = []
    allowed_types = set(track_types) if track_types else None
    allowed_langs = set(languages) if languages else None
    for track_id, track in doc.tracks.items():
        if allowed_types is not None and track.track_type not in allowed_types:
            continue
        if allowed_langs is not None and track.language not in allowed_langs:
            continue
        for m in regex.finditer(track.content):
            start, end = m.span()
            window_start = max(0, start - 20)
            window_end = min(len(track.content), end + 20)
            extract = track.content[window_start:window_end]
            results.append(
                SearchMatch(
                    track_id=track_id,
                    track_type=track.track_type,
                    language=track.language,
                    start=start,
                    end=end,
                    extract=extract,
                )
            )
    return results
