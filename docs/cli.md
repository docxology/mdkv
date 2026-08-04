# CLI Reference

```bash
uv run mdkv --help

# or use python -m
python -m mdkv --help
```

## Version and License

```bash
# show version
uv run mdkv --version

# show license info
uv run mdkv license
```

## Init, Info, Validate

```bash
uv run mdkv init --title "Doc" --author "You" --out doc.mdkv
uv run mdkv info doc.mdkv
uv run mdkv validate doc.mdkv
```

Validation reports both ERRORs (which cause exit code 1) and WARNs (which
are informational). Warnings include: empty track content, code tracks
without fenced blocks, translation tracks without language, bad version
format, and multiple primary tracks.

### Validate with JSON output

```bash
# human-readable (default)
uv run mdkv validate doc.mdkv

# JSON output for CI/automation
uv run mdkv validate doc.mdkv --json
```

JSON output returns `{"ok": true, "issues": [...]}` or `{"ok": false, "error": "..."}`.

### Info with table format

```bash
# JSON (default)
uv run mdkv info doc.mdkv

# Human-readable table
uv run mdkv info doc.mdkv --format table
```

## Import

```bash
# import a Markdown file as a new .mdkv document
uv run mdkv import README.md --out imported.mdkv --title "Imported" --author "You"

# import with custom track type and language
uv run mdkv import notes.md --out notes.mdkv --title "Notes" --author "You" \
    --track-id notes --track-type commentary --language en
```

## Track Operations

```bash
# list tracks as JSON
uv run mdkv list-tracks doc.mdkv

# add a commentary track
uv run mdkv add-track doc.mdkv --id notes --type commentary --lang "" --content "Note"

# add a track from a file (overrides --content)
uv run mdkv add-track doc.mdkv --id notes --type commentary --file notes.md

# remove a track
uv run mdkv remove-track doc.mdkv --id notes

# rename track id
uv run mdkv rename-track doc.mdkv --old-id notes --new-id commentary

# update track content
uv run mdkv update-track doc.mdkv --id commentary --content "Updated note"

# update track content from a file
uv run mdkv update-track doc.mdkv --id primary --file updated.md

# rename id and then export a subset
uv run mdkv rename-track doc.mdkv --old-id commentary --new-id notes
uv run mdkv export-tracks doc.mdkv --types primary,commentary > exported.md

# move a track to a new position
uv run mdkv move-track doc.mdkv --id notes --after-id primary
uv run mdkv move-track doc.mdkv --id notes   # move to first position
```

## History & Incremental Save

```bash
# show revision history for a specific track (revision tracks whose id matches)
uv run mdkv history doc.mdkv --id rev1

# save the document to disk, reusing unchanged track content
uv run mdkv save-incremental doc.mdkv
```

`history --id <track>` returns only the `revision`-type tracks whose `track_id`
equals `<track>`; if none match it prints a message and exits 0. Revisions are
expected to be stored as `revision` tracks. `save-incremental` rewrites the
container atomically, carrying unchanged track content over instead of
re-encoding it, and falls back to a full save if the file is missing or
corrupt.

## Export

```bash
# Markdown (all tracks, default)
uv run mdkv export doc.mdkv

# HTML with specific track types
uv run mdkv export doc.mdkv --html --types primary,commentary

# Full document as JSON
uv run mdkv export doc.mdkv --format json

# JSON with track type filter
uv run mdkv export doc.mdkv --format json --types primary

# PDF/EPUB/DOCX (requires pandoc installed)
uv run mdkv export doc.mdkv --format pdf
uv run mdkv export doc.mdkv --format epub
uv run mdkv export doc.mdkv --format docx

# Markdown with YAML frontmatter
uv run mdkv export doc.mdkv --metadata-header > out.md

# Export tracks as individual files to a directory
uv run mdkv export --out-dir tracks_out/ doc.mdkv

# launch GUI
uv run mdkv gui --path doc.mdkv
```

GUI notes:
- The preview supports multi-select via checkboxes (All or any subset).
- Backend also exposes `POST /api/render/tracks_html` to render a specific subset by `track_ids`.

## Diff

```bash
# compare two .mdkv documents
uv run mdkv diff doc_v1.mdkv doc_v2.mdkv
```

Reports changes in title, authors, version, tracks (added/removed/modified),
and metadata (added/removed/changed). A track is considered "modified" if its
content, type, language, or path differs. Outputs "No differences found." if
identical.

## Stats

```bash
uv run mdkv stats doc.mdkv
```

Shows track count, types breakdown, languages, metadata keys, and total
character/line counts.

## Metadata

```bash
uv run mdkv set-meta doc.mdkv author "Another"
uv run mdkv get-meta doc.mdkv author
```

## Search

```bash
# case-sensitive search (default)
uv run mdkv search doc.mdkv --pattern beta --types primary --languages en

# case-insensitive search
uv run mdkv search doc.mdkv --pattern hello -i

# limit number of matches
uv run mdkv search doc.mdkv --pattern "." --limit 10
```

Search results include `track_id`, `track_type`, `language`, `start`, `end`,
and `extract` for each match. Invalid regex patterns return a clean error
message with exit code 1.

## Batch Operations

```bash
# validate multiple documents
uv run mdkv batch validate doc1.mdkv doc2.mdkv doc3.mdkv

# validate with JSON output
uv run mdkv batch validate *.mdkv --json

# show stats for multiple documents
uv run mdkv batch stats doc1.mdkv doc2.mdkv
```

## Shell Completions

```bash
# generate completion instructions for bash, zsh, or fish
uv run mdkv completions bash
uv run mdkv completions zsh
uv run mdkv completions fish
```

## Error Handling

All CLI commands that load `.mdkv` files catch `FileNotFoundError` and
`MDKVFormatError` and print clean error messages to stderr with exit code 1,
instead of Python tracebacks.
