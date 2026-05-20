from tflex_harness.config import load_config
from tflex_harness.recipes import list_recipes


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
