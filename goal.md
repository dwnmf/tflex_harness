# T-FLEX Harness — Полный план имплементации

Дата: 2026-05-27
Статус: рабочий план к исполнению

---

## 1) Цель

Сделать `tflex_harness` быстрым и надёжным контуром для:

1. генерации 3D-деталей и сборок через helper-слой;
2. верификации геометрии и артефактов (GRB/STEP/DXF/DWG/PDF);
3. контроля сборочных ошибок (коллизии, плавающие фрагменты, контакт);
4. исследования и автоматизации native mates с доказуемыми live-результатами.

---

## 2) Базовые принципы

1. Минимальные, прозрачные helper’ы — без «магии».
2. Любой API-факт: сначала `compile_only`, потом live-run.
3. Любое сильное утверждение — только с `run_dir` и stdout-доказательством.
4. Артефакты писать только в `artifacts/runs/...` / `artifacts/tflex_docs/...`.
5. Не расширять scope: закрывать текущие блокеры по очереди.

---

## 3) Текущее состояние (кратко)

Уже есть рабочий helper-backlog (моделирование, булевы, профили, экспорт, сборка, валидация, инспектор mates, probe команд) и свежие рецепты с live-подтверждениями.

Критический открытый блокер:

- в harness-сессии нет полноценного UI-контекста команд:
  - `ActiveDocument == null`;
  - `ActiveViewDocument == null`;
  - `Document.IsUIVisible == false`;
  - `Document.Views` пуст;
  - `RibbonBar.TabCount == 0`.

Следствие: интерактивные mate-команды (`CreateMate` и соседние) через `RunSystemCommand(...)` не стартуют, даже при корректной 3D-сборке.

---

## 4) Область имплементации

### 4.1 Helper-слой (обязательный)

1. `TFlexEasyBoolean`
2. `TFlexEasySketchProfiles`
3. `TFlexEasyEvidence`
4. `TFlexEasyReopen`
5. расширение `TFlexEasySolids`
6. `TFlexEasyWorkplanes`
7. `TFlexEasyFeatures`
8. `TFlexEasyAssemblyBuild`
9. расширение `TFlexEasyAssemblyValidation`
10. `TFlexEasyMateInspector`
11. `TFlexEasyCommandProbe`
12. расширение `TFlexEasyExport`

### 4.2 Recipe/CLI слой (обязательный)

1. Полный набор helper-рецептов с metadata/markdown.
2. Проверки freshness/verified для recipe-контрактов.
3. `new-helper-recipe` scaffold (если не закрыто полностью — дозакрыть).

### 4.3 Native mate track (обязательный)

1. Подтвердить путь получения **положительного** native mate (`MateEdgeCount > 0`).
2. Развести два режима:
   - headless harness (ограниченный по UI);
   - in-process UI plugin режим (полный UI-контекст команд).

---

## 5) Детальный план по фазам

## Фаза A — Стабилизация helper-платформы

### A1. API-контракты helper’ов
- Уточнить/зафиксировать публичные сигнатуры helper-классов.
- Проверить обратную совместимость helper-set’ов в `runner.py`.

**Критерий готовности:** все helper-сборки проходят `compile_only`.

### A2. Единый формат live-evidence
- Нормализовать ключи stdout (`*.expectedClean`, `*.saved`, `*.bbox`, `*.count`).
- Зафиксировать шаблон markdown-отчёта recipe.

**Критерий готовности:** у каждого helper-рецепта есть одинаково читаемое доказательство.

---

## Фаза B — Закрытие функционального helper-backlog

### B1. Геометрия детали
- Профили: rectangle/rounded rectangle/triangle/slot/obround/lug.
- Примитивы: block/cylinder по осям X/Y/Z, именованные cutters.
- Булевы: unite/subtract + предсказуемые параметры blend/chamfer.

**Критерий:** live-рецепт строит целевые тела с валидным bbox.

### B2. Готовые feature-блоки
- base plate, lug pair, mounting hole pattern;
- horizontal bore cutter;
- triangular lightening cutout;
- reinforcing rib;
- round transitions.

**Критерий:** feature-рецепты дают ожидаемое число операций/тел + сохранение GRB.

### B3. Save/Reopen/Evidence/Export
- `SaveCloseReopen3D`, `VerifyReopened`.
- `Export.All`, `VerifyNonEmpty`, `ExportManifest`.
- Учет известной особенности STEP (файл может сохраниться при `Export=false`).

