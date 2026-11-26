# Implications for Governance and Reproducibility

- Governance: `revision` + metadata expose intent and review structure.
- Reproducibility: deterministic export + manifest versioning.
- Interoperability: ubiquitous primitives (ZIP, YAML, Markdown).
- Diff‑friendliness: semantic separation reduces merge conflicts.
- Extensibility: add track types/exporters without core changes.
- Supply-chain clarity: explicit manifests, source hashes and runtime records make a specific bundle auditable; deterministic text composition is not a byte-reproducible build certification.

## Licensing and community

- **License**: Apache‑2.0. See [LICENSE](https://github.com/docxology/mdkv/blob/main/LICENSE) in the repository.
- **Source & issues**: development and issue tracking on the [GitHub repository](https://github.com/docxology/mdkv).
- **Contributions**: small, focused pull requests preferred; tests and docs alongside changes.

## Security and Privacy Considerations

- `.mdkv` bundles are not encrypted; sensitive content SHOULD be managed with appropriate transport and storage controls (e.g., encryption at rest, signed artifacts).
- `metadata` may contain personally identifiable information; producers SHOULD minimize PII and consumers SHOULD handle metadata under applicable policies.
- Track headers in exported Markdown are informational; avoid embedding secrets in headers or comments.
- Validation is minimal by design; distributors SHOULD layer additional checks where provenance and integrity are critical (e.g., checksums, signatures).

## Evidence and limitations of this methods description

The examples in this paper and `library/definitions/` are authored synthetic
demonstrations, not empirical datasets. This work reports no user study,
comparative benchmark, empirical validation of an active-inference model, or
measured improvement in governance, collaboration, cognition or merge-conflict rates. The use-case
benefits are design motivations and hypotheses, not experimental findings.

For implementation assurance, the repository's versioned release receipt records
the exact runtime, commands, source binding and observed checks. Statement
coverage measures executed statements, not conformance completeness or security.
The defensive review models a malicious document supplier and a website
attempting access to the loopback GUI; hostile same-user processes, collaborative
concurrency and external Pandoc/LaTeX resource policies remain outside that model.
History helpers are standalone in-memory objects; MDKV does not automatically
persist edits as revision history. Unknown ZIP members and unknown manifest keys
are not preserved by model-based save/load roundtrips.

## Cryptographic provenance and signing

- Manifest and track checksums: producers MAY compute SHA‑256 (or stronger) digests for each file and include them in `metadata` for integrity verification after transport.
- Container signing: producers MAY sign the `.mdkv` archive (e.g., using minisign or GPG) and distribute the signature alongside the artifact. Consumers SHOULD verify signatures prior to ingest in security‑sensitive contexts.
- Reproducibility scope: fixed document fields, track order and renderer versions give deterministic text exports. ZIP timestamps and bundle generation timestamps are not byte-reproducible build guarantees; published checksums verify the particular supplied artifacts, not independent rebuild identity.
- Threat model notes: code tracks are not executed by MDKV. Version 0.12.0 disables raw HTML in its HTML renderers, escapes diff descriptions, sandboxes GUI previews and rejects foreign browser origins/hosts. This is not authentication, an external-resource fetch sandbox, or isolation from another process running as the same user.

## Interoperability and Migration Guidance

- Content SHOULD be authored in CommonMark‑compatible Markdown to maximize renderer compatibility.
- For downstream channels (PDF/EPUB), use `to_markdown()` with pandoc‑compatible flags/templates; retain track headers to assist provenance.
- When migrating legacy multi‑file projects, prefer one‑track‑per‑file mapping under `tracks/` and encode provenance in `metadata`.
