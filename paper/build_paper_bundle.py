#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import platform
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from mdkv import (
    MDKVDocument,
    Track,
    export_to_files,
    save_mdkv,
    to_html,
    to_markdown,
    validate_document,
)
from mdkv.core.errors import (
    ValidationError,
)

def split_front_matter_and_body(markdown_text: str) -> tuple[dict[str, Any], str]:
    """Parse explicit YAML frontmatter without silently discarding bad metadata."""
    lines = markdown_text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, markdown_text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            try:
                data = yaml.safe_load("".join(lines[1:idx]))
            except yaml.YAMLError as exc:
                raise ValueError(f"invalid manuscript frontmatter: {exc}") from exc
            if not isinstance(data, dict):
                raise ValueError("manuscript frontmatter must be a mapping")
            return data, "".join(lines[idx + 1:])
    raise ValueError("manuscript frontmatter has no closing delimiter")


def strip_leading_html_comments(markdown_body: str) -> str:
    """Remove any leading HTML comments from the start of the body.

    This is resilient to multiple consecutive comments and arbitrary whitespace.
    """
    text = markdown_body
    while text.lstrip().startswith("<!--"):
        start = text.index("<!--")
        end = text.find("-->", start)
        if end == -1:
            break
        text = text[end + 3:]
    return text


def ensure_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value]
    if isinstance(value, list) and value and all(isinstance(v, str) and v.strip() for v in value):
        return list(value)
    raise ValueError("manuscript must declare a nonempty author or authors list")


def build_document(markdown_path: Path, language: str | None) -> MDKVDocument:
    text = markdown_path.read_text(encoding="utf-8")
    fm, body = split_front_matter_and_body(text)
    body = strip_leading_html_comments(body)

    title = fm.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("manuscript must declare its title in frontmatter")
    authors = ensure_list(fm.get("author") or fm.get("authors"))
    created_value = fm.get("created")
    if isinstance(created_value, datetime):
        created = created_value
    elif isinstance(created_value, str):
        created = datetime.fromisoformat(created_value)
    else:
        raise ValueError("manuscript must declare an ISO-8601 created timestamp")
    if created.tzinfo is None:
        raise ValueError("manuscript created timestamp must include a timezone")

    metadata: dict[str, str] = {}
    for key in ("doi", "orcid", "email", "date"):
        if key in fm and fm[key] is not None:
            metadata[key] = str(fm[key])

    track = Track(
        track_id="primary",
        track_type="primary",
        language=language,
        path="tracks/primary.md",
        content=body,
    )

    doc = MDKVDocument(
        title=title,
        authors=authors,
        created=created,
        version=str(fm.get("version", "0.1")),
    )
    doc.metadata.update(metadata)
    doc.add_track(track)
    # Compute and record checksum for primary
    doc.metadata["sha256_tracks/primary.md"] = hashlib.sha256(track.content.encode("utf-8")).hexdigest()

    # Auto-extract References section (if present) as a separate reference track
    # This showcases multi-track export from a single authored source
    refs = extract_section_by_heading(body, heading=r"^##\s+References\s*$")
    if refs and refs.strip():
        ref_track = Track(
            track_id="references",
            track_type="reference",
            language=None,
            path="tracks/references.md",
            content=refs.strip() + "\n",
        )
        doc.add_track(ref_track)
        doc.metadata["sha256_tracks/references.md"] = hashlib.sha256(ref_track.content.encode("utf-8")).hexdigest()
    return doc


def extract_section_by_heading(text: str, heading: str) -> str:
    """Extract a markdown section by its H2 heading regex up to the next H2 or end.

    - heading: regex string that matches the full heading line (e.g., r"^##\\s+References\\s*$")
    """
    lines = text.splitlines()
    start_idx = None
    pattern = re.compile(heading, re.IGNORECASE)
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            start_idx = i + 1
            break
    if start_idx is None:
        return ""
    # find next H2 heading (line starting with '## ')
    end_idx = len(lines)
    for j in range(start_idx, len(lines)):
        if lines[j].startswith("## "):
            end_idx = j
            break
    return "\n".join(lines[start_idx:end_idx])


