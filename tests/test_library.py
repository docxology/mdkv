from datetime import UTC, datetime
from pathlib import Path

from mdkv.core.validate import validate_document
from mdkv.library import build_all_examples, build_document_from_definition, load_example_definition
from mdkv.storage import load_mdkv


def test_library_build_document_all_created_branches():
    # 1. string created
    d1 = build_document_from_definition({"title": "T1", "authors": ["A"], "created": "2025-01-01T00:00:00", "tracks": []})
    assert d1.created == datetime(2025, 1, 1, 0, 0, 0)
    # 2. datetime created
    now = datetime.now(UTC)
    d2 = build_document_from_definition({"title": "T2", "authors": ["A"], "created": now, "tracks": []})
    assert d2.created == now
    # 3. None / missing created
    d3 = build_document_from_definition({"title": "T3", "authors": ["A"], "tracks": []})
    assert isinstance(d3.created, datetime)

    # Test load_example_definition invalid yaml non-dict
    import tempfile
    with tempfile.NamedTemporaryFile("w+", suffix=".yaml") as f:
        f.write("- item1\n- item2\n")
        f.flush()
        d = load_example_definition(Path(f.name))
        assert d == {}


def test_library_build_and_validate(tmp_path: Path):
    defs = Path("library/definitions")
    out = tmp_path / "built"
    built = build_all_examples(defs, out)
    assert len(built) >= 4
    report = []
    for p in built:
        doc = load_mdkv(p)
        validate_document(doc)
        report.append((p.name, set(t.track_type for t in doc.tracks.values()), doc.list_languages()))
    # names and features
    names = {n for n, _, _ in report}
    assert {"small_en.mdkv", "large_multilingual.mdkv", "bilingual_es.mdkv", "code_snippets.mdkv", "revisions.mdkv", "active_inference.mdkv", "media_refs.mdkv"}.issuperset(names)
    # bilingual_es includes translation and commentary/media tracks
    bi = next((r for r in report if r[0] == "bilingual_es.mdkv"), None)
    assert bi and "translation" in bi[1] and "commentary" in bi[1] and "media_ref" in bi[1]
    # code_snippets includes code track
    cs = next((r for r in report if r[0] == "code_snippets.mdkv"), None)
    assert cs and "code" in cs[1]
    # revisions includes revision tracks
    rev = next((r for r in report if r[0] == "revisions.mdkv"), None)
    assert rev and "revision" in rev[1]


