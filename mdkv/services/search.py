from __future__ import annotations

"""Search utilities for MDKV documents.

Provides regex-based search across tracks with optional filtering by
track type and language.  Each ``SearchMatch`` carries enough context
to identify the hit without re-reading the document.
"""

import asyncio
import re
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass

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
    language: str | None
    start: int
    end: int
    extract: str


def search_document(
    doc: MDKVDocument,
    pattern: str,
    flags: int = 0,
    track_types: Iterable[str] | None = None,
    languages: Iterable[str] | None = None,
    case_insensitive: bool = False,
    limit: int | None = None,
) -> list[SearchMatch]:
    """Search ``doc`` for ``pattern``.

    - ``track_types``: optional subset filter (e.g. ``["primary", "commentary"]``)
    - ``languages``: optional subset filter (e.g. ``["en", "es"]``)
    - ``case_insensitive``: if ``True``, adds ``re.IGNORECASE`` to flags
    - ``limit``: if provided, return at most this many matches

    Returns a list of ``SearchMatch`` with small surrounding extracts.
    """
    if case_insensitive:
        flags |= re.IGNORECASE
    regex = re.compile(pattern, flags)
    results: list[SearchMatch] = []
    allowed_types = set(track_types) if track_types else None
    allowed_langs = set(languages) if languages else None
    for track_id, track in doc.tracks.items():
        if limit is not None and len(results) >= limit:
            break
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
            if limit is not None and len(results) >= limit:
                break
    return results


async def search_document_async(
    doc: MDKVDocument,
    pattern: str,
    flags: int = 0,
    track_types: Iterable[str] | None = None,
    languages: Iterable[str] | None = None,
    case_insensitive: bool = False,
    limit: int | None = None,
    offset: int = 0,
) -> AsyncIterator[SearchMatch]:
    """Async generator that yields ``SearchMatch`` results.

    Supports ``limit`` and ``offset`` for pagination.  Yields matches
    one at a time, allowing the caller to process them incrementally
    without waiting for the full result set.
    """
    if case_insensitive:
        flags |= re.IGNORECASE
    regex = re.compile(pattern, flags)
    allowed_types = set(track_types) if track_types else None
    allowed_langs = set(languages) if languages else None
    yielded = 0
    skipped = 0
    for track_id, track in doc.tracks.items():
        if limit is not None and yielded >= limit:
            break
        if allowed_types is not None and track.track_type not in allowed_types:
            continue
        if allowed_langs is not None and track.language not in allowed_langs:
            continue
        for m in regex.finditer(track.content):
            start, end = m.span()
            if skipped < offset:
                skipped += 1
                continue
            window_start = max(0, start - 20)
            window_end = min(len(track.content), end + 20)
            extract = track.content[window_start:window_end]
            yield SearchMatch(
                track_id=track_id,
                track_type=track.track_type,
                language=track.language,
                start=start,
                end=end,
                extract=extract,
            )
            yielded += 1
            if limit is not None and yielded >= limit:
                break
            # Yield control to the event loop periodically
            if yielded % 100 == 0:
                await asyncio.sleep(0)
