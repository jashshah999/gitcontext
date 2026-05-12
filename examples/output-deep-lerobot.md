# gitcontext --deep output for huggingface/lerobot

Generated with: `gitcontext /path/to/lerobot --deep` (using Gemini 2.5 Flash)

---

## Project Overview

LeRobot is a PyTorch-based library for real-world robotics, providing datasets, pretrained policies, and tools for training, evaluation, data collection, and robot control. It integrates with Hugging Face Hub for model/dataset sharing.

## Tech Stack

Python 3.10+ · PyTorch · Hugging Face (datasets, Hub, accelerate) · draccus (config/CLI) · Gymnasium (envs) · uv (package management)

## Development Setup

```bash
uv sync --locked                            # Base dependencies
uv sync --locked --extra test --extra dev   # Test + dev tools
uv sync --locked --extra all                # Everything
git lfs install && git lfs pull             # Test artifacts
```

## Key Commands

```bash
uv run pytest tests -svv --maxfail=10                 # All tests
DEVICE=cuda make test-end-to-end                      # All E2E tests
pre-commit run --all-files                            # Lint + format (ruff, typos, bandit)
```

## Architecture

- **`scripts/`** — CLI entry points (`lerobot-train`, `lerobot-eval`, `lerobot-record`, etc.), mapped in `pyproject.toml [project.scripts]`.
- **`configs/`** — Dataclass configs parsed by draccus. `train.py` has `TrainPipelineConfig` (top-level). Polymorphism via `draccus.ChoiceRegistry` with `@register_subclass("name")` decorators.
- **`policies/`** — Each policy in its own subdir. All inherit `PreTrainedPolicy` (`nn.Module` + `HubMixin`). Factory with lazy imports in `factory.py`.
- **`datasets/`** — `LeRobotDataset` (episode-aware sampling + video decoding) and `LeRobotDatasetMetadata`.
- **`envs/`** — `EnvConfig` base in `configs.py`, factory in `factory.py`. Each env subclass defines `gym_kwargs` and `create_envs()`.
- **`robots/`, `motors/`, `cameras/`, `teleoperators/`** — Hardware abstraction layers.

## Conventions and Patterns

- Config system uses draccus dataclasses with `ChoiceRegistry` for polymorphic dispatch
- Policies register themselves via `@register_subclass("policy_name")` decorator
- Optional dependencies guarded behind extras (`lerobot[aloha]`, `lerobot[pi0]`)
- Video decoding handled transparently by `LeRobotDataset.__getitem__`
- All CLI scripts use the pattern: dataclass config + `draccus.wrap()` for CLI parsing

## Common Gotchas

- Video decoding (pyav) dominates `__getitem__` time (~92%); consider torchcodec for 3x speedup
- Many policies/envs/robots behind optional extras — imports must be guarded or lazy
- `policy.path` is special CLI-only handling, filtered before draccus sees it
- Tests need `git lfs pull` for video fixtures or they silently fail
- Mypy is gradual: strict only for specific modules (envs, configs, optim, cameras, motors)

## Notes for Contributors

- Use `uv run` to execute Python commands (not raw `python` or `pip`)
- New policies go in `src/lerobot/policies/<name>/` with config registered via decorator
- PR CI runs `fast_tests.yml` on every PR, `full_tests.yml` after approval (GPU required)
- Pre-commit includes ruff, typos, bandit — run before pushing
