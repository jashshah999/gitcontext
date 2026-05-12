# gitcontext static output for huggingface/lerobot

Generated with: `gitcontext /path/to/lerobot`

---

## Project Overview

lerobot — State-of-the-art Machine Learning for Real-World Robotics in Pytorch

## Tech Stack

Python · FastAPI · PyTorch · Hugging Face Transformers · Hugging Face · Hugging Face Datasets · Pydantic · Gymnasium · NumPy · uv

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

- **`benchmarks/`** — Performance benchmarks
- **`docker/`** — Docker configuration
- **`docs/`** — Documentation
- **`examples/`** — Example scripts and tutorials
- **`scripts/`** — Utility and CLI scripts
- **`src/`** — Source code
- **`tests/`** — Test suite

## Entry Points

- `lerobot-calibrate = lerobot.scripts.lerobot_calibrate:main`
- `lerobot-find-cameras = lerobot.scripts.lerobot_find_cameras:main`
- `lerobot-find-port = lerobot.scripts.lerobot_find_port:main`
- `lerobot-record = lerobot.scripts.lerobot_record:main`
- `lerobot-replay = lerobot.scripts.lerobot_replay:main`
- `lerobot-setup-motors = lerobot.scripts.lerobot_setup_motors:main`
- ... and 11 more (see pyproject.toml)

## CI/CD

CI: GitHub Actions (benchmark_tests, claude, docker_publish, documentation-upload-pr, documentation)

## Notes

- Notable files: CONTRIBUTING.md, Makefile
- Required env vars: CLOSE_ISSUE_MESSAGE, CLOSE_PR_MESSAGE, DOCKER_IMAGE_NAME, DOCKER_IMAGE_NAME_CPU, DOCKER_IMAGE_NAME_GPU
