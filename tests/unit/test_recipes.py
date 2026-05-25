import hashlib
import json

from tflex_harness.config import HarnessConfig, load_config
from tflex_harness import recipes as recipes_module
from tflex_harness.recipes import RecipeRegistry, list_recipes, run_recipe


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_list_recipes_includes_verified_baseline():
    names = {recipe["name"] for recipe in list_recipes()}
    assert "environment_probe" in names
    assert "create_empty_document" in names
    assert "save_document_as_temp" in names
    assert "create_simple_2d_line" in names
    assert "create_simple_3d_extrusion" in names
    assert "helper_environment_probe" in names
    assert "helper_simple_extrusion" in names
    assert "helper_step_export" in names
    assert "helper_planetary_static_assembly" in names
    assert "prototype_open_copy_save" in names
    assert "prototype_set_text_variable" in names
    assert "prototype_set_real_variable" in names
    assert "prototype_set_table_cell" in names
    assert "prototype_set_document_property" in names


def test_helper_recipes_are_fresh_and_use_all_helpers():
    recipes = {recipe["name"]: recipe for recipe in list_recipes()}
    for name in {
        "helper_environment_probe",
        "helper_simple_extrusion",
        "helper_step_export",
        "helper_planetary_static_assembly",
    }:
        recipe = recipes[name]
        assert recipe["verified"] is True
        assert recipe["freshness"]["status"] == "fresh"
        assert recipe["helpers"] == ["all"]


def test_prototype_recipe_is_fresh_and_uses_prototype_helpers():
    recipes = {recipe["name"]: recipe for recipe in list_recipes()}
    recipe = recipes["prototype_open_copy_save"]

    assert recipe["verified"] is True
    assert recipe["freshness"]["status"] == "fresh"
    assert recipe["helpers"] == ["easy_prototype"]

    mutation = recipes["prototype_set_text_variable"]
    assert mutation["verified"] is True
    assert mutation["freshness"]["status"] == "fresh"
    assert mutation["helpers"] == ["easy_variables"]

    real_mutation = recipes["prototype_set_real_variable"]
    assert real_mutation["verified"] is True
    assert real_mutation["freshness"]["status"] == "fresh"
    assert real_mutation["helpers"] == ["easy_variables"]

    table_mutation = recipes["prototype_set_table_cell"]
    assert table_mutation["verified"] is True
    assert table_mutation["freshness"]["status"] == "fresh"
    assert table_mutation["helpers"] == ["easy_text"]

    doc_property = recipes["prototype_set_document_property"]
    assert doc_property["verified"] is True
    assert doc_property["freshness"]["status"] == "fresh"
    assert doc_property["helpers"] == ["easy_document_properties"]


def test_each_verified_recipe_has_markdown_and_csharp_source():
    cfg = load_config()
    recipes_dir = cfg.repo_dir / "agent_workspace" / "recipes"

    for recipe in list_recipes():
        if recipe["verified"]:
            assert recipe["markdown_path"] == str(recipes_dir / f"{recipe['name']}.md")
            assert recipe["source_path"] == str(recipes_dir / f"{recipe['name']}.cs")
            assert recipe["markdown_exists"] is True
            assert recipe["source_exists"] is True
            assert (recipes_dir / f"{recipe['name']}.md").exists(), recipe
            assert (recipes_dir / f"{recipe['name']}.cs").exists(), recipe


def test_each_verified_recipe_has_live_verification_report():
    cfg = load_config()
    recipes_dir = cfg.repo_dir / "agent_workspace" / "recipes"
    required_phrases = [
        "## Live Verification Report",
        "Test:",
        "Docs used:",
        "Snippet:",
        "Result:",
        "Evidence:",
        "Blockers:",
    ]

    for recipe in list_recipes():
        if recipe["verified"]:
            text = (recipes_dir / f"{recipe['name']}.md").read_text(encoding="utf-8")
            for phrase in required_phrases:
                assert phrase in text, (recipe["name"], phrase)


def test_unknown_recipe_returns_structured_input_error():
    result = run_recipe("missing_recipe", timeout_sec=1)

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "unknown recipe"
    assert result["recipe"] == "missing_recipe"
    assert "environment_probe" in result["known_recipes"]


def test_recipe_output_file_must_stay_under_artifacts(tmp_path):
    outside = tmp_path / "outside.grb"

    result = run_recipe("create_empty_document", args={"output_file": str(outside)}, timeout_sec=1)

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "recipe output_file must be under artifacts/tflex_docs"
    assert result["recipe"] == "create_empty_document"
    assert result["allowed_output_root"].endswith("artifacts\\tflex_docs")
    assert not outside.exists()


def test_run_recipe_result_exposes_source_contract(monkeypatch):
    def fake_run_csharp_snippet(*args, **kwargs):
        return {"ok": True, "stage": "run", "stdout": "init=True", "artifacts": []}

    monkeypatch.setattr(recipes_module, "run_csharp_snippet", fake_run_csharp_snippet)

    result = run_recipe("environment_probe", timeout_sec=1)

    assert result["ok"] is True
    assert result["recipe_info"]["source_path"].endswith("agent_workspace\\recipes\\environment_probe.cs")
    assert result["recipe_info"]["markdown_path"].endswith("agent_workspace\\recipes\\environment_probe.md")
    assert result["recipe_info"]["source_exists"] is True
    assert result["recipe_info"]["markdown_exists"] is True


