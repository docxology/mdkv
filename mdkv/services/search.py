from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Iterable, Optional

from mdkv.core.model import MDKVDocument


@dataclass
class SearchMatch:
    track_id: str
    start: int
    end: int
    extract: str


def search_document(
    doc: MDKVDocument,
    pattern: str,
    flags: int = 0,
    track_types: Optional[Iterable[str]] = None,
    languages: Optional[Iterable[str]] = None,
) -> List[SearchMatch]:
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
            results.append(SearchMatch(track_id=track_id, start=start, end=end, extract=extract))
    return results


