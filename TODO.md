# MDKV — Upcoming Improvements TODO

Last updated: 2025-07-23
Current version: 0.10.0
Tests: 274 passing, 93% coverage

## All items completed

All minor, medium, and major improvements from the original TODO have been
shipped across v0.2.0 through v0.10.0. See [CHANGELOG.md](CHANGELOG.md) for
the full release history.

### Remaining low-priority items

- [ ] **Type stubs audit**: Run `mypy --strict mdkv/` and fix all type errors.
  The `py.typed` marker is present but the codebase hasn't been audited under
  strict mode. Focus on `gui/server.py` (FastAPI dict payloads need `TypedDict`).
- [ ] **Schema-based manifest validation**: Replace manual dict key checks in
  `_doc_from_manifest` with Pydantic models for more rigorous validation.
- [ ] **Translation files**: Create actual `.po`/`.mo` files for Spanish and
  French (i18n infrastructure is in place but only English is shipped).
- [ ] **GUI library endpoint coverage**: The `/api/library` endpoint (lines 70-81
  in `gui/server.py`) is not covered by tests because it depends on the
  repository layout at runtime.
