#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import yaml

from mdkv import (
    MDKVDocument,
    Track,
    save_mdkv,
    to_markdown,
    to_html,
    export_to_files,
    validate_document,
)
from mdkv.core.errors import (
    ValidationError,
)


def parse_front_matter(markdown_text: str) -> Dict[str, Any]:
    """Parse YAML front matter if present and return it as a dict (else {})."""
    lines = markdown_text.splitlines()
    if len(lines) >= 3 and lines[0].strip() == "---":
        # find closing '---'
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                fm_text = "\n".join(lines[1:idx])
                try:
                    data = yaml.safe_load(fm_text) or {}
                    return data if isinstance(data, dict) else {}
                except Exception:
                    return {}
    return {}


def split_front_matter_and_body(markdown_text: str) -> tuple[Dict[str, Any], str]:
    """Return (front_matter_dict, body_without_front_matter)."""
    lines = markdown_text.splitlines()
    if len(lines) >= 3 and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                fm_text = "\n".join(lines[1:idx])
                try:
                    data = yaml.safe_load(fm_text) or {}
                    if not isinstance(data, dict):
                        data = {}
                except Exception:
                    data = {}
                body = "\n".join(lines[idx + 1 :])
                return data, body
    return {}, markdown_text


def strip_leading_html_comments(markdown_body: str) -> str:
    """Remove any leading HTML comments from the start of the body.

    This is resilient to multiple consecutive comments and arbitrary whitespace.
    """
    text = markdown_body.lstrip()
    while text.startswith("<!--"):
        end = text.find("-->")
        if end == -1:
            break
        text = text[end + 3 :].lstrip()
    return text


def ensure_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def build_document(markdown_path: Path, language: str | None) -> MDKVDocument:
    text = markdown_path.read_text(encoding="utf-8")
    fm, body = split_front_matter_and_body(text)
    body = strip_leading_html_comments(body)

    title = str(fm.get("title") or markdown_path.stem)
    authors = ensure_list(fm.get("author") or fm.get("authors") or "Unknown")
    created = datetime.now(timezone.utc)

    metadata: Dict[str, str] = {}
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
        version="0.1",
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
            text=True,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "git not found"


def clone_repo(repo_url: str, dest_dir: Path, depth: int = 1) -> str | None:
    if dest_dir.exists() and any(dest_dir.iterdir()):
        # assume already cloned
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

    doc = build_document(markdown_path, args.lang)

    # Optionally clone repo and record commit hash
    cloned_commit: str | None = None
    local_commit: str | None = None
    if not args.no_clone:
        cloned_commit = clone_repo(args.repo_url, Path(args.clone_dir))
    # local commit (builder repo), if any
    local_commit = get_local_repo_commit(Path(__file__).resolve().parents[1])

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

    # Save .mdkv
    save_mdkv(doc, output_mdkv)

    # Exports
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "paper.md").write_text(to_markdown(doc), encoding="utf-8")
    (bundle_dir / "paper.html").write_text(to_html(doc), encoding="utf-8")
    export_to_files(doc, bundle_dir / "tracks")

    # Emit bundle info
    bundle_info = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_markdown": str(markdown_path.resolve()),
        "output_mdkv": str(output_mdkv.resolve()),
        "repo_url": args.repo_url,
        "cloned_commit": cloned_commit,
        "builder_commit": local_commit,
    }
    (bundle_dir / "BUNDLE_INFO.yaml").write_text(yaml.safe_dump(bundle_info, sort_keys=False), encoding="utf-8")

    # Checksums for bundle artifacts
    def _sha256_file(p: Path) -> str:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    checksums = {
        "paper.mdkv": _sha256_file(output_mdkv),
        "_bundle/paper.md": _sha256_file(bundle_dir / "paper.md"),
        "_bundle/paper.html": _sha256_file(bundle_dir / "paper.html"),
    }
    tracks_dir = bundle_dir / "tracks"
    for tfile in sorted(tracks_dir.glob("*.md")):
        checksums[f"_bundle/tracks/{tfile.name}"] = _sha256_file(tfile)
    (bundle_dir / "CHECKSUMS.yaml").write_text(yaml.safe_dump(checksums, sort_keys=True), encoding="utf-8")

    print(f"Wrote: {output_mdkv}")
    print(f"Bundle: {bundle_dir}/ (paper.md, paper.html, tracks/, BUNDLE_INFO.yaml, src_repo/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


