"""Tests for the repo analyzer."""

import tempfile
from pathlib import Path

from gitcontext.analyzer import RepoAnalyzer
from gitcontext.detectors.language import detect_languages
from gitcontext.generators.claude_md import generate_claude_md


def test_detect_languages_python():
    files = ["main.py", "utils.py", "tests/test_main.py", "README.md"]
    langs = detect_languages(files)
    assert langs[0][0] == "Python"
    assert langs[0][1] == 100.0


def test_detect_languages_mixed():
    files = ["app.py", "index.ts", "helper.ts", "README.md"]
    langs = detect_languages(files)
    assert len(langs) == 2
    assert langs[0][0] == "TypeScript"
    assert langs[1][0] == "Python"


def test_analyzer_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "pyproject.toml").write_text(
            '[project]\nname = "testproj"\nversion = "0.1.0"\n'
            'description = "A test project"\ndependencies = ["click"]\n'
        )
        (p / "main.py").write_text("print('hello')\n")
        (p / "tests").mkdir()
        (p / "tests" / "test_main.py").write_text("def test_ok(): pass\n")

        analyzer = RepoAnalyzer(tmpdir)
        ctx = analyzer.analyze()

        assert ctx.name == Path(tmpdir).name
        assert ctx.description == "A test project"
        assert ctx.languages[0][0] == "Python"


def test_generate_claude_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "pyproject.toml").write_text(
            '[project]\nname = "myapp"\nversion = "1.0.0"\n'
            'description = "My awesome app"\n'
            'dependencies = ["fastapi", "pydantic"]\n'
            '\n[project.scripts]\nmyapp = "myapp.cli:main"\n'
        )
        (p / "src").mkdir()
        (p / "src" / "myapp").mkdir()
        (p / "src" / "myapp" / "__init__.py").write_text("")
        (p / "src" / "myapp" / "cli.py").write_text("def main(): pass\n")
        (p / "tests").mkdir()
        (p / "tests" / "test_app.py").write_text("def test_ok(): pass\n")

        analyzer = RepoAnalyzer(tmpdir)
        ctx = analyzer.analyze()
        md = generate_claude_md(ctx)

        assert "myapp" in md
        assert "My awesome app" in md
        assert "FastAPI" in md
        assert "Pydantic" in md


def test_analyzer_empty_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = RepoAnalyzer(tmpdir)
        ctx = analyzer.analyze()
        assert ctx.name == Path(tmpdir).name
        # Should not crash
        md = generate_claude_md(ctx)
        assert ctx.name in md
