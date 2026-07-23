# CLI Reference

```bash
uv run mdkv --help
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

# remove a track
uv run mdkv remove-track doc.mdkv --id notes

# rename track id
uv run mdkv rename-track doc.mdkv --old-id notes --new-id commentary

# update track content
uv run mdkv update-track doc.mdkv --id commentary --content "Updated note"

# rename id and then export a subset
uv run mdkv rename-track doc.mdkv --old-id commentary --new-id notes
uv run mdkv export-tracks doc.mdkv --types primary,commentary > exported.md
```

## Export & GUI

```bash
# export selected track types to Markdown
uv run mdkv export-tracks doc.mdkv --types primary,commentary > exported.md

# export HTML of primary track (default)
uv run mdkv export --html doc.mdkv > primary.html

# export HTML with specific track types
uv run mdkv export --html --types primary,commentary doc.mdkv > combined.html

# export tracks as individual files to a directory
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
and metadata (added/removed/changed). Outputs "No differences found." if
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
uv run mdkv search doc.mdkv --pattern beta --types primary --languages en
```

Search results include `track_id`, `track_type`, `language`, `start`, `end`,
and `extract` for each match.
