# Examples

Run with `uv run python examples/<script>.py`.

- `create_doc.py`: create a new `.mdkv` file with multiple tracks and links.
- `validate_doc.py`: validate an `.mdkv` file.
- `export_html.py`: export HTML from a `.mdkv` file.
- `search_docs.py`: search within a `.mdkv` file.
- `roundtrip.py`: save then load a document.
- `logged_workflow.py`: full workflow that logs steps and writes outputs to `workflow_out/`.
- `load_from_yaml.py`: build a `.mdkv` from a YAML definition in `library/definitions/`.

Tip: launch the GUI with a demo document:

```bash
python3 run_gui.py --path demo/demo.mdkv
```
