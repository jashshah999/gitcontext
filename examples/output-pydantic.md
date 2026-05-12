## Project Overview

pydantic — Pydantic Validation

## Tech Stack

Python · Rust · Pydantic · SQLAlchemy · uv

## Development Setup

```bash
uv sync --locked
```

## Key Commands

```bash
uv run pytest tests
make lint
make test
```

## Architecture

- **`docs/`** — Documentation
- **`pydantic/`** — Python modules
- **`release/`** — Python modules
- **`tests/`** — Test suite

## CI/CD

CI: GitHub Actions (ci, codspeed, coverage, dependencies-check, docs-update)

## Notes

- Notable files: Makefile
- Required env vars: COLUMNS, FORCE_COLOR, PIP_PROGRESS_BAR, UV_FROZEN, UV_PYTHON

