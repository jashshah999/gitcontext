"""Detect test framework and patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from gitcontext.utils import read_file_safe


@dataclass
class TestInfo:
    framework: str = ""
    test_command: str = ""
    test_dirs: list[str] = field(default_factory=list)


def detect_testing(repo_path: Path, files: list[str], build_system: str) -> TestInfo:
    """Detect test framework and return info."""
    info = TestInfo()

    # Find test directories
    for f in files:
        parts = f.split("/")
        if len(parts) >= 2 and parts[0] in ("tests", "test", "spec", "__tests__"):
            if parts[0] not in info.test_dirs:
                info.test_dirs.append(parts[0])

    # Python
    pyproject = read_file_safe(repo_path / "pyproject.toml") or ""
    if "pytest" in pyproject or (repo_path / "pytest.ini").exists() or (repo_path / "conftest.py").exists():
        info.framework = "pytest"
        prefix = "uv run " if build_system == "uv" else ""
        info.test_command = f"{prefix}pytest tests"
    elif any(f.startswith("test") and f.endswith(".py") for f in files):
        info.framework = "pytest"
        prefix = "uv run " if build_system == "uv" else ""
        info.test_command = f"{prefix}pytest"

    # JavaScript
    pkg_json = read_file_safe(repo_path / "package.json") or ""
    if "jest" in pkg_json:
        info.framework = "Jest"
        info.test_command = "npm test"
    elif "vitest" in pkg_json:
        info.framework = "Vitest"
        info.test_command = "npm test"
    elif "mocha" in pkg_json:
        info.framework = "Mocha"
        info.test_command = "npm test"

    # Rust
    if build_system == "Cargo":
        info.framework = "cargo test"
        info.test_command = "cargo test"

    # Go
    if build_system == "Go modules":
        info.framework = "go test"
        info.test_command = "go test ./..."

    return info
