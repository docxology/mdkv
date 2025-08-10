from pathlib import Path

from mdkv.library import build_all_examples
from mdkv.storage import load_mdkv
from mdkv.core.validate import validate_document


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
    assert {"small_en.mdkv", "large_multilingual.mdkv", "bilingual_es.mdkv", "code_snippets.mdkv", "revisions.mdkv"}.issuperset(names)
    # bilingual_es includes translation and commentary/media tracks
    bi = next((r for r in report if r[0] == "bilingual_es.mdkv"), None)
    assert bi and "translation" in bi[1] and "commentary" in bi[1] and "media_ref" in bi[1]
    # code_snippets includes code track
    cs = next((r for r in report if r[0] == "code_snippets.mdkv"), None)
    assert cs and "code" in cs[1]
    # revisions includes revision tracks
    rev = next((r for r in report if r[0] == "revisions.mdkv"), None)
    assert rev and "revision" in rev[1]


