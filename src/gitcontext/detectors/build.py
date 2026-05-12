"""Detect build system and extract commands."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from gitcontext.utils import read_file_safe


@dataclass
class BuildInfo:
    system: str = ""
    install_cmd: str = ""
    build_cmd: str = ""
    run_cmd: str = ""
    lint_cmd: str = ""
    extra_commands: dict[str, str] = field(default_factory=dict)


def detect_build_system(repo_path: Path, files: list[str]) -> BuildInfo:
    """Detect build system and extract relevant commands."""
    info = BuildInfo()

    # Python: uv / poetry / pip
    if "pyproject.toml" in files:
        pyproject = read_file_safe(repo_path / "pyproject.toml") or ""
        if "uv.lock" in files or "[tool.uv]" in pyproject:
            info.system = "uv"
            info.install_cmd = "uv sync --locked"
            info.run_cmd = "uv run python"
        elif "[tool.poetry]" in pyproject:
            info.system = "Poetry"
            info.install_cmd = "poetry install"
            info.run_cmd = "poetry run python"
        else:
            info.system = "pip"
            info.install_cmd = "pip install -e ."
            info.run_cmd = "python"

        # Don't override run_cmd with scripts - those go to entry_points

    elif "requirements.txt" in files:
        info.system = "pip"
        info.install_cmd = "pip install -r requirements.txt"
        info.run_cmd = "python"

    # JavaScript/TypeScript: npm / yarn / pnpm
    elif "package.json" in files:
        pkg_content = read_file_safe(repo_path / "package.json")
        if "pnpm-lock.yaml" in files:
            info.system = "pnpm"
            info.install_cmd = "pnpm install"
        elif "yarn.lock" in files:
            info.system = "Yarn"
            info.install_cmd = "yarn install"
        else:
            info.system = "npm"
            info.install_cmd = "npm install"

        if pkg_content:
            try:
                pkg = json.loads(pkg_content)
                scripts = pkg.get("scripts", {})
                if "build" in scripts:
                    info.build_cmd = f"{info.system} run build"
                if "dev" in scripts:
                    info.run_cmd = f"{info.system} run dev"
                elif "start" in scripts:
                    info.run_cmd = f"{info.system} run start"
                if "lint" in scripts:
                    info.lint_cmd = f"{info.system} run lint"
            except json.JSONDecodeError:
                pass

    # Rust
    elif "Cargo.toml" in files:
        info.system = "Cargo"
        info.install_cmd = "cargo build"
        info.build_cmd = "cargo build --release"
        info.run_cmd = "cargo run"

    # C/C++
    elif "CMakeLists.txt" in files:
        info.system = "CMake"
        info.install_cmd = "cmake -B build && cmake --build build"
        info.build_cmd = "cmake --build build"

    # Go
    elif "go.mod" in files:
        info.system = "Go modules"
        info.install_cmd = "go mod download"
        info.build_cmd = "go build ./..."
        info.run_cmd = "go run ."

    # Makefile as supplementary
    if "Makefile" in files:
        makefile = read_file_safe(repo_path / "Makefile") or ""
        targets = re.findall(r"^([a-zA-Z_][a-zA-Z0-9_-]*):", makefile, re.MULTILINE)
        if not info.system:
            info.system = "Make"
            info.install_cmd = "make"
        if "lint" in targets and not info.lint_cmd:
            info.lint_cmd = "make lint"
        if "test" in targets:
            info.extra_commands["test"] = "make test"

    # pre-commit
    if ".pre-commit-config.yaml" in files and not info.lint_cmd:
        info.lint_cmd = "pre-commit run --all-files"

    return info
