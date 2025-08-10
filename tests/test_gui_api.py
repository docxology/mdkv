from pathlib import Path

from fastapi.testclient import TestClient

from mdkv.gui.server import create_app, state
from mdkv.demo import build_multitrack_demo_document


def test_gui_api_endpoints(tmp_path: Path):
    # preload a demo doc
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()

    app = create_app()
    c = TestClient(app)

    # document
    r = c.get("/api/document")
    assert r.status_code == 200 and r.json()["title"]

    # tracks
    r2 = c.get("/api/tracks")
    assert r2.status_code == 200 and len(r2.json()) >= 1

    # one track
    tid = r2.json()[0]["id"]
    r3 = c.get(f"/api/track/{tid}")
    assert r3.status_code == 200

    # render single and all
    r4 = c.get(f"/api/render/track_html", params={"track_id": tid})
    assert r4.status_code == 200 and "<" in r4.text
    r5 = c.get("/api/render/all_html")
    assert r5.status_code == 200 and "<" in r5.text

    # validate
    r6 = c.post("/api/validate")
    assert r6.status_code == 200 and r6.json()["ok"] is True


