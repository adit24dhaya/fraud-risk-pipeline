# Agent Instructions

Keep context lean. Prefer targeted symbol lookup, graph queries, and small file reads over broad repository scans.

## Context Tools
- Use Serena first for code navigation: symbols, references, declarations, implementations, diagnostics, and safe refactors.
- Use Graphify for architecture and relationship questions after a graph exists, for example auth-to-database paths or cross-module concepts.
- Use Context7 when writing code that depends on library, framework, SDK, or API behavior.
- Use Repomix only for token audits or explicit repo packing. Do not pack the whole repo by default.

## Search Discipline
- Start with semantic or graph queries when possible.
- Use `rg` for exact text search.
- Read only the smallest relevant file sections.
- Avoid reading generated output, build folders, dependency folders, lock-heavy artifacts, or packed AI outputs unless directly needed.

## Generated And Heavy Paths
Treat these as excluded from normal context:
- `node_modules/`, `.venv/`, `venv/`, `dist/`, `build/`, `.next/`, `.nuxt/`, `coverage/`
- `graphify-out/cache/`, `repomix-output.*`, `.serena/cache/`
- binary media, archives, PDFs, model/checkpoint files, and logs

## Verification
When changing code, run the smallest relevant test/build/check command first. Broaden verification only when the change touches shared behavior.
