from tflex_harness.runner import parse_csc_diagnostics


def test_parse_csc_diagnostics():
    text = r"C:\tmp\Snippet.cs(7,13): error CS0246: The type or namespace name 'Foo' could not be found"
    diagnostics = parse_csc_diagnostics(text)
    assert diagnostics == [{
        "file": r"C:\tmp\Snippet.cs",
        "line": 7,
        "column": 13,
        "severity": "error",
        "code": "CS0246",
        "message": "The type or namespace name 'Foo' could not be found",
    }]
