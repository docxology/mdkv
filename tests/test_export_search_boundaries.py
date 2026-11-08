"""Behavioral regressions for export and search trust boundaries."""
import asyncio
import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from mdkv import (
    MDKVDocument, Track, export_to_files, save_mdkv, search_document,
    search_document_async, to_html, to_markdown,
)
from mdkv.cli import main


def document():
    doc = MDKVDocument("Canonical", ["Real author"], datetime(2026, 1, 1, tzinfo=UTC))
    doc.add_track(Track("main", "primary", "en", "tracks/main.md", "  alpha\n\n"))
    return doc


def test_frontmatter_is_delimited_and_preserves_attribution():
    doc = document()
    doc.metadata.update({"title": "spoof", "author": "spoof", "authors": "spoof", "note": "x: y"})
    text = to_markdown(doc, metadata_header=True)
    lines = text.splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    metadata = yaml.safe_load("\n".join(lines[1:end]))
    assert metadata["title"] == "Canonical"
    assert metadata["author"] == metadata["authors"] == ["Real author"]
    assert metadata["note"] == "x: y"
    assert text.endswith("  alpha\n\n")


@pytest.mark.parametrize("other_id", ["path/main", "MAIN"])
def test_filename_collisions_fail_before_any_write(tmp_path, other_id):
    doc = document()
    doc.add_track(Track(other_id, "commentary", None, "tracks/other.md", "lost"))
    with pytest.raises(ValueError, match="collision"):
        export_to_files(doc, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_export_symlink_cannot_modify_external_target(tmp_path):
    target = tmp_path / "target.md"
    target.write_text("preserve")
    out = tmp_path / "out"
    out.mkdir()
    (out / "main.md").symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        export_to_files(document(), out)
    assert target.read_text() == "preserve"
    assert (out / "main.md").is_symlink()


def test_html_keeps_markup_inert_and_text_rendered():
    doc = document()
    doc.tracks["main"].content = '<img src=x onerror="alert(1)">\n\n# Visible\n\n[bad](javascript:alert(1))'
    rendered = to_html(doc)
    assert "<img" not in rendered
    assert "&lt;img" in rendered
    assert "<h1>Visible</h1>" in rendered
    assert 'href="javascript:' not in rendered


def test_empty_filters_and_search_pagination():
    doc = document()
    assert search_document(doc, "alpha", track_types=[]) == []
    assert search_document(doc, "alpha", languages=[]) == []
    assert search_document(doc, "alpha", limit=0) == []
    assert "alpha" not in to_markdown(doc, include_track_types=[])
    async def page():
        return [match.start async for match in search_document_async(doc, "a", offset=1, limit=1)]
    assert asyncio.run(page()) == [6]
    with pytest.raises(ValueError):
        search_document(doc, "a", limit=-1)


def test_pathological_regex_is_bounded():
    doc = document()
    doc.tracks["main"].content = "a" * 100_000 + "!"
    with pytest.raises(TimeoutError, match="deadline"):
        search_document(doc, "(a+)+$")


def test_native_markdown_omits_informational_headers_and_unsafe_metadata(tmp_path):
    from mdkv.services.pandoc_export import _write_temp_markdown

    doc = document()
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "  hidden layer\n"))
    doc.tracks["main"].content = "  literal <!-- track:ghost type:code -->\n"
    doc.metadata["header-includes"] = "\\usepackage{evil}"
    source = _write_temp_markdown(doc, ["primary"], True, tmp_path)
    text = source.read_text(encoding="utf-8")
    assert text.startswith("---\n") and text.count("\n---\n") == 1
    assert text.endswith("  literal <!-- track:ghost type:code -->\n")
    assert "<!-- MDKV:" not in text and "<!-- track:main" not in text
    assert "hidden layer" not in text and "header-includes" not in text


def test_cli_reports_duplicate_track_without_traceback(tmp_path):
    path = tmp_path / "document.mdkv"
    save_mdkv(document(), path)
    before = path.read_bytes()
    result = CliRunner().invoke(main, ["add-track", str(path), "--id", "main", "--type", "primary", "--content", "lost"])
    assert result.exit_code == 1
    assert "ERROR" in result.output
    assert "Traceback" not in result.output
    assert path.read_bytes() == before


def test_manuscript_requires_explicit_attribution(tmp_path):
    spec = importlib.util.spec_from_file_location("mdkv_paper_builder", Path(__file__).parents[1] / "paper/build_paper_bundle.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    source = tmp_path / "paper.md"
    source.write_text("# Untitled\n")
    with pytest.raises(ValueError, match="title"):
        builder.build_document(source, "en")
    source.write_text('---\ntitle: Accurate\nauthor: [Researcher]\ncreated: 2025-08-10T00:00:00Z\n---\n  Body\n')
    doc = builder.build_document(source, "en")
    assert doc.title == "Accurate"
    assert doc.authors == ["Researcher"]
    assert doc.created == datetime(2025, 8, 10, tzinfo=UTC)
    assert doc.tracks["primary"].content == "  Body\n"
    source.write_text("---\ntitle: [broken\n---\nbody")
    with pytest.raises(ValueError, match="frontmatter"):
        builder.build_document(source, "en")


@pytest.mark.parametrize("terminator", ["-->", "--!>", "---->>"])
def test_metadata_cannot_break_out_of_export_comments(terminator):
    from html.parser import HTMLParser

    from markdown_it import MarkdownIt

    class Tags(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tags = []

        def handle_starttag(self, tag, attrs):
            self.tags.append(tag)

    doc = document()
    doc.title = terminator + '<img src=x onerror="alert(1)">'
    doc.tracks["main"].language = doc.title
    rendered = MarkdownIt().render(to_markdown(doc))
    parser = Tags()
    parser.feed(rendered)
    assert "img" not in parser.tags
    assert "alpha" in rendered


def test_diff_reports_order_and_creation_changes():
    from mdkv import diff_documents

    left = document()
    left.add_track(Track("notes", "commentary", None, "tracks/notes.md", "note"))
    right = MDKVDocument.from_dict(left.to_dict())
    right.move_track("notes", None)
    result = diff_documents(left, right)
    assert result.has_changes
    assert result.to_dict()["track_order_changed"] == [["main", "notes"], ["notes", "main"]]
    assert result.tracks_modified == []
    right = MDKVDocument.from_dict(left.to_dict())
    right.created = datetime(2026, 2, 1, tzinfo=UTC)
    assert diff_documents(left, right).to_dict()["created_changed"] == [
        left.created.isoformat(), right.created.isoformat(),
    ]
