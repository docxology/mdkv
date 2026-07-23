"""Performance benchmarks for MDKV operations.

Tests save/load/search/export on synthetic documents of varying sizes.
Does not require pytest-benchmark — uses simple time assertions.
"""
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mdkv import MDKVDocument, Track, save_mdkv, load_mdkv, search_document, to_markdown, compute_stats


def _make_doc(num_tracks: int, content_size: int = 500) -> MDKVDocument:
    """Create a synthetic document with the given number of tracks."""
    doc = MDKVDocument(
        title="Benchmark Doc",
        authors=["Benchmark"],
        created=datetime.now(timezone.utc),
    )
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Primary\n\n" + "x" * content_size))
    for i in range(1, num_tracks):
        content = f"# Track {i}\n\n" + "y" * content_size
        doc.add_track(Track(
            f"track-{i}", "commentary", None, f"tracks/track-{i}.md", content
        ))
    return doc


class TestBenchmarkSaveLoad:
    """Benchmark save and load operations."""

    def test_save_small_doc(self, tmp_path: Path):
        doc = _make_doc(5)
        path = tmp_path / "small.mdkv"
        start = time.perf_counter()
        save_mdkv(doc, path)
        elapsed = time.perf_counter() - start
        assert path.exists()
        assert elapsed < 2.0  # should be well under 2 seconds

    def test_save_medium_doc(self, tmp_path: Path):
        doc = _make_doc(50, content_size=2000)
        path = tmp_path / "medium.mdkv"
        start = time.perf_counter()
        save_mdkv(doc, path)
        elapsed = time.perf_counter() - start
        assert path.exists()
        assert elapsed < 5.0

    def test_load_small_doc(self, tmp_path: Path):
        doc = _make_doc(5)
        path = tmp_path / "small.mdkv"
        save_mdkv(doc, path)
        start = time.perf_counter()
        loaded = load_mdkv(path)
        elapsed = time.perf_counter() - start
        assert len(loaded.tracks) == 5
        assert elapsed < 2.0

    def test_load_medium_doc(self, tmp_path: Path):
        doc = _make_doc(50, content_size=2000)
        path = tmp_path / "medium.mdkv"
        save_mdkv(doc, path)
        start = time.perf_counter()
        loaded = load_mdkv(path)
        elapsed = time.perf_counter() - start
        assert len(loaded.tracks) == 50
        assert elapsed < 5.0

    def test_roundtrip_integrity(self, tmp_path: Path):
        """Verify that save+load preserves all track content."""
        doc = _make_doc(10, content_size=1000)
        path = tmp_path / "roundtrip.mdkv"
        save_mdkv(doc, path)
        loaded = load_mdkv(path)
        for tid in doc.track_ids:
            assert loaded.get_track(tid).content == doc.get_track(tid).content


class TestBenchmarkSearch:
    """Benchmark search operations."""

    def test_search_small_doc(self, tmp_path: Path):
        doc = _make_doc(5)
        path = tmp_path / "small.mdkv"
        save_mdkv(doc, path)
        loaded = load_mdkv(path)
        start = time.perf_counter()
        matches = search_document(loaded, pattern="x")
        elapsed = time.perf_counter() - start
        assert len(matches) > 0
        assert elapsed < 1.0

    def test_search_medium_doc(self, tmp_path: Path):
        doc = _make_doc(50, content_size=2000)
        path = tmp_path / "medium.mdkv"
        save_mdkv(doc, path)
        loaded = load_mdkv(path)
        start = time.perf_counter()
        matches = search_document(loaded, pattern="y", limit=10)
        elapsed = time.perf_counter() - start
        assert len(matches) <= 10
        assert elapsed < 1.0

    def test_search_no_matches(self, tmp_path: Path):
        doc = _make_doc(5)
        path = tmp_path / "small.mdkv"
        save_mdkv(doc, path)
        loaded = load_mdkv(path)
        start = time.perf_counter()
        matches = search_document(loaded, pattern="zzzznotfound")
        elapsed = time.perf_counter() - start
        assert len(matches) == 0
        assert elapsed < 1.0


class TestBenchmarkExport:
    """Benchmark export operations."""

    def test_export_markdown_small(self, tmp_path: Path):
        doc = _make_doc(5)
        start = time.perf_counter()
        md = to_markdown(doc)
        elapsed = time.perf_counter() - start
        assert len(md) > 0
        assert elapsed < 1.0

    def test_export_markdown_medium(self, tmp_path: Path):
        doc = _make_doc(50, content_size=2000)
        start = time.perf_counter()
        md = to_markdown(doc)
        elapsed = time.perf_counter() - start
        assert len(md) > 0
        assert elapsed < 2.0

    def test_stats_small(self, tmp_path: Path):
        doc = _make_doc(5)
        start = time.perf_counter()
        stats = compute_stats(doc)
        elapsed = time.perf_counter() - start
        assert stats.track_count == 5
        assert elapsed < 1.0
