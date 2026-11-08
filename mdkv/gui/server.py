from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from markdown_it import MarkdownIt
from starlette.middleware.base import RequestResponseEndpoint

from mdkv.core.errors import ValidationError
from mdkv.core.model import MDKVDocument, Track, allowed_track_types
from mdkv.core.validate import validate_document
from mdkv.library import example_definitions_dir, load_example_document
from mdkv.services.diff import diff_documents
from mdkv.services.export import to_markdown
from mdkv.services.search import search_document
from mdkv.services.stats import compute_stats
from mdkv.storage import load_mdkv, save_mdkv


class MDKVState:
    def __init__(self) -> None:
        self.path: Path | None = None
        self.doc: MDKVDocument | None = None


state = MDKVState()


def _require_doc() -> MDKVDocument:
    """Return the loaded document or raise 400."""
    if state.doc is None:
        raise HTTPException(400, "no document loaded")
    return state.doc


def _string(value: Any, name: str, *, nonempty: bool = False) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise HTTPException(422, f"{name} must be a {'nonempty ' if nonempty else ''}string")
    return value


def _path(value: Any) -> Path:
    value = _string(value, "path", nonempty=True)
    try:
        return Path(value).expanduser()
    except (ValueError, RuntimeError, OSError) as exc:
        raise HTTPException(400, f"invalid path: {exc}") from exc


def _load(path: Path) -> MDKVDocument:
    try:
        return load_mdkv(path)
    except FileNotFoundError as exc:
        raise HTTPException(404, "file not found") from exc
    except Exception as exc:
        raise HTTPException(400, f"failed to open document: {exc}") from exc


def _track_values(payload: dict[str, Any], current: Track | None = None) -> tuple[str, str | None, str]:
    track_type = _string(payload.get("type", current.track_type if current else "commentary"), "type")
    if track_type not in allowed_track_types():
        raise HTTPException(400, f"Unsupported track_type: {track_type}")
    language = payload.get("language", current.language if current else None)
    if language is not None:
        _string(language, "language")
    content = _string(payload.get("content", current.content if current else ""), "content")
    return track_type, language, content


def _origin(value: str) -> tuple[str, str, int]:
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path or parsed.query or parsed.fragment):
        raise ValueError("invalid origin")
    port = parsed.port
    return parsed.scheme, parsed.hostname.lower(), port if port is not None else (443 if parsed.scheme == "https" else 80)


def _render(markdown: str) -> str:
    return str(MarkdownIt("commonmark", {"html": False}).enable("table").render(markdown))


