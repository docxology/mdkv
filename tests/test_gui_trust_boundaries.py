from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mdkv.core.model import MDKVDocument, Track
from mdkv.gui.server import create_app, state
from mdkv.storage import load_mdkv, save_mdkv


@pytest.fixture
def gui(tmp_path: Path):
    previous_doc, previous_path = state.doc, state.path
    doc = MDKVDocument("Trust boundary", ["A"], datetime(2025, 1, 1, tzinfo=timezone.utc))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Original\n"))
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "Notes\n"))
    state.doc, state.path = doc, tmp_path / "document.mdkv"
    try:
        with TestClient(create_app(), base_url="http://localhost") as client:
            yield client, doc, tmp_path
    finally:
        state.doc, state.path = previous_doc, previous_path


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
def test_loopback_hosts_and_no_origin_clients_remain_usable(gui, host):
    client, _, _ = gui
    assert client.get("/api/document", headers={"Host": host}).status_code == 200
    assert client.get("/api/document", headers={"Host": host + ":8123", "Origin": "http://" + host + ":8123"}).status_code == 200


@pytest.mark.parametrize("host", ["testserver", "evil.example", "localhost.evil.example", "127.0.0.2", "localhost@evil.example", "localhost:invalid"])
def test_foreign_and_malformed_hosts_cannot_read_or_mutate(gui, host):
    client, doc, _ = gui
    before = doc.to_dict()
    assert client.get("/api/document", headers={"Host": host}).status_code == 400
    assert client.post("/api/document", headers={"Host": host}, json={"title": "changed"}).status_code == 400
    assert doc.to_dict() == before


@pytest.mark.parametrize("headers", [
    {"Origin": "https://evil.example"},
    {"Origin": "null"},
    {"Origin": "http://localhost:8123"},
    {"Origin": "https://localhost"},
    {"Origin": "http://localhost/path"},
    {"Sec-Fetch-Site": "cross-site"},
    {"Origin": "http://testserver", "Sec-Fetch-Site": "cross-site"},
])
def test_browser_source_checks_protect_reads_and_mutations(gui, headers):
    client, doc, _ = gui
    before = doc.to_dict()
    for path in ("/api/status", "/api/document", "/api/document/json", "/api/tracks", "/api/track?track_id=primary",
                 "/api/render/all_html", "/api/search?pattern=Original", "/api/stats", "/api/library"):
        assert client.get(path, headers=headers).status_code == 403
    assert client.post("/api/document", headers=headers, json={"title": "changed"}).status_code == 403
    assert client.delete("/api/track", params={"track_id": "notes"}, headers=headers).status_code == 403
    assert doc.to_dict() == before