**Критерий:** live-пакет экспортов стабильно не-пустой; reopen-проверка положительная.

---

## Фаза C — Сборка и валидация

### C1. Сборочный bootstrap
- Надёжный путь через `Fragment3D + PointsLCS + FixByFragmentLCS`.
- Фиксированные и плавающие фрагменты через helper-API.

**Критерий:** рецепты корректно различают grounded/floating.

### C2. Политики валидации
- `allowContact`;
- `allowedOverlapPairs`;
- `ignoredOperationNames`;
- `ignoredBodyNames`;
- JSON summary writer.

**Критерий:** policy-рецепты показывают разные исходы при одинаковой геометрии.

---

## Фаза D — Native mates (главный риск и главный блокер)

### D1. Разделение execution-контуров

#### D1.1 Headless harness контур
- Сохранить текущую диагностику UI-ограничения как факт.
- Не ожидать от него интерактивных mate-команд.

#### D1.2 UI plugin контур (новый обязательный шаг)
- Поднять in-process плагин в живом окне T-FLEX.
- Включить «имена команд Open API» в подсказках.
- Проверить `RunSystemCommand("CreateMate", ...)` в активном UI-документе.

**Критерий:** есть run-доказательство, что в UI-контуре команда хотя бы стартует.

### D2. Положительный native mate кейс
- Создать/открыть сборку с реальным mate (через UI).
- Сохранить `.grb`.
- Переоткрыть в harness и получить `Document3D.GetMates(doc).Count > 0`.
- Подтвердить ребра графа: `Operation1/Operation2` или эквивалентное связанное доказательство.

**Критерий:** зафиксирован первый `MateEdgeCount > 0` с run_dir.

### D3. Инспекция и граф
- Расширить `EasyMateInspector`: owner mapping, relation graph dump.
- Вывести причины «не связалось» в понятных кодах.

**Критерий:** диагностический отчёт объясняет каждую связь/несвязь.

---

## Фаза E — Тесты, документация, контракт релиза

### E1. Тесты
- Unit: recipes metadata/freshness/helper contracts.
- Smoke: ключевые helper-рецепты.
- Live (точечно): только критические ветки.

### E2. Документация
- `verified-api-facts.md` — только подтверждённые live-факты.
- `fragments-mates-selection.md` — актуальные гипотезы/ограничения/пруфы.
- `README.md`/`install.md` — команды запуска и ожидания.

### E3. Гейт «готово»
- Любой заявленный сценарий имеет compile + live evidence.
- Нет «success без доказательства».

---

## 6) Порядок исполнения (приоритеты)

1. **P0:** UI plugin контур для native mate команд (разблокировка основной неопределенности).
2. **P1:** Положительный native mate `.grb` + `MateEdgeCount > 0`.
3. **P2:** Завершение policy-расширений assembly validation.
4. **P3:** Финишное выравнивание helper-рецептов и metadata freshness.
5. **P4:** Документация/тестовый гейт релиза.

---

## 7) Артефакты, которые должны появиться

1. Live run dirs для UI plugin mate-проверок.
2. Минимум один эталонный `.grb` с реальным native mate.
3. JSON/markdown отчёт инспектора mate-графа.
4. Обновлённые recipe metadata с fresh hashes.

---

## 8) Риски и меры

### Риск R1: Команда существует, но не стартует в headless
**Мера:** запуск через UI plugin контур, не тратить циклы на blind brute-force в headless.

### Риск R2: Нестабильность макро/loader окружения
**Мера:** зафиксировать зависимости окружения и отдельный bootstrap для plugin-контура.

### Риск R3: Ложные выводы из docs/forum
**Мера:** считать источники только гипотезой, истина — только live evidence.

---

## 9) Definition of Done (финал)

План считается реализованным, когда:

1. helper-backlog закрыт и подтверждён live-рецептами;
2. assembly validation имеет policy-режимы и стабильные отчёты;
3. native mate путь доказан положительным кейсом (`MateEdgeCount > 0`);
4. документация и тесты синхронизированы с фактическим состоянием.

---

## 10) Ближайшие практические шаги (следующий спринт)

1. Поднять минимальный UI plugin execution path для команды mate.
2. Снять первый live run: активный UI-документ + `RunSystemCommand("CreateMate", ...)`.
3. Создать и сохранить эталонную сборку с UI-created mate.
4. Переоткрыть в harness, подтвердить `GetMates(...) > 0`.
5. Добавить recipe-пруф + обновить verified facts.
