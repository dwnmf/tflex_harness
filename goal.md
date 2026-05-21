# Goal: T-FLEX CAD 17 Harness/MCP по принципам Browser Use Bitter Lesson

## 0. Краткая формулировка цели

Создать `tflex_harness` — тонкий, проверяемый harness/MCP для работы LLM-агента с T-FLEX CAD 17 API.

Главная идея: **не строить большой CAD-фреймворк с сотнями заранее придуманных tools**, а дать агенту:

1. быстрый поиск по официальной документации T-FLEX CAD 17 API;
2. возможность писать и запускать маленькие C# snippets против настоящих `TFlexAPI*.dll`;
3. live feedback от компилятора, runtime, T-FLEX CAD и состояния документа;
4. место для накопления проверенных helper-рецептов;
5. минимальный MCP-протокол, который не скрывает реальный API.

Итоговый workflow должен быть таким:

```text
LLM -> search docs -> write C# snippet -> compile/run -> observe result/errors -> fix -> save verified recipe
```

А не таким:

```text
LLM -> call huge wrapper create_extrude(...) -> wrapper guesses hidden API details -> silent mismatch -> brittle automation
```

---

## 1. Почему именно такая архитектура

### 1.1. Урок из Browser Use Bitter Lesson

Ключевой вывод статьи про agent frameworks: модели становятся сильнее, а жёсткие фреймворки быстро устаревают. Если framework заранее решает, какие действия агенту доступны и как он должен мыслить, то он ограничивает модель.

Для browser automation Browser Use пришли к принципу:

- protocol is the API;
- не делать толстый слой wrappers поверх browser primitives;
- дать агенту прямой доступ к низкоуровневым возможностям;
- helpers должны быть редкими, прозрачными и редактируемыми;
- runtime feedback важнее, чем заранее построенная идеальная абстракция.

Для T-FLEX CAD это означает:

- не надо заранее делать `create_line`, `create_circle`, `create_extrusion`, `set_material`, `create_bom`, `create_fragment`, `update_layer`, `make_drawing`, `export_step` как десятки MCP tools;
- надо дать агенту возможность читать документацию и писать настоящий C# код против T-FLEX API;
- если какой-то паттерн часто повторяется и проверен live-тестами, его можно вынести в helper;
- helper не должен прятать важные параметры и состояния T-FLEX API.

### 1.2. Главный архитектурный принцип

**MCP — транспорт, а не CAD framework.**

MCP server должен быть маленьким:

- принять запрос;
- найти документацию;
- скомпилировать/запустить snippet;
- вернуть stdout/stderr/errors/artifacts;
- показать состояние T-FLEX окружения;
- позволить сохранить проверенный helper.

Он не должен становиться альтернативным T-FLEX SDK.

### 1.3. Почему T-FLEX-код должен быть на C#

Основная машиночитаемая документация T-FLEX CAD 17 API — это .NET XML docs рядом с DLL:

- `TFlexAPI.dll` + `TFlexAPI.xml`
- `TFlexAPI3D.dll` + `TFlexAPI3D.xml`
- `TFlexAPIData.dll` + `TFlexAPIData.xml`
- `TFlexCommandAPI.dll` + `TFlexCommandAPI.xml`

Поэтому основной исполняемый код против T-FLEX API должен быть **C#/.NET**.

Причины:

1. Нативная модель API — .NET assemblies.
2. Компилятор сразу проверяет типы, namespaces, overloads и signatures.
3. Ошибки компиляции дают LLM точный feedback.
4. XML-docs напрямую соответствуют C# symbols.
5. Примеры T-FLEX API обычно ближе к C#-стилю, чем к Python.
6. Не нужно тащить дополнительные неопределённости `pythonnet`, COM late binding или динамические wrappers.

### 1.4. Почему harness/MCP должен быть на Python

MCP/harness слой лучше делать на **Python**.

Причины:

1. Быстро писать MCP server.
2. Удобно работать с JSONL, Markdown, logs, subprocess, временными файлами.
3. Удобно вызывать `dotnet build/run`, `rg`, diagnostics.
4. Удобно делать документационный search по `D:\REALPROJECTS\tflex_api`.
5. LLM легко редактирует Python helpers.
6. Python слой остаётся тонким и не конкурирует с C# API.

Итого:

```text
Python = harness/MCP/control plane/docs/logs
C#     = actual T-FLEX API execution/data plane
```

