from __future__ import annotations

"""Stdlib ``re`` search in a short-lived, supervised interpreter.

Each query gets five seconds to start and receive its filtered input, then one
second to compile and match. At most 10,000 results may be returned per query;
request a smaller page to search documents with more matches. Exceeding either
budget raises an explicit exception, never a silently truncated result.
"""

import asyncio
import json
import queue
import re
import subprocess
import sys
import threading
import time
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from typing import Any, cast

from mdkv.core.model import MDKVDocument

SEARCH_TIMEOUT_SECONDS = 1.0
SEARCH_STARTUP_TIMEOUT_SECONDS = 5.0
MAX_PATTERN_LENGTH = 16_384
MAX_SEARCH_RESULTS = 10_000

# Only this fixed program is executed. Neither document text nor patterns become
# Python source. Isolated mode avoids importing the application, __main__, or
# modules from the caller's working directory, including in GUI/pytest callers.
_SEARCH_WORKER = r'''
import json
import re
import sys
import time

protocol = sys.stdout
# Raw UTF-8 with surrogatepass also preserves adjacent surrogate code points;
# ASCII-escaped JSON would combine a surrogate pair and change Python offsets.
protocol.reconfigure(encoding="utf-8", errors="surrogatepass")
sys.stdin.reconfigure(encoding="utf-8", errors="surrogatepass")
sys.stdout = sys.stderr  # re.DEBUG must not corrupt the result protocol.

def send(message):
    protocol.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
    protocol.flush()

def search(request):
    pattern, flags, tracks, limit, offset, maximum = request
    compiled = re.compile(pattern, flags)
    results = []
    skipped = 0
    if limit == 0:
        return results
    for index, track in enumerate(tracks):
        for match in compiled.finditer(track[3]):
            if skipped < offset:
                skipped += 1
                continue
            if len(results) == maximum:
                raise ValueError("search exceeds the maximum of %d results; request a bounded page" % maximum)
            results.append((index, *match.span()))
            if limit is not None and len(results) == limit:
                return results
    return results

request = json.load(sys.stdin)
send(("ready", time.monotonic()))
try:
    results = search(request)
except re.error as exc:
    send(("syntax", exc.msg, exc.pattern, exc.pos))
except (ValueError, TypeError, OverflowError, RecursionError) as exc:
    send(("error", type(exc).__name__, str(exc)))
else:
    send(("results", results))
'''


@dataclass
class SearchMatch:
    """A match's track identity, character offsets and surrounding text."""

    track_id: str
    track_type: str
    language: str | None
    start: int
    end: int
    extract: str


class _SearchCancelled(Exception):
    """Internal signal: the async caller is waiting for child cleanup."""


def _receive(
    messages: queue.Queue[Any], deadline: float, cancelled: threading.Event,
    timeout_message: str,
) -> Any:
    while True:
        if cancelled.is_set():
            raise _SearchCancelled()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(timeout_message)
        try:
            message = messages.get(timeout=min(remaining, 0.05))
        except queue.Empty:
            continue
        if message[0] == "io_error":
            raise RuntimeError("search subprocess communication failed") from message[1]
        return message


def _run_worker(request: tuple[Any, ...], cancelled: threading.Event) -> list[list[int]]:
    if cancelled.is_set():
        raise _SearchCancelled()
    startup_deadline = time.monotonic() + SEARCH_STARTUP_TIMEOUT_SECONDS
    process = subprocess.Popen(
        [sys.executable, "-I", "-u", "-c", _SEARCH_WORKER],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="surrogatepass",
    )
    input_stream, output_stream = process.stdin, process.stdout
    assert input_stream is not None and output_stream is not None
    messages: queue.Queue[Any] = queue.Queue()
    threads: list[threading.Thread] = []

    def write_request() -> None:
        try:
            # Stream JSON rather than building another complete document-sized
            # payload. Only already-filtered track tuples cross the pipe.
            json.dump(request, input_stream, ensure_ascii=False, separators=(",", ":"))
        except Exception as exc:
            messages.put(("io_error", exc))
        finally:
            try:
                input_stream.close()
            except OSError:
                pass  # A terminated child may close its input mid-write.

    def read_messages() -> None:
        try:
            for line in output_stream:
                message = json.loads(line)
                messages.put(message)
                if message[0] != "ready":
                    return
            raise RuntimeError("search subprocess exited without a result")
        except Exception as exc:
            messages.put(("io_error", exc))

    try:
        for target in (write_request, read_messages):
            thread = threading.Thread(target=target, name=f"mdkv-search-{process.pid}")
            thread.start()
            threads.append(thread)
        ready = _receive(
            messages, startup_deadline, cancelled,
            "search exceeded the five-second subprocess startup deadline",
        )
        if ready[0] != "ready":
            raise RuntimeError("search subprocess did not acknowledge its input")
        # monotonic clocks share their reference across processes. Count from
        # the child's acknowledgement, not from when this thread is scheduled.
        response = _receive(
            messages, ready[1] + SEARCH_TIMEOUT_SECONDS, cancelled,
            "search exceeded the one-second matching deadline",
        )
        if response[0] == "syntax":
            raise re.error(response[1], response[2], response[3])
        if response[0] == "error" and response[1] == "RecursionError":
            raise ValueError("regex exceeds compiler nesting limits")
        if response[0] == "error" and response[1] == "OverflowError":
            raise ValueError("regex repetition exceeds compiler limits")
        if response[0] == "error":
            errors = {
                "ValueError": ValueError, "TypeError": TypeError,
            }
            raise errors[response[1]](response[2])
        if response[0] != "results":
            raise RuntimeError("search subprocess returned an invalid response")
        return cast(list[list[int]], response[1])
    finally:
        # This also runs for syntax errors, timeouts, and async cancellation.
        # Reap before joining pipe threads: terminating the sole writer/reader
        # closes the other pipe ends and releases blocked I/O on every platform.
        try:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        finally:
            for thread in threads:
                thread.join()
            input_stream.close()
            output_stream.close()


