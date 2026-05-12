"""Fetch repo from GitHub (shallow clone)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def clone_repo(url: str) -> Path:
    """Shallow clone a GitHub repo to a temp directory. Returns the path."""
    # Normalize URL
    if not url.endswith(".git"):
        url = url.rstrip("/") + ".git"

    tmpdir = Path(tempfile.mkdtemp(prefix="gitcontext_"))
    try:
        subprocess.run(
            ["git", "clone", "--depth=1", "--single-branch", url, str(tmpdir / "repo")],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"Failed to clone {url}: {e.stderr.strip()}") from e
    except subprocess.TimeoutExpired:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"Timeout cloning {url}")

    return tmpdir / "repo"


def cleanup_clone(path: Path) -> None:
    """Remove a cloned repo temp directory."""
    # Go up to the temp dir parent
    if path.name == "repo":
        shutil.rmtree(path.parent, ignore_errors=True)
    else:
        shutil.rmtree(path, ignore_errors=True)


def is_github_url(s: str) -> bool:
    """Check if a string looks like a GitHub URL."""
    return s.startswith(("https://github.com/", "git@github.com:", "http://github.com/"))