---

## 2. Целевая структура проекта

```text
tflex_harness/
  goal.md
  README.md
  pyproject.toml
  .agents/
    skills/
      deepwiki-tflex-api/
        SKILL.md
        agents/
          openai.yaml
        references/
          deepwiki-query-patterns.md
          diagnostics-runbook.md
          repo-hotspots.md

  src/
    tflex_harness/
      __init__.py
      mcp_server.py
      config.py
      docs_search.py
      runner.py
      diagnostics.py
      artifacts.py
      schemas.py
      logging_utils.py

  runner/
    TFlexRunner/
      TFlexRunner.csproj
      Program.cs
      SnippetHost.cs
      TFlexSession.cs
      ResultWriter.cs
      References.props

  agent_workspace/
    helpers.py
    recipes/
      README.md
    snippets/
      README.md

  tests/
    unit/
      test_docs_search.py
      test_runner_payloads.py
      test_artifacts.py
    smoke/
      test_dotnet_runner_compiles.py
    integration/
      test_tflex_environment.py
      test_tflex_live_document.py

  artifacts/
    .gitkeep

  logs/
    .gitkeep
```

Разделение ответственности:

| Area | Language | Responsibility |
|---|---:|---|
| `src/tflex_harness` | Python | MCP, docs search, subprocess runner, logs, artifacts |
| `runner/TFlexRunner` | C# | Compile/run snippets against T-FLEX .NET API |
| `agent_workspace/helpers.py` | Python | Малые reusable helpers, которые агент может менять |
| `agent_workspace/recipes` | Markdown/C# | Проверенные live-рецепты |
| `D:\REALPROJECTS\tflex_api` | JSONL/Markdown/CHM/XML | Документация T-FLEX CAD 17 API |

---

## 3. Документационная база

Документация уже подготовлена в отдельном репозитории:

```text
D:\REALPROJECTS\tflex_api
https://github.com/dwnmf/tflex_api
```

Структура:

```text
tflex_api/
  raw/
    TFlexAPI.chm
    TFlexAPI.xml
    TFlexAPI3D.xml
    TFlexAPIData.xml
    TFlexCommandAPI.xml

  llm/
    symbols.jsonl
    chm_pages.jsonl
    index.md
    manifest.json
    types/
      *.md

  scripts/
    convert_tflex_docs.py
```

### 3.1. Как использовать `symbols.jsonl`

`llm/symbols.jsonl` — главный файл для точных API lookups.

Одна строка = один XML documentation member:

```json
{
  "id": "M:...",
  "kind": "method",
  "assembly": "TFlexAPI3D",
  "namespace": "TFlex.Model.Model3D",
  "type": "...",
  "name": "...",
  "signature": "...",
  "summary": "...",
  "params": {},
  "returns": null
}
```

Использовать для:

- exact symbol lookup;
- определения assembly;
- определения namespace;
- поиска методов/свойств типа;
- предварительного RAG retrieval.

### 3.2. Как использовать `types/*.md`

`llm/types/*.md` — удобный контекст целого класса/типа.

Использовать когда:

- надо понять весь API surface класса;
- надо увидеть constructors/methods/properties/events рядом;
- надо дать LLM context для написания C# snippet.

### 3.3. Как использовать `chm_pages.jsonl`

`llm/chm_pages.jsonl` — объяснительные CHM pages, одна страница на JSON line.

Использовать когда:

- XML docs слишком краткие;
- нужны conceptual docs;
- нужно найти usage pattern;
- нужно объяснение операций, документов, команд, 2D/3D model concepts.

### 3.4. DeepWiki

Skill `deepwiki-tflex-api` должен использовать repo:

```text
dwnmf/tflex_api
```

DeepWiki использовать для semantic questions, но точные signatures всё равно проверять через локальные JSONL/Markdown, когда они доступны.

---

## 4. Минимальный набор MCP tools

Нужно сделать маленький набор универсальных tools.

### 4.1. `search_tflex_docs`

Назначение: искать по локальной документации T-FLEX API.

Input:

```json
{
  "query": "Document Save",
  "scope": "symbols|types|chm|all",
  "assembly": "TFlexAPI|TFlexAPI3D|TFlexAPIData|TFlexCommandAPI|null",
  "limit": 20
}
```

Output:

