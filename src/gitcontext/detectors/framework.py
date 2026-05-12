"""Detect frameworks from config files and imports."""

from __future__ import annotations

from pathlib import Path

from gitcontext.utils import read_file_safe


def detect_frameworks(repo_path: Path, files: list[str]) -> list[str]:
    """Detect frameworks used in the project."""
    frameworks = []

    # Check pyproject.toml / setup.cfg / requirements.txt for Python frameworks
    pyproject = read_file_safe(repo_path / "pyproject.toml")
    requirements = read_file_safe(repo_path / "requirements.txt")
    setup_cfg = read_file_safe(repo_path / "setup.cfg")
    python_deps = " ".join(filter(None, [pyproject, requirements, setup_cfg]))

    if python_deps:
        _check_python_frameworks(python_deps, frameworks)

    # Check package.json for JS/TS frameworks
    pkg_json = read_file_safe(repo_path / "package.json")
    if pkg_json:
        _check_js_frameworks(pkg_json, frameworks)

    # Check Cargo.toml for Rust frameworks
    cargo = read_file_safe(repo_path / "Cargo.toml")
    if cargo:
        _check_rust_frameworks(cargo, frameworks)

    # Infrastructure detection
    if any(f == "Dockerfile" or f.startswith("Dockerfile") or f.endswith("Dockerfile") for f in files):
        frameworks.append("Docker")
    if any("kubernetes" in f.lower() or f.endswith("k8s.yml") or f.endswith("k8s.yaml") for f in files):
        frameworks.append("Kubernetes")
    if any(f.endswith(".tf") for f in files):
        frameworks.append("Terraform")

    return frameworks


def _check_python_frameworks(deps: str, frameworks: list[str]) -> None:
    mapping = {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "torch": "PyTorch",
        "tensorflow": "TensorFlow",
        "transformers": "Hugging Face Transformers",
        "huggingface": "Hugging Face",
        "datasets": "Hugging Face Datasets",
        "click": "Click",
        "typer": "Typer",
        "pydantic": "Pydantic",
        "sqlalchemy": "SQLAlchemy",
        "celery": "Celery",
        "gymnasium": "Gymnasium",
        "numpy": "NumPy",
        "pandas": "pandas",
        "scipy": "SciPy",
        "draccus": "draccus",
        "accelerate": "Accelerate",
    }
    deps_lower = deps.lower()
    for key, name in mapping.items():
        if key in deps_lower:
            frameworks.append(name)


def _check_js_frameworks(pkg_json: str, frameworks: list[str]) -> None:
    mapping = {
        '"react"': "React",
        '"next"': "Next.js",
        '"vue"': "Vue",
        '"nuxt"': "Nuxt",
        '"express"': "Express",
        '"@nestjs/core"': "NestJS",
        '"svelte"': "Svelte",
        '"vite"': "Vite",
        '"webpack"': "webpack",
        '"tailwindcss"': "Tailwind CSS",
        '"prisma"': "Prisma",
    }
    for key, name in mapping.items():
        if key in pkg_json:
            frameworks.append(name)


def _check_rust_frameworks(cargo: str, frameworks: list[str]) -> None:
    mapping = {
        "actix": "Actix",
        "tokio": "Tokio",
        "rocket": "Rocket",
        "axum": "Axum",
        "serde": "Serde",
        "clap": "clap",
    }
    cargo_lower = cargo.lower()
    for key, name in mapping.items():
        if key in cargo_lower:
            frameworks.append(name)
