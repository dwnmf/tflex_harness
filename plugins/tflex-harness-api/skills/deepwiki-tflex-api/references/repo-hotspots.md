# Repository Hotspots

Use this checklist when validating local code against T-FLEX CAD 17 API docs.
Paths are expected hotspots; only open those that exist in the current project.

## Local Documentation Repository

- `$env:TFLEX_API_DOCS_DIR\llm\symbols.jsonl` or `<tflex-api-docs>/llm/symbols.jsonl`
Purpose: compact exact API symbol records generated from XML docs.
Check: `id`, `kind`, `assembly`, `namespace`, `type`, `signature`, `summary`, `params`, `returns`.

- `$env:TFLEX_API_DOCS_DIR\llm\types\*.md` or `<tflex-api-docs>/llm/types/*.md`
Purpose: type/class-level Markdown context grouped by assembly.
Check: constructors, methods, properties, fields, events, remarks.

- `$env:TFLEX_API_DOCS_DIR\llm\chm_pages.jsonl` or `<tflex-api-docs>/llm/chm_pages.jsonl`
Purpose: explanatory CHM pages as one JSONL file.
Check: broader usage patterns and conceptual docs.

- `$env:TFLEX_API_DOCS_DIR\raw\*.xml` or `<tflex-api-docs>/raw/*.xml`
Purpose: original XML documentation copies.
Check: source truth if generated files look incomplete.

- `$env:TFLEX_API_DOCS_DIR\scripts\convert_tflex_docs.py` or `<tflex-api-docs>/scripts/convert_tflex_docs.py`
Purpose: repeatable converter.
Check: generated format assumptions before changing docs structure.

## Likely Project Areas

- `src/`
Purpose: runtime wrapper/tool implementation if present.
Check: exact API member names, document/model lifecycle, exception handling.

- `tests/`
Purpose: unit/integration verification if present.
Check: coverage for API wrappers and environment-dependent behavior.

- `.agents/skills/`
Purpose: project-local agent workflows.
Check: skill instructions match current documentation repo and local paths.

## Validation Notes

- Prefer exact search for member names before broad semantic lookup.
- Verify ambiguous DeepWiki answers against local `symbols.jsonl` or `types/*.md`.
- Treat CHM content as explanatory context and XML-derived symbol records as API-reference context.
- If local project files do not exist yet, report that validation is documentation-only.
