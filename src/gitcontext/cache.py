"""Cache LLM responses based on content hashes."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

CACHE_DIR = Path(os.path.expanduser("~/.cache/gitcontext"))


def _compute_hash(content: str) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_cached(key_content: str) -> str | None:
    """Return cached result if it exists for the given key content."""
    cache_file = CACHE_DIR / f"{_compute_hash(key_content)}.json"
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text())
        return data.get("result")
    except (json.JSONDecodeError, OSError):
        return None


def set_cached(key_content: str, result: str) -> None:
    """Store result in cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{_compute_hash(key_content)}.json"
    try:
        cache_file.write_text(json.dumps({"result": result}))
    except OSError:
        pass


def clear_cache() -> None:
    """Remove all cached results."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.iterdir():
            if f.suffix == ".json":
                f.unlink(missing_ok=True)
