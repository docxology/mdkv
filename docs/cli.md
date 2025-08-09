# CLI Reference

```bash
uv run mdkv --help
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
```

## Export

```bash
# export selected track types to Markdown
uv run mdkv export-tracks doc.mdkv --types primary,commentary > exported.md

# export HTML of primary track
uv run mdkv export --html doc.mdkv > primary.html
```

## Metadata

```bash
uv run mdkv set-meta doc.mdkv author "Another"
uv run mdkv get-meta doc.mdkv author
```

## Search

```bash
uv run mdkv search doc.mdkv --pattern beta --types primary --languages en
```
