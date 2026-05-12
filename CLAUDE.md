## Project Overview

gitcontext — Auto-generate AI context docs (CLAUDE.md / AGENTS.md) for any codebase. Static analysis detects stack, architecture, and commands. `--deep` mode uses Gemini/Claude for rich output.

## Tech Stack

Python 3.10+ · Click (CLI) · PyYAML · hatchling (build)

## Development Setup

```bash
pip install -e '.[all]'
```

## Key Commands

```bash
pytest tests -v
gitcontext .                    # Run on self (dogfood)
gitcontext . --deep --output CLAUDE.md
```

## Architecture

- **`src/gitcontext/cli.py`** — Click CLI entry point. Handles arg parsing, URL detection, output routing.
- **`src/gitcontext/analyzer.py`** — Core `RepoAnalyzer` class. Orchestrates detectors, builds `RepoContext` dataclass.
- **`src/gitcontext/deep.py`** — LLM integration (Anthropic + Gemini). Builds context from file selection, calls API.
- **`src/gitcontext/file_selector.py`** — Smart file selection for deep mode. Priority files first, then entry points, then largest source files. 80K char budget.
- **`src/gitcontext/generators/claude_md.py`** — Template-based markdown generation from `RepoContext`.
- **`src/gitcontext/github.py`** — Shallow clone of GitHub URLs to temp dirs.
- **`src/gitcontext/detectors/`** — Individual detectors: `language.py`, `framework.py`, `build.py`, `ci.py`, `testing.py`.
- **`src/gitcontext/utils.py`** — File walking, safe reads, gitignore-aware traversal.

## Conventions

- Detectors return dataclasses (`BuildInfo`, `CIInfo`, `TestInfo`)
- `RepoContext` is the central data structure passed between stages
- Deep mode auto-detects provider from env vars (ANTHROPIC_API_KEY or GEMINI_API_KEY)
- File selection caps at 80K chars total, 200 lines per file
- CLI uses Click; all progress/debug output goes to stderr, content to stdout

## Entry Points

- `gitcontext` CLI command mapped to `gitcontext.cli:main`
