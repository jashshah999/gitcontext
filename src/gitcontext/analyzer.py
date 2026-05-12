"""Core analysis engine."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from gitcontext.detectors.build import BuildInfo, detect_build_system
from gitcontext.detectors.ci import CIInfo, detect_ci
from gitcontext.detectors.framework import detect_frameworks
from gitcontext.detectors.language import detect_languages
from gitcontext.detectors.testing import TestInfo, detect_testing
from gitcontext.utils import get_top_level_dirs, read_file_safe, walk_repo


@dataclass
class RepoContext:
    name: str = ""
    description: str = ""
    languages: list[tuple[str, float]] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    build: BuildInfo = field(default_factory=BuildInfo)
    architecture: list[tuple[str, str]] = field(default_factory=list)  # (dir, description)
    entry_points: list[str] = field(default_factory=list)
    ci: CIInfo = field(default_factory=CIInfo)
    test: TestInfo = field(default_factory=TestInfo)
    notable_files: list[str] = field(default_factory=list)


# Heuristic directory descriptions
DIR_DESCRIPTIONS = {
    "src": "Source code",
    "lib": "Library code",
    "tests": "Test suite",
    "test": "Test suite",
    "docs": "Documentation",
    "doc": "Documentation",
    "examples": "Example scripts and tutorials",
    "scripts": "Utility and CLI scripts",
    "config": "Configuration files",
    "configs": "Configuration files",
    "bin": "Executable scripts",
    "cmd": "Command entry points",
    "pkg": "Package code",
    "internal": "Internal packages",
    "api": "API layer",
    "app": "Application code",
    "public": "Static public assets",
    "static": "Static files",
    "templates": "Template files",
    "migrations": "Database migrations",
    "fixtures": "Test fixtures",
    "benchmarks": "Performance benchmarks",
    "tools": "Development tools",
    "deploy": "Deployment configuration",
    "infra": "Infrastructure code",
    "docker": "Docker configuration",
    ".github": "CI/CD workflows",
}


class RepoAnalyzer:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        if not self.path.is_dir():
            raise ValueError(f"Not a directory: {self.path}")

    def analyze(self) -> RepoContext:
        ctx = RepoContext()
        files = walk_repo(self.path)

        # Name and description
        ctx.name = self.path.name
        ctx.description = self._detect_description()

        # Languages
        ctx.languages = detect_languages(files)

        # Frameworks
        ctx.frameworks = detect_frameworks(self.path, files)

        # Build system
        ctx.build = detect_build_system(self.path, files)

        # CI
        ctx.ci = detect_ci(self.path, files)

        # Testing
        ctx.test = detect_testing(self.path, files, ctx.build.system)

        # Architecture
        ctx.architecture = self._detect_architecture()

        # Entry points
        ctx.entry_points = self._detect_entry_points(files)

        # Notable files
        ctx.notable_files = self._detect_notable_files(files)

        return ctx

    def _detect_description(self) -> str:
        """Try to extract a one-line description from README or pyproject."""
        # pyproject.toml description
        pyproject = read_file_safe(self.path / "pyproject.toml")
        if pyproject:
            m = re.search(r'description\s*=\s*"([^"]+)"', pyproject)
            if m:
                return m.group(1)

        # package.json description
        pkg = read_file_safe(self.path / "package.json")
        if pkg:
            m = re.search(r'"description"\s*:\s*"([^"]+)"', pkg)
            if m:
                return m.group(1)

        # Cargo.toml
        cargo = read_file_safe(self.path / "Cargo.toml")
        if cargo:
            m = re.search(r'description\s*=\s*"([^"]+)"', cargo)
            if m:
                return m.group(1)

        # First line of README
        readme = self._find_readme()
        if readme:
            content = read_file_safe(self.path / readme)
            if content:
                for line in content.splitlines():
                    line = line.strip().lstrip("#").strip()
                    if line and not line.startswith("!") and not line.startswith("["):
                        return line[:120]

        return ""

    def _find_readme(self) -> str | None:
        for name in ("README.md", "readme.md", "README.rst", "README.txt", "README"):
            if (self.path / name).exists():
                return name
        return None

    def _detect_architecture(self) -> list[tuple[str, str]]:
        """Detect architecture from top-level directory structure."""
        arch = []
        top_dirs = get_top_level_dirs(self.path)

        for d in top_dirs:
            desc = DIR_DESCRIPTIONS.get(d, "")
            if not desc:
                # Try to infer from contents
                desc = self._infer_dir_purpose(d)
            if desc:
                arch.append((d, desc))

        # Also check for src subdirectory structure
        src_path = self.path / "src"
        if src_path.is_dir():
            for entry in sorted(src_path.iterdir()):
                if entry.is_dir() and not entry.name.startswith((".", "_")):
                    sub_desc = self._infer_src_subdir(entry)
                    if sub_desc:
                        arch.append((f"src/{entry.name}", sub_desc))

        return arch

    def _infer_dir_purpose(self, dirname: str) -> str:
        """Infer purpose of a directory from its name."""
        dir_path = self.path / dirname
        if not dir_path.is_dir():
            return ""

        contents = [f.name for f in dir_path.iterdir() if not f.name.startswith(".")][:20]

        # Check if it's a Python package
        if "__init__.py" in contents:
            return "Python package"

        # Check if it looks like a module directory
        py_files = [f for f in contents if f.endswith(".py")]
        if py_files:
            return "Python modules"

        ts_files = [f for f in contents if f.endswith((".ts", ".tsx"))]
        if ts_files:
            return "TypeScript modules"

        return ""

    def _infer_src_subdir(self, path: Path) -> str:
        """Infer purpose of a src subdirectory."""
        contents = [f.name for f in path.iterdir() if not f.name.startswith(".")][:20]

        if "cli.py" in contents or "main.py" in contents:
            return "Main package with CLI entry point"
        if "__init__.py" in contents:
            return "Core package"
        return ""

    def _detect_entry_points(self, files: list[str]) -> list[str]:
        """Detect main entry points."""
        entry_points = []

        # From pyproject.toml scripts
        pyproject = read_file_safe(self.path / "pyproject.toml")
        if pyproject and "[project.scripts]" in pyproject:
            section = pyproject.split("[project.scripts]")[1].split("\n[")[0]
            for line in section.strip().splitlines():
                if "=" in line:
                    name = line.split("=")[0].strip()
                    target = line.split("=")[1].strip().strip('"').strip("'")
                    if name and target:
                        entry_points.append(f"{name} = {target}")

        # From package.json main/bin
        pkg = read_file_safe(self.path / "package.json")
        if pkg:
            m = re.search(r'"main"\s*:\s*"([^"]+)"', pkg)
            if m:
                entry_points.append(m.group(1))
            m = re.search(r'"bin"\s*:\s*"([^"]+)"', pkg)
            if m:
                entry_points.append(m.group(1))

        # Common main files
        for candidate in ("main.py", "app.py", "manage.py", "main.go", "main.rs"):
            if candidate in files:
                entry_points.append(candidate)
            src_candidate = os.path.join("src", candidate)
            if src_candidate in files:
                entry_points.append(src_candidate)

        return entry_points

    def _detect_notable_files(self, files: list[str]) -> list[str]:
        """Detect notable files that might be relevant."""
        notable = []
        candidates = [
            "CONTRIBUTING.md", "CHANGELOG.md", ".env.example",
            "docker-compose.yml", "docker-compose.yaml",
            "Makefile", "justfile",
        ]
        for c in candidates:
            if c in files:
                notable.append(c)
        return notable
