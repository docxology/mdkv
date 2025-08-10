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

## Track Operations

```bash
# list tracks as JSON
uv run mdkv list-tracks doc.mdkv

# add a commentary track
uv run mdkv add-track doc.mdkv --id notes --type commentary --lang "" --content "Note"

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

# export HTML of primary track
uv run mdkv export --html doc.mdkv > primary.html

# launch GUI
uv run mdkv gui --path doc.mdkv
```

GUI notes:
- The preview supports multi-select via checkboxes (All or any subset).
- Backend also exposes `POST /api/render/tracks_html` to render a specific subset by `track_ids`.

## Metadata

```bash
uv run mdkv set-meta doc.mdkv author "Another"
uv run mdkv get-meta doc.mdkv author
```

## Search

```bash
uv run mdkv search doc.mdkv --pattern beta --types primary --languages en
```
