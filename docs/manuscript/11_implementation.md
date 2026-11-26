# Implementation Notes: Runtime, Packaging and Testing

- Python 3.11+; dataclasses and type hints; explicit naming.
- Packaging: public API re‑exports; CLI entry point `mdkv`.
- Dependencies: YAML, ZIP (std lib), Markdown renderer for HTML export.
- Tests: cover CLI, services, model invariants, and storage round‑trip.
