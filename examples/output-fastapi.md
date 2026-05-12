## Project Overview

fastapi — FastAPI framework, high performance, easy to learn, fast to code, ready for production

## Tech Stack

Python · FastAPI · Flask · Click · Typer · Pydantic · uv

## Development Setup

```bash
uv sync --locked
```

## Key Commands

```bash
uv run pytest tests
pre-commit run --all-files
```

## Architecture

- **`docs/`** — Documentation
- **`fastapi/`** — Python modules
- **`scripts/`** — Utility and CLI scripts
- **`tests/`** — Test suite

## Entry Points

- `fastapi = fastapi.cli:main`

## CI/CD

CI: GitHub Actions (add-to-project, build-docs, contributors, deploy-docs, detect-conflicts)

## Notes

- Notable files: CONTRIBUTING.md
- Required env vars: HAS_SECRETS, INLINE_SNAPSHOT_DEFAULT_FLAGS, UV_NO_SYNC

