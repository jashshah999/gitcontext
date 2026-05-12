"""Detect languages from file extensions."""

from __future__ import annotations

from collections import Counter

EXTENSION_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".scala": "Scala",
    ".zig": "Zig",
    ".lua": "Lua",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".clj": "Clojure",
    ".dart": "Dart",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

# Files to exclude from language detection
EXCLUDE_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".lock", ".csv", ".xml", ".html", ".css", ".scss", ".less", ".svg", ".png", ".jpg", ".gif", ".ico"}


def detect_languages(files: list[str]) -> list[tuple[str, float]]:
    """Detect languages and return sorted list of (language, percentage)."""
    counter: Counter[str] = Counter()
    for f in files:
        ext = "." + f.rsplit(".", 1)[-1] if "." in f else ""
        if ext in EXCLUDE_EXTENSIONS:
            continue
        lang = EXTENSION_MAP.get(ext)
        if lang:
            counter[lang] += 1
    total = sum(counter.values())
    if total == 0:
        return []
    return [(lang, count / total * 100) for lang, count in counter.most_common()]
