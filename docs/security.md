# Security

MDKV is designed with defense-in-depth principles. This page documents the
security measures implemented across the codebase.

## Path Traversal Prevention

`export_to_files()` uses `_safe_filename()` to sanitize track IDs before
deriving filenames. This prevents a malicious `track_id` like
`../../etc/passwd` from writing files outside the output directory.

```python
from mdkv.services.export import _safe_filename

_safe_filename("../../etc/passwd")  # → "passwd"
_safe_filename("foo/bar")          # → "bar"
_safe_filename("normal_id")        # → "normal_id"
```

## YAML Injection Prevention

The `metadata_header` export option uses `yaml.safe_dump()` for frontmatter
generation. This properly quotes values that contain YAML special characters
(colons, brackets, etc.), preventing YAML injection via crafted titles or
metadata values.

## HTML Comment Injection Prevention

Track metadata in export headers (`<!-- track:... -->`) is sanitized by
stripping `-->` sequences from `track_id`, `track_type`, and `language`
before embedding in HTML comments. This prevents an attacker from breaking
out of the comment context and injecting arbitrary content.

## Container Integrity

`save_mdkv()` detects and rejects duplicate track paths before writing the
ZIP container. Without this check, `zf.writestr()` would silently overwrite
one track's content with another's, causing data loss.

`load_mdkv()` wraps `ValueError` from `Track` construction in
`MDKVFormatError`, so corrupt manifests with invalid track types produce
clean errors instead of unhandled exceptions.

## Input Validation

- The GUI API validates `track_type` on both creation and mutation of tracks
  via `allowed_track_types()`.
- Invalid regex patterns in search return clean `re.error` messages (HTTP 400
  in GUI, exit code 1 in CLI) instead of crashing.
- Reserved track IDs (`all`, `none`, `null`, `true`, `false`) generate
  validation warnings to prevent confusing the GUI's track selection logic.

## CLI Error Handling

All CLI commands that load `.mdkv` files catch `FileNotFoundError` and
`MDKVFormatError` and print clean error messages to stderr with exit code 1,
instead of Python tracebacks. This prevents information leakage in production.

## Attack Surface

- The GUI server binds to `127.0.0.1` by default (localhost only)
- No authentication is implemented — the GUI is designed for local use
- The `POST /api/open` endpoint accepts arbitrary file paths via `expanduser()`
  — this is intentional for local use but should be restricted in any
  networked deployment
