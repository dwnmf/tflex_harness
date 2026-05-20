# DeepWiki Query Patterns

Use repository `dwnmf/tflex_api`.
Prefer short, single-purpose questions.

## Exact Member Lookup

Use:
- "In T-FLEX CAD 17 API docs, what is `TFlex.Model.Document` used for and which assembly defines it?"
- "For `TFlexAPI3D`, what members exist on `<TypeName>` and what are their signatures?"
- "What is the summary, parameters, and return value for `<full member name>`?"

Expect:
- assembly name
- namespace/type/member name
- signature when available
- summary and parameter semantics

## 2D Model Operations

Use:
- "Which T-FLEX CAD 17 API classes in `TFlex.Model.Model2D` create or edit 2D geometry?"
- "For `<2D type>`, what properties and methods control coordinates, style, and document ownership?"
- "What CHM pages explain 2D object creation and document model usage?"

Expect:
- relevant `TFlexAPI` members
- document/context requirements
- notes when XML docs are sparse and CHM should be checked

## 3D Model Operations

Use:
- "Which `TFlex.Model.Model3D` classes create 3D operations/features?"
- "For `<3D operation type>`, what parameters and nested types are documented?"
- "What is the expected sequence to create or configure `<feature>` in T-FLEX CAD 17 API?"

Expect:
- `TFlexAPI3D` types and methods
- required model/document context
- operation-specific parameter objects or enums

## Commands, Dialogs, and UI

Use:
- "What does `TFlexCommandAPI` expose for commands/dialogs?"
- "Which `TFlex.Dialogs` controls are documented and what events/properties do they provide?"
- "For `<dialog/control type>`, what are construction and event patterns?"

Expect:
- command API assembly/type names
- dialog/control properties and events
- caveats about UI context if documented

## JSONL/RAG Usage

Use:
- "How is this repository structured for LLM/RAG usage?"
- "Which file should be searched for exact API symbols vs explanatory CHM content?"

Expect:
- `llm/symbols.jsonl` for exact symbols
- `llm/types/*.md` for type-level context
- `llm/chm_pages.jsonl` for explanatory pages

## Good Question Form

Use this template:

"In `dwnmf/tflex_api`, for T-FLEX CAD 17 `<assembly>` `<namespace/type/member>`, what is the exact documented signature, parameter meaning, return behavior, and any related CHM explanation?"
