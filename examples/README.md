# Examples

Run with `python examples/<script>.py` in the provisioned project environment.
No dependency installation or environment synchronization is performed by the examples.

- `create_doc.py`: create a new `.mdkv` file with multiple tracks and links.
- `validate_doc.py`: validate an `.mdkv` file.
- `export_html.py`: export HTML from a `.mdkv` file.
- `search_docs.py`: search within a `.mdkv` file.
- `roundtrip.py`: save then load a document.
- `logged_workflow.py`: full workflow that logs steps and writes outputs to a fresh `workflow_out-*/` directory, including JSON search results.
- `load_from_yaml.py`: build a `.mdkv` from a YAML definition in `library/definitions/`.
- `import_example.py`: import a Markdown file as a new `.mdkv` document, then validate.
- `diff_example.py`: create two .mdkv documents, diff them, and print changes.
- `stats_example.py`: print statistics and demonstrate `to_dict`/`from_dict` roundtrip.
- `diff_stats_example.py`: demonstrate `diff_documents()` + `compute_stats()` together.
- `record_gui_demo.py`: record a short GUI demo video (requires Playwright).

Tip: launch the GUI with a demo document:

```bash
python run_gui.py --path demo/demo.mdkv
```

The import, diff, statistics, and roundtrip demonstrations use owned temporary
directories and remove only their own outputs. `create_doc.py`, `export_html.py`,
and `record_gui_demo.py` refuse to replace existing destination files. The YAML
builder uses the canonical library builder (including the definition's `created`
value); its explicitly supplied output path is the caller's chosen destination.
The GUI recorder additionally requires Playwright and its Chromium installation;
it is not part of the dependency-only CLI demonstrations.
