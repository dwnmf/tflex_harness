---
name: deepwiki-tflex-api
description: T-FLEX CAD 17 API documentation research workflow using DeepWiki repository dwnmf/tflex_api with local JSONL/Markdown cross-checks. Use when implementing, debugging, reviewing, or extending T-FLEX CAD Open API/.NET API behavior, 2D/3D model operations, commands, dialogs, object model usage, and LLM/RAG documentation lookups in this project.
---

# Deepwiki T-FLEX API

## Overview

Use this skill to answer "what does T-FLEX CAD 17 API expose?" and "which API member should our code use?" quickly.
Use DeepWiki repo `dwnmf/tflex_api` as the primary documentation source, then verify against local converted files when available.

## Workflow

1. Confirm documentation source.
- Use DeepWiki repo `dwnmf/tflex_api`.
- Prefer local copy `D:\REALPROJECTS\tflex_api` for exact grep/search when present.
- Start with `read_wiki_structure` when the needed section is unknown.
1. Retrieve targeted documentation.
- Use `ask_question` with exact class, method, property, namespace, or assembly names.
- Focus on signatures, parameter meanings, return values, units, object lifetime, and caveats.
1. Cross-check machine-readable data.
- Search `llm/symbols.jsonl` for exact API member IDs and compact metadata.
- Open `llm/types/*.md` for whole class/type context.
- Use `llm/chm_pages.jsonl` for explanatory CHM pages.
1. Map docs to local code.
- Open files listed in `references/repo-hotspots.md` when they exist in the current project.
- Verify API references, wrapper behavior, schema names, and error handling directly in code.
1. Validate behavior locally.
- Run the smallest available unit/tool check first.
- Run T-FLEX-dependent integration checks only when the CAD environment is installed and reachable.
- Mark environment blockers explicitly, do not guess.
1. Report with evidence.
- Cite DeepWiki finding and local file paths.
- Separate confirmed facts, inferred behavior, and open uncertainty.

## DeepWiki Query Strategy

Use templates from `references/deepwiki-query-patterns.md`.
Prefer queries that include:
- exact assembly (`TFlexAPI`, `TFlexAPI3D`, `TFlexAPIData`, `TFlexCommandAPI`)
- exact namespace/type/member name
- 2D vs 3D context
- expected parameter/return semantics
- failure behavior or required document state

## Local Documentation Checklist

Use `references/repo-hotspots.md` for file-level checks.
Minimum checks for documentation lookups:
- `llm/symbols.jsonl` contains the member ID and summary
- `llm/types/<assembly>__<type>__*.md` contains grouped members for the type
- `llm/chm_pages.jsonl` has explanatory pages when XML docs are sparse
- `raw/*.xml` can be checked when generated output appears incomplete
- `raw/TFlexAPI.chm` remains the original CHM source

## Diagnostics Runbook

Use `references/diagnostics-runbook.md` for command order and interpretation.

## Guardrails

- Treat `dwnmf/tflex_api` as documentation, not runtime truth.
- Prefer exact member IDs from `symbols.jsonl` over fuzzy memory.
- Keep local generated docs separate from source code changes.
- If CHM/XML docs are ambiguous, state ambiguity and propose a concrete T-FLEX runtime verification step.
- Do not assume T-FLEX CAD is installed or COM/.NET automation is registered unless checked locally.
