"""Build import graph from Python source files to find architectural hub files."""

from __future__ import annotations

import ast
import os
from collections import defaultdict
from pathlib import Path

from gitcontext.utils import read_file_safe, walk_repo


def _resolve_module_to_file(module_name: str, repo_path: Path, all_files: list[str]) -> str | None:
    """Try to resolve a Python module name to a file path in the repo."""
    # Convert module.name to module/name.py or module/name/__init__.py
    parts = module_name.split(".")
    candidates = [
        os.path.join(*parts) + ".py",
        os.path.join(*parts, "__init__.py"),
        os.path.join("src", *parts) + ".py",
        os.path.join("src", *parts, "__init__.py"),
    ]
    for candidate in candidates:
        if candidate in all_files:
            return candidate
    return None


def _extract_imports(source: str) -> list[str]:
    """Extract all import module names from Python source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def build_import_graph(repo_path: Path) -> dict[str, list[str]]:
    """Build an import graph: {file_path: [files_it_imports_from_this_repo]}.

    Only includes internal imports (imports that resolve to files in the repo).
    """
    all_files = walk_repo(repo_path, max_depth=6)
    py_files = [f for f in all_files if f.endswith(".py")]

    graph: dict[str, list[str]] = {}

    for py_file in py_files:
        content = read_file_safe(repo_path / py_file, max_size=256_000)
        if not content:
            continue

        imports = _extract_imports(content)
        resolved = []
        for module in imports:
            # Also try submodule prefixes (e.g., for "foo.bar.baz", try "foo.bar" and "foo")
            parts = module.split(".")
            for i in range(len(parts), 0, -1):
                sub = ".".join(parts[:i])
                resolved_file = _resolve_module_to_file(sub, repo_path, all_files)
                if resolved_file and resolved_file != py_file:
                    resolved.append(resolved_file)
                    break

        if resolved:
            graph[py_file] = resolved

    return graph


def find_hub_files(repo_path: Path, top_n: int = 15) -> list[tuple[str, int]]:
    """Find files with the most in-edges (most imported by others).

    Returns list of (file_path, import_count) sorted by count descending.
    """
    graph = build_import_graph(repo_path)

    # Count in-edges
    in_edges: dict[str, int] = defaultdict(int)
    for _source, targets in graph.items():
        for target in targets:
            in_edges[target] += 1

    # Sort by import count
    sorted_hubs = sorted(in_edges.items(), key=lambda x: x[1], reverse=True)
    return sorted_hubs[:top_n]


def get_imports_of_file(filepath: str, repo_path: Path) -> list[str]:
    """Get the internal files imported by a specific file (one level of imports)."""
    all_files = walk_repo(repo_path, max_depth=6)
    content = read_file_safe(repo_path / filepath, max_size=256_000)
    if not content:
        return []

    imports = _extract_imports(content)
    resolved = []
    for module in imports:
        parts = module.split(".")
        for i in range(len(parts), 0, -1):
            sub = ".".join(parts[:i])
            resolved_file = _resolve_module_to_file(sub, repo_path, all_files)
            if resolved_file and resolved_file != filepath:
                resolved.append(resolved_file)
                break

    return resolved