def test_run_recipe_passes_helper_metadata(monkeypatch):
    calls = []

    def fake_run_csharp_snippet(*args, **kwargs):
        calls.append(kwargs)
        return {"ok": True, "stage": "run", "stdout": "helper=true", "artifacts": []}

    monkeypatch.setattr(recipes_module, "run_csharp_snippet", fake_run_csharp_snippet)

    result = run_recipe("helper_environment_probe", timeout_sec=1)

    assert result["ok"] is True
    assert calls[-1]["helpers"] == ["all"]


def test_prototype_recipe_requires_source_or_catalog_id(monkeypatch):
    def fake_run_csharp_snippet(*args, **kwargs):
        raise AssertionError("run should not start without a source")

    monkeypatch.setattr(recipes_module, "run_csharp_snippet", fake_run_csharp_snippet)

    result = run_recipe("prototype_open_copy_save", timeout_sec=1)

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "source_path or prototype_id is required"


def test_prototype_set_text_variable_requires_variable_name(tmp_path, monkeypatch):
    source = tmp_path / "demo.grb"
    source.write_bytes(b"demo")

    def fake_run_csharp_snippet(*args, **kwargs):
        raise AssertionError("run should not start without variable name")

    monkeypatch.setattr(recipes_module, "run_csharp_snippet", fake_run_csharp_snippet)

    result = run_recipe("prototype_set_text_variable", args={"source_path": str(source)}, timeout_sec=1)

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "variable_name is required"


def test_prototype_set_real_variable_requires_variable_name(tmp_path, monkeypatch):
    source = tmp_path / "demo.grb"
    source.write_bytes(b"demo")

    def fake_run_csharp_snippet(*args, **kwargs):
        raise AssertionError("run should not start without variable name")

    monkeypatch.setattr(recipes_module, "run_csharp_snippet", fake_run_csharp_snippet)

    result = run_recipe("prototype_set_real_variable", args={"source_path": str(source), "real_value": "42"}, timeout_sec=1)

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "variable_name is required"


def test_prototype_set_real_variable_requires_real_value(tmp_path, monkeypatch):
    source = tmp_path / "demo.grb"
    source.write_bytes(b"demo")

    def fake_run_csharp_snippet(*args, **kwargs):
        raise AssertionError("run should not start without real value")

    monkeypatch.setattr(recipes_module, "run_csharp_snippet", fake_run_csharp_snippet)

    result = run_recipe("prototype_set_real_variable", args={"source_path": str(source), "variable_name": "Length"}, timeout_sec=1)

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "real_value is required"


def test_prototype_set_table_cell_requires_cell_index(tmp_path, monkeypatch):
    source = tmp_path / "demo.grb"
    source.write_bytes(b"demo")

    def fake_run_csharp_snippet(*args, **kwargs):
        raise AssertionError("run should not start without cell index")

    monkeypatch.setattr(recipes_module, "run_csharp_snippet", fake_run_csharp_snippet)

    result = run_recipe("prototype_set_table_cell", args={"source_path": str(source), "text_value": "x"}, timeout_sec=1)

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "cell_index is required"


def test_prototype_set_document_property_requires_property_name(tmp_path, monkeypatch):
    source = tmp_path / "demo.grb"
    source.write_bytes(b"demo")

    def fake_run_csharp_snippet(*args, **kwargs):
        raise AssertionError("run should not start without property name")

    monkeypatch.setattr(recipes_module, "run_csharp_snippet", fake_run_csharp_snippet)

    result = run_recipe("prototype_set_document_property", args={"source_path": str(source), "text_value": "x"}, timeout_sec=1)

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "property_name is required"


def test_recipe_registry_marks_hash_mismatch_unverified(tmp_path):
    recipes_dir = tmp_path / "agent_workspace" / "recipes"
    recipes_dir.mkdir(parents=True)
    source = recipes_dir / "demo.cs"
    markdown = recipes_dir / "demo.md"
    source.write_text("public class Program {}", encoding="utf-8")
    markdown.write_text(
        "\n".join(
            [
                "## Live Verification Report",
                "Test:",
                "Docs used:",
                "Snippet:",
                "Result:",
                "Evidence:",
                "Blockers:",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "name": "demo",
        "description": "Demo",
        "args": {},
        "verified": True,
        "last_verified": "2026-05-24",
        "source": "demo.cs",
        "evidence": "demo.md",
        "limitations": [],
        "source_sha256": _hash(source),
        "markdown_sha256": _hash(markdown),
    }
    (recipes_dir / "demo.recipe.json").write_text(json.dumps(metadata), encoding="utf-8")
    cfg = HarnessConfig(
        repo_dir=tmp_path,
        docs_dir=tmp_path / "docs",
        tflex_install_dir=tmp_path / "tflex",
        tflex_program_dir=tmp_path / "tflex" / "Program",
        runner_dir=tmp_path / "runner",
        artifacts_dir=tmp_path / "artifacts",
        logs_dir=tmp_path / "logs",
    )
    registry = RecipeRegistry(cfg)

    assert registry.definition("demo")["verified"] is True
    source.write_text("public class Program { static int Main(){ return 0; } }", encoding="utf-8")
    stale = registry.definition("demo")

    assert stale["verified"] is False
    assert stale["freshness"]["status"] == "stale"
    assert "source hash mismatch" in stale["freshness"]["reasons"]