def create_app(static_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="MDKV GUI")

    @app.middleware("http")
    async def local_requests_only(request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Browser source checks are not authentication or same-user isolation.
        hosts = request.headers.getlist("host")
        try:
            if len(hosts) != 1:
                raise ValueError("invalid Host")
            destination = _origin(f"{request.url.scheme}://{hosts[0]}")
            if destination[1] not in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("untrusted Host")
        except ValueError:
            return JSONResponse({"detail": "untrusted Host"}, status_code=400)
        if request.url.path == "/api" or request.url.path.startswith("/api/"):
            if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
                return JSONResponse({"detail": "cross-site API access denied"}, status_code=403)
            origins = request.headers.getlist("origin")
            if origins:
                try:
                    if len(origins) != 1 or _origin(origins[0]) != destination:
                        raise ValueError("foreign origin")
                except ValueError:
                    return JSONResponse({"detail": "foreign Origin API access denied"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if response.headers.get("content-type", "").startswith("text/html"):
            if request.url.path.startswith("/api/"):
                response.headers["Content-Security-Policy"] = (
                    "sandbox; default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'"
                )
            else:
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self'; img-src 'self' data:; object-src 'none'; "
                    "base-uri 'none'; frame-ancestors 'none'"
                )
        return response

    static_root = static_dir or Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

    @app.get("/favicon.ico")
    def favicon() -> Response:
        svg_path = static_root / "favicon.svg"
        if svg_path.exists():
            return Response(content=svg_path.read_text(encoding="utf-8"), media_type="image/svg+xml")
        return Response(content="", media_type="image/svg+xml")

    @app.get("/", response_class=HTMLResponse)
    def root() -> str:
        return (static_root / "index.html").read_text(encoding="utf-8")

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        return {"loaded": state.doc is not None, "path": str(state.path) if state.path else None,
                "tracks": list(state.doc.tracks) if state.doc else []}

    @app.get("/api/library")
    def list_library() -> dict[str, Any]:
        """List installed canonical examples without generating files."""
        try:
            definitions = sorted(
                (p for p in example_definitions_dir().iterdir() if p.is_file() and p.name.endswith(".yaml")),
                key=lambda p: p.name,
            )
            return {"files": [{"name": p.name, "id": f"library:{p.name[:-5]}",
                               "path": f"library:{p.name[:-5]}"} for p in definitions]}
        except (OSError, ValueError) as exc:
            raise HTTPException(400, f"failed to list examples: {exc}") from exc

    @app.post("/api/open")
    def open_file(payload: dict[str, Any]) -> dict[str, Any]:
        value = _string(payload.get("path"), "path", nonempty=True)
        if value.startswith("library:"):
            try:
                doc = load_example_document(value[len("library:"):] + ".yaml")
            except FileNotFoundError as exc:
                raise HTTPException(404, "library example not found") from exc
            except Exception as exc:
                raise HTTPException(400, f"failed to open library example: {exc}") from exc
            p = None
        else:
            p = _path(value)
            doc = _load(p)
        state.path, state.doc = p, doc
        return {"ok": True, "title": doc.title, "tracks": list(doc.tracks)}

    @app.post("/api/save")
    def save(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        doc = _require_doc()
        destination = _path(payload["path"]) if payload is not None and "path" in payload else state.path
        if destination is None:
            raise HTTPException(400, "choose a local file path to save this document")
        try:
            save_mdkv(doc, destination)
        except Exception as exc:
            raise HTTPException(400, f"failed to save document: {exc}") from exc
        state.path = destination
        return {"ok": True}

    @app.get("/api/document")
    def get_document() -> dict[str, Any]:
        doc = _require_doc()
        return {"title": doc.title, "authors": doc.authors, "version": doc.version,
                "created": doc.created.isoformat(),
                "tracks": [{"id": t.track_id, "type": t.track_type, "language": t.language,
                            "path": t.path, "content": t.content} for t in doc.tracks.values()]}

    @app.get("/api/tracks")
    def list_tracks() -> list[dict[str, Any]]:
        return [{"id": t.track_id, "type": t.track_type, "language": t.language, "path": t.path}
                for t in _require_doc().tracks.values()]

    @app.get("/api/track")
    def get_track(track_id: str) -> dict[str, Any]:
        t = _require_doc().get_track(track_id)
        if t is None:
            raise HTTPException(404, "track not found")
        return {"id": t.track_id, "type": t.track_type, "language": t.language,
                "path": t.path, "content": t.content}

    @app.post("/api/document")
    def update_document(payload: dict[str, Any]) -> dict[str, Any]:
        doc = _require_doc()
        # Validate the entire request before changing any of the live document.
        for name in ("title", "version"):
            if name in payload:
                _string(payload[name], name)
        if "authors" in payload:
            if not isinstance(payload["authors"], list) or not all(isinstance(x, str) for x in payload["authors"]):
                raise HTTPException(422, "authors must be a list of strings")
        if "metadata" in payload:
            metadata = payload["metadata"]
            if not isinstance(metadata, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()):
                raise HTTPException(422, "metadata must map strings to strings")
        for name in ("title", "version"):
            if name in payload:
                setattr(doc, name, payload[name])
        if "authors" in payload:
            doc.authors = list(payload["authors"])
        if "metadata" in payload:
            doc.metadata.clear()
            doc.metadata.update(payload["metadata"])
        return {"ok": True}

    @app.post("/api/track")
    def upsert_track(payload: dict[str, Any]) -> dict[str, Any]:
        doc = _require_doc()
        track_id = _string(payload.get("id"), "id", nonempty=True)
        t = doc.get_track(track_id)
        track_type, language, content = _track_values(payload, t)
        if t is None:
            try:
                doc.add_track(Track(track_id, track_type, language, f"tracks/{track_id}.md", content))
            except (ValueError, ValidationError) as exc:
                raise HTTPException(400, str(exc)) from exc
        else:
            t.track_type, t.language, t.content = track_type, language, content
        return {"ok": True}

    @app.put("/api/track")
    def update_track(payload: dict[str, Any]) -> dict[str, Any]:
        # Canonical single-track editing never creates a track from body text.
        doc = _require_doc()
        track_id = _string(payload.get("id"), "id", nonempty=True)
        t = doc.get_track(track_id)
        if t is None:
            raise HTTPException(404, "track not found")
        track_type, language, content = _track_values(payload, t)
        t.track_type, t.language, t.content = track_type, language, content
        return {"ok": True}

    @app.post("/api/move-track")
    def move_track(payload: dict[str, Any]) -> dict[str, Any]:
        doc = _require_doc()
        track_id = _string(payload.get("track_id"), "track_id", nonempty=True)
        after_id = payload.get("after_id")
        if after_id is not None:
            _string(after_id, "after_id", nonempty=True)
        try:
            doc.move_track(track_id, after_id)
        except KeyError as exc:
            raise HTTPException(404, "track not found") from exc
        return {"ok": True, "track_ids": doc.track_ids}

    @app.get("/api/validate-track")
    def validate_single_track(track_id: str) -> dict[str, Any]:
        t = _require_doc().get_track(track_id)
        if t is None:
            raise HTTPException(404, "track not found")
        from mdkv.core.validate import validate_track
        try:
            issues = validate_track(t)
            return {"ok": True, "warnings": [{"level": i.level, "message": i.message, "track_id": i.track_id} for i in issues]}
        except ValidationError as exc:
            return {"ok": False, "error": str(exc)}

    @app.delete("/api/track")
    def delete_track(track_id: str) -> dict[str, Any]:
        try:
            _require_doc().remove_track(track_id)
        except KeyError as exc:
            raise HTTPException(404, "track not found") from exc
        return {"ok": True}

    @app.get("/api/render/html", response_class=HTMLResponse)
    def render_html() -> str:
        return _render("\n\n".join(t.content for t in _require_doc().tracks.values() if t.track_type == "primary"))

    @app.get("/api/render/markdown")
    def render_markdown() -> JSONResponse:
        return JSONResponse({"markdown": to_markdown(_require_doc())})

    @app.get("/api/render/track_html", response_class=HTMLResponse)
    def render_track_html(track_id: str) -> str:
        t = _require_doc().get_track(track_id)
        if t is None:
            raise HTTPException(404, "track not found")
        return _render(t.content)

    @app.get("/api/render/all_html", response_class=HTMLResponse)
    def render_all_html() -> str:
        return _render("\n\n".join(t.content for t in _require_doc().tracks.values()))

    @app.post("/api/render/tracks_html", response_class=HTMLResponse)
    def render_tracks_html(payload: dict[str, Any]) -> str:
        doc = _require_doc()
        ids = payload.get("track_ids")
        if ids is None:
            return _render("\n\n".join(t.content for t in doc.tracks.values()))
        if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            raise HTTPException(422, "track_ids must be a list of strings")
        idset = set(ids)
        return _render("\n\n".join(t.content for t in doc.tracks.values() if t.track_id in idset))

    @app.post("/api/validate")
    def validate() -> dict[str, Any]:
        try:
            issues = validate_document(_require_doc())
            return {"ok": True, "warnings": [{"level": i.level, "message": i.message, "track_id": i.track_id}
                                             for i in issues if i.level == "WARN"]}
        except ValidationError as exc:
            return {"ok": False, "error": str(exc)}

    @app.get("/api/search")
    def search(pattern: str, types: str = "", languages: str = "", case_insensitive: bool = False,
               limit: int = 0) -> dict[str, Any]:
        doc = _require_doc()
        tt = [t.strip() for t in types.split(",") if t.strip()] or None
        langs = [lang.strip() for lang in languages.split(",") if lang.strip()] or None
        if limit < 0:
            raise HTTPException(400, "limit must be nonnegative")
        try:
            matches = search_document(doc, pattern=pattern, track_types=tt, languages=langs,
                                      case_insensitive=case_insensitive, limit=limit if limit else None)
        except re.error as exc:
            raise HTTPException(400, f"invalid regex pattern: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(400, f"invalid search: {exc}") from exc
        except TimeoutError as exc:
            raise HTTPException(408, "search exceeded its time limit") from exc
        return {"matches": [{"track_id": m.track_id, "track_type": m.track_type, "language": m.language,
                             "start": m.start, "end": m.end, "extract": m.extract} for m in matches]}

    @app.get("/api/stats")
    def stats() -> dict[str, Any]:
        return compute_stats(_require_doc()).to_dict()

    @app.get("/api/document/json")
    def get_document_json() -> JSONResponse:
        return JSONResponse(_require_doc().to_dict())

    @app.post("/api/import")
    def import_track(payload: dict[str, Any]) -> dict[str, Any]:
        doc = _require_doc()
        p = _path(payload.get("path"))
        track_id = _string(payload.get("id"), "id", nonempty=True)
        track_type, language, _ = _track_values(payload)
        if doc.get_track(track_id) is not None:
            raise HTTPException(400, f"duplicate track_id: {track_id}")
        try:
            content = p.read_text(encoding="utf-8")
            track = Track(track_id, track_type, language, f"tracks/{track_id}.md", content)
            doc.add_track(track)
        except FileNotFoundError as exc:
            raise HTTPException(404, "file not found") from exc
        except (OSError, UnicodeError, ValueError, ValidationError) as exc:
            raise HTTPException(400, f"failed to import track: {exc}") from exc
        return {"ok": True, "track_id": track_id}

    @app.post("/api/diff")
    def diff(payload: dict[str, Any]) -> dict[str, Any]:
        doc_a = _require_doc()
        doc_b = _load(_path(payload.get("path")))
        return diff_documents(doc_a, doc_b).to_dict()

    @app.get("/api/diff/view", response_class=HTMLResponse)
    def diff_view(other_path: str) -> str:
        import difflib
        doc_a = _require_doc()
        doc_b = _load(_path(other_path))
        return str(difflib.HtmlDiff(tabsize=2).make_table(
            to_markdown(doc_a).splitlines(keepends=True), to_markdown(doc_b).splitlines(keepends=True),
            fromdesc=escape(doc_a.title), todesc=escape(doc_b.title), context=True))

    return app


def run(host: str = "127.0.0.1", port: int = 8000, path: str | None = None) -> None:
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("GUI binding must use a loopback host: 127.0.0.1, localhost or ::1")
    import uvicorn

    app = create_app()
    if path:
        p = Path(path).expanduser()
        doc = load_mdkv(p)
        state.path, state.doc = p, doc
    uvicorn.run(app, host=host, port=port)
