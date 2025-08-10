from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from mdkv.core.model import MDKVDocument, Track
from mdkv.core.validate import validate_document
from mdkv.core.errors import ValidationError
from mdkv.services.export import to_html, to_markdown
from mdkv.storage import load_mdkv, save_mdkv
from mdkv.library import build_all_examples


class MDKVState:
    def __init__(self) -> None:
        self.path: Optional[Path] = None
        self.doc: Optional[MDKVDocument] = None


state = MDKVState()


def create_app(static_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="MDKV GUI")

    static_root = static_dir or Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def root() -> str:
        return (static_root / "index.html").read_text(encoding="utf-8")

    @app.get("/api/status")
    def status() -> dict:
        return {
            "loaded": state.doc is not None,
            "path": str(state.path) if state.path else None,
            "tracks": list(state.doc.tracks) if state.doc else [],
        }

    @app.get("/api/library")
    def list_library() -> dict:
        """Return available example `.mdkv` files under `library/definitions`.

        If built files are missing under `library/_built`, they are generated.
        """
        repo_root = Path(__file__).resolve().parents[2]
        defs = repo_root / "library" / "definitions"
        out_dir = repo_root / "library" / "_built"
        out_dir.mkdir(parents=True, exist_ok=True)
        built_paths = list(out_dir.glob("*.mdkv"))
        if not built_paths:
            try:
                build_all_examples(defs, out_dir)
                built_paths = list(out_dir.glob("*.mdkv"))
            except Exception as e:
                raise HTTPException(500, f"failed to build examples: {e}")
        return {
            "files": [
                {"name": p.name, "path": str(p)}
                for p in sorted(built_paths)
            ]
        }

    @app.post("/api/open")
    def open_file(payload: dict) -> dict:
        p = Path(payload.get("path", "")).expanduser()
        if not p.exists():
            raise HTTPException(404, "file not found")
        try:
            doc = load_mdkv(p)
        except Exception as e:  # surface container/manifest issues as 400
            raise HTTPException(400, f"failed to open document: {e}")
        state.path = p
        state.doc = doc
        return {"ok": True, "title": doc.title, "tracks": list(doc.tracks)}

    @app.post("/api/save")
    def save() -> dict:
        if not state.doc or not state.path:
            raise HTTPException(400, "no document loaded")
        save_mdkv(state.doc, state.path)
        return {"ok": True}

    @app.get("/api/document")
    def get_document() -> dict:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        return {
            "title": state.doc.title,
            "authors": state.doc.authors,
            "tracks": [
                {
                    "id": t.track_id,
                    "type": t.track_type,
                    "language": t.language,
                    "path": t.path,
                    "content": t.content,
                }
                for t in state.doc.tracks.values()
            ],
        }

    @app.get("/api/tracks")
    def list_tracks() -> list[dict]:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        return [
            {
                "id": t.track_id,
                "type": t.track_type,
                "language": t.language,
                "path": t.path,
            }
            for t in state.doc.tracks.values()
        ]

    @app.get("/api/track/{track_id}")
    def get_track(track_id: str) -> dict:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        t = state.doc.get_track(track_id)
        if t is None:
            raise HTTPException(404, "track not found")
        return {
            "id": t.track_id,
            "type": t.track_type,
            "language": t.language,
            "path": t.path,
            "content": t.content,
        }

    @app.post("/api/document")
    def update_document(payload: dict) -> dict:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        state.doc.title = payload.get("title", state.doc.title)
        if "authors" in payload and isinstance(payload["authors"], list):
            state.doc.authors = list(payload["authors"])
        return {"ok": True}

    @app.post("/api/track")
    def upsert_track(payload: dict) -> dict:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        if "id" not in payload or not str(payload["id"]).strip():
            raise HTTPException(422, "missing track id")
        track_id = payload["id"]
        t = state.doc.get_track(track_id)
        if t is None:
            try:
                t = Track(
                    track_id=track_id,
                    track_type=payload.get("type", "commentary"),
                    language=payload.get("language"),
                    path=f"tracks/{track_id}.md",
                    content=payload.get("content", ""),
                )
            except ValueError as e:
                raise HTTPException(400, str(e))
            state.doc.add_track(t)
        else:
            t.track_type = payload.get("type", t.track_type)
            t.language = payload.get("language", t.language)
            t.content = payload.get("content", t.content)
        return {"ok": True}

    @app.delete("/api/track/{track_id}")
    def delete_track(track_id: str) -> dict:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        state.doc.remove_track(track_id)
        return {"ok": True}

    @app.get("/api/render/html", response_class=HTMLResponse)
    def render_html() -> str:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        return to_html(state.doc)

    @app.get("/api/render/markdown")
    def render_markdown() -> JSONResponse:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        return JSONResponse({"markdown": to_markdown(state.doc)})

    @app.get("/api/render/track_html", response_class=HTMLResponse)
    def render_track_html(track_id: str) -> str:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        t = state.doc.get_track(track_id)
        if t is None:
            raise HTTPException(404, "track not found")
        # render only this track's content
        from markdown_it import MarkdownIt

        return MarkdownIt().render(t.content)

    @app.get("/api/render/all_html", response_class=HTMLResponse)
    def render_all_html() -> str:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        from markdown_it import MarkdownIt

        return MarkdownIt().render(to_markdown(state.doc))

    @app.post("/api/validate")
    def validate() -> dict:
        if not state.doc:
            raise HTTPException(400, "no document loaded")
        try:
            validate_document(state.doc)
            return {"ok": True}
        except ValidationError as e:
            return {"ok": False, "error": str(e)}

    return app


def run(host: str = "127.0.0.1", port: int = 8000, path: str | None = None) -> None:
    import uvicorn

    app = create_app()
    if path:
        p = Path(path).expanduser()
        if p.exists():
            # preload
            doc = load_mdkv(p)
            state.path = p
            state.doc = doc
    uvicorn.run(app, host=host, port=port)