def _search(
    doc: MDKVDocument, pattern: str, flags: int, track_types: Iterable[str] | None,
    languages: Iterable[str] | None, case_insensitive: bool, limit: int | None,
    offset: int, cancelled: threading.Event,
) -> list[SearchMatch]:
    if limit is not None and (not isinstance(limit, int) or limit < 0):
        raise ValueError("search limit must be a nonnegative integer")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("search offset must be a nonnegative integer")
    if limit is not None and limit > MAX_SEARCH_RESULTS:
        raise ValueError(f"search limit exceeds the maximum of {MAX_SEARCH_RESULTS} results")
    if len(pattern) > MAX_PATTERN_LENGTH:
        raise ValueError(f"search pattern exceeds {MAX_PATTERN_LENGTH} characters")
    if case_insensitive:
        flags |= re.IGNORECASE
    allowed_types = set(track_types) if track_types is not None else None
    allowed_langs = set(languages) if languages is not None else None
    tracks = [
        (track_id, track.track_type, track.language, track.content)
        for track_id, track in doc.tracks.items()
        if (allowed_types is None or track.track_type in allowed_types)
        and (allowed_langs is None or track.language in allowed_langs)
    ]
    rows = _run_worker((pattern, flags, tracks, limit, offset, MAX_SEARCH_RESULTS), cancelled)
    results = []
    for index, start, end in rows:
        track_id, track_type, language, content = tracks[index]
        results.append(SearchMatch(
            track_id, track_type, language, start, end,
            content[max(0, start - 20):min(len(content), end + 20)],
        ))
    return results


def search_document(
    doc: MDKVDocument, pattern: str, flags: int = 0,
    track_types: Iterable[str] | None = None, languages: Iterable[str] | None = None,
    case_insensitive: bool = False, limit: int | None = None,
) -> list[SearchMatch]:
    """Search with exact stdlib grammar, flags, and original character offsets.

    ``None`` selects all tracks; an empty filter selects none. Syntax errors
    raise ``re.error``. Startup or matching deadline violations raise
    ``TimeoutError``. Invalid pagination or more than 10,000 returned matches
    raise ``ValueError``; an explicit limit may not exceed 10,000.
    """
    return _search(
        doc, pattern, flags, track_types, languages, case_insensitive, limit, 0,
        threading.Event(),
    )


async def search_document_async(
    doc: MDKVDocument, pattern: str, flags: int = 0,
    track_types: Iterable[str] | None = None, languages: Iterable[str] | None = None,
    case_insensitive: bool = False, limit: int | None = None, offset: int = 0,
) -> AsyncIterator[SearchMatch]:
    """Yield a bounded page without blocking the event loop on subprocess I/O.

    Matching still runs only in a separate interpreter, never in a thread.
    Results are collected before yielding, so consumer wait time is not part
    of the matching deadline. Cancellation reaps the child before returning.
    Pagination and exceptions otherwise follow ``search_document``.
    """
    cancelled = threading.Event()
    worker = asyncio.create_task(asyncio.to_thread(
        _search, doc, pattern, flags, track_types, languages, case_insensitive,
        limit, offset, cancelled,
    ))
    try:
        results = await asyncio.shield(worker)
    except asyncio.CancelledError:
        cancelled.set()
        cleanup = asyncio.gather(worker, return_exceptions=True)
        while not cleanup.done():
            try:
                await asyncio.shield(cleanup)
            except asyncio.CancelledError:
                # A repeated cancel must not abandon the process supervisor.
                continue
        raise
    for index, match in enumerate(results):
        yield match
        if index % 100 == 99:
            await asyncio.sleep(0)
