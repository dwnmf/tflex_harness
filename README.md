# tflex_harness

`tflex_harness` — тонкая Python-обвязка для работы с T-FLEX CAD 17 через MCP, CLI и видимые C#-сниппеты.

Главная граница проекта:

- Python управляет CLI/MCP, конфигом, поиском по документации, артефактами, рецептами и диагностикой.
- C# выполняет реальные вызовы T-FLEX CAD 17 API.
- Все результаты запусков сохраняются в `artifacts/`.
- Проверенные C#-рецепты лежат в `agent_workspace/recipes/`.
- Переиспользуемые вспомогательные C#-файлы лежат в `src/tflex_harness/csharp_helpers/`.

## Требования

- Windows.
- Установленный T-FLEX CAD 17.
- Python 3.11+.
- `git`.
- `uv` желательно, но не обязательно.

## Быстрая установка

```powershell
git clone https://github.com/dwnmf/tflex_harness C:\tflex_harness
cd C:\tflex_harness
uv tool install -e ".[mcp]"
tflex-harness bootstrap --full
```

`bootstrap --full` делает первичную настройку:

- клонирует документацию API из `https://github.com/dwnmf/tflex_api`, если её нет;
- сохраняет переменные `TFLEX_HARNESS_REPO_DIR` и `TFLEX_API_DOCS_DIR`;
- регистрирует навык Codex;
- проверяет установку T-FLEX, документацию, компиляторы и runner.

После `bootstrap --full` перезапустите терминал.

Если `uv` не используется:

```powershell
py -m pip install -e ".[mcp]"
python -m tflex_harness.cli bootstrap --full
```

Подробная инструкция: [`install.md`](install.md).

## Проверка установки

```powershell
tflex-harness doctor
tflex-harness env
tflex-harness recipes
tflex-harness run-csharp --mode compile_only --code "public class Program { public static int Main(){ return 0; } }"
```

Здоровая установка должна видеть:

- DLL T-FLEX API;
- локальную документацию `tflex_api`;
- компилятор C# (`csc.exe`);
- рабочий каркас runner.

## MCP

Запуск MCP-сервера:

```powershell
tflex-harness-mcp
```

Сгенерировать конфиг:

```powershell
tflex-harness mcp-config --for codex
tflex-harness mcp-config --for claude
```

Для Codex команда печатает TOML:

```toml
[mcp_servers."tflex-harness"]
command = "tflex-harness-mcp"

[mcp_servers."tflex-harness".env]
TFLEX_HARNESS_REPO_DIR = "<repo>"
TFLEX_API_DOCS_DIR = "<tflex-api-docs>"
TFLEX_INSTALL_DIR = "<tflex-install>"
```

Для Claude команда печатает JSON.

## Основные команды

```powershell
tflex-harness search "Document SaveAs" --scope symbols --limit 5
tflex-harness run-csharp --mode compile_only --code "public class Program { public static int Main(){ return 0; } }"
tflex-harness recipes
tflex-harness run-recipe environment_probe --timeout-sec 60
tflex-harness state
tflex-harness create-document --payload input.json --dry-run
tflex-harness document-factory-batch --payload-dir payloads --dry-run
```

## Что умеет обвязка

- Искать по локальному экспорту документации T-FLEX API.
- Компилировать и запускать видимые C#-сниппеты против DLL T-FLEX.
- Запускать проверенные C#-рецепты.
- Создавать документы из JSON-задания через фабрику документов.
- Сканировать и проверять прототипы T-FLEX.
- Сохранять воспроизводимые артефакты каждого запуска.
- Давать Codex/Claude доступ к этим операциям через MCP.

## Артефакты

Запуски пишутся в:

```text
artifacts/runs/<timestamp>_<slug>/
```

Обычно внутри есть:

- `request.json`
- `snippet.cs`
- `helpers/*.cs`
- `build.log`
- `stdout.txt`
- `stderr.txt`
- `run.log`
- `result.json`
- `artifacts/`

Сгенерированные T-FLEX документы должны оставаться под `artifacts/tflex_docs/`.

## Вспомогательные C#-файлы

Вспомогательные файлы — это обычные `.cs` исходники. Они копируются в каталог запуска и компилируются вместе со сниппетом.

Пример:

```powershell
tflex-harness run-csharp --mode compile_only --helper easy_core --code "using TFlexEasy; public class Program { public static int Main(){ System.Console.WriteLine(EasyUnits.F(1)); return 0; } }"
```

Доступные наборы вспомогательных файлов определены в `src/tflex_harness/runner.py`.

## Тесты

Основная точка тестирования — внешняя: CLI/MCP/runner.

```powershell
python -m pytest tests/smoke -v
```

Проверки на живом T-FLEX требуют установленного и доступного T-FLEX CAD:

```powershell
python -m pytest tests/integration -v
```

Не заявляйте, что путь на живом T-FLEX работает, без конкретного живого запуска и каталога запуска из `artifacts/runs/`.

## Релизы

Версия задаётся в:

- `pyproject.toml`
- `src/tflex_harness/__init__.py`

Сборка пакета:

```powershell
python -m build
```

Файлы релиза:

- `dist/tflex_harness-<version>-py3-none-any.whl`
- `dist/tflex_harness-<version>.tar.gz`

Процесс `.github/workflows/release-build.yml` публикует файлы релиза для тегов `v*`.

## Для ИИ-агентов

Сначала читать:

1. `install.md` — установка и первичный bootstrap.
2. `AGENTS.md` — правила работы с репозиторием.
3. `.agents/skills/tflex-harness/SKILL.md` — короткий рабочий навык.

Минимальный запрос для настройки:

```text
Настрой https://github.com/dwnmf/tflex_harness. Сначала прочитай install.md. Установи репозиторий в редактируемом режиме с дополнениями MCP, запусти tflex-harness bootstrap --full, затем проверь через tflex-harness doctor и tflex-harness recipes. Не запускай широкие пакетные проверки на живом T-FLEX без отдельной просьбы.
```
