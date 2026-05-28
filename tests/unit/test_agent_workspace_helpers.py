import importlib.util


def _load_helpers():
    path = "agent_workspace/helpers.py"
    spec = importlib.util.spec_from_file_location("agent_workspace_helpers", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_agent_workspace_helpers_find_repo_and_recipes():
    helpers = _load_helpers()

    root = helpers.repo_root()

    assert (root / "AGENTS.md").exists()
    assert (root / "install.md").exists()
    assert helpers.recipes_dir(root).name == "recipes"
    assert helpers.recipe_source_path("environment_probe", ".cs", root).exists()
    assert helpers.recipe_source_path("environment_probe", ".md", root).exists()


def test_agent_workspace_helpers_json_roundtrip(tmp_path):
    helpers = _load_helpers()
    path = tmp_path / "payload.json"

    helpers.write_json(path, {"ok": True, "value": 3})

    assert helpers.read_json(path) == {"ok": True, "value": 3}