```json
{
  "results": [
    {
      "source": "symbols.jsonl",
      "score": 1.0,
      "assembly": "TFlexAPI",
      "kind": "method",
      "id": "M:...",
      "type": "...",
      "signature": "...",
      "summary": "..."
    }
  ]
}
```

Implementation принцип:

1. Сначала exact search по `symbols.jsonl`.
2. Потом fuzzy/substring по `types/*.md`.
3. Потом optional search по `chm_pages.jsonl`.
4. Не возвращать огромные страницы целиком без необходимости.
5. Для больших CHM hits возвращать preview + id/source path.

### 4.2. `get_tflex_environment`

Назначение: проверить локальное окружение.

Должен вернуть:

```json
{
  "tflex_install_dir": "C:\\Program Files\\T-FLEX CAD 17",
  "program_dir": "C:\\Program Files\\T-FLEX CAD 17\\Program",
  "dlls": {
    "TFlexAPI": true,
    "TFlexAPI3D": true,
    "TFlexAPIData": true,
    "TFlexCommandAPI": true
  },
  "dotnet": {
    "available": true,
    "version": "..."
  },
  "runner": {
    "project_exists": true,
    "build_ok": true
  },
  "tflex_process": {
    "running": false,
    "pids": []
  }
}
```

Важно: этот tool не должен запускать тяжёлые операции без необходимости. Это healthcheck.

### 4.3. `run_csharp_tflex`

Назначение: скомпилировать и запустить C# snippet против T-FLEX API.

Input:

```json
{
  "code": "using TFlex.Model; ...",
  "timeout_sec": 30,
  "references": ["TFlexAPI", "TFlexAPI3D"],
  "mode": "compile_only|run",
  "artifact_prefix": "test_document_save"
}
```

Output:

```json
{
  "ok": false,
  "stage": "compile|run|timeout",
  "exit_code": 1,
  "stdout": "...",
  "stderr": "...",
  "diagnostics": [
    {
      "severity": "error",
      "code": "CS1061",
      "message": "...",
      "file": "Snippet.cs",
      "line": 12
    }
  ],
  "artifacts": []
}
```

Принципы:

- Возвращать compiler diagnostics полностью, но без лишнего мусора.
- Всегда сохранять snippet в artifacts для воспроизводимости.
- Разделять compile errors и runtime errors.
- Не скрывать T-FLEX exceptions.
- Не превращать ошибки в vague messages.

### 4.4. `run_tflex_recipe`

Назначение: запускать уже проверенные рецепты.

Input:

```json
{
  "recipe": "create_basic_3d_box",
  "args": {
    "width": 100,
    "height": 50,
    "depth": 20
  }
}
```

Принципы:

- Recipe появляется только после live verification.
- Recipe должен иметь Markdown описание:
  - что делает;
  - какие API members использует;
  - какие assumptions;
  - как проверялся;
  - known limitations.

### 4.5. `capture_tflex_state`

Назначение: получить наблюдаемое состояние после run.

Минимально:

```json
{
  "documents": [],
  "active_document": null,
  "object_counts": {},
  "selection": [],
  "artifacts": []
}
```

Позже можно расширить:

- screenshot active view;
- export temporary file;
- list model tree;
- list variables;
- list 2D/3D objects;
- bounding boxes;
- document path and dirty state.

---

## 5. C# runner architecture

### 5.1. Runner цель

C# runner — это маленький host, который:

1. получает snippet или путь к snippet;
2. references T-FLEX assemblies;
3. компилирует или запускает код;
4. пишет structured JSON result;
5. возвращает stdout/stderr/exception/diagnostics.

### 5.2. Почему не динамический Python COM

Python COM/dynamic automation может быть полезен для quick checks, но не как основной путь.

Недостатки:

- слабая типизация;
- runtime-only ошибки;
- сложнее сопоставлять с XML docs;
- возможны проблемы с COM apartments;
- LLM хуже видит overloads и signatures.

C# даёт immediate compile feedback.

### 5.3. Runner project

```text
runner/TFlexRunner/
  TFlexRunner.csproj
  Program.cs
  SnippetHost.cs
  TFlexSession.cs
  ResultWriter.cs
  References.props
```

`TFlexRunner.csproj` должен ссылаться на локальные DLL:

