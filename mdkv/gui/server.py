from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from mdkv.core.model import MDKVDocument, Track, allowed_track_types
from mdkv.core.validate import validate_document
from mdkv.core.errors import ValidationError
from mdkv.services.export import to_html, to_markdown
from mdkv.services.search import search_document
from mdkv.services.diff import diff_documents
from mdkv.services.stats import compute_stats
from mdkv.storage import load_mdkv, save_mdkv
from mdkv.library import build_all_examples


class MDKVState:
    def __init__(self) -> None:
        self.path: Optional[Path] = None
        self.doc: Optional[MDKVDocument] = None


state = MDKVState()


def _require_doc() -> MDKVDocument:
    """Return the loaded document or raise 400."""
    if not state.doc:
        raise HTTPException(400, "no document loaded")
    return state.doc


def create_app(static_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="MDKV GUI")

    static_root = static_dir or Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

    @app.get("/favicon.ico")
    def favicon() -> Response:
        svg_path = static_root / "favicon.svg"
        if svg_path.exists():
            svg = svg_path.read_text(encoding="utf-8")
            return Response(content=svg, media_type="image/svg+xml")
        return Response(content="", media_type="image/svg+xml")

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
            except Exception as exc:
                raise HTTPException(500, f"failed to build examples: {exc}")
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
        except Exception as exc:
            raise HTTPException(400, f"failed to open document: {exc}")
        state.path = p
        state.doc = doc
        return {"ok": True, "title": doc.title, "tracks": list(doc.tracks)}

    @app.post("/api/save")
    def save() -> dict:
        doc = _require_doc()
        if not state.path:
            raise HTTPException(400, "no file path set")
        save_mdkv(doc, state.path)
        return {"ok": True}

    @app.get("/api/document")
    def get_document() -> dict:
        doc = _require_doc()
        return {
            "title": doc.title,
            "authors": doc.authors,
            "version": doc.version,
            "created": doc.created.isoformat(),
            "tracks": [
                {
                    "id": t.track_id,
                    "type": t.track_type,
                    "language": t.language,
                    "path": t.path,
                    "content": t.content,
                }
                for t in doc.tracks.values()
            ],
        }

    @app.get("/api/tracks")
    def list_tracks() -> list[dict]:
        doc = _require_doc()
        return [
            {
                "id": t.track_id,
                "type": t.track_type,
                "language": t.language,
                "path": t.path,
            }
            for t in doc.tracks.values()
        ]

    @app.get("/api/track/{track_id}")
    def get_track(track_id: str) -> dict:
        doc = _require_doc()
        t = doc.get_track(track_id)
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
        doc = _require_doc()
        if "title" in payload:
            doc.title = payload["title"]
        if "authors" in payload and isinstance(payload["authors"], list):
            doc.authors = list(payload["authors"])
        if "version" in payload:
            doc.version = payload["version"]
        if "metadata" in payload and isinstance(payload["metadata"], dict):
            doc.metadata.clear()
            doc.metadata.update(payload["metadata"])
        return {"ok": True}

    @app.post("/api/track")
    def upsert_track(payload: dict) -> dict:
        doc = _require_doc()
        if "id" not in payload or not str(payload["id"]).strip():
            raise HTTPException(422, "missing track id")
        track_id = payload["id"]
        t = doc.get_track(track_id)
        if t is None:
            try:
                t = Track(
                    track_id=track_id,
                    track_type=payload.get("type", "commentary"),
                    language=payload.get("language"),
                    path=f"tracks/{track_id}.md",
                    content=payload.get("content", ""),
                )
            except ValueError as exc:
                raise HTTPException(400, str(exc))
            doc.add_track(t)
        else:
            new_type = payload.get("type", t.track_type)
            if new_type not in allowed_track_types():
                raise HTTPException(400, f"Unsupported track_type: {new_type}")
            t.track_type = new_type
            t.language = payload.get("language", t.language)
            t.content = payload.get("content", t.content)
        return {"ok": True}

    @app.post("/api/move-track")
    def move_track(payload: dict) -> dict:
        doc = _require_doc()
        track_id = payload.get("track_id")
        if not track_id:
            raise HTTPException(422, "missing track_id")
        after_id = payload.get("after_id")
        try:
            doc.move_track(track_id, after_id)
        except KeyError:
            raise HTTPException(404, "track not found")
        return {"ok": True, "track_ids": doc.track_ids}

    @app.get("/api/validate-track")
    def validate_single_track(track_id: str) -> dict:
        doc = _require_doc()
        t = doc.get_track(track_id)
        if t is None:
            raise HTTPException(404, "track not found")
        from mdkv.core.validate import validate_track
        try:
            issues = validate_track(t)
            return {
                "ok": True,
                "warnings": [
                    {"level": i.level, "message": i.message, "track_id": i.track_id}
                    for i in issues
                ],
            }
        except ValidationError as exc:
            return {"ok": False, "error": str(exc)}

    @app.delete("/api/track/{track_id}")
    def delete_track(track_id: str) -> dict:
        doc = _require_doc()
        try:
            doc.remove_track(track_id)
        except KeyError:
            raise HTTPException(404, "track not found")
        return {"ok": True}

    @app.get("/api/render/html", response_class=HTMLResponse)
    def render_html() -> str:
        doc = _require_doc()
        return to_html(doc)

    @app.get("/api/render/markdown")
    def render_markdown() -> JSONResponse:
        doc = _require_doc()
        return JSONResponse({"markdown": to_markdown(doc)})

    @app.get("/api/render/track_html", response_class=HTMLResponse)
    def render_track_html(track_id: str) -> str:
        doc = _require_doc()
        t = doc.get_track(track_id)
        if t is None:
            raise HTTPException(404, "track not found")
        from markdown_it import MarkdownIt

        return MarkdownIt().render(t.content)

    @app.get("/api/render/all_html", response_class=HTMLResponse)
    def render_all_html() -> str:
        doc = _require_doc()
        from markdown_it import MarkdownIt

        return MarkdownIt().render(to_markdown(doc))

    @app.post("/api/render/tracks_html", response_class=HTMLResponse)
    def render_tracks_html(payload: dict) -> str:
        doc = _require_doc()
        from markdown_it import MarkdownIt
        ids = payload.get("track_ids")
        if ids is None:
            return MarkdownIt().render(to_markdown(doc))
        if not isinstance(ids, list):
            raise HTTPException(422, "track_ids must be a list")
        if len(ids) == 0:
            return MarkdownIt().render("<!-- MDKV: empty selection -->")
        parts: list[str] = [f"<!-- MDKV: {doc.title} -->"]
        idset = set(str(x) for x in ids)
        for t in doc.tracks.values():
            if t.track_id not in idset:
                continue
            # Escape track metadata in comment to prevent comment-injection (-->)
            safe_id = t.track_id.replace("-->", "")
            safe_type = t.track_type.replace("-->", "")
            safe_lang = str(t.language).replace("-->", "") if t.language else "None"
            header = f"\n\n<!-- track:{safe_id} type:{safe_type} lang:{safe_lang} -->\n\n"
            parts.append(header + t.content)
        return MarkdownIt().render("".join(parts))

    @app.post("/api/validate")
    def validate() -> dict:
        doc = _require_doc()
        try:
            issues = validate_document(doc)
            return {
                "ok": True,
                "warnings": [
                    {
                        "level": i.level,
                        "message": i.message,
                        "track_id": i.track_id,
                    }
                    for i in issues if i.level == "WARN"
                ],
            }
        except ValidationError as exc:
            return {"ok": False, "error": str(exc)}

    @app.get("/api/search")
    def search(
        pattern: str,
        types: str = "",
        languages: str = "",
        case_insensitive: bool = False,
        limit: int = 0,
    ) -> dict:
        doc = _require_doc()
        tt = [t.strip() for t in types.split(",") if t.strip()] or None
        ll = [l.strip() for l in languages.split(",") if l.strip()] or None
        try:
            matches = search_document(
                doc, pattern=pattern, track_types=tt, languages=ll,
                case_insensitive=case_insensitive,
                limit=limit if limit > 0 else None,
            )
        except re.error as exc:
            raise HTTPException(400, f"invalid regex pattern: {exc}")
        return {
            "matches": [
                {
                    "track_id": m.track_id,
                    "track_type": m.track_type,
                    "language": m.language,
                    "start": m.start,
                    "end": m.end,
                    "extract": m.extract,
                }
                for m in matches
            ]
        }

    @app.get("/api/stats")
    def stats() -> dict:
        doc = _require_doc()
        return compute_stats(doc).to_dict()

    @app.get("/api/document/json")
    def get_document_json() -> JSONResponse:
        """Return the full document as JSON (using ``MDKVDocument.to_dict``)."""
        doc = _require_doc()
        return JSONResponse(doc.to_dict())

    @app.post("/api/import")
    def import_track(payload: dict) -> dict:
        """Import a Markdown file into the loaded document as a new track."""
        doc = _require_doc()
        file_path = payload.get("path")
        if not file_path:
            raise HTTPException(422, "missing 'path' field")
        p = Path(file_path).expanduser()
        if not p.exists():
            raise HTTPException(404, "file not found")
        track_id = payload.get("id")
        if not track_id or not str(track_id).strip():
            raise HTTPException(422, "missing track id")
        track_type = payload.get("type", "commentary")
        language = payload.get("language")
        content = p.read_text(encoding="utf-8")
        try:
            track = Track(
                track_id=track_id,
                track_type=track_type,
                language=language,
                path=f"tracks/{track_id}.md",
                content=content,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        doc.add_track(track)
        return {"ok": True, "track_id": track_id}

    @app.post("/api/diff")
    def diff(payload: dict) -> dict:
        other_path = payload.get("path")
        if not other_path:
            raise HTTPException(422, "missing 'path' field")
        p = Path(other_path).expanduser()
        if not p.exists():
            raise HTTPException(404, "file not found")
        doc_a = _require_doc()
        try:
            doc_b = load_mdkv(p)
        except Exception as exc:
            raise HTTPException(400, f"failed to load: {exc}")
        result = diff_documents(doc_a, doc_b)
        return result.to_dict()

    return app


def run(host: str = "127.0.0.1", port: int = 8000, path: str | None = None) -> None:
    import uvicorn

    app = create_app()
    if path:
        p = Path(path).expanduser()
        if p.exists():
            doc = load_mdkv(p)
            state.path = p
            state.doc = doc
    uvicorn.run(app, host=host, port=port)
