> Your AI agent is flying blind. Fix it in one command.

# gitcontext

Generate `CLAUDE.md` / `AGENTS.md` files for any codebase in seconds. Static analysis detects your stack, architecture, commands, and conventions. `--deep` mode uses Gemini or Claude to produce a rich context doc from actual source code.

## The Problem

AI coding agents (Claude Code, Cursor, Copilot) work better with context files. Writing them manually is tedious and they go stale. Most repos have nothing, so your agent guesses wrong about your build system, test commands, and architecture.

**Before:** Agent hallucinates your project structure, runs wrong commands, misses conventions.

**After:** One command generates a context doc. Your agent knows your stack instantly.

```
$ gitcontext . --output CLAUDE.md
```

<!-- TODO: Record terminal GIF showing: gitcontext run on a real repo, output streaming to terminal, ~10 seconds total -->
<!-- Suggested tool: asciinema + svg-term for animated SVG, or vhs for GIF -->

## Install

```bash
pip install gitcontext
```

For AI-enhanced deep analysis:
```bash
pip install 'gitcontext[all]'  # Gemini + Claude support
```

## Usage

```bash
# Analyze current directory
gitcontext .

# Analyze any local repo
gitcontext /path/to/repo

# Analyze a GitHub repo directly (shallow clones it)
gitcontext https://github.com/huggingface/lerobot

# Write output to file
gitcontext . --output CLAUDE.md

# AGENTS.md format (slightly different structure)
gitcontext . --format agents

# Deep mode: LLM reads your source code for richer output
export GEMINI_API_KEY=...   # or ANTHROPIC_API_KEY
gitcontext . --deep --output CLAUDE.md

# Choose model for deep analysis
gitcontext . --deep --model gemini-2.5-pro
```

## Example Output (Static)

Running `gitcontext .` on [huggingface/lerobot](https://github.com/huggingface/lerobot):

```markdown
## Project Overview

lerobot — State-of-the-art Machine Learning for Real-World Robotics in Pytorch

## Tech Stack

Python · PyTorch · Hugging Face Transformers · Hugging Face Datasets · Gymnasium · uv

## Development Setup

uv sync --locked

## Key Commands

uv run pytest tests
pre-commit run --all-files

## Architecture

- benchmarks/ — Performance benchmarks
- docker/ — Docker configuration
- docs/ — Documentation
- examples/ — Example scripts and tutorials
- src/ — Source code
- tests/ — Test suite

## Entry Points

- lerobot-calibrate = lerobot.scripts.lerobot_calibrate:main
- lerobot-record = lerobot.scripts.lerobot_record:main
- lerobot-train = lerobot.scripts.lerobot_train:main
- ... and 14 more (see pyproject.toml)

## CI/CD

CI: GitHub Actions (benchmark_tests, docker_publish, documentation, fast_tests, full_tests)
```

Generated in ~2 seconds. No API key needed.

## Deep Mode (`--deep`)

Deep mode sends your key source files (configs, entry points, core modules) to an LLM and generates a comprehensive context doc with:

- Architecture explanations (the *why*, not just file names)
- Conventions and patterns (naming, config systems, inheritance)
- Common gotchas and non-obvious behaviors
- Exact setup and contribution workflows

```bash
export GEMINI_API_KEY=your-key    # Free tier works fine
gitcontext . --deep --output CLAUDE.md
```

Auto-detects provider from environment variables. Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` for Gemini, `ANTHROPIC_API_KEY` for Claude.

See [examples/output-deep-lerobot.md](examples/output-deep-lerobot.md) for sample deep output.

## Supported Languages & Frameworks

| Category | Detected |
|----------|----------|
| Languages | Python, TypeScript, JavaScript, Rust, Go, Java, C/C++, Ruby, Kotlin |
| Python Frameworks | FastAPI, Flask, Django, PyTorch, TensorFlow, Click, Pydantic |
| JS/TS Frameworks | React, Next.js, Express, Vite, Svelte |
| Build Systems | pip, uv, poetry, npm, yarn, pnpm, cargo, go mod, cmake, make |
| CI/CD | GitHub Actions, GitLab CI, CircleCI, Jenkins |
| Test Frameworks | pytest, unittest, jest, vitest, cargo test, go test |

## How It Works

1. **Walk** the repo file tree (respects `.gitignore` patterns, skips binaries)
2. **Detect** languages by extension ratio, frameworks by dependency files, build/test/CI by config files
3. **Generate** structured markdown from detections

With `--deep`:

4. **Select** the ~15-20 most important files (configs, entry points, largest source modules)
5. **Send** to Gemini/Claude with a prompt tuned for generating contributor-facing docs
6. **Output** the LLM-generated CLAUDE.md

Total context sent to the LLM is capped at ~80K characters to stay within free tier limits.

## Comparison

| | gitcontext | [gitingest](https://github.com/cyclotruc/gitingest) | Manual | Nothing |
|---|---|---|---|---|
| Auto-detects stack | Yes | No (dumps raw files) | N/A | N/A |
| Structured output | Yes | No | Yes | No |
| Works on any repo | Yes | Yes | No (per-repo effort) | N/A |
| AI-enhanced mode | Yes | No | No | No |
| Speed | ~2s static, ~15s deep | Varies | Hours | 0s |
| Output quality | High (targeted) | Raw dump | Highest | None |

gitingest gives you a raw file dump to paste into an LLM. gitcontext gives you a finished, structured context doc ready to commit.

## Contributing

```bash
git clone https://github.com/jashshah999/gitcontext.git
cd gitcontext
pip install -e '.[all]'
pytest tests
```

PRs welcome. Keep it simple — the goal is a tool that works on any repo without configuration.

## License

MIT
