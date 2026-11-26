# Appendix A: Glossary

- MDKV: Multitrack Markdown container defined by this specification.
- Track: A named, typed Markdown layer within an MDKV document (e.g., `primary`, `translation`).
- Manifest: YAML file at the root of the container that indexes tracks and captures metadata.
- Round-trip: exact modeled field and track-text preservation through ZIP or JSON. Combined Markdown is a presentation export; embedded header-like text is not escaped into a reversible interchange format.
- Conformance: Degree to which an implementation satisfies normative requirements in this document.