```xml
<ItemGroup>
  <Reference Include="TFlexAPI">
    <HintPath>C:\Program Files\T-FLEX CAD 17\Program\TFlexAPI.dll</HintPath>
  </Reference>
  <Reference Include="TFlexAPI3D">
    <HintPath>C:\Program Files\T-FLEX CAD 17\Program\TFlexAPI3D.dll</HintPath>
  </Reference>
  <Reference Include="TFlexAPIData">
    <HintPath>C:\Program Files\T-FLEX CAD 17\Program\TFlexAPIData.dll</HintPath>
  </Reference>
  <Reference Include="TFlexCommandAPI">
    <HintPath>C:\Program Files\T-FLEX CAD 17\Program\TFlexCommandAPI.dll</HintPath>
  </Reference>
</ItemGroup>
```

Версию target framework надо определить live:

- сначала попробовать `net48`, если assemblies требуют .NET Framework;
- если возможно, проверить `net8.0-windows`;
- выбрать минимально совместимый вариант по build результатам.

### 5.4. Политика компиляции

Компиляция C# — это feedback loop, а не обязательная цена каждого API действия.

Целевой порядок зрелости:

1. **Dynamic snippet mode** — для исследования и live verification можно компилировать один видимый C# snippet на один `run_csharp_tflex` вызов.
2. **Content-addressed compile cache** — успешные сборки кешируются по hash исходника, references, compiler path и ключевых build options. Повторный запуск того же snippet не должен снова вызывать `csc.exe`.
3. **Verified recipe mode** — проверенные recipes лежат как C# исходники, но запускаются через тот же compile cache, чтобы они оставались редактируемыми и не превращались в скрытый framework.
4. **Persistent runner mode** — будущая production-оптимизация: долгоживущий C# process держит T-FLEX session и принимает JSON-команды от Python/MCP без перекомпиляции на каждую мелкую операцию.

Важно: кеш или persistent runner не должны скрывать реальный C# код от LLM. Snippet/recipe source остаётся основным контрактом и всегда сохраняется в artifacts.

### 5.5. Snippet shape

Желательный формат snippet:

```csharp
using System;
using TFlex;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;

public static class Snippet
{
    public static int Main(string[] args)
    {
        Console.WriteLine("Hello from T-FLEX snippet");
        return 0;
    }
}
```

Runner может генерировать wrapper вокруг user code, но wrapper должен быть прозрачным.

Плохой вариант:

```csharp
CreateBox(width, height, depth);
```

Хороший вариант:

```csharp
// real T-FLEX API calls here, visible to the LLM
var app = ...;
var doc = ...;
...
```

### 5.6. Structured result

Каждый запуск должен создавать:

```text
artifacts/runs/<timestamp>_<slug>/
  request.json
  snippet.cs
  result.json
  stdout.txt
  stderr.txt
  build.log
  run.log
  artifacts/
```

`result.json`:

```json
{
  "ok": true,
  "stage": "run|compile|timeout",
  "phase": "compile|run",
  "duration_ms": 1234,
  "exit_code": 0,
  "cache_key": "sha256...",
  "cache_hit": false,
  "diagnostics": [],
  "stdout_path": "stdout.txt",
  "stderr_path": "stderr.txt",
  "snippet_path": "snippet.cs",
  "artifacts_dir": "artifacts/runs/.../artifacts",
  "artifacts": []
}
```

При запуске snippet runner должен передавать:

- `TFLEX_HARNESS_RUN_DIR` — корень конкретного запуска;
- `TFLEX_HARNESS_ARTIFACTS_DIR` — writable папка для файлов, которые создаёт snippet.

Timeout должен быть структурированным: `stage="timeout"` и `phase="compile"` или `phase="run"`, чтобы LLM понимала, на каком этапе зависло выполнение.

---

## 6. Live testing philosophy

### 6.1. Почему live testing обязательно

T-FLEX CAD API — stateful CAD API. Документации недостаточно.

Нужно проверять:

- установлен ли T-FLEX;
- видит ли runner DLL;
- совпадает ли bitness;
- можно ли создать/получить application/document;
- какие операции требуют active document;
- какие операции требуют 2D/3D context;
- какие методы возвращают null/false/exception;
- когда документ становится dirty;
- какие объекты реально появляются после API call.

Без live testing получится wrapper, который выглядит правильно, но ломается на первом реальном документе.

### 6.2. Уровни тестирования

#### Level 0: Static docs tests

