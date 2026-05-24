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
