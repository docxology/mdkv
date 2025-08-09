from pathlib import Path

from fastapi.testclient import TestClient

from mdkv.gui.server import create_app


def test_gui_status_and_static(tmp_path: Path):
    app = create_app()
    client = TestClient(app)
    r = client.get("/api/status")
    assert r.status_code == 200 and r.json()["loaded"] is False
    r2 = client.get("/")
    assert r2.status_code == 200


