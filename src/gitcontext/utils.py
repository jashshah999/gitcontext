"""File tree walking and gitignore handling."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path


DEFAULT_IGNORE = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    ".next",
    "target",  # Rust/Java
    "vendor",
}


IMPORTANT_DOTFILES = {
    ".pre-commit-config.yaml",
    ".env.example",
    ".dockerignore",
    ".eslintrc.json",
    ".eslintrc.js",
    ".prettierrc",
    ".gitlab-ci.yml",
}


def _is_important_dotfile(filename: str) -> bool:
    return filename in IMPORTANT_DOTFILES


def parse_gitignore(repo_path: Path) -> list[str]:
    """Parse .gitignore and return list of patterns."""
    gitignore = repo_path / ".gitignore"
    if not gitignore.exists():
        return []
    patterns = []
    for line in gitignore.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)
    return patterns


def should_ignore(path: str, ignore_patterns: list[str]) -> bool:
    """Check if path matches any ignore pattern."""
    basename = os.path.basename(path)
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(basename, pattern):
            return True
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def walk_repo(repo_path: Path, max_depth: int = 4) -> list[str]:
    """Walk repo and return relative file paths, respecting gitignore."""
    ignore_patterns = parse_gitignore(repo_path)
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        rel_root = os.path.relpath(root, repo_path)
        depth = 0 if rel_root == "." else rel_root.count(os.sep) + 1
        if depth >= max_depth:
            dirs.clear()
            continue
        # Filter dirs in-place
        dirs[:] = [
            d for d in dirs
            if d not in DEFAULT_IGNORE
            and not should_ignore(d, ignore_patterns)
            and (not d.startswith(".") or d == ".github")
        ]
        for f in filenames:
            rel_path = os.path.join(rel_root, f) if rel_root != "." else f
            if should_ignore(rel_path, ignore_patterns):
                continue
            # Include important dotfiles at repo root
            if f.startswith(".") and not _is_important_dotfile(f):
                continue
            files.append(rel_path)
    return files


def get_top_level_dirs(repo_path: Path) -> list[str]:
    """Get top-level directories (non-hidden, non-ignored)."""
    ignore_patterns = parse_gitignore(repo_path)
    dirs = []
    for entry in sorted(repo_path.iterdir()):
        if entry.is_dir() and not entry.name.startswith(".") and entry.name not in DEFAULT_IGNORE:
            if not should_ignore(entry.name, ignore_patterns):
                dirs.append(entry.name)
    return dirs


def read_file_safe(path: Path, max_size: int = 512_000) -> str | None:
    """Read a file, returning None if it doesn't exist or is too large."""
    if not path.exists() or not path.is_file():
        return None
    if path.stat().st_size > max_size:
        return None
    try:
        return path.read_text(errors="ignore")
    except (OSError, PermissionError):
        return None
