"""Smart file selection for deep analysis context window."""

from __future__ import annotations

import os
from pathlib import Path

from gitcontext.utils import read_file_safe, walk_repo

# Max total characters to send as file context
CHAR_BUDGET = 80_000
DEEP_CHAR_BUDGET = 120_000
# Max lines per file
MAX_LINES_PER_FILE = 200
DEEP_MAX_LINES_PER_FILE = 400

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

# High-priority filename patterns (factory, registry, config, types, base)
HIGH_PRIORITY_NAMES = {
    "factory", "registry", "config", "configs", "configuration",
    "types", "constants", "base", "core", "utils", "helpers",
    "models", "schema", "schemas", "settings", "exceptions",
}

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
    "vendor",
    "migrations",
    "fixtures",
    "generated",
    ".generated",
    "third_party",
    "thirdparty",
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
    ".pb",
    ".onnx",
    ".parquet",
    ".arrow",
    ".npy",
    ".npz",
    ".pkl",
    ".pickle",
    ".h5",
    ".hdf5",
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
    if basename.endswith("_test.go") or basename.endswith(".spec.ts") or basename.endswith(".spec.js"):
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


def _is_init_file(filepath: str) -> bool:
    """Check if file is __init__.py (defines public API)."""
    return os.path.basename(filepath) == "__init__.py"


def _is_high_priority_name(filepath: str) -> bool:
    """Check if the file stem matches high-priority patterns."""
    stem = os.path.splitext(os.path.basename(filepath))[0]
    return stem in HIGH_PRIORITY_NAMES


def _truncate(content: str, max_lines: int = MAX_LINES_PER_FILE) -> str:
    """Truncate file to max_lines."""
    lines = content.splitlines(keepends=True)
    if len(lines) <= max_lines:
        return content
    return "".join(lines[:max_lines]) + f"\n... (truncated, {len(lines) - max_lines} more lines)\n"


def _get_source_root(all_files: list[str]) -> str | None:
    """Detect the main source directory for large repos."""
    # Check common source roots
    src_prefixes = ["src/", "lib/", "pkg/", "app/", "internal/"]
    for prefix in src_prefixes:
        if any(f.startswith(prefix) for f in all_files):
            return prefix.rstrip("/")
    return None


def select_files(repo_path: Path, deep: bool = False) -> list[tuple[str, str]]:
    """Select the most important files for deep analysis.

    Returns list of (relative_path, content) tuples.
    """
    char_budget = DEEP_CHAR_BUDGET if deep else CHAR_BUDGET
    max_lines = DEEP_MAX_LINES_PER_FILE if deep else MAX_LINES_PER_FILE

    all_files = walk_repo(repo_path, max_depth=6 if deep else 4)
    selected: list[tuple[str, str]] = []
    total_chars = 0
    selected_paths: set[str] = set()

    def _add_file(filepath: str) -> bool:
        nonlocal total_chars
        if filepath in selected_paths:
            return False
        if total_chars >= char_budget:
            return False
        content = read_file_safe(repo_path / filepath)
        if not content:
            return False
        content = _truncate(content, max_lines)
        if total_chars + len(content) > char_budget:
            return False
        selected.append((filepath, content))
        selected_paths.add(filepath)
        total_chars += len(content)
        return True

    # Phase 1: Priority files (config, README, etc.)
    for pfile in PRIORITY_FILES:
        if pfile in all_files:
            _add_file(pfile)

    # Phase 2: Entry points anywhere in the tree
    for f in sorted(all_files):
        if _should_skip(f):
            continue
        if _is_entry_point(f):
            _add_file(f)

    # Phase 3: __init__.py files (public API definitions) — but only non-trivial ones
    init_files = []
    for f in all_files:
        if _should_skip(f):
            continue
        if _is_init_file(f):
            full_path = repo_path / f
            try:
                size = full_path.stat().st_size
            except OSError:
                continue
            # Only include __init__.py files that actually have content (> 100 bytes)
            if size > 100:
                init_files.append((f, size))

    init_files.sort(key=lambda x: x[1], reverse=True)
    for f, _ in init_files[:10]:
        _add_file(f)

    # Phase 4: High-priority names (factory, registry, config, types, base, etc.)
    priority_source: list[tuple[str, int]] = []
    for f in all_files:
        if _should_skip(f):
            continue
        _, ext = os.path.splitext(f)
        if ext not in SOURCE_EXTENSIONS:
            continue
        if _is_high_priority_name(f):
            full_path = repo_path / f
            try:
                size = full_path.stat().st_size
            except OSError:
                continue
            priority_source.append((f, size))

    priority_source.sort(key=lambda x: x[1], reverse=True)
    for f, _ in priority_source[:15]:
        _add_file(f)

    # Phase 5: Import graph hubs (most imported files)
    if deep:
        try:
            from gitcontext.import_graph import find_hub_files
            hubs = find_hub_files(repo_path, top_n=15)
            for filepath, _count in hubs:
                _add_file(filepath)
        except Exception:
            pass  # Non-critical, skip if import graph fails

    # Phase 6: Largest source files (often core modules)
    source_files: list[tuple[str, int]] = []
    # For large repos, restrict to source root
    large_repo = len(all_files) > 1000
    source_root = _get_source_root(all_files) if large_repo else None

    for f in all_files:
        if _should_skip(f):
            continue
        if large_repo and source_root and not f.startswith(source_root + "/"):
            # In large repos, skip docs/examples/tests for this phase
            parts = f.split(os.sep)
            if parts[0] in ("docs", "examples", "tests", "test", "benchmarks", "scripts"):
                continue
        _, ext = os.path.splitext(f)
        if ext not in SOURCE_EXTENSIONS:
            continue
        full_path = repo_path / f
        try:
            size = full_path.stat().st_size
        except OSError:
            continue
        source_files.append((f, size))

    source_files.sort(key=lambda x: x[1], reverse=True)
    for f, _ in source_files[:20]:
        _add_file(f)

    return selected
