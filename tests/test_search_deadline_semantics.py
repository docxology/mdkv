"""Real-interpreter regressions for stdlib search semantics and supervision."""

import asyncio
import json
import os
import re
import signal
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

import mdkv.services.search as search
from mdkv.core.model import MDKVDocument, Track


def document(*contents):
    doc = MDKVDocument("Search", ["Author"], datetime(2026, 1, 1, tzinfo=UTC))
    for index, content in enumerate(contents):
        doc.add_track(Track(
            f"t{index}", "primary" if index == 0 else "commentary",
            "en" if index == 0 else None, f"tracks/t{index}.md", content,
        ))
    return doc


def reference(doc, pattern, flags=0):
    return [
        search.SearchMatch(
            track_id, track.track_type, track.language, match.start(), match.end(),
            track.content[max(0, match.start() - 20):min(len(track.content), match.end() + 20)],
        )
        for track_id, track in doc.tracks.items()
        for match in re.finditer(pattern, track.content, flags)
    ]


@pytest.mark.parametrize(
    ("pattern", "text", "flags"),
    [
        (r"(dog){e<=1}", "dog dug dog{e<=1} DOG{e<=1}", 0),
        (r"\w+", "cafe\u0301 café a\u0308 α\u0301", 0),
        (r"\b", "a\u0301b café\u0301 👋x", 0),
        (r"\b\w+\b", "é e\u0301 Ελληνικά 你好_123", 0),
        (r"[a-z]+", "İ ı ſ K K S Straße", re.IGNORECASE),
        (r"\b\w+\b", "İ ı ſ K café Cafe_12", re.ASCII | re.IGNORECASE),
        (r"(?ai)\b[a-z]+\b", "İ ı ſ K café Cafe", 0),
        (r"(?i:dog)(?-i:CAT)", "DOGCAT dogcat dogCAT", 0),
        (r"(?<=α)(?=β)|(?<!\w)cat(?!\w)", "αβ cat bobcat cat!", 0),
        (r"(?P<word>\w+)\s+(?P=word)", "café café dog cat cat cat", 0),
        (r"(?=a)|a*", "aa b", 0),
        (r"^.+?$", "α\n👋\nbeta\n", re.MULTILINE | re.DOTALL),
        (r".|\b", "a\ud800👋\udfffz", re.DOTALL),
        (r".|\b", "a\ud83d\udc4b👋z", re.DOTALL),
        (r"(?x) \b (foo|bar) \b # comment", "foo bar foobar", 0),
        (r"(?i:ß|ss)", "ß SS ss ẞ", 0),
        (r"a+", "aa b a", re.DEBUG),
    ],
)
def test_matches_are_exactly_stdlib_re(pattern, text, flags):
    doc = document(text, "👋 " + text)
    assert search.search_document(doc, pattern, flags=flags) == reference(doc, pattern, flags)


def test_case_insensitive_option_keeps_original_unicode_offsets():
    doc = document("👋 e\u0301 İ dog DOG dog{e<=1}")
    pattern = r"dog|i|\w+"
    assert search.search_document(doc, pattern, case_insensitive=True) == reference(
        doc, pattern, re.IGNORECASE,
    )


def test_excessively_nested_pattern_is_a_clean_resource_error():
    with pytest.raises(ValueError, match="compiler nesting"):
        search.search_document(document("a"), "(" * 600 + "a" + ")" * 600)


def test_excessively_large_repetition_is_a_clean_resource_error():
    with pytest.raises(ValueError, match="compiler limits"):
        search.search_document(document("a"), "a{999999999999999999999999}")


def test_filtering_excludes_pathological_tracks_before_matching():
    doc = document("a" * 100_000 + "!", "aa")
    matches = search.search_document(doc, "(a+)+$", track_types=["commentary"], languages=[None])
    assert [(match.track_id, match.start, match.end) for match in matches] == [("t1", 0, 2)]
    assert search.search_document(doc, "(a+)+$", track_types=[]) == []
    assert search.search_document(doc, "(a+)+$", languages=[]) == []
    assert search.search_document(doc, "(a+)+$", limit=0) == []


