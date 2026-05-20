from tflex_harness.recipes import list_recipes


def test_list_recipes_includes_verified_baseline():
    names = {recipe["name"] for recipe in list_recipes()}
    assert "environment_probe" in names
    assert "create_empty_document" in names
    assert "create_simple_2d_line" in names