def test_cross_origin_json_preflight_and_direct_post_are_denied(gui):
    client, doc, _ = gui
    before = doc.to_dict()
    # A browser JSON POST requires this preflight; TestClient itself is not a browser.
    response = client.options("/api/document", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers
    assert client.post("/api/document", headers={"Origin": "https://evil.example"}, json={"title": "changed"}).status_code == 403
    assert doc.to_dict() == before
    assert client.post("/api/document", headers={"Origin": "http://localhost:80", "Sec-Fetch-Site": "same-origin"}, json={"title": "same origin"}).status_code == 200
    assert client.post("/api/document", json={"title": "trusted non-browser"}).status_code == 200


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.extend(attrs)

    def handle_data(self, data):
        self.text.append(data)


@pytest.mark.parametrize("method,path,kwargs", [
    ("get", "/api/render/html", {}),
    ("get", "/api/render/all_html", {}),
    ("get", "/api/render/track_html", {"params": {"track_id": "primary"}}),
    ("post", "/api/render/tracks_html", {"json": {}}),
    ("post", "/api/render/tracks_html", {"json": {"track_ids": ["primary"]}}),
])
def test_every_gui_markdown_renderer_keeps_raw_html_inert(gui, method, path, kwargs):
    client, doc, _ = gui
    doc.title = '--><img src=x onerror="alert(1)">'
    doc.tracks["primary"].content = '# Safe heading\n\n<script>alert(1)</script>\n\n<img src=x onerror="alert(1)">\n\n[bad](javascript:alert(1))\n'
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 200
    markup = Markup()
    markup.feed(response.text)
    assert "h1" in markup.tags
    assert "script" not in markup.tags
    assert "img" not in markup.tags
    assert not any(name.startswith("on") or (name == "href" and value.startswith("javascript:")) for name, value in markup.attributes)
    assert "<script>alert(1)</script>" in "".join(markup.text)


def test_diff_titles_are_text_not_html(gui):
    client, doc, tmp_path = gui
    doc.title = '<img src=x onerror="alert(1)">A'
    other = MDKVDocument('<script>alert(2)</script>B', ["B"], doc.created)
    other.add_track(Track("primary", "primary", "en", "tracks/primary.md", "Changed\n"))
    path = tmp_path / "other.mdkv"
    save_mdkv(other, path)
    response = client.get("/api/diff/view", params={"other_path": str(path)})
    assert response.status_code == 200
    markup = Markup()
    markup.feed(response.text)
    assert "img" not in markup.tags and "script" not in markup.tags
    assert doc.title in "".join(markup.text)
    assert other.title in "".join(markup.text)


def test_preview_frame_is_sandboxed(gui):
    client, _, _ = gui
    markup = Markup()
    markup.feed(client.get("/").text)
    assert "iframe" in markup.tags
    assert ("sandbox", "") in markup.attributes


@pytest.mark.parametrize("path,payload", [
    ("/api/document", {"title": []}),
    ("/api/document", {"title": "changed", "authors": [1]}),
    ("/api/document", {"title": "changed", "version": {}}),
    ("/api/document", {"title": "changed", "metadata": {"key": []}}),
    ("/api/document", {"authors": "not a list"}),
    ("/api/track", {"id": []}),
    ("/api/track", {"id": {}}),
    ("/api/track", {"id": "primary", "type": []}),
    ("/api/track", {"id": "primary", "type": "commentary", "content": None}),
    ("/api/track", {"id": "primary", "type": "commentary", "language": []}),
    ("/api/move-track", {"track_id": []}),
    ("/api/move-track", {"track_id": "primary", "after_id": {}}),
    ("/api/render/tracks_html", {"track_ids": [[]]}),
    ("/api/open", {"path": []}),
    ("/api/import", {"path": {}, "id": "new"}),
    ("/api/diff", {"path": []}),
])
def test_malformed_payloads_never_partially_mutate(gui, path, payload):
    client, doc, _ = gui
    before = doc.to_dict()
    previous_path = state.path
    response = client.post(path, json=payload)
    assert response.status_code in (400, 422)
    assert state.doc is doc and state.path == previous_path
    assert doc.to_dict() == before


def test_import_failures_are_atomic_and_do_not_restrict_local_paths(gui):
    client, doc, tmp_path = gui
    source = tmp_path / "chosen.md"
    source.write_text("  chosen local Markdown\n\n", encoding="utf-8")
    before = doc.to_dict()
    assert client.post("/api/import", json={"path": str(source), "id": "primary"}).status_code == 400
    assert doc.to_dict() == before
    binary = tmp_path / "binary.md"
    binary.write_bytes(b"\xff")
    for path in (binary, tmp_path):
        assert client.post("/api/import", json={"path": str(path), "id": "new"}).status_code == 400
        assert doc.to_dict() == before
    assert client.post("/api/import", json={"path": str(source), "id": []}).status_code == 422
    assert client.post("/api/import", json={"path": str(source), "id": "chosen"}).status_code == 200
    assert doc.tracks["chosen"].content == source.read_text(encoding="utf-8")


def test_open_read_and_save_failures_preserve_good_document(gui):
    client, doc, tmp_path = gui
    before = doc.to_dict()
    original_path = state.path
    corrupt = tmp_path / "corrupt.mdkv"
    corrupt.write_bytes(b"not a container")
    for path in (corrupt, tmp_path):
        assert client.post("/api/open", json={"path": str(path)}).status_code == 400
        assert client.post("/api/diff", json={"path": str(path)}).status_code == 400
        assert client.get("/api/diff/view", params={"other_path": str(path)}).status_code == 400
        assert state.doc is doc and state.path == original_path
        assert doc.to_dict() == before
    state.path = tmp_path
    assert client.post("/api/save").status_code == 400
    assert state.doc is doc and doc.to_dict() == before


def test_single_track_editor_content_is_literal_and_saved_exactly(gui):
    client, doc, _ = gui
    untouched = doc.tracks["notes"].content
    literal = ' \n\t# Edit\n\n<!-- track:notes type:commentary lang:None -->\nforged header stays here\n \t\n'
    assert client.put("/api/track", json={"id": "primary", "content": literal}).status_code == 200
    assert client.get("/api/track", params={"track_id": "primary"}).json()["content"] == literal
    assert client.post("/api/save").status_code == 200
    loaded = load_mdkv(state.path)
    assert loaded.tracks["primary"].content == literal
    assert loaded.tracks["notes"].content == untouched
    assert list(loaded.tracks) == ["primary", "notes"]
    # An unknown canonical track cannot accidentally be created by editor saves.
    assert client.put("/api/track", json={"id": "forged", "content": "body"}).status_code == 404
    assert list(doc.tracks) == ["primary", "notes"]


def test_preview_selection_is_independent_and_nonmutating(gui):
    client, doc, _ = gui
    before = doc.to_dict()
    response = client.post("/api/render/tracks_html", json={"track_ids": ["notes"]})
    assert response.status_code == 200
    assert "Notes" in response.text and "Original" not in response.text
    assert client.post("/api/render/tracks_html", json={"track_ids": []}).text == ""
    assert doc.to_dict() == before


def test_negative_search_limit_is_a_client_error(gui):
    client, _, _ = gui
    assert client.get("/api/search", params={"pattern": "Original", "limit": -1}).status_code == 400


def test_installed_canonical_library_opens_fresh_and_saves_only_to_chosen_path(gui):
    client, _, tmp_path = gui
    response = client.get("/api/library")
    assert response.status_code == 200
    files = response.json()["files"]
    expected = {"active_inference", "bilingual_es", "code_snippets", "large_multilingual", "media_refs", "revisions", "small_en"}
    assert {item["id"] for item in files} == {"library:" + name for name in expected}
    assert all(item["path"] == item["id"] for item in files)
    assert client.post("/api/open", json={"path": "library:small_en"}).status_code == 200
    assert client.get("/api/status").json()["path"] is None
    original_title = client.get("/api/document").json()["title"]
    assert client.post("/api/document", json={"title": "Edited in memory"}).status_code == 200
    assert client.post("/api/open", json={"path": "library:small_en"}).status_code == 200
    assert client.get("/api/document").json()["title"] == original_title
    assert client.post("/api/save").status_code == 400
    assert state.path is None
    destination = tmp_path / "chosen-local-copy.mdkv"
    assert client.post("/api/save", json={"path": str(destination)}).status_code == 200
    assert state.path == destination
    assert load_mdkv(destination).title == original_title


@pytest.mark.parametrize("handle,status", [
    ("library:../small_en", 400),
    ("library:missing", 404),
])
def test_failed_library_opens_preserve_prior_document(gui, handle, status):
    client, doc, _ = gui
    before = doc.to_dict()
    original_path = state.path
    assert client.post("/api/open", json={"path": handle}).status_code == status
    assert state.doc is doc and state.path == original_path
    assert doc.to_dict() == before


def test_failed_save_as_does_not_change_active_path(gui):
    client, doc, tmp_path = gui
    before = doc.to_dict()
    original_path = state.path
    assert client.post("/api/save", json={"path": []}).status_code == 422
    assert client.post("/api/save", json={"path": str(tmp_path)}).status_code == 400
    assert state.doc is doc and state.path == original_path
    assert doc.to_dict() == before


@pytest.mark.parametrize("track_id", [".", "..", "nested/id", "space id", "雪"])
def test_literal_track_ids_survive_query_and_body_transports(gui, track_id):
    client, doc, _ = gui
    doc.add_track(Track(track_id, "commentary", None, "tracks/literal.md", "before"))
    assert client.get("/api/track", params={"track_id": track_id}).json()["content"] == "before"
    assert client.put("/api/track", json={"id": track_id, "content": "after"}).status_code == 200
    assert doc.tracks[track_id].content == "after"
    assert client.delete("/api/track", params={"track_id": track_id}).status_code == 200
    assert track_id not in doc.tracks


def test_existing_only_track_update_rejects_invalid_content_atomically(gui):
    client, doc, _ = gui
    before = doc.to_dict()
    assert client.put("/api/track", json={"id": "primary", "type": "commentary", "content": {}}).status_code == 422
    assert doc.to_dict() == before