@pytest.mark.parametrize("offset,limit", [(0, None), (0, 0), (1, 1), (2, 3), (5, None), (100, 2)])
def test_async_page_matches_sync_order_offsets_and_limit(offset, limit):
    doc = document("a\u0301 aa", "", "a 👋a")
    pattern = r"\b|a"
    all_matches = search.search_document(doc, pattern)

    async def collect():
        return [match async for match in search.search_document_async(
            doc, pattern, offset=offset, limit=limit,
        )]

    end = None if limit is None else offset + limit
    assert asyncio.run(collect()) == all_matches[offset:end]
    assert search.search_document(doc, pattern, limit=limit) == all_matches[:limit]


def test_async_filters_and_case_insensitive_semantics():
    doc = document("DOG", "İ dog DOG")

    async def collect():
        return [match async for match in search.search_document_async(
            doc, r"i|dog", track_types=["commentary"], languages=[None],
            case_insensitive=True, offset=1, limit=1,
        )]

    assert asyncio.run(collect()) == [search.SearchMatch("t1", "commentary", None, 2, 5, "İ dog DOG")]


@pytest.mark.parametrize("pattern", ["[", r"(?P<x>a)(?P<x>b)", r"(?<=a+)b", "("])
def test_syntax_errors_keep_stdlib_error_details(pattern):
    with pytest.raises(re.error) as expected:
        re.compile(pattern)
    with pytest.raises(re.error) as actual:
        search.search_document(document("anything"), pattern, limit=0, track_types=[])
    assert (actual.value.msg, actual.value.pattern, actual.value.pos) == (
        expected.value.msg, expected.value.pattern, expected.value.pos,
    )


@pytest.mark.parametrize("flags", [re.LOCALE, re.ASCII | re.UNICODE])
def test_invalid_stdlib_flags_raise_value_error(flags):
    with pytest.raises(ValueError):
        search.search_document(document("x"), "x", flags=flags)


@pytest.mark.parametrize("limit", [-1, -100, 1.5, "1", search.MAX_SEARCH_RESULTS + 1])
def test_invalid_sync_limits_raise_value_error(limit):
    with pytest.raises(ValueError):
        search.search_document(document("x"), "x", limit=limit)


@pytest.mark.parametrize("params", [{"limit": -1}, {"offset": -1}, {"offset": 1.5}, {"offset": "1"}])
def test_invalid_async_pagination_raises_value_error(params):
    async def collect():
        return [match async for match in search.search_document_async(document("x"), "x", **params)]

    with pytest.raises(ValueError):
        asyncio.run(collect())


def test_pattern_length_budget_remains_explicit():
    with pytest.raises(ValueError, match="pattern exceeds"):
        search.search_document(document("x"), "x" * (search.MAX_PATTERN_LENGTH + 1))


def test_zero_width_results_fail_explicitly_instead_of_truncating():
    doc = document("x" * search.MAX_SEARCH_RESULTS)
    with pytest.raises(ValueError, match="maximum.*results"):
        search.search_document(doc, r"(?=)")
    page = search.search_document(doc, r"(?=)", limit=search.MAX_SEARCH_RESULTS)
    assert len(page) == search.MAX_SEARCH_RESULTS
    assert (page[0].start, page[-1].end) == (0, search.MAX_SEARCH_RESULTS - 1)
    exact = search.search_document(document("x" * (search.MAX_SEARCH_RESULTS - 1)), r"(?=)")
    assert len(exact) == search.MAX_SEARCH_RESULTS


def test_async_zero_width_result_budget_is_not_silently_truncated():
    async def collect():
        return [match async for match in search.search_document_async(
            document("x" * search.MAX_SEARCH_RESULTS), r"(?=)",
        )]

    with pytest.raises(ValueError, match="maximum.*results"):
        asyncio.run(collect())


_PRELUDE = '''
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
sys.path.insert(0, sys.argv[1])
from mdkv.core.model import MDKVDocument, Track
from mdkv.services.search import search_document, search_document_async

def document(text):
    doc = MDKVDocument("Native caller", [], datetime(2026, 1, 1, tzinfo=UTC))
    doc.add_track(Track("main", "primary", "en", "tracks/main.md", text))
    return doc

def assert_reaped():
    try:
        pid, status = os.waitpid(-1, os.WNOHANG)
    except ChildProcessError:
        return
    raise AssertionError("search left a running or unreaped child: %r" % ((pid, status),))
'''