Не требует T-FLEX CAD.

Проверяет:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl` существует;
- JSONL валиден;
- `manifest.json` содержит ожидаемые counts;
- search возвращает результаты;
- type pages доступны;
- CHM JSONL доступен.

Команды:

```powershell
python -m pytest tests/unit/test_docs_search.py -v
```

#### Level 1: Runner compile tests

Не требует запущенного T-FLEX, но требует DLL/reference compatibility.

Проверяет:

- `dotnet` доступен;
- `TFlexRunner.csproj` собирается;
- references на DLL корректны;
- минимальный snippet компилируется;
- compile diagnostics правильно парсятся.

Команды:

```powershell
python -m pytest tests/smoke/test_dotnet_runner_compiles.py -v
```

#### Level 2: T-FLEX environment tests

Требует установленный T-FLEX CAD 17.

Проверяет:

- install dir существует;
- DLL существуют;
- возможно загрузить assemblies;
- возможно найти/запустить T-FLEX process, если выбран такой режим;
- возможно подключиться к application/session, если API это позволяет.

Команды:

```powershell
python -m pytest tests/integration/test_tflex_environment.py -v
```

#### Level 3: Live document smoke tests

Требует working T-FLEX environment.

Проверяет:

- создать новый документ;
- сохранить временный документ;
- создать простейший объект;
- прочитать состояние;
- закрыть/очистить документ.

Пример сценария:

```text
1. start/connect T-FLEX
2. create temporary document
3. create one simple 2D line or variable
4. save to artifacts
5. verify file exists / object count changed
6. close without user interaction
```

#### Level 4: Recipe tests

Каждый проверенный recipe должен иметь свой live test.

Пример:

```text
recipe: create_basic_3d_box
checks:
- document created
- 3D body count increased
- bounding box roughly matches input dimensions
- exported artifact exists
```

### 6.3. Правило продвижения helpers

Snippet можно превратить в helper/recipe только если:

1. найден через docs search;
2. написан на видимом C# API;
3. успешно компилируется;
4. успешно выполняется live;
5. имеет наблюдаемую проверку результата;
6. сохранён с описанием assumptions/limitations.

---

## 7. Что НЕ делать

### 7.1. Не создавать толстый CAD abstraction layer

Не надо начинать с такого API:

```text
create_2d_line
create_2d_circle
create_2d_rectangle
create_3d_box
create_3d_cylinder
create_extrude_boss
create_extrude_cut
create_hole
create_filleting
create_chamfer
create_drawing_view
export_step
export_pdf
set_material
set_variable
create_bom
```

Это выглядит удобно, но плохо масштабируется.

Проблемы:

- каждая команда скрывает десятки API assumptions;
- неясно, что делать с unsupported edge cases;
- LLM перестаёт видеть настоящий T-FLEX API;
- wrappers становятся багами;
- документация расходится с реализацией;
- live errors становятся менее полезными.

### 7.2. Не прятать compile errors

Плохо:

```json
{"ok": false, "error": "Snippet failed"}
```

Хорошо:

```json
{
  "ok": false,
  "stage": "compile",
  "diagnostics": [
    {
      "code": "CS0246",
      "message": "The type or namespace name 'Foo' could not be found",
      "line": 7,
      "column": 13
    }
  ]
}
```

### 7.3. Не смешивать docs repo и harness repo

`D:\REALPROJECTS\tflex_api` — документация.

`D:\REALPROJECTS\tflex_harness` — исполнение, MCP, tests, recipes.

Не надо копировать всю документацию внутрь harness. Harness должен ссылаться на docs repo.

---

## 8. Implementation milestones

### Milestone 1: Skeleton

Deliverables:

- `README.md`
- `pyproject.toml`
- Python package `src/tflex_harness`
- config loader
- basic logging
- artifact directory creation
- unit tests skeleton

Definition of done:

- `python -m pytest tests/unit -v` runs;
- package imports;
- config resolves T-FLEX install dir and docs dir.

### Milestone 2: Docs search

Deliverables:

- `docs_search.py`
- `search_tflex_docs` internal function
- JSONL parser for `symbols.jsonl`
- JSONL parser for `chm_pages.jsonl`
- type page lookup
- tests for exact symbol search and CHM search

Definition of done:

- exact query returns member records;
- type query returns type Markdown path/preview;
- CHM query returns page ids/previews;
- no huge unbounded output.

### Milestone 3: MCP server

Deliverables:

- `mcp_server.py`
- MCP tools:
  - `search_tflex_docs`
  - `get_tflex_environment`
- tool schemas
- manual smoke run

Definition of done:

- MCP server starts;
- tools are listed;
- docs search tool returns useful data;
- environment tool returns paths and DLL status.

### Milestone 4: C# runner compile-only

Deliverables:

- `runner/TFlexRunner/TFlexRunner.csproj`
- basic snippet compilation
- Python `runner.py` wrapper
- compile diagnostics parser
- artifacts per run

Definition of done:

- compile-only hello snippet works;
- invalid snippet returns structured CS diagnostics;
- T-FLEX references are checked.

### Milestone 5: C# runner live execution

Deliverables:

- `run_csharp_tflex` MCP tool
- timeout handling
- stdout/stderr capture
- result JSON
- first live T-FLEX smoke snippet

Definition of done:

- compile and run mode works;
- timeout is enforced;
- artifacts are saved;
- live environment failures are explicit.

### Milestone 6: First verified recipes

Candidate recipes:

1. `environment_probe`
2. `create_empty_document`
3. `save_document_as_temp`
4. `create_simple_2d_geometry`
5. `create_simple_3d_feature` only after 2D/doc flow is stable

Definition of done:

- each recipe has `.md` explanation;
- each recipe has C# source;
- each recipe has live test;
- assumptions and limitations are documented.

### Current implementation status — 2026-05-21

This section records what is implemented in the current `D:\REALPROJECTS\tflex_harness` worktree and what is still open.

#### Implemented and live-verified

- **Milestone 1: Skeleton** — implemented.
  - Evidence: `README.md`, `pyproject.toml`, package `src/tflex_harness`, config loader, logging helpers, artifact store, unit/smoke/integration test layout.
  - Config resolves default docs repo `D:\REALPROJECTS\tflex_api`, T-FLEX install dir `C:\Program Files\T-FLEX CAD 17`, program dir, runner dir, artifacts dir, and logs dir.
- **Milestone 2: Docs search** — implemented.
  - Evidence: `src/tflex_harness/docs_search.py`, `src/tflex_harness/schemas.py`, tests in `tests/unit/test_docs_search.py`, CLI/MCP smoke tests.
  - Supported scopes: `symbols`, `types`, `chm`, `all`.
  - Supported assembly filter values: `TFlexAPI`, `TFlexAPI3D`, `TFlexAPIData`, `TFlexCommandAPI`.
  - Output is bounded by normalized limits and returns machine-readable previews instead of huge CHM/type pages.
- **Milestone 3: MCP server** — implemented and extended beyond the minimal two tools.
  - Evidence: `src/tflex_harness/mcp_server.py`, `tests/smoke/test_mcp_server.py`, `tests/smoke/test_packaging.py`.
  - Tools present: `search_tflex_docs`, `get_tflex_environment`, `run_csharp_tflex`, `list_tflex_recipes`, `run_tflex_recipe`, `capture_tflex_state`, `save_tflex_snippet_candidate`.
  - Console entrypoint present: `tflex-harness-mcp = "tflex_harness.mcp_server:main"`.
- **Milestone 4: C# runner compile-only** — implemented.
  - Evidence: `runner/TFlexRunner/TFlexRunner.csproj`, `build.ps1`, `References.props`, `Program.cs`, `SnippetHost.cs`, `TFlexSession.cs`, `ResultWriter.cs`, `src/tflex_harness/runner.py`.
  - `build_runner()` exists and reports target framework/platform.
  - `run_csharp_snippet(..., mode="compile_only")` compiles snippets with `csc.exe`, parses CS diagnostics, records artifacts, checks requested T-FLEX references, and exposes resolved references.
- **Milestone 5: C# runner live execution** — implemented and live-verified.
  - Evidence: `tests/smoke/test_csharp_runner.py`, `tests/integration/test_tflex_live_session.py`, `tests/integration/test_tflex_environment.py`, `tests/integration/test_tflex_cli_live.py`, `tests/integration/test_tflex_mcp_live.py`.
  - Result contract includes structured `stage`, `phase`, `exit_code`, `duration_ms`, `cache_key`, `cache_hit`, `diagnostics`, `snippet_path`, `build_log`, `stdout_path`, `stderr_path`, `run_log`, `artifacts_dir`, and collected `artifacts`.
  - Timeouts are structured as `stage="timeout"` with `phase="compile"` or `phase="run"`.
  - Successful C# builds are cached by content-addressed key and reused on repeated calls.
  - Snippets receive `TFLEX_HARNESS_RUN_DIR` and `TFLEX_HARNESS_ARTIFACTS_DIR`.
- **Milestone 6: First verified recipes** — implemented and live-verified.
  - Evidence: `agent_workspace/recipes/*.cs`, `agent_workspace/recipes/*.md`, `src/tflex_harness/recipes.py`, `tests/integration/test_tflex_recipes.py`, `tests/unit/test_recipes.py`.
  - Verified recipes:
    - `environment_probe`
    - `create_empty_document`
    - `save_document_as_temp`
    - `create_simple_2d_line`
    - `create_simple_3d_extrusion`
  - Each verified recipe has C# source, Markdown explanation, documented docs evidence, assumptions, limitations, live verification report, and integration coverage.
- **Live state capture** — implemented.
  - Evidence: `src/tflex_harness/state.py`, `tests/integration/test_tflex_state.py`, `tests/integration/test_tflex_mcp_live.py`.
  - Captures session status, active document, document list, document count, aggregate object counts, observed 2D/3D type counts, 3D operation bounding boxes when available, variables, empty selection, run info, and artifacts.
- **Snippet candidate workflow** — implemented.
  - Evidence: `src/tflex_harness/workspace.py`, `agent_workspace/snippets/README.md`, `tests/unit/test_workspace.py`.
  - Saves candidate C# and Markdown review metadata under `agent_workspace/snippets` without promoting them to verified recipes.
- **Repository skill** — implemented.
  - Evidence: `.agents/skills/deepwiki-tflex-api/SKILL.md`.
  - Points agents to DeepWiki repo `dwnmf/tflex_api` and local docs repo `D:\REALPROJECTS\tflex_api`.
- **Latest full validation observed** — passed.
  - Evidence: `python -m pytest -v` on 2026-05-21 collected 66 tests and passed all 66, including live T-FLEX integration tests.

#### Recently implemented guardrails

- A safety guardrail rejects `run_tflex_recipe(..., args={"output_file": ...})` paths outside `artifacts/tflex_docs`.
  - Evidence: `src/tflex_harness/recipes.py`, `tests/unit/test_recipes.py`, `README.md`.
  - Validation observed before this status update: `tests/unit/test_recipes.py` plus `tests/integration/test_tflex_recipes.py` passed, and then full `python -m pytest -v` passed 66 tests.

#### Not implemented / intentionally deferred

- **Persistent runner mode** is not implemented.
  - The current implementation uses dynamic snippet mode plus content-addressed compile cache.
  - This matches the required maturity level for the current harness; persistent runner remains a future production optimization.
- **Screenshot/export active view** in `capture_tflex_state` is not implemented.
  - Current state capture is structured/textual and includes model/document counts, variables, 2D/3D type counts, and 3D bounding boxes.
- **Full model tree traversal** is not implemented.
  - Current capture reports aggregate counts and selected observable entities, not a complete tree dump.
- **Broad high-level CAD wrapper/toolset** is intentionally not implemented.
  - No `create_line`, `create_circle`, `create_extrusion`, `set_material`, `export_step`, etc. MCP tool explosion was explicitly rejected by the architecture.
- **Completion audit for marking the whole project done** has not been performed.
  - The implementation is substantially functional and live-verified, but the active goal should only be marked complete after a requirement-by-requirement audit against this document.

---

## 9. Suggested first files

### 9.1. `pyproject.toml`

Should define:

- package name: `tflex-harness`
- Python version: `>=3.11`
- dependencies:
  - MCP library if used;
  - pydantic optional;
  - pytest for tests.

### 9.2. `src/tflex_harness/config.py`

Responsibilities:

- default docs dir: `D:\REALPROJECTS\tflex_api`
- default T-FLEX dir: `C:\Program Files\T-FLEX CAD 17`
- default program dir: `C:\Program Files\T-FLEX CAD 17\Program`
- env overrides:
  - `TFLEX_API_DOCS_DIR`
  - `TFLEX_INSTALL_DIR`
  - `TFLEX_PROGRAM_DIR`
  - `TFLEX_RUNNER_PROJECT`

### 9.3. `src/tflex_harness/docs_search.py`

Functions:

```python
def search_symbols(query: str, assembly: str | None = None, limit: int = 20) -> list[dict]: ...
def search_types(query: str, limit: int = 20) -> list[dict]: ...
def search_chm(query: str, limit: int = 20) -> list[dict]: ...
def search_all(query: str, assembly: str | None = None, limit: int = 20) -> dict: ...
```

### 9.4. `src/tflex_harness/runner.py`

Functions:

```python
def run_csharp_snippet(code: str, mode: str, timeout_sec: int) -> dict: ...
def build_runner(timeout_sec: int) -> dict: ...
def write_run_artifacts(request: dict, result: dict) -> Path: ...
```

### 9.5. `src/tflex_harness/diagnostics.py`

Functions:

```python
def get_environment() -> dict: ...
def check_tflex_dlls() -> dict: ...
def check_dotnet() -> dict: ...
def check_docs_repo() -> dict: ...
```

---

## 10. Live testing details

### 10.1. Test artifact policy

All live tests must write under:

```text
artifacts/runs/<timestamp>_<test_name>/
```

Never write random files into project root.

Temporary T-FLEX documents should go under:

```text
artifacts/tflex_docs/<timestamp>_<test_name>/
```

### 10.2. Test safety

Live tests must:

- not modify user documents;
- not assume an existing active document is safe to change;
- create temporary documents when possible;
- close or leave clear artifacts;
- not require interactive clicks;
- have timeouts;
- clearly mark skipped tests if T-FLEX is unavailable.

### 10.3. Environment blockers

Common blockers to report explicitly:

- T-FLEX CAD 17 not installed;
- DLL path missing;
- .NET target mismatch;
- bitness mismatch;
- license dialog / interactive startup;
- COM registration missing, if COM is used;
- T-FLEX process cannot start headlessly;
- API requires GUI session.

Never hide these as generic test failures.

### 10.4. Live test reporting

Each live test result should state:

```text
Test: create_empty_document
Docs used:
- symbols: ...
- type page: ...
Snippet: artifacts/runs/.../snippet.cs
Result: pass/fail/skipped
Evidence:
- stdout line
- saved file path
- object count
- screenshot/export if available
Blockers: none / listed
```

---

## 11. Agent operating procedure

When the agent needs to implement a T-FLEX operation:

1. Search docs:
   - `search_tflex_docs` with exact operation terms.
   - DeepWiki `dwnmf/tflex_api` if conceptual context is needed.
2. Identify assembly/type/member:
   - verify in `symbols.jsonl`.
   - open type page if needed.
3. Write minimal C# snippet:
   - no helper unless already verified.
   - visible T-FLEX API calls.
4. Compile only:
   - fix namespace/reference/signature errors.
5. Run live:
   - observe runtime exceptions and T-FLEX state.
6. Add assertions/checks:
   - document created, object count changed, file exists, etc.
7. Promote to recipe only after repeated success.
8. Update docs/recipe with assumptions.

---

## 12. Definition of success

The project is successful when an LLM can:

1. Ask what T-FLEX API member to use.
2. Retrieve exact docs from `tflex_api`.
3. Generate C# code against real T-FLEX DLLs.
4. Compile it and receive actionable diagnostics.
5. Run it against live T-FLEX CAD when available.
6. Observe actual document/model changes.
7. Iterate from errors to working code.
8. Save verified recipes without building a brittle mega-wrapper.

---

## 13. Non-goals

This project is not:

- a complete replacement for T-FLEX CAD SDK;
- a huge high-level CAD automation library;
- a static code generator for every API member;
- a wrapper that hides T-FLEX API details from the model;
- a no-code CAD tool;
- a project that guesses behavior without live verification.

---

## 14. Immediate next steps

1. Perform a requirement-by-requirement completion audit against this `goal.md`.
2. If the audit passes, mark the active implementation goal complete.
3. If the audit finds gaps, implement only the missing items with live verification.
4. Keep future expansion focused on visible C# snippets and verified recipes, not a large hidden CAD wrapper.

---

## 15. One-sentence architecture rule

**Let the model write small, typed C# programs against the real T-FLEX CAD 17 API, while Python MCP only searches docs, runs code, captures feedback, and stores verified recipes.**