def _run_git(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            check=False,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=60,
            text=True,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def clone_repo(repo_url: str, dest_dir: Path, depth: int = 1) -> str | None:
    if dest_dir.exists() and any(dest_dir.iterdir()):
        code, observed_url, _ = _run_git(["remote", "get-url", "origin"], cwd=dest_dir)
        if code != 0 or observed_url.removesuffix(".git").rstrip("/") != repo_url.removesuffix(".git").rstrip("/"):
            raise ValueError("existing clone origin does not match the requested repository")
        code, out, _ = _run_git(["rev-parse", "HEAD"], cwd=dest_dir)
        return out if code == 0 else None
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    code, _, err = _run_git(["clone", "--depth", str(depth), "--no-tags", repo_url, str(dest_dir)])
    if code != 0:
        print(f"Warning: git clone failed: {err}")
        return None
    code, out, _ = _run_git(["rev-parse", "HEAD"], cwd=dest_dir)
    return out if code == 0 else None


def get_local_repo_commit(cwd: Path) -> str | None:
    code, out, _ = _run_git(["rev-parse", "HEAD"], cwd=cwd)
    return out if code == 0 else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Build MDKV publication bundle for the paper")
    parser.add_argument("--markdown", default=str(Path(__file__).with_name("mdkv_paper.md")), help="Path to the paper markdown source")
    parser.add_argument("--out", default=str(Path(__file__).with_name("paper.mdkv")), help="Output .mdkv file path")
    parser.add_argument("--bundle-dir", default=str(Path(__file__).with_name("_bundle")), help="Directory to write exported files")
    parser.add_argument("--lang", default="en", help="Language code for the primary track")
    parser.add_argument("--repo-url", default="https://github.com/docxology/mdkv", help="Repository URL to clone into the bundle")
    parser.add_argument("--clone-dir", default=str(Path(__file__).with_name("_bundle") / "src_repo"), help="Directory to clone the repository into (inside bundle by default)")
    parser.add_argument("--no-clone", action="store_true", help="Skip cloning the repository")
    args = parser.parse_args()

    markdown_path = Path(args.markdown)
    output_mdkv = Path(args.out)
    bundle_dir = Path(args.bundle_dir)

    if not markdown_path.exists():
        print(f"Markdown source not found: {markdown_path}", file=sys.stderr)
        return 1

    try:
        doc = build_document(markdown_path, args.lang)
    except (ValueError, OSError) as exc:
        print(f"Manuscript metadata failed: {exc}", file=sys.stderr)
        return 1

    # Capture source custody before clone/bundle generation dirties the tree.
    builder_root = Path(__file__).resolve().parents[1]
    local_commit = get_local_repo_commit(builder_root)
    status_code, status_output, _ = _run_git(["status", "--porcelain"], cwd=builder_root)
    builder_dirty = bool(status_output) if status_code == 0 else None
    cloned_commit: str | None = None
    if not args.no_clone:
        cloned_commit = clone_repo(args.repo_url, Path(args.clone_dir))

    if cloned_commit:
        doc.metadata["cloned_repo_url"] = args.repo_url
        doc.metadata["cloned_repo_commit"] = cloned_commit
    if local_commit:
        doc.metadata["builder_repo_commit"] = local_commit

    # Validate before saving
    try:
        validate_document(doc)
    except ValidationError as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        return 1

    expected_tracks = {f"{track.track_id}.md" for track in doc.tracks.values()}
    stale_tracks = {p.name for p in (bundle_dir / "tracks").glob("*.md")} - expected_tracks
    if stale_tracks:
        print(f"Unexpected prior track artifacts (preserved): {sorted(stale_tracks)}", file=sys.stderr)
        return 1

    figure_source = Path(__file__).with_name("figures")
    figure_files = sorted(
        path.relative_to(figure_source)
        for path in figure_source.rglob("*") if path.is_file()
    ) if figure_source.is_dir() else []
    stale_figures = {
        path.relative_to(bundle_dir / "figures")
        for path in (bundle_dir / "figures").rglob("*") if path.is_file()
    } - set(figure_files)
    if stale_figures:
        print(f"Unexpected prior figure artifacts (preserved): {sorted(map(str, stale_figures))}", file=sys.stderr)
        return 1

    # Save .mdkv
    save_mdkv(doc, output_mdkv)

    # Exports
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "paper.md").write_text(
        to_markdown(doc, include_track_types=["primary"], metadata_header=True), encoding="utf-8"
    )
    (bundle_dir / "paper.html").write_text(to_html(doc), encoding="utf-8")
    for relative in figure_files:
        destination = bundle_dir / "figures" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((figure_source / relative).read_bytes())
    export_to_files(doc, bundle_dir / "tracks")

    # Emit bundle info
    bundle_info = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_markdown": markdown_path.name,
        "source_sha256": hashlib.sha256(markdown_path.read_bytes()).hexdigest(),
        "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "output_mdkv": output_mdkv.name,
        "repo_url": args.repo_url,
        "cloned_commit": cloned_commit,
        "builder_commit": local_commit,
        "checksum_root": "parent of bundle directory",
        "builder_dirty": builder_dirty,
        "python": platform.python_version(),
        "mdkv_version": importlib.metadata.version("mdkv"),
        "markdown_it_version": importlib.metadata.version("markdown-it-py"),
        "pyyaml_version": importlib.metadata.version("pyyaml"),
        "uv_lock_sha256": hashlib.sha256(
            Path(__file__).resolve().parents[1].joinpath("uv.lock").read_bytes()
        ).hexdigest(),
        "reproducibility": "text composition for fixed inputs/runtime; ZIP and generation timestamps vary",
    }
    (bundle_dir / "BUNDLE_INFO.yaml").write_text(yaml.safe_dump(bundle_info, sort_keys=False), encoding="utf-8")

    # Checksums for bundle artifacts
    def _sha256_file(p: Path) -> str:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    artifacts = [
        output_mdkv, bundle_dir / "paper.md", bundle_dir / "paper.html",
        bundle_dir / "BUNDLE_INFO.yaml",
        *(bundle_dir / "tracks" / name for name in sorted(expected_tracks)),
        *(bundle_dir / "figures" / name for name in figure_files),
    ]
    checksums = {
        os.path.relpath(path.resolve(), bundle_dir.resolve().parent): _sha256_file(path)
        for path in artifacts
    }
    (bundle_dir / "CHECKSUMS.yaml").write_text(yaml.safe_dump(checksums, sort_keys=True), encoding="utf-8")

    print(f"Wrote: {output_mdkv}")
    print(f"Bundle: {bundle_dir}/ (paper.md, paper.html, tracks/, figures/, BUNDLE_INFO.yaml, CHECKSUMS.yaml; no PDF)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


