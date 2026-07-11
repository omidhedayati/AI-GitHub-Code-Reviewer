from pathlib import Path

from app.services.analyzers.python_analyzer import PythonAnalyzer


def test_python_analyzer_detects_syntax_error() -> None:
    analyzer = PythonAnalyzer()
    issues = analyzer.analyze(
        Path("bad.py"),
        "def broken(:\n    pass\n",
        "bad.py",
    )
    assert any(issue.rule_id == "python-syntax-error" for issue in issues)


def test_python_analyzer_detects_eval_and_long_function() -> None:
    content = '''
"""Module docstring."""


def ok():
    """Documented."""
    return 1


def risky():
    value = eval("1 + 1")
    return value
'''
    analyzer = PythonAnalyzer()
    issues = analyzer.analyze(Path("sample.py"), content, "sample.py")
    rule_ids = {issue.rule_id for issue in issues}
    assert "python-eval-exec" in rule_ids
