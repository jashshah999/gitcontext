"""Smart file selection for deep analysis context window."""

from __future__ import annotations

import os
from pathlib import Path

from gitcontext.utils import read_file_safe, walk_repo

# Max total characters to send as file context
CHAR_BUDGET = 80_000
# Max lines per file
MAX_LINES_PER_FILE = 200

# Files to always include if they exist
PRIORITY_FILES = [
    "README.md",
    "readme.md",
    "CONTRIBUTING.md",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Makefile",
    "docker-compose.yml",
    "docker-compose.yaml",
]

# Entry point patterns (higher priority)
ENTRY_PATTERNS = [
    "main.py",
    "app.py",
    "cli.py",
    "manage.py",
    "__main__.py",
    "index.ts",
    "index.js",
    "main.go",
    "main.rs",
    "lib.rs",
]

# Skip patterns
SKIP_PATTERNS = {
    "node_modules",
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".egg-info",
    "venv",
    ".venv",
    ".tox",
}

SKIP_EXTENSIONS = {
    ".lock",
    ".min.js",
    ".min.css",
    ".map",
    ".wasm",
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".bin",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".pdf",
}

SOURCE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".kt", ".rb", ".c", ".cpp", ".h"}


def _should_skip(filepath: str) -> bool:
    """Check if a file should be skipped."""
    parts = filepath.split(os.sep)
    for part in parts:
        if part in SKIP_PATTERNS:
            return True
    # Skip test files
    basename = os.path.basename(filepath)
    if basename.startswith("test_") or basename.endswith("_test.py") or basename.endswith(".test.ts"):
        return True
    # Skip by extension
    _, ext = os.path.splitext(filepath)
    if ext in SKIP_EXTENSIONS:
        return True
    return False


def _is_entry_point(filepath: str) -> bool:
    """Check if file looks like an entry point."""
    basename = os.path.basename(filepath)
    return basename in ENTRY_PATTERNS


def _truncate(content: str, max_lines: int = MAX_LINES_PER_FILE) -> str:
    """Truncate file to max_lines."""
    lines = content.splitlines(keepends=True)
    if len(lines) <= max_lines:
        return content
    return "".join(lines[:max_lines]) + f"\n... (truncated, {len(lines) - max_lines} more lines)\n"


def select_files(repo_path: Path) -> list[tuple[str, str]]:
    """Select the most important files for deep analysis.

    Returns list of (relative_path, content) tuples.
    """
    all_files = walk_repo(repo_path)
    selected: list[tuple[str, str]] = []
    total_chars = 0

    # Phase 1: Priority files (config, README, etc.)
    for pfile in PRIORITY_FILES:
        if total_chars >= CHAR_BUDGET:
            break
        if pfile in all_files:
            content = read_file_safe(repo_path / pfile)
            if content:
                content = _truncate(content)
                selected.append((pfile, content))
                total_chars += len(content)

    # Phase 2: Entry points anywhere in the tree
    entry_files = []
    for f in all_files:
        if _should_skip(f):
            continue
        if _is_entry_point(f):
            entry_files.append(f)

    for f in sorted(entry_files):
        if total_chars >= CHAR_BUDGET:
            break
        if any(s[0] == f for s in selected):
            continue
        content = read_file_safe(repo_path / f)
        if content:
            content = _truncate(content)
            selected.append((f, content))
            total_chars += len(content)

    # Phase 3: Largest source files in src/, lib/, or root package
    source_files: list[tuple[str, int]] = []
    for f in all_files:
        if _should_skip(f):
            continue
        _, ext = os.path.splitext(f)
        if ext not in SOURCE_EXTENSIONS:
            continue
        if any(s[0] == f for s in selected):
            continue
        # Get file size as proxy for importance
        full_path = repo_path / f
        try:
            size = full_path.stat().st_size
        except OSError:
            continue
        source_files.append((f, size))

    # Sort by size descending (largest files are often core modules)
    source_files.sort(key=lambda x: x[1], reverse=True)

    for f, _ in source_files[:15]:
        if total_chars >= CHAR_BUDGET:
            break
        content = read_file_safe(repo_path / f)
        if content:
            content = _truncate(content)
            if total_chars + len(content) > CHAR_BUDGET:
                continue
            selected.append((f, content))
            total_chars += len(content)

    return selected
