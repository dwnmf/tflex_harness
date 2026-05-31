# Diagnostics Runbook

Run checks in this order.

## 1) Documentation File Health

Commands:
- `$docs = $env:TFLEX_API_DOCS_DIR`
- `Test-Path (Join-Path $docs 'llm\symbols.jsonl')`
- `Test-Path (Join-Path $docs 'llm\chm_pages.jsonl')`
- `Get-Content (Join-Path $docs 'llm\manifest.json') -Raw`

Goal:
- confirm the local converted documentation exists and counts match expectations.

Expected current counts:
- API symbols: 17,929
- type/class Markdown pages: 2,452
- CHM JSONL pages: 19,350

## 2) Exact Symbol Search

Commands:
- `rg "<TypeOrMemberName>" (Join-Path $docs 'llm\symbols.jsonl')`
- `rg "<TypeName>" (Join-Path $docs 'llm\types')`

Goal:
- confirm exact API member spelling, assembly, namespace, and summary before coding.

## 3) CHM Explanation Search

Command:
- `rg "<term>" (Join-Path $docs 'llm\chm_pages.jsonl')`

Goal:
- find explanatory documentation when XML member docs are too terse.

## 4) Project Tests

Use project-specific tests if present.
Typical commands may include:
- `python -m pytest`
- project-specific smoke tests or diagnostics

Interpretation:
- failures before T-FLEX startup usually indicate local environment/configuration blockers.
- failures after API calls may indicate wrapper/code issues or undocumented API preconditions.

## 5) Reporting Format

Always state:
- DeepWiki repo used: `dwnmf/tflex_api`
- local files searched, if any
- commands executed
- pass/fail/skipped results
- environment blockers
- whether conclusion is documentation-level, code-level, or runtime-verified
