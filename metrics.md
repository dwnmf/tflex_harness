# Install Simplicity Metrics

Date: 2026-05-28.

Goal: raise external GitHub install simplicity from `5/10` to `8/10+`.

## Current Score

| Audience | Baseline | Current | Target | Status |
|---|---:|---:|---:|---|
| External GitHub user | 5/10 | 8/10 | 8/10 | Target reached locally |
| Target user: Windows + T-FLEX CAD 17 | 7/10 | 8.6/10 | 8.5/10 | Target reached locally |

## Funnel Metrics

| Metric | Baseline | Current | Target | Evidence | Status |
|---|---:|---:|---:|---|---|
| Commands to first green install readiness | 5 | 4 | ≤ 4 | `README.md` simple install; `bootstrap --full` runs doctor | Done |
| Commands after package install | 3 | 1 | 1 | `bootstrap --full` now runs install readiness checks | Done |
| First-screen prerequisites visible | Partial | Yes | Yes | `README.md` requirements block | Done |
| One-command bootstrap alias | No | Yes | Yes | `tflex-harness bootstrap --full`; verified by targeted tests | Done |
| Manual env vars on happy path | 0 | 0 | 0 | `bootstrap --full` persists `TFLEX_HARNESS_REPO_DIR` and `TFLEX_API_DOCS_DIR` | Done |
| Human-readable next steps | Partial | Better | Full | `bootstrap --full` reports readiness, optional follow-ups, and doctor fix hints | In progress |
| Broken release promise | Yes | Release create/update workflow added | No | `.github/workflows/release-build.yml`; local wheel/sdist build passed | In progress |
| Wheel/full-checkout behavior explicit | Partial | Clear + diagnosed | Clear | `install.md` wheel status; `doctor` reports missing `repo_workspace` with `TFLEX_HARNESS_REPO_DIR` fix | Done |
| Clean install CI | Unknown | Added | Green on PR | `.github/workflows/install-smoke.yml` | In progress |
| MCP config manual edit | Yes | Generated | Generated | `tflex-harness mcp-config --for codex|claude` | Done |
| Doctor/fix hints | Partial | Implemented | 100% blockers include fix hints | `tflex-harness doctor`; includes T-FLEX/docs/repo/python/git/uv/dotnet/csc/runner | Done |

## Completed Changes

- Added `tflex-harness bootstrap --full`.
- `--full` enables docs handling, persisted env, Codex skill registration, and checks.
- `bootstrap` now reports `full` and a compile-only verification command in `next`.
- Updated `README.md` first install path to use `bootstrap --full`.
- Added first-screen requirements to `README.md`.
- Changed release wording from promised releases to secondary wheel status.
- Updated `install.md` to document `--full` and wheel/checkout status.
- Added `tflex-harness doctor` with install readiness checks and fix hints.
- Added doctor coverage for fake blockers and CLI output.
- Added `tflex-harness mcp-config --for codex|claude`.
- Added MCP config unit and CLI smoke coverage.
- Added Windows editable install smoke workflow.
- Documented install CI contract in `README.md` and `install.md`.
- Added `git` and optional `uv` checks to `doctor`.
- `bootstrap --full` now runs install readiness checks through `doctor`.
- Reduced README/install happy path to four commands: clone, `cd`, install, bootstrap.
- Added release-build workflow for wheel + sdist artifacts and tag releases.
- Updated release-build workflow to create missing releases or update existing releases with `--clobber`.
- Added manual release update inputs: `publish_release=true` and `tag=v<version>`.
- Verified local `python -m build` and clean venv wheel smoke install.
- Removed stale `goal.md` include from `MANIFEST.in` to keep package builds warning-free.
- Added `repo_workspace` doctor check for wheel users without a checkout.
- Decided recipes remain checkout-owned; wheel installs are supported but diagnosed as needing `TFLEX_HARNESS_REPO_DIR` for full recipe/helper workspace behavior.
- Updated repo-root detection to use existing markers: `AGENTS.md`, `.agents`, and `install.md`.
- Unified custom docs path snippets on `bootstrap --docs-dir <path> --full`.
- `bootstrap --docs-dir` now updates current process env before checks/doctor.