@pytest.fixture
def native_caller(tmp_path):
    """Keep child-lifecycle assertions separate from pytest's own subprocesses."""
    root = str(Path(search.__file__).resolve().parents[2])

    def run(script):
        process = subprocess.Popen(
            [sys.executable, "-c", _PRELUDE + script, root],
            cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=(os.name == "posix"),
        )
        try:
            stdout, stderr = process.communicate(timeout=20)
            assert process.returncode == 0, stdout + stderr
            return json.loads(stdout)
        finally:
            # Even a regression must not strand a catastrophic grandchild in
            # the test runner. All fixture processes have a private POSIX group.
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()
            process.stderr.close()

    return run


def test_native_caller_outside_checkout_needs_no_spawn_main_guard(native_caller):
    assert native_caller('''
matches = search_document(document("dog{e<=1} dug"), r"(dog){e<=1}")
print(json.dumps([(match.start, match.end) for match in matches]))
''') == [[0, 9]]


@pytest.mark.skipif(os.name != "posix", reason="isolated POSIX waitpid lifecycle assertions")
def test_real_pathological_timeout_and_other_outcomes_reap_children(native_caller):
    assert native_caller('''
import re
from mdkv.services.search import MAX_SEARCH_RESULTS
assert len(search_document(document("aa"), "a")) == 2
assert_reaped()
try:
    search_document(document("x"), "[")
except re.error:
    pass
else:
    raise AssertionError("syntax error was not preserved")
assert_reaped()
try:
    search_document(document("x" * MAX_SEARCH_RESULTS), r"(?=)")
except ValueError:
    pass
else:
    raise AssertionError("result budget was silently truncated")
assert_reaped()
try:
    search_document(document("a" * 100_000 + "!"), r"(a+)+$")
except TimeoutError as exc:
    assert "matching deadline" in str(exc)
else:
    raise AssertionError("catastrophic stdlib matching was not terminated")
assert_reaped()
print(json.dumps("reaped"))
''') == "reaped"


@pytest.mark.skipif(os.name != "posix", reason="isolated POSIX waitpid lifecycle assertions")
def test_async_wait_is_responsive_and_repeated_cancel_reaps_child(native_caller):
    assert native_caller('''
async def consume():
    return [match async for match in search_document_async(
        document("a" * 100_000 + "!"), r"(a+)+$",
    )]

async def exercise():
    task = asyncio.create_task(consume())
    async def wait_for_live_child():
        while True:
            if task.done():
                await task
                raise AssertionError("search finished before the caller could run")
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                pass
            else:
                assert pid == 0, "worker exited before cancellation"
                return
            await asyncio.sleep(0.01)
    try:
        await asyncio.wait_for(wait_for_live_child(), timeout=10)
        heartbeat = []
        asyncio.get_running_loop().call_soon(heartbeat.append, "responsive")
        await asyncio.sleep(0)
        assert heartbeat == ["responsive"]
        assert not task.done()
    finally:
        task.cancel()
        asyncio.get_running_loop().call_soon(task.cancel)
        try:
            await task
        except asyncio.CancelledError:
            pass
    assert_reaped()

asyncio.run(exercise())
assert_reaped()
print(json.dumps("cancelled and reaped"))
''') == "cancelled and reaped"


@pytest.mark.skipif(os.name != "posix", reason="isolated POSIX waitpid lifecycle assertions")
def test_async_pathological_timeout_reaps_child(native_caller):
    assert native_caller('''
async def exercise():
    try:
        results = [match async for match in search_document_async(
            document("a" * 100_000 + "!"), r"(a+)+$", offset=1, limit=1,
        )]
    except TimeoutError as exc:
        assert "matching deadline" in str(exc)
    else:
        raise AssertionError("pathological async search unexpectedly completed: %r" % results)
    assert_reaped()

asyncio.run(exercise())
assert_reaped()
print(json.dumps("async timeout reaped"))
''') == "async timeout reaped"
