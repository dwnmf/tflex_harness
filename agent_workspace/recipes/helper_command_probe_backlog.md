# helper_command_probe_backlog

## Live Verification Report

Test: `python -m tflex_harness.cli run-recipe helper_command_probe_backlog --timeout-sec 60`

Docs used: `goal.md`; T-FLEX API docs for `Application.RunSystemCommand`; T-FLEX forum evidence for `ZoomMax` command name; local `CommandInfo` list.

Snippet: `agent_workspace/recipes/helper_command_probe_backlog.cs`

Result: passed live in T-FLEX CAD 17.

Evidence:

- Run: `artifacts/runs/20260527_121244_863443_recipe_helper_command_probe_backlog`
- `commandProbe.listKnownCommands.available=True`
- `commandProbe.listKnownCommands.count=195`
- `commandProbe.listKnownCommands.hasCreateMate=True`
- `commandProbe.name=ZoomMax`
- `commandProbe.started=True`
- `commandProbe.error=null`
- `commandProbe.name=CreateMate`
- `commandProbe.started=False`
- `commandProbe.error=InvalidOperationException: Specified command not found`
- `commandRecipe.listOk=True`
- `commandRecipe.zoomMaxOk=True`
- `commandRecipe.createMateRejected=True`
- `commandRecipe.expectedClean=True`

Blockers: `RunSystemCommand("CreateMate", ...)` still rejected; need exact mate command invocation/selection sequence or UI-created native-mate `.grb`.