## Next Optimization Targets

1. Observe first GitHub Actions `install-smoke` run on PR/push.
2. Observe first GitHub Actions `release-build` run on PR/tag/manual release update; current GitHub releases API check returned `404`.
3. Add PATH-specific fix hints if user reports command discovery issues.
4. Observe real release creation/update after a `v*` tag or manual workflow run.
5. Observe real clean install from published release assets.

## Verification Log

Passed after current edits:

- `python -m pytest tests/unit/test_bootstrap.py -v`
- `python -m pytest tests/smoke/test_cli.py::test_cli_bootstrap_dry_path_has_no_external_side_effects -v`
- `$env:PYTHONPATH='src'; python -m tflex_harness.cli bootstrap --help`
- `python -m pytest tests/smoke/test_environment.py::test_install_doctor_returns_fix_hints_for_missing_components tests/smoke/test_cli.py::test_cli_doctor_reports_install_checks -v`
- `$env:PYTHONPATH='src'; python -m tflex_harness.cli doctor` — local score `8/8`, `ok=true`
- `$env:PYTHONPATH='src'; python -m tflex_harness.cli --help | Select-String -Pattern "doctor|bootstrap"`
- `python -m pytest tests/unit/test_mcp_config.py tests/smoke/test_cli.py::test_cli_mcp_config_prints_ready_json -v`
- `$env:PYTHONPATH='src'; python -m tflex_harness.cli mcp-config --for codex`
- `$env:PYTHONPATH='src'; python -m tflex_harness.cli mcp-config --for claude`
- `python -m pytest tests/unit/test_bootstrap.py tests/unit/test_mcp_config.py tests/smoke/test_environment.py::test_install_doctor_returns_fix_hints_for_missing_components tests/smoke/test_cli.py::test_cli_bootstrap_dry_path_has_no_external_side_effects tests/smoke/test_cli.py::test_cli_doctor_reports_install_checks tests/smoke/test_cli.py::test_cli_mcp_config_prints_ready_json -v` — `6 passed`
- Workflow readback check for `.github/workflows/install-smoke.yml` — `workflow-ok`
- `$env:PYTHONPATH='src'; python -c "import mcp; import tflex_harness.mcp_server; print('mcp-import-ok')"`
- `python -m pytest tests/smoke/test_environment.py::test_install_doctor_returns_fix_hints_for_missing_components tests/smoke/test_cli.py::test_cli_doctor_reports_install_checks -v`
- `$env:PYTHONPATH='src'; python -m tflex_harness.cli doctor` — local score `10/10`, `ok=true`
- `python -m pytest tests/unit/test_bootstrap.py tests/unit/test_mcp_config.py tests/smoke/test_cli.py::test_cli_bootstrap_dry_path_has_no_external_side_effects tests/smoke/test_cli.py::test_cli_doctor_reports_install_checks tests/smoke/test_cli.py::test_cli_mcp_config_prints_ready_json -v` — `5 passed`
- `python -m pytest tests/unit/test_bootstrap.py tests/smoke/test_cli.py::test_cli_bootstrap_dry_path_has_no_external_side_effects -v` — `2 passed`
- `$env:PYTHONPATH='src'; python -m tflex_harness.cli bootstrap --no-docs --no-checks`
- README/install readback confirms happy path is four commands.
- `python -m pytest tests/unit/test_bootstrap.py tests/unit/test_mcp_config.py tests/smoke/test_environment.py::test_install_doctor_returns_fix_hints_for_missing_components tests/smoke/test_cli.py::test_cli_bootstrap_dry_path_has_no_external_side_effects tests/smoke/test_cli.py::test_cli_doctor_reports_install_checks tests/smoke/test_cli.py::test_cli_mcp_config_prints_ready_json -v` — `6 passed`
- `python -m build` — built `tflex_harness-0.2.0.tar.gz` and `tflex_harness-0.2.0-py3-none-any.whl`
- Release version bump prepared: `0.2.1`.
- `python -m build` — built `tflex_harness-0.2.1.tar.gz` and `tflex_harness-0.2.1-py3-none-any.whl`.
- Clean temporary venv `0.2.1` wheel smoke: install wheel + `mcp>=1.0`, `tflex-harness --help`, `bootstrap --no-docs --no-checks`, `mcp-config --for codex` — `wheel-smoke-ok`.
- Clean temporary venv wheel smoke: install wheel + `mcp>=1.0`, `tflex-harness --help`, `bootstrap --no-docs --no-checks`, `mcp-config --for codex` — `wheel-smoke-ok`
- Removed local generated `build/` and `dist/` after verification.
- GitHub releases API check for `dwnmf/tflex_harness` returned `404`; release workflow is prepared to create first release or update existing tag release.
- Release update workflow contract check — `release-update-workflow-ok`.
- Manual release workflow contract check — `manual-release-workflow-ok`.
- First `release-build` tag run reached build/smoke but failed on `actions/upload-artifact` quota; made artifact upload non-blocking with one-day retention because release assets are uploaded through GitHub releases.
- `python -m pytest tests/smoke/test_environment.py::test_install_doctor_reports_missing_repo_workspace tests/smoke/test_cli.py::test_cli_doctor_reports_install_checks -v` — `2 passed`
- `$env:PYTHONPATH='src'; python -m tflex_harness.cli doctor` — local score `11/11`, `ok=true`
- `python -m pytest tests/unit/test_bootstrap.py tests/smoke/test_environment.py::test_install_doctor_returns_fix_hints_for_missing_components tests/smoke/test_environment.py::test_install_doctor_reports_missing_repo_workspace tests/smoke/test_cli.py::test_cli_doctor_reports_install_checks -v` — `4 passed`
- `python -m pytest tests/unit/test_agent_workspace_helpers.py tests/unit/test_config.py::test_config_defaults_point_to_existing_docs -v` — `3 passed`
- `python -m pytest tests/unit/test_bootstrap.py tests/unit/test_mcp_config.py tests/unit/test_agent_workspace_helpers.py tests/smoke/test_environment.py::test_install_doctor_returns_fix_hints_for_missing_components tests/smoke/test_environment.py::test_install_doctor_reports_missing_repo_workspace tests/smoke/test_cli.py::test_cli_bootstrap_dry_path_has_no_external_side_effects tests/smoke/test_cli.py::test_cli_doctor_reports_install_checks tests/smoke/test_cli.py::test_cli_mcp_config_prints_ready_json -v` — `9 passed`
- `python -m pytest tests/unit/test_bootstrap.py -v` — `2 passed`
- `$env:PYTHONPATH='src'; python -m tflex_harness.cli bootstrap --docs-dir D:\REALPROJECTS\tflex_api --no-docs --no-checks`
- `install.md` readback confirms all `bootstrap --docs-dir` snippets use `--full`.
- `python -m pytest tests/unit/test_bootstrap.py tests/unit/test_mcp_config.py tests/unit/test_agent_workspace_helpers.py tests/smoke/test_environment.py::test_install_doctor_returns_fix_hints_for_missing_components tests/smoke/test_environment.py::test_install_doctor_reports_missing_repo_workspace tests/smoke/test_cli.py::test_cli_bootstrap_dry_path_has_no_external_side_effects tests/smoke/test_cli.py::test_cli_doctor_reports_install_checks tests/smoke/test_cli.py::test_cli_mcp_config_prints_ready_json -v` — `10 passed`

Note: pytest exited `0` but Windows printed a temp symlink cleanup `PermissionError` from pytest atexit.
